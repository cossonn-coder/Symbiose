"""
SYMBIOSE — plants/base/familles.py
PlantBase abstrait (interface lumière polymorphe + profils de croissance/écrasement)
et les 5 familles botaniques de base. S'appuie sur `stades` (GrowthStage) et
`empreintes` (STRATE_DEFAULTS, STRATE_SHADE_TOLERANCE) ; `PlantInstance` n'est
référencé qu'en annotation (forward ref string), donc pas importé.

Sprint éclairement (D20-D21) :
  - Empreintes métriques : hauteur + rayon de canopée + rayon racinaire par
    stade (cm), opacité d'ombre `foliage_density` par espèce. Les anciens
    `foliar_offsets`/`root_offsets` (dessinés à la main) sont REMPLACÉS par une
    dérivation rayon → plots (cf. empreintes._plots_in_radius).
  - Position continue `x_cm, y_cm` (cadrage hybride : lue par le LightField ;
    le sous-sol reste indexé au plot via plot_foyer).
  - Interface lumière polymorphe (height_at / canopy_radius_at / root_radius_at /
    foliage_density_at) partagée avec les pérennes ligneuses (perennials.py).
"""

from __future__ import annotations
import math
from abc import ABC

from .empreintes import STRATE_DEFAULTS, STRATE_SHADE_TOLERANCE, STRATE_SILHOUETTE
from .stades import GrowthStage

# ---------------------------------------------------------------------------
# HIÉRARCHIE DES PLANTES — Niveau 1 : PlantBase (abstrait)
# ---------------------------------------------------------------------------

class PlantBase(ABC):
    """
    Classe abstraite racine.
    Les sous-classes définissent family, genus, name, growth_stages, etc.

    Interface lumière polymorphe (height_at / canopy_radius_at / root_radius_at /
    foliage_density_at) : implémentation par défaut = lecture des stades, avec
    repli sur STRATE_DEFAULTS. Les pérennes ligneuses (perennials.py) la
    surchargent pour interpoler des courbes d'âge. Le LightField n'appelle QUE
    ces méthodes → annuelles et arbres traités uniformément, zéro duplication.
    """
    family: str = ""
    genus: str = ""
    name: str = ""
    rarity: str = "Établie"              # Pionnière · Établie · Climacique · Ancienne · Sentinelle
    keywords: list[str] = []
    space_tolerance_weeks: int = 3       # délai avant régression en cas de conflit non résolu
    growth_stages: list[GrowthStage] = []
    family_effects: list[dict] = []      # effets partagés au niveau famille
    # Cycle de vie saisonnier
    life_cycle: str = "perennial"        # "annual" | "biennial" | "perennial"
    winter_strategy: str = "dormant"     # "die" | "dormant" | "evergreen"
    deciduous: bool = False              # perd son feuillage l'hiver (ombre nulle)
    archetype: str | None = None         # archétype succession écologique
    reproduction_rate: float = 0.02      # production graines par semaine
    # Pollinisation (D22) — pilote l'appariement biparental (reproduction.py)
    pollination_mode: str = "insect"     # "wind" | "insect" | "self"
    pollination_radius_cm: float = 150.0 # portée de croisement (distance euclidienne)
    # Dispersion des GRAINES (sprint VENT ⑤, §5.3 — orthogonal à la POLLINISATION).
    # "barochore" : la graine tombe au pied (gravité, défaut). "anemochore" : graine
    # ailée/plumée (samare, aigrette) emportée SOUS LE VENT → le dépôt génétique de
    # _reproduction se décale dans la direction du vent ∝ sa force (anémochorie).
    seed_dispersal: str = "barochore"    # "barochore" | "anemochore"
    foliage_density: float | None = None # opacité d'ombre [0-1] ; None ⇒ défaut strate
    # Mortalité réaliste (D27) — longévité + âge de fructification
    longevity_years: float | None = None # longévité (ans) ; None ⇒ défaut par life_cycle
    maturity_years: float = 0.0          # âge de 1re fructification (renouvellement arbres)
    # Organes-fruits traçables (décompo·compost ③, absorbe D19). Critère
    # d'ÉLIGIBILITÉ fruitière : seules les espèces au profil reproducteur fruitier
    # portent des `fruits` (Tomato, AppleTree — périmètre de REPRO_BY_SEASON).
    # Gate complet (engine._tick_fruits) = `fruitier ET age_years >= maturity_years`
    # → un jeune plant (pommier < 5 ans) ne fructifie pas. Défaut False = inerte.
    fruitier: bool = False
    # Phénologie florale (arc pollinisation, tronçon ① — CONCEPTION_POLLINISATION §A.4).
    # Fenêtre de floraison PAR ESPÈCE : double porte GDD (« la plante est prête »)
    # + photopériode (« c'est la saison »). Défauts ESTIVAUX (jours longs) ; calibrage
    # post-test. Une stratégie jours-courts (automne) = un seul couple de seuils à
    # régler. INERTE à ce tronçon (rien ne lit `floraison` → golden NEUTRE).
    gdd_floraison:    float = 200.0   # degrés-jours cumulés requis (base T_BASE_FLORAISON)
    bloom_daylen_min: float = 13.5    # h de jour : borne basse de la fenêtre photopériodique
    bloom_daylen_max: float = 16.5    # h de jour : borne haute (estival → au-delà du pic 16 h)
    fungal_susceptibility: float = 0.5   # sensibilité aux maladies fongiques [0-1]
    # --- Constitution d'espèce (sprint SANTÉ & RÉSILIENCE ②, couche 2) ---
    # `resilience_base` = « quand un coup PASSE, à quel point je plie plutôt que je
    # casse ». Tampon de MAGNITUDE générique, appliqué EN AVAL dans `erode()`
    # (instance.py) : `vitalite -= amount / resilience_base`. ORTHOGONAL à la niche
    # (tolérances par stresseur, qui filtrent la SOURCE en amont) → aucun double-compte
    # (source ≠ magnitude, points différents du pipeline). Axe CSR de Grime :
    #   • S (stress-tolérantes, slow-tough) → 1.25 : ligneuses établies, coriaces
    #     lentes, pionnières rustiques (ortie/consoude), graminées fibreuses ;
    #   • intermédiaires → 1.0 : vivaces herbacées, aromatiques, compagnes ;
    #   • R (rudérales, fast-fragile) → 0.8 : annuelles tendres, Solanacées, semis
    #     exigeants qui encaissent mal mais poussent vite.
    # Table COMPLÈTE exigée (Nico) : CHAQUE espèce du catalogue reçoit une valeur
    # explicite — soit une base de FAMILLE ci-dessous (Solanaceae 0.8, Poaceae 1.25),
    # soit un override d'ESPÈCE (species.py/perennials.py). Le défaut 1.0 ci-dessous
    # ne doit rester atteint QUE par une classe nue de test (jamais par le catalogue).
    resilience_base: float = 1.0
    # `hail_resistance_base` (couche 1 — niche grêle) : susceptibilité D'ESPÈCE à
    # l'impact de grêle, médiée EN AMONT dans `_mediated_damage` (mortalite.py, quand
    # `gene_name is None`). >1 = feuillage coriace/petit (graminée, aromatique
    # ligneuse) qui résiste ; <1 = grandes feuilles tendres exposées (courge, potagère)
    # qui se déchirent. Défaut 1.0 = neutre acceptable (la grêle est rare et locale) →
    # pas de table exhaustive requise, seuls quelques profils marqués suffisent.
    hail_resistance_base: float = 1.0
    # `root_loss_tolerance_base` (couche 1 — niche herbivorie racinaire, campagnol,
    # sprint santé & résilience ③) : capacité D'ESPÈCE à ENCAISSER la perte de chevelu
    # racinaire sans effondrer son uptake. DIVISE la perte dans `plant_uptake`. >1 =
    # racines profondes / fort partenariat mycorhizien / système fasciculé redondant
    # (l'arbre garde des pivots hors d'atteinte, le trèfle refait vite du chevelu) ;
    # <1 = bulbeuses & racines superficielles concentrées (l'ail/l'oignon perd son
    # organe de réserve d'un coup). Défaut 1.0 = neutre acceptable (le campagnol est
    # local et rare) → pas de table exhaustive requise, seuls quelques profils marqués.
    root_loss_tolerance_base: float = 1.0
    temp_min_growth: float = 5.0         # °C — seuil de croissance (météo 02) ; en deçà, stagnation. Extensible par espèce.
    # Fenêtre pH d'espèce (sprint physico-chimie, tronçon ⑤). Cloche d'acidité
    # `bell(ph, ph_opt, ph_tol)` lue en germination/succession (porte) ET en
    # croissance/vigueur (façade `vigueur_plante`). DÉFAUT NEUTRE : `ph_tol` LARGE
    # (≈ 3.0) ⇒ `bell ≈ 1.0` sur toute la plage [4.0, 8.5] → une espèce non
    # spécifiée est INSENSIBLE au pH (golden ~neutre). Override par espèce (myrtille
    # acidophile 4.8/0.8, lavande/thym calciphiles 7.4/1.1). La valeur 3.0 est un
    # LITTÉRAL ici (≡ PH_TOL_DEFAUT de la conception §3) : la couche `plants` est la
    # plus basse et n'importe JAMAIS `fields` (règle de couches) — pas d'import du
    # constants.py d'`ecofields`. Cf. CONCEPTION_SOL_PH.md §2.3.
    ph_opt: float = 6.8                  # pH optimal (défaut ≈ neutre)
    ph_tol: float = 3.0                  # demi-largeur LARGE → cloche plate → insensible au pH
    # Fenêtre thermique de LEVÉE (sprint germination thermique, tronçon ②). Cloche
    # `bell(T_sol, t_germ_opt, t_germ_tol)` lue aux 3 points de germination (porte de
    # niche dans succession). MÊME patron que le pH ci-dessus. DÉFAUT NEUTRE : `t_germ_tol`
    # TRÈS LARGE (300.0) ⇒ `bell ≈ 1.0` (0.996–0.997) sur toute la plage de T_sol
    # rencontrée au golden (≈ −1 à +33 °C, swing ±18 °C autour de l'opt) → une espèce
    # non typée est INSENSIBLE à la température de germination (golden INTACT au ②). Le
    # littéral 30.0 du kickoff ② était trop étroit face à ce swing (bell ≈ 0.67–0.77 →
    # flips de germination) : 300.0 est la plus petite demi-largeur qui garde le golden
    # intact (cf. §REPRISE du 00_etat). Le typage qui rend la porte mordante (et le
    # plancher froid `T_GERM_FLOOR`) vient au ③. Littéraux ici (≡ patron pH) : la couche
    # `plants` est la plus basse et n'importe JAMAIS `fields` (règle de couches).
    # Cf. CONCEPTION_GERMINATION_THERMIQUE.md §1.
    t_germ_opt: float = 18.0             # T_sol optimale de levée (°C)
    t_germ_tol: float = 300.0            # demi-largeur TRÈS LARGE → cloche plate → neutre au départ
    # Racine PIVOT décompactante (sprint physico-chimie ⑧) : une plante ainsi marquée
    # fore le sol et l'aère, faisant remonter `structure_sol` sur ses plots (lu par
    # `structure.tick_structure` via RACINE_PIVOT). Défaut False = NEUTRE (aucune action
    # sur la structure). Override par espèce (ex. MedicagoLupulina, luzerne lupuline).
    decompactante: bool = False
    # Tolérance à l'ombre de référence (compétition intra-plot, Q6). None ⇒ dérivée
    # de la strate du stade mature (STRATE_SHADE_TOLERANCE) ; override explicite si
    # l'espèce dévie de sa strate (ex. annuelle héliophile en strate basse).
    shade_tolerance: float | None = None
    # Densification clonale (sprint LUXURIANCE, tronçon ②, D65 §2.2 — absorbe D62).
    # UNE mécanique paramétrée (pas 3 chemins de code, décision D4) : une plante mature
    # de `clonal_mode != "none"` émet des RAMETS (clones génétiques) dans son voisinage
    # → tapissage + colonies ÉMERGENTS (lu par `sim/clonal.py`). Le mode ne module que
    # portée/gate/cadence ; le caractère « envahissant » du rhizome ÉMERGE (portée longue
    # + tolérance ombre), pas d'un flag. DÉFAUTS NEUTRES (`none`) ⇒ aucune espèce non
    # marquée n'émet → golden inchangé hors trèfle stolonifère. Couche `plants` la plus
    # basse : littéraux seuls, aucun import de `fields`/`sim` (règle de couches).
    clonal_mode: str = "none"            # "none" | "stolon" | "rhizome" | "drageon"
    clonal_radius_cm: float = 60.0       # portée d'un ramet (offset ≤ ce rayon)
    clonal_interval: int = 4             # cadence : 1 chance d'émission toutes N semaines
    # BOUTURE (sprint PALETTE DE GESTES ②) — multiplication végétative PAR LE JOUEUR :
    # `bouturable=True` marque les espèces qui reprennent réellement d'un fragment
    # (ligneuses souples, aromatiques : saule/menthe/lavande/figuier/framboisier…) →
    # `sim.actions.bouture.bouturer` accepte d'en prélever un greffon clone. DÉFAUT
    # False = espèce NON bouturable (la plupart : arbre à pivot, annuelle éphémère,
    # carotte…) → le geste refuse EN AMONT sans dépense. Distinct du clonal spontané
    # (`clonal_mode`, émission autonome au tick) : la bouture est un ACTE joueur,
    # event-driven au-dessus du tick → défaut neutre ⇒ golden inchangé. Littéral seul,
    # aucun import (règle de couches : `plants` est la couche la plus basse).
    bouturable: bool = False
    # GREFFE (sprint PALETTE DE GESTES ③) — greffe PAR LE JOUEUR : `greffable=True`
    # marque les espèces LIGNEUSES FRUITIÈRES sur lesquelles la greffe se pratique
    # (pommier, cerisier, figuier, framboisier…). Le geste `sim.actions.greffe.greffer`
    # exige que le greffon ET le porte-greffe soient tous deux greffables (au-delà du
    # gate de FAMILLE `species_compatible`) → une plante non ligneuse (annuelle,
    # aromatique herbacée…) refuse EN AMONT sans dépense. DÉFAUT False = NON greffable
    # (la plupart : annuelles, herbacées) → geste refusé, golden inchangé (aucune
    # espèce greffable n'est semée par le smoke). Distinct de `bouturable` : la bouture
    # multiplie un CLONE entier ; la greffe SOUDE l'aérien d'un greffon sur le
    # racinaire d'un porte-greffe (D8). Littéral seul, aucun import (règle de couches).
    greffable: bool = False
    # Silhouette de RENDU (sprint LUXURIANCE ③, D65 §2.4 (a)). PUR DESCRIPTEUR data :
    # AUCUN effet moteur ici — le renderer C# le lira au tronçon ⑥ (via le pont) pour
    # dessiner la bonne forme au sol. None ⇒ dérivée de la strate du stade MATURE
    # (STRATE_SILHOUETTE) ; override explicite par espèce quand la forme dévie du défaut
    # (courge basse-mais-ÉTALÉE, rosette plaquée…). Palette : touffe · rosette · étalée ·
    # dressée · tapis · buisson. Golden NEUTRE (rien ne lit ce champ dans le moteur).
    silhouette: str | None = None        # None ⇒ défaut par strate mature

    # --- Profil de croissance procédurale (D29 réorienté, tronçon 2) ---
    # Leviers PAR ESPÈCE lus par sim/growth.py (CONCEPTION_CROISSANCE §E.1). Les
    # DÉFAUTS reproduisent les anciennes constantes de module de growth.py → une
    # espèce non migrée pousse exactement comme au tronçon 1 (golden de structure
    # intact). Une espèce migrée (procedural_growth=True) règle ces leviers sur ses
    # growth_stages/age_curve (« reproduire l'allure d'abord », §E.3).
    growth_speed:          float = 2.0    # cm/tick d'allongement de l'apex (≡ GROWTH_SPEED)
    port_archetype:        str   = "fleche"   # stratégie de port (§E.2) — descriptif ici
    apical_dominance_base: float = 1.0    # FORCE de dominance = production d'auxine d'un apex au repos (1.0 = nominal ≡ AUXIN_SOURCE ; >1 = flèche tenue plus longtemps, cf. Tomato)
    branch_angle:          float = 50.0   # angle d'insertion des latéraux (degrés, ≡ BRANCH_ANGLE)
    phototropism_strength: float = 0.30   # sensibilité au gradient de lumière (MARQUÉ par défaut, Q3 — l'apex se penche vers le clair ; 0 = tout droit ; Nico tranche la valeur finale à la maquette, tronçon 4)
    wood_persistence:      int   = 60     # longévité du bois sans apex (semaines, ≡ WOOD_PERSISTENCE)
    max_height_cm:         float = 200.0  # plafond de hauteur de l'apex (≡ MAX_REACH_CM, défaut d'arbre)
    max_extent_cm:         float = 200.0  # plafond d'extension horizontale de la couronne
    emit_length_cm:        float = 8.0    # cm : granularité de segment émis par l'apex (≡ EMIT_LENGTH)
    max_segments:          int   = 40     # plafond dur de segments (≡ MAX_SEGMENTS ; haut pour un arbre)
    organ_site:            str   = "terminal"  # "terminal"|"lateral" — naissance fleurs/fruits (tronçon 5)
    foliage_halfwidth:     float = 0.0    # demi-largeur de feuillage autour d'un segment (couronne non nulle)
    # Bascule vers la voie procédurale (empreinte dérivée de la structure §G). OFF par
    # défaut : l'espèce garde l'ancien chemin (stades). True = migrée (ici : Tomato).
    procedural_growth:     bool  = False

    # --- Port grimpant (D49 volet A, CONCEPTION_GRIMPANTES §2/§3) ---
    # DÉFAUTS INERTES : None → non-grimpante, mécanique de grimpe éteinte (golden
    # intact pour toutes les espèces qui ne les règlent pas). Une grimpante libre
    # (sans support) au-delà de `hauteur_autoportante` VOIT son plancher d'apex
    # s'effondrer → elle retombe (port affalé ÉMERGENT de la géométrie, philo #2 :
    # aucune hauteur clampée, c'est la vraie structure qui se couche). L'accroche à
    # un support (tronçon ②) relèvera à nouveau le plancher → grimpe.
    hauteur_autoportante:  float | None = None  # cm tenus debout SANS appui ; None = non-grimpante
    mode_grimpe:           str | None   = None  # None|"crampon"|"vrille_volubile"|"sarmenteux" — gouverne (②) quels supports sont valides

    # --- Réponse à l'écrasement (volet 2, CONCEPTION_ECRASEMENT §5) ---
    # DEUX axes indépendants, LUS UNIQUEMENT par sim.actions.ecraser_plante (geste
    # joueur event-driven, hors tick) → défauts NEUTRES = golden intact (au repos
    # rien ne les lit). Calibrage de DÉPART par espèce dans species.py/perennials.py.
    resistance_ecrasement:  float = 0.5   # ∈ [0,1] — résistance STRUCTURELLE : pilote
                                          # l'intensité au seam (haute → reste DOUX/plie ;
                                          # basse → NET/casse). Modulée par l'âge (Q4).
    stimulation_ecrasement: float = 0.0   # ∈ [0,1] — BÉNÉFICE de repousse : seuil qui
                                          # ÉPARGNE la santé en régime NET (basilic 0.85
                                          # → écimé mais repart ; tournesol 0.05 → décapité).

    # --- Source de mulch (sprint équilibre invasion ④, D9/D10) ---
    # NATURE de mulch produite quand on RÉCOLTE cette espèce (blé/chanvre → "paille",
    # sapin → "aiguilles", tronçon ⑤ ; None = pas une plante à paille → récolte
    # inchangée). LU UNIQUEMENT par `sim.actions.paillage.recolter_paille` (geste joueur
    # event-driven, hors tick) → défaut None = golden intact (au repos rien ne le lit).
    mulch_source: str | None = None

    # --- Allélopathie racinaire (sprint ALLÉLOPATHIE ①, D4/D5) ---
    # Quantité d'allélochimiques qu'un ÉMETTEUR dépose par tick dans le champ de sol
    # `allelopathie` sur son empreinte RACINAIRE (via un family_effect `inject_field
    # variable="allelopathie" cible="local"`, route générique — même chemin que l'azote
    # de l'ortie). DÉFAUT 0.0 = espèce NON allélopathique (la plupart) → n'injecte rien
    # → champ nul → golden inchangé. Les VALEURS par espèce (noyer fort, tournesol
    # modéré, aulx/aromatiques léger, armoise, seigle) sont posées au tronçon ⑤ ; ici le
    # trait est seulement DÉCLARÉ (0 partout). Lu par PERSONNE ce tronçon (l'inhibition
    # germination ② / croissance ③ arrive après). Littéral seul, aucun import (règle de
    # couches : `plants` est la couche la plus basse, n'importe jamais `fields`).
    allelopathie_emission: float = 0.0
    # SENSIBILITÉ de l'espèce à l'allélopathie (sprint ALLÉLOPATHIE ②, D2). Facteur
    # ∈ [0,1] qui module l'escompte de niche à la GERMINATION lu par la succession :
    # `f_allelo = 1 − allelopathie_sensibilite · rampe(allelopathie[plot])` (rampe
    # Monod continue, cf. ALLELO_GERM_K). 1.0 = sensible STANDARD (une graine ne lève
    # pas dans un sol chargé) ; 0.0 = TOLÉRANT/insensible (lève quand même). Sert aussi
    # l'AUTO-TOLÉRANCE de l'émetteur (D2) : au tronçon ⑤, un émetteur reçoit une
    # sensibilité BASSE à sa propre molécule (le noyer ne s'auto-inhibe pas — champ
    # unique D4, on approxime l'auto-tolérance par la sensibilité, pas d'auto-exclusion
    # du champ, choix surgical du kickoff ②). DÉFAUT 1.0 partout ICI : aucune valeur
    # marquante n'est posée à ce tronçon (calibrage des sensibilités emblématiques =
    # tronçon ⑤). INVARIANT GOLDEN : le champ `allelopathie` étant nul au repos
    # (aucun émetteur avant le ⑤), `rampe(0)=0` ⇒ `f_allelo=1` quelle que soit la
    # sensibilité ⇒ germination inchangée. Littéral seul, aucun import (règle de
    # couches : `plants` est la couche la plus basse, n'importe jamais `fields`).
    allelopathie_sensibilite: float = 1.0

    # --- Interface lumière (polymorphe) ---

    @classmethod
    def height_at(cls, inst: "PlantInstance") -> float:
        """Hauteur effective (cm). Voie procédurale (§G) : max(z) de la structure ×
        génétique (growth_factor déjà intégré dans la croissance). Sinon : potentiel
        du stade × growth_factor × génétique."""
        if cls.procedural_growth:
            return inst.footprint_value("height") * inst.gene("hauteur")
        st = inst.stage
        h = st.canopy_height if st.canopy_height is not None \
            else STRATE_DEFAULTS[st.strate]["height"]
        return h * inst.growth_factor * inst.gene("hauteur")

    @classmethod
    def canopy_radius_at(cls, inst: "PlantInstance") -> float:
        if cls.procedural_growth:
            return inst.footprint_value("canopy_r")
        st = inst.stage
        return st.canopy_radius if st.canopy_radius is not None \
            else STRATE_DEFAULTS[st.strate]["canopy_r"]

    @classmethod
    def root_radius_at(cls, inst: "PlantInstance") -> float:
        if cls.procedural_growth:
            return inst.footprint_value("root_r")
        st = inst.stage
        return st.root_radius if st.root_radius is not None \
            else STRATE_DEFAULTS[st.strate]["root_r"]

    @classmethod
    def foliage_density_at(cls, inst: "PlantInstance", saison: str | None = None) -> float:
        """Opacité d'ombre. Les caducs renvoient 0 l'hiver (cf. pérennes)."""
        if cls.deciduous and saison == "hiver":
            return 0.0
        return cls.foliage_density if cls.foliage_density is not None \
            else STRATE_DEFAULTS[inst.stage.strate]["density"]

    @classmethod
    def shade_tolerance_base(cls) -> float:
        """Tolérance à l'ombre de RÉFÉRENCE de l'espèce (sciaphile >1, héliophile
        <1). Override explicite via `shade_tolerance`, sinon dérivée de la strate
        du stade MATURE (dernier `growth_stages`). Modulée individuellement par le
        gène `tolerance_ombre` : tolérance effective = base × gene("tolerance_ombre").
        Lue en germination (lumière effective) et en croissance (growth_factor)."""
        if cls.shade_tolerance is not None:
            return cls.shade_tolerance
        strate = cls.growth_stages[-1].strate if cls.growth_stages else "moyenne"
        return STRATE_SHADE_TOLERANCE.get(strate, 1.0)

    @classmethod
    def silhouette_base(cls) -> str:
        """Silhouette de RENDU de l'espèce (pur descripteur, tronçon ③). Override
        explicite via `silhouette`, sinon dérivée de la strate du stade MATURE
        (dernier `growth_stages`) via STRATE_SILHOUETTE. Lu par le renderer C# (⑥),
        AUCUN effet moteur → golden neutre. Même patron que shade_tolerance_base."""
        if cls.silhouette is not None:
            return cls.silhouette
        strate = cls.growth_stages[-1].strate if cls.growth_stages else "moyenne"
        return STRATE_SILHOUETTE.get(strate, "touffe")

    @classmethod
    def longevity(cls) -> float:
        """
        Longévité (ans). Override explicite (longevity_years) sinon défaut par
        cycle de vie : annuelle = ∞ (meurt à l'hiver, sénescence sans objet),
        bisannuelle = 2, vivace herbacée = 5.
        """
        if cls.longevity_years is not None:
            return cls.longevity_years
        return {"annual": math.inf, "biennial": 2.0,
                "perennial": 5.0}.get(cls.life_cycle, 5.0)

    def get_all_effects(self, stage_index: int) -> list[dict]:
        """Fusionne les effets famille + les effets du stade courant."""
        if stage_index >= len(self.growth_stages):
            return self.family_effects[:]
        return self.family_effects + self.growth_stages[stage_index].effects

    @classmethod
    def describe(cls) -> str:
        return f"{cls.name} ({cls.family} › {cls.genus}) — {cls.rarity}"

# ---------------------------------------------------------------------------
# NIVEAU 2 : FAMILLES BOTANIQUES
# ---------------------------------------------------------------------------

class Solanaceae(PlantBase):
    """
    Famille : Solanacées.
    Sensibilité familiale au mildiou : chaque rondelle Maladie active
    dégrade la santé une fois par semaine.
    """
    family = "Solanaceae"
    space_tolerance_weeks = 2  # réagissent vite à la compétition
    fungal_susceptibility = 1.0  # mildiou — la plus sensible
    resilience_base = 0.8  # R — annuelles tendres, encaissent mal (tomate/poivron)
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "condition": {"rondelle": "maladie", "min": 1},
            "action": "reduce_health",
            "amount": 1,
            "description": "Sensibilité familiale au mildiou"
        }
    ]


class Fabaceae(PlantBase):
    """
    Famille : Légumineuses.
    Fixation N₂ active en permanence — enrichit la rondelle Lombric du sol.
    """
    family = "Fabaceae"
    space_tolerance_weeks = 4  # très tolérantes à la compétition
    # Bonus spécifique légumineuses : fixation N₂ → fertilité. L'enrichissement
    # du microbiome n'est plus scripté ici — il émerge des exsudats universels
    # (boucle rhizosphère, _apply_exudates).
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "inject_field",
            "variable": "n",
            "amount": 0.03,
            "cible": "local",
            "description": "Fixation N₂ — enrichit la fertilité du sol"
        }
    ]


class Asteraceae(PlantBase):
    """
    Famille : Astéracées.
    Floraison mellifère familiale — ajoute un pollinisateur à chaque floraison.
    """
    family = "Asteraceae"
    space_tolerance_weeks = 3
    fungal_susceptibility = 0.4
    family_effects = [
        {
            "type": "floraison",
            "action": "add_rondelle",
            "variable": "pollinisateur",
            "amount": 1,
            "max": 3,
            "description": "Floraison mellifère familiale"
        }
    ]


class Lamiaceae(PlantBase):
    """
    Famille : Lamiacées (aromatiques).
    Répulsion naturelle des nuisibles pour les plantes adjacentes.
    """
    family = "Lamiaceae"
    space_tolerance_weeks = 4  # très tolérantes
    fungal_susceptibility = 0.2  # aromatiques — peu sensibles
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "adjacency_bonus",
            "bonus": "reduce_maladie_rondelle",
            "amount": 1,
            "description": "Aromatiques — répulsion naturelle des nuisibles au voisinage"
        }
    ]

class Urticaceae(PlantBase):
    """
    Famille : Urticacées (orties).
    Bioindicatrice/améliorante des sols riches en azote : injection locale de
    fertilité, comme une légumineuse mais par minéralisation d'une biomasse
    azotée abondante (patron Fabaceae). Anémophile (fleurs discrètes pollinisées
    par le vent → aucune retombée sur les butineurs, _ATTRACT_* = 0).
    """
    family = "Urticaceae"
    space_tolerance_weeks = 5        # robuste, encaisse bien la compétition
    fungal_susceptibility = 0.3
    pollination_mode = "wind"        # anémophile — fleurs discrètes
    pollination_radius_cm = 300.0    # le pollen voyage loin au vent
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "inject_field",
            "variable": "n",
            "amount": 0.03,
            "cible": "local",
            "description": "Biomasse azotée — enrichit la fertilité du sol"
        }
    ]


class Amaryllidaceae(PlantBase):
    """
    Famille : Amaryllidacées (aulx, oignons).
    Répulsif familial : les composés soufrés éloignent les nuisibles du
    voisinage. Faute d'action moteur qui injecte du NÉGATIF dans le champ
    `ravageur` (cf. note ③), on réutilise le levier défensif data-pur des
    Lamiacées (adjacency_bonus → protège la santé des voisines). Une vraie
    baisse du champ `ravageur` resterait une action moteur à créer (dette).
    """
    family = "Amaryllidaceae"
    space_tolerance_weeks = 4
    fungal_susceptibility = 0.3
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "adjacency_bonus",
            "bonus": "reduce_maladie_rondelle",
            "amount": 1,
            "description": "Répulsif soufré — protège les voisines au voisinage"
        }
    ]


class Poaceae(PlantBase):
    """
    Famille : Graminées.
    Compétition hydrique intense — racines fibreuses épuisent l'humidité locale.
    """
    family = "Poaceae"
    space_tolerance_weeks = 6   # très tolérantes à la compétition
    fungal_susceptibility = 0.4
    resilience_base = 1.25       # S — graminées fibreuses, coriaces (paturin/blé/bambou)
    hail_resistance_base = 1.4   # feuilles étroites/souples — la grêle glisse dessus
    pollination_mode = "wind"        # graminées anémophiles
    pollination_radius_cm = 300.0    # le pollen voyage loin au vent
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "inject_field",
            "variable": "humidite",
            "amount": -0.06,
            "cible": "local",
            "description": "Racines fibreuses — compétition hydrique intense"
        }
    ]


class Ericaceae(PlantBase):
    """
    Famille : Éricacées (myrtille, bruyère, rhododendron).
    Plantes ACIDOPHILES/calcifuges des landes et sous-bois acides : leur signature
    n'est PAS un family_effect (aucun flux injecté), elle EST leur fenêtre pH basse
    (`ph_opt`/`ph_tol` par espèce, tronçon ⑤) — elles ne lèvent ni ne prospèrent sur
    calcaire, et y subissent la chlorose ferrique (jaunissement). Famille INERTE au
    repos (pas de family_effects) : la fenêtre fait tout le travail diégétique.
    """
    family = "Ericaceae"
    space_tolerance_weeks = 4
    fungal_susceptibility = 0.3
    family_effects = []


class Violaceae(PlantBase):
    """
    Famille : Violacées (violettes, pensées).
    Petits couvre-sols de sous-bois et de lisière (sprint LUXURIANCE ⑤, absorbe D62).
    Famille INERTE au repos (aucun family_effect, aucun flux injecté) : sa signature
    est écologique (couvre-sol d'ombre stolonifère, mellifère précoce), portée au
    niveau ESPÈCE (silhouette, clonal_mode, fenêtre thermique) — pas un effet familial.
    Sciaphiles : elles prospèrent SOUS la canopée là où les héliophiles calent, ce qui
    ÉMERGE de la tolérance à l'ombre de leur strate `sol`, pas d'un drapeau familial.
    """
    family = "Violaceae"
    space_tolerance_weeks = 4
    fungal_susceptibility = 0.3
    family_effects = []
