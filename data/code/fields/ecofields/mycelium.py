"""
SYMBIOSE — fields/ecofields/mycelium.py
Réseau fongique : calcul PUR de la dynamique du champ `mycelium ∈ [0,1]`
(1 = sol densément colonisé, 0 = sol sans réseau).

Acteur NEUF du sprint mycélium & interconnexions (CONCEPTION_MYCELIUM_INTERCONNEXIONS
§1). Isolé de `container.py` (le fichier le plus dense du dépôt) sur le modèle de
`ph.py`/`structure.py`/`nutriments.py` : le conteneur n'expose qu'une fine méthode
`tick_mycelium` qui délègue ici. Fonction pure, zéro RNG, zéro log — déterminisme
philo #3.

Modèle (tronçon ①, §1.2) — croissance/déclin par plot, EFFETS §2 DÉBRANCHÉS :

    substrat       = bois_fresh_at[r,c] + MYCEL_OM_POIDS · om_active[r,c]
    substrat_norm  = min(1, substrat / MYCEL_SUBSTRAT_REF)
    epuisement     = 1 − substrat_norm
    humidite_norm  = min(1, humidite[r,c] / 3)          (échelle [0,3])
    secheresse     = 1 − humidite_norm
    fenetre_temp   = bell(temperature_sol[r,c], MYCEL_TEMP_OPT, MYCEL_TEMP_TOL)

    croissance = MYCEL_K_G · substrat_norm · humidite_norm · fenetre_temp
    declin     = MYCEL_K_D · mycelium · (secheresse + epuisement)
    mycelium  += croissance − declin                     (clampe [0,1])

Le réseau pousse là où il y a du carbone (BOIS surtout, sa spécialité), de l'eau et
une température tempérée ; il régresse au sec et quand le substrat est épuisé. Au
tronçon ① PERSONNE ne lit `mycelium` (saprophyte ②, mycorhize ③, faune ④ branchés
plus tard) → aucun effet écologique en retour ; comme `mycelium = 0` au repos et que
le smoke ne pose pas de bois colonisable notable, le golden vise BIT-IDENTIQUE (§1.3).

Le TRAVAIL DU SOL (becher/grelinette) n'est PAS un terme de tick : c'est une
perturbation EVENT-DRIVEN (becher retirera un quantum directement au geste, tronçon
⑤). Le champ `disturbance` (bruit de succession environnemental) n'est délibérément
PAS lu ici (≠ travail joueur, piège du kickoff §1.2).
"""

from __future__ import annotations

from .constants import (MYCEL_K_G, MYCEL_K_D, MYCEL_SUBSTRAT_REF, MYCEL_OM_POIDS,
                        MYCEL_TEMP_OPT, MYCEL_TEMP_TOL, LIANT_K)
from .nutriments import bell


def tick_mycelium(eco) -> None:
    """Met à jour `eco.mycelium` (croissance/déclin) depuis la litière C-riche
    (`bois_fresh_at`), l'`om_active`, l'`humidite` et la `temperature_sol`. Écrit
    `mycelium` ET, au tronçon ②, ajoute LENTEMENT à `om_stable` (rôle LIANT :
    glomaline du réseau qui structure l'humus). À appeler APRÈS `tick_structure`
    (litière/humidité/T_sol déjà à jour ce tick) et AVANT `tick_diffusion`."""
    mycel = eco.mycelium
    for r in range(eco.rows):
        for c in range(eco.cols):
            substrat = eco.bois_fresh_at(r, c) + MYCEL_OM_POIDS * eco.om_active.at_plot(r, c)
            substrat_norm = min(1.0, substrat / MYCEL_SUBSTRAT_REF)
            epuisement = 1.0 - substrat_norm
            humidite_norm = min(1.0, eco.humidite.at_plot(r, c) / 3.0)
            secheresse = 1.0 - humidite_norm
            fenetre_temp = bell(eco.temperature_sol.at_plot(r, c),
                                MYCEL_TEMP_OPT, MYCEL_TEMP_TOL)

            croissance = MYCEL_K_G * substrat_norm * humidite_norm * fenetre_temp
            declin = MYCEL_K_D * mycel.at_plot(r, c) * (secheresse + epuisement)
            mycel.set(r, c, mycel.data[r][c] + croissance - declin)  # clampe [0,1]

            # Rôle LIANT (②, §2.1) : la glomaline sécrétée par le réseau agrège
            # les particules → un petit apport TRÈS LENT à `om_stable` (mémoire du
            # sol), proportionnel au réseau MIS À JOUR ce tick. LIANT_K minuscule
            # (om_stable se décompose à 0.0006/sem) → la mémoire ne dérive pas
            # au-delà du bois. mycelium=0 ⇒ apport nul ⇒ sol non colonisé inchangé.
            if mycel.data[r][c] > 0.0:
                eco.om_stable.add(r, c, LIANT_K * mycel.data[r][c])
