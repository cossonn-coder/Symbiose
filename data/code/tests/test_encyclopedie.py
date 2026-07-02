"""
SYMBIOSE — tests/test_encyclopedie.py
Test de l'ENCYCLOPÉDIE (sprint Voix narratives, tronçon ④).
Spec : `docs/conception/CONCEPTION_VOIX_NARRATIVES.md` §2.2/§6 + kickoff
`sprints/sprint_voix_narratives/04_encyclopedie.md`.

Propriétés exigées (« Définition de done » du kickoff) :
  A. SANS JOUEUR → index `[]`, lecture → `None` (golden-safe, lecture pure).
  B. TRONCATURE — palier 1/2/3 → fiche au BON niveau ; palier 4/5 → plafonné à 3.
  C. NON DÉCOUVERT (palier 0) → ABSENT de l'index ET lecture → `None`.
  D. ALIGNEMENT DES CLÉS — toutes les clés du corpus existent au catalogue, et le
     corpus couvre EXACTEMENT les 28 espèces (PLANT + PERENNIAL).
  E. CHAQUE FICHE a bien ses 3 niveaux non vides.

D60 (tronçon ① — encyclopédie multi-règnes) ajoute :
  F. TYPE_DE couvre toutes les clés attendues, SANS collision (priorité stable).
  G. INDEX TAGUÉ — chaque entrée = `{cle, type, titre}` ; filtre par type.
  H. DISPATCH MONO-NIVEAU — animal + champignon → 1 niveau (blurb + graphe),
     plafonnés palier 1 même à palier supérieur.

Le palier de l'ESPÈCE est posé directement (raccourci de test, comme test_carnet).
Lecture pure → déterminisme total.

Usage (depuis data/code/) :
  python3 -m tests.test_encyclopedie
"""
from sim import encyclopedie
from sim.encyclopedie_corpus import FICHES
from sim import maitrise
from sim import encyclopedie_types as ET
from sim.champignon_encyclo import CLE_CHAMPIGNON
from fields.faune_encyclo import FAUNE_ENCYCLO
from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _poser_palier(gs, player, espece, p):
    """Pose DIRECTEMENT le palier d'une espèce (raccourci de test) : découverte via
    l'API puis écriture du palier — évite de compter les preuves de la courbe."""
    maitrise.decouvrir(gs, player, espece)
    gs["maitrise"][player]["objets"][espece]["palier"] = p


# ---------------------------------------------------------------------------
# A. Sans joueur → [] / None
# ---------------------------------------------------------------------------

def test_sans_joueur():
    gs = {}
    check("index sans joueur → []", encyclopedie.encyclopedie_index(gs, "j1") == [])
    check("lire sans joueur → None",
          encyclopedie.encyclopedie_lire(gs, "j1", "tomate") is None)
    # aucune clé créée par les lectures (no-op golden)
    check("aucune clé maitrise/journal créée", gs == {}, f"{gs}")


# ---------------------------------------------------------------------------
# B. Troncature au bon niveau (1/2/3 et plafond 3 pour 4/5)
# ---------------------------------------------------------------------------

def test_troncature():
    gs = {}
    _poser_palier(gs, "j1", "tomate", 1)
    f1 = encyclopedie.encyclopedie_lire(gs, "j1", "tomate")
    check("palier 1 → niveau_max=1, 1 niveau",
          f1["niveau_max"] == 1 and set(f1["niveaux"]) == {1}, f"{f1['niveaux'].keys()}")
    check("palier 1 → N1 = corpus", f1["niveaux"][1] == FICHES["tomate"][1])

    _poser_palier(gs, "j1", "tomate", 2)
    f2 = encyclopedie.encyclopedie_lire(gs, "j1", "tomate")
    check("palier 2 → niveau_max=2, niveaux {1,2}",
          f2["niveau_max"] == 2 and set(f2["niveaux"]) == {1, 2})
    check("palier 2 → N2 = corpus", f2["niveaux"][2] == FICHES["tomate"][2])

    _poser_palier(gs, "j1", "tomate", 3)
    f3 = encyclopedie.encyclopedie_lire(gs, "j1", "tomate")
    check("palier 3 → niveau_max=3, niveaux {1,2,3}",
          f3["niveau_max"] == 3 and set(f3["niveaux"]) == {1, 2, 3})

    # paliers 4 et 5 : plafonnés à 3 (décision A figée)
    _poser_palier(gs, "j1", "tomate", 4)
    f4 = encyclopedie.encyclopedie_lire(gs, "j1", "tomate")
    check("palier 4 → plafond niveau_max=3", f4["niveau_max"] == 3)
    _poser_palier(gs, "j1", "tomate", 5)
    f5 = encyclopedie.encyclopedie_lire(gs, "j1", "tomate")
    check("palier 5 → plafond niveau_max=3, pas de N4",
          f5["niveau_max"] == 3 and 4 not in f5["niveaux"])


# ---------------------------------------------------------------------------
# C. Non découvert (palier 0) → absent de l'index + lecture None
# ---------------------------------------------------------------------------

def test_non_decouvert():
    gs = {}
    _poser_palier(gs, "j1", "tomate", 2)        # une seule espèce découverte
    idx = encyclopedie.encyclopedie_index(gs, "j1")
    cles = [e["cle"] for e in idx]
    check("index = [tomate] seule découverte", cles == ["tomate"], f"{cles}")
    check("basilic (palier 0) absent de l'index", "basilic" not in cles)
    check("lire basilic (palier 0) → None",
          encyclopedie.encyclopedie_lire(gs, "j1", "basilic") is None)
    # index trié dans l'ordre stable du corpus
    _poser_palier(gs, "j1", "haricot", 1)       # haricot vient après poivron au §6
    _poser_palier(gs, "j1", "poivron", 1)
    cles2 = [e["cle"] for e in encyclopedie.encyclopedie_index(gs, "j1")]
    ordre_corpus = [e for e in FICHES if e in {"tomate", "poivron", "haricot"}]
    check("index trié dans l'ordre du corpus", cles2 == ordre_corpus, f"{cles2}")


# ---------------------------------------------------------------------------
# D. Alignement des clés corpus ⟷ catalogue
# ---------------------------------------------------------------------------

def test_alignement_cles():
    cat = {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}
    hors_cat = [k for k in FICHES if k not in cat]
    check("toutes les clés corpus existent au catalogue",
          hors_cat == [], f"orphelines : {hors_cat}")
    sans_fiche = [k for k in cat if k not in FICHES]
    check("toutes les espèces catalogue ont une fiche",
          sans_fiche == [], f"muettes : {sans_fiche}")
    check("corpus = 28 fiches", len(FICHES) == 28, f"{len(FICHES)}")


# ---------------------------------------------------------------------------
# E. Chaque fiche a ses 3 niveaux non vides
# ---------------------------------------------------------------------------

def test_fiches_completes():
    incompletes = [k for k, f in FICHES.items()
                   if set(f) != {1, 2, 3} or not all(f[n].strip() for n in (1, 2, 3))]
    check("chaque fiche = 3 niveaux non vides",
          incompletes == [], f"incomplètes : {incompletes}")


# ---------------------------------------------------------------------------
# F. type_de couvre les clés attendues, sans collision (D60 ①)
# ---------------------------------------------------------------------------

def test_type_de():
    # chaque catégorie est bien taguée par son type
    check("tomate → plante", ET.type_de("tomate") == "plante")
    check("chene (pérenne) → plante", ET.type_de("chene") == "plante")
    check("puceron → animal", ET.type_de("puceron") == "animal")
    check("champignon → champignon", ET.type_de(CLE_CHAMPIGNON) == "champignon")
    check("eau → concept", ET.type_de("eau") == "concept")
    check("pollinisation → concept", ET.type_de("pollinisation") == "concept")
    check("arrosage → technique", ET.type_de("arrosage") == "technique")
    check("arrosoir → outil", ET.type_de("arrosoir") == "outil")
    check("planter → geste", ET.type_de("planter") == "geste")
    check("clé inconnue → None", ET.type_de("zorglub") is None)
    # Une SEULE clé multi-catégories aujourd'hui : `grelinette` est à la fois un
    # geste (verbe de `COUTS`) ET un outil (le même mot dans `OBJETS_TOUCHES`).
    # L'ordre de priorité déterministe (outil AVANT geste) la range en OUTIL —
    # cohérent avec l'énumération outils du kickoff. Toute AUTRE clé doit tomber
    # dans son unique type (aucune ambiguïté imprévue ne doit apparaître).
    ensembles = {"plante": ET.PLANTES, "animal": ET.ANIMAUX,
                 "champignon": {CLE_CHAMPIGNON}, "concept": ET.CONCEPTS,
                 "technique": ET.TECHNIQUES, "outil": ET.OUTILS, "geste": ET.GESTES}
    COLLISIONS_CONNUES = {"grelinette"}
    collisions = []
    for nom_type, membres in ensembles.items():
        for cle in membres:
            if cle in COLLISIONS_CONNUES:
                continue
            if ET.type_de(cle) != nom_type:
                collisions.append((cle, nom_type, ET.type_de(cle)))
    check("aucune collision de classification imprévue", collisions == [], f"{collisions}")
    check("grelinette (collision connue) → outil (priorité)",
          ET.type_de("grelinette") == "outil")
    # technique et outil sont disjoints, tous deux couvrent OBJETS_TOUCHES
    check("technique ∩ outil = ∅", not (ET.TECHNIQUES & ET.OUTILS))


# ---------------------------------------------------------------------------
# G. Index tagué + filtre par type (D60 ①)
# ---------------------------------------------------------------------------

def test_index_tague():
    gs = {}
    _poser_palier(gs, "j1", "tomate", 2)
    maitrise.decouvrir(gs, "j1", "puceron")      # animal découvert
    idx = encyclopedie.encyclopedie_index(gs, "j1")
    formes = all(set(e) == {"cle", "type", "titre"} for e in idx)
    check("chaque entrée = {cle, type, titre}", formes, f"{idx}")
    types = {e["cle"]: e["type"] for e in idx}
    check("tomate taguée plante", types.get("tomate") == "plante")
    check("puceron tagué animal", types.get("puceron") == "animal")
    # filtre par type
    idx_pl = encyclopedie.encyclopedie_index(gs, "j1", "plante")
    check("filtre plante → que des plantes",
          all(e["type"] == "plante" for e in idx_pl) and idx_pl, f"{idx_pl}")
    idx_an = encyclopedie.encyclopedie_index(gs, "j1", "animal")
    check("filtre animal → [puceron]",
          [e["cle"] for e in idx_an] == ["puceron"], f"{idx_an}")


# ---------------------------------------------------------------------------
# H. Dispatch mono-niveau : animal + champignon (D60 ①)
# ---------------------------------------------------------------------------

def test_dispatch_mono():
    gs = {}
    _poser_palier(gs, "j1", "puceron", 4)        # palier haut : doit rester capé à 1
    f = encyclopedie.encyclopedie_lire(gs, "j1", "puceron")
    check("animal → type animal, niveau_max=1",
          f["type"] == "animal" and f["niveau_max"] == 1, f"{f}")
    check("animal → blurb = faune_encyclo",
          f["niveaux"][1] == FAUNE_ENCYCLO["puceron"][0])
    check("animal → interconnexions présentes",
          list(f["interconnexions"]) == list(FAUNE_ENCYCLO["puceron"][1]))

    _poser_palier(gs, "j1", CLE_CHAMPIGNON, 3)
    fc = encyclopedie.encyclopedie_lire(gs, "j1", CLE_CHAMPIGNON)
    check("champignon → type champignon, niveau_max=1",
          fc["type"] == "champignon" and fc["niveau_max"] == 1, f"{fc}")
    check("champignon → blurb + graphe non vides",
          fc["niveaux"][1].strip() and fc["interconnexions"])

    # concept/geste sans corpus (④⑤ pas encore là) → None propre
    _poser_palier(gs, "j1", "eau", 2)
    check("concept sans corpus → None (point d'extension)",
          encyclopedie.encyclopedie_lire(gs, "j1", "eau") is None)


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Encyclopédie (Voix narratives ④)")
    print("=" * 60)
    test_sans_joueur()
    test_troncature()
    test_non_decouvert()
    test_alignement_cles()
    test_fiches_completes()
    test_type_de()
    test_index_tague()
    test_dispatch_mono()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
