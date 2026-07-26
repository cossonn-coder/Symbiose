"""
SYMBIOSE — tests/peripherie/harness.py
Harness partagé des suites PÉRIPHÉRIE : compteur de résultats `check`/`_results`
et fabriques de ceintures de test. Importé par tous les modules de thème
(ceinture, exposition, flux) → ils écrivent dans le MÊME accumulateur, que
l'entrée `test_peripherie.py` agrège.
"""
from fields.light import LightField
from fields.peripherie import COTES, MONDE_CM, secteur_neutre

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# Le jardin fait 20×20 m = 40×40 plots : une grille de cette taille placée à
# l'origine monde (0,0) EST le jardin, donc la ceinture l'encadre exactement.
COTE_PLOTS = int(MONDE_CM / 50.0)


def _neutre():
    """Ceinture NEUTRE : 4 prairies rases. L'état opt-in de référence."""
    return [secteur_neutre(cote) for cote in COTES]


def _foret(cote, hauteur=1500.0, densite=0.9):
    """Ceinture neutre SAUF un secteur boisé (hauteur en cm, densité ∈ [0,1])."""
    ceinture = _neutre()
    ceinture[cote].update(type="foret", essence="hetre",
                          hauteur_canopee=hauteur, densite_ligneuse=densite)
    return ceinture


def _secteur(cote, **champs):
    """Ceinture neutre SAUF un secteur, décrit par ses champs (type, ligne_eau…)."""
    ceinture = _neutre()
    ceinture[cote].update(**champs)
    return ceinture


def _sol(ceinture, saison, rows=COTE_PLOTS, cols=COTE_PLOTS):
    """Grille de lumière-sol du jardin entier pour une saison + une ceinture."""
    lf = LightField(rows, cols)
    lf.compute([], saison, ceinture=ceinture)
    return [row[:] for row in lf.data]
