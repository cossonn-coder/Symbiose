"""
SYMBIOSE — tests/test_inoculum.py
Tests ciblés du champ MÉMOIRE D'INOCULUM du sol (sprint mémoire d'inoculum ①).
Exercent `EcoFields.inoculum` (`InoculumField` : `deposit`, `at`, `total`,
`tick_decay`) sur des champs forcés, hors golden.

Couvre :
  (a) DÉPÔT : `deposit` monte le bucket de la BONNE famille (spécificité D3) ;
              une autre famille du même plot reste à 0.
  (b) DÉCROISSANCE : `tick_decay` fait BAISSER la charge ; un microbiome plein
              ACCÉLÈRE la baisse (sol suppressif) vs un sol mort.
  (c) PURGE : un bucket retombé sous INOC_EPSILON est SUPPRIMÉ (sparse).
  (d) REPOS : un plot jamais infecté reste à 0 pour TOUTE famille (`at`/`total`),
              et `tick_decay` sur un champ vide est un no-op (golden neutre).
  Plus : test_golden INCHANGÉ (assert du hash de référence).

Usage (depuis data/code/) : python3 -m tests.test_inoculum
"""
import sys

from fields import EcoFields
from fields.ecofields.constants import (INOC_MAX, INOC_EPSILON, INOC_DECAY,
                                        INOC_MICRO_SUPPRESS, MICROBE_EFFECT_REF)

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "OK " if cond else "XX "
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _eco(rows=2, cols=2):
    """EcoFields nu (construction directe : inoculum VIDE, microbiome à 0)."""
    return EcoFields(tile_id="I0", rows=rows, cols=cols)


# ---------------------------------------------------------------------------
# (a) dépôt spécifique à la famille
# ---------------------------------------------------------------------------
def test_depot_par_famille():
    print("\n[a] dépôt : la charge monte dans le bucket de la BONNE famille")
    eco = _eco()
    eco.inoculum.deposit(0, 0, "Solanaceae", 0.4)
    eco.inoculum.deposit(0, 0, "Solanaceae", 0.3)   # cumul dans la même famille
    check("bucket Solanaceae cumule les dépôts",
          abs(eco.inoculum.at(0, 0, "Solanaceae") - 0.7) < 1e-9,
          f"at={eco.inoculum.at(0, 0, 'Solanaceae'):.3f}")
    check("autre famille du même plot reste à 0 (spécificité D3)",
          eco.inoculum.at(0, 0, "Fabaceae") == 0.0)
    check("total du plot = somme des familles",
          abs(eco.inoculum.total(0, 0) - 0.7) < 1e-9,
          f"total={eco.inoculum.total(0, 0):.3f}")
    # Borne haute INOC_MAX
    eco.inoculum.deposit(0, 0, "Solanaceae", 5.0)
    check("dépôt borné par INOC_MAX",
          eco.inoculum.at(0, 0, "Solanaceae") == INOC_MAX,
          f"at={eco.inoculum.at(0, 0, 'Solanaceae'):.3f}, max={INOC_MAX}")
    # deposit(q<=0) est un no-op (n'ouvre pas de bucket)
    eco.inoculum.deposit(1, 1, "Rosaceae", 0.0)
    check("deposit(q=0) n'ouvre pas de bucket (sparse)",
          (1, 1) not in eco.inoculum.load)


# ---------------------------------------------------------------------------
# (b) décroissance + accélération par le microbiome
# ---------------------------------------------------------------------------
def test_decroissance_microbiome():
    print("\n[b] décroissance : baisse au tick, ACCÉLÉRÉE par un microbiome plein")
    # Sol MORT (microbiome 0) : décroissance passive pure.
    eco_mort = _eco()
    eco_mort.microbiome.fill(0.0)
    eco_mort.inoculum.deposit(0, 0, "Solanaceae", 0.8)
    eco_mort.inoculum.tick_decay(eco_mort)
    apres_mort = eco_mort.inoculum.at(0, 0, "Solanaceae")
    attendu_passif = 0.8 * INOC_DECAY
    check("sol mort : décroissance passive pure (× INOC_DECAY)",
          abs(apres_mort - attendu_passif) < 1e-9,
          f"après={apres_mort:.4f}, attendu={attendu_passif:.4f}")

    # Sol VIVANT (microbiome plein) : suppression additive en plus.
    eco_vivant = _eco()
    eco_vivant.microbiome.fill(MICROBE_EFFECT_REF)   # micro_norm = 1
    eco_vivant.inoculum.deposit(0, 0, "Solanaceae", 0.8)
    eco_vivant.inoculum.tick_decay(eco_vivant)
    apres_vivant = eco_vivant.inoculum.at(0, 0, "Solanaceae")
    check("sol vivant : baisse PLUS que le sol mort (suppression microbienne)",
          apres_vivant < apres_mort,
          f"vivant={apres_vivant:.4f} < mort={apres_mort:.4f}")
    attendu_vivant = 0.8 * INOC_DECAY - INOC_MICRO_SUPPRESS
    check("sol vivant : × INOC_DECAY − INOC_MICRO_SUPPRESS",
          abs(apres_vivant - attendu_vivant) < 1e-9,
          f"après={apres_vivant:.4f}, attendu={attendu_vivant:.4f}")


# ---------------------------------------------------------------------------
# (c) purge sous EPSILON (sparse)
# ---------------------------------------------------------------------------
def test_purge_epsilon():
    print("\n[c] purge : un bucket sous INOC_EPSILON est SUPPRIMÉ (sparse)")
    eco = _eco()
    eco.microbiome.fill(0.0)
    # Charge minuscule qui retombe sous EPSILON en un tick.
    petite = INOC_EPSILON * 0.5
    eco.inoculum.deposit(0, 0, "Solanaceae", petite)
    check("bucket présent avant décroissance", (0, 0) in eco.inoculum.load)
    eco.inoculum.tick_decay(eco)
    check("bucket purgé après (charge < EPSILON)",
          eco.inoculum.at(0, 0, "Solanaceae") == 0.0
          and (0, 0) not in eco.inoculum.load,
          f"load={dict(eco.inoculum.load)}")


# ---------------------------------------------------------------------------
# (d) repos neutre : plot jamais infecté
# ---------------------------------------------------------------------------
def test_repos_neutre():
    print("\n[d] repos : un plot jamais infecté reste à 0, tick_decay no-op")
    eco = _eco()
    check("at() = 0 pour toute famille sur un plot vierge",
          eco.inoculum.at(1, 1, "Solanaceae") == 0.0
          and eco.inoculum.at(1, 1, "Rosaceae") == 0.0)
    check("total() = 0 sur un plot vierge", eco.inoculum.total(1, 1) == 0.0)
    check("champ VIDE au repos (aucune entrée)", len(eco.inoculum.load) == 0)
    eco.inoculum.tick_decay(eco)   # no-op sur un champ vide
    check("tick_decay sur champ vide reste vide (golden-safe)",
          len(eco.inoculum.load) == 0)


# ---------------------------------------------------------------------------
# Golden inchangé (le champ est DORMANT au ① : personne ne le lit)
# ---------------------------------------------------------------------------
def test_golden_intact():
    print("\n[golden] le smoke test golden reste INCHANGÉ (inoculum dormant)")
    import os
    from tests.test_golden import compute_hash
    hash_now = compute_hash()
    ref_path = os.path.join(os.path.dirname(__file__), "golden_hash.txt")
    with open(ref_path) as f:
        ref = f.read().strip()
    check("hash golden identique à golden_hash.txt", hash_now == ref,
          f"now={hash_now[:16]}… ref={ref[:16]}…")


if __name__ == "__main__":
    print("=" * 64)
    print("SYMBIOSE — tests mémoire d'inoculum (champ dormant ①)")
    print("=" * 64)
    test_depot_par_famille()
    test_decroissance_microbiome()
    test_purge_epsilon()
    test_repos_neutre()
    test_golden_intact()
    print("\n" + "=" * 64)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print(f"RÉSULTAT : {passed}/{total} vérifications passées")
    print("=" * 64)
    sys.exit(0 if passed == total else 1)
