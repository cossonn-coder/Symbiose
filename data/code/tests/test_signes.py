"""
SYMBIOSE — test_signes.py
Tests des signes diégétiques météo (Z2, sous-sprint 04 — read-only).

Cinq vérifications, toutes DÉTERMINISTES (aucun RNG live) :
  1. Déterminisme : weather_signs rejoué deux fois → identique.
  2. Cohérence forecast == réalité : le `kind` annoncé à `week` pour l'horizon
     `k` est EXACTEMENT celui que `weather_at(seed, week + k)` renverra.
  3. Masque ~80 % : sur un large échantillon d'événements, `is_signed` vrai
     ≈ 80 % (tolérance large 70-90 %, §4.3).
  4. Couverture table : tout `kind` du `_CATALOGUE` (hors « Beau temps ») a une
     entrée dans `SIGN_TABLE` (sinon KeyError silencieux plus tard).
  5. Ambiguïté voulue : au moins un signe apparaît pour ≥ 2 `kind` distincts
     (§4.1 « certains signes sont ambigus entre deux événements proches »).

Usage (depuis data/code/) : python3 -m tests.test_signes
"""
from collections import Counter

from sim.weather import (
    weather_at, weather_signs, is_signed,
    SIGN_TABLE, _CATALOGUE, CALME, WeatherSign,
)

SEED = 0x5AB1057E
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# 1. Déterminisme
# ---------------------------------------------------------------------------

def test_determinisme():
    print("\n[1] weather_signs est pure et déterministe")
    ident = all(
        weather_signs(SEED, w) == weather_signs(SEED, w)
        for w in range(1, 520)
    )
    check("rejoué = identique sur 520 semaines", ident)
    # Type de retour : structure immuable annoncée.
    sample = next((s for w in range(1, 520) for s in weather_signs(SEED, w)),
                  None)
    check("renvoie des WeatherSign",
          sample is None or isinstance(sample, WeatherSign))


# ---------------------------------------------------------------------------
# 2. Cohérence forecast == réalité (le cœur de §3)
# ---------------------------------------------------------------------------

def test_coherence_realite():
    print("\n[2] ce qui est annoncé EST ce qui tombe")
    horizon = 2
    coherent = True
    nb_annonces = 0
    for w in range(1, 1040):
        for sg in weather_signs(SEED, w, horizon):
            nb_annonces += 1
            reel = weather_at(SEED, w + sg.in_weeks)
            if reel.kind != sg.kind:
                coherent = False
                break
    check("kind annoncé == kind réel (horizon)", coherent,
          f"{nb_annonces} annonces vérifiées")
    # Le calme n'émet jamais de signe.
    aucun_calme = all(
        sg.kind != CALME.kind
        for w in range(1, 1040) for sg in weather_signs(SEED, w)
    )
    check("le temps calme n'émet aucun signe", aucun_calme)


# ---------------------------------------------------------------------------
# 3. Masque ~80 % (§4.3)
# ---------------------------------------------------------------------------

def test_masque_proportion():
    print("\n[3] masque de signe ~80 % (part imprévisible ~20 %)")
    # On échantillonne les SEMAINES À ÉVÉNEMENT (un événement réel y tombe),
    # puis on mesure la proportion signée.
    weeks_event = [
        w for w in range(1, 5200)
        if weather_at(SEED, w).kind != CALME.kind
    ]
    signes = sum(1 for w in weeks_event if is_signed(SEED, w))
    prop = signes / len(weeks_event) if weeks_event else 0.0
    check("~80 % des événements signés (70-90 %)",
          0.70 <= prop <= 0.90,
          f"{prop:.1%} sur {len(weeks_event)} événements")


# ---------------------------------------------------------------------------
# 4. Couverture de la table
# ---------------------------------------------------------------------------

def test_couverture_table():
    print("\n[4] tout kind du catalogue a une entrée SIGN_TABLE")
    kinds = {e[0] for e in _CATALOGUE}
    manquants = sorted(k for k in kinds if k not in SIGN_TABLE)
    check("aucun kind du catalogue sans signes", not manquants,
          f"manquants={manquants}" if manquants else f"{len(kinds)} couverts")
    check("« Beau temps » absent de SIGN_TABLE",
          CALME.kind not in SIGN_TABLE)


# ---------------------------------------------------------------------------
# 5. Ambiguïté voulue (§4.1)
# ---------------------------------------------------------------------------

def test_ambiguite():
    print("\n[5] ambiguïté : un signe partagé par ≥ 2 événements")
    compteur = Counter()
    for signs in SIGN_TABLE.values():
        for s in set(signs):
            compteur[s] += 1
    partages = [s for s, n in compteur.items() if n >= 2]
    check("≥ 1 signe ambigu entre 2 kinds", bool(partages),
          f"{len(partages)} signe(s) partagé(s)")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Tests signes diégétiques météo (Z2, sous-sprint 04)")
    print("=" * 60)
    test_determinisme()
    test_coherence_realite()
    test_masque_proportion()
    test_couverture_table()
    test_ambiguite()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    raise SystemExit(0 if passed == total else 1)
