"""
SYMBIOSE — tests/test_diversite_fondatrice.py
Tests du tronçon ① — GÉNÉTIQUE FONDATRICE (sprint DIVERSITÉ FONDATRICE).

Cœur de la demande : une plante née SANS lignée ne doit plus être un CLONE neutre.
On active `GENE_INIT_SIGMA` via `founder_genes` (+ ensemencement du pool-sol
`seed_founder_pool`), toujours DÉTERMINISTE (philo #3, aucun RNG live).

Quatre vérifications :
  1. DÉTERMINISME — même (cls, seed, week, r, c, x_cm, y_cm) → gènes IDENTIQUES.
  2. DIVERSITÉ inter-position — deux positions CONTINUES ≠ au MÊME plot donnent des
     gènes ≠ (correctif B : compétition intra-plot, plus de clones).
  3. VARIANCE bornée — les gènes tournent autour de 1.0, dans les bornes dures.
  4. POOL ensemencé — `seed_founder_pool` rend `sample_genes` NON vide dès le départ.

Usage (depuis data/code/) : python3 -m tests.test_diversite_fondatrice
"""

from plants import Tomato, Basil, GENE_NAMES
from plants.genetics import GENE_HARD_MIN, GENE_HARD_MAX, GENE_INIT_SIGMA
from fields import SeedBank, founder_genes, FOUNDER_POOL_DENSITY
from fields.ecofields import init_eco

SEED = 0x5AB1057E
_results = []


def _valeurs(champ, rows, cols):
    return [champ.at_plot(r, c) for r in range(rows) for c in range(cols)]


def _variance(vals):
    m = sum(vals) / len(vals)
    return sum((v - m) ** 2 for v in vals) / len(vals)


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def test_determinisme():
    """Rejouer le même tirage fondateur donne EXACTEMENT les mêmes gènes."""
    a = founder_genes(Tomato, SEED, 0, 2, 3, 125.0, 175.0)
    b = founder_genes(Tomato, SEED, 0, 2, 3, 125.0, 175.0)
    check("déterminisme", a == b, f"{len(a)} gènes identiques")
    check("vecteur complet", set(a) == set(GENE_NAMES),
          f"{len(a)}/{len(GENE_NAMES)} gènes")


def test_diversite_inter_position():
    """Deux individus de MÊME espèce partageant un plot (positions continues
    distinctes) ne sont PLUS des clones (correctif B)."""
    a = founder_genes(Tomato, SEED, 0, 2, 3, 110.0, 160.0)
    b = founder_genes(Tomato, SEED, 0, 2, 3, 140.0, 190.0)   # même plot, autre point
    check("diversité intra-plot", a != b,
          "deux positions continues → gènes différents")
    # Deux ESPÈCES au même point diffèrent aussi (canal décorrélé par nom de classe).
    t = founder_genes(Tomato, SEED, 0, 2, 3, 125.0, 175.0)
    ba = founder_genes(Basil, SEED, 0, 2, 3, 125.0, 175.0)
    check("diversité inter-espèce", t != ba, "canal décorrélé par espèce")


def test_variance_bornee():
    """La variance fondatrice est présente (pas de clones neutres) mais SAINE :
    centrée ~1.0, jamais hors des bornes dures physiologiques."""
    vals = []
    for r in range(6):
        for c in range(8):
            g = founder_genes(Tomato, SEED, 0, r, c,
                              c * 50 + 25.0, r * 50 + 25.0)
            vals.extend(g.values())
    non_neutres = sum(1 for v in vals if abs(v - 1.0) > 1e-6)
    check("variance présente", non_neutres == len(vals),
          f"{non_neutres}/{len(vals)} gènes ≠ 1.0 (aucun clone)")
    check("bornes dures respectées",
          all(GENE_HARD_MIN <= v <= GENE_HARD_MAX for v in vals),
          f"min={min(vals):.3f} max={max(vals):.3f}")
    moy = sum(vals) / len(vals)
    check("centrée ~1.0", abs(moy - 1.0) < 0.03, f"moyenne={moy:.4f}")


def test_pool_ensemence():
    """`seed_founder_pool` rend `sample_genes` NON vide dès le tick 0 (le pool-sol
    fondateur n'est jamais génétiquement uniforme, philo #4)."""
    bank = SeedBank(4, 4)
    # Pool vide au départ → gènes neutres (dict vide, rétro-compatible).
    check("pool vide → neutre",
          bank.sample_genes(1, 1, Tomato, SEED, 0) == {},
          "avant ensemencement")
    bank.seed_founder_pool(1, 1, Tomato, GENE_INIT_SIGMA, FOUNDER_POOL_DENSITY)
    g = bank.sample_genes(1, 1, Tomato, SEED, 0)
    check("pool ensemencé → non vide", bool(g) and set(g) == set(GENE_NAMES),
          f"{len(g)} gènes tirés")
    check("variance du pool (tirage ≠ 1.0)",
          any(abs(v - 1.0) > 1e-6 for v in g.values()),
          "sélection a de quoi mordre")


def test_catena_hetero_vs_uniforme():
    """Tronçon ② — hétérogénéité fondatrice des champs de sol (catena topo).
    Sous `heterogene=True`, les champs édaphiques deviennent NON uniformes ;
    au défaut (False) ils restent STRICTEMENT uniformes (non-régression ciblée)."""
    R, C = 6, 8
    uni = init_eco("t_uni", R, C, soil_type="terre")            # défaut False
    het = init_eco("t_het", R, C, soil_type="terre", heterogene=True)
    for nom in ("ph", "n", "p", "k", "structure_sol"):
        vu = _valeurs(getattr(uni, nom), R, C)
        vh = _valeurs(getattr(het, nom), R, C)
        check(f"uniforme ({nom})", _variance(vu) < 1e-12,
              "défaut heterogene=False → champ plat")
        check(f"hétérogène ({nom})", _variance(vh) > 1e-9,
              f"var={_variance(vh):.2e}")


def test_catena_decorrelation():
    """Deux champs à canaux de hash ≠ ne sont PAS identiques plot-à-plot (pas de
    corrélation « plot riche partout »). On compare la MODULATION (facteur relatif
    au plancher), car n/p/k ont des planchers hérités différents."""
    R, C = 6, 8
    het = init_eco("t_dec", R, C, soil_type="terre", heterogene=True)
    fn = [het.n.at_plot(r, c) / het.n.at_plot(0, 0)
          for r in range(R) for c in range(C)]
    fk = [het.k.at_plot(r, c) / het.k.at_plot(0, 0)
          for r in range(R) for c in range(C)]
    check("décorrélation n≠k", fn != fk, "canaux _n et _k distincts")


def test_catena_determinisme():
    """Même tile_id → même motif de catena (philo #3, aucun RNG)."""
    R, C = 6, 8
    a = init_eco("t_det", R, C, soil_type="terre", heterogene=True)
    b = init_eco("t_det", R, C, soil_type="terre", heterogene=True)
    check("catena déterministe",
          _valeurs(a.n, R, C) == _valeurs(b.n, R, C),
          "motif reproductible à tile_id fixe")


def main():
    print("=== DIVERSITÉ FONDATRICE ① — génétique ===")
    test_determinisme()
    test_diversite_inter_position()
    test_variance_bornee()
    test_pool_ensemence()
    print("=== DIVERSITÉ FONDATRICE ② — champs (catena) ===")
    test_catena_hetero_vs_uniforme()
    test_catena_decorrelation()
    test_catena_determinisme()
    ok = sum(1 for _, c in _results if c)
    print("=" * 60)
    print(f"RÉSULTAT : {ok}/{len(_results)} vérifications passées")
    print("=" * 60)
    return 0 if ok == len(_results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
