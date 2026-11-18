"""
SYMBIOSE — sim/engine/feuille.py
Température de la FEUILLE au jour le plus chaud (D139, sprint niche thermique ①).

📖 Pédagogie — pourquoi une feuille n'est pas à la température de l'air :
  Une feuille au soleil absorbe de l'énergie. Elle s'en débarrasse surtout en
  TRANSPIRANT : l'eau qui s'évapore par les stomates emporte la chaleur, comme la
  sueur. Une plante bien arrosée reste donc proche de l'air ; une plante ASSOIFFÉE
  ferme ses stomates pour garder son eau, ne se refroidit plus, et sa feuille
  monte de +10 à +15 °C au-dessus de l'air en plein soleil (échaudage). À l'ombre,
  pas d'énergie à évacuer : la feuille reste à l'air.

      T_feuille = t_max_jour + ECHAUFF_FEUILLE · lumière_reçue · soif

- `t_max_jour` : jour le plus chaud de la semaine (`fields/ecofields/thermique.py`).
- `lumière_reçue` ∈ [0,1] : intégrale journalière de la plante (LightField, ombre de
  la maison, de la canopée et de la ceinture déjà comprises).
- `soif` ∈ [0,1] : fermeture des stomates. Proxy retenu = stress hydrique INSTANTANÉ
  sur l'humidité RESSENTIE (D111 ④, `eau_percue`) : `max(0, 1 − hum/HUM_CONFORT)`,
  la même rampe que `drought_stress` de `_update_physiology` (croissance.py).
  Pourquoi pas `drought_memory` : c'est une intégrale lente (lerp 0,05, ≈ 20 semaines)
  qui garde la plante « assoiffée » des mois après la pluie. Les stomates, eux,
  répondent à l'eau de la semaine : une averse les rouvre aussitôt. Et `eau_percue`
  compte les racines rongées ou pourries — une plante au collet malade a soif dans un
  sol humide, ce qui est réel.

Couche : `sim.engine` (lit une plante ET l'humidité ressentie du frère `racines`).
Pure : zéro RNG, n'écrit rien. Calculée à la demande, une fois par plante et par
semaine par ses lecteurs (dégâts de chaleur, tronçon ③). Niche ② : `heat_memory`
(`_update_physiology`) la lit via `t_feuille_de`.
"""

from __future__ import annotations

from fields.ecofields.thermique import t_max_jour
from .racines import eau_percue

# Échauffement maximal de la feuille (°C) : plein soleil, stomates fermés.
# Ordre de grandeur mesuré sur feuilles en déficit hydrique : +10 à +15 °C au-dessus
# de l'air [conception D139 §3, ordre de grandeur, non revérifié].
ECHAUFF_FEUILLE = 12.0

# Humidité ressentie sous laquelle les stomates commencent à se fermer. Miroir du
# seuil 0.5 de `drought_stress` (`_update_physiology`, croissance.py) : même rampe,
# même sens (« la plante a soif » ne doit pas vouloir dire deux choses).
HUM_CONFORT = 0.5


def soif(plant, eco) -> float:
    """Fermeture des stomates ∈ [0,1] : 0 = plante bien arrosée, 1 = sol sec."""
    r, c = plant.position
    hum = eau_percue(plant, eco, eco.humidite.at_plot(r, c))
    return max(0.0, 1.0 - hum / HUM_CONFORT)


def t_feuille_de(t_max: float, lumiere: float, hum_percue: float) -> float:
    """Cœur PUR de `t_feuille`, pour un appelant qui a déjà la lumière reçue et
    l'humidité ressentie de la plante (`_update_physiology`, niche thermique ②) :
    on ne relit pas deux fois ce que le tick a déjà calculé."""
    return t_max + ECHAUFF_FEUILLE * lumiere * max(0.0, 1.0 - hum_percue / HUM_CONFORT)


def t_feuille(plant, eco, t_air: float, nebulosite: float) -> float:
    """Température de la feuille au jour le plus chaud de la semaine (°C).
    Toujours ≥ `t_max_jour` ; = `t_max_jour` à l'ombre ou bien arrosée."""
    lumiere = eco.lumiere.light_received(plant)
    return t_max_jour(t_air, nebulosite) + ECHAUFF_FEUILLE * lumiere * soif(plant, eco)
