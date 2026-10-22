"""
SYMBIOSE — tests/test_infobulle_vivant.py
INFO-BULLE DU VIVANT, tronçon ① (Python). Spec :
`docs/narration/semiologie/conception_infobulle_vivant.md` §2-§4.1.

  A. Corpus : `FAUNE_ROLE` = mêmes clés que `FAUNE_VU`, ≤ 6 mots ; champignon,
     voix saine, libellés et bornes de nourriture (mesurées, ordonnées).
  B. Crédit saisonnier (pont `observer_espece`) : 1er survol = palier 1 ; même
     saison = rien ; 2ᵉ saison = 2 ; 3ᵉ = 3 et `appris` ; 4ᵉ = reste 3 ; plante =
     aucun crédit ; champignon idem (3 automnes) ; option anticipée nommée au 1er.
  C. Rôle carpophore : bois / racines / humus.
  D. Légende : nouvelles clés, anciennes intactes.
  E. (③, pont 0.5.48) `observer` d'une bête renvoie `appris` (nom révélé tout de
     suite côté vue) ; d'une plante, non.

Usage (depuis data/code/) : python3 -m tests.test_infobulle_vivant
"""
from sim import maitrise
from sim import signes as SG
from sim import signes_corpus as SC
from sim.champignon_role import plots_racines, role_carpophore
from tools.simserver.maitrise_pont import observer_espece, _CLE_DE_NOM
from tools.simserver.server import SimServer

P = "joueur_1"
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def test_corpus():
    print("\n[A] corpus")
    check("FAUNE_ROLE : mêmes clés que FAUNE_VU", set(SC.FAUNE_ROLE) == set(SC.FAUNE_VU),
          sorted(set(SC.FAUNE_ROLE) ^ set(SC.FAUNE_VU)))
    longs = {k: v for k, v in SC.FAUNE_ROLE.items()
             if len(v.replace(";", " ").replace(",", " ").split()) > 6}
    check("rôles ≤ 6 mots", not longs, longs)
    check("champignon : vu + 3 rôles b/r/h",
          SC.CHAMPIGNON_VU and set(SC.CHAMPIGNON_ROLE) == {"b", "r", "h"})
    check("voix saine : franc / automne / terne",
          set(SC.VOIX_SAINE) == {"franc", "automne", "terne"})
    check("bornes nourriture mesurées et ordonnées",
          0 < SC.NOURRITURE_SUFFISANTE < SC.NOURRITURE_ABONDANTE < 1,
          (SC.NOURRITURE_SUFFISANTE, SC.NOURRITURE_ABONDANTE))
    check("libellés abondance / nourriture / réseau",
          len(SC.ABONDANCE) == 3 and len(SC.NOURRITURE) == 3 and len(SC.RESEAU) == 2)


def _survols(cle, semaines, gs=None):
    gs = gs if gs is not None else {}
    paliers = []
    for s in semaines:
        observer_espece(gs, P, cle, s)
        paliers.append(maitrise.palier(gs, P, cle))
    return gs, paliers


def test_credit():
    print("\n[B] crédit par observation saisonnière")
    # Semaines : 1 et 5 (saison 0), 14 (saison 1), 30 (saison 2), 45 (saison 3).
    gs, p = _survols("coccinelle", [1, 5, 14, 30, 45])
    check("1er survol = palier 1", p[0] == 1, p)
    check("même saison = rien", p[1] == 1, p)
    check("2ᵉ saison = palier 2", p[2] == 2, p)
    check("3ᵉ saison = palier 3", p[3] == 3, p)
    check("3ᵉ saison → appris (nommée)", "coccinelle" in SG.appris(gs, P)["faune"],
          SG.appris(gs, P))
    check("4ᵉ saison = reste 3 (plafond SEUIL_CARNET)", p[4] == 3, p)
    check("mémoire sérialisable (dict str → int)",
          gs["maitrise"][P]["_saisons_vues"] == {"coccinelle": 2},
          gs["maitrise"][P].get("_saisons_vues"))
    gs = {}
    for s in (1, 14, 30):                      # nom de CLASSE (comme le C#)
        observer_espece(gs, P, "Tomato", s)
    check("plante survolée : aucun crédit saisonnier",
          maitrise.palier(gs, P, "tomate") == 1
          and "_saisons_vues" not in gs["maitrise"][P], maitrise.palier(gs, P, "tomate"))
    gs, p = _survols("coprin", [30, 35, 82, 134])
    check("champignon (coprin) : 3 saisons → 3 et appris",
          p == [1, 1, 2, 3] and "coprin" in SG.appris(gs, P)["faune"], p)
    gs, p = _survols("puceron", [0, 1])
    check("semaine 0 (avant le 1er tick) = même saison que la semaine 1", p == [1, 1], p)
    gs, p = _survols("merle", [1], gs={"options": {P: {"carnet_anticipe": True}}})
    check("option anticipée : nommée dès le 1er survol",
          p == [1] and "merle" in SG.appris(gs, P)["faune"], p)
    gs2 = {}
    observer_espece(gs2, P, "libellule")       # sans semaine (debug) → découverte seule
    check("sans semaine : découverte seule, aucune mémoire",
          maitrise.palier(gs2, P, "libellule") == 1
          and "_saisons_vues" not in gs2["maitrise"][P])
    gs3 = {}
    maitrise.decouvrir(gs3, P, "osmie")         # connue AVANT le sprint (pas de mémoire)
    observer_espece(gs3, P, "osmie", 14)
    check("clé connue sans mémoire → mémorisée sans crédit",
          maitrise.palier(gs3, P, "osmie") == 1
          and gs3["maitrise"][P]["_saisons_vues"] == {"osmie": 1})


class _Eco:
    def __init__(self, bois):
        self._bois = bois

    def bois_fresh_at(self, r, c):
        return self._bois.get((r, c), 0.0)


class _Plante:
    def __init__(self, plots, vivante=True):
        self.root_plots = plots
        self.is_alive = vivante


def test_role_carpophore():
    print("\n[C] rôle local du carpophore")
    eco = _Eco({(0, 0): 1.2})
    racines = plots_racines([_Plante([(0, 0), (1, 1)]), _Plante([(2, 2)], vivante=False)])
    check("bois frais au plot → b (prioritaire sur les racines)",
          role_carpophore(eco, racines, 0, 0) == "b")
    check("racines vivantes → r", role_carpophore(eco, racines, 1, 1) == "r")
    check("racines d'une plante morte ignorées → h", role_carpophore(eco, racines, 2, 2) == "h")
    check("rien → h", role_carpophore(eco, racines, 3, 3) == "h")


def test_legende():
    print("\n[D] légende")
    rep = SimServer().cmd_legende({})
    attendues = {"ok", "signes", "faune", "faune_role", "champignon", "champignons",
                 "voix_saine", "abondance", "nourriture", "reseau"}
    check("clés attendues (anciennes + nouvelles)", set(rep) == attendues, sorted(rep))
    check("nourriture : bornes du corpus",
          rep["nourriture"]["suffisante"] == SC.NOURRITURE_SUFFISANTE
          and rep["nourriture"]["abondante"] == SC.NOURRITURE_ABONDANTE)
    check("champignon : vu + rôles", rep["champignon"]["vu"] == SC.CHAMPIGNON_VU
          and set(rep["champignon"]["roles"]) == {"b", "r", "h"})
    check("réseau dense = plot plein (CARPO_DENS_REF)", rep["reseau"]["dense"] == 0.70)


def test_observer_appris():
    print("\n[E] observer → appris (③)")
    srv = SimServer()
    gs = {"current_player": P, "week": 1}
    srv.engine = type("E", (), {"game_state": gs})()
    reps = []
    for semaine in (2, 15, 28):   # 3 saisons distinctes (semaine consignée = week - 1)
        gs["week"] = semaine
        reps.append(srv.cmd_observer({"species": "coccinelle"}))
    check("bête : `appris` dans chaque réponse", all("appris" in r for r in reps))
    check("pas nommée avant la 3ᵉ saison", "coccinelle" not in reps[1]["appris"]["faune"])
    check("nommée dans la réponse de la 3ᵉ saison", "coccinelle" in reps[2]["appris"]["faune"])
    plante = srv.cmd_observer({"species": next(iter(_CLE_DE_NOM))})
    check("plante : pas d'`appris`", plante["ok"] and "appris" not in plante, plante)


if __name__ == "__main__":
    test_corpus()
    test_credit()
    test_role_carpophore()
    test_legende()
    test_observer_appris()
    ok = sum(1 for _, c in _results if c)
    print(f"\n{ok}/{len(_results)} OK")
    raise SystemExit(0 if ok == len(_results) else 1)
