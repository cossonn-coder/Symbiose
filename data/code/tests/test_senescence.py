"""
SYMBIOSE — tests/test_senescence.py
Test LONG, lancé À LA DEMANDE (hors smoke test).

Récupère la couverture de la sénescence du pommier (~70 ans) qui a quitté le
golden quand celui-ci est devenu un smoke test rapide (sprint maison, tronçon 1,
décision Q4). Plutôt qu'un hash global gonflé, c'est une assertion de
COMPORTEMENT, robuste et lisible : un pommier laissé vieillir finit par mourir
de sénescence, dans la fenêtre d'âge attendue (au-delà de SENESCENCE_ONSET ×
longévité, sans dépasser de beaucoup la longévité).

Déterministe : la mort par sénescence est tirée via `_hash_noise` (pas de RNG).

Lancement (depuis data/code/) :
  python3 -m tests.test_senescence
"""

import sys

from world import Tile
from plants import AppleTree
from fields import init_eco, SENESCENCE_ONSET
from sim.engine import Engine

MAX_YEARS = 110   # garde-fou : longévité 70 ans → mort attendue bien avant


def run_until_apple_death():
    """Fait vieillir un pommier précis (position (0,0)) jusqu'à SA mort ; renvoie
    (cause, âge_ans). La cause est lue dans le log de la semaine de décès, ciblé
    sur SON identité « nom@(0, 0) » — la succession/reproduction peut faire mourir
    d'AUTRES plantes de sénescence, il ne faut pas les confondre avec la nôtre.
    Tuile 6×6 terre, humidité de CONFORT (1.5) : assez d'espace racinaire et
    d'eau pour que le pommier vieillisse SANS mourir d'un stress hydrique — ni
    par le BAS (sécheresse) ni par le HAUT (asphyxie, modèle eau Session B :
    sur argile gorgée hum→3.0 soutenu, le pommier mourrait asphyxié à ~27 ans,
    bien avant la sénescence). On isole donc la sénescence (age-based) sur un sol
    drainant à humidité médiane, entre les deux seuils de stress.
    Petit monde quand même → test rapide (~20 s) malgré l'horizon ~60 ans."""
    tile = Tile(tile_id="T0", soil_type="terre", grid_rows=6, grid_cols=6)
    eco = init_eco("T0", 6, 6, humidite=1.5, fertilite=1.2, microbiome=0.3)
    # Isolation de la sénescence : on COUPE la succession adventice sur cette
    # tuile. Depuis le sprint compétition intra-plot, le verrou d'occupation est
    # levé et les adventices peuvent coloniser DENSÉMENT les plots du pommier ;
    # une vingtaine d'adventices vivaces (Poa fibreuse, pissenlit à pivot) entre
    # alors en compétition hydrique avec le pommier solitaire et le tue vers
    # ~7 ans — comportement émergent légitime de la compétition, mais qui défait
    # l'ISOLATION voulue par ce test (vérifier la VOIE de mort par sénescence en
    # vieillissant un arbre seul). On neutralise donc la germination spontanée
    # ici (double de test), comme on a déjà choisi l'humidité médiane pour écarter
    # les deux stress hydriques. La compétition, elle, est couverte par
    # tests/test_competition.py.
    eco.seed_bank.germination_candidates = lambda *a, **k: []
    apple = tile.add_plant(AppleTree, 3, 3)
    tag = f"{apple.name}@{apple.position}"   # identité exacte dans les logs
    game_state = {
        "tiles": [tile], "eco": {"T0": eco}, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
    }
    engine = Engine(game_state)

    for _ in range(MAX_YEARS * 52):
        log = engine.tick_semaine()
        if not apple.is_alive:        # NOTRE pommier vient de mourir cette semaine
            cause = "autre"
            for line in log:
                if tag in line and "meurt de sénescence" in line:
                    cause = "senescence"
                    break
            return cause, apple.age_years
        game_state["log"].clear()
    return "vivant", apple.age_years   # jamais mort dans l'horizon (anomalie)


def test_apple_dies_of_senescence():
    L = AppleTree.longevity()              # 70 ans
    onset = SENESCENCE_ONSET * L           # 49 ans : début de la pression de déclin
    cause, age = run_until_apple_death()
    assert cause == "senescence", f"cause de mort inattendue : {cause} (âge {age:.1f} ans)"
    assert onset <= age <= 1.6 * L, (
        f"mort à {age:.1f} ans hors fenêtre attendue [{onset:.0f}, {1.6*L:.0f}]")
    print(f"[senescence] PASS — pommier mort de sénescence à {age:.1f} ans "
          f"(longévité {L:.0f}, onset {onset:.0f})")


if __name__ == "__main__":
    try:
        test_apple_dies_of_senescence()
    except AssertionError as e:
        print(f"[senescence] FAIL — {e}")
        sys.exit(1)
    sys.exit(0)
