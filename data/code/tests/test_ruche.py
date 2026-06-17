"""
SYMBIOSE — tests/test_ruche.py
Tronçon ⑥ (arc pollinisation) — ruche & miel (§H/§I, couche joueur).

La ruche est une structure posable (modèle bac/pile ⑤) qui CAPTURE un essaim
sauvage existant (philo #1 : pas d'abeilles dans le milieu → ruche vide) puis
PRODUIT du miel ∝ nectar mellifère butiné (§I.1). La récolte transfère le miel →
Vigueur joueur, GATÉE par un équipement débloqué par MAÎTRISE (§I.3).

Vérifications :
  A. POSER — `poser_ruche` crée une ruche VIDE (essaim/miel = 0) ; binaire.
  B. CAPTURE — abeille locale ≥ seuil → l'essaim MONTE (saturant) ; abeille
     effondrée → l'essaim DÉCLINE (famine/abandon §H.2).
  C. MIEL — essaim + nectar local (fleur mellifère) → le miel MONTE et plafonne ;
     sans fleur (nectar 0) → AUCUN miel (interconnexion floraison↔miel §I.1).
  D. HABITAT — une ruche peuplée RENFORCE l'habitat abeille local (§H.2).
  E. RÉCOLTE — équipement (palier maîtrise) → réserve vidée ; sans équipement →
     récolte partielle ; réserve vide → 0 (aucune Vigueur dépensée). Gain Vigueur.
  F. NEUTRALITÉ — sans ruche, `tick_ruches` est un no-op STRICT (golden §H.3).
  G. DÉTERMINISME — deux runs identiques → même état (zéro RNG).

Lancement (depuis data/code/) :
  python3 -m tests.test_ruche
"""
import sys

from world import Tile
from fields import init_eco
from fields.apiculture import (tick_ruches, ESSAIM_MIN, MIEL_MAX, MIEL_RATE,
                               CAPTURE_RATE)
from fields.population import _abeille_habitat_grid
from sim import actions as ACT
from sim import vigueur as V
from sim import maitrise as M
from plants import Basil

ROWS, COLS = 6, 8
RR, CC = 3, 4    # plot de la ruche (et de la fleur mellifère)

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'OK ' if cond else 'XX '} {name}" + (f" — {detail}" if detail else ""))


def _eco():
    tile = Tile(tile_id="TR", soil_type="terre")
    eco = init_eco("TR", ROWS, COLS, humidite=1.5, fertilite=1.0, microbiome=0.3)
    return tile, eco


def _gs(courante=None):
    gs = {"current_player": "joueur_1", "week": 1, "log": []}
    V.ensure_player(gs, "joueur_1")
    if courante is not None:
        gs["vigueur"]["joueur_1"]["courante"] = courante
    return gs


def _equiper(gs):
    """Force le palier de maîtrise pollinisation au seuil d'équipement (§I.3)."""
    st = M.ensure_player_maitrise(gs, "joueur_1")
    st["objets"][ACT.CONCEPT_ABEILLES] = {"palier": ACT.SEUIL_EQUIPEMENT, "preuves": 0}


# ---------------------------------------------------------------------------
def test_poser():
    print("\n[A] poser_ruche : structure vide, binaire")
    tile, eco = _eco()
    gs = _gs()
    ruche = ACT.poser_ruche(gs, "joueur_1", eco, RR, CC)
    check("ruche posée (Structure renvoyée)", ruche is not None and ruche.kind == "ruche")
    check("ruche VIDE (essaim=0, miel=0)", ruche.essaim == 0.0 and ruche.miel == 0.0)
    check("dans eco.structures", eco.structures == [ruche])
    # Binaire : Vigueur insuffisante → rien posé.
    gs_vide = _gs(courante=1.0)
    r2 = ACT.poser_ruche(gs_vide, "joueur_1", eco, 1, 1)
    check("Vigueur insuffisante → None, rien ajouté", r2 is None and len(eco.structures) == 1)


def test_capture_et_declin():
    print("\n[B] capture : abeille ≥ seuil → essaim monte ; effondrée → décline")
    tile, eco = _eco()
    gs = _gs()
    ruche = ACT.poser_ruche(gs, "joueur_1", eco, RR, CC)
    eco.populations["abeille"].fill(0.7)          # essaim sauvage présent
    serie = []
    for _ in range(6):
        tick_ruches(eco, tile, tile.plants)
        serie.append(ruche.essaim)
    check("l'essaim monte (capture saturante)", serie[0] > 0.0 and serie[-1] > serie[0],
          f"{serie[0]:.3f} → {serie[-1]:.3f}")
    check("essaim borné ≤ 1", serie[-1] <= 1.0, f"{serie[-1]:.4f}")
    # Abeille effondrée (sous le seuil) → déclin.
    eco.populations["abeille"].fill(ESSAIM_MIN * 0.5)
    avant = ruche.essaim
    for _ in range(5):
        tick_ruches(eco, tile, tile.plants)
    check("essaim décline quand l'abeille s'effondre (famine §H.2)",
          ruche.essaim < avant, f"{avant:.3f} → {ruche.essaim:.3f}")


def test_miel():
    print("\n[C] miel : essaim + nectar → miel monte/plafonne ; sans fleur → 0")
    tile, eco = _eco()
    gs = _gs()
    ruche = ACT.poser_ruche(gs, "joueur_1", eco, RR, CC)
    ruche.essaim = 1.0
    # SANS fleur : nectar nul → aucun miel, même essaim plein.
    for _ in range(3):
        tick_ruches(eco, tile, tile.plants)
    check("sans fleur mellifère → 0 miel (interconnexion §I.1)", ruche.miel == 0.0,
          f"{ruche.miel:.4f}")
    # AVEC une fleur mellifère (Basil, Lamiaceae attractivité abeille 1.0) au plot.
    p = tile.add_plant(Basil, RR, CC)
    p.floraison = 1.0
    ruche.essaim = 1.0
    tick_ruches(eco, tile, tile.plants)
    check("miel produit avec fleur + essaim", ruche.miel > 0.0, f"{ruche.miel:.4f}")
    for _ in range(200):
        ruche.essaim = 1.0                        # maintien (isolé du déclin)
        tick_ruches(eco, tile, tile.plants)
    check("miel plafonné à MIEL_MAX", abs(ruche.miel - MIEL_MAX) < 1e-6,
          f"{ruche.miel:.4f} / {MIEL_MAX}")


def test_habitat():
    print("\n[D] habitat : ruche peuplée renforce l'habitat abeille local (§H.2)")
    tile, eco = _eco()
    gs = _gs()
    ruche = ACT.poser_ruche(gs, "joueur_1", eco, RR, CC)
    base = _abeille_habitat_grid(eco, tile, tile.plants)[RR][CC]   # essaim 0
    ruche.essaim = 0.8
    bumped = _abeille_habitat_grid(eco, tile, tile.plants)[RR][CC]
    check("ruche vide → habitat inchangé", base == 0.0, f"{base:.3f}")
    check("ruche peuplée → habitat local renforcé", bumped > base, f"{base:.3f} → {bumped:.3f}")


def test_recolte():
    print("\n[E] recolter_miel : équipement → vide ; sans → partiel ; vide → 0")
    tile, eco = _eco()
    # Réserve vide → refus en amont, aucune Vigueur dépensée.
    gs = _gs()
    ruche = ACT.poser_ruche(gs, "joueur_1", eco, RR, CC)
    v_avant = gs["vigueur"]["joueur_1"]["courante"]
    g0 = ACT.recolter_miel(gs, "joueur_1", ruche)
    check("réserve vide → 0 gain, Vigueur intacte",
          g0 == 0.0 and gs["vigueur"]["joueur_1"]["courante"] == v_avant)
    # SANS équipement : récolte partielle.
    ruche.miel = 5.0
    g_sans = ACT.recolter_miel(gs, "joueur_1", ruche)
    attendu_sans = 5.0 * ACT.RECOLTE_SANS_EQUIP * ACT.MIEL_VIGUEUR_RATIO
    check("sans équipement → récolte PARTIELLE", abs(g_sans - attendu_sans) < 1e-6
          and ruche.miel > 0.0, f"gain {g_sans:.2f}, reste {ruche.miel:.2f}")
    check("équipement absent (gate)", not ACT.equipe(gs, "joueur_1"))
    # AVEC équipement (palier maîtrise) : réserve VIDÉE.
    gs2 = _gs()
    _equiper(gs2)
    ruche.miel = 5.0
    g_avec = ACT.recolter_miel(gs2, "joueur_1", ruche)
    check("équipement présent (palier ≥ seuil)", ACT.equipe(gs2, "joueur_1"))
    check("avec équipement → réserve VIDÉE, gain plein",
          abs(ruche.miel) < 1e-9 and abs(g_avec - 5.0 * ACT.MIEL_VIGUEUR_RATIO) < 1e-6,
          f"gain {g_avec:.2f}, reste {ruche.miel:.4f}")


def test_neutralite():
    print("\n[F] neutralité : sans ruche, tick_ruches est un no-op STRICT (§H.3)")
    tile, eco = _eco()
    tile.add_plant(Basil, RR, CC).floraison = 1.0
    eco.populations["abeille"].fill(0.9)
    # Aucune ruche posée : tick_ruches retourne immédiatement (aucun champ touché).
    before = [eco.populations[n].average() for n in ("abeille", "syrphe", "papillon")]
    tick_ruches(eco, tile, tile.plants)
    after = [eco.populations[n].average() for n in ("abeille", "syrphe", "papillon")]
    check("aucune structure posée", eco.structures == [])
    check("tick_ruches sans ruche n'écrit rien", before == after)


def test_determinisme():
    print("\n[G] déterminisme : deux runs identiques → même état")
    def run():
        tile, eco = _eco()
        gs = _gs()
        ruche = ACT.poser_ruche(gs, "joueur_1", eco, RR, CC)
        tile.add_plant(Basil, RR, CC).floraison = 1.0
        eco.populations["abeille"].fill(0.6)
        for _ in range(10):
            tick_ruches(eco, tile, tile.plants)
        return round(ruche.essaim, 9), round(ruche.miel, 9)
    a, b = run(), run()
    check("deux runs → essaim/miel identiques", a == b, f"{a} vs {b}")


def main():
    test_poser()
    test_capture_et_declin()
    test_miel()
    test_habitat()
    test_recolte()
    test_neutralite()
    test_determinisme()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[ruche] {n_ok}/{n} OK")
    sys.exit(0 if n_ok == n else 1)


if __name__ == "__main__":
    main()
