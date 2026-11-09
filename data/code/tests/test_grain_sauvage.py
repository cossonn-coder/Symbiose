"""
SYMBIOSE — tests/test_grain_sauvage.py
Tests ciblés du GRAIN SAUVAGE (sprint zoochorie ①, D42) : `GrainEnAttente` devient
le véhicule de toute graine sauvage (tombée, portée par une bête) — dormance jusqu'au
printemps suivant, péremption par viabilité d'espèce, plafond par plot — sans rien
changer aux graines plantées par le joueur.

Aucun producteur de grain sauvage n'existe encore (② et ④-⑥) : on dépose les grains
à la main et on appelle `succession` directement (labo, hors golden).

Couvre :
  (a) un grain déposé en été ne lève pas avant le printemps suivant, puis lève ;
  (b) un grain périmé disparaît sans lever ;
  (c) plafond : le 4ᵉ dépôt sauvage sur un plot est refusé (le joueur n'y compte pas) ;
  (d) un grain en dormance en tête ne bloque pas un grain éligible derrière ;
  (e) un grain `joueur` lève comme avant (contre-factuel figé sur l'ancien code).

Usage (depuis data/code/) :
  python3 -m tests.test_grain_sauvage
"""
import sys

from world import Tile
from plants import Tomato, PLANT_CATALOGUE
from fields import init_eco
from fields.seedbank import (GrainEnAttente, grain_sauvage, deposer_grain_sauvage,
                             GRAINS_SAUVAGES_MAX_PLOT)
from calendrier import wiy_de
from sim import actions as ACT
from sim import vigueur as V
from sim.seeds import Seed, PlayerSeedBank
from sim.succession import succession

SEED = 0x5EED
ETE = 20          # semaine absolue 20 = wiy 20 (≈ début août), année 1
PRINTEMPS_2 = 53  # wiy 1 de l'année 2 = premier printemps strictement après
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _monde(week=3):
    """Monde minimal à niche FAVORABLE (même recette que `test_planter`)."""
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    eco.lumiere.fill(1.0)
    eco.disturbance.fill(1.0)
    eco.soil_memory_deep.fill(0.0)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "joueur_1", "week": week, "log": [], "seed": SEED,
          "player_seed_bank": PlayerSeedBank()}
    return gs, tile, eco


def _premiere_levee(gs, tile, eco, w0, w1, pos=(2, 2)):
    """Semaine de la première plante vivante sur `pos`, ou None ; + logs cumulés."""
    logs = []
    for w in range(w0, w1):
        gs["week"] = w
        logs += succession(gs, tile, eco, w)
        if any(p.is_alive and p.position == pos for p in tile.plants):
            return w, logs
    return None, logs


def test_dormance():
    print("\n[a] dormance : déposé en été → ne lève qu'au printemps suivant")
    gs, tile, eco = _monde(ETE)
    g = grain_sauvage(Tomato, {}, {}, "merle", ETE, None, None)
    check("levee_des = premier printemps strictement après",
          g.levee_des == PRINTEMPS_2 and wiy_de(g.levee_des) == 1, f"levee_des={g.levee_des}")
    check("grain sauvage = férale (cultive=False)", g.cultive is False)
    check("clé catalogue portée", g.species == "tomate", g.species)
    check("péremption = dépôt + 1 an (défaut)", g.perime_a == ETE + 52, f"{g.perime_a}")
    g_print = grain_sauvage(Tomato, {}, {}, "chute", PRINTEMPS_2, None, None)
    check("déposé PILE au wiy 1 → printemps SUIVANT (strict)",
          g_print.levee_des == PRINTEMPS_2 + 52, f"{g_print.levee_des}")
    check("viabilité d'espèce lue (framboisier 5 ans)",
          grain_sauvage(PLANT_CATALOGUE["framboisier"], {}, {}, "merle", ETE, None, None).perime_a == ETE + 260)
    deposer_grain_sauvage(tile, 2, 2, g)
    w, logs = _premiere_levee(gs, tile, eco, ETE, PRINTEMPS_2 + 20)
    check("pas de levée avant le printemps suivant", w is not None and w >= PRINTEMPS_2,
          f"levée semaine {w}")
    check("log « semé par merle »", any("Levée (semé par merle)" in l for l in logs))


def test_peremption():
    print("\n[b] péremption : un grain périmé disparaît sans lever")
    gs, tile, eco = _monde(ETE)
    g = grain_sauvage(Tomato, {}, {}, "geai", ETE, None, None)
    g.perime_a = PRINTEMPS_2 - 1           # meurt juste avant sa sortie de dormance
    deposer_grain_sauvage(tile, 2, 2, g)
    w, _ = _premiere_levee(gs, tile, eco, ETE, PRINTEMPS_2 + 20)
    check("aucune levée", w is None, f"levée semaine {w}")
    check("grain purgé du plot", not tile.grains_en_attente.get((2, 2)))


def test_plafond():
    print("\n[c] plafond : le 4ᵉ dépôt sauvage est refusé")
    _, tile, _ = _monde()
    tile.grains_en_attente[(2, 2)] = [GrainEnAttente(species="tomate")]  # planté : hors plafond
    oks = [deposer_grain_sauvage(tile, 2, 2,
                                 grain_sauvage(Tomato, {}, {}, "merle", ETE + i, None, None))
           for i in range(GRAINS_SAUVAGES_MAX_PLOT + 1)]
    check("3 premiers acceptés", all(oks[:GRAINS_SAUVAGES_MAX_PLOT]), f"{oks}")
    check("4ᵉ refusé", oks[-1] is False)
    check("plot = 1 planté + 3 sauvages", len(tile.grains_en_attente[(2, 2)]) == 4)


def test_dormant_ne_bloque_pas():
    print("\n[d] un grain en dormance en tête ne bloque pas l'éligible derrière")
    gs, tile, eco = _monde(ETE)
    sauvage = grain_sauvage(Tomato, {}, {}, "merle", ETE, None, None)
    deposer_grain_sauvage(tile, 2, 2, sauvage)
    tile.grains_en_attente[(2, 2)].append(
        GrainEnAttente(species="tomate", cultive=False, semaine_depot=ETE))
    w, logs = _premiere_levee(gs, tile, eco, ETE, PRINTEMPS_2)
    check("le grain planté lève avant le printemps", w is not None and w < PRINTEMPS_2,
          f"levée semaine {w}")
    check("log « (planté) » inchangé", any("Levée (planté)" in l for l in logs))
    check("le grain sauvage dort toujours", tile.grains_en_attente[(2, 2)] == [sauvage])


# Contre-factuel (e) : semaine de levée du même scénario sous l'ANCIEN code
# (`grains[0]`, avant zoochorie ①), mesurée le 2026-11-09 par `git stash`.
SEMAINE_LEVEE_ANCIEN_CODE = 4


def test_joueur_inchange():
    print("\n[e] grain joueur : lève comme avant (contre-factuel)")
    gs, tile, eco = _monde(3)
    bank = gs["player_seed_bank"]
    bank.add(Seed(species="tomate", genes={"hauteur": 1.42}))
    V.ensure_player(gs, "joueur_1")
    ACT.planter(gs, "joueur_1", tile, eco, "tomate", 2, 2)
    g = tile.grains_en_attente[(2, 2)][0]
    check("défauts joueur (origine, levée 0, jamais périmé)",
          g.origine == "joueur" and g.levee_des == 0 and g.perime_a is None)
    w, _ = _premiere_levee(gs, tile, eco, 3, 30)
    check("même semaine de levée que l'ancien code",
          w == SEMAINE_LEVEE_ANCIEN_CODE, f"levée semaine {w}")


def main():
    test_dormance()
    test_peremption()
    test_plafond()
    test_dormant_ne_bloque_pas()
    test_joueur_inchange()
    ko = [n for n, ok in _results if not ok]
    print(f"\n{len(_results) - len(ko)}/{len(_results)} OK")
    sys.exit(1 if ko else 0)


if __name__ == "__main__":
    main()
