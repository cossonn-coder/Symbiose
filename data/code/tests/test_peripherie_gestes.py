"""
SYMBIOSE — tests/test_peripherie_gestes.py
Tests ciblés des GESTES FORESTIERS de la ceinture (sprint PÉRIPHÉRIE ④, D73).
Spec : `docs/champs/peripherie/conception_peripherie.md` §3.3/§4.3/§4.4/§5 + kickoff
`sprints/champs/peripherie/sprint_peripherie/04_gestes_forestiers.md`.

Fichier SÉPARÉ de `tests/test_peripherie.py` (①②③) : celui-ci était déjà à 415 LDC
(🔴 > 400) et le kickoff de ④/⑤ allait l'amener vers 550. Un fichier par tronçon —
c'est exactement la scission que le `00_etat` renvoyait au `/refactor` de fin de
sprint, faite d'emblée plutôt que payée deux fois.

Six suites :
  L. GOLDEN NEUTRE  — `tick_repousse(None)` est un no-op strict, et sur une ceinture
                      jamais coupée aussi : le tick ne touche RIEN sans joueur ;
  M. GATING         — `abattre` sans hache → False, **aucune Vigueur débitée**,
                      secteur intact (« refuser sans rien coûter ») ; avec la hache
                      acquise à l'Atelier, le geste passe ;
  N. REJET DE SOUCHE— `receper` sur charme ⇒ souche `vivante` ; sur hêtre ⇒ `morte`
                      ET cinétique d'abattage (« recéper une hêtraie, c'est l'abattre ») ;
  O. CINÉTIQUES     — l'ASYMÉTRIE, le vrai matériau du tronçon : trogne 5 ans,
                      taillis 10 ans (pas à 5), abattage pas revenu à 10 ans ;
  P. MATIÈRE        — le bois tombe en parcelles `bois` sur les plots du BORD (pas au
                      centre), la pile l'accepte, le bac le REFUSE ;
  Q. BORNES+CACHES  — densité ∈ [0,1] après gestes répétés, et une coupe INVALIDE
                      bien les caches de lumière et d'abri (sans quoi elle n'aurait
                      aucun effet visible) ;
  R. CORRIDOR       — `eco.lisiere` répond à la coupe (arbitrage Nico 2026-07-26) :
                      le TYPE reste l'archétype, la `densite_ligneuse` en module
                      l'intensité (affine, monotone, socle non nul), la mémoïsation
                      ne fige plus rien, et la repousse ramène le corridor.

Usage (depuis data/code/) :
  python3 -m tests.test_peripherie_gestes
"""
import sys
from types import SimpleNamespace

from fields.ecofields import init_eco
from fields.ecofields.bordure import intensite_lisiere
from fields.ecofields.constants import INTENSITE_LISIERE
from fields.ecofields.litiere import STRUCTURE_ACCEPTE
from fields.light import LightField
from fields.abri import _obstacles, _signature
from fields.peripherie import (
    COTES, NORD, SUD, secteur_neutre, couper_secteur, tick_repousse,
    CINETIQUES, ESSENCES_QUI_REJETTENT, SEMAINES_PAR_AN, MONDE_CM, DENSITE_FORET,
)
from sim import outils as OU
from sim import vigueur as V
from sim.actions import abattre, receper, eteter, TRES_ELEVE
from sim.actions.deblocage import marquer_action, evaluer_deblocages

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


COTE_PLOTS = int(MONDE_CM / 50.0)
PLAYER = "joueur_1"


# --- Fixtures ---------------------------------------------------------------
def _ceinture(cote=NORD, essence="charme", hauteur=1500.0, densite=0.8):
    """Ceinture neutre SAUF un bord boisé (le sujet des gestes)."""
    c = [secteur_neutre(k) for k in COTES]
    c[cote].update(type="foret", essence=essence,
                   hauteur_canopee=hauteur, densite_ligneuse=densite)
    return c


def _monde(cote=NORD, essence="charme", rows=8, cols=8, outille=True):
    """`game_state` minimal : une ceinture, une tuile au bord `cote` avec son
    `EcoFields`, un joueur outillé (hache + serpe) et un `log` pour le ledger.

    La tuile est collée au bord visé pour que `plots_de_bord` la voie : le jardin
    fait `MONDE_CM` de côté, une tuile de `rows×cols` plots à l'origine touche donc
    les bords NORD et OUEST ; pour le SUD on l'aligne sur le bord opposé."""
    eco = init_eco("T0", rows, cols)
    oy = 0.0 if cote != SUD else MONDE_CM - rows * 50.0
    tile = SimpleNamespace(tile_id="T0", origin_x_cm=0.0, origin_y_cm=oy)
    gs = {"ceinture": _ceinture(cote, essence=essence),
          "tiles": [tile], "eco": {"T0": eco}, "log": [], "week": 1,
          "current_player": PLAYER}
    V.ensure_player(gs, PLAYER)
    if outille:
        # Voie normale : l'Atelier pose les marqueurs et rouvre la chaîne. On ne
        # bricole pas `gestes_debloques` à la main — on passe par le vrai flux.
        for outil in ("hache", "serpe"):
            marquer_action(gs, PLAYER, OU.OUTILS[outil]["marqueur"])
        evaluer_deblocages(gs, PLAYER)
    return gs, eco, tile


def _plein(gs):
    """Recharge la Vigueur (les gestes forestiers coûtent 30 à 60 sur 100)."""
    V.ensure_player(gs, PLAYER)["courante"] = V.MAX_BASE
    return gs


def _vieillir(ceinture, annees):
    """Avance la repousse de `annees` années, semaine par semaine — exactement
    comme le fait `boucle.py` (aucun raccourci qui masquerait un pas de travers)."""
    for _ in range(int(round(annees * SEMAINES_PAR_AN))):
        tick_repousse(ceinture)


# --- L. Golden neutre -------------------------------------------------------
def test_golden_neutre():
    print("\n[L] Golden NEUTRE — sans joueur, rien n'est appelé ni écrit")
    tick_repousse(None)                       # ne doit pas lever
    check("tick_repousse(None) : no-op strict (aucune exception)", True)
    vierge = [secteur_neutre(k) for k in COTES]
    avant = [dict(s) for s in vierge]
    for _ in range(200):
        tick_repousse(vierge)
    check("ceinture jamais coupée : 200 ticks ne changent RIEN",
          vierge == avant)
    boisee = _ceinture()
    avant_b = [dict(s) for s in boisee]
    for _ in range(200):
        tick_repousse(boisee)
    check("lisière intacte (geste_coupe None) : aucune dérive sur 200 ticks",
          boisee == avant_b)


# --- M. Gating par outil ----------------------------------------------------
def test_gating():
    print("\n[M] Gating — « refuser sans rien coûter » (patron planter/lot vide)")
    gs, _eco, _t = _monde(outille=False)
    avant = dict(gs["ceinture"][NORD])
    vig_avant = V.ensure_player(gs, PLAYER)["courante"]
    ok = abattre(gs, PLAYER, NORD)
    check("abattre sans hache : refusé", ok is False)
    check("… AUCUNE Vigueur débitée",
          V.ensure_player(gs, PLAYER)["courante"] == vig_avant,
          f"{V.ensure_player(gs, PLAYER)['courante']:.1f}")
    check("… secteur strictement intact", gs["ceinture"][NORD] == avant)
    check("… aucune ligne au ledger", gs["log"] == [])

    # Étêter est gaté sur le GESTE (avoir recépé), pas sur un outil de plus.
    gs2, _e2, _t2 = _monde()
    check("eteter avant tout recépage : refusé (chaîne receper→eteter)",
          eteter(gs2, PLAYER, NORD) is False)
    check("receper avec la serpe : accepté", receper(_plein(gs2), PLAYER, NORD))
    check("… un bord recépé n'a plus de tête à étêter",
          eteter(_plein(gs2), PLAYER, NORD) is False)
    # Le pont marque le verbe-déclencheur puis réévalue (`DECLENCHEURS` contient
    # `receper` par dérivation de `GESTE_UNLOCK`). On étête alors une lisière INTACTE.
    gs2b, _e2b, _t2b = _monde()
    marquer_action(gs2b, PLAYER, "receper")
    evaluer_deblocages(gs2b, PLAYER)
    check("… le recépage ouvre eteter sur une lisière debout",
          eteter(_plein(gs2b), PLAYER, NORD))

    # Vigueur insuffisante : binaire tout-ou-rien.
    gs3, _e3, _t3 = _monde()
    V.ensure_player(gs3, PLAYER)["courante"] = TRES_ELEVE - 1.0
    intact = dict(gs3["ceinture"][NORD])
    check("Vigueur insuffisante : abattage refusé, secteur intact",
          abattre(gs3, PLAYER, NORD) is False
          and gs3["ceinture"][NORD] == intact)

    # Pas de ceinture / bord rase : erreur de protocole, aucun effet.
    gs4 = {"current_player": PLAYER}
    check("aucune ceinture : refus sans effet ni clé créée",
          abattre(gs4, PLAYER, NORD) is False and "vigueur" not in gs4)
    gs5, _e5, _t5 = _monde()
    check("bord rase (prairie) : rien de ligneux à couper",
          abattre(_plein(gs5), PLAYER, SUD) is False)


# --- N. Rejet de souche -----------------------------------------------------
def test_rejet_souche():
    print("\n[N] Rejet de souche — LE fait discriminant (#6 : jamais annoncé)")
    gs, _e, _t = _monde(essence="charme")
    check("receper un charme : accepté (rien n'est bloqué)",
          receper(gs, PLAYER, NORD))
    check("charme ⇒ souche VIVANTE",
          gs["ceinture"][NORD]["souche_memory"] == "vivante")
    check("… et cinétique de taillis (10 ans)",
          gs["ceinture"][NORD]["geste_coupe"] == "receper")

    gs2, _e2, _t2 = _monde(essence="hetre")
    check("receper un hêtre : accepté AUSSI (aucun avertissement)",
          receper(gs2, PLAYER, NORD))
    check("hêtre ⇒ souche MORTE", gs2["ceinture"][NORD]["souche_memory"] == "morte")
    check("… « recéper une hêtraie, c'est l'abattre » : cinétique d'abattage",
          gs2["ceinture"][NORD]["geste_coupe"] == "abattre")
    check("… et le ledger le consigne (trace, jamais un score)",
          any("Recépage" in l and "ne rejettera pas" in l for l in gs2["log"]),
          gs2["log"][-1].strip() if gs2["log"] else "—")

    check("le registre des essences qui rejettent est celui de la sylviculture",
          ESSENCES_QUI_REJETTENT == {"charme", "aulne", "saule"})
    for essence in ("hetre", "bouleau"):
        s = _ceinture(essence=essence)[NORD]
        couper_secteur(s, "receper")
        check(f"{essence} ne rejette pas", s["souche_memory"] == "morte")

    # L'étêtage laisse toujours un tronc vivant, quelle que soit l'essence.
    s = _ceinture(essence="hetre")[NORD]
    couper_secteur(s, "eteter")
    check("étêter : souche vivante même sur une essence qui ne rejette pas",
          s["souche_memory"] == "vivante" and s["geste_coupe"] == "eteter")


# --- O. Cinétiques ----------------------------------------------------------
def test_cinetiques():
    print("\n[O] Cinétiques — l'ASYMÉTRIE de réversibilité (5 / 10 / 30 ans)")
    check("durées figées : trogne 5, taillis 10, abattage 30",
          (CINETIQUES["eteter"][2], CINETIQUES["receper"][2],
           CINETIQUES["abattre"][2]) == (5.0, 10.0, 30.0))

    # Recépage d'un charme : plein à 10 ans, PAS à 5.
    c = _ceinture(essence="charme", densite=0.8, hauteur=1500.0)
    couper_secteur(c[NORD], "receper")
    check("recépage : densité effondrée tout de suite",
          c[NORD]["densite_ligneuse"] <= 0.2 and c[NORD]["hauteur_canopee"] == 0.0)
    _vieillir(c, 5.0)
    d5 = c[NORD]["densite_ligneuse"]
    check("charme recépé : PAS revenu à 5 ans", d5 < 0.8, f"densité {d5:.3f}")
    _vieillir(c, 5.0)
    check("charme recépé : densité PLEINE à 10 ans",
          abs(c[NORD]["densite_ligneuse"] - 0.8) < 1e-9
          and abs(c[NORD]["hauteur_canopee"] - 1500.0) < 1e-6,
          f"densité {c[NORD]['densite_ligneuse']:.3f} · "
          f"hauteur {c[NORD]['hauteur_canopee']:.0f} cm")
    check("… et la coupe cesse d'être une coupe (cinétique close)",
          c[NORD]["geste_coupe"] is None)
    check("… mais la souche reste en mémoire du milieu (D-3, trace persistante)",
          c[NORD]["souche_memory"] == "vivante")

    # Abattage : toujours pas revenu à 10 ans — la structure est lente.
    a = _ceinture(essence="charme", densite=0.8, hauteur=1500.0)
    couper_secteur(a[NORD], "abattre")
    _vieillir(a, 4.0)
    d4 = a[NORD]["densite_ligneuse"]
    check("abattage : les pionnières comblent le vide dès 4 ans",
          d4 > 0.2, f"densité {d4:.3f}")
    check("… mais la canopée est à terre (hauteur ≈ 1/7)",
          a[NORD]["hauteur_canopee"] < 300.0,
          f"{a[NORD]['hauteur_canopee']:.0f} cm")
    _vieillir(a, 6.0)
    check("abattage : TOUJOURS pas revenu à 10 ans (30 ans de canopée)",
          a[NORD]["densite_ligneuse"] < 0.8 and a[NORD]["hauteur_canopee"] < 1500.0,
          f"densité {a[NORD]['densite_ligneuse']:.3f} · "
          f"hauteur {a[NORD]['hauteur_canopee']:.0f} cm")
    _vieillir(a, 20.0)
    check("… et revenu à 30 ans (la forêt repousse, rien n'est épuisable #4)",
          abs(a[NORD]["densite_ligneuse"] - 0.8) < 1e-9
          and abs(a[NORD]["hauteur_canopee"] - 1500.0) < 1e-6)

    # Trogne : 5 ans, densité JAMAIS touchée.
    e = _ceinture(essence="saule", densite=0.8, hauteur=1500.0)
    couper_secteur(e[NORD], "eteter")
    check("étêtage : densité CONSERVÉE (aucune tige retirée)",
          e[NORD]["densite_ligneuse"] == 0.8)
    check("… hauteur rabattue de ~40 %", abs(e[NORD]["hauteur_canopee"] - 900.0) < 1e-6)
    _vieillir(e, 5.0)
    check("trogne : tête revenue à 5 ans",
          abs(e[NORD]["hauteur_canopee"] - 1500.0) < 1e-6
          and e[NORD]["geste_coupe"] is None)

    # Recouper avant reconstitution n'efface pas la mémoire du peuplement mûr.
    r = _ceinture(essence="charme", densite=0.8, hauteur=1500.0)
    couper_secteur(r[NORD], "receper")
    _vieillir(r, 3.0)
    couper_secteur(r[NORD], "receper")
    check("recoupe précoce : la cible de repousse reste le peuplement MÛR",
          r[NORD]["densite_avant"] == 0.8 and r[NORD]["hauteur_avant"] == 1500.0)


# --- P. Retour de matière ---------------------------------------------------
def _masse_bois(eco, r, c):
    return sum(p.masse for p in eco.litiere[r][c] if p.tissu == "bois")


def test_matiere():
    print("\n[P] Matière — le bois est POSÉ au sol, pas crédité à une jauge (#5)")
    gs, eco, _t = _monde(essence="charme")
    check("avant : aucune litière bois", _masse_bois(eco, 0, 0) == 0.0)
    check("abattage payé", abattre(gs, PLAYER, NORD))
    bord = _masse_bois(eco, 0, 4)
    seconde = _masse_bois(eco, 1, 4)
    centre = _masse_bois(eco, 4, 4)
    check("le bois tombe sur la rangée du BORD", bord > 0.0, f"{bord:.3f}")
    check("… décroissant vers l'intérieur", 0.0 < seconde < bord, f"{seconde:.3f}")
    check("… et RIEN au centre de la tuile (portée 2 plots)", centre == 0.0)
    check("aucun stock de mulch crédité (pas de nature « bois »)",
          "mulch_stock" not in gs or not gs.get("mulch_stock", {}).get("bois"))
    check("le geste est consigné au ledger (canal log existant)",
          any("Abattage" in l for l in gs["log"]),
          gs["log"][-1].strip() if gs["log"] else "—")

    # Circuit aval : la pile accepte le bois, le bac le refuse (⑤ décompo·compost).
    check("la PILE accepte le bois (habitat, `empiler_bois`)",
          "bois" in STRUCTURE_ACCEPTE["pile"])
    check("le BAC à compost le REFUSE", "bois" not in STRUCTURE_ACCEPTE["bac"])

    # Étêter rend MOINS de bois qu'abattre (on n'a pris que la tête).
    g2, e2, _ = _monde(essence="saule")
    marquer_action(g2, PLAYER, "receper")   # le pont ouvre eteter après un recépage
    evaluer_deblocages(g2, PLAYER)
    check("étêtage payé", eteter(_plein(g2), PLAYER, NORD))
    tete = _masse_bois(e2, 0, 4)
    check("étêter rend moins de bois qu'abattre (la tête, pas le fût)",
          0.0 < tete < bord, f"tête {tete:.3f} < fût {bord:.3f}")

    # Une tuile qui ne touche PAS le bord visé ne reçoit rien.
    g3, e3, _ = _monde(essence="charme")
    g3["tiles"][0].origin_y_cm = 900.0            # tuile déportée au centre
    check("abattage payé (tuile loin du bord)", abattre(_plein(g3), PLAYER, NORD))
    check("… aucune parcelle déposée (D32 : on ne balaie pas la grille)",
          all(_masse_bois(e3, r, c) == 0.0
              for r in range(e3.rows) for c in range(e3.cols)))


# --- Q. Bornes & invalidation des caches ------------------------------------
def test_bornes_et_caches():
    print("\n[Q] Bornes + caches — une coupe doit être VUE par lumière et abri")
    gs, _e, _t = _monde(essence="charme")
    for _ in range(6):
        _plein(gs)
        abattre(gs, PLAYER, NORD)
        receper(gs, PLAYER, NORD)
        _vieillir(gs["ceinture"], 1.0)
    s = gs["ceinture"][NORD]
    check("densité ∈ [0,1] après gestes répétés",
          0.0 <= s["densite_ligneuse"] <= 1.0, f"{s['densite_ligneuse']:.3f}")
    check("hauteur ≥ 0 après gestes répétés", s["hauteur_canopee"] >= 0.0)
    check("densité jamais au-dessus du peuplement mûr mémorisé",
          s["densite_ligneuse"] <= s["densite_avant"] + 1e-9)

    # Friche clairsemée : abattre ne la DENSIFIE pas (borne du min).
    f = [secteur_neutre(k) for k in COTES]
    f[NORD].update(type="friche", densite_ligneuse=0.05)
    couper_secteur(f[NORD], "abattre")
    check("friche à 0.05 : abattre ne la densifie pas", f[NORD]["densite_ligneuse"] == 0.05)
    _vieillir(f, 30.0)
    check("… et la « repousse pionnière » ne la densifie pas non plus (cible bornée)",
          f[NORD]["densite_ligneuse"] == 0.05, f"{f[NORD]['densite_ligneuse']:.3f}")

    # LUMIÈRE : le cache `geom_key` doit MISS après une coupe (sinon l'éclaircie
    # n'aurait aucun effet). On le prouve par le champ, pas par le code de retour.
    ceinture = _ceinture(SUD, hauteur=1500.0, densite=0.9)
    lf = LightField(COTE_PLOTS, COTE_PLOTS)
    lf.compute([], "hiver", tile_origin=(0.0, 0.0), ceinture=ceinture)
    ombre = lf.at_plot(COTE_PLOTS - 1, COTE_PLOTS // 2)
    lf.data[0][0] = -42.0                     # sentinelle : réécrite si MISS
    lf.compute([], "hiver", tile_origin=(0.0, 0.0), ceinture=ceinture)
    check("ceinture figée ⇒ lumière mémoïsée (HIT)", lf.data[0][0] == -42.0)
    couper_secteur(ceinture[SUD], "abattre")
    lf.compute([], "hiver", tile_origin=(0.0, 0.0), ceinture=ceinture)
    check("coupe ⇒ cache lumière INVALIDÉ (MISS)", lf.data[0][0] != -42.0)
    clair = lf.at_plot(COTE_PLOTS - 1, COTE_PLOTS // 2)
    check("… et la trouée fait ENTRER la lumière au bord sud",
          clair > ombre, f"{ombre:.3f} → {clair:.3f}")

    # ABRI : la signature doit bouger aussi (hauteur ET porosité y entrent).
    c2 = _ceinture(SUD, hauteur=1500.0, densite=0.9)
    sig_avant = _signature(_obstacles([], None, (0.0, 0.0), ceinture=c2), 0.0)
    couper_secteur(c2[SUD], "eteter")         # densité conservée, hauteur rabattue
    sig_eteté = _signature(_obstacles([], None, (0.0, 0.0), ceinture=c2), 0.0)
    check("étêtage (hauteur seule) ⇒ signature d'abri invalidée",
          sig_avant != sig_eteté)
    c3 = _ceinture(SUD, hauteur=1500.0, densite=0.9)
    c3[SUD]["densite_ligneuse"] = 0.4         # éclaircie SANS changer la hauteur
    sig_clair = _signature(_obstacles([], None, (0.0, 0.0), ceinture=c3), 0.0)
    check("éclaircie (densité seule) ⇒ signature d'abri invalidée",
          sig_avant != sig_clair)


# --- R. Corridor de lisière sensible à la coupe -----------------------------
def test_corridor_apres_coupe():
    print("\n[R] Corridor — un abattage FAIT BAISSER eco.lisiere (arbitrage ④)")
    # 1. L'intensité d'un secteur : archétype du type × densité, socle inclus.
    plein = dict(secteur_neutre(NORD), type="foret", essence="charme",
                 hauteur_canopee=1500.0, densite_ligneuse=DENSITE_FORET[1])
    rase = dict(plein, densite_ligneuse=0.10)
    i_plein, i_rase = intensite_lisiere(plein), intensite_lisiere(rase)
    check("canopée pleine ⇒ intensité = archétype du type (1.00)",
          abs(i_plein - INTENSITE_LISIERE["foret"]) < 1e-12, f"{i_plein:.3f}")
    check("forêt rasée ⇒ intensité effondrée mais NON nulle (socle : litière, ourlet)",
          0.0 < i_rase < 0.5 * i_plein, f"{i_rase:.3f} contre {i_plein:.3f}")
    # Monotone croissante, aucune non-linéarité inventée.
    serie = [intensite_lisiere(dict(plein, densite_ligneuse=d))
             for d in (0.0, 0.2, 0.4, 0.6, 0.8, 0.95)]
    check("monotone croissante en densité",
          all(serie[i] < serie[i + 1] for i in range(len(serie) - 1)),
          " < ".join(f"{v:.2f}" for v in serie))
    # Les types SANS strate ligneuse gardent leur comportement du ③, intact.
    for typ in ("prairie", "riviere", "falaise"):
        s = dict(secteur_neutre(NORD), type=typ)
        check(f"{typ} : intensité NON modulée (densité sans sens pour lui)",
              intensite_lisiere(s) == INTENSITE_LISIERE[typ])
    # L'ordre des archétypes tient : une friche clairsemée > une prairie rase.
    friche = dict(secteur_neutre(NORD), type="friche", densite_ligneuse=0.05)
    check("friche la plus clairsemée > prairie (l'ordre des archétypes tient)",
          intensite_lisiere(friche) > INTENSITE_LISIERE["prairie"],
          f"friche {intensite_lisiere(friche):.3f} > prairie "
          f"{INTENSITE_LISIERE['prairie']:.2f}")

    # 2. Le champ : abattre le bord nord fait BAISSER eco.lisiere aux plots de bord.
    gs, eco, _t = _monde(essence="charme")
    eco.maj_lisiere(gs["ceinture"])
    bord_avant = [eco.lisiere.at_plot(r, 4) for r in range(3)]
    centre_avant = eco.lisiere.at_plot(7, 4)
    check("abattage payé", abattre(gs, PLAYER, NORD))
    eco.maj_lisiere(gs["ceinture"])            # la mémoïsation NE DOIT PAS le figer
    bord_apres = [eco.lisiere.at_plot(r, 4) for r in range(3)]
    check("coupe ⇒ corridor EN BAISSE sur toute la bande de bord",
          all(a > b > 0.0 for a, b in zip(bord_avant, bord_apres)),
          " · ".join(f"{a:.3f}→{b:.3f}" for a, b in zip(bord_avant, bord_apres)))
    check("… la mémoïsation n'a pas figé le champ (densité dans la signature)",
          bord_apres[0] != bord_avant[0])
    check("… et le gradient reste un gradient (décroissant depuis le bord)",
          bord_apres[0] > bord_apres[1] > bord_apres[2])
    check("… loin du bord, rien ne bouge (l'effet reste local)",
          eco.lisiere.at_plot(7, 4) == centre_avant)

    # 3. La repousse le REMONTE — le corridor revient avec la forêt (rien d'épuisable).
    _vieillir(gs["ceinture"], 30.0)
    eco.maj_lisiere(gs["ceinture"])
    check("30 ans plus tard : corridor revenu à son niveau d'avant",
          abs(eco.lisiere.at_plot(0, 4) - bord_avant[0]) < 1e-12,
          f"{eco.lisiere.at_plot(0, 4):.3f}")

    # 4. Neutralité : sans ceinture, aucun champ, donc aucune capacité modifiée.
    vierge = init_eco("N", 8, 8)
    vierge.maj_lisiere(None)
    check("sans ceinture : eco.lisiere reste None (capacité bit-identique)",
          vierge.lisiere is None)


def main():
    test_golden_neutre()
    test_gating()
    test_rejet_souche()
    test_cinetiques()
    test_matiere()
    test_bornes_et_caches()
    test_corridor_apres_coupe()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[test_peripherie_gestes] {n_ok}/{n} OK")
    if n_ok != n:
        print("ÉCHECS : " + ", ".join(name for name, ok in _results if not ok))
        sys.exit(1)
    print("[test_peripherie_gestes] PASS")


if __name__ == "__main__":
    main()
