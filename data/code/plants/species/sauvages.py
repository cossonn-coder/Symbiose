"""
SYMBIOSE — plants/species/sauvages.py
Plantes spontanées « sauvages » (non-archétypes de succession) : Ortie
(Urticaceae), Myrtille (Ericaceae) + le trio clonal du sprint LUXURIANCE ⑤
(absorbe D62) — Framboisier (Rosaceae, drageon), Bambou traçant (Poaceae,
rhizome envahissant), Violette odorante (Violaceae, stolon d'ombre). Données
pures (niveau 3), s'appuient sur `plants.base`.

DISTINCT d'`adventices.py` : ces espèces ne sont PAS des archétypes de succession
(`archetype=None`) → elles n'entrent PAS dans WEED_CATALOGUE ni dans la
germination spontanée. Elles existent au catalogue (PLANT_CATALOGUE) pour être
posées par le joueur ou acquises (magazine), pas tirées par la SeedBank. Leur
intérêt est écologique (hôte de chenilles, biomasse azotée, bioindication,
tapissage clonal). Les trois clonales réutilisent la mécanique figée au tronçon ②
(`clonal_mode` + `sim/clonal.py`) — AUCUNE modif du moteur clonal ; le mode ne
module que portée/gate/cadence, le caractère envahissant ÉMERGE (cf. D65 §2.2).
Toutes HORS scénario golden (jamais semées) → dérive NEUTRE.
"""

from __future__ import annotations
from plants.base import (GrowthStage, Urticaceae, Ericaceae, Poaceae,
                         Violaceae, Asteraceae, Sphagnaceae, Droseraceae,
                         PlantBase)


class Nettle(Urticaceae):
    """
    Urtica dioica — Ortie (Urticaceae).
    Vivace robuste, bioindicatrice de sols riches en azote : sa famille injecte
    localement de la fertilité (biomasse azotée minéralisée). Anémophile (fleurs
    discrètes au vent → aucune retombée butineurs). Hôte majeur de chenilles de
    papillons (paon-du-jour, vulcain) — via le pont chenille générique. Biomasse
    abondante pour le paillis/compost. Comestible (jeunes pousses).
    """
    genus = "Urtica"
    name = "Ortie"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.25         # S — pionnière nitrophile robuste, quasi increvable
    resistance_ecrasement  = 0.6   # touffe dressée, repart de la souche
    stimulation_ecrasement = 0.4
    rarity = "Établie"
    keywords = ["Bioindicatrice", "Comestible", "Biomasse", "Hôte"]
    space_tolerance_weeks = 5
    life_cycle = "perennial"
    winter_strategy = "dormant"
    archetype = None               # PAS une adventice de succession (hors WEED_CATALOGUE)
    seed_dispersal = "anemochore"  # akène léger d'ortie — graines au vent (⑤, §5.3)
    t_germ_opt = 14.0              # vivace robuste tempérée : lève au frais (fenêtre ③)
    t_germ_tol = 13.0              # large → opportuniste des sols riches
    foliage_density = 0.50
    longevity_years = 8
    reproduction_rate = 0.10
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=4,
        ),
        # Vivace : touffe adulte (duration 0). PAS d'effet floraison-pollinisateur
        # (anémophile) — l'injection d'azote vient du family_effects d'Urticaceae.
        GrowthStage(
            name="adulte", duration_weeks=0, strate="basse",
            vigueur_cost=1, canopy_height=90, canopy_radius=30,
            root_radius=40,
            effects=[],
        ),
    ]


class Vaccinium(Ericaceae):
    """
    Vaccinium myrtillus — Myrtille (Ericaceae).
    Sous-arbrisseau ACIDOPHILE/calcifuge des landes et sous-bois acides : le
    DÉMONSTRATEUR ROI de la fenêtre pH (tronçon ⑤). Sa fenêtre basse (`ph_opt=4.8`,
    `ph_tol=0.8`) fait qu'elle ne lève ni ne prospère sur calcaire ; sous SEUIL_
    ACIDOPHILE, posée sur sol alcalin (`ph > CHLOROSE_PH`) elle subit la CHLOROSE
    ferrique (jaunissement, malus de vigueur). archetype=None ⇒ hors WEED_CATALOGUE
    (jamais tirée par la succession) : posée par le joueur / acquise (magazine).
    Mellifère (cloches discrètes), baies comestibles.
    """
    genus = "Vaccinium"
    name = "Myrtille"
    ligneux = True        # D111 ②bis : arbrisseau — rameaux âgés qui sèchent (hiver)
    bois_chute_cm3 = 60.0
    bois_chute_semaine = 46
    feuillage = "cireux"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.6  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.25         # S — sous-arbrisseau ligneux de lande acide, lent et coriace
    ph_opt = 4.8                   # acidophile strict — fenêtre étroite (calcifuge)
    ph_tol = 0.8
    t_germ_opt = 13.0              # lande/sous-bois frais : lève au frais (fenêtre ③)
    t_germ_tol = 9.0               # moyenne
    resistance_ecrasement  = 0.5
    stimulation_ecrasement = 0.3
    rarity = "Établie"
    keywords = ["Acidophile", "Comestible", "Mellifère", "Indicatrice"]
    silhouette = "buisson"         # sous-arbrisseau ligneux ramifié (luxuriance ③) — dévie du défaut `touffe` de la strate basse ; HORS golden → neutre
    space_tolerance_weeks = 4
    life_cycle = "perennial"
    winter_strategy = "dormant"
    deciduous = True               # caduc : feuillage rougi puis largué l'automne
    archetype = None               # PAS une adventice de succession (hors WEED_CATALOGUE)
    foliage_density = 0.40
    longevity_years = 15
    reproduction_rate = 0.06
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=4,
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="basse",
            vigueur_cost=1, canopy_height=40, canopy_radius=30,
            root_radius=35,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison mellifère — clochettes nourrissant l'abeille"
                },
            ],
        ),
    ]


class Raspberry(PlantBase):
    """
    Rubus idaeus — Framboisier (Rosaceae).
    Sous-arbrisseau fruitier DRAGEONNANT (sprint LUXURIANCE ⑤, absorbe D62) : il
    lance des DRAGEONS — de courts rejets qui percent le sol tout près de la souche
    mère — et forme peu à peu un fourré (thicket) DENSE et RESSERRÉ. C'est le
    démonstrateur du mode `drageon` : portée TRÈS COURTE (`clonal_radius_cm=40`, la
    fille naît aux pieds de la mère, ≠ le rhizome qui file loin) et gate LUMIÈRE au
    sol (comme le stolon — un drageon ne perce pas sous un couvert fermé) → la touffe
    s'épaissit sur place sans envahir tout le terrain. Strate `moyenne`→`haute`
    (cannes de 1,5 m), `silhouette="buisson"`. Fruitier : framboises traçables très
    attractives pour la faune. Famille Rosaceae (comme fraisier et pommier). HORS
    golden (jamais semé) → dérive NEUTRE.
    """
    family = "Rosaceae"
    genus = "Rubus"
    name = "Framboisier"
    ligneux = True        # D111 ②bis : cannes de 2 ans qui meurent après fructification
    bois_chute_cm3 = 600.0
    bois_chute_semaine = 38
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.8  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.25         # S — ronce ligneuse drageonnante, repart du réseau souterrain
    resistance_ecrasement  = 0.4   # cannes ligneuses mais cassantes
    stimulation_ecrasement = 0.3
    rarity = "Établie"
    keywords = ["Comestible", "Fruitier", "Drageonnant", "Mellifère"]
    silhouette = "buisson"         # sous-arbrisseau ligneux ramifié (cannes) ; HORS golden → neutre
    space_tolerance_weeks = 4
    life_cycle = "perennial"
    winter_strategy = "dormant"    # cannes qui repartent de la souche au printemps
    t_germ_opt = 15.0              # tempéré : lève au frais du printemps (fenêtre ③)
    t_germ_tol = 10.0              # tolérante
    foliage_density = 0.45
    longevity_years = 10
    reproduction_rate = 0.06       # se ressème peu — il mise sur les drageons
    fruitier = True                # framboises traçables (maturity_years=0 → dès l'année)
    greffable = True               # ligneux fruitier (cannes) greffable (palette ③, D8) ; Rosaceae → compatible pommier/cerisier
    # Drageon (sprint LUXURIANCE ⑤) : portée TRÈS COURTE (le rejet naît près de la
    # mère → fourré resserré), gate LUMIÈRE au sol (mode héliophile, cf. sim/clonal.py).
    # Cf. table D65 §2.2.
    clonal_mode = "drageon"
    graine_viabilite_ans = 5.0   # zoochorie ① (D42) : Rubus = banque de graines PERSISTANTE [ordre de grandeur]
    clonal_radius_cm = 40.0        # rejet TRÈS court (défaut 60) — le fourré reste dense
    bouturable = True              # bouture de canne ligneuse en hiver (palette ②)
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=6,
        ),
        # Canne dressée fleurie : 1er stade fleuri → table pour les butineurs.
        GrowthStage(
            name="canne", duration_weeks=6, strate="moyenne",
            vigueur_cost=1, canopy_height=120, canopy_radius=25,
            root_radius=35,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Fleurs blanches — nourrit l'abeille"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=5, strate="haute",
            vigueur_cost=0, canopy_height=150, canopy_radius=30,
            effects=[
                {
                    "type": "recolte",
                    "action": "score", "axis": "recolte", "amount": 2,
                    "description": "Récolte de framboises"
                },
            ],
        ),
    ]


class RunningBamboo(Poaceae):
    """
    Phyllostachys sp. — Bambou traçant (Poaceae).
    Graminée géante à RHIZOME TRAÇANT — le démonstrateur EXTRÊME de l'envahissement
    clonal (sprint LUXURIANCE ⑤, absorbe D62). `clonal_mode="rhizome"` : portée
    LONGUE (`clonal_radius_cm=120`, le rhizome file loin de la mère) + gate lumière
    IGNORÉ (réserve souterraine → tolère l'ombre) + cadence rapide (`clonal_interval=3`)
    → une colonie qui court vite, loin, y compris sous canopée. C'est de cette
    combinaison qu'ÉMERGE le caractère envahissant — aucun flag. Son expansion reste
    BORNÉE par le gate de COUVERTURE (tronçon ①, cov ≥ 0.85 = plot saturé) : le champ
    de couverture est son garde-fou, pas une limite scriptée. Strate `haute` (chaumes
    dressés), `silhouette="dressée"`. Anémophile (Poaceae) → aucune retombée butineurs.
    Hérite de la compétition hydrique familiale (Poaceae : racines fibreuses).
    HORS golden → dérive NEUTRE.
    """
    genus = "Phyllostachys"
    name = "Bambou traçant"
    feuillage = "fin"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resistance_ecrasement  = 0.7   # chaume flexible, plie sans casser
    stimulation_ecrasement = 0.5
    rarity = "Établie"
    keywords = ["Structurant", "Envahissant", "Traçant", "Brise-vent"]
    silhouette = "dressée"         # chaumes dressés en bosquet ; HORS golden → neutre
    space_tolerance_weeks = 6      # graminée très tolérante (hérité, robuste)
    life_cycle = "perennial"
    winter_strategy = "evergreen"  # persistant : les chaumes gardent leur feuillage
    deciduous = False
    t_germ_opt = 18.0              # tempéré chaud : lève sur sol réchauffé (fenêtre ③)
    t_germ_tol = 10.0              # tolérante
    foliage_density = 0.55
    longevity_years = 20
    reproduction_rate = 0.02       # floraison/graine rarissime — il mise TOUT sur le rhizome
    # Rhizome TRÈS ENVAHISSANT (sprint LUXURIANCE ⑤) : portée LONGUE, cadence RAPIDE,
    # gate lumière IGNORÉ (rhizome → réserve, tolère l'ombre, cf. sim/clonal.py) → la
    # colonie court vite et loin. BORNÉE par le gate de couverture (tronçon ①), pas par
    # un flag. Cf. table D65 §2.2.
    clonal_mode = "rhizome"
    clonal_radius_cm = 120.0       # porte TRÈS loin (défaut 60) — le rhizome fuse
    clonal_interval = 3            # cadence soutenue (défaut 4) — colonise vite
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=8,
        ),
        # Chaume dressé : vivace (duration 0). Anémophile → PAS d'effet
        # floraison-pollinisateur (aucune retombée butineurs).
        GrowthStage(
            name="chaume", duration_weeks=0, strate="haute",
            vigueur_cost=1, canopy_height=250, canopy_radius=30,
            root_radius=45,
            effects=[],
        ),
    ]


class SweetViolet(Violaceae):
    """
    Viola odorata — Violette odorante (Violaceae).
    Couvre-sol d'OMBRE stolonifère et mellifère PRÉCOCE (sprint LUXURIANCE ⑤, absorbe
    D62). SCIAPHILE : elle prospère SOUS la canopée là où les héliophiles calent —
    ce qui ÉMERGE de la forte tolérance à l'ombre de sa strate `sol` (override
    `shade_tolerance` élevé), pas d'un flag. `clonal_mode="stolon"` : elle tapisse
    par courts stolons rampants — MAIS son gate lumière est le point subtil : le
    stolon exige de la lumière au sol (sim/clonal.py, mode héliophile) alors que la
    plante, elle, vit à l'ombre → elle tapisse surtout aux CLAIRIÈRES et lisières,
    pas au cœur le plus sombre (auto-limitation émergente). Fleurs violettes
    parfumées TRÈS PRÉCOCES (une des premières tables de nectar de l'année),
    `silhouette="tapis"`. HORS golden → dérive NEUTRE.
    """
    genus = "Viola"
    name = "Violette odorante"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.3  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.0          # intermédiaire — petit couvre-sol d'ombre vivace, tenue moyenne
    resistance_ecrasement  = 0.7   # rosette basse plaquée, encaisse le piétinement
    stimulation_ecrasement = 0.4
    rarity = "Établie"
    keywords = ["Mellifère", "Couvre-sol", "Sciaphile", "Précoce"]
    silhouette = "tapis"           # tapis ras de rosettes ; HORS golden → neutre
    shade_tolerance = 1.6          # SCIAPHILE : prospère sous canopée (override strate sol)
    space_tolerance_weeks = 4
    life_cycle = "perennial"
    winter_strategy = "dormant"    # persiste en rosette, repart tôt au printemps
    t_germ_opt = 12.0              # sous-bois frais : lève au frais précoce (fenêtre ③)
    t_germ_tol = 9.0               # moyenne
    bloom_forcing_gdd = 6.0        # PRINTEMPS TRÈS précoce (~S14) : une des 1res tables de nectar (①)
    bloom_duration = 4
    foliage_density = 0.35
    longevity_years = 6
    reproduction_rate = 0.08       # se ressème modérément — complète le tapissage clonal
    # Stolon d'OMBRE (sprint LUXURIANCE ⑤) : portée courte, gate LUMIÈRE au sol (mode
    # héliophile → tapisse aux clairières, cf. sim/clonal.py). Cf. table D65 §2.2.
    clonal_mode = "stolon"
    clonal_radius_cm = 45.0        # stolon court (défaut 60) — la fille s'enracine près
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=2,
        ),
        # Rosette basse fleurie précoce : 1er stade fleuri → table butineurs.
        GrowthStage(
            name="adulte", duration_weeks=0, strate="sol",  # vivace, tapis ras
            vigueur_cost=1, canopy_height=12, canopy_radius=14,
            root_radius=16,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Fleurs violettes parfumées, précoces — nourrit l'abeille"
                },
            ],
        ),
    ]


class Mugwort(Asteraceae):
    """
    Artemisia vulgaris — Armoise commune (Asteraceae).
    VIVACE inhibitrice PUISSANTE (sprint ALLÉLOPATHIE ⑤) : la facette « vivace
    toxique » de l'allélopathie. Ses racines et son feuillage libèrent des lactones
    et terpènes (dont l'absinthine du genre Artemisia) qui « FONT LE VIDE » autour
    d'elle — peu de plantes lèvent à son pied. Émission FORTE (proche du noyer),
    AUTO-TOLÉRANTE (`allelopathie_sensibilite` bas). Anémophile (fleurs verdâtres
    discrètes au vent → aucune retombée butineurs, on N'hérite PAS de la floraison
    mellifère d'Asteraceae : `family_effects` surchargé par la seule injection).
    `archetype=None` → hors WEED_CATALOGUE (posée par le joueur / acquise). Plante
    aromatique médicinale ancienne (« herbe aux cent goûts », veillées de la
    Saint-Jean). HORS scénario golden (jamais semée) → dérive NEUTRE.
    """
    genus = "Artemisia"
    name = "Armoise"
    feuillage = "cireux"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.25         # S — vivace rustique quasi-increvable, souche ligneuse
    resistance_ecrasement  = 0.6   # touffe dressée, repart de la souche
    stimulation_ecrasement = 0.4
    rarity = "Établie"
    keywords = ["Allélopathe", "Vivace", "Aromatique", "Rudérale"]
    space_tolerance_weeks = 5      # robuste, encaisse la compétition
    life_cycle = "perennial"
    winter_strategy = "dormant"
    archetype = None               # PAS une adventice de succession (hors WEED_CATALOGUE)
    pollination_mode = "wind"      # anémophile — capitules verdâtres discrets
    pollination_radius_cm = 300.0
    seed_dispersal = "anemochore"  # akènes légers au vent
    t_germ_opt = 15.0              # rudérale tempérée : lève au frais (fenêtre ③)
    t_germ_tol = 12.0              # large → opportuniste des sols remués
    bloom_forcing_gdd = 180.0      # AUTOMNE (~S33) : jour-court APPROXIMÉ par seuil élevé (①, §2.5)
    bloom_duration = 5
    foliage_density = 0.55
    longevity_years = 10
    reproduction_rate = 0.08
    allelopathie_emission = 0.18     # FORT (lactones/terpènes) — « fait le vide » ; arme l'autotox ④
    allelopathie_sensibilite = 0.05  # AUTO-TOLÉRANTE : ne s'auto-inhibe pas (D2)
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "inject_field",
            "variable": "allelopathie",
            "amount": 0.18,
            "cible": "local",
            "description": "Lactones/terpènes — forte allélopathie (fait le vide)"
        }
    ]
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=4,
        ),
        # Vivace : touffe adulte dressée (duration 0). Anémophile → PAS d'effet
        # floraison-pollinisateur. L'allélopathie vient du family_effects ci-dessus.
        GrowthStage(
            name="adulte", duration_weeks=0, strate="moyenne",
            vigueur_cost=1, canopy_height=110, canopy_radius=35,
            root_radius=45,
            effects=[],
        ),
    ]


class Sphagnum(Sphagnaceae):
    """
    Sphagnum spp. — Sphaigne (Sphagnaceae, mousse des tourbières). L'INGÉNIEUR DU
    MILIEU de la guilde marécageuse (sprint HYDROLOGIE & MARÉCAGES ⑤) : elle ne
    « donne » rien aux plantes — elle TRANSFORME le milieu à son avantage, et la
    tourbière ÉMERGE de ses trois flux (philo #2), tous en `inject_field cible=
    "local"` (route générique), déposés sous le tapis vivant :

      (a) ACIDIFICATION — elle échange des cations contre des ions H⁺ → le pH baisse.
          Petite injection NÉGATIVE hebdomadaire sur `ph` : elle S'ACCUMULE contre la
          dérive très lente du pH (PH_INERTIA=0.02) et se BORNE au plancher PH_MIN=4.0
          du champ — le MÊME clamp que l'acidification du marais (③), donc AUCUN
          double-comptage possible (les deux poussées se plafonnent ensemble à PH_MIN,
          elles ne s'additionnent pas sous le plancher). Elle crée sa tourbière acide.
      (b) RÉTENTION D'EAU — capillarité colossale (une sphaigne retient ~20× son poids
          sec en eau). Petite injection POSITIVE sur `humidite` : le tapis garde le sol
          gorgé (bornée [0,3] par le champ), entretenant la flaque/le marais.
      (c) NÉCROMASSE-TOURBE — sa litière quasi-indécomposable (`litter_tissue="mousse"`,
          decay 0.008) s'accumule à sa mort → la MO grossit → épaisseur/tourbe
          émergentes (aucun code neuf). Antiseptique (phénols) : peu attaquée.

    Strate `sol`, PAS de morphogénèse à segments (bryophyte, modèle minimal : un
    tapis ras). ACIDOPHILE (fenêtre pH basse, comme la myrtille) et hyper-tolérante à
    l'asphyxie (elle FLOTTE quasiment). `archetype=None` → hors WEED_CATALOGUE (posée/
    acquise). Anémophile n/a (spores) : `pollination_mode="self"` (pas de retombée
    butineurs, pas de fleur). HORS scénario smoke (jamais posée) → golden NEUTRE.
    """
    genus = "Sphagnum"
    name = "Sphaigne"
    feuillage = "fin"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    rarity = "Établie"
    keywords = ["Tourbière", "Ingénieur", "Acidophile", "Zone humide"]
    silhouette = "tapis"             # tapis ras de mousse (pur descripteur rendu)
    resilience_base = 1.25          # S — coussin lent et coriace des tourbières
    resistance_ecrasement  = 0.7    # tapis souple, se relève
    stimulation_ecrasement = 0.3
    space_tolerance_weeks = 6       # tapis lent, très tolérant au voisinage
    life_cycle = "perennial"
    winter_strategy = "evergreen"   # mousse persistante (ne largue pas de feuillage)
    archetype = None                # PAS une adventice de succession (hors WEED_CATALOGUE)
    pollination_mode = "self"       # bryophyte (spores) — aucune fleur/butineur
    ph_opt = 4.2                    # ACIDOPHILE STRICTE (tourbière) — la plus basse du catalogue
    ph_tol = 1.0
    asphyxie_tolerance_base = 4.0   # quasi flottante : increvable au sol gorgé (⑤)
    litter_tissue = "mousse"        # nécromasse-TOURBE (flux c) — decay quasi nul
    t_germ_opt = 11.0               # milieu froid et humide
    t_germ_tol = 10.0
    foliage_density = 0.25          # tapis ras, ombre négligeable
    longevity_years = 20
    reproduction_rate = 0.04
    # Trois flux d'INGÉNIEUR déposés sous le tapis vivant (family_effects vide sur
    # Sphagnaceae : toute la signature est ICI, à l'espèce). AMONTS de DÉPART (calibrage
    # F5, overlay pH/humidité) — petits, l'accumulation contre les dérives lentes fait
    # le travail. Golden NEUTRE : aucune sphaigne dans le smoke → aucune injection.
    family_effects = [
        {
            "type": "permanent", "trigger": "weekly",
            "action": "inject_field", "variable": "ph",
            "amount": -0.03, "cible": "local",
            "description": "Échange cationique — acidifie le sol (borné PH_MIN, cf. marais)"
        },
        {
            "type": "permanent", "trigger": "weekly",
            "action": "inject_field", "variable": "humidite",
            "amount": 0.05, "cible": "local",
            "description": "Capillarité de la sphaigne — retient l'eau, entretient le marais"
        },
    ]
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=2, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=1,
        ),
        # Tapis adulte (vivace, duration 0). Empreinte MINIMALE (mousse ras) : hauteur
        # 6 cm, petit rayon de « racines » (rhizoïdes) portant les flux d'ingénieur.
        GrowthStage(
            name="tapis", duration_weeks=0, strate="sol",
            vigueur_cost=0, canopy_height=6, canopy_radius=25,
            root_radius=25, effects=[],
        ),
    ]


class Drosera(Droseraceae):
    """
    Drosera rotundifolia — Rossolis / Drosera (Droseraceae). Le PREMIER
    VÉGÉTAL-PRÉDATEUR du jeu (sprint HYDROLOGIE & MARÉCAGES ⑥) : une petite rosette
    plaquée des TOURBIÈRES ACIDES, dont les feuilles portent des poils rouges gluants
    qui capturent les insectes. Sa niche = le marais acide et pauvre en azote — là où
    la sphaigne (⑤) a fabriqué la tourbe. Deux traits la définissent :

      (a) `carnivore=True` : le hook `sim/engine/carnivore.py` (après `tick_populations`)
          PRÉLÈVE une fraction de la densité `moustique` sur son empreinte foliaire →
          la nuée se raréfie autour d'elle (flux réel, observable, philo #2), et son
          azote vient des proies → elle ÉCHAPPE à la faim d'azote édaphique (le sol
          pauvre ne la bride plus sur N). Elle SURVIT là où une herbacée normale
          carence, sans pousser plus vite (pas de bonus, philo #1).
      (b) ACIDOPHILE STRICTE (`ph_opt=4.2`, comme la sphaigne) + hyper-tolérante à
          l'asphyxie (`asphyxie_tolerance_base=3.0`, ses pieds baignent dans la tourbe
          gorgée).

    Petite fleur blanche entomophile FAIBLE (`bloom_forcing_gdd` estival, rosette
    minuscule → une seule table discrète). `archetype=None` → hors WEED_CATALOGUE
    (posée/acquise, jamais tirée par la succession). HORS scénario smoke (jamais
    posée) → golden NEUTRE.
    """
    genus = "Drosera"
    name = "Rossolis"
    feuillage = "fin"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.1  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    rarity = "Ancienne"                # curiosité rare des tourbières
    keywords = ["Carnivore", "Tourbière", "Acidophile", "Zone humide"]
    silhouette = "tapis"               # rosette plaquée au sol (pur descripteur rendu)
    resilience_base = 1.0              # intermédiaire — petite plante spécialiste, pas coriace
    resistance_ecrasement  = 0.4       # rosette tendre, glu fragile
    stimulation_ecrasement = 0.2
    carnivore = True                   # végétal-prédateur (puits moustique + N interne, ⑥)
    ph_opt = 4.2                       # ACIDOPHILE STRICTE (tourbière), comme la sphaigne
    ph_tol = 1.0
    asphyxie_tolerance_base = 3.0      # pieds dans la tourbe gorgée — increvable au sol noyé
    space_tolerance_weeks = 3
    life_cycle = "perennial"
    winter_strategy = "dormant"        # rosette d'hiver (hibernacle) au ras du sol
    archetype = None                   # PAS une adventice de succession (hors WEED_CATALOGUE)
    t_germ_opt = 11.0                  # milieu froid et humide (tourbière)
    t_germ_tol = 10.0
    bloom_forcing_gdd = 60.0           # hampe florale estivale (~S22) — table discrète
    bloom_duration = 4
    foliage_density = 0.20             # minuscule rosette : ombre négligeable
    longevity_years = 8
    reproduction_rate = 0.04           # graines fines, se ressème peu
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=1,
        ),
        # Rosette adulte fleurie (vivace, duration 0). Empreinte MINIMALE (rosette
        # plaquée) : la hampe florale porte une petite table entomophile.
        GrowthStage(
            name="rosette", duration_weeks=0, strate="sol",
            vigueur_cost=0, canopy_height=10, canopy_radius=12,
            root_radius=12,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Hampe florale blanche discrète — table entomophile faible"
                },
            ],
        ),
    ]
