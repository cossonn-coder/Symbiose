"""
SYMBIOSE — tests/test_pressentis.py
Gestes PRESSENTIS et FAMILLES (sprint ACCÈS AUX GESTES ③, conception
`docs/joueur/gestes/conception_refonte_palette.md` §3.4 et §3.5).

Vérifie, sur les tables réelles et sur un état joueur minimal (aucun monde) :
  A. Familles : tout verbe de `COUTS` et de `GESTE_UNLOCK` a une famille connue,
     aucun verbe n'est rangé deux fois, le bloc du pont garde l'ordre.
  B. Tables : tout geste gaté a une technique, toute technique gatante (et toute
     technique de `PORTES_TECHNIQUE`) a sa phrase, tout indice est bien formé.
  C. Voix : les phrases ne portent ni chiffre, ni lieu, ni consigne.
  D. Calcul : inconnu → pressenti (indice) → ouvert ; technique découverte mais
     geste encore fermé (chaîne interne) ; lettre active ; geste voisin ouvert.
  E. Lecture PURE : `gestes_pressentis` ne crée aucune clé (golden neutre).

Lancement : depuis `data/code/`, `python3 -m tests.test_pressentis`.
"""
from __future__ import annotations

import copy
import sys

from sim import maitrise as M
from sim import pressentis as P
from sim import quetes as Q
from sim.actions import deblocage as D
from sim.actions.couts import COUTS, OBJETS_TOUCHES
from sim.actions.familles import (FAMILLES, FAMILLE_GESTE, BLOC_FAMILLES,
                                  _GESTES_PAR_FAMILLE)

_results = []
J = "j1"


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def test_familles():
    print("[A] familles de gestes")
    verbes = set(COUTS) | set(D.GESTE_UNLOCK)
    check("tout verbe de COUTS et de GESTE_UNLOCK a une famille",
          verbes <= set(FAMILLE_GESTE), sorted(verbes - set(FAMILLE_GESTE)))
    check("aucune famille ne range un verbe inconnu du moteur",
          set(FAMILLE_GESTE) <= verbes, sorted(set(FAMILLE_GESTE) - verbes))
    check("toute famille citée est connue",
          set(FAMILLE_GESTE.values()) == set(FAMILLES) and len(FAMILLES) == 8)
    ranges = [v for f in FAMILLES for v in _GESTES_PAR_FAMILLE[f]]
    check("aucun verbe rangé deux fois (exactement une famille)",
          len(ranges) == len(set(ranges)) == len(FAMILLE_GESTE))
    check("bloc du pont : ordre + gestes par famille, en listes",
          BLOC_FAMILLES["ordre"] == list(FAMILLES)
          and all(BLOC_FAMILLES["gestes"][f] == list(_GESTES_PAR_FAMILLE[f])
                  for f in FAMILLES))


def test_tables():
    print("[B] tables des pressentis")
    check("tout geste gaté a une technique",
          set(P.TECHNIQUE_DE_GESTE) == set(D.GESTE_UNLOCK))
    # L'ordre des tuples d'OBJETS_TOUCHES est-il fiable ? La technique d'un geste
    # d'entrée est celle que sa condition `maitrise` nomme (hors concepts du tick).
    ecarts = [(v, c[1]) for v, conds in D.GESTE_UNLOCK.items() for c in conds
              if c[0] == "maitrise" and c[2] == 1 and c[1] in D.PORTES_TECHNIQUE
              and P.TECHNIQUE_DE_GESTE[v] != c[1]]
    check("1er élément d'OBJETS_TOUCHES = technique nommée par GESTE_UNLOCK",
          not ecarts, ecarts)
    techniques = set(P.TECHNIQUE_DE_GESTE.values())
    check("toute technique gatante a sa phrase",
          techniques <= set(P.PHRASE_PRESSENTI),
          sorted(techniques - set(P.PHRASE_PRESSENTI)))
    check("toute technique de PORTES_TECHNIQUE a sa phrase",
          set(D.PORTES_TECHNIQUE) <= set(P.PHRASE_PRESSENTI))
    check("aucune phrase orpheline", set(P.PHRASE_PRESSENTI) <= techniques,
          sorted(set(P.PHRASE_PRESSENTI) - techniques))
    check("tout indice porte sur une technique gatante",
          set(P.INDICES_TECHNIQUE) <= techniques)
    formes = {"maitrise", "action", "evenement", "stock", "compte", "et",
              "lettre", "geste"}
    check("toute forme d'indice est connue",
          all(i[0] in formes for l in P.INDICES_TECHNIQUE.values() for i in l))
    check("les grimpantes du catalogue nourrissent l'indice du palissage",
          {"haricot", "jasmin", "lierre"} <= set(P._GRIMPANTES)
          and ("maitrise", "jasmin", 1) in P.INDICES_TECHNIQUE["palissage"])


def test_voix():
    print("[C] voix des phrases d'ambiance")
    interdits = ("atelier", "lettre", "courrier", "magazine", "achet", "outil",
                 "clique", "il faut", "va ", "allez", "débloqu", "palier")
    for technique, phrase in sorted(P.PHRASE_PRESSENTI.items()):
        bas = phrase.lower()
        ok = (not any(ch.isdigit() for ch in phrase)
              and not any(mot in bas for mot in interdits)
              and phrase[0].isupper() and phrase.rstrip()[-1] in ".?…")
        check(f"phrase « {technique} » sans chiffre, lieu ni consigne", ok, phrase)
    sans_je = [t for t, ph in sorted(P.PHRASE_PRESSENTI.items())
               if not any(m in f" {ph.lower()}"
                          for m in (" je ", " j'", " me ", " mes "))]
    check("toutes les phrases sont à la première personne", not sans_je, sans_je)


def _lettre(technique, qid="lettre_test"):
    return Q.Quete(id=qid, donneur="Gaston",
                   condition=("recolte_cumulee", "recolter", 3, "tomate"),
                   recompense=("technique", technique))


def test_calcul():
    print("[D] inconnu → pressenti → ouvert")
    gs: dict = {}
    check("joueur neuf : rien de pressenti", P.gestes_pressentis(gs, J) == [])

    # Indice « geste voisin fait une fois » : un glanage → compostage + paillage.
    D.compter_geste(gs, J, "glaner")
    pres = P.gestes_pressentis(gs, J)
    attendus = {"poser_bac", "poser_pile", "composter", "retourner", "epandre",
                "empiler_bois", "pailler"}
    check("un glanage fait pressentir compost et paillage", set(pres) == attendus,
          pres)
    check("liste triée", pres == sorted(pres))
    bloc = P.bloc_pressentis(gs, J)
    check("bloc du pont = [{verbe, phrase}] dans le même ordre",
          [b["verbe"] for b in bloc] == pres
          and all(set(b) == {"verbe", "phrase"} for b in bloc))
    check("la phrase est celle de la technique du geste",
          next(b["phrase"] for b in bloc if b["verbe"] == "composter")
          == P.PHRASE_PRESSENTI["compostage"])

    # La porte franchie (3 glanages) OUVRE les gestes d'entrée ; le reste de la
    # technique reste pressenti (chaîne interne : il faut d'abord poser le bac).
    D.compter_geste(gs, J, "glaner"); D.compter_geste(gs, J, "glaner")
    D.evaluer_deblocages(gs, J)
    pres = set(P.gestes_pressentis(gs, J))
    check("porte franchie : poser_bac/poser_pile ouverts, plus pressentis",
          D.est_debloque(gs, J, "poser_bac") and "poser_bac" not in pres
          and "poser_pile" not in pres)
    check("technique découverte, geste encore fermé → pressenti (composter)",
          {"composter", "retourner", "epandre", "empiler_bois"} <= pres, sorted(pres))

    # Concept voisin : la pollinisation fait pressentir l'apiculture.
    M.decouvrir(gs, J, "pollinisation")
    check("pollinisation découverte → ruche pressentie",
          {"poser_ruche", "recolter_miel"} <= set(P.gestes_pressentis(gs, J)))

    # Lettre ACTIVE : pressenti ; lettre comblée sans technique acquise : plus rien.
    check("greffe inconnue avant la lettre",
          "greffer" not in P.gestes_pressentis(gs, J))
    Q.ajouter_quete(gs, _lettre("greffe"))
    check("lettre active de greffe → greffer pressenti",
          "greffer" in P.gestes_pressentis(gs, J))
    gs[Q.CLE_QUETES]["lettre_test"]["semaine_fin"] = 5     # comblée (sans récompense)
    check("lettre close → l'indice « lettre » retombe",
          "greffer" not in P.gestes_pressentis(gs, J))

    # Geste voisin OUVERT : bouturer ouvert fait pressentir greffer.
    D.init_gestes_debloques(gs, J).add("bouturer")
    check("bouturer ouvert → greffer pressenti",
          "greffer" in P.gestes_pressentis(gs, J))

    # Espèce grimpante connue, merle connu.
    M.decouvrir(gs, J, "haricot")
    check("une grimpante connue → palissage pressenti",
          {"poser_tuteur", "poser_treillis", "poser_pergola", "palisser"}
          <= set(P.gestes_pressentis(gs, J)))
    check("perchoir encore inconnu", "poser_perchoir" not in P.gestes_pressentis(gs, J))
    M.decouvrir(gs, J, "merle")
    check("merle connu → perchoir pressenti",
          "poser_perchoir" in P.gestes_pressentis(gs, J))

    # Technique sans indice : inconnue tant que rien ne l'évoque.
    check("abattre reste inconnu (aucun indice d'essartage)",
          "abattre" not in P.gestes_pressentis(gs, J))
    check("jamais un geste ouvert parmi les pressentis",
          not (set(P.gestes_pressentis(gs, J)) & set(D.gestes_debloques(gs, J))))


def test_lecture_pure():
    print("[E] lecture pure")
    gs: dict = {}
    P.gestes_pressentis(gs, J); P.bloc_pressentis(gs, J)
    check("état vide : aucune clé créée", gs == {}, sorted(gs))
    gs = {}
    D.compter_geste(gs, J, "glaner")
    M.decouvrir(gs, J, "taille")
    avant = copy.deepcopy(gs)
    P.bloc_pressentis(gs, J)
    check("état peuplé : rien n'est écrit (ni `actions_faites`, ni autre)",
          gs == avant, sorted(set(gs) - set(avant)))
    check("rien n'est stocké sous un nom de pressenti",
          not any("pressenti" in k for k in gs))


def main() -> int:
    test_familles()
    test_tables()
    test_voix()
    test_calcul()
    test_lecture_pure()
    n_fail = sum(1 for _, ok in _results if not ok)
    print(f"\n[test_pressentis] {'PASS' if n_fail == 0 else 'FAIL'} — "
          f"{len(_results) - n_fail}/{len(_results)} checks verts")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
