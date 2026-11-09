"""
SYMBIOSE — plants/perennials/rives.py
Les arbres des milieux humides : aulne, saule.
"""

from __future__ import annotations
from plants.perennials.base import PerennialWoody


# ---------------------------------------------------------------------------
# AULNE (sprint HYDROLOGIE & MARÉCAGES ⑤) — arbre hélophyte fixateur d'azote
# ---------------------------------------------------------------------------

class Alder(PerennialWoody):
    """
    Alnus glutinosa — Aulne glutineux (Betulaceae, comme bouleau/charme).
    ARBRE DES BERGES qui « pousse les pieds dans l'eau » : la vedette de la guilde
    marécageuse. Deux signatures :

      • FIXATION D'AZOTE ACTINORHIZIENNE — comme la légumineuse Medicago mais via la
        bactérie FRANKIA (nodosités racinaires), pas le Rhizobium. Mécanisme MOTEUR
        IDENTIQUE : un `family_effect inject_field variable="n" cible="local"` enrichit
        le N du sol sous son empreinte racinaire (route générique, cf. ortie/minette).
        C'est un FLUX (philo #2) : l'aulne ne « booste » pas ses voisines, il
        ENRICHIT le milieu — d'où sa valeur de pionnier améliorateur des sols pauvres
        et gorgés, là où rien ne fixe l'azote.
      • TOLÉRANCE À L'ASPHYXIE constitutive ÉLEVÉE (`asphyxie_tolerance_base=3.0`) :
        aérenchyme + racines adventices → il survit au sol gorgé qui NOIE le pommier
        (§2.3 asphyxie, palier 2). Émergent : posé dans une cuvette marécageuse, il
        tient là où un fruitier de terrain sec dépérit.

    Anémophile (chatons pendants), caduc, croissance rapide de pionnier, vie moyenne.
    Fenêtre pH TOLÉRANTE de l'acide (tourbière) sans être acidophile strict. HORS
    scénario smoke (`archetype=None`, posé/acquis) → golden NEUTRE.
    """
    family = "Betulaceae"
    genus  = "Alnus"
    name   = "Aulne"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    shade_tolerance = 0.85  # D111 ②ter : pionnier de berge, héliophile modéré (≠ défaut strate haute 0,90)
    rarity = "Établie"
    keywords = ["Berge", "Fixatrice N₂", "Pionnière", "Zone humide"]
    foliage_density = 0.55           # houppier moyen, ombre légère de ripisylve
    fragilite_bois = 1.2           # D111 ②bis : bois tendre
    pollination_mode = "wind"        # anémophile (chatons)
    pollination_radius_cm = 500.0
    reproduction_rate = 0.15         # petits strobiles ligneux, graines flottantes
    seed_dispersal = "anemochore"    # graine légère à flotteurs (vent + eau)
    ph_opt = 5.8                     # tolère l'acide des berges/tourbières (≠ strict)
    ph_tol = 1.6                     # fenêtre assez large
    asphyxie_tolerance_base = 3.0    # HÉLOPHYTE : plie où le pommier se noie (⑤)
    t_germ_opt = 12.0               # lève au frais des sols humides de printemps
    t_germ_tol = 11.0
    longevity_years = 100
    rejet_souche = 0.8       # souche ② (D130) : rejette fort de souche (aulnaies traitées en taillis) [ordre de grandeur]
    maturity_years = 10
    bouturable = True                # rameau de saule/aulne piqué au bord de l'eau reprend
    girth_max_cm = 16.0              # tronc mûr ~16 cm (pipe model, procédural)
    age_curve = [(0, 40, 20), (5, 350, 120), (10, 700, 200),
                 (20, 1200, 320), (50, 2000, 450), (100, 2500, 550)]
    # --- Croissance procédurale (AUTOMNE VISIBLE ②) — conique de berge -------------
    # Fiche : 650/170 à l'an 10. Pousse VITE (pionnier), tronc suivi jusqu'à la cime,
    # branches courtes à 55° : dominance haute + release_scale long, latéraux après
    # l'an 5 (même coût assumé que le bouleau). Les family_effects (fixation N₂ Frankia)
    # et asphyxie_tolerance_base sont INDÉPENDANTS de la morphologie → INCHANGÉS (rôle
    # hydro D61 préservé, vérifié en test). HORS golden.
    procedural_growth   = True
    port_archetype      = "conique"
    growth_speed        = 1.54        # pionnier rapide
    apical_dominance_base = 2.4
    auxin_release_scale = 800.0       # tient la flèche sans saturer le cap segments
    branch_angle        = 55.0
    max_height_cm       = 1500.0
    max_extent_cm       = 350.0
    foliage_halfwidth   = 55.0        # houppier élancé cr~170 ; racines via spread latéral
    # Fixation N₂ actinorhizienne (Frankia) — même route générique que l'azote de
    # l'ortie/minette. `amount` légèrement au-dessus de la minette (0.04) : l'aulne
    # est un gros améliorateur ligneux. Réparti sur l'empreinte racinaire (cible
    # "local", partagé par `inject_field`). Golden NEUTRE (jamais dans le smoke).
    family_effects = [
        {
            "type": "permanent", "trigger": "weekly",
            "action": "inject_field", "variable": "n",
            "amount": 0.05, "cible": "local",
            "description": "Fixation N₂ actinorhizienne (Frankia) — enrichit le sol gorgé"
        }
    ]


# ---------------------------------------------------------------------------
# SAULE (sprint PÉRIPHÉRIE ⑥, décision D-5) — l'arbre de la TROGNE
# ---------------------------------------------------------------------------

class Willow(PerennialWoody):
    """
    Salix alba — Saule blanc (Salicaceae, famille NEUVE déclarée à l'espèce comme
    l'ont fait FirTree pour Pinaceae et BirchTree pour Betulaceae).

    SEULE espèce ajoutée par le sprint PÉRIPHÉRIE (règle « le catalogue grandit avec
    les idées », application signalée) : le sprint invente le geste `eteter` et il lui
    fallait son incarnation. Le saule têtard EST la trogne — l'arbre que l'on coupe
    pour qu'il dure. Trois signatures, toutes déjà portées par des leviers existants :

      • REJET DE SOUCHE — il figure dans `fields/peripherie.ESSENCES_QUI_REJETTENT`
        (avec le charme et l'aulne) : recépé, il ne meurt pas, il rajeunit. C'est la
        moitié « vivante » de l'asymétrie que le joueur découvre en coupant.
      • BOUTURE SPONTANÉE (`bouturable`) — un rameau piqué en terre humide reprend.
        Croise l'événement rare « bouture » et le canal d'acquisition #2 déjà en place ;
        c'est aussi pourquoi le bocage se plantait sans pépinière.
      • RIPISYLVE — hélophyte (`asphyxie_tolerance_base`, comme l'aulne) : il pousse
        les pieds dans l'eau, d'où sa place dans `ESSENCES_RIPISYLVE` (un secteur de
        forêt au bord d'une rivière tire saule ou aulne).

    Et une quatrième, gratuite : il fleurit AVANT de feuiller (`bloom_forcing_gdd` très
    bas), en chatons nectarifères — la PREMIÈRE table des butineurs au sortir de
    l'hiver, quand rien d'autre n'est ouvert (entomophile, ≠ l'aulne anémophile).

    Croissance la plus RAPIDE du catalogue ligneux, port PLEUREUR (le levier
    `gravitropism_gain` que le bouleau avait ouvert « pour préparer le saule »), vie
    brève pour un arbre — mais un saule ÉTÊTÉ vit bien plus vieux qu'un saule libre.
    HORS scénario smoke (jamais semé dans `build_world`) → golden NEUTRE.
    """
    family = "Salicaceae"
    genus  = "Salix"
    name   = "Saule"
    feuillage = "fin"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.75  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    shade_tolerance = 0.80  # D111 ②ter : pionnier héliophile (≠ défaut strate haute 0,90)
    rarity = "Établie"
    keywords = ["Berge", "Trogne", "Bouture", "Mellifère précoce"]
    foliage_density = 0.50           # feuillage fin et lâche → ombre légère de bord d'eau
    fragilite_bois = 1.6           # D111 ②bis : bois mou qui casse net (saule)
    pollination_mode = "insect"      # chatons NECTARIFÈRES (≠ aulne/bouleau anémophiles)
    reproduction_rate = 0.22         # graines cotonneuses innombrables, viabilité très courte
    seed_dispersal = "anemochore"    # aigrette de coton (vent + eau)
    ph_opt = 6.5                     # indifférent, tolère du frais au neutre
    ph_tol = 1.5
    asphyxie_tolerance_base = 3.0    # HÉLOPHYTE comme l'aulne : tient le sol gorgé
    t_germ_opt = 12.0                # lève au frais des berges de printemps
    t_germ_tol = 10.0
    longevity_years = 80
    rejet_souche = 0.8       # souche ② (D130) : rejet de souche et bouture proverbiaux (saule têtard, osier) [ordre de grandeur]
    maturity_years = 5
    bouturable = True                # bouture PROVERBIALE : un rameau piqué reprend seul
    bloom_forcing_gdd = 4.0          # fleurit AVANT les feuilles (~fin d'hiver) : 1ʳᵉ table
    bloom_duration = 3               # chatons brefs
    girth_max_cm = 22.0              # fût épais (une trogne épaissit) ; placeholder → F5
    age_curve = [(0, 50, 25), (5, 600, 220), (10, 1100, 380),
                 (20, 1700, 520), (50, 2200, 650), (80, 2400, 700)]
    # --- Croissance procédurale (AUTOMNE VISIBLE ②) — grande tête ample et souple ---
    # Fiche : 800/300 à l'an 10, le plus rapide du catalogue. Saule blanc, pas pleureur :
    # `gravitropism_gain` < bouleau, extrémités retombantes seulement (ex 1.4).
    # Le saule n'est semé nulle part (ni golden, ni monde de démo) : banc seul.
    procedural_growth   = True
    port_archetype      = "arrondi_souple"
    growth_speed        = 1.89       # le plus rapide du catalogue ligneux
    max_height_cm       = 1500.0
    max_extent_cm       = 600.0
    apical_dominance_base = 2.8
    auxin_release_scale = 300.0      # s'ouvre tôt en houppier ample
    branch_angle        = 60.0
    foliage_halfwidth   = 100.0      # houppier lâche + racines multi-plots (survie)
    gravitropism_gain   = 0.8        # extrémités retombantes (calibrer au F5)
