# SYMBIOSE — tools/jardinier_auto/perception.py
# Étape 1 de la boucle (§3.1) : « que sais-je de cette plante ET de son voisinage ? ».
# Une interface, deux implémentations commutées par le profil (§9) :
#   - omniscient : lit DIRECTEMENT l'état écologique (vitalité continue D75,
#     humidité, lumière reçue, Qi, paillage, structure du sol) + le VOISINAGE
#     (férales concurrentes, voisin ombrageant). Référence haute. Câblé dès ①/②.
#   - semiologique : ne lira que ce qu'un joueur VOIT (signes, `etat` discret).
#     Stub ici → tronçon ⑦ optionnel.
#
# LECTURE PURE (philo #2/#5) : aucune fonction n'écrit un champ ni un attribut de
# plante. La perception ne fait qu'observer ; ce sont les gestes (execution.py) qui
# agissent, via `sim.actions`. Le VOISINAGE (§5 : concurrence férale, ombrage) est
# scanné LOCALEMENT — plantes de la MÊME tuile seulement (N/tuile petit → O(N²)
# local négligeable, §11), avec un départage stable `(y_cm, x_cm)` (philo #3).

from __future__ import annotations
from dataclasses import dataclass

from sim.vigueur_plante import maturite, qi_local
from sim.semiologie import leaf_symptoms
from sim.actions.paillage import TISSUS_GLANABLES   # tissus glanables → mulch (③, canal 1)
from .tutelle import est_ferale


def _litiere_tendre_at(eco, r: int, c: int) -> float:
    """Masse de litière de SURFACE tendre (glanable → mulch `feuilles`, ③) au plot
    (r,c) — lecture PURE. Sert au ravitaillement par `glaner` : c'est la matière
    qu'un geste `glaner` créditerait au stock. Miroir de la sélection de la façade
    `sim.actions.glaner` (mêmes `TISSUS_GLANABLES`)."""
    return sum(p.masse for p in eco.litiere[r][c] if p.tissu in TISSUS_GLANABLES)


@dataclass(frozen=True)
class Perception:
    """Instantané omniscient d'une plante sous tutelle + son voisinage, à un tick.
    Valeurs continues — le profil semiologique les remplacera par des signes."""

    position: tuple      # (row, col) plot-foyer, cible des gestes de milieu
    vitalite: float      # santé continue [0,1] (D75)
    maturite: float      # avancement du cycle [0,1] — mûr → récolte possible
    humidite: float      # humidité du sol au plot-foyer [0,3]
    lumiere: float       # lumière reçue par la canopée [0,1] (1 = plein soleil)
    qi: float            # Qi territorial puisé sous l'empreinte racinaire [0,1]
    paillage: float      # couverture du sol au plot-foyer [0,1] (0 = sol nu)
    structure: float     # structure du sol au plot-foyer [0,1] (bas = compacté)
    litiere_tendre: float    # masse de litière de SURFACE tendre au plot (glanable → mulch, ③)
    ferale_cible: object     # férale à arracher (concurrence diagnostiquée) | None
    voisin_ombrageant: object  # voisin plus haut qui ombrage la plante | None


@dataclass(frozen=True)
class PerceptionSemio:
    """Instantané SÉMIOLOGIQUE (§9, tronçon ⑦) : ce qu'un JOUEUR humain voit à
    l'écran, rien de plus. AUCUNE valeur continue de santé/humidité/Qi/structure —
    seulement les SIGNES diégétiques réellement émis par le moteur :
      - `etat`  : l'état discret {sain/affaibli/malade/mort} (couleur/texture) ;
      - `signes`: l'ensemble des causes de symptômes FOLIAIRES visibles (la même
        liste `leaf_symptoms` que la vue affiche : secheresse/ombre/asphyxie…) ;
      - `ferale_cible` / `voisin_ombrageant` : entités VISIBLES à l'écran (sprites
        d'adventices dans le rang, voisin manifestement plus haut) — mêmes helpers
        que l'omniscient (une mauvaise herbe et un voisin dominant SE VOIENT) ;
      - `maturite` : proxy du seul fait visible « il y a un organe MÛR » (le fruit
        apparaît sur la plante) — le diagnostic n'en lit que le seuil, pas la valeur.
    Volontairement plus PAUVRE que l'omniscient : un facteur sans signe (sol nu, sol
    compacté) est INVISIBLE → non diagnosticable → défaut de sémiologie #5 mesurable."""

    position: tuple             # (row, col) plot-foyer
    etat: str                   # "sain" | "affaibli" | "malade" | "mort"
    signes: frozenset           # causes de symptômes foliaires visibles (leaf_symptoms)
    maturite: float             # avancement du cycle — proxy du fruit mûr VISIBLE
    ferale_cible: object        # adventice visible à arracher | None
    voisin_ombrageant: object   # voisin dominant visible | None


def _ferale_cible(plant, voisins, tile_id, cultivees, seuil):
    """La férale à arracher, ou None. Compte les férales VIVANTES dont le plot-foyer
    tombe dans l'empreinte racinaire de la cultivée ; si leur nombre atteint `seuil`
    (mode `desherbage`, §4), renvoie la « pire » (départage stable `(y_cm, x_cm)`).
    `seuil is None` (mode `aucun`) → jamais de cible."""
    if seuil is None:
        return None
    empreinte = set(plant.root_plots)
    empreinte.add(plant.position)
    ferales = [v for v in voisins
               if v is not plant and est_ferale(v, tile_id, cultivees)
               and v.position in empreinte]
    if len(ferales) < seuil:
        return None
    return min(ferales, key=lambda v: (v.y_cm, v.x_cm))


def _voisin_ombrageant(plant, voisins):
    """Le voisin qui ombrage `plant`, ou None. Candidat = plante VIVANTE plus HAUTE
    dont la canopée recouvre le plot-foyer de la cultivée. On renvoie le plus haut
    (départage stable). Sert au geste `tailler` (§5). Ne présume RIEN sur la lumière
    reçue — c'est le diagnostic qui croise ombrage géométrique ET lumière basse."""
    r_c = plant.position
    h0 = plant.current_height
    candidats = [v for v in voisins
                 if v is not plant and v.is_alive
                 and v.current_height > h0 and r_c in v.foliar_plots]
    if not candidats:
        return None
    return max(candidats, key=lambda v: (v.current_height, -v.y_cm, -v.x_cm))


def _percevoir_semio(plant, eco, voisins, tile_id, cultivees, seuil, saison):
    """Perception SÉMIOLOGIQUE (§9) : ne lit QUE les signes visibles. Les symptômes
    foliaires passent par `sim.semiologie.leaf_symptoms` — EXACTEMENT la liste que la
    vue Godot affiche sur le feuillage (ombre/secheresse/asphyxie…). On n'en garde
    que l'ENSEMBLE des causes présentes (le joueur voit QUE ça souffre, pas de combien).
    Le voisinage visible (adventice, voisin dominant) réutilise les helpers omniscients
    — ce sont des SPRITES à l'écran, donc légitimement perçus. Aucune lecture de
    vitalité/Qi/humidité/structure : ces champs n'ont pas de rendu direct."""
    r, c = plant.position
    signes = frozenset(s["cause"] for s in leaf_symptoms(plant, eco, saison))
    return PerceptionSemio(
        position=(r, c),
        etat=plant.etat,
        signes=signes,
        maturite=maturite(plant),
        ferale_cible=_ferale_cible(plant, voisins, tile_id, cultivees, seuil),
        voisin_ombrageant=_voisin_ombrageant(plant, voisins),
    )


def percevoir(plant, eco, profil, voisins, tile_id, cultivees, saison=None):
    """Construit la perception d'une `plant` cultivée selon le `profil`, en incluant
    son voisinage (`voisins` = plantes de la même tuile, `cultivees` = zones
    cultivées). `omniscient` : lecture directe des champs continus. `semiologique`
    (⑦) : ne lit que les signes visibles (`saison` requis pour `leaf_symptoms`)."""
    if profil.perception == "semiologique":
        return _percevoir_semio(plant, eco, voisins, tile_id, cultivees,
                                profil.seuil_concurrence(), saison)
    r, c = plant.position
    return Perception(
        position=(r, c),
        vitalite=plant.vitalite,
        maturite=maturite(plant),
        humidite=eco.humidite.at_plot(r, c),
        lumiere=eco.lumiere.light_received(plant),
        qi=qi_local(plant, eco),
        paillage=eco.paillage.at_plot(r, c),
        structure=eco.structure_sol.at_plot(r, c),
        litiere_tendre=_litiere_tendre_at(eco, r, c),
        ferale_cible=_ferale_cible(plant, voisins, tile_id, cultivees,
                                   profil.seuil_concurrence()),
        voisin_ombrageant=_voisin_ombrageant(plant, voisins),
    )
