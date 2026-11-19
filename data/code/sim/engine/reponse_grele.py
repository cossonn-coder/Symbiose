"""
SYMBIOSE — sim/engine/reponse_grele.py
Ce que la GRÊLE retire à une plante (sprint STRESS AU BILAN, tronçon ②bis).

📖 Pédagogie — un grêlon est un projectile : il ne gèle rien, il DÉCHIRE. Il hache
les limbes exposés (trous, lambeaux, feuilles arrachées), plus fort sur les larges
feuilles tendres que sur les feuilles étroites ou coriaces. Avant ②bis, la grêle ne
frappait que les semis ; désormais elle touche TOUTE plante qui se trouve sous le coin
frappé (patch `scope="local"`, sim/weather.patch_local) :
  - PLANTULE (stade « semis ») : comportement d'avant conservé — le coup passe par
    l'adaptateur `erode` (feuilles hachées ÷ constitution) et un coup qui dépasse la
    vitalité restante TUE (un plant de trois feuilles n'a pas de quoi repartir) ;
  - ADULTE : des FEUILLES perdues, jamais de mort directe. La plante refait son
    feuillage sur ses réserves ; si elle ne le peut pas, elle meurt ensuite de faim,
    par le bilan (« le moteur ne tue pas, la plante meurt »).
La quantité perdue suit la même échelle que celle qu'`erode` retire au semis
(`DAMAGE_STEP` → `VITALITE_STEP`, division par la constitution `resilience_base`),
× `PART_EXPOSEE_ADULTE` : un semis offre toutes ses feuilles au ciel, une plante faite
n'en expose que la couche externe — les grêlons s'y arrêtent, le cœur du feuillage
est abrité par elle. La sévérité
arrive déjà médiée (intensité × niche `hail_resistance_base` × coriacité × (1 −
paillage − voile/cloche)) par `MortaliteMixin._mediated_damage`.

Fonction pure, déterministe, zéro RNG (philo #3).
"""

from __future__ import annotations

from fields.ecofields.constants import VITALITE_STEP
from sim.effects.mutations import PerteTissus, ReduceHealth
from .aleas import DAMAGE_STEP

RAISON_GRELE = "grêle (feuillage)"

# Part du feuillage d'une plante faite exposée aux grêlons (couche externe). Calibré
# sur l'ouverture `full` seed 42 (grêle s22, i=1,75) : à 1,0 (même main que le semis)
# les annuelles hachées aux ¾ mouraient de faim en série (herbacées posées mortes
# 18 → 46/123, critère ≤ 25 % de Nico rompu) ; à 0,5 : 23/123 [n=1].
PART_EXPOSEE_ADULTE = 0.5


def grele_tissus(plant, effectif: float) -> list:
    """Réponse à la GRÊLE (passée à `_mediated_damage`, `seulement_semis=False`).
    `effectif` = sévérité médiée (> 0). Semis : ancienne voie `ReduceHealth` (mort
    possible). Adulte : `PerteTissus` de feuillage seul, sans destruction."""
    amount = effectif / DAMAGE_STEP
    if plant.stage.name == "semis":
        return [ReduceHealth(plant, amount, RAISON_GRELE, cause="grele")]
    resilience = getattr(plant.plant_class, "resilience_base", 1.0)
    perte = min(plant.feuillage,
                amount * VITALITE_STEP * PART_EXPOSEE_ADULTE / resilience)
    if perte <= 0.0:
        return []               # feuilles déjà tombées (ou pas encore sorties)
    return [PerteTissus(plant, perte, reason="grêle (feuilles hachées)", cause="grele")]
