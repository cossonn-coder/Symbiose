"""
SYMBIOSE — tests/test_structures.py
Tests ciblés des structures posables (décompo·compost ⑤ phase A, CONCEPTION §5).

Phase A = le SQUELETTE des structures : modèle `Structure{kind, plot, contenu,
compost_mur}` porté par `eco.structures`, gestes `poser_bac`/`poser_pile` (pose,
phase planification) et `composter`/`empiler_bois` (déplacent la litière du plot
vers la structure). PAS encore de maturation (phase B) ni d'épandage (phase C).

Invariants vérifiés ici :
  1. Poser : crée une structure VIDE du bon `kind` dans `eco.structures` ;
     binaire (Vigueur insuffisante → rien posé, None).
  2. Acceptation (§5) : bac = {feuille, fleur, herbace, fruit} ; pile = {bois}.
     Le bac REFUSE `bois` ET `diffus` (décision ⑤A) ; la pile refuse le tendre.
  3. composter : déplace la litière tendre plot→bac. `diffus` et `bois` RESTENT
     au sol. Masse CONSERVÉE (déplacement, jamais de création).
  4. empiler_bois : déplace le `bois` plot→pile ; le tendre reste au sol.
  5. Fusion par tissu dans le contenu (deux dépôts même tissu → une parcelle).
  6. Déterminisme : deux runs identiques → contenu identique (zéro RNG).
  7. Neutralité du refactor : `deposer_litiere` se comporte exactement comme avant
     (fusion masse + age pondéré) ; un `eco` neuf a `structures == []`.

Usage (depuis data/code/) :
  python3 -m tests.test_structures
"""
import sys

from fields import init_eco, Structure, STRUCTURE_ACCEPTE
from fields.ecofields import RETOURNE_DUREE
from world.tile import Tile
from sim import actions as ACT
from sim import vigueur as V

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _gs(courante=None):
    """game_state minimal avec un joueur. `courante` force la Vigueur restante
    (None → plein MAX_BASE)."""
    gs = {"current_player": "joueur_1", "week": 1, "log": []}
    V.ensure_player(gs, "joueur_1")
    if courante is not None:
        gs["vigueur"]["joueur_1"]["courante"] = courante
    return gs


def _tile(rows=4, cols=4):
    """Tuile minimale (porteuse des tiges/rondelles) — `poser_pile` y pose son
    habitat auxiliaire (§4.1)."""
    return Tile(tile_id="T0", soil_type="terre", grid_rows=rows, grid_cols=cols)


def _masse(parcelles, tissu=None):
    return sum(p.masse for p in parcelles if tissu is None or p.tissu == tissu)


# ---------------------------------------------------------------------------
# 1. Poser
# ---------------------------------------------------------------------------
def test_poser():
    print("\n[1] poser_bac / poser_pile : structure vide, bon kind, binaire")
    eco = init_eco("T0", 4, 4)
    tile = _tile()
    gs = _gs()
    bac = ACT.poser_bac(gs, "joueur_1", eco, 1, 1)
    pile = ACT.poser_pile(gs, "joueur_1", eco, tile, 2, 2)
    check("bac posé (Structure renvoyée)", bac is not None and bac.kind == "bac")
    check("pile posée", pile is not None and pile.kind == "pile")
    check("2 structures dans eco.structures", len(eco.structures) == 2)
    check("plot mémorisé", bac.plot == (1, 1) and pile.plot == (2, 2))
    check("posées VIDES", bac.contenu == [] and pile.contenu == []
          and bac.compost_mur == 0.0)

    # Binaire : Vigueur insuffisante → None, rien ajouté.
    eco2 = init_eco("T0", 4, 4)
    gs_pauvre = _gs(courante=3.0)            # < MODERE (15)
    res = ACT.poser_bac(gs_pauvre, "joueur_1", eco2, 0, 0)
    check("Vigueur insuffisante → None", res is None)
    check("aucune structure posée à vide", len(eco2.structures) == 0)


# ---------------------------------------------------------------------------
# 2. Acceptation (§5)
# ---------------------------------------------------------------------------
def test_acceptation():
    print("\n[2] acceptation : bac = tendre (refuse bois ET diffus), pile = bois")
    bac = Structure(kind="bac", plot=(0, 0))
    pile = Structure(kind="pile", plot=(0, 0))
    check("bac accepte feuille/fleur/herbace/fruit",
          all(bac.accepte(t) for t in ("feuille", "fleur", "herbace", "fruit")))
    check("bac REFUSE bois", not bac.accepte("bois"))
    check("bac REFUSE diffus (décision ⑤A)", not bac.accepte("diffus"))
    check("pile accepte bois", pile.accepte("bois"))
    check("pile refuse le tendre",
          not any(pile.accepte(t) for t in ("feuille", "fleur", "herbace", "fruit", "diffus")))
    check("tables figées cohérentes",
          STRUCTURE_ACCEPTE["bac"] == frozenset(("feuille", "fleur", "herbace", "fruit"))
          and STRUCTURE_ACCEPTE["pile"] == frozenset(("bois",)))


# ---------------------------------------------------------------------------
# 3. composter : déplace le tendre, laisse diffus + bois
# ---------------------------------------------------------------------------
def test_composter():
    print("\n[3] composter : tendre plot→bac, diffus & bois restent, masse conservée")
    eco = init_eco("T0", 4, 4)
    eco.deposer_litiere(1, 1, "feuille", 2.0)
    eco.deposer_litiere(1, 1, "fruit", 1.5)
    eco.deposer_litiere(1, 1, "bois", 3.0)          # doit RESTER au sol
    # le plot porte déjà sa parcelle `diffus` permanente (masse 0)
    masse_avant = _masse(eco.litiere[1][1])

    gs = _gs()
    bac = ACT.poser_bac(gs, "joueur_1", eco, 1, 1)
    ok = ACT.composter(gs, "joueur_1", eco, 1, 1, bac)
    check("geste payé/appliqué", ok)
    check("bac reçoit feuille (2.0) + fruit (1.5)",
          abs(_masse(bac.contenu, "feuille") - 2.0) < 1e-9
          and abs(_masse(bac.contenu, "fruit") - 1.5) < 1e-9)
    check("bois RESTE au sol", abs(_masse(eco.litiere[1][1], "bois") - 3.0) < 1e-9)
    check("diffus RESTE au sol (présent)",
          any(p.tissu == "diffus" for p in eco.litiere[1][1]))
    check("plus de tendre au sol",
          _masse(eco.litiere[1][1], "feuille") == 0.0
          and _masse(eco.litiere[1][1], "fruit") == 0.0)
    check("masse totale CONSERVÉE (sol + bac)",
          abs((_masse(eco.litiere[1][1]) + _masse(bac.contenu)) - masse_avant) < 1e-9,
          f"{_masse(eco.litiere[1][1]) + _masse(bac.contenu):.4f} vs {masse_avant:.4f}")

    # Binaire : composter à vide ne déplace rien.
    eco2 = init_eco("T0", 4, 4)
    eco2.deposer_litiere(0, 0, "feuille", 1.0)
    bac2 = Structure(kind="bac", plot=(0, 0))
    gs_pauvre = _gs(courante=1.0)             # < FAIBLE (5)
    res = ACT.composter(gs_pauvre, "joueur_1", eco2, 0, 0, bac2)
    check("Vigueur insuffisante → False, litière intacte",
          res is False and abs(_masse(eco2.litiere[0][0], "feuille") - 1.0) < 1e-9
          and bac2.contenu == [])


# ---------------------------------------------------------------------------
# 4. empiler_bois : déplace le bois, laisse le tendre
# ---------------------------------------------------------------------------
def test_empiler():
    print("\n[4] empiler_bois : bois plot→pile, tendre reste au sol")
    eco = init_eco("T0", 4, 4)
    eco.deposer_litiere(2, 2, "bois", 4.0)
    eco.deposer_litiere(2, 2, "feuille", 1.0)       # doit RESTER au sol
    gs = _gs()
    pile = ACT.poser_pile(gs, "joueur_1", eco, _tile(), 2, 2)
    ok = ACT.empiler_bois(gs, "joueur_1", eco, 2, 2, pile)
    check("geste payé/appliqué", ok)
    check("pile reçoit le bois (4.0)", abs(_masse(pile.contenu, "bois") - 4.0) < 1e-9)
    check("feuille RESTE au sol", abs(_masse(eco.litiere[2][2], "feuille") - 1.0) < 1e-9)
    check("plus de bois au sol", _masse(eco.litiere[2][2], "bois") == 0.0)


# ---------------------------------------------------------------------------
# 5. Fusion par tissu dans le contenu
# ---------------------------------------------------------------------------
def test_fusion_contenu():
    print("\n[5] deposer_dans_structure : fusion par tissu (masse +, age pondéré)")
    eco = init_eco("T0", 4, 4)
    bac = Structure(kind="bac", plot=(0, 0))
    eco.deposer_dans_structure(bac, "feuille", 3.0)
    bac.contenu[0].age_sem = 4.0                      # vieillit le tas
    eco.deposer_dans_structure(bac, "feuille", 1.0)   # dépôt neuf, age 0
    check("une seule parcelle feuille", len(bac.contenu) == 1)
    check("masse cumulée = 4.0", abs(bac.contenu[0].masse - 4.0) < 1e-9)
    check("age moyenné par la masse = 3.0",
          abs(bac.contenu[0].age_sem - (4.0 * 3.0) / 4.0) < 1e-9,
          f"{bac.contenu[0].age_sem:.4f}")
    # garde-fou : tissu refusé → no-op
    eco.deposer_dans_structure(bac, "bois", 5.0)
    check("tissu refusé → contenu inchangé", len(bac.contenu) == 1)


# ---------------------------------------------------------------------------
# 6. Déterminisme
# ---------------------------------------------------------------------------
def _scenario_compost():
    """Pose un bac et composte un plot garni — renvoie le contenu (tissu, masse)
    trié, pour comparaison."""
    eco = init_eco("T0", 4, 4)
    eco.deposer_litiere(1, 1, "feuille", 2.0)
    eco.deposer_litiere(1, 1, "herbace", 0.7)
    eco.deposer_litiere(1, 1, "fruit", 1.5)
    gs = _gs()
    bac = ACT.poser_bac(gs, "joueur_1", eco, 1, 1)
    ACT.composter(gs, "joueur_1", eco, 1, 1, bac)
    return sorted((p.tissu, round(p.masse, 9)) for p in bac.contenu)


def test_determinisme():
    print("\n[6] déterminisme : deux runs identiques → contenu identique")
    a = _scenario_compost()
    b = _scenario_compost()
    check("contenu reproductible (h1 == h2)", a == b, f"{a}")


# ---------------------------------------------------------------------------
# 7. Neutralité du refactor (deposer_litiere inchangé) + eco neuf vide
# ---------------------------------------------------------------------------
def test_neutralite_refactor():
    print("\n[7] neutralité : eco neuf sans structure + deposer_litiere inchangé")
    eco = init_eco("T0", 4, 4)
    check("eco neuf : structures == []", eco.structures == [])

    # Même comportement de fusion qu'avant le refactor (_fusion_parcelle partagé).
    eco.deposer_litiere(0, 0, "feuille", 3.0)
    feuille = [p for p in eco.litiere[0][0] if p.tissu == "feuille"][0]
    feuille.age_sem = 4.0
    eco.deposer_litiere(0, 0, "feuille", 1.0)
    check("litière : une parcelle feuille, masse 4.0",
          len([p for p in eco.litiere[0][0] if p.tissu == "feuille"]) == 1
          and abs(feuille.masse - 4.0) < 1e-9)
    check("litière : age moyenné = 3.0", abs(feuille.age_sem - 3.0) < 1e-9)
    check("diffus permanente toujours présente",
          any(p.tissu == "diffus" for p in eco.litiere[0][0]))
    eco.deposer_litiere(0, 0, "feuille", -1.0)   # no-op masse ≤ 0
    check("dépôt masse ≤ 0 → no-op", abs(feuille.masse - 4.0) < 1e-9)


# ---------------------------------------------------------------------------
# 8. Maturation passive (phase B) : compost_mur monte, contenu fond, masse bornée
# ---------------------------------------------------------------------------
def test_maturation():
    print("\n[8] tick_structures : maturation passive → compost_mur, masse bornée")
    eco = init_eco("T0", 4, 4)
    bac = Structure(kind="bac", plot=(1, 1))
    eco.structures.append(bac)
    eco.deposer_dans_structure(bac, "feuille", 4.0)
    masse_initiale = _masse(bac.contenu)
    for _ in range(10):
        eco.tick_structures()
    mur = bac.compost_mur
    reste = _masse(bac.contenu)
    check("compost_mur a monté (> 0)", mur > 0.0, f"{mur:.4f}")
    check("contenu a fondu (< initial)", reste < masse_initiale, f"{reste:.4f}")
    check("age_sem a vieilli (= 10 sem)",
          all(abs(p.age_sem - 10.0) < 1e-9 for p in bac.contenu))
    # Conservation bornée : ce qui sort en mûr + ce qui reste ≤ masse initiale
    # (le complément = respiration, perte nette assumée — pas de création).
    check("compost_mur + reste ≤ masse initiale (rien créé)",
          mur + reste <= masse_initiale + 1e-9,
          f"{mur + reste:.4f} ≤ {masse_initiale:.4f}")


# ---------------------------------------------------------------------------
# 9. retourner : accélère la maturation + lisse les âges (bonus, jamais blocage)
# ---------------------------------------------------------------------------
def test_retourner():
    print("\n[9] retourner : bac retourné mûrit plus vite + lisse les âges")
    eco = init_eco("T0", 4, 4)
    bac_t = Structure(kind="bac", plot=(0, 0))   # témoin (jamais retourné)
    bac_r = Structure(kind="bac", plot=(1, 1))   # retourné
    eco.structures += [bac_t, bac_r]
    for b in (bac_t, bac_r):
        eco.deposer_dans_structure(b, "feuille", 3.0)
        eco.deposer_dans_structure(b, "herbace", 2.0)
    # Âges DISTINCTS pour que le lissage (moyenne pondérée) soit testable, pas trivial.
    for b in (bac_t, bac_r):
        next(p for p in b.contenu if p.tissu == "feuille").age_sem = 10.0
        next(p for p in b.contenu if p.tissu == "herbace").age_sem = 2.0

    gs = _gs()
    ok = ACT.retourner(gs, "joueur_1", bac_r)
    check("retourner payé/appliqué", ok and bac_r.retourne_restant == RETOURNE_DUREE)

    eco.tick_structures()
    check("retourné : compost_mur > témoin",
          bac_r.compost_mur > bac_t.compost_mur,
          f"{bac_r.compost_mur:.4f} vs {bac_t.compost_mur:.4f}")
    check("retourné : âges lissés (feuille == herbace)",
          abs(bac_r.contenu[0].age_sem - bac_r.contenu[1].age_sem) < 1e-9)
    check("drapeau décompté (RETOURNE_DUREE-1)",
          abs(bac_r.retourne_restant - (RETOURNE_DUREE - 1)) < 1e-9)

    # Binaire : Vigueur insuffisante → False, drapeau non posé.
    bac_p = Structure(kind="bac", plot=(2, 2))
    gs_pauvre = _gs(courante=1.0)             # < FAIBLE (5)
    res = ACT.retourner(gs_pauvre, "joueur_1", bac_p)
    check("Vigueur insuffisante → False, drapeau à 0",
          res is False and bac_p.retourne_restant == 0.0)


# ---------------------------------------------------------------------------
# 10. Biais cinétique : la pile (bois) mûrit beaucoup plus lentement que le bac
# ---------------------------------------------------------------------------
def test_pile_plus_lente():
    print("\n[10] pile (bois) mûrit plus lentement que le bac (tendre)")
    eco = init_eco("T0", 4, 4)
    bac = Structure(kind="bac", plot=(0, 0))
    pile = Structure(kind="pile", plot=(1, 1))
    eco.structures += [bac, pile]
    eco.deposer_dans_structure(bac, "feuille", 5.0)
    eco.deposer_dans_structure(pile, "bois", 5.0)
    for _ in range(10):
        eco.tick_structures()
    check("bac mûrit plus que la pile à masse égale",
          bac.compost_mur > pile.compost_mur,
          f"bac {bac.compost_mur:.4f} vs pile {pile.compost_mur:.4f}")


# ---------------------------------------------------------------------------
# 11. Neutralité du tick : aucune structure → tick_structures no-op strict
# ---------------------------------------------------------------------------
def test_tick_neutre():
    print("\n[11] tick_structures sans structure : no-op strict (invariant golden)")
    eco = init_eco("T0", 4, 4)
    eco.deposer_litiere(1, 1, "feuille", 2.0)
    fert_avant = eco.n.data[1][1]
    om_avant = eco.om_stable.data[1][1]
    eco.tick_structures()                     # structures == [] → boucle vide
    check("structures toujours vides", eco.structures == [])
    check("n inchangé", eco.n.data[1][1] == fert_avant)
    check("om_stable inchangé", eco.om_stable.data[1][1] == om_avant)


# ---------------------------------------------------------------------------
# 12. Déterminisme de la maturation
# ---------------------------------------------------------------------------
def _scenario_maturation():
    eco = init_eco("T0", 4, 4)
    bac = Structure(kind="bac", plot=(1, 1))
    eco.structures.append(bac)
    eco.deposer_dans_structure(bac, "feuille", 2.0)
    eco.deposer_dans_structure(bac, "fruit", 1.0)
    for _ in range(8):
        eco.tick_structures()
    return (round(bac.compost_mur, 9),
            sorted((p.tissu, round(p.masse, 9), round(p.age_sem, 9)) for p in bac.contenu))


def test_determinisme_maturation():
    print("\n[12] déterminisme : maturation reproductible (h1 == h2)")
    a = _scenario_maturation()
    b = _scenario_maturation()
    check("maturation reproductible", a == b, f"{a[0]}")


# ---------------------------------------------------------------------------
# 13. epandre (phase C) : borné par la jauge + trio humus au bon ratio
# ---------------------------------------------------------------------------
def test_epandre():
    print("\n[13] epandre : borné par compost_mur, trio humus (bac équilibré)")
    eco = init_eco("T0", 4, 4, fertilite=0.0)   # n=p=k=0 → deltas exacts (③)
    eco.om_stable.fill(0.0)                      # humus de fond D56 remis à 0 → deltas
                                                 # d'épandage exacts (baseline propre, ①)
    bac = Structure(kind="bac", plot=(0, 0))
    eco.structures.append(bac)
    bac.compost_mur = 2.0                     # jauge mûre (posée directement)
    gs = _gs()
    epandu = ACT.epandre(gs, "joueur_1", eco, 3, 3, bac, q=2.0)
    w = ACT.EPANDRE_W["bac"]
    check("épandu = 2.0 (toute la jauge)", abs(epandu - 2.0) < 1e-9, f"{epandu}")
    check("jauge décrémentée → 0", abs(bac.compost_mur) < 1e-9)
    check("om_stable += q×0.6", abs(eco.om_stable.at_plot(3, 3) - 2.0 * w["om_stable"]) < 1e-9)
    check("microbiome ensemencé += q×0.3",
          abs(eco.microbiome.at_plot(3, 3) - 2.0 * w["microbiome"]) < 1e-9)
    check("n += q×0.3", abs(eco.n.at_plot(3, 3) - 2.0 * w["n"]) < 1e-9)
    check("plot voisin INTACT (épandage local)",
          eco.om_stable.at_plot(0, 0) == 0.0 and eco.n.at_plot(0, 0) == 0.0)

    # Bornage (piège #5) : demander plus que la jauge → tronqué à la jauge.
    bac.compost_mur = 1.5
    epandu2 = ACT.epandre(gs, "joueur_1", eco, 2, 2, bac, q=10.0)
    check("demande > jauge → tronqué à 1.5", abs(epandu2 - 1.5) < 1e-9, f"{epandu2}")
    check("jauge vidée", abs(bac.compost_mur) < 1e-9)

    # q=None → épand tout le disponible.
    bac.compost_mur = 0.8
    epandu3 = ACT.epandre(gs, "joueur_1", eco, 1, 1, bac, q=None)
    check("q=None → tout le disponible (0.8)", abs(epandu3 - 0.8) < 1e-9)

    # Jauge vide → refus EN AMONT, aucune Vigueur dépensée.
    v_avant = gs["vigueur"]["joueur_1"]["courante"]
    epandu4 = ACT.epandre(gs, "joueur_1", eco, 1, 1, bac, q=5.0)
    check("jauge vide → 0.0 épandu", epandu4 == 0.0)
    check("jauge vide → AUCUNE Vigueur dépensée",
          gs["vigueur"]["joueur_1"]["courante"] == v_avant)


# ---------------------------------------------------------------------------
# 14. Biais structure : la pile amende plus de structure, moins de fertilité
# ---------------------------------------------------------------------------
def test_pile_biais():
    print("\n[14] epandre pile : biais structure (om_stable fort, n faible)")
    eco = init_eco("T0", 4, 4, fertilite=0.0)   # n=p=k=0 → comparaison nette (③)
    bac = Structure(kind="bac", plot=(0, 0))
    pile = Structure(kind="pile", plot=(1, 1))
    eco.structures += [bac, pile]
    bac.compost_mur = pile.compost_mur = 2.0
    gs = _gs()
    ACT.epandre(gs, "joueur_1", eco, 0, 0, bac, q=2.0)    # bac → plot (0,0)
    ACT.epandre(gs, "joueur_1", eco, 3, 3, pile, q=2.0)   # pile → plot (3,3)
    check("pile : om_stable > bac (biais structure)",
          eco.om_stable.at_plot(3, 3) > eco.om_stable.at_plot(0, 0),
          f"pile {eco.om_stable.at_plot(3, 3):.3f} vs bac {eco.om_stable.at_plot(0, 0):.3f}")
    check("pile : n < bac (nourrit peu)",
          eco.n.at_plot(3, 3) < eco.n.at_plot(0, 0),
          f"pile {eco.n.at_plot(3, 3):.3f} vs bac {eco.n.at_plot(0, 0):.3f}")


# ---------------------------------------------------------------------------
# 15. Pile → habitat auxiliaire (§4.1) : poser_pile pose une rondelle, lue par
#     _stability_grid (patron favoriser_auxiliaire)
# ---------------------------------------------------------------------------
def test_pile_habitat():
    print("\n[15] poser_pile : pose une rondelle auxiliaire (habitat §4.1)")
    eco = init_eco("T0", 4, 4)
    tile = _tile()
    check("tuile vierge : 0 rondelle auxiliaire",
          tile.get_rondelle_count("auxiliaire") == 0)
    gs = _gs()
    pile = ACT.poser_pile(gs, "joueur_1", eco, tile, 2, 2)
    check("pile posée", pile is not None)
    check("rondelle auxiliaire posée sur la tuile",
          tile.get_rondelle_count("auxiliaire") == 1)
    # Le bac, lui, NE pose PAS d'habitat (asymétrie voulue).
    tile2 = _tile()
    ACT.poser_bac(gs, "joueur_1", eco, 1, 1)
    check("poser_bac n'ajoute aucune rondelle",
          tile2.get_rondelle_count("auxiliaire") == 0)


# ---------------------------------------------------------------------------
# 16. (mycélium ⑤ §3.1) Appartenance TUILE : au plus UN bac et UNE pile par tuile ;
#     poser un 2ᵉ du même kind est refusé EN AMONT (rien dépensé). composter depuis
#     N'IMPORTE QUEL plot de la tuile verse dans l'unique bac (résolu par helper).
# ---------------------------------------------------------------------------
def test_un_par_tuile():
    print("\n[16] niveau tuile : au plus un bac + une pile, composter depuis tout plot")
    eco = init_eco("T0", 4, 4)
    tile = _tile()
    gs = _gs()
    b1 = ACT.poser_bac(gs, "joueur_1", eco, 0, 0)
    check("1er bac posé", b1 is not None)
    avant = gs["vigueur"]["joueur_1"]["courante"]
    b2 = ACT.poser_bac(gs, "joueur_1", eco, 3, 3)
    apres = gs["vigueur"]["joueur_1"]["courante"]
    check("2ᵉ bac REFUSÉ (None) — un seul par tuile", b2 is None)
    check("2ᵉ bac refusé EN AMONT → aucune Vigueur dépensée",
          abs(apres - avant) < 1e-9, f"{avant:.2f}→{apres:.2f}")
    p1 = ACT.poser_pile(gs, "joueur_1", eco, tile, 1, 1)
    check("1ʳᵉ pile posée (kind différent → OK)", p1 is not None)
    p2 = ACT.poser_pile(gs, "joueur_1", eco, tile, 2, 2)
    check("2ᵉ pile REFUSÉE (None)", p2 is None)
    # Helper de résolution : la structure de la tuile est l'unique de son kind.
    check("structure_de_tuile('bac') == l'unique bac",
          ACT.structure_de_tuile(eco, "bac") is b1)
    check("structure_de_tuile('pile') == l'unique pile",
          ACT.structure_de_tuile(eco, "pile") is p1)
    # composter depuis un plot ≠ ancrage (bac ancré (0,0)) verse bien dans CE bac.
    eco.deposer_litiere(3, 2, "feuille", 2.0)
    bac = ACT.structure_de_tuile(eco, "bac")
    ACT.composter(gs, "joueur_1", eco, 3, 2, bac)
    check("composter depuis (3,2) ≠ ancrage (0,0) → versé dans le bac de la tuile",
          _masse(bac.contenu, "feuille") == 2.0 and _masse(eco.litiere[3][2]) == 0.0)


# ---------------------------------------------------------------------------
# 17. (mycélium ⑤ §3.3/§3.4) Colonisation fongique du tas : croît tant qu'il y a du
#     contenu, ACCÉLÈRE la maturation, ENSEMENCE `mycelium` au plot d'ancrage (→ la
#     faune fongivore ④ et les carpophores s'installent sur le bac), DÉCLINE à vide.
# ---------------------------------------------------------------------------
def test_colonisation_fongique():
    print("\n[17] colonisation fongique : croît, accélère la maturation, ensemence mycélium")
    eco = init_eco("T0", 4, 4)
    bac = Structure(kind="bac", plot=(2, 2))
    eco.structures.append(bac)
    eco.deposer_dans_structure(bac, "feuille", 5.0)
    check("colonisation initiale = 0 (tas neuf)", bac.colonisation == 0.0)
    myc_avant = eco.mycelium.at_plot(2, 2)
    for _ in range(5):
        eco.tick_structures()
    check("colonisation a crû (> 0)", bac.colonisation > 0.0, f"{bac.colonisation:.4f}")
    check("colonisation bornée ≤ 1", bac.colonisation <= 1.0)
    check("mycélium ENSEMENCÉ au plot d'ancrage (faune/carpophores ④ §3.4)",
          eco.mycelium.at_plot(2, 2) > myc_avant,
          f"{myc_avant:.4f}→{eco.mycelium.at_plot(2, 2):.4f}")

    # Maturation ACCÉLÉRÉE par la colonisation : un tas qu'on garde colonisé mûrit
    # plus que le même tas SANS colonisation (témoin figé à 0 chaque tick).
    eco2 = init_eco("T0", 4, 4)
    bac_c = Structure(kind="bac", plot=(0, 0))   # colonisé librement
    bac_t = Structure(kind="bac", plot=(3, 3))   # témoin : colonisation forcée à 0
    eco2.structures += [bac_c, bac_t]
    for b in (bac_c, bac_t):
        eco2.deposer_dans_structure(b, "feuille", 5.0)
    for _ in range(6):
        eco2.tick_structures()
        bac_t.colonisation = 0.0                 # neutralise la voie fongique sur le témoin
    check("tas colonisé mûrit PLUS que le témoin non colonisé",
          bac_c.compost_mur > bac_t.compost_mur,
          f"colonisé {bac_c.compost_mur:.4f} vs témoin {bac_t.compost_mur:.4f}")

    # Déclin à vide : un tas dont le contenu est épuisé voit sa colonisation refluer.
    eco3 = init_eco("T0", 4, 4)
    bac_v = Structure(kind="bac", plot=(1, 1), colonisation=0.8)   # déjà colonisé, contenu VIDE
    eco3.structures.append(bac_v)
    eco3.tick_structures()
    check("colonisation DÉCLINE quand le tas est vide (rien à digérer)",
          bac_v.colonisation < 0.8, f"{bac_v.colonisation:.4f}")


# ---------------------------------------------------------------------------
# 18. Déterminisme de la colonisation (zéro RNG)
# ---------------------------------------------------------------------------
def _scenario_colonisation():
    eco = init_eco("T0", 4, 4)
    bac = Structure(kind="bac", plot=(2, 2))
    eco.structures.append(bac)
    eco.deposer_dans_structure(bac, "feuille", 3.0)
    for _ in range(7):
        eco.tick_structures()
    return (round(bac.colonisation, 9), round(bac.compost_mur, 9),
            round(eco.mycelium.at_plot(2, 2), 9))


def test_determinisme_colonisation():
    print("\n[18] déterminisme : colonisation reproductible (h1 == h2)")
    a = _scenario_colonisation()
    b = _scenario_colonisation()
    check("colonisation reproductible", a == b, f"{a}")


def main():
    print("=" * 60)
    print("TEST STRUCTURES POSABLES (décompo·compost ⑤ phases A+B+C + mycélium ⑤)")
    print("=" * 60)
    test_poser()
    test_acceptation()
    test_composter()
    test_empiler()
    test_fusion_contenu()
    test_determinisme()
    test_neutralite_refactor()
    test_maturation()
    test_retourner()
    test_pile_plus_lente()
    test_tick_neutre()
    test_determinisme_maturation()
    test_epandre()
    test_pile_biais()
    test_pile_habitat()
    test_un_par_tuile()
    test_colonisation_fongique()
    test_determinisme_colonisation()

    print("\n" + "=" * 60)
    total = len(_results)
    ok = sum(1 for _, c in _results if c)
    for name, cond in _results:
        if not cond:
            print(f"  ÉCHEC : {name}")
    print(f"RÉSULTAT : {ok}/{total} vérifications passées")
    if ok == total:
        print("[test_structures] PASS")
        return 0
    print("[test_structures] FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
