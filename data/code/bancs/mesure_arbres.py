"""
SYMBIOSE — bancs/mesure_arbres.py
BANC DE MESURE (hors golden, hors registre F5) du sprint AUTOMNE VISIBLE (①,
docs/rendu/ambiance/conception_automne_visible.md) : photographie chiffrée de la
STRUCTURE des 11 arbres de `PERENNIAL_CATALOGUE` à 5, 10, 15 et 25 ans, rejouée à
l'identique avant et après le réglage des ports (②).

Lecture seule : le script ne modifie aucune mécanique, il déroule `pre_croitre`
(la morphogénèse du tick, sans lumière ni concurrence, cf. sim/precroissance.py)
sur des plantes isolées, hors de tout monde. Déterministe : mêmes entrées → même
tableau. Il ne couvre donc NI l'ombre des voisins, NI la sécheresse, NI la taille.

Pédagogie (Nico) : `pre_croitre` numérote toujours ses semaines depuis 1. Faire
pousser 5 ans puis 5 ans de plus ne donne donc pas un arbre de 10 ans : la fenêtre
de cladoptose (hachée sur le n° de semaine) tomberait ailleurs. Chaque âge repart
d'un semis neuf, exactement comme l'init d'un monde. C'est ce qui rend le banc lent
pour un banc (~8 s [n=1, VM]) : 55 années de pousse × 11 espèces, ~70 segments en fin de course.

La plante mesurée est celle de la conception (§1) : plot (3,3) avec son patrimoine
fondateur → le tableau d'origine se reproduit au chiffre près. La hauteur lue
(`height_at`) inclut donc le gène `hauteur` de CE pied (colonne « gène »), le rayon
(`canopy_radius_at`) non. Une autre position donne un autre gène et d'autres branches :
ces chiffres décrivent un pied, pas une moyenne d'espèce.

« Feuillé » = même règle que le rendu (`tools/maquette/organes.py`,
`LeafMaxThickCm` côté C#) : apex ou bois assez fin pour porter des feuilles.

Usage (depuis data/code/) :
  python3 -m bancs.mesure_arbres          # tableau Markdown sur la sortie standard
"""
from __future__ import annotations

from fields import founder_genes
from plants import PlantInstance
from plants.catalogue import PERENNIAL_CATALOGUE
from sim.precroissance import pre_croitre
from tools.maquette.organes import LEAF_MAX_THICK_CM

AGES = (5, 10, 15, 25)
SEED = 42
PLOT = (3, 3)            # plot du tableau de la conception (§1)
ETIQUETTE = "[seed 42, sans lumière, VM]"


def _pied(classe, annees: int) -> PlantInstance:
    """Un pied fondateur de `classe`, poussé `annees` ans depuis le semis."""
    r, c = PLOT
    plante = PlantInstance(plant_class=classe, position=PLOT)
    plante.genes = founder_genes(classe, SEED, 0, r, c, plante.x_cm, plante.y_cm)
    pre_croitre(plante, SEED, annees)
    return plante


def _mesure(plante: PlantInstance) -> dict:
    """Les chiffres d'un pied. Tout est lu sur l'état réel, rien n'est recalculé."""
    segs = plante.segments
    feuilles = sum(s.is_apex or s.thickness_cm <= LEAF_MAX_THICK_CM for s in segs)
    return {"segments": len(segs),
            "hauteur": plante.plant_class.height_at(plante),
            "rayon": plante.plant_class.canopy_radius_at(plante),
            "apex": sum(s.is_apex for s in segs),
            "feuilles": feuilles / len(segs)}


def mesurer() -> dict:
    """{clé catalogue: {âge: mesure}} + gène `hauteur` du pied (clé 'gene')."""
    res = {}
    for cle, classe in PERENNIAL_CATALOGUE.items():
        res[cle] = {age: _mesure(_pied(classe, age)) for age in AGES}
        res[cle]["gene"] = _pied(classe, 0).gene("hauteur")
    return res


def rapport() -> str:
    """Tableau Markdown, un chiffre par colonne, la limite dans chaque en-tête."""
    colonnes = ("segments", "hauteur cm", "rayon cm", "apex", "% feuillés")
    tete = " | ".join(f"{c} {ETIQUETTE}" for c in colonnes)
    out = [f"| arbre | âge | {tete} | gène hauteur du pied |",
           "|---|---|---|---|---|---|---|---|"]
    for cle, ages in mesurer().items():
        for age in AGES:
            m = ages[age]
            out.append(f"| {cle} | {age} | {m['segments']} | {m['hauteur']:.0f} "
                       f"| {m['rayon']:.0f} | {m['apex']} | {m['feuilles']:.0%} "
                       f"| {ages['gene']:.3f} |")
    return "\n".join(out)


if __name__ == "__main__":
    print(rapport())
