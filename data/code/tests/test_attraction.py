"""
SYMBIOSE — tests/test_attraction.py
Sous-sprint ④ (décompo·compost) — attraction animale par le fruit tombé.

Le fruit tombé (parcelle `fruit` déposée par engine._tick_fruits à la chute des
sur-mûrs) émet un signal selon son `age_sem`, AJOUTÉ à la capacité de charge :
  - FRAIS (age bas)  → nourrit l'`auxiliaire` (frugivores) ;
  - POURRI (age haut) → appelle le `ravageur` DOMINANT + une PETITE fraction
    `auxiliaire` (décomposeurs).
Pas de 5ᵉ guilde ; le fruit ne touche JAMAIS la plante (philo #2).

Deux niveaux de vérification :
  A. MODÈLE PUR — les grilles de signal `_aux_fruit_signal` / `_rav_fruit_signal`
     (déterministes, exactes) : composition frais/pourri, dominance ravageur,
     monotonie, mise à l'échelle par la masse, NEUTRALITÉ (0 fruit → 0 partout).
  B. INTÉGRÉ — après N ticks de population, le plot-fruit dépasse un plot-témoin
     du même eco (spatialement uniforme hors fruit) ; déterminisme h1==h2 ;
     neutralité (eco sans fruit → champ uniforme).

Lancement (depuis data/code/) :
  python3 -m tests.test_attraction
"""

import sys

from world import Tile
from fields import init_eco
from fields.population import (
    _aux_fruit_signal, _rav_fruit_signal,
    FRUIT_SIGNAL_REF, FRAC_AUX_POURRI,
)

ROWS, COLS = 6, 8
FRUIT_R, FRUIT_C = 2, 3      # plot où l'on dépose le fruit
CTRL_R, CTRL_C = 4, 6        # plot témoin (sans fruit), même eco uniforme
EPS = 1e-9


def _make_eco():
    """Eco minimal, spatialement UNIFORME (aucune plante, aucune rondelle) :
    tout écart entre deux plots après tick vient du seul fruit déposé."""
    tile = Tile(tile_id="TA", soil_type="terre")
    eco = init_eco("TA", ROWS, COLS, humidite=1.5, fertilite=1.0, microbiome=0.3)
    return tile, eco


def _deposit_fruit(eco, r, c, masse, age_sem):
    """Dépose une parcelle `fruit` puis force son `age_sem` (contrôle du test)."""
    eco.deposer_litiere(r, c, "fruit", masse)
    for p in eco.litiere[r][c]:
        if p.tissu == "fruit":
            p.age_sem = age_sem
            return
    raise AssertionError("parcelle fruit non déposée")


def _tick(tile, eco, weeks):
    """Ticke seulement les populations (age_sem du fruit reste fixe — contrôle)."""
    for _ in range(weeks):
        eco.tick_populations(tile, tile.plants)


def _check(cond, label):
    if not cond:
        print(f"[attraction] ÉCHEC : {label}")
        raise SystemExit(1)
    print(f"[attraction] OK : {label}")


# ---------------------------------------------------------------------------
# A. MODÈLE PUR — grilles de signal (déterministes, exactes)
# ---------------------------------------------------------------------------

def test_signal_frais_va_a_l_auxiliaire():
    tile, eco = _make_eco()
    _deposit_fruit(eco, FRUIT_R, FRUIT_C, FRUIT_SIGNAL_REF, age_sem=0.0)
    aux = _aux_fruit_signal(eco, tile, tile.plants)
    rav = _rav_fruit_signal(eco, tile, tile.plants)
    _check(aux[FRUIT_R][FRUIT_C] > 0.0, "fruit frais → signal auxiliaire > 0")
    _check(abs(rav[FRUIT_R][FRUIT_C]) < EPS, "fruit frais → signal ravageur = 0")
    _check(abs(aux[CTRL_R][CTRL_C]) < EPS, "hors plot-fruit → signal nul (localité)")


def test_signal_pourri_ravageur_dominant():
    tile, eco = _make_eco()
    _deposit_fruit(eco, FRUIT_R, FRUIT_C, FRUIT_SIGNAL_REF, age_sem=12.0)
    aux = _aux_fruit_signal(eco, tile, tile.plants)[FRUIT_R][FRUIT_C]
    rav = _rav_fruit_signal(eco, tile, tile.plants)[FRUIT_R][FRUIT_C]
    _check(rav > 0.0, "fruit pourri → signal ravageur > 0")
    _check(aux > 0.0, "fruit pourri → fraction auxiliaire > 0 (décomposeurs)")
    _check(rav > aux, "fruit pourri → ravageur DOMINANT sur l'auxiliaire")


def test_signal_monotonie_age():
    """Ravageur croît avec l'âge ; auxiliaire (frugivore) décroît avec l'âge."""
    tile, eco = _make_eco()
    rav_par_age, aux_par_age = [], []
    for age in (0.0, 4.0, 8.0, 12.0):
        eco.litiere[FRUIT_R][FRUIT_C] = []   # purge le plot avant chaque dépôt
        _deposit_fruit(eco, FRUIT_R, FRUIT_C, FRUIT_SIGNAL_REF, age_sem=age)
        rav_par_age.append(_rav_fruit_signal(eco, tile, tile.plants)[FRUIT_R][FRUIT_C])
        aux_par_age.append(_aux_fruit_signal(eco, tile, tile.plants)[FRUIT_R][FRUIT_C])
    _check(rav_par_age == sorted(rav_par_age),
           "ravageur croît (monotone) avec l'âge du fruit")
    _check(aux_par_age[0] > aux_par_age[-1],
           "auxiliaire (frugivore) plus fort sur frais que sur pourri")


def test_signal_echelle_masse():
    """Un plus gros tas appelle plus fort (jusqu'à saturation à FRUIT_SIGNAL_REF)."""
    tile, eco = _make_eco()
    eco.litiere[FRUIT_R][FRUIT_C] = []
    _deposit_fruit(eco, FRUIT_R, FRUIT_C, FRUIT_SIGNAL_REF * 0.25, age_sem=0.0)
    petit = _aux_fruit_signal(eco, tile, tile.plants)[FRUIT_R][FRUIT_C]
    eco.litiere[FRUIT_R][FRUIT_C] = []
    _deposit_fruit(eco, FRUIT_R, FRUIT_C, FRUIT_SIGNAL_REF, age_sem=0.0)
    gros = _aux_fruit_signal(eco, tile, tile.plants)[FRUIT_R][FRUIT_C]
    _check(gros > petit, "signal auxiliaire ↑ avec la masse du tas")


def test_signal_neutralite_sans_fruit():
    """INVARIANT GOLDEN : zéro parcelle `fruit` → signal nul PARTOUT (terme=0)."""
    tile, eco = _make_eco()
    aux = _aux_fruit_signal(eco, tile, tile.plants)
    rav = _rav_fruit_signal(eco, tile, tile.plants)
    nul = all(abs(aux[r][c]) < EPS and abs(rav[r][c]) < EPS
              for r in range(ROWS) for c in range(COLS))
    _check(nul, "sans fruit → signal auxiliaire ET ravageur nuls partout")


# ---------------------------------------------------------------------------
# B. INTÉGRÉ — champ de population après ticks
# ---------------------------------------------------------------------------

def test_integre_frais_monte_auxiliaire():
    # Depuis ④c, le fruit FRAIS nourrit le MERLE (frugivore) : `_aux_fruit_signal`
    # repromu de signal additif en RESSOURCE du merle (`_merle_food_grid`). On lit
    # donc la catégorie `auxiliaire` (agrégat des 5 espèces, dont le merle).
    tile, eco = _make_eco()
    _deposit_fruit(eco, FRUIT_R, FRUIT_C, FRUIT_SIGNAL_REF, age_sem=0.0)
    _tick(tile, eco, 15)
    aux_plot = eco.category_density("auxiliaire", FRUIT_R, FRUIT_C)
    aux_ctrl = eco.category_density("auxiliaire", CTRL_R, CTRL_C)
    _check(aux_plot > aux_ctrl + 1e-4,
           "fruit frais → auxiliaire(plot) > auxiliaire(témoin) (via le merle)")


def test_integre_pourri_monte_ravageur():
    tile, eco = _make_eco()
    _deposit_fruit(eco, FRUIT_R, FRUIT_C, FRUIT_SIGNAL_REF, age_sem=12.0)
    _tick(tile, eco, 15)
    # « ravageur » est une CATÉGORIE (puceron/limace/doryphore, ④b) : le fruit pourri
    # alimente la spec `limace` (détritivore préf.). Côté auxiliaire (catégorie de 5
    # espèces, ④c), le fruit pourri appelle AUSSI le merle via la fraction pourri de
    # `_aux_fruit_signal` (FRAC_AUX_POURRI) repromue en ressource → légère hausse.
    rav_plot = eco.category_density("ravageur", FRUIT_R, FRUIT_C)
    rav_ctrl = eco.category_density("ravageur", CTRL_R, CTRL_C)
    _check(rav_plot > rav_ctrl + 1e-4,
           "fruit pourri → ravageur(plot) > ravageur(témoin)")
    aux_plot = eco.category_density("auxiliaire", FRUIT_R, FRUIT_C)
    aux_ctrl = eco.category_density("auxiliaire", CTRL_R, CTRL_C)
    _check(aux_plot > aux_ctrl + 1e-4,
           "fruit pourri → auxiliaire(plot) > témoin aussi (fraction décomposeurs, merle)")


def test_integre_pourri_plus_de_ravageur_que_frais():
    """Monotonie intégrée : pourri appelle plus de ravageur que frais."""
    t1, e1 = _make_eco(); _deposit_fruit(e1, FRUIT_R, FRUIT_C, FRUIT_SIGNAL_REF, 0.0)
    t2, e2 = _make_eco(); _deposit_fruit(e2, FRUIT_R, FRUIT_C, FRUIT_SIGNAL_REF, 12.0)
    _tick(t1, e1, 15); _tick(t2, e2, 15)
    rav_frais = e1.category_density("ravageur", FRUIT_R, FRUIT_C)
    rav_pourri = e2.category_density("ravageur", FRUIT_R, FRUIT_C)
    _check(rav_pourri > rav_frais, "ravageur(pourri) > ravageur(frais)")


def _digest(eco):
    out = []
    for g in ("puceron", "limace", "doryphore",
              "coccinelle", "chrysope", "carabe", "merle", "herisson",
              "abeille", "syrphe", "papillon", "vers_de_terre"):
        f = eco.populations[g]
        for r in range(f.rows):
            out.append(" ".join(f"{f.at_plot(r, c):.9f}" for c in range(f.cols)))
    return "\n".join(out)


def test_determinisme():
    def run():
        tile, eco = _make_eco()
        _deposit_fruit(eco, FRUIT_R, FRUIT_C, FRUIT_SIGNAL_REF, age_sem=5.0)
        _tick(tile, eco, 15)
        return _digest(eco)
    _check(run() == run(), "deux runs identiques → champs bit-identiques (déterminisme)")


def test_integre_neutralite_uniforme():
    """Sans fruit, l'eco uniforme reste uniforme : aucun signal parasite."""
    tile, eco = _make_eco()
    _tick(tile, eco, 15)
    for g in ("puceron", "limace", "doryphore",
              "coccinelle", "chrysope", "carabe", "merle", "herisson"):
        f = eco.populations[g]
        v0 = f.at_plot(FRUIT_R, FRUIT_C)
        uniforme = all(abs(f.at_plot(r, c) - v0) < EPS
                       for r in range(ROWS) for c in range(COLS))
        _check(uniforme, f"sans fruit → champ {g} spatialement uniforme")


def main():
    test_signal_frais_va_a_l_auxiliaire()
    test_signal_pourri_ravageur_dominant()
    test_signal_monotonie_age()
    test_signal_echelle_masse()
    test_signal_neutralite_sans_fruit()
    test_integre_frais_monte_auxiliaire()
    test_integre_pourri_monte_ravageur()
    test_integre_pourri_plus_de_ravageur_que_frais()
    test_determinisme()
    test_integre_neutralite_uniforme()
    print("[attraction] TOUS LES TESTS PASSENT")


if __name__ == "__main__":
    main()
