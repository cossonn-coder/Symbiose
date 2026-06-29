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

Le palier de l'ESPÈCE est posé directement (raccourci de test, comme test_carnet).
Lecture pure → déterminisme total.

Usage (depuis data/code/) :
  python3 -m tests.test_encyclopedie
"""
from sim import encyclopedie
from sim.encyclopedie_corpus import FICHES
from sim import maitrise
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
    check("index = [tomate] seule découverte", idx == ["tomate"], f"{idx}")
    check("basilic (palier 0) absent de l'index", "basilic" not in idx)
    check("lire basilic (palier 0) → None",
          encyclopedie.encyclopedie_lire(gs, "j1", "basilic") is None)
    # index trié dans l'ordre stable du corpus
    _poser_palier(gs, "j1", "haricot", 1)       # haricot vient après poivron au §6
    _poser_palier(gs, "j1", "poivron", 1)
    idx2 = encyclopedie.encyclopedie_index(gs, "j1")
    ordre_corpus = [e for e in FICHES if e in {"tomate", "poivron", "haricot"}]
    check("index trié dans l'ordre du corpus", idx2 == ordre_corpus, f"{idx2}")


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


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Encyclopédie (Voix narratives ④)")
    print("=" * 60)
    test_sans_joueur()
    test_troncature()
    test_non_decouvert()
    test_alignement_cles()
    test_fiches_completes()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
