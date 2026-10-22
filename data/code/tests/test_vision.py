"""
SYMBIOSE — tests/test_vision.py
LE SOL QUI RESPIRE ⑥ — manger un champignon et la vision (D111 §4).

  A. Effets par comestibilité (interrupteur « Vigueur infinie » OFF) : comestible →
     Vigueur ; vénéneux → perte ; mortel → perte plus forte, plancher 0, jamais de
     mort ; psychédélique → vision ; tue-mouches → vision ET perte ; immangeable →
     refus sans consommation. Interrupteur ON → la perte est masquée (documenté).
  B. Le carpophore mangé disparaît du snapshot pour la semaine ; le nom n'est pas
     révélé par le geste tant que l'espèce n'est pas nommée.
  C. Durée de la vision (semaine en cours + 1 semaine pleine) et lecture
     transcendante (carnet, encyclopédie, info-bulle) ; tout revient ensuite.
  D. Isolation : Vigueur max et paliers de maîtrise INCHANGÉS pendant la vision.
  E. `parler` : muet hors vision ; 1-3 phrases déterministes sous vision (plante,
     bête, champignon).
  F. Overdose : clé `voix` au snapshot (tous les êtres), absente sinon.
  G. Ce qui reste : +1 palier exactement par espèce assez survolée, une fois par
     vision, jamais jusqu'au transcendant.

Échantillonnage des carpophores forcé par monkeypatch (espèce choisie) : on teste
le vrai chemin du geste et du snapshot, pas la météo. Golden non concerné.
Usage (depuis data/code/) : python3 -m tests.test_vision
"""
import sim.champignon_manger as CM
from fields.population.perception import Carpophore
from sim import maitrise, vision, vigueur as V
from sim import signes as SG, encyclopedie, carnet
from tools.simserver.server import SimServer

P = "joueur_1"
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _forcer(espece):
    """Un seul carpophore visible, de l'espèce voulue, au plot (2, 3) slot 0."""
    CM.sample_carpophores = lambda eco, seed, wiy, pluie, racines=None: [
        Carpophore(row=2, col=3, slot=0, x_frac=0.5, y_frac=0.5, densite=0.7,
                   espece=espece)]
    CM.pluie_semaine_precedente = lambda gs: True


def _serveur(infinie=None):
    s = SimServer()
    msg = {"config": "smoke"}
    if infinie is not None:
        msg["vigueur_infinie"] = infinie
    s.cmd_init(msg)
    return s


def _manger(s, espece, tile=None):
    _forcer(espece)
    gs = s.engine.game_state
    tid = tile or gs["tiles"][0].tile_id
    rep = s.cmd_action({"verb": "manger",
                        "target": {"tile": tid, "carpophore": [2, 3, 0]}})
    return rep["result"], rep["snapshot"]


def _vig(s):
    return V.ensure_player(s.engine.game_state, P)["courante"]


def _facade(s, espece):
    """Geste par la FAÇADE (`sim/champignon_manger`) : isole l'effet du champignon de
    la progression générique du pont (découverte du geste `manger` + son petit gain
    de Vigueur, qui touchent aussi la Vigueur max)."""
    _forcer(espece)
    gs = s.engine.game_state
    return CM.manger_carpophore(gs, P, gs["tiles"][0], 2, 3, 0)


def test_comestibilite():
    print("\n[A] effets par comestibilité (Vigueur infinie OFF)")
    s = _serveur()
    gs = s.engine.game_state
    vmax = V.vigueur_max(gs, P)
    V.ensure_player(gs, P)["courante"] = 50.0
    r = _facade(s, "pleurote")
    check("comestible → +Vigueur (∝ maturité)", r["applied"] and r["gain"] > 0
          and abs(_vig(s) - (50.0 + r["gain"])) < 1e-9, r["gain"])
    s = _serveur()
    r = _facade(s, "hypholome")
    check("vénéneux → perte = moitié de la Vigueur max",
          abs(r["perte"] - 0.5 * vmax) < 1e-9 and abs(_vig(s) - 0.5 * vmax) < 1e-9,
          (r["perte"], _vig(s)))
    s = _serveur()
    V.ensure_player(s.engine.game_state, P)["courante"] = 10.0
    r = _facade(s, "clitocybe")
    check("mortel → perte plus forte, plancher 0, jamais de mort",
          r["applied"] and r["perte"] > 0.5 * vmax and _vig(s) == 0.0
          and s.cmd_step_week({})["ok"], r["perte"])
    s = _serveur()
    r = _facade(s, "psilocybe")
    check("psychédélique → vision, sans perte",
          r["vision"] == "vision" and _vig(s) == vmax
          and vision.vision_active(s.engine.game_state, P))
    s = _serveur()
    r = _facade(s, "amanite_tue_mouches")
    check("tue-mouches → vision ET perte", r["vision"] == "vision" and _vig(s) < vmax)
    s = _serveur()
    r = _facade(s, "polypore_bouleau")
    snap = s.cmd_snapshot({})["snapshot"]
    check("immangeable → refus, rien consommé",
          not r["applied"] and _vig(s) == vmax
          and len(snap["carpophores"][s.engine.game_state["tiles"][0].tile_id]) == 1)
    s = _serveur(infinie=True)
    r = _facade(s, "hypholome")
    check("interrupteur ON : la perte est masquée (seul point de débit = spend)",
          r["applied"] and _vig(s) == vmax)


def test_disparition_et_nom():
    print("\n[B] disparition pour la semaine, nom non révélé")
    s = _serveur()
    gs = s.engine.game_state
    tid = gs["tiles"][0].tile_id
    _forcer("cepe")
    k0 = s.cmd_snapshot({})["snapshot"]["carpophores"][tid][0]
    check("⑧ (0.5.56) : 8ᵉ champ = slot, la clé [r, c, slot] du geste",
          len(k0) == 8 and [k0[0], k0[1], k0[7]] == [2, 3, 0], k0)
    r, snap = _manger(s, "cepe")
    check("le geste ne nomme pas une espèce inconnue",
          r["espece_nommee"] is None and "Cèpe" not in r["message"], r["message"])
    check("carpophore mangé absent du snapshot", snap["carpophores"][tid] == [])
    r2, _ = _manger(s, "cepe")
    check("re-manger le même → refus", not r2["applied"])
    snap2 = s.cmd_step_week({})["snapshot"]
    check("semaine suivante : il peut ressortir", len(snap2["carpophores"][tid]) == 1)
    maitrise.enregistrer_preuve(gs, P, "cepe", poids=50)
    r3, _ = _manger(s, "cepe")
    check("espèce nommée → nom dans la réponse",
          r3["espece_nommee"] == "cepe" and "Cèpe" in r3["message"], r3["message"])


def test_duree_et_lecture():
    print("\n[C] durée et lecture transcendante")
    s = _serveur()
    gs = s.engine.game_state
    maitrise.decouvrir(gs, P, "tomate")
    avant_appris = SG.appris(gs, P)
    w0 = gs["week"]
    _manger(s, "psilocybe")
    check("lecture : encyclopédie plante au niveau 3",
          encyclopedie.encyclopedie_lire(gs, P, "tomate")["niveau_max"] == 3)
    check("lecture : fiche non découverte toujours fermée",
          encyclopedie.encyclopedie_lire(gs, P, "basilic") is None)
    check("lecture : carnet interprétatif", carnet._registre(gs, P, "eau") == carnet._I)
    ap = SG.appris(gs, P)
    check("lecture : info-bulle complète (bêtes et champignons nommés)",
          "herisson" in ap["faune"] and "psilocybe" in ap["champignons"])
    snap = s.cmd_step_week({})["snapshot"]
    check("semaine w+1 : toujours en vision", snap["player"]["vision"]["active"]
          and snap["player"]["vision"]["fin"] == w0 + 1)
    snap = s.cmd_step_week({})["snapshot"]
    check("semaine w+2 : vision close", not snap["player"]["vision"]["active"]
          and "vision" not in gs or P not in gs.get("vision", {}))
    check("lecture revenue au vrai palier",
          encyclopedie.encyclopedie_lire(gs, P, "tomate")["niveau_max"] == 1
          and SG.appris(gs, P) == avant_appris)


def test_isolation():
    print("\n[D] isolation : Vigueur max et maîtrise intactes pendant la vision")
    s = _serveur()
    gs = s.engine.game_state
    maitrise.decouvrir(gs, P, "tomate")
    vmax = V.vigueur_max(gs, P)
    objets = repr(gs["maitrise"][P]["objets"])
    _facade(s, "psilocybe")
    check("Vigueur max inchangée", V.vigueur_max(gs, P) == vmax
          and V.regen_rate(gs, P) == V.REGEN_BASE * maitrise.palier_bonus(gs, P))
    check("paliers de maîtrise inchangés", repr(gs["maitrise"][P]["objets"]) == objets
          and maitrise.palier(gs, P, "tomate") == 1)


def _plante(snap):
    p = next(p for p in snap["plants"] if not p.get("dead"))
    return {"tile": p["tile"], "x_cm": p["x_cm"], "y_cm": p["y_cm"]}


def test_parler():
    print("\n[E] les êtres parlent")
    s = _serveur()
    gs = s.engine.game_state
    snap = s.cmd_step_week({})["snapshot"]
    cible = _plante(snap)
    check("hors vision : muet", s.cmd_parler(cible) == {"ok": True, "vision": False,
                                                       "phrases": []})
    _manger(s, "psilocybe")
    a, b = s.cmd_parler(cible), s.cmd_parler(cible)
    check("plante : 1 à 3 phrases, déterministes", a["vision"]
          and 1 <= len(a["phrases"]) <= 3 and a["phrases"] == b["phrases"], a["phrases"])
    tid = cible["tile"]
    bete = s.cmd_parler({"espece": "lombric", "tile": tid, "r": 1, "c": 1})
    champi = s.cmd_parler({"espece": "pleurote", "tile": tid, "r": 1, "c": 1})
    check("bête et champignon parlent", bete["phrases"] and champi["phrases"],
          (bete["phrases"], champi["phrases"]))
    check("survols comptés (plante + bête + champignon)",
          set(gs["vision"][P]["survols"]) >= {"lombric", "pleurote"}
          and len(gs["vision"][P]["survols"]) == 3, gs["vision"][P]["survols"])
    check("être inconnu → refus", not s.cmd_parler({"espece": "licorne", "tile": tid,
                                                    "r": 1, "c": 1})["ok"])


def test_overdose():
    print("\n[F] overdose")
    s = _serveur()
    gs = s.engine.game_state
    _, snap = _manger(s, "psilocybe")
    check("vision simple : pas de clé voix", "voix" not in snap)
    fin = gs["vision"][P]["fin"]
    s.cmd_step_week({})   # semaine suivante (vision encore active) : nouveau carpophore
    r, snap = _manger(s, "amanite_tue_mouches")
    n_vivantes = sum(1 for p in snap["plants"] if not p.get("dead"))
    n_voix = sum(len(v["plantes"]) for v in snap["voix"].values())
    check("2ᵉ psychédélique → overdose, fin inchangée",
          r["vision"] == "overdose" and gs["vision"][P]["fin"] == fin
          and snap["player"]["vision"]["overdose"])
    check("overdose : toutes les plantes vivantes parlent", n_voix == n_vivantes > 0,
          (n_voix, n_vivantes))
    check("overdose : champignons du snapshot parlent aussi",
          all(len(v["champignons"]) == len(snap["carpophores"][t])
              for t, v in snap["voix"].items()))
    snap = s.cmd_step_week({})["snapshot"]
    check("fin d'effet : plus de voix", "voix" not in snap)


def test_reste():
    print("\n[G] ce qui reste")
    s = _serveur()
    gs = s.engine.game_state
    tid = gs["tiles"][0].tile_id
    maitrise.enregistrer_preuve(gs, P, "lombric", poids=0)       # palier 1
    for _ in range(4):
        maitrise.enregistrer_preuve(gs, P, "merle", poids=100)  # palier 5 → plafonné
    maitrise.decouvrir(gs, P, "carabe")
    while maitrise.palier(gs, P, "carabe") < 4:
        maitrise.enregistrer_preuve(gs, P, "carabe")
    _manger(s, "psilocybe")
    for _ in range(10):
        s.cmd_parler({"espece": "lombric", "tile": tid, "r": 1, "c": 1})
    for esp in ("carabe", "merle", "pleurote"):
        for _ in range(3):
            s.cmd_parler({"espece": esp, "tile": tid, "r": 1, "c": 1})
    s.cmd_parler({"espece": "cloporte", "tile": tid, "r": 1, "c": 1})
    av = {e: maitrise.palier(gs, P, e)
          for e in ("lombric", "carabe", "merle", "pleurote", "cloporte")}
    s.cmd_step_week({})
    check("pendant l'effet : rien n'est encore crédité",
          all(maitrise.palier(gs, P, e) == p for e, p in av.items()))
    snap = s.cmd_step_week({})["snapshot"]
    ap = {e: maitrise.palier(gs, P, e) for e in av}
    check("10 survols → +1 palier exactement (une fois par vision)",
          ap["lombric"] == av["lombric"] + 1, (av["lombric"], ap["lombric"]))
    check("jamais jusqu'au transcendant (4 reste 4, 5 reste 5)",
          ap["carabe"] == 4 and ap["merle"] == 5)
    check("espèce inconnue assez survolée → découverte (palier 1)", ap["pleurote"] == 1)
    check("1 seul survol → rien", ap["cloporte"] == 0)
    check("la vue est notifiée une fois (`reste`)",
          sorted(snap["player"]["vision"]["reste"]) == ["lombric", "pleurote"]
          and s.cmd_snapshot({})["snapshot"]["player"]["vision"]["reste"] == [],
          snap["player"]["vision"]["reste"])


if __name__ == "__main__":
    _orig = (CM.sample_carpophores, CM.pluie_semaine_precedente)
    try:
        test_comestibilite()
        test_disparition_et_nom()
        test_duree_et_lecture()
        test_isolation()
        test_parler()
        test_overdose()
        test_reste()
    finally:
        CM.sample_carpophores, CM.pluie_semaine_precedente = _orig
    ok = sum(1 for _, c in _results if c)
    print(f"\n{ok}/{len(_results)} vérifications OK")
    raise SystemExit(0 if ok == len(_results) else 1)
