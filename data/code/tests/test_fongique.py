"""
SYMBIOSE — tests/test_fongique.py
Règne fongique (sprint « le sol qui respire » ③, D111 §3.1-3.2) : registre
data-driven des 13 espèces, niche du plot → espèce candidate, sosies qui partagent
leurs niches, parasites seulement sur hôte affaibli, fructification après la pluie,
déterminisme. Perception pure → hors golden.

Usage (depuis data/code/) :
  python3 -m tests.test_fongique
"""
import sys
from types import SimpleNamespace

from fields import init_eco, sample_carpophores
from fields.fongique import (REGISTRE_FONGIQUE, BOIS, HUMUS, RACINES, en_saison,
                             especes_de_saison, candidates_du_plot, choisir_espece)
from fields.ecofields.litiere import Parcelle
from sim.champignon_role import racines_par_plot

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  {'OK ' if cond else 'XX '} {name}" + (f" — {detail}" if detail else ""))


SEED = 0x5AB1057E
TAGS = {"comestible", "veneneux", "mortel", "psychedelique", "immangeable"}

# --- A. Registre : 13 espèces, données complètes -----------------------------
R = REGISTRE_FONGIQUE
check("13 espèces au registre", len(R) == 13, str(len(R)))
check("chaque espèce : substrats ⊂ {bois, humus, racines}, fenêtre, comestibilité",
      all(e.substrats and set(e.substrats) <= {BOIS, HUMUS, RACINES} and e.fenetres
          and e.comestibilite and set(e.comestibilite) <= TAGS for e in R.values()))
check("niche RACINES ⇒ au moins un hôte déclaré",
      all(e.hotes for e in R.values() if RACINES in e.substrats))
check("tue-mouches psychédélique ET toxique",
      set(R["amanite_tue_mouches"].comestibilite) == {"psychedelique", "veneneux"})
check("parasites = armillaire + polypore",
      {k for k, e in R.items() if e.parasite} == {"armillaire", "polypore_bouleau"})
check("morille seule au printemps (sem. 5-13), jamais ailleurs",
      {k for w in range(5, 14) for k in especes_de_saison(w)} == {"morille"}
      and all(not en_saison(R["morille"], w) for w in range(14, 53)),
      str(sorted({k for w in range(5, 14) for k in especes_de_saison(w)})))
check("collybie seule au cœur de l'hiver (sem. 44-52 et 1-4)",
      all(especes_de_saison(w) == ("collybie",) for w in list(range(44, 53)) + [1, 2, 3, 4]))

# --- B. Sosies : niches réellement partagées ---------------------------------
def _meme_niche(a, b):
    return set(R[a].substrats) & set(R[b].substrats) and (
        BOIS in R[a].substrats and BOIS in R[b].substrats
        or set(R[a].hotes) & set(R[b].hotes))
check("sosie hypholome / armillaire / collybie / pleurote : même bois",
      all(BOIS in R[k].substrats for k in ("hypholome", "armillaire", "collybie", "pleurote")))
check("sosie clitocybe / rosé : mêmes graminées", _meme_niche("clitocybe", "rose_des_pres"))
check("sosie phalloïde / cèpe : même Fagacée", _meme_niche("amanite_phalloide", "cepe"))

# --- C. Niche du plot → candidates --------------------------------------------
eco = init_eco("fongique", 3, 3)
eco.litiere[0][0].append(Parcelle("bois", 1.0))      # bois mort au plot (0,0)
eco.om_active.set(1, 1, 2.0)                          # humus riche au plot (1,1)
saison_aut = especes_de_saison(34)
cand_bois = candidates_du_plot(eco, 0, 0, set(), saison_aut)
check("plot BOIS, automne : pleurote + hypholome + armillaire (sosies ensemble)",
      set(cand_bois) == {"pleurote", "hypholome", "armillaire"}, str(cand_bois))
check("plot BOIS, plein hiver : collybie seule",
      candidates_du_plot(eco, 0, 0, set(), especes_de_saison(48)) == ["collybie"])
check("plot HUMUS riche : coprin",
      candidates_du_plot(eco, 1, 1, set(), saison_aut) == ["coprin"])
check("plot nu sans racines : aucune espèce",
      candidates_du_plot(eco, 2, 2, set(), saison_aut) == [])
check("racines de Poaceae : rosé + clitocybe + psilocybe",
      set(candidates_du_plot(eco, 2, 2, {"Poaceae", "Pâturin"}, saison_aut))
      == {"rose_des_pres", "clitocybe", "psilocybe"})
check("racines de chêne (Fagaceae) en été : cèpe + phalloïde",
      set(candidates_du_plot(eco, 2, 2, {"Fagaceae", "Chêne"}, especes_de_saison(22)))
      == {"cepe", "amanite_phalloide"})
check("bouleau SAIN : tue-mouches, pas de polypore",
      candidates_du_plot(eco, 2, 2, {"Betulaceae", "Bouleau"}, saison_aut)
      == ["amanite_tue_mouches"])
check("bouleau AFFAIBLI : + polypore (parasite de faiblesse)",
      set(candidates_du_plot(eco, 2, 2, {"Betulaceae", "Bouleau", "!Betulaceae", "!Bouleau"},
                             saison_aut)) == {"amanite_tue_mouches", "polypore_bouleau"})
check("pommier au printemps : morille",
      candidates_du_plot(eco, 2, 2, {"Rosaceae", "Pommier"}, especes_de_saison(8)) == ["morille"])
tas = frozenset({(2, 2)})
check("tas de compost posé au plot : coprin",
      candidates_du_plot(eco, 2, 2, set(), saison_aut, tas) == ["coprin"])

# --- D. Choix déterministe -----------------------------------------------------
check("choix d'espèce déterministe et ∈ candidates",
      choisir_espece(cand_bois, SEED, 0, 0) == choisir_espece(cand_bois, SEED, 0, 0)
      and choisir_espece(cand_bois, SEED, 0, 0) in cand_bois)
check("aucune candidate → None", choisir_espece([], SEED, 0, 0) is None)
choix = {choisir_espece(["clitocybe", "rose_des_pres"], SEED, r, c)
         for r in range(20) for c in range(20)}
check("sosies : les deux espèces sortent sur une prairie (hash spatial)",
      choix == {"clitocybe", "rose_des_pres"}, str(choix))

# --- E. Racines par plot (pont) -------------------------------------------------
def _pl(family, name, plots, vit=1.0):
    cls = SimpleNamespace(family=family, name=name)
    return SimpleNamespace(plant_class=cls, root_plots=plots, is_alive=vit > 0,
                           etat="sain" if vit > 0.6 else "affaibli")
rp = racines_par_plot([_pl("Fagaceae", "Chêne", [(0, 0)]),
                       _pl("Betulaceae", "Bouleau", [(0, 0), (1, 0)], vit=0.3),
                       _pl("Poaceae", "Pâturin", [(2, 2)], vit=0.0)])
check("racines_par_plot : familles + noms, `!` pour l'affaibli, morts ignorés",
      rp == {(0, 0): {"Fagaceae", "Chêne", "Betulaceae", "Bouleau", "!Betulaceae", "!Bouleau"},
             (1, 0): {"Betulaceae", "Bouleau", "!Betulaceae", "!Bouleau"}}, str(rp))

# --- F. Fructification : pluie + mycélium + humidité + niche -------------------
e = init_eco("carpo", 3, 3, humidite=2.5)
e.mycelium.fill(0.8)
e.litiere[0][0].append(Parcelle("bois", 1.0))
k_pluie = sample_carpophores(e, SEED, 34, True, {(2, 2): {"Poaceae"}})
check("après pluie : carpophores SEULEMENT sur les plots à niche",
      {(k.row, k.col) for k in k_pluie} == {(0, 0), (2, 2)},
      str({(k.row, k.col, k.espece) for k in k_pluie}))
check("espèce du bois ∈ {pleurote, hypholome, armillaire}",
      all(k.espece in cand_bois for k in k_pluie if (k.row, k.col) == (0, 0)))
check("sans pluie la semaine d'avant : rien", sample_carpophores(e, SEED, 34, False) == [])
check("déterministe (deux appels identiques)",
      sample_carpophores(e, SEED, 34, True, {(2, 2): {"Poaceae"}}) == k_pluie)

fails = [n for n, ok in _results if not ok]
if fails:
    print(f"\n[test_fongique] FAIL — {len(fails)}/{len(_results)} rouges : {fails}")
    sys.exit(1)
print(f"\n[test_fongique] PASS — {len(_results)}/{len(_results)} OK")
