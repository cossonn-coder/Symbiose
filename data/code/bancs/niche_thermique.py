"""
SYMBIOSE — bancs/niche_thermique.py
Banc d'essai NICHE THERMIQUE (D139, sprint niche thermique ⑤, observation F5).

Ce que Nico doit VOIR en faisant défiler les semaines, deux scènes à la fois :

  (b) CANICULE — trois basilics par décor, au sud de la maison et dans son ombre :
      ① plein soleil, sable SEC (assoiffé) : se replie, flétrit à midi, jaunit aux
         bords, puis BRÛLE à la canicule (semaine 24 du seed 42) ;
      ② plein soleil, terre GORGÉE (arrosé) : la feuille transpire, reste près de l'air ;
      ③ à l'OMBRE du mur nord, sable sec : sans soleil, la soif ne chauffe plus la feuille.
  (a) AUTOMNE-HIVER — sur une même tuile, en rangées :
      basilics sol NU · basilics PAILLÉS (litière épaisse) · basilics VOILÉS (voile
      d'hivernage) · mâches · seigles. Les nuits d'automne passent sous 10 °C : le
      basilic pend, se violace, se détrempe puis meurt — d'abord sur sol nu, plus tard
      sous paillis ou voile ; la mâche et le seigle restent verts.

📖 Pourquoi une seule tuile de départ en ÉTÉ : la vue lance 12 semaines de warmup avant
le premier dessin. Départ s11 (≈ début juin) → arrivée s23, la canicule tombe en s24, et
l'automne suit sans relancer le banc. Un départ plus tôt tuerait le basilic dès les nuits
de mai (lim_froid 10 °C), avant toute observation.

📖 Pourquoi pas de canicule FORCÉE : forcer la météo demanderait un drapeau moteur
(patron `pluie_forcee`) ; ce tronçon ne touche pas au moteur. La vue lance le seed 42
(`WorldView.Seed`), qui pose une Canicule en s16 et s24 (T_air 22,0 et 24,9 °C).

Pure COMPOSITION d'un état (sol, litière, voile, plantes) : golden NEUTRE (une fabrique
de banc n'est jamais montée pour smoke/full). Zéro RNG (philo #3).
"""
from __future__ import annotations

from plants import Basil, CornSalad, Rye
from sim.actions.couvertures import VOILE_COUVERT, RAYON_VOILE_PLOTS
from .base import build_banc_tile, monde, banque_de, sans_herbivorie

ROWS, COLS = 8, 8
# Origines (cm, monde 20 m, maison au centre 600-1400) : tout ce qui est au SUD de la
# maison est devant elle à l'écran ; l'ombre, elle, est au NORD (derrière le mur :
# touche H pour la maison transparente, ou Page↑ pour tourner la vue).
OX_SOLEIL_SEC, OX_SOLEIL_ARROSE, OY_SUD = 150.0, 600.0, 1450.0
OX_OMBRE, OY_OMBRE = 800.0, 200.0          # rangée 7 = pied du mur nord (y 550-600)
OX_AUTOMNE, OY_AUTOMNE = 1450.0, 1450.0

HUM_SEC = 0.1           # sable sec : `soif` ≈ 1 (stomates fermés)
HUM_ARROSE = 1.8        # terre gorgée : la pluie d'été ne la fait pas passer sous 0,5
LITIERE_PAILLIS = 3.0   # masse de litière : tient l'automne malgré la décomposition
COLS_TRIO = (2, 4, 6)   # trois pieds par décor, espacés d'un plot


def _trio(tile, rang: int, cls=Basil, repiquee: bool = False) -> None:
    for c in COLS_TRIO:
        p = tile.add_plant(cls, rang, c)
        if repiquee:
            # ACCÉLÉRATION (patron `vieillir`) : une rosette déjà formée, comme un plant
            # repiqué. Sur sable sec, au-dessus de sa limite de chaleur, un semis de
            # mâche ne passe jamais le stade semis (2 cm) : on ne verrait pas sa feuille.
            p.advance_stage()


def niche_thermique():
    """Banc « niche thermique » (⑤) : canicule (soleil sec / arrosé / ombre) et
    automne (basilic nu / paillé / voilé, mâche, seigle)."""
    tiles, ecos = [], {}

    def tuile(nom, sol, ox, oy, hum):
        tile, eco = build_banc_tile(nom, sol, ROWS, COLS, ox, oy,
                                    humidite=hum, fertilite=1.0, microbiome=0.4)
        # Instrument d'observation : sans ce garde l'herbivorie emporte les pieds
        # isolés en quelques semaines (patron `lignees`, D127).
        sans_herbivorie(eco)
        tiles.append(tile)
        ecos[tile.tile_id] = eco
        return tile, eco

    # (b) Canicule : même espèce, trois décors.
    sec, _ = tuile("SOLEIL_SEC", "sable", OX_SOLEIL_SEC, OY_SUD, HUM_SEC)
    _trio(sec, 4, CornSalad, repiquee=True)
    arrose, _ = tuile("SOLEIL_ARROSE", "terre", OX_SOLEIL_ARROSE, OY_SUD, HUM_ARROSE)
    _trio(arrose, 4, CornSalad, repiquee=True)
    ombre, _ = tuile("OMBRE_NORD", "sable", OX_OMBRE, OY_OMBRE, HUM_SEC)
    _trio(ombre, ROWS - 1, CornSalad, repiquee=True)

    # (a) Automne-hiver : une rangée par traitement, terre fraîche.
    automne, eco = tuile("AUTOMNE", "terre", OX_AUTOMNE, OY_AUTOMNE, 1.2)
    _trio(automne, 0)                                   # basilics sol nu
    _trio(automne, 2)                                   # basilics paillés
    for c in COLS_TRIO:
        eco.deposer_litiere(2, c, "herbace", LITIERE_PAILLIS)
    _trio(automne, 4)                                   # basilics voilés
    for c in COLS_TRIO:
        eco.poser_couvert(4, c, VOILE_COUVERT, RAYON_VOILE_PLOTS)   # = geste poser_voile
    _trio(automne, 6, CornSalad)                        # mâches
    for c in (1, 3, 5, 7):
        automne.add_plant(Rye, 7, c)                    # seigles (rang du fond)
    return monde(tiles, ecos, banque=banque_de("basilic", "mache", "seigle", par_espece=3))


def post_init(game_state: dict, player: str) -> None:
    """Coupe la germination FÉRALE (`feral_off`, patron du monde « propre ») : sur le
    sable sec, des dizaines de levées spontanées meurent de soif et couvrent la scène
    de squelettes — on ne verrait plus les trois mâches. Les grains PLANTÉS au F5
    lèvent toujours. Hors tick → golden intact (jamais appelé pour smoke/full)."""
    game_state["feral_off"] = True
