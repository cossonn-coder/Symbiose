# SYMBIOSE — tools/jardinier_auto/perception.py
# Étape 1 de la boucle (§3.1) : « que sais-je de cette plante ? ». Une interface,
# deux implémentations commutées par le profil (§9) :
#   - omniscient : lit DIRECTEMENT l'état écologique (vitalité continue D75,
#     humidité de sol, lumière reçue, Qi territorial). Référence haute : ce que
#     ferait un jardinier parfaitement informé. Câblé dès ①.
#   - semiologique : ne lira que ce qu'un joueur VOIT (signes, `etat` discret).
#     Stub ici → tronçon ⑦ optionnel.
#
# LECTURE PURE (philo #2/#5) : aucune fonction n'écrit un champ ni un attribut de
# plante. La perception ne fait qu'observer ; ce sont les gestes (execution.py)
# qui agissent, via `sim.actions`.

from __future__ import annotations
from dataclasses import dataclass

from sim.vigueur_plante import maturite, qi_local


@dataclass(frozen=True)
class Perception:
    """Instantané omniscient d'une plante sous tutelle, à un tick donné.
    Valeurs continues — le profil semiologique les remplacera par des signes."""

    position: tuple      # (row, col) plot-foyer, cible des gestes de milieu
    vitalite: float      # santé continue [0,1] (D75)
    maturite: float      # avancement du cycle [0,1] — mûr → récolte possible
    humidite: float      # humidité du sol au plot-foyer [0,3]
    lumiere: float       # lumière reçue par la canopée
    qi: float            # Qi territorial puisé sous l'empreinte racinaire [0,1]


def percevoir(plant, eco, profil) -> Perception:
    """Construit la perception d'une `plant` selon le `profil`.
    `omniscient` : lecture directe des champs. `semiologique` : non encore câblé
    (⑦) → refuse explicitement plutôt que de mentir sur ce qui est perçu."""
    if profil.perception == "semiologique":
        raise NotImplementedError(
            "perception 'semiologique' câblée au tronçon ⑦ (optionnel)")
    r, c = plant.position
    return Perception(
        position=(r, c),
        vitalite=plant.vitalite,
        maturite=maturite(plant),
        humidite=eco.humidite.at_plot(r, c),
        lumiere=eco.lumiere.light_received(plant),
        qi=qi_local(plant, eco),
    )
