"""
SYMBIOSE — bancs/mesure_nouaison.py
BANC DE MESURE (hors golden, hors registre F5) : instrumente la chaîne
floraison → butineurs → `pollen_recu` → `frac_nouaison` d'un pommier mûr, sous le
monde RÉEL du jeu (`build_world_full`, mêmes tuiles/faune/pré-vieillissement que
la config "full" du serveur, seed 42). But : MESURER la dose de pollen qu'accumule
un fruitier bien placé AVANT de tuner le levier de nouaison (D86 secondaire,
démarche perf-first : mesure d'abord, calibrage ensuite).

Ce n'est PAS un banc F5 (pas de fabrique dans `BANCS[]`) mais un script de
diagnostic exécutable — sœur de `tools/diag_population.py`. Il ne touche à AUCUNE
mécanique : il déroule le moteur et LIT `plant.floraison` / `plant.pollen_recu`
chaque semaine. `pollen_recu` étant remis à 0 à la nouaison (`_tick_fruits`), on
enregistre le PIC atteint juste avant la remise à zéro = la dose intégrée sur
toute la fenêtre de floraison, puis on la passe dans `frac_nouaison` pour lire la
fraction de sites qui nouent.

Usage (depuis data/code/) :
  python3 -m bancs.mesure_nouaison            # 2 années, seed 42
  python3 -m bancs.mesure_nouaison 3 7        # 3 années, seed 7
"""
from __future__ import annotations
import sys

from main import build_world_full
from sim.engine import Engine
from sim.engine.decompo import frac_nouaison, POLLEN_DEMI
from fields import POLLINATOR_NAMES
from sim import vigueur as VIG
from sim.seeds import PlayerSeedBank


def _dens_pollinisateurs(eco) -> str:
    """Densité moyenne de chaque type de pollinisateur sur la tuile (lecture de
    `eco.populations`) — pour voir SI des butineurs sont actifs pendant la
    floraison du pommier (une densité nulle = aucun agent échantillonné = 0 dépôt,
    indépendamment de tout calibrage de dose)."""
    out = []
    for name in POLLINATOR_NAMES:
        f = eco.populations.get(name) if eco.populations else None
        if f is None:
            continue
        n = f.rows * f.cols
        m = sum(f.data[r][c] for r in range(f.rows) for c in range(f.cols)) / n
        if m > 1e-4:
            out.append(f"{name[:4]}={m:.3f}")
    return " ".join(out) or "—"


def _monde_full():
    """Monde "full" du serveur : 8 tuiles plantées + maison + pommier verger,
    fruitiers pré-vieillis à `maturity_years` (comme `commands.cmd_init` config
    "full") → le pommier fleurit/noue dès l'année 1. Retourne (game_state, engine,
    pommier)."""
    tiles, ecos, _aux, house = build_world_full()
    for tile in tiles:
        for p in tile.plants:
            if getattr(p.plant_class, "fruitier", False):
                p.age_years = float(p.plant_class.maturity_years)
    game_state = {
        "tiles": tiles, "eco": ecos, "house": house, "scores": {},
        "current_player": "joueur_1", "week": 1, "log": [],
        "player_seed_bank": PlayerSeedBank(),
    }
    VIG.ensure_player(game_state, "joueur_1")
    engine = Engine(game_state)
    pommier = next(p for t in tiles for p in t.plants
                   if p.plant_class.__name__ == "AppleTree")
    tile_pom = next(t for t in tiles if pommier in t.plants)
    return game_state, engine, pommier, ecos[tile_pom.tile_id]


def mesurer(n_years: int = 2, seed_ignore: int | None = None) -> None:
    """Déroule le monde full `n_years` années et journalise, pour le pommier
    verger, sa `floraison` et son `pollen_recu` chaque semaine. Détecte les
    NOUAISONS (chute de `pollen_recu` vers 0 après un pic) et rapporte la dose de
    pic + la `frac` obtenue = ce que tunerait le levier `POLLEN_DEMI` / débit."""
    game_state, engine, pommier, eco_pom = _monde_full()
    print(f"Pommier verger @{pommier.position} (tuile) — "
          f"mode pollinisation={pommier.plant_class.pollination_mode}, "
          f"maturity_years={pommier.plant_class.maturity_years}")
    print(f"POLLEN_DEMI actuel = {POLLEN_DEMI}\n")

    # On enveloppe `_tick_fruits` pour LIRE la dose `pollen_recu` À L'ENTRÉE du pas
    # (donc APRÈS le dépôt des butineurs du même tick, AVANT la remise à 0) — c'est
    # la dose EXACTE que voit la nouaison. Sans ce hook on ne verrait que la valeur
    # post-reset (0). Instrument READ-ONLY : on ne modifie pas le comportement.
    orig = engine._tick_fruits.__func__
    journal = {"wiy": 0}

    def _wrap(self, tile, eco, wiy):
        # On ne journalise QUE l'appel sur la tuile qui porte le pommier — sinon un
        # appel de tuile ULTÉRIEURE relit `pollen_recu` déjà remis à 0 par la
        # nouaison de la vraie tuile → dose faussée. (`_tick_fruits` est appelé une
        # fois par tuile ; le pommier n'est que sur l'une d'elles.)
        mien = pommier in tile.plants
        pr_avant = pommier.pollen_recu
        af_avant = getattr(pommier, "a_fleuri", False)
        nf_avant = len(pommier.fruits)
        out = orig(self, tile, eco, wiy)
        if mien:
            from plants import organ_sites
            journal.update(wiy=wiy, pr=pr_avant, af=af_avant,
                           fl=pommier.floraison, nf=len(pommier.fruits),
                           sites=len(organ_sites(pommier)),
                           noue=(len(pommier.fruits) != nf_avant))
        return out
    engine._tick_fruits = _wrap.__get__(engine, type(engine))

    print(f"{'an':>3} {'wiy':>4} {'floraison':>10} {'pollen(dose)':>13} "
          f"{'a_fleuri':>9} {'sites':>6} {'frac':>6} {'fruits':>7}")
    for y in range(1, n_years + 1):
        for _ in range(52):
            engine.tick_semaine()
            j = journal
            fl, pr, nf = j["fl"], j["pr"], j["nf"]
            if fl > 0.01 or pr > 0.001 or j["noue"] or (nf > 0 and j["wiy"] < 40):
                print(f"{y:>3} {j['wiy']:>4} {fl:>10.3f} {pr:>13.4f} "
                      f"{str(j['af']):>9} {j.get('sites', 0):>6} "
                      f"{frac_nouaison(pr):>6.3f} {nf:>7}   "
                      f"{_dens_pollinisateurs(eco_pom)}")
            if j["noue"]:
                print(f"    → NOUAISON an {y} @S{j['wiy']} : dose vue "
                      f"= {pr:.4f} pollen ; frac = {frac_nouaison(pr):.3f} ; "
                      f"sites = {j.get('sites', 0)} ; {nf} fruits noués")
        game_state["log"].clear()


if __name__ == "__main__":
    ny = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    mesurer(ny)
