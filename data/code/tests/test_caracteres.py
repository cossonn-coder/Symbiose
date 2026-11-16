"""
SYMBIOSE — tests/test_caracteres.py
Registre des caractères génétiques (D139, sprint génétique infinitésimale ①).

Vérifie :
  1. Chaque nom de GENE_NAMES a une entrée au registre, et l'ORDRE est stable
     (canaux de hash positionnels : un réordonnancement casserait tous les tirages).
  2. Tronçon ① = refactor pur : tous les caractères sont des « facteur », neutre
     1.0, σ_A 0.10, bornes [GENE_HARD_MIN, GENE_HARD_MAX] ; `adaptogene` recopie
     ADAPTOGENIC_GENES.
  3. `plant.gene(nom)` d'un gène ABSENT du vecteur = neutre du caractère pour
     l'espèce (et une valeur présente est rendue telle quelle).
  4. Une surcharge d'espèce (`PlantBase.genetique`) est lue par
     `parametres_espece` et par `gene()` — sans fuir sur les autres espèces.
  5. `borne(nom, x)` == `clamp_gene(x)` pour un caractère facteur.
"""
from __future__ import annotations

from plants import (Tomato, Carrot, PlantInstance, GENE_NAMES, GENE_HARD_MIN,
                    GENE_HARD_MAX, GENE_INIT_SIGMA, ADAPTOGENIC_GENES,
                    CARACTERES, parametres_espece, neutre, sigma_a, borne,
                    clamp_gene)

_results = []

# Ordre historique figé (golden) — NE PAS modifier, seulement AJOUTER en queue.
_ORDRE_HISTORIQUE = ("hauteur", "rusticite_froid", "vigueur",
                     "resistance_pathogene", "tolerance_secheresse",
                     "tolerance_ombre", "tolerance_asphyxie", "port_trapu",
                     "germination_thermique", "phenologie_florale")


# D139 ③ : (unité, neutre, σ_A, bornes) des caractères passés en vraies unités.
_VRAIES_UNITES = {
    "germination_thermique": ("°C", 0.0, 1.5, (-6.0, 6.0)),
    "phenologie_florale":    ("semaines", 0.0, 1.0, (-4.0, 4.0)),
}


def check(name, cond, detail=""):
    _results.append((name, bool(cond)))
    print(f"  [{'OK' if cond else 'KO'}] {name}" + (f" — {detail}" if detail and not cond else ""))


def test_registre_complet_et_ordonne():
    check("chaque gène a une entrée", all(g in CARACTERES for g in GENE_NAMES))
    check("GENE_NAMES dérivé du registre", tuple(CARACTERES) == GENE_NAMES)
    check("ordre historique préservé en tête",
          GENE_NAMES[:len(_ORDRE_HISTORIQUE)] == _ORDRE_HISTORIQUE, str(GENE_NAMES))


def test_valeurs_refactor_pur():
    for g, car in CARACTERES.items():
        if g == "autofecondation":       # ajouté en queue au D139 ② (probabilité)
            ok = (car.unite == "probabilité" and car.bornes == (0.0, 1.0)
                  and car.sigma_a == 0.05 and not car.adaptogene)
            check(f"caractère neuf : {g}", ok, repr(car))
            continue
        if g in _VRAIES_UNITES:          # D139 ③ : vraies unités (neutre 0)
            ok = (car.unite, car.neutre, car.sigma_a, car.bornes) == _VRAIES_UNITES[g] \
                and not car.adaptogene
            check(f"vraie unité : {g}", ok, repr(car))
            continue
        ok = (car.unite == "facteur" and car.neutre == 1.0
              and car.sigma_a == GENE_INIT_SIGMA == 0.10
              and car.bornes == (GENE_HARD_MIN, GENE_HARD_MAX)
              and car.adaptogene == (g in ADAPTOGENIC_GENES))
        check(f"valeurs inchangées : {g}", ok, repr(car))


def test_gene_absent_vaut_neutre():
    p = PlantInstance(plant_class=Tomato, position=(0, 0))
    p.genes = {"hauteur": 1.2}
    check("gène présent rendu tel quel", p.gene("hauteur") == 1.2)
    check("gène absent = neutre", p.gene("vigueur") == neutre("vigueur", Tomato) == 1.0)


def test_surcharge_espece():
    class TomateTest(Tomato):
        genetique = {"vigueur": {"neutre": 0.8, "sigma_a": 0.3},
                     "hauteur": {"sigma_a": 0.05}}
    check("neutre surchargé", neutre("vigueur", TomateTest) == 0.8)
    check("σ_A surchargé", sigma_a("vigueur", TomateTest) == 0.3)
    check("surcharge partielle : champ absent = table",
          parametres_espece(TomateTest, "hauteur") == (1.0, 0.05))
    check("caractère non surchargé = table",
          parametres_espece(TomateTest, "port_trapu") == (1.0, 0.10))
    check("pas de fuite sur la classe mère", neutre("vigueur", Tomato) == 1.0)
    check("pas de fuite sur une autre espèce", neutre("vigueur", Carrot) == 1.0)
    p = PlantInstance(plant_class=TomateTest, position=(0, 0))
    check("gene() lit la surcharge d'espèce", p.gene("vigueur") == 0.8)


def test_borne_identique_clamp():
    for x in (-1.0, 0.0, 0.39, 0.4, 1.0, 1.6, 1.61, 5.0):
        check(f"borne(x={x}) == clamp_gene", borne("hauteur", x) == clamp_gene(x))


def run():
    test_registre_complet_et_ordonne()
    test_valeurs_refactor_pur()
    test_gene_absent_vaut_neutre()
    test_surcharge_espece()
    test_borne_identique_clamp()
    total = len(_results)
    ok = sum(1 for _, c in _results if c)
    print(f"\n=== CARACTÈRES : {ok}/{total} ===")
    return ok == total


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
