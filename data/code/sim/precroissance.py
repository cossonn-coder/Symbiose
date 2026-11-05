"""
SYMBIOSE — sim/precroissance.py
PRÉ-CROISSANCE des plantes pré-vieillies (D111 ②ter, ferme D105). Un fruitier
« de 5 ans » posé à l'init des mondes de jeu (`full`/`propre`) ou d'un banc avait
l'ÂGE de 5 ans mais la STRUCTURE d'un semis (1 segment, ~22 cm) : on vieillissait
le nombre, pas l'arbre. Ici on DÉROULE la morphogénèse sur ces années, semaine
par semaine, avec le vrai cycle saisonnier — l'arbre a la charpente de son âge.

Pédagogie (Nico) : c'est la même fonction `grow_plant` que le tick, appelée en
boucle HORS tick (pure, déterministe, aucun `eco`). Sans lumière (`light_field=
None` : arbre isolé, apex droit) — le champ de lumière n'existe pas encore à
l'init. La cladoptose y est jouée au même rythme borné qu'en jeu (plein soleil,
auto-ombrage de la couronne seul) : la couronne arrive « déjà taillée par l'ombre »
au lieu de lâcher d'un coup tout son bois intérieur la première année. Le bois
tombé pendant ces années n'est PAS déposé : c'est `sim/bois_initial.py` qui pose
le bois des années passées.
Les semaines 1..N·52 finissent en fin d'hiver → la partie démarre au printemps
(semaine 1) dans la continuité du cycle.
"""

from __future__ import annotations

from sim.growth import (grow_plant, shade_tolerance_effective, branches_ombragees,
                        couper_branches, seuil_et_age, fenetre_ouverte)
from sim.growth.constantes import CLADO_PAR_FENETRE
from sim.growth.tige_libre import effondrer

from calendrier import SEMAINE_HIVER, wiy_de   # calendrier UNIQUE (D122, couche basse)


def pre_croitre(plant, seed: int, annees: float) -> None:
    """Fait pousser la structure de `plant` sur `annees` années (no-op pour une
    espèce non procédurale : son empreinte suit son stade, pas des segments).
    N'écrit PAS l'âge : l'appelant le pose (cohérence avec `age_years`)."""
    cls = plant.plant_class
    n = int(round(annees * 52))
    if not cls.procedural_growth or not plant.segments or n <= 0:
        return
    for w in range(1, n + 1):
        grow_plant(plant, seed, w)
        effondrer(plant)                 # liane à `rigidite_tige` : même port qu'en jeu, sinon no-op
        if cls.ligneux and fenetre_ouverte(plant, seed, w):
            saison = "hiver" if wiy_de(w) >= SEMAINE_HIVER else "ete"
            densite = cls.foliage_density_at(plant, saison)
            if densite > 0.0:
                seuil, age_min = seuil_et_age(shade_tolerance_effective(plant))
                couper_branches(plant, branches_ombragees(
                    plant, 1.0, densite, seuil, age_min, n_max=CLADO_PAR_FENETRE))
    plant.update_footprint()
