"""
SYMBIOSE — plants/species/grimpantes.py
Espèces GRIMPANTES du sprint Grimpantes (D49 volet A, tronçon ⑤). Données pures
(niveau 3), s'appuient sur `plants.base`. Deux espèces neuves qui COMPLÈTENT la
démonstration des 3 modes de grimpe — le haricot (`vrille_volubile`) étant déjà
couvert par les Fabaceae de `cultivees.py` :

  - Lierre (Araliaceae, NEUVE) — `mode_grimpe="crampon"` : ses crampons adhésifs
    escaladent même le MUR NU (support « MUR », cf. `world/support.py`).
    SCIAPHILE et sempervirent (feuillage gardé l'hiver, comme les aromatiques).
  - Jasmin (Oleaceae, NEUVE) — `mode_grimpe="sarmenteux"` : ne s'accroche PAS
    seul ; il faut le PALISSER (geste ④) sur un support posé. Mellifère parfumé.

Ces deux familles n'ont AUCUN effet familial propre (pas de flux injecté) → elles
suivent le patron « famille sans base class » des potagères (Apiaceae…) : un
simple attribut `family` sur une classe qui hérite directement de `PlantBase`.
`archetype=None` ⇒ hors WEED_CATALOGUE : jamais tirées par la succession
spontanée, elles vivent au catalogue pour être posées/acquises (magazine).

Toutes les métriques (hauteurs, rayons, gabarits procéduraux, `hauteur_autoportante`)
sont des PLACEHOLDERS de calibrage — ajustées à la maquette F5 (tronçon ⑥).
"""

from __future__ import annotations
from plants.base import GrowthStage, PlantBase


class Ivy(PlantBase):
    """
    Hedera helix — Lierre (Araliaceae).
    Liane ligneuse à CRAMPONS adhésifs : elle tapisse le sol puis, dès qu'elle
    touche une paroi, l'escalade — mur nu compris (le crampon accroche tout, §2).
    SCIAPHILE (`shade_tolerance` > 1) : prospère au pied d'un mur nord ou en
    sous-bois, là où les héliophiles calent. Sempervirente (`winter_strategy=
    "evergreen"`) → ombre non nulle même l'hiver. Sans appui au-delà de
    `hauteur_autoportante`, son apex retombe (affalement géométrique, ①). Sa
    floraison tardive d'automne est une MANNE de nectar pour l'abeille quand tout
    le reste est fané. `archetype=None` ⇒ hors succession spontanée.
    """
    family = "Araliaceae"
    genus = "Hedera"
    name = "Lierre"
    feuillage = "cireux"  # transpiration (D111 ①) : type de feuillage d'espèce
    resilience_base = 1.25         # S — liane ligneuse persistante, extrêmement rustique
    mode_grimpe            = "crampon"   # crampons adhésifs → escalade le mur nu (②)
    hauteur_autoportante   = 15.0        # rampe bas ; au-delà, libre → l'apex retombe (①)
    shade_tolerance        = 1.4         # SCIAPHILE : prospère à l'ombre (pied de mur nord)
    resistance_ecrasement  = 0.7         # liane coriace, repart de la souche
    stimulation_ecrasement = 0.4
    rarity = "Établie"
    keywords = ["Grimpante", "Sempervirent", "Sciaphile", "Mellifère"]
    space_tolerance_weeks = 5            # couvre-sol/mur robuste, encaisse la compétition
    life_cycle = "perennial"
    winter_strategy = "evergreen"        # sempervirent — feuillage gardé l'hiver
    deciduous = False                    # evergreen ⇒ ombre non nulle même en hiver
    archetype = None                     # hors WEED_CATALOGUE (posé/acquis, pas semé)
    t_germ_opt = 15.0                    # tempéré : lève au frais du sous-bois (fenêtre ③)
    t_germ_tol = 10.0                    # tolérant
    foliage_density = 0.60               # feuillage dense et opaque (ombre forte)
    longevity_years = 40                 # liane pérenne très longue
    reproduction_rate = 0.05
    fungal_susceptibility = 0.25
    bouturable = True                    # liane ligneuse : un fragment reprend aisément (palette ②)
    # --- Profil de croissance procédurale (grimpe géométrique ①②) ---
    # PLACEHOLDERS : le lierre monte haut sur un mur mais reste étroit (canopée
    # plaquée). Gabarit calibré à la maquette (⑥).
    procedural_growth = True
    port_archetype    = "fleche"         # une pousse chercheuse d'appui (descriptif)
    max_height_cm     = 300.0            # peut tapisser haut une paroi
    max_extent_cm     = 40.0             # couronne étroite (plaquée au support)
    foliage_halfwidth = 20.0
    organ_site        = "lateral"
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=4,
        ),
        # Rampe au sol tant qu'aucun appui n'est trouvé (sciaphile, couvre-sol).
        GrowthStage(
            name="jeune", duration_weeks=5, strate="sol",
            vigueur_cost=1, effects=[], canopy_height=15, canopy_radius=30,
            root_radius=35,
        ),
        # Accroché → grimpe (strate « grimpante », ②).
        GrowthStage(
            name="adulte", duration_weeks=8, strate="grimpante",
            vigueur_cost=2, canopy_height=200, canopy_radius=30,
            root_radius=45, effects=[],
        ),
        # Sujet âgé : floraison tardive d'automne, nectar rare et précieux.
        GrowthStage(
            name="mature", duration_weeks=0, strate="grimpante",
            vigueur_cost=0, canopy_height=300, canopy_radius=35,
            root_radius=50,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison d'automne — manne de nectar tardive pour l'abeille"
                },
            ],
        ),
    ]


class Jasmine(PlantBase):
    """
    Jasminum officinale — Jasmin (Oleaceae).
    Grimpante SARMENTEUSE : ses tiges souples ne s'agrippent PAS seules — sans
    palissage elles retombent et s'étalent (affalement géométrique, ①). Le SEUL
    canal d'accroche est le geste `palisser` (④), qui l'attache à un support posé.
    C'est LE démonstrateur du palissage. Floraison estivale mellifère et parfumée
    (nectar pour l'abeille et surtout le papillon). `archetype=None` ⇒ hors
    succession spontanée.
    """
    family = "Oleaceae"
    genus = "Jasminum"
    name = "Jasmin"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    resilience_base = 1.0          # intermédiaire — sarment ligneux, mais rameaux tendres au froid
    mode_grimpe            = "sarmenteux"  # ne s'accroche que par palissage (④)
    hauteur_autoportante   = 25.0          # sarments souples : retombent vite sans appui (①)
    resistance_ecrasement  = 0.4           # tige souple, casse mais rejette
    stimulation_ecrasement = 0.3
    rarity = "Établie"
    keywords = ["Grimpante", "Mellifère", "Parfum", "Palissage"]
    space_tolerance_weeks = 3
    life_cycle = "perennial"
    winter_strategy = "dormant"            # semi-caduc → dort l'hiver
    deciduous = True                       # feuillage largué l'hiver
    archetype = None                       # hors WEED_CATALOGUE (posé/acquis, pas semé)
    t_germ_opt = 18.0                      # tempéré-chaud : lève sur sol réchauffé (fenêtre ③)
    t_germ_tol = 9.0                       # moyenne
    foliage_density = 0.45
    longevity_years = 20
    reproduction_rate = 0.06
    fungal_susceptibility = 0.3
    bouturable = True                      # sarment souple : bouture de tige d'été (palette ②)
    # --- Profil de croissance procédurale (grimpe géométrique ①②) ---
    # PLACEHOLDERS : sarments longs et souples qui s'étalent large SANS palissage
    # (max_extent élevé) et montent une fois palissés.
    procedural_growth = True
    port_archetype    = "fleche"           # sarment chercheur (descriptif)
    max_height_cm     = 250.0
    max_extent_cm     = 50.0               # sarments souples qui s'étalent si non palissés
    foliage_halfwidth = 18.0
    organ_site        = "lateral"
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=4,
        ),
        GrowthStage(
            name="jeune", duration_weeks=4, strate="basse",
            vigueur_cost=1, effects=[], canopy_height=25, canopy_radius=30,
            root_radius=30,
        ),
        # Palissé → grimpe (strate « grimpante ») + floraison estivale mellifère.
        GrowthStage(
            name="adulte", duration_weeks=8, strate="grimpante",
            vigueur_cost=2, canopy_height=180, canopy_radius=40,
            root_radius=45,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison parfumée — nectar pour l'abeille et le papillon"
                },
            ],
        ),
        GrowthStage(
            name="mature", duration_weeks=0, strate="grimpante",
            vigueur_cost=0, canopy_height=250, canopy_radius=45,
            root_radius=50, effects=[],
        ),
    ]
