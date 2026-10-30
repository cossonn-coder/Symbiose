"""
SYMBIOSE — tests/test_couvertures.py
Couvertures posées : voile / cloche / ombrière (sprint effondrement météo ③).

Prouve que la PRÉPARATION atténue réellement l'effondrement (tronçon ①). On rejoue
le collapse CONNU (seed 12345, année 5 semaine 10 = `week=218`, une Grêle
d'intensité 2.0, `scope="local"`) : sous le même hiver catastrophe, les plots
DÉCOUVERTS s'effondrent tandis que les plots protégés d'un VOILE gardent un noyau
vivant — sans aucun bonus direct sur la plante (le voile relève un CHAMP du milieu,
`eco.couvert_pose`, lu par la grêle médiée). Deux garde-fous accompagnent :
  • NEUTRALITÉ : un `eco` neuf n'alloue AUCUN champ de couverture (None) → les
    readers rendent 0.0 → golden NEUTRE par construction.
  • MILIEU (philo #1/#2) : les gestes écrivent `couvert_pose`/`ombre_pose`, et
    l'ombrière ATTÉNUE bien la lumière-sol (`appliquer_ombrieres`).

Lancement : python3 -m tests.test_couvertures   (depuis data/code/)
"""

from world import Tile
from plants import Basil
from fields import init_eco
from sim.engine import Engine
from sim.seeds import semer_fondateur
from sim.weather import patch_local
from sim.actions.couvertures import (
    VOILE_COUVERT, poser_voile, poser_cloche, poser_ombriere,
)

SEED = 12345          # seed du collapse connu (conception §0/§1.3)
WEEK = 218           # année 5, semaine 10 → Grêle i=2.0 scope="local" (D122 ③ : ex-1310)
ROWS, COLS = 16, 11   # tuile du scénario de conception


def _tuile_semee():
    """Tuile ROWS×COLS nue, un semis de Basilic (tissu tendre, cible de la grêle)
    sur chaque plot. Renvoie (tile, eco, plants)."""
    tile = Tile(tile_id="TX", soil_type="terre",
                grid_rows=ROWS, grid_cols=COLS, origin_x_cm=0.0, origin_y_cm=0.0)
    eco = init_eco("TX", ROWS, COLS, humidite=1.5, fertilite=1.0,
                   microbiome=0.3, soil_type="terre", heterogene=True)
    plants = [semer_fondateur(tile, Basil, r, c, 42)
              for r in range(ROWS) for c in range(COLS)]
    return tile, eco, plants


def _collapse(voile: bool = False):
    """Joue LE tick du collapse (seed 12345, week 218). Si `voile`, on tend un voile
    (écran `couvert_pose`) sur TOUS les plots AVANT le tick. Renvoie (plants, eco)."""
    tile, eco, plants = _tuile_semee()
    if voile:
        for r in range(ROWS):
            for c in range(COLS):
                eco.poser_couvert(r, c, VOILE_COUVERT, 0.0)
    game_state = {"tiles": [tile], "eco": {"TX": eco}, "scores": {},
                  "current_player": "j", "week": WEEK, "log": [], "seed": SEED}
    Engine(game_state).tick_semaine()
    return plants, eco


def test_voile_attenue_le_collapse():
    """Cœur du tronçon : sous la MÊME grêle, les plots du PATCH voilés gardent un
    noyau vivant là où, découverts, ils s'effondrent. On mesure sur le patch frappé
    (hors patch, la grêle n'agit pas → sans intérêt discriminant)."""
    dans_patch = patch_local(SEED, WEEK, ROWS, COLS)

    nus, _   = _collapse(voile=False)
    voiles, _ = _collapse(voile=True)

    surv_nus = sum(p.is_alive for p in nus if dans_patch(*p.position))
    surv_voile = sum(p.is_alive for p in voiles if dans_patch(*p.position))
    total_patch = sum(1 for p in nus if dans_patch(*p.position))
    assert total_patch > 0, "le patch doit frapper des plots (collapse connu)"

    # Sans voile l'exposé encaisse des pertes ; avec voile, STRICTEMENT plus de
    # survivants dans le patch (la préparation atténue — aucun chiffre gravé, monotonie).
    assert surv_nus < total_patch, "sans voile, le patch doit perdre des semis"
    assert surv_voile > surv_nus, (
        f"le voile devrait sauver des semis du patch : voilé {surv_voile} "
        f"> nu {surv_nus} (sur {total_patch})")

    # Déterminisme (philo #3) : rejouer donne le même verdict.
    voiles2, _ = _collapse(voile=True)
    assert [p.is_alive for p in voiles2] == [p.is_alive for p in voiles]


def test_eco_neuf_est_neutre():
    """NEUTRALITÉ (golden) : un `eco` neuf n'alloue aucun champ de couverture, et les
    readers rendent 0.0 partout → aucun terme ne bouge tant que rien n'est posé."""
    _, eco, _ = _tuile_semee()
    assert eco.couvert_pose is None and eco.ombre_pose is None
    assert eco.couvert_at(3, 4) == 0.0 and eco.ombre_at(3, 4) == 0.0
    # appliquer_ombrieres sans ombrière = no-op strict (lumière-sol intacte).
    avant = eco.lumiere.data[3][4]
    eco.appliquer_ombrieres()
    assert eco.lumiere.data[3][4] == avant


def test_gestes_ecrivent_le_milieu():
    """MILIEU (philo #1/#2) : chaque geste écrit un CHAMP, jamais la plante. Le voile
    et la cloche relèvent `couvert_pose` ; l'ombrière pose `ombre_pose` et atténue
    bien la lumière-sol (via `appliquer_ombrieres`)."""
    _, eco, _ = _tuile_semee()
    gs = {"current_player": "j"}

    assert poser_voile(gs, "j", eco, 5, 5) is True
    assert eco.couvert_at(5, 5) > 0.0          # écran posé sur la zone

    assert poser_cloche(gs, "j", eco, 1, 1) is True
    assert eco.couvert_at(1, 1) > 0.0          # écran individuel (1×1)

    _, eco2, _ = _tuile_semee()
    lum_avant = eco2.lumiere.data[8][6]
    assert poser_ombriere(gs, "j", eco2, 8, 6) is True
    assert eco2.ombre_at(8, 6) > 0.0
    eco2.appliquer_ombrieres()
    assert eco2.lumiere.data[8][6] < lum_avant  # l'ombrière tamise la lumière-sol


def main():
    test_voile_attenue_le_collapse()
    test_eco_neuf_est_neutre()
    test_gestes_ecrivent_le_milieu()
    print("[couvertures] PASS — voile atténue le collapse + neutralité + gestes-milieu")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
