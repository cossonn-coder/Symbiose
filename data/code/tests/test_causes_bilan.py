"""
SYMBIOSE — tests/test_causes_bilan.py
Causes en mots (D140 G, sprint stress au bilan ⑤, `sim/causes_bilan.py`) + signes.

  [amont]   une mort de famine prend la cause qui a miné la plante, dans l'ordre :
            marque de tissus retirés (gel, grêle…) / oïdium > racines perdues >
            vaisseaux embolisés > facteur limitant du bilan > signe chronique ; rien
            de lisible → None (le carnet garde « épuisée ») ;
  [affiner] seules les morts `famine` changent ; plante introuvable → `famine` ;
  [journal] `consigner(…, affineur=…)` consigne la cause affinée, sans affineur le
            flux brut (comportement historique) ;
  [voix]    `voix_cause` : desséchée > gelée > racines > âge, None sinon ;
  [signes]  le signe `secheresse` lit l'embolie (reste après la pluie), signe `oidium`.

Fonctions pures sur des plantes de labo : < 1 s. Lancement (depuis data/code/) :
  python3 -m tests.test_causes_bilan
"""

import sys

from plants import PlantInstance
from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from sim import journal as J
from sim import semiologie
from sim.causes_bilan import affiner, cause_amont, voix_cause
from sim.evenements import Evenement
from sim.embolie import SEUIL_EMBOLIE

_ok = []


def check(nom, cond, detail=""):
    _ok.append(bool(cond))
    print(f"  {'✅' if cond else '❌'} {nom}" + (f" — {detail}" if detail else ""))


def _plante(cle="poivron", cat=PLANT_CATALOGUE):
    p = PlantInstance(cat[cle], (2, 3))
    p.limitant = ""
    return p


def test_amont():
    print("\n[amont]")
    p = _plante()
    check("rien de lisible → None", cause_amont(p, None) is None)
    p.limitant = "ombre"
    check("limitant ombre → ombre", cause_amont(p, None) == "ombre")
    p.embolie = 0.5
    check("vaisseaux à moitié embolisés > limitant", cause_amont(p, None) == "secheresse")
    p.pourriture_memory, p.asphyxie_memory = 0.5, 0.9
    check("racines noyées > embolie", cause_amont(p, None) == "asphyxie")
    p.asphyxie_memory = 0.0
    check("racines pourries sans eau stagnante → maladie (pourridié)",
          cause_amont(p, None) == "maladie")
    p.symptom_marks = {"gel": 0.3, "grele": 0.6}
    check("marque la plus forte (grêle) > racines", cause_amont(p, None) == "grele")
    p.symptom_marks = {"froid": 0.2}
    p.oidium = 0.5
    check("oïdium plus fort que le froid → maladie", cause_amont(p, None) == "maladie")
    q = _plante()
    q.limitant = "noyé"
    check("limitant noyé → asphyxie", cause_amont(q, None) == "asphyxie")


def test_affiner_et_journal():
    print("\n[affiner + journal]")
    p = _plante()
    p.symptom_marks = {"gel": 0.8}
    morts = {("T0", (2, 3), "poivron"): p}
    evs = [Evenement("mort", "T0", (2, 3), "poivron", "famine"),
           Evenement("mort", "T0", (5, 5), "poivron", "famine"),
           Evenement("mort", "T0", (2, 3), "poivron", "sénescence")]
    out = affiner(evs, morts, {})
    check("famine d'une plante gelée → gel", out[0].cause == "gel")
    check("plante introuvable → famine", out[1].cause == "famine")
    check("autre cause intacte", out[2].cause == "sénescence")
    log = ["[T0]", "    🪦 Poivron@(2, 3) meurt de faim (réserves épuisées, bilan -0.10)"]
    gs = {}
    J.consigner(gs, "j", log, 7)
    J.consigner(gs, "k", log, 7, affineur=lambda e: affiner(e, morts, {}))
    brut = gs["journal"]["j"]["entries"][0]["cause"]
    fin = gs["journal"]["k"]["entries"][0]["cause"]
    check("sans affineur : famine (historique)", brut == "famine", brut)
    check("avec affineur : gel", fin == "gel", fin)


def test_voix():
    print("\n[voix]")
    p = _plante()
    check("plante saine → None", voix_cause(p) is None)
    p.pourriture_memory = 0.3
    check("racines perdues → racines", voix_cause(p) == "racines")
    p.symptom_marks = {"gel": 0.6}
    check("gel fort → gelee (> racines)", voix_cause(p) == "gelee")
    p.embolie = 0.5
    check("vaisseaux → dessechee (> gel)", voix_cause(p) == "dessechee")
    c = _plante("consoude", {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE})
    c.age_years = 0.97 * c.plant_class.longevity()
    check("consoude à 97 % de sa longévité → age", voix_cause(c) == "age")


def test_signes():
    print("\n[signes]")
    p = _plante()
    p.drought_memory = 0.0
    p.embolie = SEUIL_EMBOLIE / 2
    check("embolie à ½ seuil → sécheresse 0,5, sol arrosé ou non",
          abs(semiologie.secheresse(p, None, None) - 0.5) < 1e-9)
    p.oidium = 0.4
    causes = [s["cause"] for s in semiologie.leaf_symptoms(p, None, None)]
    check("oïdium dans les symptômes", "oidium" in causes, causes)


if __name__ == "__main__":
    for t in (test_amont, test_affiner_et_journal, test_voix, test_signes):
        t()
    print(f"\n{sum(_ok)}/{len(_ok)} OK")
    sys.exit(0 if all(_ok) else 1)
