"""
SYMBIOSE — tests/test_substrat.py
Tests ciblés du tronçon ① du sprint pots/bacs : le registre data-driven des
substrats (`world/substrat.py`) + le hook `drainage_override` de `tick_hydrology`.

Tronçon DATA PURE : aucun conteneur, aucune boucle touchée. Ces tests vérifient
seulement (a) le contenu du registre conforme à la CONCEPTION §2, (b) que les
tissus de pré-charge sont CONNUS du moteur, (c) l'accès `get_substrat`, et (d) que
`drainage_override` change bien le drainage d'un `EcoFields` jouet (le défaut
`None` laissant le comportement historique).

Le golden ÉCOLOGIQUE reste l'autorité du déterminisme ; ici on exerce la donnée
et le hook hors golden.

Usage (depuis data/code/) :
  python3 -m tests.test_substrat
"""
import sys

from fields import init_eco, DRAINAGE
from fields.ecofields import TISSU, FAIM_N_TISSUS
from world import SUBSTRATS, get_substrat, SubstratRecette

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# --- A. Présence des 6 recettes ---
CLES_ATTENDUES = {"terreau", "compost", "drainant_mineral",
                  "lasagnes", "terre_jardin", "mycelium_use"}
check("6 clés exactes", set(SUBSTRATS) == CLES_ATTENDUES,
      detail=str(sorted(SUBSTRATS)))
check("toutes des SubstratRecette",
      all(isinstance(r, SubstratRecette) for r in SUBSTRATS.values()))


# --- B. Valeurs EXACTES du tableau §2 ---
def vals(r):
    return (r.drainage, r.structure_init, r.ph_init, r.npk_init,
            r.microbiome_init, r.litiere_precharge, r.herite_tuile)


ATTENDU = {
    "terreau":          (0.990, 0.85, 6.5, (1.2, 1.0, 1.0), 0.6, (), False),
    "compost":          (0.992, 0.90, 7.0, (2.2, 1.5, 1.8), 1.5, (), False),
    "drainant_mineral": (0.975, 0.95, 6.8, (0.2, 0.2, 0.2), 0.1, (), False),
    "lasagnes":         (0.988, 0.70, 6.5, (0.5, 0.4, 0.4), 0.8,
                         (("feuille", 2.0), ("herbace", 1.0), ("bois", 0.8)), False),
    "terre_jardin":     (0.993, 0.70, 6.5, (1.0, 1.0, 1.0), 0.5, (), True),
    "mycelium_use":     (0.985, 0.80, 6.5, (0.3, 0.3, 0.3), 0.5,
                         (("substrat", 2.0),), False),
}
for cle, attendu in ATTENDU.items():
    check(f"valeurs {cle}", vals(SUBSTRATS[cle]) == attendu,
          detail="" if vals(SUBSTRATS[cle]) == attendu else f"got {vals(SUBSTRATS[cle])}")

check("terre_jardin a herite_tuile=True", SUBSTRATS["terre_jardin"].herite_tuile)


# --- C. Tissus de pré-charge CONNUS du moteur ---
connus = frozenset(TISSU.keys()) | FAIM_N_TISSUS
for cle, rec in SUBSTRATS.items():
    for tissu, _m in rec.litiere_precharge:
        check(f"tissu {tissu!r} ({cle}) connu", tissu in connus,
              detail=f"connus={sorted(connus)}")


# --- D. get_substrat ---
check("get_substrat('compost') == registre",
      get_substrat("compost") is SUBSTRATS["compost"])
try:
    get_substrat("inexistant_xyz")
    check("get_substrat lève sur clé inconnue", False, detail="pas d'exception")
except KeyError:
    check("get_substrat lève sur clé inconnue", True)


# --- E. drainage_override change bien le drainage (EcoFields jouet) ---
# Deux mini-sols identiques, humidité de départ élevée pour voir le drainage agir.
# L'un sans override (drainage historique terre), l'autre avec un override plus
# DRAINANT (0.90 << 0.993) → l'humidité finale doit être PLUS BASSE avec override.
HUM0 = 2.0
eco_def = init_eco("jouet_def", 1, 1, humidite=HUM0)
eco_ovr = init_eco("jouet_ovr", 1, 1, humidite=HUM0)
eco_def.tick_hydrology()                          # défaut : override=None
eco_ovr.tick_hydrology(drainage_override=0.90)    # substrat plus drainant
h_def = eco_def.humidite.data[0][0]
h_ovr = eco_ovr.humidite.data[0][0]
check("override 0.90 assèche davantage que le défaut", h_ovr < h_def,
      detail=f"h_def={h_def:.4f} h_ovr={h_ovr:.4f}")

# Et l'override None reproduit EXACTEMENT le drainage terre historique : un 3e
# mini-sol avec override=DRAINAGE explicite doit coïncider avec le défaut. MÊME
# tile_id que `eco_def` : depuis ①a l'`om_stable`/`epaisseur_sol` de fond est
# HÉTÉROGÈNE par `tile_id` (D56, hash), et depuis ①b la rétention d'épaisseur les
# LIT (`tick_hydrology` step 3b) — deux tuiles de tile_id ≠ ne sont donc plus bit-
# identiques. Ce test isole la SEULE variable drainage_override → même tile_id.
eco_eq = init_eco("jouet_def", 1, 1, humidite=HUM0)
eco_eq.tick_hydrology(drainage_override=DRAINAGE)
check("override=DRAINAGE ≡ défaut (rétrocompat)",
      eco_eq.humidite.data[0][0] == h_def,
      detail=f"{eco_eq.humidite.data[0][0]:.6f} vs {h_def:.6f}")


# --- Bilan ---
fails = [n for n, ok in _results if not ok]
if fails:
    print(f"\n[test_substrat] FAIL — {len(fails)}/{len(_results)} rouges : {fails}")
    sys.exit(1)
print(f"\n[test_substrat] PASS — {len(_results)}/{len(_results)} OK")
