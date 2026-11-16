"""
SYMBIOSE — plants/caracteres.py
Registre des CARACTÈRES génétiques (D139, sprint génétique infinitésimale ①).

Fondation pure : aucun import interne au projet (comme `genetics.py`, qui en
dérive `GENE_NAMES`) → `fields`, `sim`, `bancs` peuvent tous s'y appuyer.

POURQUOI UNE TABLE ?
Jusqu'ici chaque gène était un « facteur » anonyme centré sur 1,0, borné par un
`clamp_gene` global. Ça suffisait tant que tous les gènes étaient des
multiplicateurs sans dimension. Le sprint D139 veut des caractères en VRAIES
unités (un décalage d'optimum en °C, une avance de floraison en semaines, un
taux d'autofécondation en probabilité) : leur valeur « moyenne » n'est plus 1,0
(un décalage moyen vaut 0), leurs bornes ne sont plus [0,4 ; 1,6] (une
probabilité vit dans [0 ; 1]). Il faut donc que chaque caractère DÉCLARE :
  - `unite`      : dans quelle grandeur il s'exprime (lisibilité + vue) ;
  - `neutre`     : la valeur d'un individu moyen de l'espèce — ce que vaut
                   `plant.gene(nom)` quand le gène est absent du vecteur ;
  - `sigma_a`    : la diversité génétique ADDITIVE de l'espèce (écart-type, dans
                   l'unité). C'est le « carburant » de la sélection : plus σ_A est
                   grand, plus une population répond vite à un milieu qui trie ;
  - `bornes`     : limites dures physiologiques (aucun individu ne les franchit,
                   même par introgression) ;
  - `adaptogene` : le caractère a une mémoire d'exposition (plasticité) — voir
                   `ADAPTOGENIC_GENES` dans `genetics.py`, inchangé ici.

POURQUOI UN σ_A (et un neutre) PAR ESPÈCE ?
Une lignée de blé autogame quasi fixée et une population d'ortie allogame n'ont
pas la même réserve de diversité : la table donne la valeur de DÉPART commune,
et une espèce peut la surcharger par un attribut de classe
`genetique = {"autofecondation": {"neutre": 0.95}}` (cf. `PlantBase`). C'est par
ESPÈCE, jamais par plante : la variation individuelle, elle, est dans le
vecteur de gènes de chaque plante.

ORDRE = CANAUX DE HASH. `child_genes`/`sample_genes`/`founder_genes` indexent le
bruit déterministe par la POSITION du gène dans `GENE_NAMES` (dérivé de l'ordre
de cette table). On n'AJOUTE donc qu'EN QUEUE, on ne réordonne jamais, on ne
renomme jamais : un décalage changerait tous les tirages (golden).

Tronçon ① = refactor PUR : toutes les entrées valent ce qui était codé en dur
(facteur, neutre 1,0, σ_A 0,10, bornes [0,4 ; 1,6]). Les vraies unités arrivent
aux tronçons ② et ③.
"""

from dataclasses import dataclass

# Bornes dures d'un caractère « facteur » (multiplicateur sans dimension). Ce sont
# les anciennes GENE_HARD_MIN/GENE_HARD_MAX de `genetics.py`, qui les ré-exporte.
BORNES_FACTEUR = (0.40, 1.60)
SIGMA_A_FACTEUR = 0.10       # = l'ancien GENE_INIT_SIGMA


@dataclass(frozen=True)
class Caractere:
    """Déclaration d'un caractère génétique (valeurs par défaut de l'espèce
    « moyenne » ; `neutre` et `sigma_a` surchargeables par espèce)."""
    unite: str = "facteur"            # "facteur" | "°C" | "semaines" | "probabilité"
    neutre: float = 1.0
    sigma_a: float = SIGMA_A_FACTEUR
    bornes: tuple = BORNES_FACTEUR
    adaptogene: bool = False


_FACTEUR = Caractere()
_FACTEUR_ADAPTO = Caractere(adaptogene=True)

# LA table. Ordre = ordre historique de GENE_NAMES (canaux de hash) — dict Python
# ordonné par insertion. Le sens biologique de chaque gène est commenté dans
# `genetics.py` (au-dessus de GENE_NAMES) ; `adaptogene` recopie ADAPTOGENIC_GENES.
CARACTERES = {
    "hauteur":               _FACTEUR,
    "rusticite_froid":       _FACTEUR_ADAPTO,
    "vigueur":               _FACTEUR,
    "resistance_pathogene":  _FACTEUR_ADAPTO,
    "tolerance_secheresse":  _FACTEUR_ADAPTO,
    "tolerance_ombre":       _FACTEUR_ADAPTO,
    "tolerance_asphyxie":    _FACTEUR_ADAPTO,
    "port_trapu":            _FACTEUR_ADAPTO,
    "germination_thermique": _FACTEUR,
    "phenologie_florale":    _FACTEUR,
}


def parametres_espece(plant_class, nom: str) -> tuple:
    """(neutre, sigma_a) EFFECTIFS d'un caractère pour une espèce : la valeur de la
    table, surchargée champ par champ par `plant_class.genetique[nom]` si l'espèce
    en déclare une. `plant_class=None` → valeurs de la table (espèce « moyenne »).
    Helper UNIQUE : tout lecteur de neutre/σ_A passe par ici."""
    car = CARACTERES[nom]
    surcharge = getattr(plant_class, "genetique", None)
    if surcharge:
        s = surcharge.get(nom)
        if s:
            return (s.get("neutre", car.neutre), s.get("sigma_a", car.sigma_a))
    return (car.neutre, car.sigma_a)


def neutre(nom: str, plant_class=None) -> float:
    """Valeur neutre (individu moyen de l'espèce) d'un caractère."""
    return parametres_espece(plant_class, nom)[0]


def sigma_a(nom: str, plant_class=None) -> float:
    """Diversité génétique additive (écart-type) d'un caractère pour l'espèce."""
    return parametres_espece(plant_class, nom)[1]


def borne(nom: str, x: float) -> float:
    """Borne une valeur aux limites dures PHYSIOLOGIQUES du caractère `nom`
    (remplace, là où le nom est connu, le `clamp_gene` global)."""
    lo, hi = CARACTERES[nom].bornes
    return max(lo, min(hi, x))      # même expression que clamp_gene (bit-identique)
