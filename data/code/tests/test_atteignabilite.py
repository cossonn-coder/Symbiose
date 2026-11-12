"""
SYMBIOSE — tests/test_atteignabilite.py
GARDE-FOU PERMANENT de l'accès aux gestes (sprint ACCÈS AUX GESTES ①, conception
`docs/joueur/gestes/conception_refonte_palette.md` §1.1 et §3.1).

Le constat de départ : 20 gestes gatés sur 32 ne s'ouvraient JAMAIS en jeu normal,
parce qu'une technique n'était découverte qu'en réussissant un geste qu'elle
verrouillait (poule et œuf). Ce test refait le POINT FIXE sur les tables RÉELLES
(`GESTES_BASE`, `GESTE_UNLOCK`, `PORTES_TECHNIQUE`, `OBJETS_TOUCHES`, `OUTILS`) et
échoue si l'impasse revient. Il ne simule rien : il raisonne sur les tables.

Le point fixe, en clair — on part des gestes de BASE et on répète jusqu'à ce que
plus rien ne bouge :
  • une TECHNIQUE est connue si un geste déjà ouvert la touche (découverte à
    l'usage, `OBJETS_TOUCHES`), si le tick la fait découvrir (`CONCEPTS_DU_TICK`),
    ou si l'une de ses PORTES est franchissable ;
  • un GESTE s'ouvre si l'une de ses conditions est franchissable.
Une condition est « franchissable » quand tout ce qu'elle cite est à portée :
marqueur d'outil vendu à l'Atelier, geste déjà ouvert, événement observable…

Vérifie :
  1. Tout verbe de `COUTS` est de base ou atteignable.
  2. Toute technique GATANTE (citée par un `("maitrise", t, 1)` et qu'aucun geste de
     base ne fait découvrir) a une porte, et aucune porte ne passe par un geste de
     sa propre technique (règle R2).
  3. Les noms de `PORTES_TECHNIQUE` existent dans `OBJETS_TOUCHES`.
  4. Formes `stock` et `compte` (cas unitaires) + la porte découvre la technique.
  5. No-op golden : les lectures pures ne créent aucune clé.

Lancement : depuis `data/code/`, `python3 -m tests.test_atteignabilite`.
"""
from __future__ import annotations

import sys

from fields.ecofields import NATURES_MULCH, PAILLAGE_DOSE
from sim import maitrise as M
from sim.actions import deblocage as D
from sim.actions.couts import COUTS, OBJETS_TOUCHES
from sim.outils import OUTILS

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# --- Hypothèses du point fixe (ce que le test tient pour acquis) --------------
# Concepts que le TICK fait découvrir sans geste (détection de la maîtrise) : leurs
# paliers sont tenus pour atteignables à tout niveau.
CONCEPTS_DU_TICK = frozenset({"eau", "lumière", "météo", "pollinisation"})

# Marqueurs d'outil « PROMIS PAR LE TRONÇON ② » : les portes les lisent déjà, mais
# l'Atelier ne les vend pas encore (`sim/outils.py`). À RESSERRER au ② : quand les
# outils sont dans `OUTILS`, vider cet ensemble — le test `[0]` le rappelle.
MARQUEURS_PROMIS_PAR_2 = frozenset({
    "posseder_broyeur", "posseder_pots", "posseder_tuteurs",
    "posseder_greffoir", "posseder_voile",
})

# Événements tenus pour atteignables : observations (marqueurs posés par le pont
# après le tick), lettres du courrier (posés au ②), et la bouture spontanée.
EVENEMENTS_ATTEIGNABLES = frozenset({
    "bouture_spontanee", "merle_seme", "grimpante_sans_appui",
    "lettre_greffe", "lettre_essaim",
})

# Qui remplit le stock de chaque nature de mulch : un GESTE (qui doit être ouvert)
# ou l'Atelier (`None` = achat, toujours possible).
SOURCE_STOCK = {"feuilles": "glaner", "paille": None}


def _marqueurs_outils() -> frozenset:
    return frozenset(spec["marqueur"] for spec in OUTILS.values()) | MARQUEURS_PROMIS_PAR_2


def _franchissable(cond, ouverts, techniques) -> bool:
    """La condition peut-elle devenir vraie, vu les gestes ouverts et les techniques
    connues à cette passe ? Miroir SYMBOLIQUE de `deblocage._cond_remplie`."""
    forme = cond[0]
    if forme == "maitrise":
        _, objet, palier = cond
        if objet in CONCEPTS_DU_TICK:
            return True
        if palier <= 1:
            return objet in techniques
        # Au-delà du palier 1 il faut des PREUVES : un geste ouvert qui la pratique.
        return any(objet in OBJETS_TOUCHES.get(v, ()) for v in ouverts)
    if forme == "action":
        return cond[1] in ouverts or cond[1] in _marqueurs_outils()
    if forme == "evenement":
        return cond[1] in EVENEMENTS_ATTEIGNABLES
    if forme == "stock":
        nature = cond[1]
        if nature not in SOURCE_STOCK:
            return False
        return SOURCE_STOCK[nature] is None or SOURCE_STOCK[nature] in ouverts
    if forme == "compte":
        return cond[1] in ouverts
    if forme == "et":
        return all(_franchissable(sous, ouverts, techniques) for sous in cond[1])
    return False


def point_fixe(portes=None):
    """Renvoie (gestes atteignables, techniques connues) au point fixe. `portes`
    permet de rejouer le calcul SANS la table des portes (preuve que le test voit
    bien l'impasse d'avant le sprint)."""
    portes = D.PORTES_TECHNIQUE if portes is None else portes
    ouverts = set(D.GESTES_BASE)
    techniques: set[str] = set()
    while True:
        avant = (len(ouverts), len(techniques))
        for verbe in ouverts:                       # découverte à l'usage
            techniques.update(OBJETS_TOUCHES.get(verbe, ()))
        for technique, conds in portes.items():     # portes
            if any(_franchissable(c, ouverts, techniques) for c in conds):
                techniques.add(technique)
        for verbe, conds in D.GESTE_UNLOCK.items():  # gestes
            if any(_franchissable(c, ouverts, techniques) for c in conds):
                ouverts.add(verbe)
        if (len(ouverts), len(techniques)) == avant:
            return ouverts, techniques


def _techniques_gatantes() -> set[str]:
    """Techniques citées par un `("maitrise", t, 1)` de `GESTE_UNLOCK`, hors concepts
    du tick et hors techniques qu'un geste de BASE fait découvrir à l'usage."""
    par_base = {o for v in D.GESTES_BASE for o in OBJETS_TOUCHES.get(v, ())}
    citees = {a[1] for conds in D.GESTE_UNLOCK.values() for c in conds
              for a in D._atomes(c) if a[0] == "maitrise" and a[2] == 1}
    return citees - CONCEPTS_DU_TICK - par_base


def test_hypotheses():
    print("\n[0] hypothèses du test encore justes")
    vendus = {spec["marqueur"] for spec in OUTILS.values()}
    check("aucun marqueur « promis par ② » n'est déjà vendu (sinon : le retirer)",
          not (MARQUEURS_PROMIS_PAR_2 & vendus), f"{sorted(MARQUEURS_PROMIS_PAR_2 & vendus)}")
    check("natures de SOURCE_STOCK connues de NATURES_MULCH",
          set(SOURCE_STOCK) <= set(NATURES_MULCH))


def test_point_fixe():
    print("\n[1] tout geste de COUTS est de base ou atteignable")
    ouverts, _ = point_fixe()
    perdus = sorted(set(COUTS) - ouverts)
    check("aucun geste inatteignable", not perdus, f"inatteignables : {perdus}")
    perdus_gated = sorted(set(D.GESTE_UNLOCK) - ouverts)
    check("tout geste de GESTE_UNLOCK est atteignable", not perdus_gated, f"{perdus_gated}")
    # Contre-épreuve : sans la table des portes, le test VOIT l'impasse d'origine.
    sans, _ = point_fixe(portes={})
    check("contre-épreuve : sans portes, des gestes restent fermés",
          len(set(D.GESTE_UNLOCK) - sans) >= 15,
          f"{len(set(D.GESTE_UNLOCK) - sans)} fermés")


def test_portes():
    print("\n[2] toute technique gatante a une porte, hors de ses propres gestes")
    objets = {o for objs in OBJETS_TOUCHES.values() for o in objs}
    sans_porte = sorted(_techniques_gatantes() - set(D.PORTES_TECHNIQUE))
    check("aucune technique gatante sans porte", not sans_porte, f"{sans_porte}")
    inconnues = sorted(set(D.PORTES_TECHNIQUE) - objets)
    check("noms de PORTES_TECHNIQUE présents dans OBJETS_TOUCHES", not inconnues,
          f"{inconnues}")
    # R2 : une porte qui ne cite QUE des gestes de sa technique est une fausse porte.
    # On exige qu'au moins UNE alternative n'en cite aucun (« posséder vaut avoir
    # posé » autorise `poser_bac` comme alternative du compostage, pas comme seule voie).
    fausses = []
    for technique, conds in D.PORTES_TECHNIQUE.items():
        siens = {v for v, objs in OBJETS_TOUCHES.items() if technique in objs}
        libres = [c for c in conds
                  if not any(a[0] in ("action", "compte") and a[1] in siens
                             for a in D._atomes(c))]
        if not libres:
            fausses.append(technique)
    check("chaque technique a une porte hors de ses propres gestes (R2)",
          not fausses, f"{fausses}")


def test_forme_stock():
    print("\n[3] forme `stock` : lecture pure du stock de mulch")
    gs = {}
    cond = ("stock", "feuilles", PAILLAGE_DOSE)
    check("sans stock → faux", not D._cond_remplie(gs, "j1", cond))
    check("la lecture ne crée pas `mulch_stock`", "mulch_stock" not in gs)
    gs["mulch_stock"] = {"feuilles": PAILLAGE_DOSE * 0.5}
    check("sous le seuil → faux", not D._cond_remplie(gs, "j1", cond))
    gs["mulch_stock"]["feuilles"] = PAILLAGE_DOSE
    check("au seuil → vrai", D._cond_remplie(gs, "j1", cond))
    check("nature absente du stock → faux",
          not D._cond_remplie(gs, "j1", ("stock", "brf", PAILLAGE_DOSE)))
    # La porte : une dose de feuilles DÉCOUVRE le paillage, qui ouvre `pailler`.
    nouveaux = D.evaluer_deblocages(gs, "j1")
    check("porte paillage → technique au palier 1", M.palier(gs, "j1", "paillage") == 1)
    check("… et `pailler` s'ouvre dans le même appel", "pailler" in nouveaux, f"{nouveaux}")
    check("`broyer` ne s'ouvre plus par le paillage", "broyer" not in nouveaux)


def test_forme_compte():
    print("\n[4] forme `compte` : n réussites d'un geste")
    gs = {}
    cond = ("compte", "glaner", 3)
    check("glaner est un verbe compté (dérivé des tables)", "glaner" in D.VERBES_COMPTES)
    check("sans compteur → faux", not D._cond_remplie(gs, "j1", cond))
    check("la lecture ne crée pas `gestes_comptes`", "gestes_comptes" not in gs)
    D.compter_geste(gs, "j1", "glaner")
    D.compter_geste(gs, "j1", "glaner")
    check("2 glanages → faux", not D._cond_remplie(gs, "j1", cond))
    check("2 glanages → compostage encore inconnu",
          D.evaluer_deblocages(gs, "j1") == [] and M.palier(gs, "j1", "compostage") == 0)
    check("3ᵉ glanage → compteur à 3", D.compter_geste(gs, "j1", "glaner") == 3)
    check("compteur par avatar", not D._cond_remplie(gs, "j2", cond))
    nouveaux = D.evaluer_deblocages(gs, "j1")
    check("porte compostage → palier 1", M.palier(gs, "j1", "compostage") == 1)
    check("… ouvre poser_bac et poser_pile", nouveaux == ["poser_bac", "poser_pile"],
          f"{nouveaux}")
    check("idempotent : rien de neuf au 2ᵉ appel", D.evaluer_deblocages(gs, "j1") == [])
    check("la porte ne RÉTROGRADE jamais un palier acquis",
          M.palier(gs, "j1", "compostage") == 1)


def test_portes_composees():
    print("\n[5] portes composées et retouches de GESTE_UNLOCK")
    gs = {}
    D.marquer_evenement(gs, "j1", "lettre_greffe")
    check("greffe : la lettre seule ne suffit pas",
          D.evaluer_deblocages(gs, "j1") == [] and M.palier(gs, "j1", "greffe") == 0)
    D.marquer_action(gs, "j1", "posseder_greffoir")
    check("greffe : lettre ET greffoir → `greffer`", D.evaluer_deblocages(gs, "j1") == ["greffer"])
    check("posseder_greffoir est un déclencheur (dérivé sous le `et`)",
          "posseder_greffoir" in D.DECLENCHEURS)
    gs = {}
    D.marquer_action(gs, "j1", "posseder_voile")
    check("voile de l'Atelier → les trois couvertures",
          D.evaluer_deblocages(gs, "j1") == ["poser_cloche", "poser_ombriere", "poser_voile"])
    gs = {}
    D.marquer_action(gs, "j1", "posseder_broyeur")
    check("broyeur → `broyer`", D.evaluer_deblocages(gs, "j1") == ["broyer"])
    gs = {}
    D.marquer_action(gs, "j1", "poser_bac")       # bac offert : posséder vaut avoir posé
    nouveaux = D.evaluer_deblocages(gs, "j1")
    check("bac offert → compostage découvert + composter/retourner/epandre",
          M.palier(gs, "j1", "compostage") == 1
          and {"composter", "retourner", "epandre"} <= set(nouveaux), f"{nouveaux}")


def test_noop_golden():
    print("\n[6] no-op golden : aucune clé créée par les lectures pures")
    gs = {}
    D._cond_remplie(gs, "j1", ("stock", "paille", 1.0))
    D._cond_remplie(gs, "j1", ("compte", "glaner", 1))
    check("game_state resté vide", gs == {}, f"{sorted(gs)}")


if __name__ == "__main__":
    print("=" * 60)
    print("SYMBIOSE — Atteignabilité des gestes (accès aux gestes ①)")
    print("=" * 60)
    test_hypotheses()
    test_point_fixe()
    test_portes()
    test_forme_stock()
    test_forme_compte()
    test_portes_composees()
    test_noop_golden()

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 60)
    sys.exit(0 if passed == total else 1)
