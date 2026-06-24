"""
SYMBIOSE — world/container.py
Le CONTENEUR (pot mobile / bac immobile) = un `EcoFields` MINIATURE.

> Conception : `docs/conception/CONCEPTION_POTS_BACS_SUBSTRATS.md` §1, §2, §6.
> Tronçon ② du sprint pots/bacs : on pose l'objet `Container`, sa fabrique
> `make_container` (qui applique une recette de `world.substrat`) et son tick
> chimique ISOLÉ `tick_chimie`. PAS de plante dedans encore (uptake/confinement
> = ③). On valide la chimie d'un pot seul : drainage du substrat, décompo de la
> litière pré-chargée (lasagnes/mycélium), pH/structure/soil_memory, lumière à
> sa position.

Idée-clé (décision tranchée 1/6) : on RÉUTILISE `EcoFields`. Un conteneur ne
porte AUCUN nouveau modèle chimique — c'est un `EcoFields(rows, cols)` de petite
taille (pot = 1×1, bac = N×M) dont tous les ticks existants marchent tels quels.
Le conteneur n'ajoute que (a) sa POSITION dans le monde (lumière, déplacement),
(b) son SUBSTRAT (drainage + champs initiaux), (c) un tick chimique ALLÉGÉ (pas
de banque de graines ni de populations : un pot n'a ni succession spontanée ni
vie macro propre — dette ultérieure si on en veut).

Golden-neutre par construction : les conteneurs vivent dans une LISTE au niveau
monde, VIDE au repos. La boucle itère cette liste vide → zéro écriture → smoke
inchangé. Le smoke ne pose JAMAIS de conteneur.

Couches : `world` peut importer `fields` + `plants` ; `fields` n'importe JAMAIS
`world` → pas de cycle. La recette substrat→champs est appliquée ICI (côté
`world`), pas dans `fields`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count

from fields.ecofields import EcoFields
from world.substrat import get_substrat, SubstratRecette

# Compteur d'IDs déterministe (ordre d'appel stable, zéro RNG) pour des
# `tile_id` de mini-sol uniques quand l'appelant n'en fournit pas. Le `tile_id`
# ne sert qu'à tracer/loguer (les champs ne dépendent pas de sa valeur) → ne
# touche NI le golden NI le déterminisme du calcul écologique.
_AUTO_ID = count(1)


@dataclass
class Container:
    """Un conteneur du jardin (CONCEPTION §1).

    `pot` (mobile) ou `bac` (immobile) ; porte un mini-sol `EcoFields` composé
    par un `substrat`, une position monde `(x_cm, y_cm)` (lumière + déplacement),
    un `volume_litres` (pilotera le confinement racinaire au ③) et la/les
    plante(s) qu'il abrite (`plants`, VIDE en ② — remplie au ③).
    """
    container_id:  str
    kind:          str               # "pot" (mobile) / "bac" (immobile)
    substrat:      str               # clé du registre world.substrat.SUBSTRATS
    volume_litres: float
    x_cm:          float
    y_cm:          float
    eco:           EcoFields
    rows:          int = 1
    cols:          int = 1
    mobile:        bool = True        # pot True / bac False (déduit du kind à la fabrique)
    fond_ouvert:   bool = False       # bac couplé à la tuile dessous (§5, branché au ⑤)
    plants:        list = field(default_factory=list)   # plante(s) en pot (③)

    def tick_chimie(self, saison: str, *,
                    house=None, nebulosite: float = 0.0) -> None:
        """Ticke la chimie ISOLÉE de ce conteneur (CONCEPTION §1, tick allégé).

        MÊME ordre que la boucle tuile (`sim/engine/boucle.py`) mais ALLÉGÉ : pas
        de banque de graines, pas de populations, pas de squelettes/succession (un
        pot n'a ni succession spontanée ni vie macro propre — dette ultérieure). On
        enchaîne :

          lumière (ombre maison à la position) → thermique → hydrologie (drainage du
          SUBSTRAT, override) → décomposition (libère la litière pré-chargée) →
          maturation des structures (no-op : aucune) → pH → structure du sol →
          diffusion → soil memory.

        En ② `self.plants == []` : `tick_light` et `tick_soil_memory` voient une
        liste de plantes vide → aucune empreinte de canopée/racine, aucune signature
        de famille → comportement bien défini. L'uptake/croissance des plantes en pot
        arrive au ③ (ici ZÉRO plante).

        `house` (maison du monde) + la position `(x_cm, y_cm)` du conteneur → l'ombre
        maison s'applique selon où le pot est posé (pont lumière §6). `nebulosite` =
        scalaire météo du tick (0 = ciel clair). Déterministe (zéro RNG) ; aucun log.
        """
        eco = self.eco
        recette = get_substrat(self.substrat)
        tile_origin = (self.x_cm, self.y_cm)

        # 2. Lumière directionnelle à la POSITION du conteneur (ombre maison §6).
        eco.tick_light(self.plants, saison, house=house, tile_origin=tile_origin)
        # 2b. Microclimat T_sol (lit la lumière, précède l'hydrologie).
        eco.tick_thermique(saison, nebulosite)
        # 3. Hydrologie avec le DRAINAGE DU SUBSTRAT (override §2) au lieu du soil_type.
        eco.tick_hydrology(drainage_override=recette.drainage)
        # 4. Décomposition confinée — libère la litière pré-chargée (lasagnes/mycélium)
        #    dans la cascade om_fresh→active→stable→NPK. La faim d'azote du bois/substrat
        #    frais bride l'azote au départ puis se lève à mesure que la litière mûrit.
        eco.tick_decomposition()
        # 4b. Maturation des structures posées : un mini-sol n'en porte aucune (un pot
        #     n'accueille pas de bac à compost) → no-op strict (liste vide).
        eco.tick_structures()
        # 4c. Dérive du pH — APRÈS la décompo (elle lit la litière). Pas d'amendement
        #     rondelle dans un conteneur (amend_dir=0).
        eco.tick_ph(0)
        # 4d. Dérive de la structure du sol — APRÈS la décompo. Pas de pluie battante
        #     dans un pot abrité (pluie_norm=0) ; pas de plante (liste vide).
        eco.tick_structure(self.plants, 0.0)
        # 5. Diffusion spatiale (sur 1 cellule = quasi no-op, mais cohérent pour un bac N×M).
        eco.tick_diffusion()
        # 9. Soil memory (la version conteneur la ticke chaque semaine, pas en fin de
        #    saison : un mini-sol n'a pas de cadence saisonnière propre ici). Liste de
        #    plantes vide en ② → signature nulle.
        eco.tick_soil_memory(self.plants)


def _appliquer_recette(eco: EcoFields, recette: SubstratRecette) -> None:
    """Remplit UNIFORMÉMENT les champs du mini-sol aux valeurs de la recette
    (CONCEPTION §2) et dépose sa `litiere_precharge`. PUR `world`-side : ne touche
    que des champs `EcoFields` déjà construits (pas de cycle d'import).

    On écrit `structure_sol`, `ph`, `n/p/k`, `microbiome` (les autres champs gardent
    leur init `__post_init__`, ex. humidité à 0 — un pot fraîchement rempli est sec).
    `GridField.set` clampe aux bornes du champ : les valeurs du registre §2 sont
    déjà dans les plages (npk ≤ 2.2 < 3.0, micro ≤ 1.5 < 3.0, struct/ph bornés).
    Déterministe : balayage `(r, c)` en ordre stable, zéro RNG.
    """
    n0, p0, k0 = recette.npk_init
    for r in range(eco.rows):
        for c in range(eco.cols):
            eco.structure_sol.set(r, c, recette.structure_init)
            eco.ph.set(r, c, recette.ph_init)
            eco.n.set(r, c, n0)
            eco.p.set(r, c, p0)
            eco.k.set(r, c, k0)
            eco.microbiome.set(r, c, recette.microbiome_init)
            # Litière pré-chargée DÉPOSÉE sur chaque cellule (lasagnes, substrat
            # de champignon). `deposer_litiere` fusionne par tissu (no-op si masse
            # ≤ 0). La décompo confinée du mini-sol la libérera dans le temps —
            # zéro nouveau modèle (cascade om_fresh→active→stable→NPK existante).
            for tissu, masse in recette.litiere_precharge:
                eco.deposer_litiere(r, c, tissu, masse)


def _heriter_tuile(eco: EcoFields, tile_eco: EcoFields, tile_rc: tuple) -> None:
    """« Terre du jardin » (§2, `herite_tuile=True`) : COPIE les champs du plot
    `tile_rc=(r, c)` de la tuile source `tile_eco` dans la cellule (0,0) du
    mini-sol — pont tuile→conteneur le plus direct (§6).

    On copie les champs scalaires par plot (humidité, n/p/k, ph, structure,
    microbiome, om_active/om_stable) ET la litière (copie PROFONDE des parcelles :
    le mini-sol ne doit pas partager d'objet `Parcelle` avec la tuile, sinon la
    décompo confinée muterait la tuile — déterminisme + isolation). Un conteneur
    `terre_jardin` est forcément 1×1 (pot) ; on ne traite que la cellule (0,0).
    """
    from fields.ecofields import Parcelle   # import local : évite d'alourdir l'en-tête
    sr, sc = tile_rc
    eco.humidite.set(0, 0, tile_eco.humidite.at_plot(sr, sc))
    eco.n.set(0, 0, tile_eco.n.at_plot(sr, sc))
    eco.p.set(0, 0, tile_eco.p.at_plot(sr, sc))
    eco.k.set(0, 0, tile_eco.k.at_plot(sr, sc))
    eco.ph.set(0, 0, tile_eco.ph.at_plot(sr, sc))
    eco.structure_sol.set(0, 0, tile_eco.structure_sol.at_plot(sr, sc))
    eco.microbiome.set(0, 0, tile_eco.microbiome.at_plot(sr, sc))
    eco.om_active.set(0, 0, tile_eco.om_active.at_plot(sr, sc))
    eco.om_stable.set(0, 0, tile_eco.om_stable.at_plot(sr, sc))
    # Litière : copie profonde des parcelles du plot source (jamais le même objet).
    eco.litiere[0][0] = [Parcelle(p.tissu, p.masse, p.age_sem)
                         for p in tile_eco.litiere[sr][sc]]


def make_container(kind: str, substrat: str, volume_litres: float,
                   x_cm: float, y_cm: float, *,
                   rows: int = 1, cols: int = 1,
                   tile_eco: EcoFields | None = None,
                   tile_rc: tuple | None = None,
                   container_id: str | None = None) -> Container:
    """Fabrique un conteneur REMPLI (CONCEPTION §1, §2).

    1. construit `eco = EcoFields(tile_id, rows, cols)` (mini-sol) ;
    2. applique la recette `get_substrat(substrat)` : champs initiaux + litière
       pré-chargée — SAUF si `herite_tuile` (terre du jardin), auquel cas on COPIE
       le plot de tuile `tile_rc` de `tile_eco` (pont §6) ;
    3. `mobile = (kind == "pot")`.

    `tile_eco`/`tile_rc` ne sont REQUIS que pour le substrat `terre_jardin`
    (`herite_tuile=True`) — absents pour tout autre substrat (ValueError franc si
    manquants, échec tôt plutôt qu'un mini-sol vide silencieux).
    """
    recette = get_substrat(substrat)
    cid = container_id if container_id is not None else f"{kind}{next(_AUTO_ID)}"
    eco = EcoFields(tile_id=f"{kind}:{cid}", rows=rows, cols=cols)

    if recette.herite_tuile:
        if tile_eco is None or tile_rc is None:
            raise ValueError(
                f"substrat {substrat!r} (herite_tuile) exige tile_eco + tile_rc "
                f"(le plot de tuile à copier)"
            )
        _heriter_tuile(eco, tile_eco, tile_rc)
    else:
        _appliquer_recette(eco, recette)

    return Container(
        container_id=cid, kind=kind, substrat=substrat,
        volume_litres=volume_litres, x_cm=x_cm, y_cm=y_cm,
        eco=eco, rows=rows, cols=cols,
        mobile=(kind == "pot"),
    )
