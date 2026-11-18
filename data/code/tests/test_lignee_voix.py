"""
SYMBIOSE — tests/test_lignee_voix.py
Voix « lignée » (D139, sprint génétique infinitésimale ④) : du geste `planter` d'une
graine RÉCOLTÉE jusqu'au carnet, à l'encyclopédie et au palier du concept.

Chaîne vérifiée :
  planter (graine à gènes) → ligne `🫘` dans `game_state["log"]` (sim/lignee)
  → `evenements` (kind « lignee », cause fixee/en_voie/melangee)
  → journal → carnet (concept « lignée », descriptif puis interprétatif)
  → pont hook A (découverte du concept) + `detecter` (preuve à chaque ressemis).
Une graine SANS gènes (sachet magazine, récompense) n'écrit rien.

Usage (depuis data/code/) :
  python3 -m tests.test_lignee_voix
"""
import sys

from world import Tile
from fields import init_eco
from sim import actions as ACT
from sim import vigueur as V
from sim import maitrise as M
from sim import journal as J
from sim import carnet
from sim import lignee as L
from sim.evenements import evenements
from sim.encyclopedie_types import type_de
from sim.concept_corpus import FICHES_CONCEPT
from sim.seeds import Seed, PlayerSeedBank
from tools.simserver.maitrise_pont import observer_apres_tick

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _monde():
    tile = Tile(tile_id="T0", soil_type="terre")
    eco = init_eco("T0", 6, 8, humidite=1.5, fertilite=1.0, microbiome=0.3)
    gs = {"tiles": [tile], "eco": {"T0": eco}, "scores": {},
          "current_player": "j1", "week": 20, "log": [], "seed": 42,
          "player_seed_bank": PlayerSeedBank()}
    V.ensure_player(gs, "j1")
    return gs, tile, eco


def test_categorie():
    print("[a] catégories de F")
    check("F 0,98 → fixee", L.categorie(0.98) == L.FIXEE)
    check("F 0,50 → en_voie", L.categorie(0.50) == L.EN_VOIE)
    check("F 0,00 → melangee", L.categorie(0.0) == L.MELANGEE)
    ligne = L.ligne_semis("T0", 2, 3, "tomate", 0.9)
    check("aller-retour de la ligne", L.lire_semis(ligne) == ("T0", (2, 3), "tomate", "fixee"),
          ligne)
    check("ligne étrangère ignorée", L.lire_semis("  🌱 Tomate@(2, 3) → [pousse]") is None)


def test_planter():
    print("[b] planter écrit la ligne seulement pour une graine récoltée")
    gs, tile, eco = _monde()
    bank = gs["player_seed_bank"]
    bank.add(Seed(species="tomate"))                                   # sachet : sans gènes
    bank.add(Seed(species="tomate", genes={"hauteur": 1.02}, F=0.94))  # récolte
    ACT.planter(gs, "j1", tile, eco, "tomate", 1, 1)
    check("sachet : aucune ligne", gs["log"] == [], f"{gs['log']}")
    ACT.planter(gs, "j1", tile, eco, "tomate", 2, 2)
    check("graine récoltée : une ligne 🫘", len(gs["log"]) == 1 and L.MARQUEUR in gs["log"][0],
          f"{gs['log']}")
    evs = evenements(gs["log"])
    check("événement lignee, zone et cause", len(evs) == 1 and evs[0].kind == "lignee"
          and evs[0].tile_id == "T0" and evs[0].pos == (2, 2)
          and evs[0].espece == "tomate" and evs[0].cause == "fixee", f"{evs}")
    return gs


def test_voix(gs):
    print("[c] carnet, encyclopédie, palier")
    check("« lignée » est un concept d'encyclopédie", type_de(L.CONCEPT) == "concept")
    check("fiche 3 niveaux", set(FICHES_CONCEPT.get(L.CONCEPT, {})) == {1, 2, 3})
    for cause in (L.FIXEE, L.EN_VOIE, L.MELANGEE):
        check(f"carnet : concept + 2 gabarits ({cause})",
              carnet.CONCEPT_DE.get(("lignee", cause)) == L.CONCEPT
              and ("lignee", cause, "descriptif") in carnet.GABARIT
              and ("lignee", cause, "interprétatif") in carnet.GABARIT)
    log = list(gs["log"])
    J.consigner(gs, "j1", log, 20)
    observer_apres_tick(gs, "j1", log)
    check("1er ressemis : concept découvert", M.palier(gs, "j1", L.CONCEPT) >= 1)
    notes = carnet.carnet_lire(gs, "j1", {"concept": L.CONCEPT})
    check("note du carnet, descriptive sous le palier",
          len(notes) == 1 and notes[0]["registre"] == "descriptif"
          and "ma récolte" in notes[0]["texte"], f"{notes}")
    # Preuve à chaque ressemis (hook B) : le concept découvert accumule des preuves.
    st = gs["maitrise"]["j1"]["objets"][L.CONCEPT]
    avant = st["preuves"]
    from sim import maitrise_detection as MD
    MD.detecter(gs, "j1", log, 21)
    check("detecter : ressemis = preuve du concept", st["preuves"] > avant or st["palier"] > 1,
          f"{st}")
    # Au palier de maîtrise, la MÊME note se relit interprétative (révélation rétroactive).
    st["palier"] = carnet.SEUIL_CARNET
    notes = carnet.carnet_lire(gs, "j1", {"concept": L.CONCEPT})
    check("au palier de maîtrise : note interprétative",
          notes and notes[0]["registre"] == "interprétatif"
          and "fixée" in notes[0]["texte"], f"{notes}")


def main():
    test_categorie()
    gs = test_planter()
    test_voix(gs)
    ok = sum(1 for _, v in _results if v)
    print(f"\n=== VOIX LIGNÉE : {ok}/{len(_results)} ===")
    sys.exit(0 if ok == len(_results) else 1)


if __name__ == "__main__":
    main()
