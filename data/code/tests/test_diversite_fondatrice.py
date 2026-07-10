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

SEED = 0x5AB1057E
_results = []


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


def main():
    print("=== DIVERSITÉ FONDATRICE ① — génétique ===")
    test_determinisme()
    test_diversite_inter_position()
    test_variance_bornee()
    test_pool_ensemence()
    ok = sum(1 for _, c in _results if c)
    print("=" * 60)
    print(f"RÉSULTAT : {ok}/{len(_results)} vérifications passées")
    print("=" * 60)
    return 0 if ok == len(_results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
