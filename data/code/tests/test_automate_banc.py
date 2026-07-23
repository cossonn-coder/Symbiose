"""
SYMBIOSE — tests/test_automate_banc.py
Vérifs du tronçon ⑤ (D87) : le BANC « X depuis rien » paramétré. Spec :
docs/joueur/automate/conception_automate_but.md §6/§7 + kickoff
sprints/joueur/automate/sprint_automate_but/05_banc_vue_godot.md.

Contrairement aux autres suites automate (engine JOUET), on éprouve ici le banc DE
BOUT EN BOUT : il monte un vrai monde `smoke` via le serveur, tourne l'automate ENTRE
deux ticks (invariant H2 → golden intact) et compose son récit depuis le log FILTRÉ.
On prouve que chaque BRANCHE de l'arbre est bien forcée et que la chaîne est un ORACLE
déterministe (deux runs à entrées égales → récit identique).

  A. banque   : une graine pré-déposée → l'automate SÈME (geste `planter`) ;
  B. magazine : offre ouverte (palier 3) + Vigueur provisionnée → il ACHÈTE
     (`acheter_magazine`) PUIS sème ;
  C. aucune   : banque vide + pas d'offre → impasse HONNÊTE `chainon_manquant`,
     AUCUN geste créatif (le banc ne triche pas) ;
  D. nb_plants : la surcharge `nb_plants_cible` est prise en compte (chaîne non vide) ;
  E. oracle   : rejeu à entrées égales → récit strictement identique (déterminisme).

On tourne peu de semaines (annees=1) — JAMAIS 500 ans. Le golden n'est jamais touché
(le banc est hors tick, opt-in).

Usage (depuis data/code/) :
  python3 -m tests.test_automate_banc
"""
from __future__ import annotations

from tools.bancs.culture_depuis_rien import banc_culture_depuis_rien

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def test_branche_banque():
    r = banc_culture_depuis_rien("haricot", quantite=3, source_graine="banque",
                                 annees=1, verbose=False)
    check("banque → sème (planter)", r["gestes"].get("planter", 0) >= 1, str(r["gestes"]))
    check("banque → pas d'achat", "acheter_magazine" not in r["gestes"])


def test_branche_magazine():
    r = banc_culture_depuis_rien("haricot", quantite=3, source_graine="magazine",
                                 annees=1, verbose=False)
    check("magazine → achète", r["gestes"].get("acheter_magazine", 0) >= 1, str(r["gestes"]))
    check("magazine → sème après achat", r["gestes"].get("planter", 0) >= 1)


def test_branche_aucune():
    r = banc_culture_depuis_rien("haricot", quantite=3, source_graine="aucune",
                                 annees=1, verbose=False)
    check("aucune → impasse chainon_manquant",
          "chainon_manquant" in r["impasses"], str(r["impasses"]))
    check("aucune → aucun geste créatif (pas de triche)", not r["gestes"], str(r["gestes"]))
    check("aucune → issue impasse", r["issue"].startswith("impasse:"), r["issue"])


def test_nb_plants_surcharge():
    # nb_plants=1 : le planificateur ne vise qu'UNE cultivée → chaîne bien produite.
    r = banc_culture_depuis_rien("basilic", quantite=5, source_graine="banque",
                                 nb_plants=1, annees=1, verbose=False)
    check("nb_plants=1 → chaîne non vide", len(r["chaine"]) >= 1, f"{len(r['chaine'])} lignes")


def test_fruitier_post_condition():
    # C2 : une espèce fruitière porte le flag → but satisfait par le FRUIT (post-condition
    # organe-typée). On vérifie juste que le banc l'expose ; le déroulé bio dépend de
    # l'espèce (tomate meurt tôt, Q8 — non testé ici pour la vitesse).
    r = banc_culture_depuis_rien("courgette", quantite=3, source_graine="banque",
                                 annees=1, verbose=False)
    check("courgette marquée fruitier (C2)", r["fruitier"] is True)


def test_oracle_determinisme():
    # Deux runs À ENTRÉES ÉGALES → récit strictement identique (le log est un oracle).
    r1 = banc_culture_depuis_rien("haricot", quantite=3, source_graine="magazine",
                                  annees=1, verbose=False)
    r2 = banc_culture_depuis_rien("haricot", quantite=3, source_graine="magazine",
                                  annees=1, verbose=False)
    check("oracle : chaînes identiques", r1["chaine"] == r2["chaine"],
          f"{len(r1['chaine'])} vs {len(r2['chaine'])}")
    check("oracle : issues identiques", r1["issue"] == r2["issue"])
    check("oracle : gestes identiques", r1["gestes"] == r2["gestes"])


def main():
    print("[test_automate_banc] banc « X depuis rien » (D87 ⑤)")
    test_branche_banque()
    test_branche_magazine()
    test_branche_aucune()
    test_nb_plants_surcharge()
    test_fruitier_post_condition()
    test_oracle_determinisme()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[test_automate_banc] {n_ok}/{n} OK")
    if n_ok != n:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
