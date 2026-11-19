"""
SYMBIOSE — sim/embolie.py
La DÉFAILLANCE HYDRAULIQUE d'une plante (D140 G, sprint stress au bilan ①,
`docs/vegetal/sante/conception_plante_vivante.md` §5).

📖 Pédagogie — la sécheresse agit en deux temps :
1. **Stomates fermés** (déjà dans le bilan, `sim/bilan.f_eau`) : sous le seuil sec
   `0,15 / tolérance`, la feuille ferme ses pores pour ne pas perdre d'eau ; elle ne
   capte plus de CO₂, la photosynthèse tombe, la plante vit sur ses réserves. Une
   sécheresse MODÉRÉE affame donc lentement, et la plante repart à la pluie.
2. **Embolie** (ici) : si le sol devient EXTRÊMEMENT sec (sous `PART_EXTREME` du seuil
   sec), la succion dans les vaisseaux devient telle que la colonne d'eau casse : une
   bulle d'air s'y loge et le vaisseau ne conduit plus. Il ne se répare pas — seul du
   bois NEUF (croissance nette positive) rétablit la conduction, lentement. Au-delà de
   `SEUIL_EMBOLIE` (~90 % de conduction perdue, ordre de grandeur des mesures de
   cavitation chez les ligneux) la plante meurt desséchée.

Un arbre a des réserves pour des mois (il ne meurt pas de faim en une saison sèche) :
c'est l'embolie qui le tue s'il manque d'eau trop longtemps. Une herbacée, aux réserves
courtes, meurt souvent de faim avant. La tolérance (gène `tolerance_secheresse`
EXPRIMÉ, plasticité comprise) abaisse le seuil extrême : il faut un sol plus sec
encore pour la faire caviter (philo #2/#7 : pression de sélection sans bonus direct).

Seul l'état `plant.embolie` ∈ [0,1] est écrit (hors digest du golden). Il est lu par
`sim/bilan.f_eau` (la conduction perdue rabote l'eau utile). Zéro RNG (philo #3).
Couche `sim` : lit `plants` (instance) seulement, jamais `sim.engine`.
"""

from __future__ import annotations

# Seuil sec de la feuille (miroir de `sim/bilan.f_eau` : stomates fermés en dessous).
SEUIL_SEC = 0.15
# Le sol doit tomber sous cette PART du seuil sec pour que les vaisseaux cavitent :
# entre ce seuil et le seuil sec, la plante ferme ses stomates et attend (famine lente).
PART_EXTREME = 0.5
# Conduction perdue par semaine à sol TOTALEMENT sec (sévérité 1), feuilles en place :
# 0,9 atteint en ~5 sem de sol à 0, ~9 sem à mi-chemin du seuil extrême [ordre de
# grandeur — une sécheresse extrême d'un à deux mois tue un arbre].
TAUX_EMBOLIE = 0.20
# Part des vaisseaux embolisés remplacée par semaine de croissance PLEINE (surplus du
# bilan ≥ 1 semaine d'entretien, cf. `croissance.SURPLUS_PLEIN`) : demi-vie ~14 sem.
# Le bois neuf dilue l'ancien, il ne le répare pas → retour lent, jamais d'un coup.
RENOUV_BOIS = 0.05
# Défaillance hydraulique : au-delà, plus assez de conduction pour vivre.
SEUIL_EMBOLIE = 0.9


def seuil_extreme(plant) -> float:
    """Eau perçue sous laquelle `plant` cavite : PART_EXTREME × seuil sec du gène
    `tolerance_secheresse` exprimé (tolérante → seuil plus bas). Pur."""
    return PART_EXTREME * SEUIL_SEC / plant.expressed_gene("tolerance_secheresse")


def conduction(plant) -> float:
    """Part des vaisseaux qui conduisent encore ∈ [0,1] (lue par `bilan.f_eau`)."""
    return 1.0 - plant.embolie


def maj_embolie(plant, hum_percue: float, presence: float,
                surplus: float | None) -> bool:
    """Une semaine d'hydraulique. Accumulation ∝ sévérité sous le seuil extrême ×
    `presence` (feuillage en place : un caduc nu ne transpire pas, ses vaisseaux ne
    sont pas tirés) ; dilution par le bois neuf ∝ surplus de croissance. Renvoie True
    si la plante franchit `SEUIL_EMBOLIE` (défaillance hydraulique) — l'appelant la
    tue et consigne la cause. Écrit `plant.embolie` seulement."""
    seuil = seuil_extreme(plant)
    if hum_percue < seuil and presence > 0.0:
        sev = 1.0 - hum_percue / seuil
        plant.embolie = min(1.0, plant.embolie + TAUX_EMBOLIE * sev * presence)
    elif plant.embolie > 0.0 and surplus:
        plant.embolie *= 1.0 - RENOUV_BOIS * min(1.0, surplus)
    return plant.embolie >= SEUIL_EMBOLIE
