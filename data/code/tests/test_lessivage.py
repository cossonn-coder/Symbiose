"""
SYMBIOSE — tests/test_lessivage.py
Tests ciblés du lessivage NPK AMPLIFIÉ par la pluie (sprint météo→champs ③, §4).

Le lessivage passif existe DÉJÀ (`tick_decomposition` : `champ *= leach_factor(...)`,
rétention modulée par la CEC = texture + humus). Ce tronçon ne le RECRÉE pas : il
l'AMPLIFIE ∝ l'eau qui a DRAINÉ ce tick (carte `drainage_last` écrite par
`tick_hydrology`, lue par le lessivage). On l'exerce HORS golden sur des EcoFields à
conditions forcées (N/P/K uniformes, `drainage_last` posé à la main, litière vide
pour isoler le lessivage des apports de minéralisation).

Couvre la définition de done du kickoff :
  1. LESSIVAGE_PLUIE_K agit : forte pluie drainée → N chute PLUS qu'à pluie nulle.
  2. P jamais AMPLIFIÉ : sous forte pluie, P ne perd que sa part passive (puissance 1).
  3. Hiérarchie N≫K>P : la chute relative de N > celle de K > celle de P.
  4. Interconnexion CEC : sol drainant (CEC basse) lessive PLUS qu'un sol retenteur
     (CEC haute, argile/humus) à drainage égal.
  5. Cap : un drainage énorme ne dépasse jamais FACTEUR_PLUIE_CAP (pas de vidage).
  6. drainage_last = 0 → RIEN ne lessive (D120 ① : lessivage lié à l'eau).
  7. déterminisme : deux runs identiques → mêmes valeurs.
  8. Recharge (D120 ①) : un plot nu en jachère, sans drainage, comble au moins la
     moitié de son écart à l'équilibre de la roche en N en 52 semaines.
  9. Recharge : un sol au-dessus de l'équilibre n'est pas rabattu ; un mini-sol de
     conteneur (`recharge_roche=False`) ne recharge pas.

Les cas 1-7 isolent le LESSIVAGE : `tick_decomposition(recharge_roche=False)`.

Usage (depuis data/code/) :
  python3 -m tests.test_lessivage
"""
import sys

from fields import init_eco
from fields.ecofields.nutriments import leach_factor, cec_norm_at, equilibre_roche
from fields.ecofields.constants import (LESSIVAGE_PLUIE_K, DRAINAGE_PERTE_REF,
                                        FACTEUR_PLUIE_CAP, LESSIVAGE_K_ATTENUATION)

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _eco(soil_type="terre", npk=1.0):
    """Mini-sol 3×3 à N/P/K uniformes, sans litière vivante (litière `diffus` à 0)
    ni microbiome → la minéralisation n'ajoute rien : on isole le lessivage."""
    eco = init_eco("L", 3, 3, humidite=1.0, microbiome=0.0, soil_type=soil_type)
    # Humus de fond REMIS À 0 (D56, ① : `om_stable` part désormais hétérogène
    # ≈ OM_STABLE_INIT). Ce test ISOLE le lessivage — comme il annule déjà litière et
    # microbiome, on annule aussi l'humus de fond pour que la CEC de référence soit
    # exactement `cec_norm(om_stable=0)` et que les égalités math (bornes 5/6) tiennent.
    eco.om_stable.fill(0.0)
    for r in range(3):
        for c in range(3):
            eco.n.set(r, c, npk)
            eco.p.set(r, c, npk)
            eco.k.set(r, c, npk)
    return eco


def _set_drainage(eco, perte):
    """Pose une perte de drainage uniforme (ce que `tick_hydrology` écrirait)."""
    for r in range(eco.rows):
        for c in range(eco.cols):
            eco.drainage_last.set(r, c, perte)


def _moy(field):
    return field.average()


# Perte de drainage « forte pluie » (≥ DRAINAGE_PERTE_REF → drainage_norm sature à 1).
FORTE_PLUIE = DRAINAGE_PERTE_REF * 2.0


def run():
    print("== test_lessivage (météo→champs ③) ==")

    # 1. LESSIVAGE_PLUIE_K agit : forte pluie drainée → N chute plus qu'à sec.
    eco_sec = _eco(); _set_drainage(eco_sec, 0.0); eco_sec.tick_decomposition(recharge_roche=False)
    eco_pluie = _eco(); _set_drainage(eco_pluie, FORTE_PLUIE); eco_pluie.tick_decomposition(recharge_roche=False)
    n_sec, n_pluie = _moy(eco_sec.n), _moy(eco_pluie.n)
    check("1. forte pluie → N chute davantage", n_pluie < n_sec,
          f"N sec={n_sec:.5f} > N pluie={n_pluie:.5f}")

    # 2. P jamais amplifié : sous forte pluie, P ne perd que sa part PASSIVE
    #    (drainage plein, puissance 1) — D120 ① : à sec il ne perd plus rien du tout.
    p_sec, p_pluie = _moy(eco_sec.p), _moy(eco_pluie.p)
    cn0 = cec_norm_at("terre", 0.0)
    check("2. P non amplifié par la pluie", abs(p_pluie - leach_factor("P", cn0)) < 1e-9,
          f"P pluie={p_pluie:.6f} = passif {leach_factor('P', cn0):.6f}")

    # 3. Hiérarchie N≫K>P sur la chute RELATIVE due à la pluie.
    chute_n = n_sec - n_pluie
    chute_k = _moy(eco_sec.k) - _moy(eco_pluie.k)
    chute_p = p_sec - p_pluie
    check("3. hiérarchie chute N > K > P", chute_n > chute_k > chute_p - 1e-12,
          f"ΔN={chute_n:.5f} ΔK={chute_k:.5f} ΔP={chute_p:.6f}")

    # 4. Interconnexion CEC : sol drainant (sable, CEC 0.2) lessive PLUS d'azote
    #    qu'un sol retenteur (argile, CEC 0.8) à drainage IDENTIQUE.
    eco_sable = _eco("sable"); _set_drainage(eco_sable, FORTE_PLUIE); eco_sable.tick_decomposition(recharge_roche=False)
    eco_argile = _eco("argile"); _set_drainage(eco_argile, FORTE_PLUIE); eco_argile.tick_decomposition(recharge_roche=False)
    check("4. CEC basse (sable) lessive plus que CEC haute (argile)",
          _moy(eco_sable.n) < _moy(eco_argile.n),
          f"N sable={_moy(eco_sable.n):.5f} < N argile={_moy(eco_argile.n):.5f}")

    # 5. Borne : un drainage absurde ne lessive jamais plus que le facteur EFFECTIF
    #    maximal min(1 + K·1, CAP) — drainage_norm est saturé à 1, puis le cap dur
    #    s'applique. Aux valeurs courantes (K=1.5) → facteur eff = 2.5 < CAP=3.0,
    #    donc la borne vient de la saturation drainage_norm ; le cap reste un garde-fou
    #    si K est relevé. On vérifie que N ne descend pas SOUS le facteur effectif max.
    eco_cap = _eco(); _set_drainage(eco_cap, FORTE_PLUIE * 1000.0); eco_cap.tick_decomposition(recharge_roche=False)
    cn = cec_norm_at("terre", min(1.0, 0.0 / 5.0))   # `_eco` annule l'humus de fond (D56)
    facteur_eff_max = min(1.0 + LESSIVAGE_PLUIE_K * 1.0, FACTEUR_PLUIE_CAP)
    n_borne = 1.0 * leach_factor("N", cn) ** facteur_eff_max
    check("5. facteur_pluie borné (saturation + cap dur)",
          abs(_moy(eco_cap.n) - n_borne) < 1e-9,
          f"N cap={_moy(eco_cap.n):.5f} = leach^{facteur_eff_max}={n_borne:.5f}")

    # 6. drainage_last = 0 → RIEN ne lessive (D120 ① : un ion ne quitte la zone
    #    racinaire qu'emporté par l'eau qui descend).
    check("6. drainage nul ⇒ aucun lessivage",
          abs(n_sec - 1.0) < 1e-12 and abs(p_sec - 1.0) < 1e-12,
          f"N sec={n_sec:.6f}, P sec={p_sec:.6f} (départ 1.0)")

    # 7. déterminisme : deux runs identiques → mêmes valeurs.
    eco_a = _eco(); _set_drainage(eco_a, FORTE_PLUIE); eco_a.tick_decomposition(recharge_roche=False)
    eco_b = _eco(); _set_drainage(eco_b, FORTE_PLUIE); eco_b.tick_decomposition(recharge_roche=False)
    check("7. déterminisme (deux runs identiques)",
          _moy(eco_a.n) == _moy(eco_b.n) == n_pluie,
          f"{_moy(eco_a.n):.6f} == {_moy(eco_b.n):.6f}")

    # 8. Recharge (D120 ①) : plot nu en jachère (sans plante, sans drainage, sans
    #    litière ni microbiome) — N part à 0.1, l'équilibre roche « terre » est 1.0.
    eq_n = equilibre_roche("terre")[0]
    eco_j = _eco(npk=0.1); _set_drainage(eco_j, 0.0)
    for _ in range(52):
        eco_j.tick_decomposition()
    comble = (_moy(eco_j.n) - 0.1) / (eq_n - 0.1)
    check("8. jachère : ≥ ½ de l'écart N comblé en 1 an", comble >= 0.5,
          f"N 0.10 → {_moy(eco_j.n):.3f} (écart comblé {comble:.0%})")

    # 9. Sol enrichi non rabattu ; conteneur sans roche → pas de recharge.
    eco_r = _eco(npk=2.0); _set_drainage(eco_r, 0.0); eco_r.tick_decomposition()
    eco_c = _eco(npk=0.1); _set_drainage(eco_c, 0.0)
    eco_c.tick_decomposition(recharge_roche=False)
    check("9. au-dessus de l'équilibre / conteneur : aucune recharge",
          abs(_moy(eco_r.n) - 2.0) < 1e-12 and abs(_moy(eco_c.n) - 0.1) < 1e-12,
          f"N enrichi={_moy(eco_r.n):.4f}, N conteneur={_moy(eco_c.n):.4f}")

    ok = sum(1 for _, c in _results if c)
    total = len(_results)
    print(f"\n{ok}/{total} OK")
    return ok == total


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
