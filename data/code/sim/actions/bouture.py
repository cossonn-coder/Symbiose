"""
SYMBIOSE — sim/actions/bouture.py
Geste BOUTURER (sprint PALETTE DE GESTES, tronçon ②).
Spec : `docs/joueur/gestes/conception_palette_gestes.md` §3.5 + kickoff
`sprints/sprint_palette_gestes/02_bouture.md`.

Multiplication végétative PAR LE JOUEUR : on prélève un fragment (greffon) sur
une plante mère et on l'enracine ailleurs — la fille naît CLONE de la mère
(vecteur de gènes COPIÉ + priming plastique hérité, PAS de brassage sexué ≠
reproduction.py). Réutilise EXACTEMENT le patron de clonage de `sim/clonal.py`
(l'émission clonale AUTONOME au tick) : ici c'est le JOUEUR qui déclenche l'acte,
event-driven AU-DESSUS du tick.

INVARIANTS (philo de design) :
  #1/#2 — le coût de prélever un greffon passe par un état PHYSIOLOGIQUE (bouffée
          de `stress_memory` sur la mère, façade Vigueur pour le gate), jamais par
          un malus direct. Le geste est DIRECT sur le vivant (permis mais coûteux,
          #1) : coût MODERE côté Vigueur joueur (`couts.cout_action`).
  #3    — DÉTERMINISTE, zéro RNG : la bouture est un ACTE joueur, pas un tirage.
          Le clone est identique à la mère, la pose est le point du clic.
  #6    — pas de punition d'une tentative impossible : refus EN AMONT (mère non
          bouturable / trop jeune / épuisée) SANS dépense (patron `planter`/lot vide).

GARDE-FOU DE COUCHE : ce module vit au-dessus du tick écologique. Le golden
(`tests/test_golden.py`) est une succession spontanée SANS joueur → n'invoque
jamais `bouturer` → no-op strict, golden inchangé.

Couche : `sim` peut lire `fields`/`plants` et importer `sim.clonal` (helpers de
clonage, réutilisés — pas de duplication).
"""
from __future__ import annotations

from sim.vigueur import spend
from sim.vigueur_plante import vigueur_plante
from sim.clonal import _mature, _plot_of, CLONAL_STRESS_COST, CLONAL_VIGUEUR_SEUIL
from sim.actions.couts import cout_action, _objets_action
from sim.actions.deblocage import marquer_evenement

# Coût physiologique sur la MÈRE : prélever un greffon la fatigue (bouffée de
# stress_memory, puise son énergie propre → arbitrage émergent, philo #1/#2). On
# réutilise l'ordre de grandeur du clonage autonome (`CLONAL_STRESS_COST`) : un
# greffon prélevé à la main ≈ un ramet émis spontanément.
BOUTURE_STRESS_COST = CLONAL_STRESS_COST
# Seuil de Vigueur de la mère pour supporter le prélèvement (même façade read-only
# que le clonal ; une mère mourante — santé → 0 → façade nulle — refuse).
BOUTURE_VIGUEUR_SEUIL = CLONAL_VIGUEUR_SEUIL


def peut_bouturer(mother, eco) -> bool:
    """Gate physiologique du prélèvement (lecture SEULE, aucune mutation) :
      • espèce réellement bouturable (`plant_class.bouturable`) ;
      • mère VIVANTE ;
      • mère assez MÛRE (dernier stade atteint, critère `clonal._mature`) ;
      • mère assez VIGOUREUSE (façade `vigueur_plante` au-dessus d'un plancher bas).
    Toute condition manquante → refus EN AMONT, avant toute dépense (philo #6)."""
    if not getattr(mother.plant_class, "bouturable", False):
        return False
    if not mother.is_alive or not _mature(mother):
        return False
    return vigueur_plante(mother, eco) >= BOUTURE_VIGUEUR_SEUIL


def bouturer(game_state: dict, player: str, mother, tile, eco,
             r: int, c: int) -> bool:
    """Prélève un greffon sur `mother` et l'enracine sur le plot (r, c) de `tile`
    — geste à 2 temps côté pont (1er clic = la mère, 2e clic = le plot cible ;
    ici les deux cibles sont déjà résolues). BINAIRE tout-ou-rien (modèle
    `planter`/`deraciner`) : le clone n'est posé QUE si le gate physiologique passe
    ET si le coût Vigueur est INTÉGRALEMENT payé.

    Séquence :
      1. gate `peut_bouturer` — refus AVANT toute dépense si la mère ne peut donner ;
      2. coût Vigueur joueur MODERE (`cout_action`) — si `spend < 1.0`, on renonce
         (le greffon n'est pas prélevé, la mère intacte) ;
      3. pose du CLONE via `tile.add_plant` au plot cliqué (position continue =
         point du clic) : gènes COPIÉS + expression (priming) héritée, EXACTEMENT
         comme `clonal.emettre_ramets` — aucun brassage (philo #3) ;
      4. coût physiologique sur la MÈRE : bouffée de `stress_memory` (philo #1/#2) ;
      5. voie EXPÉRIMENTALE émergente (D12, §3.2·c) : réussir une bouture est la
         preuve pratique qu'on a reproduit le phénomène → on pose le marqueur
         `bouture_spontanee` au ledger du joueur, qui ouvre `bouturer` par la voie
         `("evenement", …)` de ① (idempotent). La voie savoir composée reste le
         chemin principal ; ce marqueur est le bonus diégétique minimal.

    Renvoie True si le clone a effectivement été posé. Déterministe, no-op golden
    (le smoke n'appelle jamais ce geste)."""
    if not peut_bouturer(mother, eco):
        return False                          # refus EN AMONT — aucune Vigueur dépensée (philo #6)

    cost = cout_action(game_state, player, "bouturer",
                       _objets_action("bouturer", mother))
    if spend(game_state, player, cost) < 1.0:
        return False                          # Vigueur insuffisante → greffon non prélevé

    ramet = tile.add_plant(mother.plant_class, r, c)
    if ramet is None:
        return False                          # plot invalide (add_plant a rendu None)
    # Clone : vecteur de gènes COPIÉ (pas de brassage) + priming plastique hérité,
    # à l'identique de `clonal.emettre_ramets` → le greffon naît dans l'état
    # d'acclimatation de la mère.
    ramet.genes = dict(mother.genes)
    ramet.expression.update(mother.expression)
    # Position : `add_plant(cls, r, c)` a déjà recentré le clone sur le plot cliqué
    # (`PlantInstance.__post_init__` pose x_cm/y_cm au centre du plot cible) → le
    # greffon s'enracine où le 2e clic l'a désigné. Rien de plus à écrire.

    # Coût sur la MÈRE : bouffée de stress physiologique (puise l'énergie propre →
    # arbitrage émergent). Intégré comme les perturbations, clampé [0, 1].
    mother.stress_memory = min(1.0, mother.stress_memory + BOUTURE_STRESS_COST)

    # Voie expérimentale émergente (D12) : la réussite EST la maîtrise pratique.
    marquer_evenement(game_state, player, "bouture_spontanee")
    return True
