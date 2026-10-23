"""
SYMBIOSE — fields/ecofields/vie_macro.py
Responsabilité : la VIE MACROSCOPIQUE observable d'une tuile (D31.1) — tick des
guildes trophiques dans l'ordre proie→prédateur, ponts de cycle de vie
(chenille/syrphe larve → adulte), densité pollinisatrice et agrégation par
catégorie (modèle B).

Mixin de comportement de `EcoFields` (scission refactor 2026-06-30, container
déjà dense). Aucun état propre : opère sur `self`. Comportement bit-identique
à l'ancien `container.py`.
"""

from __future__ import annotations

from fields.population import POLLINATOR_NAMES, build_lifecycle_bridges, daylength
from fields.lifecycle import tick_bridges


class VieMacroMixin:
    """Populations, ponts de cycle de vie, pollinisateurs, catégories."""

    # --- Vie macroscopique (D31.1) ---

    def tick_populations(self, tile, plants, week_in_year: int = 25) -> None:
        """
        Ticke les 4 champs de population dans l'ordre trophique. Le ravageur
        d'abord (il lit l'auxiliaire de la semaine précédente → décalage proie-
        prédateur), puis l'auxiliaire lit le ravageur fraîchement mis à jour.

        `week_in_year` pilote la porte saisonnière photopériodique des guildes
        (dormance hivernale / réveil printanier — CONCEPTION_SAISONNALITE_VIE_MACRO).
        Défaut 25 (plein été) pour les appels de test sans saison.

        À appeler APRÈS les autres champs (température, perturbation à jour).
        Pure lecture des champs existants : n'écrit QUE sur les champs de
        population, ne produit aucun log.
        """
        for name in self._population_order:
            popfield = self.populations[name]
            predator_fields = [pf for p in popfield.spec.predators
                               if (pf := self._predator_field(p)) is not None]
            popfield.tick(self, tile, plants, predator_fields, week_in_year)

    def _predator_field(self, name: str):
        """Résout un champ prédateur par nom : d'abord une guilde (`populations`),
        sinon un champ larvaire (`larvae`) — le syrphe_larve prédate le ravageur
        (§D.3.2) sans être une guilde. Retourne un objet `.at_plot`-compatible ou
        None. À densité nulle, contribue +0 → invariant golden (§D.6)."""
        f = self.populations.get(name)
        return f if f is not None else self.larvae.get(name)

    def tick_lifecycle_bridges(self, tile, plants, week_in_year: int = 25) -> None:
        """Ticke les ponts de cycle de vie (§D, tronçon ⑤) — APRÈS les guildes et
        les butineurs (ordre §K.2). Délègue au tick PUR `fields.lifecycle.tick_bridges`
        (ponte/maturation/famine/métamorphose), en lui passant la photopériode du
        moment (`daylength(week_in_year)`). N'écrit que `eco.larvae` + le terme-source
        de métamorphose dans les champs adultes (papillon/syrphe). Aucun log.

        No-op STRICT si aucun pont (registre vide) ou si chaque pont reste à 0
        (aucun adulte, ou hors fenêtre de ponte) → golden inchangé (§D.6)."""
        tick_bridges(self, tile, plants, build_lifecycle_bridges(),
                     daylength(week_in_year))

    def pollinator_density(self, r: int, c: int) -> float:
        """Densité pollinisatrice TOTALE en un plot = somme des champs par type
        (abeille + syrphe + papillon, §C/§E). Remplace l'ancien champ agrégé unique
        `pollinisateur` ; lue par `pollinator_reach` (brassage génétique) et la
        Vigueur macro. Bornée par la somme, non re-clampée (les lecteurs saturent)."""
        return sum(self.populations[n].at_plot(r, c)
                   for n in POLLINATOR_NAMES if n in self.populations)

    # --- Agrégation par CATÉGORIE (modèle B, docs/faune/vie_macro/conception_faune_dediee.md §1.2) ---
    # La guilde n'est plus un champ stocké mais une VUE : la somme des espèces qui
    # partagent l'étiquette `spec.category`. Les consommateurs « par guilde » (santé
    # des plantes, vigueur macro) lisent ces agrégats au lieu de `populations[nom]`.
    # Tant qu'une catégorie n'a qu'un membre (④a), l'agrégat == le champ unique →
    # golden NEUTRE. Les pollinisateurs (PollinatorSpec, sans `category`) en sont
    # naturellement exclus (getattr → None).

    def category_fields(self, category: str) -> list:
        """Champs de population membres d'une CATÉGORIE (étiquette `spec.category`).
        Mémoïsé (FLUIDITÉ AN 2 ②) : appelé ~4 000 fois par tick (par plot, via
        `category_density`) alors que l'appartenance ne change pas. Clé auto-
        invalidante = (dict `populations` lui-même, sa taille) ; liste en LECTURE
        seule pour les appelants (même contenu, même ordre qu'avant)."""
        pops = self.populations
        cache = getattr(self, "_cache_categories", None)
        if cache is None or cache[0] is not pops or cache[1] != len(pops):
            cache = (pops, len(pops), {})
            self._cache_categories = cache
        membres = cache[2].get(category)
        if membres is None:
            membres = [pf for pf in pops.values()
                       if getattr(pf.spec, "category", None) == category]
            cache[2][category] = membres
        return membres

    def category_density(self, category: str, r: int, c: int) -> float:
        """Densité agrégée d'une catégorie = somme des densités des espèces membres.
        Remplace la lecture directe `populations["ravageur"].at_plot(...)`."""
        return sum(pf.at_plot(r, c) for pf in self.category_fields(category))
