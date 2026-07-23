"""
SYMBIOSE — tests/test_automate_determinisme.py
Verrous de DÉTERMINISME du jardinier automate (tronçon ①, philo #3).
Spec : docs/joueur/automate/conception_jardinier_automate.md §10 + kickoff
sprints/joueur/automate/sprint_jardinier_auto/01_socle.md.

Trois propriétés :
  A. REJEU IDENTIQUE — deux moteurs neufs, même seed, joués N ticks avec un
     automate frais chacun → journaux JSON strictement égaux (aucun RNG, tri
     stable à clé totale).
  B. AUTOMATE OFF = GOLDEN — le simple fait d'importer le paquet ne bouge pas le
     hash golden (l'automate n'est jamais dans le tick : invariant H2). On
     recalcule le hash golden APRÈS import et on le compare à la référence figée.
  C. PAS D'EFFET DE BORD — ticker un moteur SANS appeler l'automate ne crée jamais
     la clé de journal `automate_journal` (opt-in strict).

Usage (depuis data/code/) :
  python3 -m tests.test_automate_determinisme
"""
from __future__ import annotations
import json
from types import SimpleNamespace

from tools.jardinier_auto import (JardinierAutomate, LIBRE, BRIDE,
                                  marquer_jardin_cultive, Objectif, ajouter_objectif)
from tools.jardinier_auto.trace import CLE_JOURNAL, journal
from world.tile import Tile
from fields.ecofields import EcoFields
from plants.base import PlantInstance
from plants.catalogue import PLANT_CATALOGUE
from sim.seeds import PlayerSeedBank, Seed
from sim import maitrise_detection as MD, vigueur

_SEED = 0x5AB1057E
_WEEKS = 60
P = "joueur_1"

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _build_engine():
    """Monte le monde 'full' via SimServer (fabrique du F5), déterministe pour
    un seed donné."""
    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": "full", "seed": _SEED})
    assert rep.get("ok"), rep
    return srv.engine


def _jouer(weeks: int) -> list:
    """Un moteur neuf joué `weeks` ticks avec un automate LIBRE frais ; renvoie
    le journal consigné. On DÉCLARE le jardin initial cultivé (tutelle = cultivées,
    tronçon ②) pour que le journal soit non trivial — le marquage est déterministe
    (itération sur listes)."""
    engine = _build_engine()
    marquer_jardin_cultive(engine, engine.game_state["current_player"])
    automate = JardinierAutomate(LIBRE)
    for _ in range(weeks):
        engine.tick_semaine()
        automate.jouer_tick(engine)
    return journal(engine.game_state)


def test_rejeu_identique():
    j1 = _jouer(_WEEKS)
    j2 = _jouer(_WEEKS)
    s1, s2 = json.dumps(j1, sort_keys=True), json.dumps(j2, sort_keys=True)
    check("A. rejeu identique", s1 == s2,
          f"{len(j1)} entrées, journaux {'égaux' if s1 == s2 else 'DIVERGENTS'}")


def test_automate_off_golden():
    """Le paquet est déjà importé en tête de module. On recalcule le hash golden
    et on le compare à la référence figée : import ⇒ zéro effet sur le tick."""
    from tests.test_golden import compute_hash, HASH_FILE
    with open(HASH_FILE) as f:
        ref = f.read().strip()
    got = compute_hash()
    check("B. automate OFF = golden bit-identique", got == ref,
          f"{got[:16]}… vs {ref[:16]}…")


def test_pas_effet_de_bord():
    engine = _build_engine()
    for _ in range(4):
        engine.tick_semaine()          # AUCUN jouer_tick
    absent = CLE_JOURNAL not in engine.game_state
    check("C. pas d'effet de bord (opt-in strict)", absent,
          "clé de journal absente sans appel de l'automate")


# ---------------------------------------------------------------------------
# Tronçon ③ — planificateur BRANCHÉ dans la boucle : préemption survie, geste
# créatif exécuté/coupé, favoriser one-shot. Détermninisme préservé (philo #3).
# ---------------------------------------------------------------------------

def _toy(objectif, *, graine=None, cultivee=None, vigueur_courante=None):
    """Engine JOUET (Tile + EcoFields réels) : une EcoFields fraîche a `humidite=0`
    partout → la cultivée est en déficit HYDRIQUE → le cœur réactif propose `arroser`
    (survie). En parallèle, `graine` + plot libre → le planificateur propose un
    `planter` créatif. De quoi éprouver l'ARTICULATION des deux étages sur un tick."""
    tile = Tile(tile_id="t0", soil_type="terre")
    eco = EcoFields(tile_id="t0", rows=tile.grid_rows, cols=tile.grid_cols,
                    soil_type="terre")
    gs = {"current_player": P, "week": 5, "player_seed_bank": PlayerSeedBank(),
          "eco": {"t0": eco}}
    if graine:
        gs["player_seed_bank"].add(Seed(species=graine))
    if cultivee:
        sp, r, c = cultivee
        tile.plants.append(PlantInstance(plant_class=PLANT_CATALOGUE[sp], position=(r, c)))
        MD.marquer_replante(gs, P, "t0", r, c)
    if vigueur_courante is not None:
        vigueur.ensure_player(gs, P)
        gs["vigueur"][P]["courante"] = vigueur_courante
        gs["vigueur"][P]["max_base"] = 500.0
    ajouter_objectif(gs, objectif)
    return SimpleNamespace(tiles=[tile], game_state=gs, week=gs["week"],
                           _eco=lambda t: gs["eco"][t.tile_id])


def test_objectif_bout_en_bout_deterministe():
    """Un run RÉEL (monde full) avec objectif `recolter tomate` + graine en banque →
    le planificateur émet des gestes créatifs (planter) ; deux rejeux à entrées
    égales → journaux strictement identiques (oracle du ①, articulation ③)."""
    def run():
        engine = _build_engine()
        gs = engine.game_state
        marquer_jardin_cultive(engine, gs["current_player"])
        gs.setdefault("player_seed_bank", PlayerSeedBank()).add(Seed(species="tomate"))
        ajouter_objectif(gs, Objectif("recolter", 3, "tomate", "obj_tom"))
        auto = JardinierAutomate(LIBRE)
        for _ in range(30):
            engine.tick_semaine()
            auto.jouer_tick(engine)
        return json.dumps(journal(gs), sort_keys=True)
    j1, j2 = run(), run()
    # Un geste CRÉATIF porte `facteur_limitant == "advenir"` (planter/acheter/
    # favoriser) — on prouve que l'étage créatif a bien TOURNÉ end-to-end (le verbe
    # exact dépend du monde : ici tomate déjà cultivée → favoriser, pas planter).
    creatifs = '"facteur_limitant": "advenir"' in j1
    check("D. objectif bout-en-bout — 2 rejeux égaux", j1 == j2,
          "journaux égaux" if j1 == j2 else "DIVERGENTS")
    check("D. le planificateur a émis des gestes créatifs (advenir)", creatifs)


def test_preemption_budget():
    """Mode PAYÉ, budget serré (15 = coût d'un arrosage) : la survie (`arroser`, prio
    10-12) passe ; le `planter` créatif (prio 5) est COUPÉ → `geste_coupe {budget}` et
    la graine est CONSERVÉE (semis reporté, jamais au prix du vivant)."""
    obj = Objectif("recolter", 2, "haricot", "obj_har")
    engine = _toy(obj, graine="haricot", cultivee=("tomate", 5, 5), vigueur_courante=15.0)
    JardinierAutomate(BRIDE).jouer_tick(engine)
    j = journal(engine.game_state)
    gestes = [l["geste"] for l in j if l["categorie"] == "geste"]
    coupes = [l for l in j if l["categorie"] == "geste_coupe"]
    check("③ préemption — arrosage (survie) exécuté", "arroser" in gestes, f"{gestes}")
    check("③ préemption — planter créatif coupé au budget",
          len(coupes) == 1 and coupes[0]["detail"] == {"verbe": "planter", "cause": "budget"},
          f"{[c['detail'] for c in coupes]}")
    check("③ préemption — graine haricot conservée (semis reporté)",
          engine.game_state["player_seed_bank"].count("haricot") == 1)


def test_ordre_libre_survie_avant_creatif():
    """Mode LIBRE : rien n'est coupé, MAIS le tri ordonne quand même `arroser` (survie)
    AVANT `planter` (créatif) dans le journal — préemption d'ORDRE (philo #3)."""
    obj = Objectif("recolter", 2, "haricot", "obj_har")
    engine = _toy(obj, graine="haricot", cultivee=("tomate", 5, 5))
    JardinierAutomate(LIBRE).jouer_tick(engine)
    verbes = [l["geste"] for l in journal(engine.game_state) if l["categorie"] == "geste"]
    ok = ("arroser" in verbes and "planter" in verbes
          and verbes.index("arroser") < verbes.index("planter"))
    check("③ ordre libre — survie AVANT créatif", ok, f"{verbes}")


def test_favoriser_une_seule_fois():
    """`favoriser_auxiliaire` (habitat pollinisateur d'une fruitière) posé AU PLUS TÔT,
    UNE seule fois : la rondelle est persistante → au 2ᵉ tick la zone n'est plus « sans
    habitat » → aucun nouveau geste (one-shot déterministe, C4)."""
    obj = Objectif("recolter", 1, "tomate", "obj_tom")
    engine = _toy(obj, cultivee=("tomate", 5, 5))   # tomate fruitier, n_vivantes==nb_cible
    auto = JardinierAutomate(LIBRE)
    auto.jouer_tick(engine)
    auto.jouer_tick(engine)
    favs = [l for l in journal(engine.game_state)
            if l["categorie"] == "geste" and l["geste"] == "favoriser_auxiliaire"]
    check("③ favoriser_auxiliaire posé une seule fois sur 2 ticks",
          len(favs) == 1, f"{len(favs)} pose(s)")


def main() -> int:
    print("=== test_automate_determinisme (tronçons ① + ③) ===")
    test_rejeu_identique()
    test_pas_effet_de_bord()
    test_objectif_bout_en_bout_deterministe()
    test_preemption_budget()
    test_ordre_libre_survie_avant_creatif()
    test_favoriser_une_seule_fois()
    test_automate_off_golden()
    ko = [n for n, ok in _results if not ok]
    if ko:
        print(f"[determinisme] FAIL — {len(ko)} échec(s) : {ko}")
        return 1
    print(f"[determinisme] PASS — {len(_results)} vérifs OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
