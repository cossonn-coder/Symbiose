"""
SYMBIOSE — tests/test_peripherie.py
Tests ciblés de la CEINTURE (sprint PÉRIPHÉRIE, tronçon ①, D73).
Spec : `docs/champs/peripherie/conception_peripherie.md` §4.1 + kickoff
`sprints/champs/peripherie/sprint_peripherie/01_ceinture.md`.

Vérifie que `fields/peripherie.py` est :
  A. DÉTERMINISTE  — même seed → même ceinture ; seeds différents → profils
                     différents (philo #3 et #7) ;
  B. D92 REFERMÉE  — LE test qui compte. Sur 300 000 seeds (pas de simulation,
                     juste du hash) : < 15 % de terrains aux 4 côtés identiques
                     (la génération C# était à 96,0 %), ≥ 5 % de terrains portant
                     une falaise (le C# n'en produisait AUCUNE), et chacun des 4
                     types non-falaise présent sur ≥ 10 % des terrains ;
  C. RIPISYLVE     — toute forêt qui touche une rivière porte aulne ou saule ;
  D. BORNÉ         — chaque scalaire dans sa plage, densité ∈ [0,1], et les champs
                     hors-type restent à leur valeur neutre.

Ce tronçon ne branche rien : aucun module de la boucle n'importe `peripherie`, donc
le golden est neutre par construction (rien à vérifier ici, `test_golden` s'en charge).

Usage (depuis data/code/) :
  python3 -m tests.test_peripherie
"""
import sys

from fields.peripherie import (
    generer_ceinture, voisins, COTES, TYPES,
    ESSENCES_RIPISYLVE, HAUTEUR_FORET_CM, DENSITE_FORET, DENSITE_FRICHE,
    LIGNE_EAU_CM, ALTITUDE_FALAISE_CM,
)

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    flag = "✅" if cond else "❌"
    print(f"  {flag} {name}" + (f" — {detail}" if detail else ""))


# Échantillon du test D92 : même taille que la mesure de référence du C#.
N_SEEDS = 300_000


# --- A. Déterminisme -------------------------------------------------------
def test_determinisme():
    print("\n[A] Déterminisme")
    for seed in (42, 7, 12345, 999_983):
        a = generer_ceinture(seed)
        b = generer_ceinture(seed)
        check(f"ceinture reproductible seed={seed}", a == b,
              " · ".join(f"{s['type']}" for s in a))
    # Deux seeds distincts doivent donner des terrains distincts (#7). On échantillonne
    # largement : le nombre de profils distincts doit être élevé, pas juste ≥ 2.
    profils = {tuple((s["type"], s["essence"]) for s in generer_ceinture(k))
               for k in range(2000)}
    check("seeds différents → profils variés", len(profils) >= 50,
          f"{len(profils)} profils distincts sur 2000 seeds")
    check("ceinture = 4 secteurs indexés N/E/S/O",
          [s["cote"] for s in generer_ceinture(1)] == list(COTES))


# --- B. D92 refermée -------------------------------------------------------
def test_d92():
    print(f"\n[B] D92 refermée — balayage de {N_SEEDS:,} seeds")
    uniformes = 0
    avec_falaise = 0
    presence = {t: 0 for t in TYPES}
    for seed in range(N_SEEDS):
        types = [s["type"] for s in generer_ceinture(seed)]
        if len(set(types)) == 1:
            uniformes += 1
        if "falaise" in types:
            avec_falaise += 1
        for t in set(types):
            presence[t] += 1

    part_unif = uniformes / N_SEEDS
    part_falaise = avec_falaise / N_SEEDS
    check("terrains aux 4 côtés identiques < 15 % (C# : 96,0 %)",
          part_unif < 0.15, f"{part_unif:.1%} ({uniformes:,})")
    check("terrains portant une falaise ≥ 5 % (C# : 0 %)",
          part_falaise >= 0.05, f"{part_falaise:.1%} ({avec_falaise:,})")
    for t in ("foret", "riviere", "prairie", "friche"):
        part = presence[t] / N_SEEDS
        check(f"type '{t}' présent sur ≥ 10 % des terrains",
              part >= 0.10, f"{part:.1%}")


# --- C. Ripisylve ----------------------------------------------------------
def test_ripisylve():
    print("\n[C] Ripisylve — une forêt de berge est un aulne ou un saule")
    n_ripi = n_seche = 0
    ok_ripi = ok_seche = True
    for seed in range(20_000):
        ceinture = generer_ceinture(seed)
        types = [s["type"] for s in ceinture]
        for s in ceinture:
            if s["type"] != "foret":
                # Hors forêt : aucune essence dominante (la ceinture est un agrégat,
                # une friche n'a pas de dominante — cf. tronçon ③).
                ok_seche = ok_seche and s["essence"] is None
                continue
            bord_de_leau = any(types[v] == "riviere" for v in voisins(s["cote"]))
            if bord_de_leau:
                n_ripi += 1
                ok_ripi = ok_ripi and s["essence"] in ESSENCES_RIPISYLVE
            else:
                n_seche += 1
                ok_seche = ok_seche and s["essence"] not in ("saule",)
    check("toute forêt adjacente à une rivière est aulne/saule", ok_ripi,
          f"{n_ripi:,} secteurs de ripisylve testés")
    check("hors berge : jamais de saule, jamais d'essence sur un non-boisé",
          ok_seche, f"{n_seche:,} forêts sèches testées")
    check("les deux cas existent dans l'échantillon", n_ripi > 0 and n_seche > 0)


# --- D. Bornes -------------------------------------------------------------
def _dans(v, plage):
    return plage[0] - 1e-6 <= v <= plage[1] + 1e-6


def test_bornes():
    print("\n[D] Bornes des scalaires")
    fails = []
    for seed in range(20_000):
        for s in generer_ceinture(seed):
            typ = s["type"]
            if not 0.0 <= s["densite_ligneuse"] <= 1.0:
                fails.append(("densite hors [0,1]", seed, s))
            if typ == "foret":
                if not (_dans(s["hauteur_canopee"], HAUTEUR_FORET_CM)
                        and _dans(s["densite_ligneuse"], DENSITE_FORET)):
                    fails.append(("foret", seed, s))
            elif typ == "friche":
                if not _dans(s["densite_ligneuse"], DENSITE_FRICHE):
                    fails.append(("friche", seed, s))
            elif typ == "riviere":
                if not _dans(s["ligne_eau"], LIGNE_EAU_CM):
                    fails.append(("riviere", seed, s))
            elif typ == "falaise":
                if not _dans(s["altitude_relative"], ALTITUDE_FALAISE_CM):
                    fails.append(("falaise", seed, s))
            # Champs hors-type : restent à leur valeur neutre.
            if typ != "foret" and s["hauteur_canopee"] != 0.0:
                fails.append(("hauteur parasite", seed, s))
            if typ not in ("foret", "friche") and s["densite_ligneuse"] != 0.0:
                fails.append(("densite parasite", seed, s))
            if typ != "riviere" and s["ligne_eau"] != 0.0:
                fails.append(("ligne_eau parasite", seed, s))
            if typ != "falaise" and s["altitude_relative"] != 0.0:
                fails.append(("altitude parasite", seed, s))
            if s["souche_memory"] is not None or s["annees_depuis_coupe"] != 0.0:
                fails.append(("cinetique non vierge", seed, s))
    check("tous les scalaires dans leurs plages, aucun champ parasite",
          not fails, fails[0] if fails else "20 000 seeds × 4 secteurs")


def main():
    test_determinisme()
    test_ripisylve()
    test_bornes()
    test_d92()
    n_ok = sum(1 for _, ok in _results if ok)
    n = len(_results)
    print(f"\n[test_peripherie] {n_ok}/{n} OK")
    if n_ok != n:
        print("ÉCHECS : " + ", ".join(name for name, ok in _results if not ok))
        sys.exit(1)
    print("[test_peripherie] PASS")


if __name__ == "__main__":
    main()
