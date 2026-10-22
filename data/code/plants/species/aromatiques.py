"""
SYMBIOSE — plants/species/aromatiques.py
Aromatiques persistantes (Lamiaceae) : Thym et Lavande. Données pures (niveau 3),
s'appuient sur `plants.base`.

Concept distinct des `compagnes` (annuelles attire-auxiliaires) : ce sont des
sous-arbrisseaux VIVACES et EVERGREEN (feuillage conservé l'hiver). Elles
exercent pour la première fois le chemin `winter_strategy="evergreen"` du moteur
(sim/engine/mortalite.py) : à l'hiver elles ne meurent NI n'entrent en dormance
profonde — juste une légère réduction métabolique (coussin de thym vert sous le
gel). Famille Lamiaceae ⇒ héritent gratis de la répulsion familiale des nuisibles
au voisinage (family_effects) ET nourrissent fort abeille/papillon via les tables
`_ATTRACT_*` de population.py, dès lors qu'elles posent la rondelle
`pollinisateur` à la floraison.
"""

from __future__ import annotations
from plants.base import GrowthStage, Lamiaceae


class Mint(Lamiaceae):
    """
    Mentha sp. — Menthe (Lamiaceae).
    Aromatique vivace à RHIZOME ENVAHISSANT : loin de tapisser doucement comme le
    trèfle, elle lance des rhizomes traçants qui colonisent vite et loin. Illustre
    le REVERS du clonal (sprint LUXURIANCE ④, absorbe D62) : `clonal_mode="rhizome"`
    tolère l'ombre (réserve souterraine → gate lumière IGNORÉ dans sim/clonal.py) et
    porte loin (`clonal_radius_cm` élevé) à cadence rapide → son caractère
    « envahissant à surveiller » ÉMERGE de la mécanique, sans aucun drapeau. Mellifère
    à la floraison, elle nourrit l'abeille comme ses sœurs Lamiacées. HORS golden.
    """
    genus = "Mentha"
    name = "Menthe"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.65  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.25         # S — vivace robuste, repart du rhizome après un coup
    t_germ_opt = 15.0              # tempérée : lève au frais du printemps (fenêtre ③)
    t_germ_tol = 10.0              # tolérante
    resistance_ecrasement  = 0.7   # touffe basse qui repart du rhizome après piétinement
    stimulation_ecrasement = 0.5
    rarity = "Établie"
    keywords = ["Aromatique", "Mellifère", "Couvre-sol", "Envahissante"]
    silhouette = "touffe"          # touffe dressée feuillue ; HORS golden → neutre
    space_tolerance_weeks = 5      # très tolérante, robuste
    life_cycle = "perennial"
    winter_strategy = "dormant"    # disparaît en surface l'hiver, repart du rhizome
    foliage_density = 0.45
    longevity_years = 10
    reproduction_rate = 0.10       # se ressème peu — elle mise sur le rhizome
    fungal_susceptibility = 0.2
    # Rhizome ENVAHISSANT (sprint LUXURIANCE ④) : portée LONGUE, cadence RAPIDE, et
    # gate lumière IGNORÉ (rhizome → réserve souterraine, tolère l'ombre, cf.
    # sim/clonal.py) → la colonie court vite et loin, y compris sous canopée. C'est
    # de là qu'émerge le caractère envahissant, pas d'un flag. Cf. table D65 §2.2.
    clonal_mode = "rhizome"
    clonal_radius_cm = 90.0        # porte loin (défaut 60) — le rhizome file
    clonal_interval = 3            # cadence soutenue (défaut 4) — colonise vite
    bouturable = True              # bouture en eau proverbiale : un brin repart tout seul (palette ②)
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=3,
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="basse",  # vivace
            vigueur_cost=1, canopy_height=30, canopy_radius=22,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison mellifère — nourrit l'abeille"
                },
            ],
        ),
    ]


class Thyme(Lamiaceae):
    """
    Thymus vulgaris — Thym (Lamiaceae).
    Sous-arbrisseau coussin, persistant (evergreen) et mellifère. Couvre-sol
    ligneux qui encaisse le piétinement (résistance élevée à l'écrasement) et
    nourrit l'abeille à la floraison. Vivace longue, ressemis modéré.
    """
    genus = "Thymus"
    name = "Thym"
    ligneux = True        # D111 ②bis : sous-arbrisseau — bois sec de la base, largué l'hiver
    bois_chute_cm3 = 40.0
    bois_chute_semaine = 48
    feuillage = "cireux"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.8  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.25         # S — coussin ligneux de garrigue, très coriace
    hail_resistance_base = 1.3     # feuilles minuscules et coriaces — insensibles à la grêle
    ph_opt = 7.4                   # calciphile : prospère sur sol calcaire (garrigue) — fenêtre ⑤
    ph_tol = 1.1
    t_germ_opt = 18.0              # méditerranéenne : lève sur sol réchauffé de la garrigue (③)
    t_germ_tol = 8.0               # moyenne
    resistance_ecrasement  = 0.8   # coussin ligneux : encaisse le piétinement (volet 2 §4)
    stimulation_ecrasement = 0.5
    rarity = "Établie"
    keywords = ["Aromatique", "Mellifère", "Médicinale", "Couvre-sol"]
    space_tolerance_weeks = 4
    life_cycle = "perennial"
    winter_strategy = "evergreen"  # PREMIER porteur de ce chemin — feuillage gardé l'hiver
    deciduous = False              # evergreen ⇒ ombre non nulle même en hiver
    foliage_density = 0.35
    bouturable = True              # sous-arbrisseau : bouture de tige semi-ligneuse (palette ②)
    longevity_years = 8
    reproduction_rate = 0.10
    fungal_susceptibility = 0.2    # aromatique — peu sensible
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=3,
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="basse",  # vivace
            vigueur_cost=1, canopy_height=25, canopy_radius=25,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison mellifère — nourrit l'abeille"
                },
            ],
        ),
    ]


class Lavender(Lamiaceae):
    """
    Lavandula angustifolia — Lavande (Lamiaceae).
    Sous-arbrisseau structurant, persistant (evergreen). Plus haute que le thym,
    elle organise l'espace en strate basse-moyenne et nourrit abeille comme
    papillon à la floraison. Vivace très longue, ressemis faible.
    """
    genus = "Lavandula"
    name = "Lavande"
    ligneux = True        # D111 ②bis : sous-arbrisseau — bois sec de la base, largué l'hiver
    bois_chute_cm3 = 80.0
    bois_chute_semaine = 48
    feuillage = "cireux"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.85  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    resilience_base = 1.25         # S — sous-arbrisseau ligneux méditerranéen, rustique
    hail_resistance_base = 1.3     # feuillage étroit argenté — la grêle glisse
    ph_opt = 7.4                   # calciphile : terrain sec et calcaire — fenêtre ⑤
    ph_tol = 1.1
    t_germ_opt = 18.0              # méditerranéenne : lève sur sol chaud et sec (③)
    t_germ_tol = 8.0               # moyenne
    resistance_ecrasement  = 0.6   # touffe ligneuse, plie sans casser (volet 2 §4)
    stimulation_ecrasement = 0.4
    rarity = "Établie"
    keywords = ["Aromatique", "Mellifère", "Structurante", "Médicinale"]
    space_tolerance_weeks = 4
    life_cycle = "perennial"
    winter_strategy = "evergreen"
    deciduous = False
    foliage_density = 0.45
    longevity_years = 12
    reproduction_rate = 0.08
    fungal_susceptibility = 0.2
    bouturable = True              # bouture d'aoûtement classique du jardinier (palette ②)
    growth_stages = [
        GrowthStage(
            name="semis", duration_weeks=3, strate="sol",
            vigueur_cost=0, effects=[], canopy_height=4,
        ),
        GrowthStage(
            name="adulte", duration_weeks=0, strate="basse",  # vivace
            vigueur_cost=1, canopy_height=50, canopy_radius=40,
            effects=[
                {
                    "type": "floraison",
                    "action": "add_rondelle", "variable": "pollinisateur",
                    "amount": 1,
                    "description": "Floraison mellifère — abeille et papillon"
                },
            ],
        ),
    ]
