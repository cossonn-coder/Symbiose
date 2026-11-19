"""
SYMBIOSE — sim/effects/herbivorie.py
HERBIVORIE PAR ATTEINTE (D140 G, sprint plante vivante ③,
`docs/vegetal/sante/conception_plante_vivante.md` §4).

📖 Pédagogie — un ravageur ne retire pas « un tiers de vie » : il MANGE des
feuilles (ou pompe des sucres), et seulement celles qu'il ATTEINT.

  - la limace rampe : elle ne broute que le feuillage BAS (sous ~40 cm) ;
  - le puceron pique les pousses tendres de toute plante en saison, et vole
    surtout des SUCRES (la sève élaborée) — il défolie peu ;
  - le doryphore ne mange que les Solanacées (pomme de terre, tomate…) ;
  - la chenille (larve du papillon) mange du feuillage, comme avant.

Sur un plot, les ravageurs d'une densité `d` mangent une QUANTITÉ fixe de
feuilles, `Q = K_HERB × d`, partagée entre les feuillages présents au prorata de
leur poids (`w = feuillage × atteinte × masse_foliaire`, patron `_foliage_grid`).
Ce que la plante perd se rapporte à SA quantité de feuilles sur ce plot :

    perte(plot) = atteinte × min(1, Q / S)          S = Σ des poids du plot

    Δfeuillage = feuillage × moyenne_plots(perte) × parfum × appétence / coriacité
                 (× 2 si foyer non régulé sur sol mort)

Un semis seul (peu de feuilles, S petit) peut tout perdre ; un chêne (feuilles en
couches épaisses sur des dizaines de plots, S grand) perd quelques pour mille.
Le résultat est une PERTE DE TISSUS (`PerteTissus`) : la plante ne meurt pas du
coup, elle meurt ensuite PAR LE BILAN si elle ne peut plus refaire ses feuilles.
Exception : les sucres volés par le puceron sortent des réserves — une plantule
vidée meurt « mangée ».

Écart à la prescription littérale du kickoff (« K × moyenne(d × part) ») : avec
`part = w/S`, un chêne SEUL sur ses plots et un semis seul sur le sien ont la même
part (1) donc la même perte — le banc « chêne < 2 %/sem » est infaisable. La perte
est donc rapportée à la quantité de feuilles de la plante (`masse_foliaire`) :
c'est le « un arbre aux dizaines de plots ne perd presque rien » de la conception.

Couche `sim` : lit `plants` (physiologie) et les champs d'`eco` ; zéro RNG.
"""

from __future__ import annotations

from typing import Callable, NamedTuple

from plants.physiologie import capacite_reserve
from fields.ecofields import MICROBE_RHYTHM_REF
from .mutations import PerteTissus

# --- Constantes (calibrées par `tests/test_herbivorie_atteinte.py`) ----------
K_HERB = 0.30            # feuilles mangées par plot et par unité de densité de ravageur
                         #  (en « couches de feuilles » : 1 = une laitue mûre sur 50×50 cm)
LIMACE_HAUTEUR_CM = 40.0 # la limace ne grimpe guère : feuillage atteint sous 40 cm
H_COUCHE_CM = 30.0       # hauteur de feuillage ≈ une couche de feuilles (masse foliaire)
MASSE_MIN = 0.10         # un semis a peu de feuilles…
MASSE_MAX = 6.0          # … une canopée dense en porte ~6 couches (indice foliaire)
PUCERON_FEUILLE = 0.25   # le puceron défolie peu : un quart de l'effet d'un brouteur
K_SUCRES = 1.0           # sucres volés (semaines d'entretien) par unité de part pompée
PERTE_MIN = 0.002        # en dessous : rien de visible, pas de mutation (ni de log)
# Parfum répulsif (D139 caractères vivants ①, conception §2.1) : les composés
# volatils de la fleur et du feuillage (terpènes) détournent une part des ravageurs.
# facteur = 1 − K_PARFUM_REPULSIF × (parfum − 1). Le caractère est borné [0,4 ; 1,6]
# ⇒ facteur ∈ [0,7 ; 1,3] : borné par construction, jamais une immunité. Une plante
# peu parfumée (< 1) est un peu PLUS broutée — symétrique, pas un bonus gratuit.
K_PARFUM_REPULSIF      = 0.5
# Goût du feuillage (D139 caractères vivants ②, conception §2.2) : un feuillage
# savoureux (`appetence_feuille` > 0, basilic, mâche) attire les ravageurs, un
# feuillage amer ou toxique (tomate, lierre) les détourne. facteur =
# max(PLANCHER, 1 + appetence_feuille) ∈ [0,2 ; 2] : jamais une immunité.
APPETENCE_PLANCHER     = 0.2
# Coriacité (D139 caractères vivants ③) : une feuille dure se mâche mal → perte
# ÷ `coriacite_feuille`, bornée par les bornes du caractère [0,4 ; 1,6] ⇒ × [0,63 ; 2,5].
# Bascule LÉTALE (M6) : foyer non régulé (peu d'auxiliaires) sur sol mort → la
# population n'est plus tenue, la consommation double. Seuil microbiome sur l'échelle
# MICROBE_RHYTHM_REF (sprint RYTHMES MO ② : stérile ~0, sain ≥ 0,08). Placeholders F5.
HERBIVORY_LETHAL_AUX   = 0.20
HERBIVORY_LETHAL_MICRO = 0.05


# --- Atteinte : quelle part du feuillage d'une plante un ravageur peut-il manger ---
def _atteinte_tout(plant) -> float:
    return 1.0


def atteinte_limace(plant) -> float:
    """Part du feuillage sous LIMACE_HAUTEUR_CM, dérivée de la hauteur : une plante
    basse est toute atteinte, un arbre de 10 m presque pas (rejets, branches basses)."""
    h = plant.current_height
    return 1.0 if h <= LIMACE_HAUTEUR_CM else LIMACE_HAUTEUR_CM / h


def _atteinte_solanacees(plant) -> float:
    return 1.0 if plant.plant_class.family == "Solanaceae" else 0.0


class Ravageur(NamedTuple):
    """Une ligne de la table d'atteinte (data-driven)."""
    nom: str                         # champ lu : `eco.populations[nom]` ou `eco.larvae[nom]`
    larve: bool                      # True = champ larvaire (pont de cycle de vie)
    atteinte: Callable               # plante → part de son feuillage à portée [0,1]
    feuille: float                   # part de l'effet qui défolie
    sucres: float                    # sucres volés (semaines d'entretien) par part pompée
    saison_croissance: bool          # n'agit qu'en saison de croissance (hors hiver)


RAVAGEURS: tuple[Ravageur, ...] = (
    Ravageur("puceron",   False, _atteinte_tout,        PUCERON_FEUILLE, K_SUCRES, True),
    Ravageur("limace",    False, atteinte_limace,       1.0, 0.0, False),
    Ravageur("doryphore", False, _atteinte_solanacees,  1.0, 0.0, False),
    Ravageur("chenille",  True,  _atteinte_tout,        1.0, 0.0, False),
)


def masse_foliaire(plant) -> float:
    """Quantité de feuilles par plot (en couches), dérivée de la hauteur : un semis
    de 3 cm ~0,1, une laitue ~1, un arbre plafonné à MASSE_MAX (indice foliaire)."""
    return max(MASSE_MIN, min(MASSE_MAX, plant.current_height / H_COUCHE_CM))


def facteur_gout(plant) -> float:
    """Parfum × appétence / coriacité (D139 caractères ①②③), conservés tels quels."""
    return ((1.0 - K_PARFUM_REPULSIF * (plant.gene("parfum") - 1.0))
            * max(APPETENCE_PLANCHER, 1.0 + plant.gene("appetence_feuille"))
            / plant.gene("coriacite_feuille"))


def _actif(rav: Ravageur, plant, saison: str) -> bool:
    if saison == "hiver" and (rav.saison_croissance or plant.plant_class.deciduous):
        return False                 # hiver : pas de pousses tendres ; un caduc est nu
    return True


def _champ(eco, rav: Ravageur):
    if eco is None:
        return None
    src = getattr(eco, "larvae", None) if rav.larve else getattr(eco, "populations", None)
    return src.get(rav.nom) if src else None


def sommes_feuillage(tile, eco, saison: str) -> dict[str, dict[tuple, float]]:
    """Σ des poids (feuillage × atteinte × masse) par plot, POUR CHAQUE ravageur dont
    le champ existe. Calculée UNE fois par tuile et par tick (pas par plante)."""
    sommes: dict[str, dict[tuple, float]] = {}
    actifs = [rav for rav in RAVAGEURS if _champ(eco, rav) is not None]
    for rav in actifs:
        sommes[rav.nom] = {}
    for p in tile.plants:
        if not p.is_alive or p.feuillage <= 0.0:
            continue
        base = p.feuillage * masse_foliaire(p)
        for rav in actifs:
            if not _actif(rav, p, saison):
                continue
            w = base * rav.atteinte(p)
            if w <= 0.0:
                continue
            g = sommes[rav.nom]
            for plot in p.foliar_plots:
                g[plot] = g.get(plot, 0.0) + w
    return sommes


def herbivorie_atteinte(plant, eco, sommes: dict, saison: str) -> list:
    """Perte de tissus de la semaine pour `plant` (cf. en-tête). Renvoie au plus une
    `PerteTissus` (feuillage et, pour le puceron, réserves)."""
    if not plant.is_alive or eco is None or plant.feuillage <= 0.0:
        return []
    plots = plant.foliar_plots
    if not plots:
        return []
    defol = 0.0                      # part du feuillage perdue (avant facteurs plante)
    sucres = 0.0                     # semaines d'entretien pompées
    for rav in RAVAGEURS:
        g = sommes.get(rav.nom)
        if g is None or not _actif(rav, plant, saison):
            continue
        att = rav.atteinte(plant)
        if att <= 0.0:
            continue
        champ = _champ(eco, rav)
        acc = 0.0
        for (r, c) in plots:
            d = champ.at_plot(r, c)
            s = g.get((r, c), 0.0)
            if d > 0.0 and s > 0.0:
                acc += min(1.0, K_HERB * d / s)
        part = att * acc / len(plots)
        defol += rav.feuille * part
        sucres += rav.sucres * part
    if defol <= 0.0 and sucres <= 0.0:
        return []
    f = facteur_gout(plant)
    # Bascule LÉTALE au plot-foyer (lecture directe : auxiliaires + microbiome).
    r, c = plant.position
    micro_norm = min(1.0, eco.microbiome.at_plot(r, c) / MICROBE_RHYTHM_REF)
    if (eco.category_density("auxiliaire", r, c) < HERBIVORY_LETHAL_AUX
            and micro_norm < HERBIVORY_LETHAL_MICRO):
        f *= 2.0
    d_feuil = min(plant.feuillage, plant.feuillage * defol * f)
    d_res = min(plant.reserves, sucres * f / max(1e-6, capacite_reserve(plant)))
    if d_feuil < PERTE_MIN and d_res < PERTE_MIN:
        return []
    return [PerteTissus(plant, d_feuil, d_res,
                        reason=f"herbivorie feuillage -{d_feuil:.3f}")]
