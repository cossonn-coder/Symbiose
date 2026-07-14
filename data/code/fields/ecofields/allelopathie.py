"""
SYMBIOSE — fields/ecofields/allelopathie.py
Allélopathie racinaire : calcul PUR de la DÉCROISSANCE du champ de sol
`allelopathie ∈ [0, ALLELO_MAX]` (concentration agrégée d'allélochimiques par plot).

Acteur du sprint ALLÉLOPATHIE (CONCEPTION_ALLELOPATHIE §A). Isolé de `container.py`
(le fichier le plus dense du dépôt) sur le modèle de `mycelium.py`/`ph.py` : le
conteneur n'expose qu'une fine méthode `tick_allelopathie` qui délègue ici.
Fonction pure, zéro RNG, zéro log — déterminisme philo #3.

Le champ est ALIMENTÉ ailleurs (par `inject_field variable="allelopathie"`, routé
générique via `get_field` — même chemin que l'azote de l'ortie) : ce module ne fait
QUE le décliner. Décroissance LABILE (tronçon ① — l'accumulation autotoxique est le
tronçon ④, un autre champ) :

    detox      = ALLELO_DECAY_MICROBE · min(1, microbiome[r,c] / 3)   (sol vivant)
    a         *= (1 − ALLELO_DECAY_BASE − detox)                      (perte fractionnelle)
    a          = 0  si a < ALLELO_FLOOR                               (snap fin de traîne)

La molécule s'estompe spontanément (hydrolyse/lessivage, ALLELO_DECAY_BASE) et PLUS
VITE là où le sol est vivant (microbiome élevé le dégrade — interconnexion). Au
tronçon ① PERSONNE ne lit `allelopathie` (germination ②, croissance ③ branchées plus
tard) → aucun effet écologique en retour ; comme `allelopathie = 0` au repos et
qu'aucune espèce n'a encore `allelopathie_emission > 0` (tronçon ⑤), le golden vise
BIT-IDENTIQUE.
"""

from __future__ import annotations

from .constants import ALLELO_DECAY_BASE, ALLELO_DECAY_MICROBE, ALLELO_FLOOR


def tick_allelopathie(eco) -> None:
    """Décline `eco.allelopathie` (perte spontanée + détox microbienne). Borné ≥ 0
    par le GridField ; snap à 0 sous ALLELO_FLOOR. À appeler dans la zone décompo/sol
    de la boucle (avant la diffusion). Champ nul au repos ⇒ no-op ⇒ golden NEUTRE."""
    allelo = eco.allelopathie
    for r in range(eco.rows):
        for c in range(eco.cols):
            a = allelo.at_plot(r, c)
            if a <= 0.0:
                continue
            detox = ALLELO_DECAY_MICROBE * min(1.0, eco.microbiome.at_plot(r, c) / 3.0)
            a *= max(0.0, 1.0 - ALLELO_DECAY_BASE - detox)
            allelo.set(r, c, 0.0 if a < ALLELO_FLOOR else a)
