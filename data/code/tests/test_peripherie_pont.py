"""
SYMBIOSE — tests/test_peripherie_pont.py
Tests ciblés de la CEINTURE AU PONT (sprint PÉRIPHÉRIE ⑦, D73 — dernier tronçon).
Spec : `docs/champs/peripherie/conception_peripherie.md` §4.1/§11 + kickoff
`sprints/champs/peripherie/sprint_peripherie/07_vue_godot.md`.

Fichier SÉPARÉ, comme ④ (`..._gestes`) et ⑤ (`..._eau_roche`) : un fichier par
tronçon, acté depuis que `test_peripherie.py` (①②③) a atteint 415 LDC.

Ce tronçon n'ajoute AUCUNE écologie : un bloc de snapshot, un routeur de gestes, un
banc. Les tests portent donc sur le CONTRAT DU PONT — ce que la vue Godot peut
tenir pour vrai (le F5 visuel, lui, reste à Nico : rien ici ne prouve un rendu).

Cinq suites :
  AD. BLOC        — `ceinture_block` : None sans ceinture, 10 champs sinon, valeurs
                    MIROIRS de l'état moteur, et le bloc SUIT une coupe ;
  AE. SNAPSHOT    — absent en `smoke` (fixture du golden), présent en `full` (monde de
                    jeu) et au banc ; version de protocole bumpée ;
  AF. ROUTAGE     — les 6 verbes de secteur passent ; `creuser` est DUAL (secteur hors
                    jardin / plot dedans) ; désignation invalide et monde sans
                    périphérie refusent SANS rien coûter ;
  AG. BANC        — 4 motifs distincts, 4 tuiles COLLÉES aux bords (sinon aucun flux
                    de bordure ne les touche), outils en poche, déterminisme ;
  AH. NEUTRALITÉ  — un monde sans ceinture reste muet de bout en bout (aucune clé
                    créée, aucun geste applicable) → le golden ne peut pas bouger.

Usage (depuis data/code/) :
  python3 -m tests.test_peripherie_pont
"""
import sys

from bancs.peripherie import PER_COLS, ceinture_contrastee, peripherie
from fields.peripherie import COTES, MONDE_CM, couper_secteur, generer_ceinture
from sim import vigueur as V
from tools.simserver.peripherie_route import CHAMPS_VUE, VERBES, ceinture_block
from tools.simserver.server import SimServer
from tools.simserver.version import ENGINE_VERSION

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


PLAYER = "joueur_1"


def _serveur(config, seed=7):
    """Un serveur monté sur une config, Vigueur remise au plein (les gestes de
    paysage coûtent TRES_ELEVE : on ne teste pas le porte-monnaie ici)."""
    srv = SimServer()
    srv.cmd_init({"config": config, "seed": seed})
    V.ensure_player(srv.engine.game_state, PLAYER)["courante"] = 1000.0
    return srv


# --- AD. le bloc de snapshot -----------------------------------------------
def test_bloc():
    print("\n[AD] bloc `ceinture` : opt-in, miroir de l'état, suit les gestes")
    check("sans ceinture → None (opt-in strict)", ceinture_block({}) is None)
    check("ceinture vide → None", ceinture_block({"ceinture": []}) is None)

    ceinture = generer_ceinture(3)
    bloc = ceinture_block({"ceinture": ceinture})
    check("4 secteurs", len(bloc) == 4, f"{len(bloc)}")
    check("un secteur = exactement les champs de la vue",
          all(tuple(s) == CHAMPS_VUE + ("floraison", "colonies") for s in bloc),
          f"{tuple(bloc[0])}")
    check("`cote` conservé dans l'ordre",
          [s["cote"] for s in bloc] == list(COTES))
    check("valeurs MIROIRS de l'état moteur (aucun recalcul)",
          all(bloc[i][champ] == ceinture[i][champ]
              for i in range(4) for champ in CHAMPS_VUE))
    check("la mécanique NE fuit PAS vers la vue (horloges, cibles, verrous)",
          not ({"annees_depuis_coupe", "geste_coupe", "densite_avant",
                "hauteur_avant", "erosion_signalee", "ligne_eau_naturelle"}
               & set(CHAMPS_VUE)))

    # Le bloc doit SUIVRE une coupe : c'est tout l'intérêt (la clairière se voit).
    boise = next(s for s in ceinture if s["type"] == "foret")
    avant = ceinture_block({"ceinture": ceinture})[boise["cote"]]
    couper_secteur(boise, "abattre")
    apres = ceinture_block({"ceinture": ceinture})[boise["cote"]]
    check("une coupe fait chuter la densité DANS le bloc",
          apres["densite_ligneuse"] < avant["densite_ligneuse"],
          f"{avant['densite_ligneuse']} → {apres['densite_ligneuse']}")
    check("la souche coupée est exposée (la vue peut la lire)",
          apres["souche_memory"] in ("vivante", "morte"),
          f"{apres['souche_memory']!r}")


# --- AE. le snapshot du serveur --------------------------------------------
def test_snapshot():
    print("\n[AE] snapshot : absent en smoke, présent dans les mondes de jeu")
    # Indépendant de la version courante (oracle périmé à chaque bump, D116 d) :
    # le bloc `ceinture` existe depuis 0.5.41 → tout protocole ≥ 0.5.41 convient.
    check("protocole ≥ 0.5.41 (bloc ceinture)",
          tuple(int(x) for x in ENGINE_VERSION.split(".")) >= (0, 5, 41),
          ENGINE_VERSION)

    smoke = _serveur("smoke").cmd_snapshot({})["snapshot"]
    check("smoke (fixture du golden) n'a AUCUN bloc `ceinture`",
          "ceinture" not in smoke)

    full = _serveur("full", seed=0x5AB1057E).cmd_snapshot({})["snapshot"]
    check("full (monde de jeu) porte le bloc", "ceinture" in full)
    check("full : 4 secteurs typés",
          len(full["ceinture"]) == 4
          and all(s["type"] for s in full["ceinture"]),
          str([s["type"] for s in full["ceinture"]]))

    banc = _serveur("peripherie").cmd_snapshot({})["snapshot"]
    check("banc `peripherie` porte le bloc", "ceinture" in banc)
    check("un tick conserve le bloc (état persistant, pas un transient)",
          "ceinture" in _serveur("peripherie").cmd_step_week({})["snapshot"])


# --- AF. routage des gestes ------------------------------------------------
def _action(srv, verb, target):
    return srv.cmd_action({"verb": verb, "target": target})["result"]


def test_routage():
    print("\n[AF] routage : 6 verbes de secteur + `creuser` dual")
    for verb, cote in (("abattre", 2), ("receper", 2), ("eteter", 2),
                       ("endiguer", 1), ("deriver", 1), ("entailler", 0)):
        srv = _serveur("peripherie")
        res = _action(srv, verb, {"cote": cote})
        check(f"`{verb}` sur le bon bord → appliqué", res["applied"],
              res["message"])
    check("les 6 verbes de secteur sont bien la liste du routeur",
          set(VERBES) == {"abattre", "receper", "eteter",
                          "endiguer", "deriver", "entailler"})

    # `creuser` : UN verbe, DEUX cibles (décision ⑤ — aucun `creuser_mare`).
    srv = _serveur("peripherie")
    res = _action(srv, "creuser", {"cote": 3})     # friche de l'ouest
    check("`creuser` + cote → mare de bordure", res["applied"], res["message"])
    ligne = srv.engine.game_state["ceinture"][3]["ligne_eau"]
    check("la mare a relevé la ligne d'eau du secteur", ligne > 0.0, f"{ligne}")
    res = _action(srv, "creuser", {"tile": "BORD_NORD", "r": 1, "c": 1})
    check("`creuser` + plot → cuvette (routage inchangé)", res["applied"],
          res["message"])
    res = _action(srv, "creuser", {"cote": 0})     # falaise : refus métier
    check("`creuser` refusé sur la falaise (pas à la bêche)",
          not res["applied"], res["message"])

    # Refus de DÉSIGNATION : aucun coût, aucun effet.
    srv = _serveur("peripherie")
    v0 = V.ensure_player(srv.engine.game_state, PLAYER)["courante"]
    for target in ({"cote": 9}, {"cote": "nord"}, {"cote": True}, {}):
        res = _action(srv, "abattre", target)
        check(f"désignation {target} refusée", not res["applied"],
              res["message"])
    check("aucun refus de désignation n'a coûté de Vigueur",
          V.ensure_player(srv.engine.game_state, PLAYER)["courante"] == v0)


# --- AG. le banc ------------------------------------------------------------
def test_banc():
    print("\n[AG] banc `peripherie` : 4 motifs, tuiles collées aux bords, outillé")
    ceinture = ceinture_contrastee()
    types = [s["type"] for s in ceinture]
    check("un motif DIFFÉRENT par bord", len(set(types)) == 4, str(types))
    check("forêt au SUD (le seul bord dont l'ombre entre au jardin)",
          types[2] == "foret")
    check("la forêt du banc est dense et haute",
          ceinture[2]["densite_ligneuse"] >= 0.85
          and ceinture[2]["hauteur_canopee"] >= 1500.0)
    check("essence qui REJETTE de souche (recépage instructif)",
          ceinture[2]["essence"] == "charme")
    check("déterministe : deux appels donnent le même état",
          ceinture_contrastee() == ceinture)

    tiles, ecos, _house, _banque = peripherie()
    check("4 tuiles", len(tiles) == 4)
    cote_cm = PER_COLS * 50.0
    colle = [t for t in tiles
             if min(t.origin_x_cm, t.origin_y_cm) == 0.0
             or max(t.origin_x_cm, t.origin_y_cm) == MONDE_CM - cote_cm]
    check("chaque tuile est COLLÉE à un bord (sinon aucun flux ne l'atteint)",
          len(colle) == 4,
          str([(t.tile_id, t.origin_x_cm, t.origin_y_cm) for t in tiles]))
    check("un eco par tuile", set(ecos) == {t.tile_id for t in tiles})

    srv = SimServer()
    srv.cmd_init({"config": "peripherie", "seed": 7})
    ouverts = srv.cmd_snapshot({})["snapshot"]["player"]["gestes_debloques"]
    check("les 7 gestes de paysage sont OUVERTS d'emblée (outils en poche)",
          {"abattre", "receper", "eteter", "endiguer", "deriver",
           "entailler", "creuser"} <= set(ouverts),
          str(sorted(ouverts)))


# --- AH. neutralité ---------------------------------------------------------
def test_neutralite():
    print("\n[AH] neutralité : un monde sans ceinture reste muet")
    srv = _serveur("smoke")
    gs = srv.engine.game_state
    check("`cmd_init` ne crée AUCUNE clé `ceinture` en smoke",
          "ceinture" not in gs)
    for verb in VERBES + ("creuser",):
        res = _action(srv, verb, {"cote": 0})
        check(f"`{verb}` sans périphérie → refusé", not res["applied"],
              res["message"])
    check("toujours aucune clé `ceinture` après les refus",
          "ceinture" not in gs)
    snap = srv.cmd_step_week({})["snapshot"]
    check("un tick sans ceinture n'émet toujours pas le bloc",
          "ceinture" not in snap)


def main():
    test_bloc()
    test_snapshot()
    test_routage()
    test_banc()
    test_neutralite()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[test_peripherie_pont] {n_ok}/{n} OK")
    if n_ok != n:
        print("ÉCHECS : " + ", ".join(name for name, ok in _results if not ok))
        sys.exit(1)
    print("[test_peripherie_pont] PASS")


if __name__ == "__main__":
    main()
