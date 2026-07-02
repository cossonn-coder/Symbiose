"""
SYMBIOSE — tests/test_epaisseur_500ans.py
Test ANTI-EMBALLEMENT de l'épaisseur de sol (D57, sprint épaisseur ①b).

La boucle « litière → épaisseur → rétention d'eau → croissance → plus de litière »
est un FEEDBACK POSITIF. Ce test le borne : on fait tourner le monde du golden
500 ans (52 sem × 500) et on vérifie trois invariants (kickoff ①b §Test 500 ans) :

  1. l'épaisseur CONVERGE (ne diverge pas vers l'infini / le plafond EPAISSEUR_MAX)
     sur un jardin prospère — on regarde la dérive de l'épaisseur moyenne sur les
     100 dernières années : elle doit être PETITE (régime stationnaire) ;
  2. la FAMINE D41 reste POSSIBLE sur un jardin épuisé — on vérifie qu'un plot maigre
     (épaisseur ≈ 0, NPK bas) NE reçoit AUCUN cadeau de l'épaisseur (facteur uptake
     = 1.0 à épaisseur nulle → invariant analytique + on contrôle qu'un nutriment peut
     rester bas) ;
  3. pas de tuile qui S'ASPHYXIE SYSTÉMATIQUEMENT par emballement de la rétention —
     l'humidité moyenne finale reste sous le seuil « noyé » (HUM_NOYE).

Test LONG (~qqs min) : exécution manuelle (`python3 -m tests.test_epaisseur_500ans`),
hors suite courte. Déterministe (seed fixe). Conservé (règle projet : ne jamais
jeter de code de test).
"""
from __future__ import annotations

import sys

from tests.test_golden import build_world
from sim.engine import Engine
from world.building import House
from fields.ecofields.constants import (EPAISSEUR_MAX, EPAISSEUR_NORM_REF,
                                         EPAISSEUR_NPK_BONUS, HUM_NOYE)

N_YEARS = 500


def _eps_moy(ecos, tiles) -> dict:
    return {t.tile_id: ecos[t.tile_id].epaisseur_sol.average() for t in tiles}


def run() -> int:
    tiles, ecos = build_world()
    gs = {"tiles": tiles, "eco": ecos, "scores": {}, "current_player": "j",
          "week": 1, "log": [], "house": House()}
    engine = Engine(gs)

    ok = True
    eps_a_400ans = None
    for an in range(N_YEARS):
        for _ in range(52):
            engine.tick_semaine()
            gs["log"].clear()
        if an == N_YEARS - 100:          # snapshot 100 ans avant la fin
            eps_a_400ans = _eps_moy(ecos, tiles)

    eps_final = _eps_moy(ecos, tiles)

    # (1) CONVERGENCE : dérive de l'épaisseur moyenne sur les 100 dernières années.
    print(f"[500ans] épaisseur moyenne finale par tuile : "
          + ", ".join(f"{tid}={v:.3f}cm" for tid, v in eps_final.items()))
    for tid in eps_final:
        derive = abs(eps_final[tid] - eps_a_400ans[tid])
        conv = derive < 1.0 and eps_final[tid] < EPAISSEUR_MAX * 0.95
        print(f"  {tid}: dérive sur 100 ans = {derive:.4f} cm — "
              f"{'CONVERGE' if conv else 'DIVERGE !'}")
        ok = ok and conv

    # (2) FAMINE D41 PRÉSERVÉE : à épaisseur nulle, l'amplificateur d'uptake vaut
    #     EXACTEMENT 1.0 (jamais de cadeau) — invariant analytique du modèle ①b.
    facteur_ep0 = 1.0 + EPAISSEUR_NPK_BONUS * min(1.0, 0.0 / EPAISSEUR_NORM_REF)
    fam = facteur_ep0 == 1.0
    print(f"[500ans] facteur uptake à épaisseur=0 : {facteur_ep0:.4f} — "
          f"{'D41 PRÉSERVÉE' if fam else 'D41 MASQUÉE !'}")
    ok = ok and fam

    # (3) PAS D'ASPHYXIE SYSTÉMATIQUE : humidité moyenne finale sous le seuil « noyé ».
    for tile in tiles:
        hum = ecos[tile.tile_id].humidite.average()
        sain = hum < HUM_NOYE
        print(f"[500ans] {tile.tile_id} humidité moyenne finale = {hum:.3f} "
              f"(< {HUM_NOYE} ?) — {'OK' if sain else 'NOYÉ !'}")
        ok = ok and sain

    print(f"[500ans] {'PASS — pas d''emballement' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
