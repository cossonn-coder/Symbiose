"""
SYMBIOSE — tests/test_champignon_voix.py
LE SOL QUI RESPIRE ⑤ — les voix des 13 champignons (D111 §3.4).

  A. Complétude : CHAQUE espèce du registre `fields/fongique` a ses voix —
     encyclopédie 3 niveaux, carnet D/I + concept, `vu`, comestibilité, article ;
     type `champignon` ; pages de lore (polypore, psilocybe, tue-mouches, morille,
     ronds de sorcière) présentes et rattachées aux concepts fongiques.
  B. Le `vu` (avant le nom) ne dit ni le nom ni la comestibilité.
  C. Parcours de survols (pont `observer_espece`) : nom en 3 saisons ; comestibilité
     absente avant, présente après ; concept découvert puis crédité au nom ; note
     `fructification` au ledger, dédupliquée par saison ; carnet D → I au palier du
     concept ; article du magazine après le nom ; page récompense au palier 3.
  D. L'ancienne clé générique `champignon` est muette.

Usage (depuis data/code/) : python3 -m tests.test_champignon_voix
"""
from fields.fongique import REGISTRE_FONGIQUE, COMESTIBLE, VENENEUX, MORTEL
from sim import maitrise, carnet, encyclopedie, pages
from sim import encyclopedie_types as ET
from sim import signes as SG
from sim.champignon_encyclo import (FICHES_CHAMPIGNON, SAPROPHYTIE, MYCORHIZE,
                                    PARASITISME, SOSIES)
from sim.champignon_voix import KIND_FRUCTIFICATION
from sim.magazine import magazine_articles
from sim.pages_corpus import PAGES
from tools.simserver.maitrise_pont import observer_espece

P = "joueur_1"
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def test_completude():
    print("\n[A] toutes les voix, pour chaque espèce du registre")
    check("corpus = registre (mêmes 13 clés, même ordre)",
          list(FICHES_CHAMPIGNON) == list(REGISTRE_FONGIQUE), list(FICHES_CHAMPIGNON))
    concepts = {SAPROPHYTIE, MYCORHIZE, PARASITISME, SOSIES}
    muettes = []
    for cle, f in FICHES_CHAMPIGNON.items():
        ok = (set(f["fiche"]) == {1, 2, 3} and all(f["fiche"][n].strip() for n in (1, 2, 3))
              and set(f["carnet"]) == {"descriptif", "interprétatif"}
              and f["concept"] in concepts and f["vu"] and f["comestibilite"]
              and len(f["article"]) == 2 and all(f["article"])
              and ET.type_de(cle) == "champignon"
              and carnet.CONCEPT_DE[(KIND_FRUCTIFICATION, cle)] == f["concept"]
              and all((KIND_FRUCTIFICATION, cle, r) in carnet.GABARIT
                      for r in ("descriptif", "interprétatif")))
        if not ok:
            muettes.append(cle)
    check("aucune espèce muette", not muettes, muettes)
    check("chaque concept fongique illustré par ≥ 2 espèces",
          all(sum(f["concept"] == c for f in FICHES_CHAMPIGNON.values()) >= 2
              for c in concepts))
    pages_f = {p["concept"] for p in PAGES.values()} & concepts
    check("les 4 concepts fongiques ont leur page secrète", pages_f == concepts, pages_f)
    lore = " ".join(PAGES[p]["texte"] for p in ("P43", "P44", "P45", "P46", "P47"))
    check("pages de lore : amadou, clochette, bouleau, morilles, ronds de sorcière",
          all(m in lore for m in ("amadou", "clochette", "bouleau", "morilles",
                                  "ronds de sorcière")))
    # Concordance comestibilité registre ↔ texte (mortel dit « mortel », etc.).
    discord = [k for k, e in REGISTRE_FONGIQUE.items()
               if (MORTEL in e.comestibilite) != ("mortel" in FICHES_CHAMPIGNON[k]["comestibilite"])
               or (VENENEUX in e.comestibilite and COMESTIBLE not in e.comestibilite
                   and "comestible" in FICHES_CHAMPIGNON[k]["comestibilite"])]
    check("comestibilité du texte = tags du registre", not discord, discord)


def test_vu_muet():
    print("\n[B] le `vu` ne trahit ni le nom ni la comestibilité")
    mots = ("comestible", "mortel", "vénéneux", "toxique", "psychédélique")
    fuites = [k for k, f in FICHES_CHAMPIGNON.items()
              if any(m in f["vu"].lower() for m in mots)
              or REGISTRE_FONGIQUE[k].nom.lower() in f["vu"].lower()]
    check("aucune fuite", not fuites, fuites)
    fuites_c = [k for k, f in FICHES_CHAMPIGNON.items()
                if "{e}" in "".join(f["carnet"].values())
                or any(m in "".join(f["carnet"].values()).lower() for m in mots)]
    check("le carnet ne nomme pas et ne dit pas la comestibilité", not fuites_c, fuites_c)


def test_parcours():
    print("\n[C] survols : nom, comestibilité, concept, ledger, carnet, magazine")
    gs = {}
    zone = ("T0", 3, 4)
    # Clitocybe (sosies) : saisons 2, 2, 6, 9 (semaine consignée).
    for s in (30, 35):
        observer_espece(gs, P, "clitocybe", s, zone=zone)
    check("1er survol : palier 1, concept `sosies` découvert",
          maitrise.palier(gs, P, "clitocybe") == 1 and maitrise.palier(gs, P, SOSIES) == 1)
    notes = [e for e in gs["journal"][P]["entries"] if e["kind"] == KIND_FRUCTIFICATION]
    check("une seule note de fructification dans la saison (dédup)",
          len(notes) == 1 and notes[0]["cause"] == "clitocybe" and notes[0]["zone"] == zone,
          notes)
    check("pas encore nommé : ni dans `faune`, ni comestibilité",
          "clitocybe" not in SG.appris(gs, P)["faune"]
          and SG.appris(gs, P)["champignons"] == {})
    fiche = encyclopedie.encyclopedie_lire(gs, P, "clitocybe")
    check("encyclopédie palier 1 : niveau 1 seul (pas la comestibilité)",
          fiche["niveau_max"] == 1 and set(fiche["niveaux"]) == {1}, fiche)
    check("magazine : pas d'article avant le nom", magazine_articles(gs, P) == [])
    for s in (82, 134):
        observer_espece(gs, P, "clitocybe", s, zone=zone)
    ap = SG.appris(gs, P)
    check("3 saisons → nommé, comestibilité dite",
          "clitocybe" in ap["faune"]
          and ap["champignons"]["clitocybe"]["comestibilite"].startswith("mortel"), ap)
    check("nommer crédite le concept (+1 → 2)", maitrise.palier(gs, P, SOSIES) == 2,
          maitrise.palier(gs, P, SOSIES))
    check("note par saison neuve (3 saisons → 3 notes)",
          sum(e["kind"] == KIND_FRUCTIFICATION for e in gs["journal"][P]["entries"]) == 3)
    check("article du magazine après le nom",
          [a["cle"] for a in magazine_articles(gs, P)] == ["clitocybe"])
    c = carnet.carnet_lire(gs, P, filtre={"espece": "clitocybe"})
    check("carnet : descriptif tant que `sosies` < 3",
          c and all(e["registre"] == "descriptif" and e["concept"] == SOSIES for e in c), c)
    # Un 2ᵉ sosie nommé → concept au palier 3 → carnet interprétatif + page.
    for s in (30, 82, 134):
        observer_espece(gs, P, "hypholome", s)
    check("2ᵉ sosie nommé → `sosies` palier 3", maitrise.palier(gs, P, SOSIES) == 3)
    c = carnet.carnet_lire(gs, P, filtre={"espece": "clitocybe"})
    check("carnet : bascule interprétative (rétroactive)",
          all(e["registre"] == "interprétatif" for e in c), c)
    check("page secrète des sosies révélée (P47)", "P47" in pages.pages_trouvees(gs, P))
    for s in (30, 82, 134, 190):
        observer_espece(gs, P, "amanite_phalloide", s)
    check("concept plafonné au seuil du carnet", maitrise.palier(gs, P, SOSIES) == 3)


def test_cle_generique():
    print("\n[D] l'ancienne clé générique est muette")
    gs = {}
    check("observer('champignon') → no-op",
          observer_espece(gs, P, "champignon", 30) is False and not gs.get("maitrise"))


if __name__ == "__main__":
    test_completude()
    test_vu_muet()
    test_parcours()
    test_cle_generique()
    ok = sum(1 for _, c in _results if c)
    print(f"\n{ok}/{len(_results)} OK")
    raise SystemExit(0 if ok == len(_results) else 1)
