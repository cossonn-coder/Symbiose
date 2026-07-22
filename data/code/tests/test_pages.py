"""
SYMBIOSE — tests/test_pages.py
Test des PAGES SECRÈTES (sprint Voix narratives, tronçon ⑤, dette D18).
Spec : `docs/narration/voix/conception_voix_narratives.md` §2.3/§7 + kickoff
`sprints/sprint_voix_narratives/05_pages.md`.

Propriétés exigées (« Définition de done » du kickoff) :
  A. SANS JOUEUR → `pages_trouvees` = set() ET aucune clé `pages` créée (golden-safe).
  B. ROBINET RÉCOMPENSE — concept X → page DE concept X, ordre par palier_theme ;
     concept épuisé → `None`.
  C. ROBINET FOUILLE — prochaine page due GLOBALE ; épuisable → `None`.
  D. ROBINET HASARD — DÉTERMINISME : même seed + même semaine ⟹ même page.
  E. ÉPUISABLE — jamais de re-révélation ; tout trouvé → tous robinets muets.
  F. ZÉRO EFFET MÉCANIQUE — `reveler_page` ne touche QUE `gs["pages"]`, aucun autre
     champ de `gs` ne change avant/après.
  G. CORPUS — 29 entrées P01..P29, champs complets, concepts/robinets recopiés.

Usage (depuis data/code/) :
  python3 -m tests.test_pages
"""
import copy

from sim import pages
from sim.pages_corpus import PAGES, ORDRE

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# A. Sans joueur → set() vide, aucune clé créée (no-op golden)
# ---------------------------------------------------------------------------

def test_sans_joueur():
    gs = {}
    check("pages_trouvees sans joueur → set()", pages.pages_trouvees(gs, "j1") == set())
    check("aucune clé `pages` créée par la lecture", gs == {}, f"{gs}")


# ---------------------------------------------------------------------------
# B. Robinet récompense → page du bon concept, ordre par palier_theme, épuisable
# ---------------------------------------------------------------------------

def test_recompense_concept():
    gs = {}
    # concept `non-action` : P01 (pt4), P08 (pt4), P19 (pt4) — toutes palier_theme 4,
    # départage par ordre du corpus (P01 < P08 < P19).
    p1 = pages.reveler_page(gs, "j1", "récompense", {"concept": "non-action"})
    check("récompense non-action → page de concept non-action",
          PAGES[p1]["concept"] == "non-action", p1)
    check("1ʳᵉ due non-action = P01 (ordre corpus)", p1 == "P01", p1)
    p2 = pages.reveler_page(gs, "j1", "récompense", {"concept": "non-action"})
    check("2ᵉ due non-action = P08", p2 == "P08", p2)
    p3 = pages.reveler_page(gs, "j1", "récompense", {"concept": "non-action"})
    check("3ᵉ due non-action = P19", p3 == "P19", p3)
    # concept épuisé → None (muet)
    p4 = pages.reveler_page(gs, "j1", "récompense", {"concept": "non-action"})
    check("concept non-action épuisé → None", p4 is None, f"{p4}")
    # un autre concept reste disponible
    p5 = pages.reveler_page(gs, "j1", "récompense", {"concept": "transcendance"})
    check("récompense transcendance → page transcendance",
          p5 is not None and PAGES[p5]["concept"] == "transcendance", p5)
    # concept inexistant → None
    check("concept inconnu → None",
          pages.reveler_page(gs, "j1", "récompense", {"concept": "zzz"}) is None)


# ---------------------------------------------------------------------------
# C. Robinet fouille → prochaine page due globale, épuisable
# ---------------------------------------------------------------------------

def test_fouille_globale():
    gs = {}
    # palier_theme minimal du corpus = 2 ; 1ʳᵉ due globale = 1ʳᵉ pt=2 dans l'ordre.
    attendu = sorted([pid for pid in ORDRE], key=lambda p: PAGES[p]["palier_theme"])[0]
    p = pages.reveler_page(gs, "j1", "fouille", {})
    check("fouille → 1ʳᵉ page due globale (palier_theme min)", p == attendu, f"{p} vs {attendu}")
    # consommer tout le corpus → None ensuite
    trouvees = pages.pages_trouvees(gs, "j1")
    while pages.reveler_page(gs, "j1", "fouille", {}) is not None:
        pass
    check("fouille épuise tout le corpus (33 pages)",
          len(pages.pages_trouvees(gs, "j1")) == 33,
          f"{len(pages.pages_trouvees(gs, 'j1'))}")
    check("fouille corpus épuisé → None",
          pages.reveler_page(gs, "j1", "fouille", {}) is None)


# ---------------------------------------------------------------------------
# D. Robinet hasard → déterminisme (même seed + semaine ⟹ même page)
# ---------------------------------------------------------------------------

def test_hasard_deterministe():
    gs_a, gs_b = {}, {}
    ctx = {"seed": 0x5AB1057E, "semaine": 42}
    pa = pages.reveler_page(gs_a, "j1", "hasard", ctx)
    pb = pages.reveler_page(gs_b, "j1", "hasard", dict(ctx))
    check("hasard : même seed+semaine ⟹ même page", pa == pb, f"{pa} vs {pb}")
    check("hasard : page révélée non None", pa is not None, f"{pa}")
    # semaine différente ⟹ tirage potentiellement différent, jamais une erreur
    pc = pages.reveler_page({}, "j1", "hasard", {"seed": ctx["seed"], "semaine": 7})
    check("hasard : autre semaine ⟹ page valide", pc in PAGES, f"{pc}")
    # hasard épuisable : on vide tout, puis None
    gs = {}
    s, w = 1, 0
    while pages.reveler_page(gs, "j1", "hasard", {"seed": s, "semaine": w}) is not None:
        w += 1
    check("hasard épuise tout le corpus (33 pages)",
          len(pages.pages_trouvees(gs, "j1")) == 33,
          f"{len(pages.pages_trouvees(gs, 'j1'))}")
    check("hasard corpus épuisé → None",
          pages.reveler_page(gs, "j1", "hasard", {"seed": s, "semaine": w + 1}) is None)


# ---------------------------------------------------------------------------
# E. Épuisable & jamais de re-révélation
# ---------------------------------------------------------------------------

def test_jamais_re_revelation():
    gs = {}
    vues = set()
    for _ in range(45):                       # > 33 : sur-tire volontairement
        p = pages.reveler_page(gs, "j1", "fouille", {})
        if p is None:
            break
        check(f"page {p} jamais re-révélée", p not in vues, f"déjà vue : {p}")
        vues.add(p)
    check("exactement 33 pages distinctes révélées", len(vues) == 33, f"{len(vues)}")
    # robinet inconnu → toujours None (jamais de crash)
    check("robinet inconnu → None",
          pages.reveler_page({}, "j1", "zzz", {}) is None)


# ---------------------------------------------------------------------------
# F. ZÉRO effet mécanique : seul gs["pages"] change
# ---------------------------------------------------------------------------

def test_zero_effet_mecanique():
    # gs « jouet » avec des champs éco factices : on vérifie qu'aucun ne bouge.
    gs = {
        "seed": 123, "week": 9,
        "eco": {"T0": {"humidite": [0.5, 0.5], "fertilite": [0.3]}},
        "tiles": ["T0"],
        "maitrise": {"j1": {"objets": {}}},
    }
    avant = copy.deepcopy({k: v for k, v in gs.items() if k != "pages"})
    pages.reveler_page(gs, "j1", "fouille", {})
    apres = {k: v for k, v in gs.items() if k != "pages"}
    check("aucun champ écologique modifié par reveler_page", apres == avant,
          "un champ a changé !")
    check("seule la clé `pages` a été créée/écrite",
          "pages" in gs and len(gs["pages"]["j1"]) == 1, f"{gs.get('pages')}")


# ---------------------------------------------------------------------------
# G. Corpus complet & fidèle
# ---------------------------------------------------------------------------

def test_corpus():
    check("corpus = 33 pages", len(PAGES) == 33, f"{len(PAGES)}")
    ids = sorted(PAGES)
    check("ids = P01..P33", ids == [f"P{i:02d}" for i in range(1, 34)], f"{ids}")
    champs = {"id", "titre", "voix", "concept", "palier_theme", "robinet", "texte"}
    incomplets = [pid for pid, f in PAGES.items()
                  if set(f) != champs or not f["texte"].strip()]
    check("chaque page a tous ses champs non vides", incomplets == [], f"{incomplets}")
    robinets_ok = all(PAGES[p]["robinet"] in {"hasard", "récompense", "fouille"}
                      for p in PAGES)
    check("tous les robinets ∈ {hasard, récompense, fouille}", robinets_ok)
    voix_ok = all(PAGES[p]["voix"] in {"A", "B", "C", "D", "E"} for p in PAGES)
    check("toutes les voix ∈ {A..E}", voix_ok)
    check("ORDRE = 33 ids alignés sur PAGES", len(ORDRE) == 33 and set(ORDRE) == set(PAGES))


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Pages secrètes (Voix narratives ⑤)")
    print("=" * 60)
    test_sans_joueur()
    test_recompense_concept()
    test_fouille_globale()
    test_hasard_deterministe()
    test_jamais_re_revelation()
    test_zero_effet_mecanique()
    test_corpus()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
