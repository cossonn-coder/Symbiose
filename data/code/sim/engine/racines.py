"""
SYMBIOSE — sim/engine/racines.py
Ce qui ABÎME les racines d'une plante, et ce qu'elle en RESSENT (D111 ④, parasite
de faiblesse). Spec : `docs/champs/sol/conception_sol_qui_respire.md` §3.3.

Deux lectures PURES, appelées par le tick (aucun état neuf, rien à sauver) :

1. `pression_parasite(plant, eco)` — pression d'un champignon PARASITE sur les
   racines d'un hôte DÉJÀ affaibli (décision Q8 de Nico). Générique, pilotée par
   les DONNÉES du registre fongique (`fields/fongique.py`, `parasite=True`, `hotes`
   = familles ou noms d'espèce) : jamais « armillaire » ni « cerisier » en dur.
       pression = PARASITE_K × mycélium moyen sous les racines × faiblesse
   faiblesse ∈ [0,1] : 0 tant que la plante est SAINE (vitalité > SEUIL_SAIN — même
   porte que la niche de fructification ③, labels `"!"`), 1 au seuil « malade ».
   Un hôte vigoureux n'est JAMAIS attaqué. Elle s'AJOUTE à la pression du campagnol
   dans la cible de `root_herbivory_memory` (canal racinaire existant).

2. `eau_percue(plant, eco, hum)` — l'eau que la plante RESSENT = humidité du plot ×
   fonction racinaire restante (`facteur_racinaire`, même formule que l'uptake).
   ⚠ Prémisse du kickoff réfutée au code : l'uptake rogné ne faisait QUE laisser plus
   d'eau au sol — aucun lecteur ne ramenait la perte à la plante (le stress hydrique,
   la croissance et la convalescence lisent l'humidité du SOL). Sans ce relais le
   canal racinaire était inerte (campagnol compris). Avec : racines rongées/pourries
   → stress hydrique perçu ↑ (voie sécheresse EXISTANTE → dégâts) et convalescence ↓.
   Philo #2 : on module le FLUX sol → plante, jamais la vitalité directement.
   mémoire = 0 ⇒ facteur 1.0 exactement ⇒ golden NEUTRE hors parasite/campagnol.

Coût : le test d'hôte (ensemble figé de labels) écarte d'emblée toute plante non
listée ; le mycélium n'est lu que pour un hôte affaibli (peu nombreux).
"""
from __future__ import annotations

from fields.ecofields.uptake import facteur_racinaire
from fields.fongique import REGISTRE_FONGIQUE
from plants.base.instance import SEUIL_SAIN, SEUIL_AFFAIBLI

# Labels (familles OU noms d'espèce) attaquables par AU MOINS un parasite du registre.
# Calculé une fois à l'import, depuis les données (ajouter un parasite = une ligne
# dans `REGISTRE_FONGIQUE`, rien ici).
HOTES_PARASITES = frozenset(h for esp in REGISTRE_FONGIQUE.values() if esp.parasite
                            for h in esp.hotes)

# POURRIDIÉ (⑦bis, décision Nico « le parasite peut tuer ») : la pression ne se
# contente plus de viser une mémoire plafonnée (canal campagnol, perte ≤ 50 %) ;
# elle CUMULE une pourriture du collet `pourriture_memory` qui n'a pas de plafond.
#   attaque (pression > 0) : m += POURRI_TAUX × pression × (1 − m)
#   répit  (pression = 0)  : m *= (1 − POURRI_REPOUSSE)  (les racines repoussent)
# Eau perçue × (1 − m) : à m → 1 la plante ne boit plus → stress hydrique → dégâts
# (voie sécheresse EXISTANTE) et convalescence bloquée → mort → squelette de bois →
# saprophytes. Un hôte sain n'est jamais attaqué ; un hôte qui se rétablit (vitalité
# > SEUIL_SAIN) coupe la pression et guérit. Le taux doit DEVANCER la convalescence
# (sinon, sur sol humide, l'hôte guérit avant que la pourriture ne compte : 0,02
# mesuré → jamais de mort). Banc [pommier 8 ans, n=1 arbre par cas, 312 sem.] :
# vitalité 0,6 + réseau 0,4 (ou 0,25) → m ≈ 0,8 en 26 sem., mort sem. 119 ;
# même hôte sans réseau → survit ; hôte parti sain (1,0), affaibli un temps →
# m 0,51 puis guérit (m → 0). Knobs de calibrage.
POURRI_TAUX     = 0.10
POURRI_REPOUSSE = 0.02

# Gain de la pression parasite (knob de calibrage, D111 ④). Mycélium du monde `full`
# sous racines ~0,02-0,45 : à 2,0 un réseau moyen (0,25) sur un hôte « malade »
# vise une mémoire 0,5 — du même ordre qu'un campagnol dense.
PARASITE_K = 2.0


def est_hote(plant) -> bool:
    """La famille ou l'espèce de la plante figure parmi les hôtes d'un parasite."""
    cls = plant.plant_class
    return (getattr(cls, "family", None) in HOTES_PARASITES
            or cls.name in HOTES_PARASITES)


def faiblesse(plant) -> float:
    """0 si saine (vitalité > SEUIL_SAIN), rampe linéaire jusqu'à 1 au seuil
    « malade » (SEUIL_AFFAIBLI) et au-delà."""
    v = plant.vitalite
    if v > SEUIL_SAIN:
        return 0.0
    return min(1.0, (SEUIL_SAIN - v) / (SEUIL_SAIN - SEUIL_AFFAIBLI))


def pression_parasite(plant, eco) -> float:
    """Pression parasite ∈ [0,1] sur les racines de `plant` (0 si non hôte, saine, ou
    sans mycélium sous ses racines). Pure, déterministe, zéro RNG."""
    if not est_hote(plant):
        return 0.0
    f = faiblesse(plant)
    if f <= 0.0:
        return 0.0
    plots = [(r, c) for (r, c) in plant.root_plots
             if 0 <= r < eco.rows and 0 <= c < eco.cols] or [plant.position]
    myc = sum(eco.mycelium.at_plot(r, c) for (r, c) in plots) / len(plots)
    return min(1.0, PARASITE_K * myc * f)


def maj_pourriture(plant, pression: float) -> None:
    """Intègre le pourridié du collet (⑦bis) depuis la pression parasite du tick."""
    m = plant.pourriture_memory
    if pression > 0.0:
        plant.pourriture_memory = min(1.0, m + POURRI_TAUX * pression * (1.0 - m))
    elif m > 0.0:
        m *= 1.0 - POURRI_REPOUSSE
        plant.pourriture_memory = m if m > 1e-6 else 0.0


def eau_percue(plant, eco, hum: float) -> float:
    """Humidité ressentie par la plante au plot-foyer : `hum` × fonction racinaire
    restante (chevelu rongé/pourri, plafonné) × (1 − pourridié du collet, ⑦bis).
    Mémoires nulles → `hum` inchangé (bit-identique)."""
    mem = plant.root_herbivory_memory
    pourri = plant.pourriture_memory
    if mem <= 0.0 and pourri <= 0.0:
        return hum
    if mem > 0.0:
        r, c = plant.position
        hum = hum * facteur_racinaire(mem, plant.plant_class.root_loss_tolerance_base,
                                      eco.mycelium.at_plot(r, c))
    return hum * (1.0 - pourri) if pourri > 0.0 else hum
