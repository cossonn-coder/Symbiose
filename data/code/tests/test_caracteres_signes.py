"""
SYMBIOSE — tests/test_caracteres_signes.py
Signes visibles et voix des caractères vivants (D139 caractères vivants ⑤).

Vérifié :
  [1] chaque signe dérivé varie avec SON gène et reste borné (bornes physiologiques) ;
      pas de signe de fleur sans axe de couleur, pas de rejets sans clonalité ;
  [2] « fleurs fanées sans graines » : seuil, ligne de log aller-retour, une note par
      espèce et par an, cause vent / insectes → événement → carnet (pollinisation) ;
  [3] goût : la note du carnet n'est écrite qu'à la PREMIÈRE bouchée amère ;
      concept « comestibilité » à l'encyclopédie, découvert puis crédité ;
  [4] table du pont : libellé pour les 32 caractères, groupes couvrant chacun une fois ;
  [5] aucune clé de signe dans le digest du golden.

Usage (depuis data/code/) :
  python3 -m tests.test_caracteres_signes
"""
import sys

from world import Tile
from fields import init_eco
from plants.caracteres import CARACTERES
from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE
from sim import actions as ACT
from sim import vigueur as V
from sim import maitrise as M
from sim import maitrise_detection as MD
from sim import carnet, gout
from sim import fanaison as FA
from sim import signes_caracteres as SC
from sim.journal import consigner
from sim.evenements import evenements
from sim.encyclopedie_types import type_de
from sim.concept_corpus import FICHES_CONCEPT
from tools.simserver.genes_pont import TABLE_CARACTERES, fecondation_pont, _LIBELLES
from tools.simserver.maitrise_pont import observer_apres_tick
from tests import test_golden

_results = []
_CAT = {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))


def _plante(cle, mure=True, **genes):
    cls = _CAT[cle]
    tile = Tile(tile_id="TS", soil_type="terre", grid_rows=6, grid_cols=6)
    p = tile.add_plant(cls, 2, 2)
    if mure:
        p.current_stage = len(cls.growth_stages) - 1
        p.age_years = 30.0
    p.genes = dict(genes)
    return tile, p


def _signe(cle, fn, gene, v):
    return fn(_plante(cle, **{gene: v})[1])


def test_signes():
    print("[1] signes dérivés : monotones et bornés")
    lo_hi = {}
    for fn, gene, cle in ((SC.echelle_fleur, "taille_fleur", "bourrache"),
                          (SC.contraste_guides, "guide_nectar", "bourrache"),
                          (SC.echelle_fruit, "taille_fruit", "pommier"),
                          (SC.matite_feuille, "coriacite_feuille", "bourrache"),
                          (SC.port, "dominance_apicale", "bourrache"),
                          (SC.rejets, "vigueur_clonale", "trefle")):
        lo, hi = CARACTERES[gene].bornes
        a, m, b = (_signe(cle, fn, gene, x) for x in (lo, 1.0, hi))
        lo_hi[fn.__name__] = (a, b)
        check(f"{fn.__name__} croît avec {gene}", a < m < b, f"{a} < {m} < {b}")
    check("contraste, matité, rejets ∈ [0, 1]",
          all(0.0 <= v <= 1.0 for k in ("contraste_guides", "matite_feuille", "rejets")
              for v in lo_hi[k]), str(lo_hi))
    check("port ∈ [−1, 1], neutre 0", lo_hi["port"] == (-1.0, 1.0)
          and _signe("bourrache", SC.port, "dominance_apicale", 1.0) == 0.0)
    t1 = _signe("bourrache", SC.teinte_fleur, "couleur_fleur", -1.0)
    t2 = _signe("bourrache", SC.teinte_fleur, "couleur_fleur", 1.0)
    check("teinte : bourrache bleue à −1, rose à +1", abs(t1[0] - 225.0) < 1 and abs(t2[0] - 330.0) < 1,
          f"{t1} {t2}")
    _, aulne = _plante("aulne")
    check("pas d'axe de couleur → pas de signe de fleur",
          SC.teinte_fleur(aulne) is None and "teinte_fleur" not in SC.signes_constants(aulne))
    check("fruitier : échelle du fruit exportée",
          "echelle_fruit" in SC.signes_constants(_plante("pommier")[1]))
    check("non clonale ou immature : aucun rejet",
          SC.rejets(_plante("bourrache")[1]) == 0.0
          and SC.rejets(_plante("trefle", mure=False)[1]) == 0.0)


def test_fanaison():
    print("[2] fleurs fanées sans graines")
    tile, bourrache = _plante("bourrache")
    _, aulne = _plante("aulne")
    tile.plants.append(aulne)
    check("pas fleurie (fec 0) : pas de signe", not FA.sans_graines(bourrache))
    bourrache.fecondation, aulne.fecondation = 0.15, 0.1
    check("fec 0,15 : signe", FA.sans_graines(bourrache))
    gs = {"tiles": [tile], "week": 30}
    notees = {}
    lignes = FA.noter_fanaisons(gs, notees)
    check("une ligne par espèce", len(lignes) == 2, repr(lignes))
    check("même année : rien de plus", FA.noter_fanaisons(gs, notees) == [])
    gs["week"] = 30 + 52
    check("année suivante : de nouveau", len(FA.noter_fanaisons(gs, notees)) == 2)
    evs = evenements(lignes)
    check("événements : fanaison, causes insectes / vent",
          [(e.kind, e.espece, e.cause) for e in evs]
          == [("fanaison", "bourrache", "sans_graines"), ("fanaison", "aulne", "sans_graines_vent")],
          repr(evs))
    bourrache.fecondation = 0.9
    check("fec 0,9 : plus de signe", not FA.sans_graines(bourrache))
    for c in (FA.CAUSE, FA.CAUSE_VENT):
        check(f"carnet : {c} sous pollinisation, 2 registres",
              carnet.CONCEPT_DE.get(("fanaison", c)) == "pollinisation"
              and ("fanaison", c, "descriptif") in carnet.GABARIT
              and ("fanaison", c, "interprétatif") in carnet.GABARIT)
    vgs = {"tiles": [], "log": []}
    V.ensure_player(vgs, "j")
    consigner(vgs, "j", lignes, 30)
    notes = carnet.carnet_lire(vgs, "j")
    check("note descriptive : « presque rien grainé »",
          notes and "presque rien grainé" in notes[0]["texte"]
          and notes[0]["registre"] == "descriptif", repr(notes[:1]))
    fp = fecondation_pont(aulne)
    check("lignée vécue : part autofécondée = a / fec (≤ 1)",
          fp["fec"] == 0.1 and 0.0 < fp["auto"] <= 1.0, str(fp))


def test_gout():
    print("[3] goût : première fois seulement, concept « comestibilité »")
    eco = init_eco("TS", 6, 6)
    tile, tomate = _plante("tomate")
    gs = {"tiles": [tile], "eco": {"TS": eco}, "log": [], "week": 4}
    st = V.ensure_player(gs, "j")
    st["max_base"], st["courante"] = 1000.0, 100.0
    ACT.manger(gs, "j", tomate, eco)
    ACT.manger(gs, "j", tomate, eco)
    check("deux bouchées toxiques : une seule note", len(gs["log"]) == 1, repr(gs["log"]))
    check("« comestibilité » est un concept d'encyclopédie, 3 niveaux",
          type_de(gout.CONCEPT) == "concept"
          and set(FICHES_CONCEPT.get(gout.CONCEPT, {})) == {1, 2, 3})
    log = list(gs["log"])
    observer_apres_tick(gs, "j", log)
    check("1ʳᵉ bouchée amère : concept découvert", M.palier(gs, "j", gout.CONCEPT) >= 1)
    obj = gs["maitrise"]["j"]["objets"][gout.CONCEPT]
    avant = (obj["preuves"], obj["palier"])
    MD.detecter(gs, "j", log, 4)
    check("detecter : la bouchée est une preuve", (obj["preuves"], obj["palier"]) != avant,
          f"{avant} → {obj}")


def test_pont():
    print("[4] table du pont")
    u = TABLE_CARACTERES["unites"]
    check("32 caractères, tous libellés", len(u) == len(CARACTERES) == 32
          and set(_LIBELLES) == set(CARACTERES), str(set(CARACTERES) - set(_LIBELLES)))
    noms = [n for _, ns in TABLE_CARACTERES["groupes"] for n in ns]
    check("groupes : chaque caractère une fois", sorted(noms) == sorted(CARACTERES))
    check("unités neuves exposées", u["couleur_fleur"]["unite"] == "position"
          and u["appetence_fruit"]["unite"] == "goût")


def test_golden_aveugle():
    print("[5] aucune clé de signe dans le digest du golden")
    attrs = set(test_golden._PLANT_ATTRS)
    check("signes hors digest", not attrs & {"signes_car", "rejets", "sans_graines"},
          str(attrs & {"signes_car", "rejets", "sans_graines"}))


def main():
    test_signes()
    test_fanaison()
    test_gout()
    test_pont()
    test_golden_aveugle()
    ok = sum(1 for _, v in _results if v)
    print(f"\n=== SIGNES DES CARACTÈRES : {ok}/{len(_results)} ===")
    sys.exit(0 if ok == len(_results) else 1)


if __name__ == "__main__":
    main()
