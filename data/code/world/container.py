"""
SYMBIOSE — world/container.py
Le CONTENEUR (pot mobile / bac immobile) = un `EcoFields` MINIATURE.

> Conception : `docs/joueur/outils/conception_pots_bacs_substrats.md` §1, §2, §6.
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
from plants.base import PlantInstance
from sim.growth import grow_plant
from world.substrat import get_substrat, SubstratRecette

# Compteur d'IDs déterministe (ordre d'appel stable, zéro RNG) pour des
# `tile_id` de mini-sol uniques quand l'appelant n'en fournit pas. Le `tile_id`
# ne sert qu'à tracer/loguer (les champs ne dépendent pas de sa valeur) → ne
# touche NI le golden NI le déterminisme du calcul écologique.
_AUTO_ID = count(1)

# ---------------------------------------------------------------------------
# CONFINEMENT RACINAIRE — effet nain HYBRIDE (CONCEPTION §3, tronçon ③).
# Trois leviers cumulés, AUCUN n'est un malus direct sur la plante (philo #2) :
# l'effet nain ÉMERGE d'une contrainte de ressource/volume/géométrie.
# Knobs de DÉPART (calibrage post-test, philo #3) — lisibles, zéro RNG.
# ---------------------------------------------------------------------------

# Volume racinaire de RÉFÉRENCE d'un plot de pleine terre (50×50 cm × ~30 cm de
# profondeur utile ≈ 75 L). `volume_norm = volume_litres / VOLUME_REF` : un pot
# de 75 L ≈ pleine terre (pas de confinement), un pot de 5 L → volume_norm ≈ 0.07.
VOLUME_REF = 75.0

# Levier 1 — borne de l'amplification de prélèvement (sécurité). volume_factor =
# 1/volume_norm, clampé à [1, VOLUME_CONF_MAX] : un grand bac (≥ VOLUME_REF) ne
# DOPE jamais l'uptake (facteur ≥ 1, jamais < 1 → un grand volume ne fait pas
# pousser PLUS qu'en pleine terre, il ne CONFINE pas), un pot minuscule sature
# la borne (pas d'uptake explosif qui viderait le champ en un tick).
VOLUME_CONF_MAX = 12.0

# Levier 3 — signal root-bound. `occupation = proxy_racinaire / volume_litres`
# (proxy = hauteur courante en cm, croît avec la plante — `biomass` n'existe pas
# sur PlantInstance, cf. §3 « proxy volontairement grossier »). Au-delà du seuil,
# la croissance segmentaire est bridée par `confinement ∈ [CONF_MIN, 1]`.
ROOTBOUND_SEUIL = 0.30   # occupation (cm/L) à partir de laquelle le pot sature
ROOTBOUND_K     = 1.20   # raideur du bridage au-delà du seuil
CONF_MIN        = 0.25   # plancher : un pot saturé ne fige jamais TOTALEMENT la pousse

# ---------------------------------------------------------------------------
# COUPLAGE FOND OUVERT — pont conteneur↔tuile dessous (CONCEPTION §5, tronçon ⑤).
# Un bac à fond ouvert COMMUNIQUE avec le plot de tuile sous lui (interconnexion
# des acteurs). AUCUN effet n'est un bonus direct sur la plante (philo #2) : tout
# passe par un flux de matière (eau, racines, microbiome/om) entre deux EcoFields.
# Knobs de DÉPART (calibrage post-test, philo #3) — zéro RNG.
# ---------------------------------------------------------------------------

# Diffusion LENTE bidirectionnelle microbiome/om entre la cellule d'assise du bac
# et le plot de tuile dessous (colonisation par le bas). Échange = part de l'écart
# transférée chaque tick — faible (l'inoculation prend des saisons, pas un tick).
COUPLAGE_DIFFUSION = 0.04


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


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
    # Assise sur le jardin (§5, tronçon ⑤). `tile_eco` = l'`EcoFields` de la tuile
    # qui PORTE le conteneur, `tile_rc` = le plot (r, c) sous lui. Renseignés à la
    # pose. Un POT (fond fermé/percé) n'a besoin que d'eux pour évacuer son drainage
    # vers la tuile (point 1) ; un BAC `fond_ouvert` ouvre EN PLUS racines (point 2)
    # et diffusion microbiome/om (point 3). À `None` → conteneur DÉTACHÉ (hors-sol
    # pur, ex. pot sur une terrasse) : aucun pont (rétrocompat ②/③/④ + golden NEUTRE).
    tile_eco:      object = None
    tile_rc:       tuple = None

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
        #    L'eau qui s'écoule du fond (perte de drainage, retournée par tick_hydrology)
        #    n'est plus JETÉE quand le conteneur est posé sur une tuile : on l'INJECTE
        #    dans l'humidité du plot d'assise (pont matière §5, point 1 — vaut pour POT
        #    comme pour BAC : tout conteneur posé a un trou/fond par où l'eau descend).
        pertes = eco.tick_hydrology(drainage_override=recette.drainage)
        self._drainer_vers_tuile(pertes)
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
        # 10. Diffusion microbiome/om ↔ tuile (§5, point 3) — UNIQUEMENT pour un bac à
        #     fond ouvert : la vie du sol colonise le mini-sol par le bas (et vice-versa).
        self._diffuser_vers_tuile()

    # ------------------------------------------------------------------
    # CONFINEMENT RACINAIRE — effet nain HYBRIDE (CONCEPTION §3, tronçon ③).
    # ------------------------------------------------------------------

    def _volume_factor(self) -> float:
        """Levier 1 (réservoir réduit, ÉMERGENT). Amplificateur de prélèvement
        rapporté au volume RÉEL du conteneur : `1/volume_norm`, clampé à
        [1, VOLUME_CONF_MAX]. Petit pot → grand facteur → la plante vide vite le
        peu d'eau/nutriments du mini-sol → sécheresse/carence émergentes (via les
        mécanismes EXISTANTS de stress, pas un malus direct — philo #2). Un volume
        ≥ VOLUME_REF retombe à 1.0 (pas de confinement = pleine terre)."""
        volume_norm = self.volume_litres / VOLUME_REF
        if volume_norm <= 0.0:
            return VOLUME_CONF_MAX
        return _clamp(1.0 / volume_norm, 1.0, VOLUME_CONF_MAX)

    def _confinement(self, plant: PlantInstance) -> float:
        """Levier 3 (signal root-bound, EXPLICITE — garantit le bonsaï visible).
        `occupation = proxy_racinaire / volume_litres` ; proxy = hauteur courante
        (cm), qui croît avec la plante (`biomass` n'existe pas sur PlantInstance,
        cf. §3 « proxy volontairement grossier »). Sous le seuil → 1.0 (croissance
        intacte). Au-delà, la croissance segmentaire est bridée par un facteur
        ∈ [CONF_MIN, 1]. Ce n'est PAS un malus « parce que c'est un pot » : il ne
        s'active QUE quand le réservoir racinaire SATURE physiquement — l'effet nain
        ÉMERGE de la contrainte de volume (philo #2)."""
        if self.volume_litres <= 0.0:
            return CONF_MIN
        occupation = plant.current_height / self.volume_litres
        if occupation <= ROOTBOUND_SEUIL:
            return 1.0
        return _clamp(1.0 - ROOTBOUND_K * (occupation - ROOTBOUND_SEUIL),
                      CONF_MIN, 1.0)

    def _cellules(self) -> list[tuple]:
        """Cellules VALIDES du mini-sol (géométrie du conteneur). Pour un pot 1×1
        → [(0,0)] ; pour un bac N×M → toutes ses cellules."""
        return [(r, c) for r in range(self.eco.rows) for c in range(self.eco.cols)]

    # ------------------------------------------------------------------
    # COUPLAGE FOND OUVERT — ponts conteneur↔tuile (CONCEPTION §5, tronçon ⑤).
    # Trois flux de matière, AUCUN bonus direct sur la plante (philo #2).
    # No-op STRICT quand `tile_eco is None` (conteneur détaché) → golden NEUTRE.
    # ------------------------------------------------------------------

    def _drainer_vers_tuile(self, pertes: list) -> None:
        """§5 point 1 — DRAINAGE → TUILE. L'eau évacuée par le fond du conteneur
        (perte de drainage par cellule, retournée par `tick_hydrology`) n'est plus
        perdue : elle est INJECTÉE dans l'humidité du plot de tuile d'assise. Pont
        matière (bilan d'eau conservé : ce que le mini-sol perd, le sol gagne). Vaut
        pour POT comme pour BAC (tout conteneur posé évacue par un trou). No-op si
        DÉTACHÉ. Déterministe : on cumule la perte de toutes les cellules en UN add."""
        if self.tile_eco is None or self.tile_rc is None:
            return
        tr, tc = self.tile_rc
        total = sum(perte for _r, _c, perte in pertes)
        if total > 0.0:
            self.tile_eco.humidite.add(tr, tc, total)

    def _diffuser_vers_tuile(self) -> None:
        """§5 point 3 — MICROBIOME/OM → TUILE (bac fond ouvert SEUL). Diffusion LENTE
        BIDIRECTIONNELLE entre la cellule d'assise du mini-sol et le plot de tuile
        dessous : la vie du sol colonise le bac par le bas (et le compost du bac
        ensemence le sol). Échange = `COUPLAGE_DIFFUSION · écart` sur microbiome,
        om_active et om_stable. Conserve la masse (ce qui sort d'un champ entre dans
        l'autre). Pas pour un pot (fond fermé). Déterministe, zéro RNG."""
        if not self.fond_ouvert or self.tile_eco is None or self.tile_rc is None:
            return
        tr, tc = self.tile_rc
        cr, cc = 0, 0   # cellule d'assise du bac (le bac N×M s'appuie par (0,0))
        for champ in ("microbiome", "om_active", "om_stable"):
            ici  = self.eco.get_field(champ)
            la   = self.tile_eco.get_field(champ)
            flux = (la.at_plot(tr, tc) - ici.at_plot(cr, cc)) * COUPLAGE_DIFFUSION
            ici.add(cr, cc, flux)        # le sol vivant migre vers le bac…
            la.add(tr, tc, -flux)        # …prélevé sur la tuile (masse conservée)

    def tick(self, saison: str, seed: int, week: int, *,
             house=None, nebulosite: float = 0.0) -> None:
        """Tick COMPLET d'un conteneur habité (CONCEPTION §3) : la chimie isolée
        PUIS l'uptake + la croissance des plantes du conteneur, MÊME enchaînement que
        la boucle tuile (`sim/engine/boucle.py` : uptake → physiologie → croissance)
        mais BORNÉ à la géométrie du mini-sol (levier 2) et MODULÉ par le volume
        (leviers 1 & 3). `tick_chimie` reste appelable seul (un conteneur vide ne fait
        que sa chimie — rétrocompat ②).

        Déterministe (zéro RNG ; ordre d'itération stable plantes×cellules)."""
        self.tick_chimie(saison, house=house, nebulosite=nebulosite)
        if not self.plants:
            return
        eco = self.eco
        vfac = self._volume_factor()              # levier 1 (constant pour ce conteneur)
        cellules = self._cellules()               # levier 2 : plafond géométrique
        for plant in self.plants:
            if not plant.is_alive:
                continue
            # Levier 2 — l'uptake n'itère QUE sur l'INTERSECTION de l'empreinte
            # racinaire et des cellules du mini-sol : les racines ne « débordent »
            # pas dans le vide hors du pot. Repli sur le foyer borné si l'empreinte
            # ne recoupe rien de valide.
            roots = [(r, c) for (r, c) in plant.root_plots if (r, c) in cellules]
            if not roots:
                roots = [(0, 0)]
            # §5 point 2 — RACINES → TUILE (bac fond ouvert SEUL) : une fois le
            # root-bound atteint (le mini-sol SATURE), les racines DESCENDENT dans le
            # plot de tuile dessous → uptake AUSSI là-bas → la plante puise enfin dans
            # le sol profond, ce qui LÈVE l'effet nain (elle n'est plus confinée). C'est
            # le couplage qui rend le bac fond ouvert ≈ pleine terre une fois colonisé.
            # ÉMERGENT (philo #2) : on n'efface aucun malus, on OUVRE un réservoir.
            descend = (self.fond_ouvert and self.tile_eco is not None
                       and self.tile_rc is not None
                       and self._confinement(plant) < 1.0)
            n_sites = len(roots) + (1 if descend else 0)
            share = 1.0 / n_sites
            for r, c in roots:
                eco.plant_uptake(r, c, plant.current_stage,
                                 shade_memory=plant.shade_memory,
                                 drought_memory=plant.drought_memory,
                                 share=share, volume_factor=vfac)
            if descend:
                # Uptake dans la TUILE (réservoir profond) — `volume_factor=1.0` (le
                # sol n'est pas confiné) : la concentration n'y chute pas vite → la
                # plante respire. Repère du root-bound levé pour le levier 3 ci-dessous.
                tr, tc = self.tile_rc
                self.tile_eco.plant_uptake(tr, tc, plant.current_stage,
                                           shade_memory=plant.shade_memory,
                                           drought_memory=plant.drought_memory,
                                           share=share, volume_factor=1.0)
            # Physiologie minimale (drought/shade/growth_factor) — RÉPLIQUE allégée
            # de `_update_physiology` (côté `sim.engine`, non importable depuis `world`).
            # Ferme la boucle ressource→stress→croissance : un pot asséché élève la
            # drought_memory → growth_factor capté par la lumière, et la pénurie d'eau
            # ralentit la pousse via les mécanismes existants (pas un malus direct).
            r0, c0 = roots[0]
            light = eco.lumiere.at_plot(r0, c0)
            hum = eco.humidite.at_plot(r0, c0)
            plant.shade_memory += (1.0 - light - plant.shade_memory) * 0.10
            plant.shade_memory = _clamp(plant.shade_memory, 0.0, 1.0)
            drought_stress = max(0.0, 1.0 - hum / 0.5) if hum < 0.5 else 0.0
            plant.drought_memory += (drought_stress - plant.drought_memory) * 0.05
            plant.drought_memory = _clamp(plant.drought_memory, 0.0, 1.0)
            target_g = 0.6 + 0.4 * min(1.0, light)
            plant.growth_factor += (target_g - plant.growth_factor) * 0.10
            plant.growth_factor = _clamp(plant.growth_factor, 0.3, 1.0)
            # Levier 3 — croissance segmentaire bridée par le signal root-bound, SAUF
            # si les racines ont DESCENDU dans la tuile (bac fond ouvert root-bound) :
            # le confinement est alors LEVÉ (la plante n'est plus à l'étroit, elle a
            # trouvé le sol profond). Émergent : on ne « débloque » pas un malus, c'est
            # l'ouverture d'un nouveau réservoir racinaire qui rend le bridage caduc.
            conf = 1.0 if descend else self._confinement(plant)
            grow_plant(plant, seed, week, eco.lumiere, confinement=conf)


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
    """Fabrique un conteneur REMPLI (CONCEPTION §1, §2, §5).

    1. construit `eco = EcoFields(tile_id, rows, cols)` (mini-sol) ;
    2. applique la recette `get_substrat(substrat)` : champs initiaux + litière
       pré-chargée — SAUF si `herite_tuile` (terre du jardin), auquel cas on COPIE
       le plot de tuile `tile_rc` de `tile_eco` (pont §6) ;
    3. `mobile = (kind == "pot")` ;
    4. MÉMORISE l'assise `tile_eco`/`tile_rc` sur le conteneur (pont §5, ⑤) : tout
       conteneur POSÉ sur une tuile la connaît → son drainage retourne au sol, et un
       bac fond ouvert ouvre racines + diffusion. À `None` → conteneur DÉTACHÉ
       (hors-sol pur), aucun pont (golden NEUTRE, rétrocompat ②/③/④).

    `tile_eco`/`tile_rc` sont REQUIS pour le substrat `terre_jardin`
    (`herite_tuile=True`, on copie le plot) ; OPTIONNELS sinon (s'ils sont fournis,
    ils servent juste d'assise de couplage §5 ; absents → conteneur détaché).
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
        tile_eco=tile_eco, tile_rc=tile_rc,
    )


def planter_dans(container: Container, plant_class: type,
                 *, cell: tuple = (0, 0)) -> PlantInstance:
    """Plante une `plant_class` DANS un conteneur (CONCEPTION §3.A, tronçon ③).

    La plante naît au CENTRE de la cellule `cell` du mini-sol (un pot 1×1 → (0,0)),
    en position CONTINUE `(x_cm, y_cm)` — la position continue existe déjà
    (`PlantInstance.x_cm/y_cm`, embedding cartésien : centre du plot (r,c) =
    (c·50+25, r·50+25)). Son `position` (plot-foyer) suit la cellule. On l'ajoute à
    `container.plants` et on la retourne (l'appelant peut la garder). Aucun RNG.
    """
    from constants import PLOT_CM   # import local : évite d'alourdir l'en-tête
    r, c = cell
    plant = PlantInstance(
        plant_class=plant_class,
        position=(r, c),
        x_cm=c * PLOT_CM + PLOT_CM / 2,
        y_cm=r * PLOT_CM + PLOT_CM / 2,
    )
    container.plants.append(plant)
    return plant
