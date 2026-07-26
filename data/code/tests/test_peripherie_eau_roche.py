"""
SYMBIOSE — tests/test_peripherie_eau_roche.py
Tests ciblés de l'EAU, de la ROCHE et de l'ÉROSION de la ceinture (sprint
PÉRIPHÉRIE ⑤, D73). Spec : `docs/champs/peripherie/conception_peripherie.md`
§3.4/§4.3/§4.4/§4.5 + kickoff
`sprints/champs/peripherie/sprint_peripherie/05_eau_roche_erosion.md`.

Fichier SÉPARÉ, comme `test_peripherie_gestes.py` (④) : `test_peripherie.py` (①②③)
est déjà à 415 LDC (🔴) et le ④ a acté « un fichier par tronçon ». Le kickoff
demandait d'étendre `test_peripherie.py` — écart assumé, même motif qu'au ④.

Six suites, une par point du kickoff :
  S. GATING       — `endiguer` sans avoir creusé / `entailler` sans pioche → False,
                    **aucune Vigueur débitée**, secteur intact ; puis le geste passe ;
  T. DÉPLACEMENT  — endiguer gorge le bord (marécage ÉMERGENT), dériver l'assèche.
                    Le joueur DÉPLACE l'eau, il n'en crée pas ;
  U. RUPTURE      — un ouvrage non entretenu rompt vers 8 ans, la ligne d'eau revient
                    à sa valeur NATURELLE, l'événement est au ledger ; refaire le
                    geste = entretien (l'horloge repart) ; une MARE, elle, ne rompt pas ;
  V. IRRÉVERSIBLE — après `entailler`, `altitude_relative` ne remonte JAMAIS (10 000
                    ticks), et l'ombre portée diminue vraiment ;
  W. ÉROSION      — `structure_sol` et `om_stable` se dégradent sur les plots de bord,
                    avec décroissance ; plots centraux INTACTS ; l'étêtage n'érode pas ;
                    la repousse ARRÊTE l'érosion ; le signe 🪨 est émis UNE fois ;
  X. NEUTRALITÉ   — sans ceinture, aucun de ces effets ne s'exécute (golden).

Usage (depuis data/code/) :
  python3 -m tests.test_peripherie_eau_roche
"""
import sys
from types import SimpleNamespace

from fields.ecofields import init_eco
from fields.ecofields.bordure import MARQUEUR_EBOULIS
from fields.light import LightField
from fields.peripherie import (
    COTES, NORD, SUD, secteur_neutre, couper_secteur, tick_repousse,
    tick_ouvrages, erosion_secteur, entailler_secteur, creuser_secteur,
    deplacer_ligne_eau, porte_eau, occulteurs, MONDE_CM, SEMAINES_PAR_AN,
    LIGNE_EAU_PAS_CM, LIGNE_EAU_BORNES, MARE_LIGNE_EAU_CM, ENTAILLE_PAS_CM,
    OUVRAGE_RUPTURE_ANS, MARQUEUR_RUPTURE, EROSION_DENUDATION_MIN,
)
from sim import outils as OU
from sim import vigueur as V
from sim.actions import endiguer, deriver, entailler, creuser_peripherie
from sim.actions.deblocage import marquer_action, evaluer_deblocages

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


COTE_PLOTS = int(MONDE_CM / 50.0)
PLAYER = "joueur_1"


# --- Fixtures ---------------------------------------------------------------
def _ceinture(cote=NORD, **champs):
    """Ceinture neutre SAUF un bord, décrit par ses champs."""
    c = [secteur_neutre(k) for k in COTES]
    c[cote].update(**champs)
    return c


def _monde(cote=NORD, rows=8, cols=8, outille=True, **champs):
    """`game_state` minimal : ceinture, tuile collée au bord visé, joueur équipé, log.

    « Équipé » passe par le VRAI flux de déblocage (marqueur d'outil / verbe
    déclencheur + `evaluer_deblocages`) — on ne bricole jamais `gestes_debloques`."""
    eco = init_eco("T0", rows, cols)
    oy = 0.0 if cote != SUD else MONDE_CM - rows * 50.0
    tile = SimpleNamespace(tile_id="T0", origin_x_cm=0.0, origin_y_cm=oy)
    gs = {"ceinture": _ceinture(cote, **champs),
          "tiles": [tile], "eco": {"T0": eco}, "log": [], "week": 1,
          "current_player": PLAYER}
    V.ensure_player(gs, PLAYER)
    if outille:
        marquer_action(gs, PLAYER, OU.OUTILS["pioche"]["marqueur"])
        marquer_action(gs, PLAYER, "creuser")     # l'expérience ouvre endiguer/deriver
        evaluer_deblocages(gs, PLAYER)
    return gs, eco, tile


def _plein(gs):
    """Recharge la Vigueur (ces gestes coûtent 30 à 60 sur 100)."""
    V.ensure_player(gs, PLAYER)["courante"] = V.MAX_BASE
    return gs


def _vieillir_ouvrage(ceinture, annees):
    """Avance les ouvrages semaine par semaine, comme `boucle.py`. Renvoie les
    marqueurs de log accumulés."""
    lignes = []
    for _ in range(int(round(annees * SEMAINES_PAR_AN))):
        lignes += tick_ouvrages(ceinture)
    return lignes


# --- S. Gating : refuser sans rien coûter ----------------------------------
def test_gating():
    print("\n[S] Gating — l'outil/l'expérience fait le geste, refuser ne coûte RIEN")

    # a) endiguer sans avoir jamais creusé.
    gs, _, _ = _monde(type="riviere", ligne_eau=10.0, outille=False)
    avant = dict(gs["ceinture"][NORD])
    v0 = V.ensure_player(gs, PLAYER)["courante"]
    ok = endiguer(gs, PLAYER, NORD)
    check("endiguer sans avoir creusé : refusé", not ok)
    check("… aucune Vigueur débitée",
          V.ensure_player(gs, PLAYER)["courante"] == v0)
    check("… secteur strictement intact", gs["ceinture"][NORD] == avant)
    check("… ledger muet", gs["log"] == [])

    # b) entailler sans pioche.
    gs, _, _ = _monde(type="falaise", altitude_relative=600.0, outille=False)
    v0 = V.ensure_player(gs, PLAYER)["courante"]
    check("entailler sans pioche : refusé", not entailler(gs, PLAYER, NORD))
    check("… aucune Vigueur débitée, roche intacte",
          V.ensure_player(gs, PLAYER)["courante"] == v0
          and gs["ceinture"][NORD]["altitude_relative"] == 600.0)

    # c) équipé, les gestes passent.
    gs, _, _ = _monde(type="riviere", ligne_eau=10.0)
    check("endiguer une fois creuser réalisé : passe",
          endiguer(_plein(gs), PLAYER, NORD))
    gs, _, _ = _monde(type="falaise", altitude_relative=600.0)
    check("entailler avec la pioche : passe", entailler(_plein(gs), PLAYER, NORD))

    # d) portes MÉTIER : rien à endiguer à sec, pas de mare dans la roche, pas
    #    d'entaille hors falaise ni sur une roche déjà rasée.
    gs, _, _ = _monde(type="prairie")
    v0 = V.ensure_player(_plein(gs), PLAYER)["courante"]
    check("endiguer un bord à SEC : refusé sans rien coûter",
          not endiguer(gs, PLAYER, NORD)
          and V.ensure_player(gs, PLAYER)["courante"] == v0)
    gs, _, _ = _monde(type="falaise", altitude_relative=300.0)
    check("creuser une mare dans la ROCHE : refusé (pas à la bêche)",
          not creuser_peripherie(_plein(gs), PLAYER, NORD))
    gs, _, _ = _monde(type="prairie")
    check("entailler hors falaise : refusé", not entailler(_plein(gs), PLAYER, NORD))
    gs, _, _ = _monde(type="falaise", altitude_relative=0.0)
    check("entailler une roche déjà rasée : refusé",
          not entailler(_plein(gs), PLAYER, NORD))

    # e) une mare rend le bord endiguable : `porte_eau` ne teste pas le type.
    gs, _, _ = _monde(type="prairie")
    creuser_peripherie(_plein(gs), PLAYER, NORD)
    check("après une mare creusée, une prairie porte de l'eau",
          porte_eau(gs["ceinture"][NORD])
          and endiguer(_plein(gs), PLAYER, NORD))


# --- T. Déplacer l'eau, pas en créer (§3.4) --------------------------------
def _cycle(eco, ceinture, ticks):
    """Circuit hydrique COMPLET (berge → hydro → ruissellement → marais), comme
    `boucle.py` : aucune ligne de physique n'est court-circuitée."""
    for _ in range(ticks):
        eco.tick_berge(ceinture)
        eco.tick_hydrology("terre")
        eco.tick_ruissellement()
        eco.tick_marais()


def _apres_gestes(sens, n, ticks=90):
    """Une tuile-monde après `n` endiguements (sens +1) ou dérivations (−1) au NORD."""
    eco = init_eco("b", COTE_PLOTS, COTE_PLOTS)
    for r in range(COTE_PLOTS):
        for c in range(COTE_PLOTS):
            eco.humidite.set(r, c, 0.6)
    ceinture = _ceinture(NORD, type="riviere", ligne_eau=0.0)
    for _ in range(n):
        deplacer_ligne_eau(ceinture[NORD], sens)
    _cycle(eco, ceinture, ticks)
    return eco, ceinture


def test_deplacement():
    print("\n[T] Déplacement — endiguer gorge, dériver assèche, le marais ÉMERGE")
    c = COTE_PLOTS // 2
    haut, ch = _apres_gestes(+1, 3)          # +90 cm
    bas, _ = _apres_gestes(-1, 3)            # −90 cm
    temoin, _ = _apres_gestes(+1, 0)

    check("3 endiguements ⇒ +3 pas de ligne d'eau",
          ch[NORD]["ligne_eau"] == 3.0 * LIGNE_EAU_PAS_CM,
          f"{ch[NORD]['ligne_eau']:.0f} cm")
    check("endiguer ⇒ le bord AMONT se gorge",
          haut.humidite.at_plot(0, c) > 2.0 * temoin.humidite.at_plot(0, c),
          f"{haut.humidite.at_plot(0, c):.3f} contre {temoin.humidite.at_plot(0, c):.3f}")
    check("dériver ⇒ le bord s'assèche",
          bas.humidite.at_plot(0, c) < 0.5 * temoin.humidite.at_plot(0, c),
          f"{bas.humidite.at_plot(0, c):.3f}")
    check("MARÉCAGE émergent près du bord après endiguement (aucun script)",
          haut.est_marais(0, c) and not haut.est_marais(10, c))
    check("le geste n'écrit AUCUN champ : hors portée, rien ne bouge",
          abs(haut.humidite.at_plot(10, c) - bas.humidite.at_plot(10, c)) < 1e-12)

    # Bornes : on ne creuse pas un canyon à force de gestes.
    s = secteur_neutre(NORD)
    s["type"] = "riviere"
    for _ in range(50):
        deplacer_ligne_eau(s, +1)
    check("ligne d'eau bornée en haut", s["ligne_eau"] == LIGNE_EAU_BORNES[1],
          f"{s['ligne_eau']:.0f} cm")
    for _ in range(100):
        deplacer_ligne_eau(s, -1)
    check("ligne d'eau bornée en bas", s["ligne_eau"] == LIGNE_EAU_BORNES[0],
          f"{s['ligne_eau']:.0f} cm")


# --- U. Rupture d'ouvrage (§4.4) ------------------------------------------
def test_rupture():
    print("\n[U] Rupture — l'artefact demande un entretien perpétuel")
    ceinture = _ceinture(NORD, type="riviere", ligne_eau=-20.0)
    s = ceinture[NORD]
    deplacer_ligne_eau(s, +1)
    deplacer_ligne_eau(s, +1)
    endigue = s["ligne_eau"]
    check("la ligne d'eau NATURELLE est mémorisée au 1ᵉʳ ouvrage",
          s["ligne_eau_naturelle"] == -20.0)

    lignes = _vieillir_ouvrage(ceinture, OUVRAGE_RUPTURE_ANS - 1.0)
    check("à 7 ans, l'ouvrage tient encore",
          s["ouvrage"] == "endiguer" and s["ligne_eau"] == endigue and not lignes)

    lignes += _vieillir_ouvrage(ceinture, 1.2)
    check("vers 8 ans, l'ouvrage ROMPT", s["ouvrage"] is None)
    check("… la ligne d'eau revient à sa valeur NATURELLE (pas à zéro)",
          s["ligne_eau"] == -20.0, f"{s['ligne_eau']:.0f} cm")
    check("… l'événement est au ledger",
          len(lignes) == 1 and MARQUEUR_RUPTURE in lignes[0], lignes[0].strip())

    # Entretien : refaire le geste remet l'horloge à zéro et NE réécrit PAS la
    # référence naturelle (sinon la rupture n'annulerait plus rien).
    ceinture = _ceinture(NORD, type="riviere", ligne_eau=-20.0)
    s = ceinture[NORD]
    for _ in range(4):                        # un passage tous les 3 ans
        deplacer_ligne_eau(s, +1)
        _vieillir_ouvrage(ceinture, 3.0)
    check("entretenu tous les 3 ans : l'ouvrage tient (12 ans)",
          s["ouvrage"] == "endiguer" and s["ligne_eau"] > -20.0,
          f"{s['ligne_eau']:.0f} cm")
    check("… et la référence naturelle n'a jamais été réécrite",
          s["ligne_eau_naturelle"] == -20.0)

    # Une MARE est une FORME, pas un artefact : elle ne rompt pas, et elle survit
    # à la rupture d'un barrage posé après.
    ceinture = _ceinture(NORD, type="prairie")
    s = ceinture[NORD]
    creuser_secteur(s)
    check("creuser ne pose AUCUN ouvrage (rien à entretenir)",
          s["ouvrage"] is None and s["ligne_eau"] == MARE_LIGNE_EAU_CM)
    _vieillir_ouvrage(ceinture, 30.0)
    check("30 ans plus tard, la mare est toujours là",
          s["ligne_eau"] == MARE_LIGNE_EAU_CM)
    deplacer_ligne_eau(s, +1)
    _vieillir_ouvrage(ceinture, OUVRAGE_RUPTURE_ANS + 0.5)
    check("un barrage posé APRÈS rompt et rend l'eau à la mare, pas à zéro",
          s["ouvrage"] is None and s["ligne_eau"] == MARE_LIGNE_EAU_CM,
          f"{s['ligne_eau']:.0f} cm")

    check("tick_ouvrages(None) : no-op strict", tick_ouvrages(None) == [])
    vierge = [secteur_neutre(k) for k in COTES]
    avant = [dict(x) for x in vierge]
    for _ in range(500):
        tick_ouvrages(vierge)
    check("ceinture sans ouvrage : 500 ticks ne changent RIEN",
          [dict(x) for x in vierge] == avant)


# --- V. Irréversibilité de l'entaille (§4.4) -------------------------------
def test_irreversible():
    print("\n[V] Irréversible — certaines échelles ne nous appartiennent pas")
    gs, _, _ = _monde(type="falaise", altitude_relative=600.0)
    s = gs["ceinture"][NORD]
    ombre_avant = occulteurs(gs["ceinture"])[0][4]

    entailler(_plein(gs), PLAYER, NORD)
    check("entailler retire un pas de roche",
          s["altitude_relative"] == 600.0 - ENTAILLE_PAS_CM,
          f"{s['altitude_relative']:.0f} cm")
    check("… et la trace `entaille_cm` est posée", s["entaille_cm"] == ENTAILLE_PAS_CM)
    check("… l'ombre portée DIMINUE (② relit altitude_relative)",
          occulteurs(gs["ceinture"])[0][4] < ombre_avant,
          f"{occulteurs(gs['ceinture'])[0][4]:.0f} contre {ombre_avant:.0f} cm")
    check("… le ledger consigne", any("⛏" in l for l in gs["log"]))

    bas = s["altitude_relative"]
    for _ in range(10_000):                   # ~190 ans, les deux horloges
        tick_repousse(gs["ceinture"])
        tick_ouvrages(gs["ceinture"])
    check("10 000 ticks plus tard : la roche n'a JAMAIS repoussé",
          s["altitude_relative"] == bas and s["entaille_cm"] == ENTAILLE_PAS_CM,
          f"{s['altitude_relative']:.0f} cm")

    # Rasage complet : borné à 0, jamais négatif, et le geste finit par refuser.
    for _ in range(20):
        entailler(_plein(gs), PLAYER, NORD)
    check("roche rasée : altitude bornée à 0, cumul cohérent",
          s["altitude_relative"] == 0.0 and s["entaille_cm"] == 600.0,
          f"entaille {s['entaille_cm']:.0f} cm")
    check("plus rien à entailler : le geste refuse (et ne coûte rien)",
          not entailler(_plein(gs), PLAYER, NORD))
    check("une falaise rasée n'occulte plus rien", occulteurs(gs["ceinture"]) == [])
    check("entailler_secteur sur roche nulle : 0.0 retiré",
          entailler_secteur(secteur_neutre(NORD)) == 0.0)


# --- W. Érosion (§4.5) -----------------------------------------------------
def _eroder(ceinture, ticks=60, rows=COTE_PLOTS, cols=COTE_PLOTS):
    """Une tuile-monde soumise à `ticks` semaines d'érosion de bordure NORD."""
    eco = init_eco("e", rows, cols)
    lignes = []
    for _ in range(ticks):
        lignes += eco.tick_erosion(ceinture)
    return eco, lignes


def test_erosion():
    print("\n[W] Érosion — le seul retour qui laisse une trace DANS le sol")
    c = COTE_PLOTS // 2

    # Une coupe rase : densité mûre 0.8 → abattage (résiduel 0.10).
    rase = _ceinture(NORD, type="foret", essence="charme",
                     hauteur_canopee=1500.0, densite_ligneuse=0.8)
    couper_secteur(rase[NORD], "abattre")
    check("une coupe RASE érode", erosion_secteur(rase[NORD]) > 0.5,
          f"intensité {erosion_secteur(rase[NORD]):.3f}")

    ref = init_eco("e", COTE_PLOTS, COTE_PLOTS)
    eco, lignes = _eroder(rase)
    s0 = eco.structure_sol.at_plot(0, c)
    s1 = eco.structure_sol.at_plot(1, c)
    s2 = eco.structure_sol.at_plot(2, c)
    check("structure_sol DÉGRADÉE au bord",
          s0 < ref.structure_sol.at_plot(0, c) - 1e-9,
          f"{s0:.4f} contre {ref.structure_sol.at_plot(0, c):.4f}")
    check("… décroissance avec la distance au bord", s0 < s1 < s2,
          f"{s0:.4f} < {s1:.4f} < {s2:.4f}")
    check("… humus DILUÉ au bord",
          eco.om_stable.at_plot(0, c) < ref.om_stable.at_plot(0, c) - 1e-9,
          f"{eco.om_stable.at_plot(0, c):.4f}")
    check("plots CENTRAUX intacts (portée 3 plots)",
          abs(eco.structure_sol.at_plot(10, c)
              - ref.structure_sol.at_plot(10, c)) < 1e-12
          and abs(eco.om_stable.at_plot(10, c)
                  - ref.om_stable.at_plot(10, c)) < 1e-12)
    check("signe 🪨 émis UNE seule fois par épisode (pas chaque semaine)",
          len(lignes) == 1 and MARQUEUR_EBOULIS in lignes[0], lignes[0].strip())

    # L'étêtage conserve la densité ⇒ n'érode pas. La trogne est fréquentable.
    trogne = _ceinture(NORD, type="foret", essence="saule",
                       hauteur_canopee=1500.0, densite_ligneuse=0.8)
    couper_secteur(trogne[NORD], "eteter")
    check("un ÉTÊTAGE n'érode pas (densité conservée)",
          erosion_secteur(trogne[NORD]) == 0.0)

    # Une éclaircie légère non plus : il faut vraiment ouvrir le couvert.
    legere = secteur_neutre(NORD)
    legere.update(type="foret", densite_ligneuse=0.8, densite_avant=0.9)
    check("une ÉCLAIRCIE légère n'érode pas (seuil de dénudation)",
          erosion_secteur(legere) == 0.0,
          f"dénudation {1 - 0.8/0.9:.3f} < {EROSION_DENUDATION_MIN}")

    # La repousse ARRÊTE l'érosion, sans qu'aucune ligne ne le dise, et le signe
    # se ré-arme pour l'épisode suivant.
    for _ in range(int(30 * SEMAINES_PAR_AN)):
        tick_repousse(rase)
    check("après 30 ans de repousse : l'érosion a CESSÉ",
          erosion_secteur(rase[NORD]) == 0.0,
          f"densité revenue à {rase[NORD]['densite_ligneuse']:.3f}")
    apres, _ = _eroder(rase, ticks=20)
    check("… et plus rien ne se dépose",
          abs(apres.structure_sol.at_plot(0, c)
              - ref.structure_sol.at_plot(0, c)) < 1e-12)
    check("… le signe est ré-armé pour le prochain épisode",
          rase[NORD]["erosion_signalee"] is False)

    # Une falaise entaillée érode en PERMANENCE — l'irréversible rendu visible.
    falaise = _ceinture(NORD, type="falaise", altitude_relative=600.0)
    entailler_secteur(falaise[NORD])
    entailler_secteur(falaise[NORD])
    check("une falaise entaillée érode à pleine intensité",
          erosion_secteur(falaise[NORD]) == 1.0)
    for _ in range(int(50 * SEMAINES_PAR_AN)):
        tick_repousse(falaise)
    check("… et 50 ans plus tard elle érode TOUJOURS (rien ne la referme)",
          erosion_secteur(falaise[NORD]) == 1.0)

    # Une tuile LOIN du bord ne reçoit rien et ne déclenche AUCUN signe.
    loin = init_eco("loin", 4, 4)
    loin_ref = init_eco("loin", 4, 4)
    rase[NORD].update(densite_ligneuse=0.1, erosion_signalee=False)
    lignes = loin.tick_erosion(rase, tile_origin=(0.0, MONDE_CM / 2.0))
    check("tuile hors portée : aucune écriture, aucun signe",
          lignes == [] and loin.structure_sol.data == loin_ref.structure_sol.data
          and rase[NORD]["erosion_signalee"] is False)


# --- X. Neutralité : sans ceinture, rien ne s'exécute ---------------------
def test_neutralite():
    print("\n[X] Neutralité — sans ceinture, le golden ne peut pas bouger")
    a, b = init_eco("n", 12, 12), init_eco("n", 12, 12)
    for _ in range(20):
        a.tick_erosion(None)
        a.tick_berge(None)
        a.tick_hydrology("terre")
        b.tick_hydrology("terre")
    check("tick_erosion(None)/tick_berge(None) : champs bit-identiques",
          a.structure_sol.data == b.structure_sol.data
          and a.om_stable.data == b.om_stable.data
          and a.humidite.data == b.humidite.data)

    # Ceinture NEUTRE (4 prairies rases, aucune coupe, aucune entaille) : l'érosion
    # reste muette — c'est la dénudation qui la déclenche, pas la présence d'un bord.
    c, d = init_eco("m", 12, 12), init_eco("m", 12, 12)
    vierge = [secteur_neutre(k) for k in COTES]
    for _ in range(20):
        c.tick_erosion(vierge)
    check("ceinture NEUTRE : aucune érosion (rien n'a été dénudé)",
          c.structure_sol.data == d.structure_sol.data
          and c.om_stable.data == d.om_stable.data)
    check("… et aucun secteur n'érode", all(erosion_secteur(s) == 0.0 for s in vierge))

    # Le champ de lumière ne bouge pas non plus : une entaille n'existe que si la
    # falaise existe (cohérence avec le cache `geom_key` du ②).
    lf_a, lf_b = LightField(8, 8), LightField(8, 8)
    lf_a.compute([], "ete", ceinture=None)
    lf_b.compute([], "ete", ceinture=vierge)
    check("lumière : ceinture neutre ≡ pas de ceinture",
          lf_a.data == lf_b.data)


def main():
    test_gating()
    test_deplacement()
    test_rupture()
    test_irreversible()
    test_erosion()
    test_neutralite()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[test_peripherie_eau_roche] {n_ok}/{n} OK")
    if n_ok != n:
        print("ÉCHECS : " + ", ".join(name for name, ok in _results if not ok))
        sys.exit(1)
    print("[test_peripherie_eau_roche] PASS")


if __name__ == "__main__":
    main()
