"""
SYMBIOSE — test_heredite.py
Hérédité INFINITÉSIMALE (D139 ②, sprint génétique infinitésimale, tronçon ②).

Vérifications, toutes DÉTERMINISTES (hash, aucun RNG live) :
  1. Autofécondation répétée : F → 1 et la variance entre frères s'effondre.
  2. Croisement → F = 0.
  3. Brassage : sur 2000 enfants croisés de parents non consanguins, l'écart-type
     vaut √(½σ_A² + H_MUT·σ_A²) (tolérance statistique).
  4. Déterminisme : deux appels identiques → mêmes gènes, même F.
  5. Une `Seed` sauvée sans F (save d'avant ②) se relit avec F = 0.
  6. Autogame : avec un père à portée, une tomate s'autoféconde ≈ 95 % du temps.
  7. Variété : graines autogames serrées (F 0,9), allogames dispersées (F 0).
  8. Dépression de consanguinité : allogame consanguine freinée, autogame ≈ 1.
  9. Banque-sol : F moyen agrégé par espèce × plot, relu par `sample_F`.

Usage (depuis data/code/) : python3 -m tests.test_heredite
"""
import math
import statistics

from plants import (PlantInstance, Tomato, Basil, Nettle, GENE_NAMES, H_MUT, DI,
                    sigma_a, neutre)
from fields import SeedBank, variete_genes
from sim.reproduction import heredite
from sim.seeds import Seed, PlayerSeedBank

SEED = 0xD139
_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


def _plante(cls, pos=(0, 0), genes=None, F=0.0):
    p = PlantInstance(cls, pos, current_stage=3,
                      genes=dict(genes) if genes else {g: neutre(g, cls) for g in GENE_NAMES})
    p.F = F
    return p


def test_autofecondation_fixe():
    print("\n[1] autofécondation répétée → F → 1, frères identiques")
    p = _plante(Basil)
    for gen in range(12):
        genes, F = heredite(p, None, SEED, gen + 1)
        p = _plante(Basil, genes=genes, F=F)
    check("F tend vers 1", p.F > 0.999, f"F={p.F:.5f}")
    # Variance entre frères (même mère, semaines différentes = graines différentes)
    def ecart_freres(mere):
        h = [heredite(mere, None, SEED, 1000 + k)[0]["hauteur"] for k in range(400)]
        return statistics.pstdev(h)
    sd_fixe = ecart_freres(p)
    sd_libre = ecart_freres(_plante(Basil))
    s_a = sigma_a("hauteur", Basil)
    check("variance entre frères effondrée (≈ filet seul)",
          sd_fixe < 0.25 * sd_libre and abs(sd_fixe - math.sqrt(H_MUT) * s_a) < 0.004,
          f"σ fixe={sd_fixe:.4f} σ libre={sd_libre:.4f} filet={math.sqrt(H_MUT) * s_a:.4f}")


def test_croisement_F0():
    print("\n[2] croisement → F = 0")
    mere, pere = _plante(Basil, F=0.75), _plante(Basil, (0, 1), F=0.5)
    # Basilic allogame (0,15) : on cherche une semaine où le hash choisit le croisement
    Fs = [heredite(mere, pere, SEED, w)[1] for w in range(1, 60)]
    check("au moins un croisement → F = 0", 0.0 in Fs)
    check("autofécondé → F = (1+F_m)/2", all(f in (0.0, 0.875) for f in Fs),
          f"valeurs={sorted(set(Fs))}")


def test_brassage_sigma():
    print("\n[3] brassage : σ attendu sur 2000 enfants croisés")
    s_a = sigma_a("hauteur", Basil)
    attendu = math.sqrt(0.5 * s_a ** 2 + H_MUT * s_a ** 2)
    vals = []
    for k in range(2000):
        pos = (k // 50, k % 50)
        mere, pere = _plante(Basil, pos), _plante(Basil, (pos[0], pos[1] + 1))
        mere.genes["autofecondation"] = 0.0          # croisement forcé
        genes, F = heredite(mere, pere, SEED, 7)
        vals.append(genes["hauteur"])
    sd, moy = statistics.pstdev(vals), statistics.fmean(vals)
    check("écart-type ≈ √(½σ_A² + H_MUT·σ_A²)", abs(sd - attendu) / attendu < 0.06,
          f"σ={sd:.4f} attendu={attendu:.4f}")
    check("moyenne centrée sur la moyenne parentale", abs(moy - 1.0) < 0.006,
          f"moy={moy:.4f}")


def test_determinisme():
    print("\n[4] déterminisme")
    mere, pere = _plante(Basil, (2, 3)), _plante(Basil, (2, 4))
    a = heredite(mere, pere, SEED, 11)
    b = heredite(mere, pere, SEED, 11)
    check("deux appels identiques", a == b)


def test_seed_sans_F():
    print("\n[5] Seed sans F (save d'avant ②) → F = 0")
    bank = PlayerSeedBank.from_dict({"tomate": [{"species": "tomate",
                                                 "genes": {"hauteur": 1.1}}]})
    check("relue avec F = 0", bank.take("tomate").F == 0.0)
    bank2 = PlayerSeedBank()
    bank2.add(Seed("tomate", {"hauteur": 1.1}, {}, 0.94))
    relue = PlayerSeedBank.from_json(bank2.to_json()).take("tomate")
    check("F aller-retour JSON", relue.F == 0.94)
    check("F nul omis du JSON (save lisible)",
          '"F"' not in PlayerSeedBank.from_dict({"tomate": [{"species": "tomate",
                                                             "genes": {}}]}).to_json())


def test_autogame_avec_pere():
    print("\n[6] tomate autogame : s'autoféconde malgré un père à portée")
    n_auto = 0
    for w in range(1, 401):
        mere, pere = _plante(Tomato, (w % 7, w % 5)), _plante(Tomato, (0, 9))
        n_auto += heredite(mere, pere, SEED, w)[1] > 0.0
    taux = n_auto / 400
    check("taux d'autofécondation ≈ 0,95", abs(taux - 0.95) < 0.04, f"taux={taux:.3f}")


def test_variete():
    print("\n[7] variété : autogame serrée, allogame dispersée")
    def lot(cls):
        res = [variete_genes(cls, SEED, 0, r, c, c * 50.0 + 13, r * 50.0 + 7)
               for r in range(6) for c in range(8)]
        return [g["hauteur"] for g, _ in res], {F for _, F in res}
    h_tom, F_tom = lot(Tomato)
    h_bas, F_bas = lot(Basil)
    check("tomate : F = 0,9", F_tom == {0.9}, f"{F_tom}")
    check("basilic : F = 0", F_bas == {0.0}, f"{F_bas}")
    sd_t, sd_b = statistics.pstdev(h_tom), statistics.pstdev(h_bas)
    check("dispersion tomate ≈ √0,1 × celle du basilic",
          sd_t < 0.5 * sd_b, f"σ tomate={sd_t:.4f} σ basilic={sd_b:.4f}")


def test_depression():
    print("\n[8] dépression de consanguinité")
    ortie = _plante(Nettle, F=1.0)
    s = neutre("autofecondation", Nettle)
    check("ortie F=1 : 1 − DI·(1 − s)",
          abs(ortie.depression_consanguinite() - (1 - DI * (1 - s))) < 1e-12,
          f"{ortie.depression_consanguinite():.4f}")
    check("tomate F=1 : ≈ 1 (purgée)",
          _plante(Tomato, F=1.0).depression_consanguinite() > 0.98)
    check("F = 0 : 1.0", _plante(Nettle).depression_consanguinite() == 1.0)


def test_banque_sol_F():
    print("\n[9] banque-sol : F moyen par espèce × plot")
    sb = SeedBank(3, 3)
    sb.add_species(1, 1, Tomato, 0.5, {"hauteur": 1.0}, None, 1.0)
    sb.add_species(1, 1, Tomato, 0.5, {"hauteur": 1.0}, None, 0.5)
    check("moyenne pondérée", abs(sb.sample_F(1, 1, Tomato) - 0.75) < 1e-12,
          f"{sb.sample_F(1, 1, Tomato)}")
    check("pool vide → 0", sb.sample_F(0, 0, Tomato) == 0.0)


if __name__ == "__main__":
    test_autofecondation_fixe()
    test_croisement_F0()
    test_brassage_sigma()
    test_determinisme()
    test_seed_sans_F()
    test_autogame_avec_pere()
    test_variete()
    test_depression()
    test_banque_sol_F()
    ok = sum(1 for _, c in _results if c)
    print(f"\n=== HÉRÉDITÉ : {ok}/{len(_results)} ===")
    raise SystemExit(0 if ok == len(_results) else 1)
