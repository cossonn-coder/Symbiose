"""
SYMBIOSE — tests/test_automate_log.py
Verrous du LOG EXHAUSTIF STRUCTURÉ de l'automate (D87 tronçon ①, philo #3).
Spec : docs/joueur/automate/conception_automate_but.md §6 + kickoff
sprints/joueur/automate/sprint_automate_but/01_log_structure.md.

Quatre propriétés :
  A. ORACLE DE DÉTERMINISME — deux moteurs neufs, même seed, joués K ticks avec un
     automate frais chacun → journaux structurés STRICTEMENT égaux ligne à ligne.
     C'est l'oracle qui protégera les tronçons ②-⑤ (tout raisonnement ajouté doit
     rester rejouable à l'identique).
  B. SCHÉMA COMMUN — toute ligne du run porte les champs communs (categorie,
     semaine, niveau, objectif_id, espece, zone) ; le legacy est bien normalisé.
  C. RÉTRO-COMPAT — les entrées entree/entree_impasse/entree_consequence gardent
     leurs clés à plat historiques (celles que onglet.py/rapport.py lisent).
  D. FILTRE — filtrer sélectionne par catégorie/espèce/niveau_max SANS muter le
     journal ; trier est stable et respecte l'ordre canonique du raisonnement.

Usage (depuis data/code/) :
  python3 -m tests.test_automate_log
"""
from __future__ import annotations
import json

from tools.jardinier_auto import JardinierAutomate, LIBRE, marquer_jardin_cultive
from tools.jardinier_auto import filtrer, trier, rendre
from tools.jardinier_auto.trace import (
    journal, entree, entree_impasse, entree_consequence,
    entree_perception, entree_diagnostic, entree_plan, entree_veille,
)

_SEED = 0x5AB1057E
_WEEKS = 30

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _build_engine():
    """Monte le monde 'full' via SimServer (fabrique du F5), déterministe pour un
    seed donné."""
    from tools.simserver.server import SimServer
    srv = SimServer()
    rep = srv.cmd_init({"config": "full", "seed": _SEED})
    assert rep.get("ok"), rep
    return srv.engine


def _jouer(weeks: int) -> list:
    """Un moteur neuf joué `weeks` ticks avec un automate LIBRE frais ; renvoie le
    journal consigné. Jardin initial déclaré cultivé (tutelle=cultivées) pour que le
    journal soit non trivial. Déterministe (itération sur listes, zéro RNG)."""
    engine = _build_engine()
    marquer_jardin_cultive(engine, engine.game_state["current_player"])
    automate = JardinierAutomate(LIBRE)
    for _ in range(weeks):
        engine.tick_semaine()
        automate.jouer_tick(engine)
    return journal(engine.game_state)


# --- A. Oracle de déterminisme ---------------------------------------------------
def test_oracle_determinisme():
    j1 = _jouer(_WEEKS)
    j2 = _jouer(_WEEKS)
    s1, s2 = json.dumps(j1, sort_keys=True), json.dumps(j2, sort_keys=True)
    check("A. oracle : journaux rejoués identiques", s1 == s2,
          f"{len(j1)} lignes, {'égaux' if s1 == s2 else 'DIVERGENTS'}")
    return j1


# --- B. Schéma commun sur un run réel --------------------------------------------
def test_schema_commun(run: list):
    communs = ("categorie", "semaine", "niveau", "objectif_id", "espece", "zone")
    ok = all(all(k in ligne for k in communs) for ligne in run)
    niveaux_ok = all(ligne["niveau"] in (0, 1, 2) for ligne in run)
    check("B. schéma commun présent sur toutes les lignes du run", ok and niveaux_ok,
          f"{len(run)} lignes, champs communs {'complets' if ok else 'MANQUANTS'}")


# --- C. Rétro-compat des clés legacy ---------------------------------------------
def test_retro_compat():
    g = entree(3, "T0", "tomate@(1,2)", "eau", "arroser", "ok", "obj1")
    i = entree_impasse(3, "T2", "sol_nu", "sol_nu", "ravitaillement_manquant")
    c = entree_consequence(3, "objectif", "obj1:accompli")
    # Clés lues par onglet.py / rapport.py / automate_cmd.py.
    geste_ok = all(k in g for k in
                   ("categorie", "objectif_id", "tile_id", "cible",
                    "facteur_limitant", "geste", "resultat"))
    imp_ok = all(k in i for k in ("categorie", "cause", "facteur_limitant", "tile_id"))
    cons_ok = all(k in c for k in ("categorie", "type", "detail"))
    # Champs communs ajoutés + niveaux legacy corrects.
    communs_ok = (g["niveau"] == 0 and i["niveau"] == 0 and c["niveau"] == 1
                  and g["espece"] is None and g["zone"] is None)
    check("C. rétro-compat clés legacy + champs communs",
          geste_ok and imp_ok and cons_ok and communs_ok,
          f"geste={geste_ok} impasse={imp_ok} conseq={cons_ok} communs={communs_ok}")


# --- D. Filtre : sélection, non-mutation, tri stable -----------------------------
def test_filtre():
    j = [
        entree_perception(1, espece="tomate", zone=("T0", 1, 2),
                          detail={"graine_banque": True}),
        entree_diagnostic(1, espece="tomate", objectif_id="obj1",
                          detail={"manque": "graine"}),
        entree_plan(1, objectif_id="obj1", espece="tomate",
                    detail={"sous_but": "graine_en_banque"}),
        entree(1, "T0", "carotte@(3,4)", "eau", "arroser", "ok", "obj2"),
        entree_veille(2, objectif_id="obj1", detail={"chainon": "graine"}),
    ]
    avant = json.dumps(j, sort_keys=True)

    par_cat = filtrer(j, categorie="plan")
    par_esp = filtrer(j, espece="tomate")
    par_niv = filtrer(j, niveau_max=0)          # décisions seules : plan + geste + veille
    par_obj = filtrer(j, objectif_id="obj1")

    apres = json.dumps(j, sort_keys=True)

    sel_ok = (len(par_cat) == 1 and par_cat[0]["categorie"] == "plan"
              and len(par_esp) == 3
              and {l["categorie"] for l in par_niv} == {"plan", "geste", "veille"}
              and len(par_obj) == 3)
    non_mut = (avant == apres)
    check("D1. filtrer sélectionne correctement", sel_ok,
          f"cat={len(par_cat)} esp={len(par_esp)} niv0={len(par_niv)} obj={len(par_obj)}")
    check("D2. filtrer ne mute pas le journal", non_mut,
          "journal inchangé" if non_mut else "MUTATION détectée")

    # Tri canonique : à semaine 1, perception(0) < diagnostic(1) < plan(2) < geste(3).
    trie = trier(j)
    cats_s1 = [l["categorie"] for l in trie if l["semaine"] == 1]
    ordre_ok = cats_s1 == ["perception", "diagnostic", "plan", "geste"]
    # trier ne mute pas non plus.
    non_mut2 = (json.dumps(j, sort_keys=True) == avant)
    check("D3. trier respecte l'ordre canonique + stable", ordre_ok and non_mut2,
          f"{cats_s1}")

    # rendre : dérive un texte non vide de chaque catégorie (pure présentation).
    rendus_ok = all(isinstance(rendre(l), str) and rendre(l) for l in j)
    check("D4. rendre dérive un texte de chaque ligne", rendus_ok)


def main() -> int:
    print("=== test_automate_log (D87 tronçon ①) ===")
    run = test_oracle_determinisme()
    test_schema_commun(run)
    test_retro_compat()
    test_filtre()
    ko = [n for n, ok in _results if not ok]
    if ko:
        print(f"[log] FAIL — {len(ko)} échec(s) : {ko}")
        return 1
    print(f"[log] PASS — {len(_results)} vérifs OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
