"""
SYMBIOSE — tests/test_signes_legende.py
Légende des signes côté Python (sprint PLANTE ASSEMBLÉE ⑥).
Spec : `docs/rendu/pixelart/conception_plante_assemblee.md` §4.4 + kickoff
`sprints/rendu/pixelart/sprint_plante_assemblee/06_signes_python.md`.

  A. Exhaustivité : les 11 signes de `semiologie` et toutes les bêtes de
     `FAUNE_ENCYCLO` ont leur corpus ; concepts existants ; aucun signe ne collide
     avec une clé classée par `encyclopedie_types.type_de`.
  B. Observation → une entrée ledger `kind="signe"` ; dédup (espèce, signe, saison) ;
     signe inconnu refusé ; nouvelle saison → nouvelle note. Aucune maîtrise créditée.
  C. Carnet : registre D puis I quand le palier du concept franchit le seuil.
  D. `appris` vide au départ, rempli après palier forcé (debug `palier3`) ; option
     « anticipé » au seuil 1.
  E. Encyclopédie : fiche « signe » verrouillée puis ouverte, index tagué `signe`.
  F. Pont : `observer` + `signe` (rétro-compatible), `player.appris` au snapshot.

Usage (depuis data/code/) : python3 -m tests.test_signes_legende
"""
from sim import carnet, encyclopedie, maitrise, semiologie
from sim import signes as SG
from sim import encyclopedie_types as ET
from sim.signes_corpus import SIGNES, FAUNE_VU
from sim.concept_corpus import FICHES_CONCEPT
from sim.pages_corpus import PAGES
from fields.faune_encyclo import FAUNE_ENCYCLO

P = "joueur_1"
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _poser_palier(gs, objet, p):
    maitrise.decouvrir(gs, P, objet)
    gs["maitrise"][P]["objets"][objet]["palier"] = p


def test_exhaustivite():
    print("\n[A] corpus exhaustif")
    attendus = {c for c, _ in semiologie.DETECTEURS} | {"maladie", "gel", "grele"}
    check("11 signes attendus", len(attendus) == 11, sorted(attendus))
    check("corpus = exactement les 11 signes", set(SIGNES) == attendus,
          sorted(set(SIGNES) ^ attendus))
    check("toutes les causes de PRIORITE ont un corpus",
          set(semiologie.PRIORITE) == set(SIGNES))
    complet = all(s["vu"] and s["concept"] and set(s["fiche"]) == {1, 2, 3}
                  and set(s["carnet"]) == {"descriptif", "interprétatif"}
                  for s in SIGNES.values())
    check("chaque signe : vu + concept + fiche 1-3 + carnet D/I", complet)
    # Concepts EXISTANTS : déjà utilisés par le carnet, l'encyclopédie ou les pages.
    connus = (set(carnet.CONCEPT_DE.values()) | set(FICHES_CONCEPT)
              | {p["concept"] for p in PAGES.values()})
    inconnus = {s["concept"] for s in SIGNES.values()} - connus
    check("aucun concept inventé", not inconnus, inconnus)
    check("faune : une description visible par bête", set(FAUNE_VU) == set(FAUNE_ENCYCLO),
          sorted(set(FAUNE_VU) ^ set(FAUNE_ENCYCLO)))
    check("aucune description de bête ne la nomme",
          all(k not in v for k, v in FAUNE_VU.items()))
    check("aucun signe classé par type_de (pas de collision)",
          all(ET.type_de(s) is None for s in SIGNES))


def test_observation():
    print("\n[B] observation → ledger + dédup")
    gs = {}
    ok = SG.observer_signe(gs, P, "tomate", "gel", ("T0", 2, 3), 10)
    entrees = gs["journal"][P]["entries"]
    check("1ʳᵉ observation écrite", ok and len(entrees) == 1)
    check("entrée ledger bien formée", entrees[0] == {
        "semaine": 10, "zone": ("T0", 2, 3), "kind": "signe",
        "cause": "gel", "espece": "tomate"}, entrees[0])
    check("même (espèce, signe, saison) → dédup",
          not SG.observer_signe(gs, P, "tomate", "gel", ("T0", 4, 4), 12))
    check("autre espèce → nouvelle note", SG.observer_signe(gs, P, "ail", "gel", ("T0",), 12))
    check("autre signe → nouvelle note",
          SG.observer_signe(gs, P, "tomate", "maladie", ("T0",), 12))
    check("saison suivante (s14) → nouvelle note",
          SG.observer_signe(gs, P, "tomate", "gel", ("T0",), 14))
    check("signe inconnu → refusé", not SG.observer_signe(gs, P, "tomate", "zorglub", (), 14))
    check("4 notes au total", len(gs["journal"][P]["entries"]) == 4)
    check("aucune maîtrise créditée", "maitrise" not in gs)


def test_carnet():
    print("\n[C] carnet : descriptif puis interprétatif au seuil du concept")
    gs = {}
    SG.observer_signe(gs, P, "tomate", "secheresse", ("T0", 1, 1), 20)
    n = carnet.carnet_lire(gs, P)
    check("concept = eau", n[0]["concept"] == "eau", n[0]["concept"])
    check("palier 0 → descriptif", n[0]["registre"] == "descriptif")
    check("texte descriptif sans cause", "soif" not in n[0]["texte"]
          and "tomate" in n[0]["texte"], n[0]["texte"])
    _poser_palier(gs, "eau", 2)
    check("palier 2 → encore descriptif", carnet.carnet_lire(gs, P)[0]["registre"] == "descriptif")
    _poser_palier(gs, "eau", 3)
    n = carnet.carnet_lire(gs, P)
    check("palier 3 → interprétatif", n[0]["registre"] == "interprétatif")
    check("texte interprétatif nomme la cause", "soif" in n[0]["texte"], n[0]["texte"])


def test_appris():
    print("\n[D] appris : vide, puis rempli au seuil")
    gs = {}
    check("vide au départ", SG.appris(gs, P) == {"signes": [], "faune": []})
    check("lecture pure (aucune clé créée)", gs == {})
    _poser_palier(gs, "météo", 3)
    check("météo p3 → gel + grêle appris", SG.appris(gs, P)["signes"] == ["gel", "grele"],
          SG.appris(gs, P))
    _poser_palier(gs, "coccinelle", 1)
    check("bête au palier 1 → pas apprise", SG.appris(gs, P)["faune"] == [])
    gs["options"] = {P: {"carnet_anticipe": True}}
    check("option anticipée → bête apprise dès p1",
          SG.appris(gs, P)["faune"] == ["coccinelle"])


def test_encyclopedie():
    print("\n[E] fiche « signe » : verrouillée puis ouverte")
    gs = {}
    check("non appris → None", encyclopedie.encyclopedie_lire(gs, P, "ombre") is None)
    check("index sans signe", not encyclopedie.encyclopedie_index(gs, P, "signe"))
    _poser_palier(gs, "lumière", 3)
    f = encyclopedie.encyclopedie_lire(gs, P, "ombre")
    check("appris → fiche 3 niveaux", f and f["type"] == "signe" and f["niveau_max"] == 3
          and f["niveaux"][3] == SIGNES["ombre"]["fiche"][3], f)
    idx = encyclopedie.encyclopedie_index(gs, P, "signe")
    check("index : ombre tagué signe", idx == [{"cle": "ombre", "type": "signe",
                                                 "titre": "ombre"}], idx)
    gs2 = {"options": {P: {"carnet_anticipe": True}}}
    _poser_palier(gs2, "lumière", 1)
    f2 = encyclopedie.encyclopedie_lire(gs2, P, "ombre")
    check("anticipé p1 → fiche niveau 1 seulement", f2 and f2["niveau_max"] == 1, f2)


def test_pont():
    print("\n[F] pont : observer + signe, player.appris")
    from tests.simserver.harness import ServerProc
    s = ServerProc()
    s.send(cmd="init", config="full", seed=7)
    s.send(cmd="step_week")
    r = s.send(cmd="observer", species="Tomato")
    check("observer sans signe : rétro-compatible", r["ok"] and "signe_note" not in r, r)
    r = s.send(cmd="observer", species="Tomato", signe="gel", tile="T0", x_cm=120, y_cm=60)
    check("observer + signe → note écrite", r["ok"] and r["signe_note"] is True, r)
    r = s.send(cmd="observer", species="Tomato", signe="gel", tile="T0", x_cm=10, y_cm=10)
    check("même saison → dédup", r["ok"] and r["signe_note"] is False, r)
    notes = s.send(cmd="carnet")
    check("le carnet lit la note de signe",
          notes["ok"] and any("liseré brun-noir" in n["texte"] for n in notes["entrees"]),
          [n["texte"] for n in notes.get("entrees", [])][-2:])
    lg = s.send(cmd="legende")
    check("legende : 11 signes + toute la faune (vu)",
          lg["ok"] and set(lg["signes"]) == set(SIGNES) and set(lg["faune"]) == set(FAUNE_ENCYCLO)
          and lg["signes"]["gel"]["vu"] == SIGNES["gel"]["vu"])
    check("legende : nom de cause court (⑦ info-bulle apprise)",
          lg["signes"]["chlorose"]["cause"] == "Chlorose ferrique"
          and all(0 < len(v["cause"]) < 40 for v in lg["signes"].values()),
          {k: v["cause"] for k, v in lg["signes"].items()})
    snap = s.send(cmd="snapshot")["snapshot"]
    check("snapshot : player.appris vide", snap["player"]["appris"] == {"signes": [], "faune": []})
    s.send(cmd="debug", op="palier3")
    ap = s.send(cmd="snapshot")["snapshot"]["player"]["appris"]
    # INFO-BULLE DU VIVANT ③ : palier3 crédite aussi le champignon (en dernier).
    check("après palier3 : 11 signes + toute la faune + champignon",
          len(ap["signes"]) == 11 and ap["faune"] == [*FAUNE_ENCYCLO, "champignon"], ap)
    s.send(cmd="quit")
    check("quit → exit 0", s.close() == 0)


if __name__ == "__main__":
    test_exhaustivite()
    test_observation()
    test_carnet()
    test_appris()
    test_encyclopedie()
    test_pont()
    ko = [n for n, ok in _results if not ok]
    print(f"\n{len(_results) - len(ko)}/{len(_results)} OK")
    raise SystemExit(1 if ko else 0)
