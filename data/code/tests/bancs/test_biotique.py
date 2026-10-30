"""
SYMBIOSE — tests/bancs/test_biotique.py
Oracles des bancs BIOTIQUES (tronçon ④) : infestation ravageur / verger en
floraison / semis tempéré. Tranchent D47-C3 (criblage), C4 (chaîne floraison),
C5 (germination Solanaceae).

Chaque oracle monte le banc via SA fabrique, simule quelques semaines, puis lit
soit les SIGNES foliaires comme la vue (`signes_du_plot`), soit l'état moteur réel
(fruits, butineurs, plantules). Vert + écran muet ⇒ bug rendu C# (tri D47).

Usage (depuis data/code/) : python3 -m tests.bancs.test_biotique
"""
import statistics

from bancs import BANCS
from sim.engine import Engine
from .oracle import run_banc, run_banc_trace, signes_du_plot, SEED

_results = []

# Fenêtre d'observation du banc d'étalement floral : on démarre en fin de printemps
# (semaine 16), quand la porte PHOTOPÉRIODIQUE de la phacélie s'ouvre (jour ≥ 13.5 h),
# et on suit 16 semaines d'été — le temps que les lignées franchissent chacune leur
# seuil de forçage floral. Départ hors saison = fleurs jamais ouvertes (jour trop
# court), d'où ce démarrage estival (l'oracle décide QUAND observer).
ETAL_WEEK_DEPART = 5
ETAL_SEMAINES = 16
ETAL_SEUIL_OUVERTURE = 0.5      # `floraison > 0.5` = fleur franchement ouverte
ETAL_MIN_SEMAINES = 3          # étalement RÉEL : ≥ 3 semaines de franchissement distinctes


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK  " if cond else "FAIL"
    print(f"  [{flag}] {name}" + (f" — {detail}" if detail else ""))


def test_infestation_ravageur():
    """Deux basilics jumeaux ; l'infesté (densité `puceron` forcée) montre le signe
    `ravageurs` (limbe criblé) en restant vivant, le témoin reste sain. Tranche
    D47-C3 : le criblage observé est-il RÉEL (oui, le moteur l'émet) ou un artefact
    de rendu ? Observation TÔT (2 sem) : le forçage-pulse décroît ensuite (hiver)."""
    game_state, _ = run_banc("infestation_ravageur", semaines=2)
    infeste, temoin = game_state["tiles"]
    hote, control = infeste.plants[0], temoin.plants[0]
    s_hote = signes_du_plot(game_state, hote)
    s_ctrl = signes_du_plot(game_state, control)
    check("ravageur — hôte infesté VIVANT", hote.is_alive, f"alive={hote.is_alive}")
    check("ravageur — signe `ravageurs` sur l'hôte infesté", "ravageurs" in s_hote,
          f"signes={sorted(s_hote)}")
    check("ravageur — témoin SANS `ravageurs`", "ravageurs" not in s_ctrl,
          f"signes={sorted(s_ctrl)}")
    check("ravageur — témoin vivant", control.is_alive, f"alive={control.is_alive}")


def test_verger_floraison():
    """Verger de pommiers mûrs en pleine floraison + abeilles : la fanaison noue des
    fruits via le pollen déposé par les butineurs. Tranche D47-C4 : sur un monde
    IDÉAL, chaque maillon de la chaîne floraison→pollen→butineurs→nouaison→fruits
    tient-il ? On trace les butineurs (transitoires, présents seulement pendant la
    floraison) et on lit les fruits noués à la fin."""
    def observe(gs, eng):
        eco = next(iter(gs["eco"].values()))
        plants = gs["tiles"][0].plants
        return {"butineurs": len(eco.foragers or []),
                "fruits": sum(len(p.fruits) for p in plants)}
    game_state, _, traces = run_banc_trace("verger_floraison", semaines=6,
                                           observe=observe)
    arbres = [p for p in game_state["tiles"][0].plants if p.plant_class.name == "Pommier"]
    max_butineurs = max(t["butineurs"] for t in traces)
    fruits_fin = traces[-1]["fruits"]
    check("verger — pommiers vivants", all(a.is_alive for a in arbres),
          f"vivants={sum(a.is_alive for a in arbres)}/{len(arbres)}")
    check("verger — butineurs présents pendant la floraison (maillon pollinisateurs)",
          max_butineurs > 0, f"max butineurs={max_butineurs}")
    check("verger — nouaison → fruits (chaîne complète)", fruits_fin > 0,
          f"fruits={fruits_fin}")


def test_semis_tempere():
    """Tomate ET poivron plantés sur une tuile paillée à niche favorable : mildiou
    familial et froid neutralisés (paillage saturé), succession isolée → les grains
    lèvent et survivent. Tranche D47-C5 : « les Solanaceae ne lèvent pas » ne vient
    PAS de la porte de `planter` (elles lèvent ici), mais de la carte `full`.

    Observé en PLEIN ÉTÉ (`week_depart=20`, cœur de `SAISONS["ete"]`=14..26) : depuis
    la germination thermique, la levée exige un sol chaud, et c'est la saison qui la
    fournit (T_air chaude → T_sol dans la fenêtre du poivron, t_germ_opt=24)."""
    game_state, _ = run_banc("semis_tempere", semaines=8, week_depart=20)
    vivantes = [p.plant_class.name for p in game_state["tiles"][0].plants if p.is_alive]
    check("semis — au moins 1 tomate vivante", "Tomate" in vivantes,
          f"vivantes={vivantes}")
    check("semis — au moins 1 poivron vivant", "Poivron" in vivantes,
          f"vivantes={vivantes}")


def _dates_de_floraison():
    """Monte `etalement_floraison` en plein été et relève, pour CHAQUE pied, la
    PREMIÈRE semaine où `floraison > 0.5` (franchissement d'ouverture). Renvoie la
    liste triée de ces semaines de franchissement. Reproduit le câblage `cmd_init`
    (mêmes clés `game_state`, seed serveur) pour un état bit-identique à Godot."""
    tiles, ecos, house, banque = BANCS["etalement_floraison"]()
    game_state = {
        "tiles": tiles, "eco": ecos, "scores": {},
        "current_player": "joueur_1", "week": ETAL_WEEK_DEPART, "log": [],
        "house": house, "seed": SEED, "player_seed_bank": banque,
    }
    engine = Engine(game_state)
    plants = [p for tile in tiles for p in tile.plants]
    franchissement = {}
    for w in range(ETAL_SEMAINES):
        engine.tick_semaine()
        game_state["log"].clear()
        for i, p in enumerate(plants):
            if i not in franchissement and p.is_alive \
                    and p.floraison > ETAL_SEUIL_OUVERTURE:
                franchissement[i] = ETAL_WEEK_DEPART + w
    return sorted(franchissement.values())


def test_etalement_floraison():
    """Tapis mono-espèce de phacélies aux lignées `phenologie_florale` étalées : les
    dates de franchissement de floraison se RÉPARTISSENT sur plusieurs semaines (S2
    fermé). Tranche « floraison synchronisée » : sans le gène, tous ouvriraient la
    MÊME semaine (créneau unique, variance nulle) ; avec, l'étalement ÉMERGE du seuil
    de forçage floral propre à chaque lignée. Tendances/bornes, pas de hash figé."""
    dates = _dates_de_floraison()
    check("étalement — au moins un pied fleurit dans la fenêtre", len(dates) > 0,
          f"n_franchissements={len(dates)}")
    semaines_distinctes = sorted(set(dates))
    check("étalement — franchissements RÉPARTIS sur ≥ 3 semaines (pas un créneau)",
          len(semaines_distinctes) >= ETAL_MIN_SEMAINES,
          f"semaines={semaines_distinctes}")
    variance = statistics.pvariance(dates) if len(dates) > 1 else 0.0
    check("étalement — variance des dates NON NULLE (désynchronisation)",
          variance > 0.0, f"variance={variance:.3f}, étendue={max(dates)-min(dates)}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Oracles bancs biotiques (tronçon ④)")
    print("=" * 60)
    test_infestation_ravageur()
    test_verger_floraison()
    test_semis_tempere()
    test_etalement_floraison()
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
