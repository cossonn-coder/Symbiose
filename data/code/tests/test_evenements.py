"""
SYMBIOSE — tests/test_evenements.py
Test du PARSEUR D'ÉVÉNEMENTS partagé (sprint Voix narratives, tronçon ①).
Spec : `docs/narration/voix/conception_voix_narratives.md` §1.2 + kickoff
`sprints/sprint_voix_narratives/01_evenements.md`.

Vérifie deux choses :
  A. PARITÉ de l'API historique `_evenements()` après extraction (preuve du
     refactor pur : les mêmes tuples qu'avant, sur les kinds avance/stagne/repro).
  B. L'API ÉLARGIE `evenements() -> list[Evenement]` reconnaît les marqueurs RÉELS
     du moteur, avec la bonne disambiguation des emojis polysémiques (🍂/🍎/❄).

Logs JOUETS au format EXACT du moteur (cf. engine/croissance.py, mortalite.py,
decompo.py). Déterminisme total (parsing pur, aucun RNG).

Usage (depuis data/code/) :
  python3 -m tests.test_evenements
"""
from sim.evenements import _evenements, evenements, Evenement

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# --- Fabriques de lignes au FORMAT RÉEL du moteur (positions = (r, c)) --------
def _entete(tid="T0"):
    return f"  [{tid}]"


def _l_avance(nom, r, c):
    return f"    🌱 {nom}@({r}, {c}) → [pousse] (hum=0.50 lum=0.80 t=18.0°C)"


def _l_stagne(nom, r, c, raison):
    txt = {"sec": "(sec hum=0.10)", "ombre": "(ombre lum=0.10)",
           "froid": "(froid t=-2.0°C)", "noyé": "(noyé hum=0.95)"}[raison]
    marq = {"sec": "⏸ ", "ombre": "🌑", "froid": "❄", "noyé": "🌊"}[raison]
    return f"    {marq} {nom}@({r}, {c}) stagne {txt}"


def _l_repro(nom, r, c, tag):
    return f"    🌰 Reproduction : {nom} @({r}, {c}) [lum=0.50 h=1.20 {tag}]"


def _l_mort_senescence(nom, r, c):
    return f"    🪦 {nom}@({r}, {c}) meurt de sénescence (âge=12/10 ans)"


def _l_mort_asphyxie(nom, r, c):
    return f"    🪦 {nom}@({r}, {c}) meurt asphyxié (excès d'eau soutenu)"


def _l_mort_conflit(nom, r, c):
    return f"    ✗ {nom}@({r}, {c}) meurt (conflit)."


def _l_nouaison(nom, r, c):
    return f"    🍎 Nouaison {nom}@({r}, {c}) → 5 fruits (frac 0.80)"


def _l_abscission(nom, r, c):
    return f"    🍂 Abscission {nom}@({r}, {c}) → feuille +0.030"


# Lignes 🍂 / 🍎 POLYSÉMIQUES qui ne doivent PAS être prises pour abscission/nouaison.
def _l_necromasse(r, c):
    return f"    🍂 Nécromasse +1.20 OM @({r}, {c})"


def _l_chute_fruit(nom, r, c):
    return f"    🍂 Chute fruit (mûr 1.10) {nom}@({r}, {c}) → fruit +0.040"


def _l_recolte_header():
    return "  🍎 Récolte :"


def _l_ravageur():
    return "  🐛  Doryphore : larves voraces sur le feuillage"


def _l_ramet(mode, nom, r, c, rm, cm):
    # Format EXACT émis par sim/clonal.py::emettre_ramets (luxuriance ②/④).
    return f"    🌿 Ramet ({mode}) : {nom} @({r}, {c}) [clone de @({rm}, {cm})]"


# ---------------------------------------------------------------------------
# A. Parité de l'API historique (refactor pur)
# ---------------------------------------------------------------------------

def test_parite_historique():
    print("\n[A] _evenements() — parité historique (avance/stagne/repro inchangés)")
    log = [_entete("T0"),
           _l_avance("Tomate", 2, 2),
           _l_stagne("Basilic", 3, 1, "sec"),
           _l_stagne("Trèfle", 1, 4, "ombre"),
           _l_stagne("Haricot", 0, 0, "froid"),
           _l_repro("Tomate", 5, 5, "biparental")]
    out = list(_evenements(log))
    check("4 transitions + 1 repro reconnues", len(out) == 5, f"out={out}")
    check("avance porte (kind, tile, pos, clé)",
          out[0] == ("avance", "T0", (2, 2), "tomate"), f"{out[0]}")
    check("stagne sec → payload 'sec'",
          out[1] == ("stagne", "T0", (3, 1), "sec"), f"{out[1]}")
    check("repro → (clé, tag)",
          out[4] == ("repro", "T0", (5, 5), ("tomate", "biparental")), f"{out[4]}")
    # L'historique IGNORE le 🌊 noyé (la détection ne s'en sert pas) — invariant.
    log2 = [_entete(), _l_stagne("Tomate", 2, 2, "noyé")]
    check("_evenements ignore la stagnation noyé (hors périmètre détection)",
          list(_evenements(log2)) == [], f"{list(_evenements(log2))}")


# ---------------------------------------------------------------------------
# B. API élargie — nouveaux kinds + disambiguation
# ---------------------------------------------------------------------------

def test_kinds_elargis():
    print("\n[B1] evenements() — kinds élargis (germination/stagnation/mort/…)")
    log = [_entete("T1"),
           _l_avance("Tomate", 2, 2),
           _l_stagne("Tomate", 2, 2, "sec"),
           _l_stagne("Myrtille", 1, 1, "noyé"),
           _l_repro("Haricot", 4, 4, "auto"),
           _l_mort_senescence("Pommier", 6, 6),
           _l_mort_asphyxie("Courgette", 7, 7),
           _l_mort_conflit("Tournesol", 8, 8),
           _l_nouaison("Pommier", 6, 6),
           _l_abscission("Pommier", 6, 6),
           _l_ravageur()]
    out = evenements(log)
    kinds = [e.kind for e in out]
    check("germination présente", "germination" in kinds, f"kinds={kinds}")
    check("noyé reconnu (élargissement carnet)",
          Evenement("stagnation", "T1", (1, 1), "myrtille", "noyé") in out, f"{out}")
    check("mort sénescence",
          Evenement("mort", "T1", (6, 6), "pommier", "sénescence") in out)
    check("mort asphyxie",
          Evenement("mort", "T1", (7, 7), "courgette", "asphyxie") in out)
    check("mort conflit (marqueur ✗)",
          Evenement("mort", "T1", (8, 8), "tournesol", "conflit") in out)
    check("nouaison",
          Evenement("nouaison", "T1", (6, 6), "pommier", None) in out)
    check("abscission",
          Evenement("abscission", "T1", (6, 6), "pommier", None) in out)
    check("reproduction porte le tag en cause",
          Evenement("reproduction", "T1", (4, 4), "haricot", "auto") in out)
    check("ravageur = aléa sans espèce ni pos",
          Evenement("ravageur", "T1", None, None, None) in out)


def test_disambiguation_emojis():
    print("\n[B2] disambiguation des emojis polysémiques 🍂 / 🍎 / ❄")
    # 🍂 : seul `Abscission` compte (≠ Nécromasse, ≠ Chute fruit).
    log = [_entete(), _l_necromasse(2, 2), _l_chute_fruit("Pommier", 3, 3),
           _l_abscission("Cerisier", 4, 4)]
    out = evenements(log)
    absc = [e for e in out if e.kind == "abscission"]
    check("Nécromasse et Chute fruit NE sont PAS des abscissions",
          len(absc) == 1 and absc[0].espece == "cerisier", f"absc={absc}")
    # 🍎 : seul `Nouaison` compte (≠ header `Récolte :`).
    log2 = [_entete(), _l_recolte_header(), _l_nouaison("Pommier", 5, 5)]
    out2 = evenements(log2)
    noua = [e for e in out2 if e.kind == "nouaison"]
    check("le header Récolte n'est PAS une nouaison",
          len(noua) == 1, f"noua={noua}")
    # ❄ : stagne (froid) → stagnation ; un header gel sans @pos est ignoré.
    log3 = [_entete(), "  ❄  gel [T0] t_air=-2.0°C (cumul 3)",
            _l_stagne("Tomate", 1, 1, "froid")]
    out3 = evenements(log3)
    stag = [e for e in out3 if e.kind == "stagnation"]
    check("❄ : le header gel est ignoré, seule la stagnation froid reste",
          len(stag) == 1 and stag[0].cause == "froid", f"stag={stag}")


def test_ramet_clonal():
    print("\n[B4] evenements() — émission clonale (🌿 Ramet) par mode (luxuriance ④)")
    log = [_entete("T0"),
           _l_ramet("stolon", "Fraisier", 2, 3, 1, 4),
           _l_ramet("rhizome", "Menthe", 5, 5, 4, 4)]
    out = evenements(log)
    check("ramet stolon → cause = mode, espèce = clé catalogue",
          Evenement("ramet", "T0", (2, 3), "fraisier", "stolon") in out, f"{out}")
    check("ramet rhizome (menthe) reconnu",
          Evenement("ramet", "T0", (5, 5), "menthe", "rhizome") in out, f"{out}")


def test_floraison_acclimatation_absentes():
    print("\n[B3] floraison (header seul) et acclimatation (pas de marqueur) → rien")
    log = [_entete(), "  🌸 Floraison :"]
    check("le header Floraison seul ne produit aucun événement",
          evenements(log) == [], f"{evenements(log)}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Parseur d'événements partagé (Voix narratives ①)")
    print("=" * 60)
    test_parite_historique()
    test_kinds_elargis()
    test_disambiguation_emojis()
    test_ramet_clonal()
    test_floraison_acclimatation_absentes()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
