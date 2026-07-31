"""
SYMBIOSE — tools/banc_favorabilite.py
Banc de mesure de la PRÉCONDITION D41 (sprint RYTHMES MO, tronçon ③).

But : après la recalibration D77/D40 (dénominateur `microbiome / MICROBE_RHYTHM_REF`
+ cap, tronçons ① et ②), mesurer sur le jardin SAIN (seed 42, ~20 ans) ce que la
nouvelle dynamique produit, et livrer le **verdict de précondition D41** :

  favorabilité = Liebig(min(N, P, K normalisés)) × fenêtre_pH,  calculée DIRECTEMENT
  (PAS via `qi_local`, qui reste épuisé — cf. DETTE.md D41).

D41 (mort par carence édaphique chronique) attend un signal ≈ FAVORABLE en
conditions normales (comme `drought_memory ≈ 0` pour la voie sécheresse). Si la
favorabilité médiane d'un sol sain est HAUTE, la précondition est atteinte → GO.
Si elle reste basse, on documente ce qui manque → NO-GO.

Ce banc est PURE MESURE : il ne touche pas le moteur, ne re-fige aucun golden.
Il RÉUTILISE les fonctions du moteur (aucune ré-implémentation) :
  • `FIELD_NORM` (sim.vigueur_plante) — normalisation canonique des champs NPK.
  • `dispo(ph, nut)` (fields.ecofields.nutriments) — fenêtre pH en cloche par nutriment.
  • `microbe_clim_factor` (fields.ecofields.thermique) — cloche T × humidité (D40).
  • `MICROBE_RHYTHM_REF` — le dénominateur recalibré du sprint.

Lancement (depuis data/code/) :
  python3 -m tools.banc_favorabilite            # 20 ans, jardin sain
  python3 -m tools.banc_favorabilite 20         # idem (⚠ NE JAMAIS 500 ans, interdit)
"""

import sys
import statistics

from world import House
from sim.engine import Engine
from sim.vigueur_plante import FIELD_NORM
from fields.ecofields.nutriments import dispo
from fields.ecofields.thermique import microbe_clim_factor
from fields.ecofields.constants import MICROBE_RHYTHM_REF

# Réutilise le monde fondateur du banc de calibration (seed 42, miroir golden) —
# pas de duplication du build_world.
from tools.banc_calibration import build_world, SEED


def favorabilite_plot(eco, r: int, c: int) -> float:
    """Favorabilité édaphique D41 DIRECTE d'un plot ∈ [0, 1] (le livrable clé).

    `Liebig(min N,P,K normalisés) × fenêtre_pH`, calculée sans `qi_local` :
      • Liebig = min des trois nutriments normalisés par `FIELD_NORM` (la loi du
        minimum : le sol vaut son nutriment le plus rare) — même normalisation que
        `qi_local`/`plant_uptake`.
      • fenêtre_pH = min des trois cloches `dispo(ph, nut)` : la disponibilité au pH
        local du nutriment le plus PÉNALISÉ par le pH (Liebig sur la fenêtre elle-même,
        P étroit → souvent limitant). C'est un FLUX de disponibilité, jamais un gate.
    Read-only, déterministe (philo #3)."""
    n_norm = min(1.0, eco.n.at_plot(r, c) / FIELD_NORM)
    p_norm = min(1.0, eco.p.at_plot(r, c) / FIELD_NORM)
    k_norm = min(1.0, eco.k.at_plot(r, c) / FIELD_NORM)
    liebig = min(n_norm, p_norm, k_norm)
    ph = eco.ph.at_plot(r, c)
    fenetre = min(dispo(ph, "N"), dispo(ph, "P"), dispo(ph, "K"))
    return liebig * fenetre


def _all_plots(ecos):
    """Itère (eco, r, c) sur tous les plots des tuiles saines (le jardin entier)."""
    for eco in ecos.values():
        for r in range(eco.rows):
            for c in range(eco.cols):
                yield eco, r, c


def _swing_d40(eco) -> tuple[float, float, float]:
    """Preuve que D40 vit : swing saisonnier de la vitesse de décompo sur un plot
    RICHE (microbiome au plus haut du jardin), hiver (T_sol froid) vs été (chaud),
    humidité optimale, pH neutre. Réutilise `microbe_clim_factor` et la MÊME formule
    que `tick_decomposition` (`speed = 0.5 + micro·f_clim·0.5`)."""
    # Plot le plus riche en microbiome (le « sol vivant » où D40 doit se voir).
    best = max(((r, c) for r in range(eco.rows) for c in range(eco.cols)),
               key=lambda rc: eco.microbiome.at_plot(*rc))
    mb = eco.microbiome.at_plot(*best)
    micro = min(1.0, mb / MICROBE_RHYTHM_REF)          # cap structurel du sprint
    hum_opt = 0.6                                       # humidité proche de l'optimum
    hiver = micro * microbe_clim_factor(4.0, hum_opt)   # T_sol 4 °C
    ete = micro * microbe_clim_factor(22.0, hum_opt)    # T_sol 22 °C
    v_hiver = 0.5 + hiver * 0.5
    v_ete = 0.5 + ete * 0.5
    swing = (v_ete - v_hiver) / v_hiver * 100.0 if v_hiver > 0 else 0.0
    return v_hiver, v_ete, swing


def run(years: int) -> None:
    tiles, ecos = build_world(dense=True)
    game_state = {"tiles": tiles, "eco": ecos, "scores": {},
                  "current_player": "joueur_1", "week": 1, "log": [],
                  "house": House()}
    engine = Engine(game_state)
    print(f"\n===== JARDIN SAIN — {years} ans, seed {SEED} =====")
    print("Par année : microbiome / NPK moy / humus (om) / favorabilité D41 (médiane)")
    print(f"{'an':>3} | {'micro':>6} | {'N moy':>6} | {'P moy':>6} | {'K moy':>6} | "
          f"{'omA':>6} | {'omS':>6} | {'favo méd':>8} | {'favo moy':>8}")
    favos_final = []
    for y in range(1, years + 1):
        for _ in range(52):
            engine.tick_semaine()
            game_state["log"].clear()
        n_moy = statistics.mean(eco.n.at_plot(r, c) for eco, r, c in _all_plots(ecos))
        p_moy = statistics.mean(eco.p.at_plot(r, c) for eco, r, c in _all_plots(ecos))
        k_moy = statistics.mean(eco.k.at_plot(r, c) for eco, r, c in _all_plots(ecos))
        mb_moy = statistics.mean(eco.microbiome.at_plot(r, c) for eco, r, c in _all_plots(ecos))
        oma = statistics.mean(eco.om_active.at_plot(r, c) for eco, r, c in _all_plots(ecos))
        oms = statistics.mean(eco.om_stable.at_plot(r, c) for eco, r, c in _all_plots(ecos))
        favos = [favorabilite_plot(eco, r, c) for eco, r, c in _all_plots(ecos)]
        favos_final = favos
        print(f"{y:>3} | {mb_moy:>6.3f} | {n_moy:>6.3f} | {p_moy:>6.3f} | {k_moy:>6.3f} | "
              f"{oma:>6.3f} | {oms:>6.3f} | {statistics.median(favos):>8.3f} | "
              f"{statistics.mean(favos):>8.3f}")

    # Distribution finale de la favorabilité (le verdict).
    favos_final.sort()
    n = len(favos_final)
    p10 = favos_final[n // 10]
    p90 = favos_final[(9 * n) // 10]
    print(f"\n--- Favorabilité D41 (Liebig×pH direct) sur sol sain, an {years} ---")
    print(f"  n plots        : {n}")
    print(f"  médiane        : {statistics.median(favos_final):.3f}")
    print(f"  moyenne        : {statistics.mean(favos_final):.3f}")
    print(f"  p10 / p90      : {p10:.3f} / {p90:.3f}")
    print(f"  min / max      : {favos_final[0]:.3f} / {favos_final[-1]:.3f}")

    v_h, v_e, swing = _swing_d40(ecos["T0"])
    print(f"\n--- Preuve D40 (swing décompo saisonnier, plot riche) ---")
    print(f"  hiver 4 °C : {v_h:.3f}   été 22 °C : {v_e:.3f}   swing : +{swing:.1f} %")
    print("  (cible ≈ +50 % ; avant sprint : +13 %)")

    print("\nAncres de lecture favorabilité : ≈ `drought_memory` inversé — une voie")
    print("« mort chronique » est SAINE si la médiane d'un sol sain est HAUTE (≥ ~0.6).")


def main() -> int:
    years = 20
    if len(sys.argv) > 1:
        years = int(sys.argv[1])
    if years > 100:
        print("⚠ banc bridé à 100 ans (les runs longs sont interdits, cf. 00_etat.md)")
        years = 100
    run(years)
    return 0


if __name__ == "__main__":
    sys.exit(main())
