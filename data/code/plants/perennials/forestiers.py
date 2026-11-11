"""
SYMBIOSE — plants/perennials/forestiers.py
Les arbres de forêt : chêne, hêtre, bouleau, charme, sapin ; et le noisetier
(arbuste de haie et de sous-bois, zoochorie ③).
"""

from __future__ import annotations
from plants.perennials.base import PerennialWoody


class OakTree(PerennialWoody):
    family = "Fagaceae"
    genus  = "Quercus"
    name   = "Chêne"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    shade_tolerance = 0.90  # D111 ②ter : intermédiaire (jeune : supporte une ombre légère) (= défaut strate haute, explicité)
    rarity = "Sentinelle"
    keywords = ["Lisière", "Sujet structurant", "Centenaire"]
    foliage_density = 0.75
    fragilite_bois = 0.6           # D111 ②bis : bois dur, branches solides
    pollination_mode = "wind"        # anémophile (chatons)
    pollination_radius_cm = 800.0
    reproduction_rate = 0.08   # glandée (mast) rare — inerte depuis la zoochorie ② (relève par les glands)
    # GLANDS traçables (zoochorie ②, D42) : la relève naît des glands qui tombent.
    # Le moteur noue le chêne à la fanaison, ~wiy 21 [1 scénario, seed 42] : 7 semaines
    # → gland mûr wiy 28 (début oct.), tombé wiy ~31 (mi-oct.). À 15 il tombait wiy 40.
    # Chêne de jardin (~11 m) : ~2 000 glands une bonne année [odg] ; ~25 apex →
    # 80 par site. Gland ~3 g de MS → 0,012 (1 unité ≈ 250 g de MS) [odg].
    # Anémophile : la dose vient du panache des AUTRES chênes (`anemophilie`) —
    # un chêne isolé peut ne rien nouer, c'est le modèle.
    fruitier = True
    fruit_semaines_maturation = 7
    fruits_par_site = 80
    fruit_masse     = 0.012
    glandee_periode_ans = 4.0   # glandée forte ~1 an sur 4 [odg]
    mange_par = ("geai", "ecureuil")   # zoochorie ⑤ : cueilli sur l'arbre, caché, parfois oublié
    longevity_years = 500
    rejet_souche = 0.8       # souche ② (D130) : essence de taillis-sous-futaie classique : la souche recépée rejette fort [ordre de grandeur]
    maturity_years = 25
    girth_max_cm = 40.0        # tronc mûr ~40 cm (pipe model, procédural)
    age_curve = [(0, 30, 20), (5, 200, 150), (10, 400, 300),
                 (20, 700, 450), (50, 1500, 800), (100, 3000, 1200)]
    # --- Croissance procédurale (AUTOMNE VISIBLE ②) — étalé tortueux ---------------
    # Fiche : 400/280 à l'an 10, plus large et plus rapide que le réel. Pas de poteau :
    # le relâchement COURT (250) ouvre la couronne dès l'an 4-5 malgré une dominance
    # haute, qui étage les charpentières sur un tronc court. Gabarit à l'échelle du
    # jardin (11 m × 5,5 m). Angle 75° : branches maîtresses presque à plat. HORS golden.
    procedural_growth   = True
    port_archetype      = "etale_tortueux"
    growth_speed        = 0.95
    apical_dominance_base = 2.8
    auxin_release_scale = 250.0
    branch_angle        = 75.0
    max_height_cm       = 1100.0
    max_extent_cm       = 550.0
    foliage_halfwidth   = 55.0      # couronne ~280, portée par les branches


# ---------------------------------------------------------------------------
# 3 ESSENCES FORESTIÈRES NORMANDES (sprint RENDU AMBIANCE T1, D58) — silhouettes
# du décor (T5) + acquisition future canal #3 (friche). CONTENU pur : pas de
# mécanique neuve, gabarit = OakTree. HORS scénario smoke → golden NEUTRE.
# ---------------------------------------------------------------------------

class BeechTree(PerennialWoody):
    """
    Fagus sylvatica — Hêtre (Fagaceae, comme le chêne). Grand arbre de la hêtraie
    cathédrale : port OVOÏDE dense, houppier haut et fermé qui fait une ombre
    profonde (foliage_density élevée). Anémophile. Stature grande mais un peu en
    deçà du chêne (adulte ~2500-3000 cm), longévité séculaire.
    """
    family = "Fagaceae"
    genus  = "Fagus"
    name   = "Hêtre"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    shade_tolerance = 1.30  # D111 ②ter : sciaphile (l'arbre d'ombre par excellence) (≠ défaut strate haute 0,90)
    rarity = "Climacique"
    keywords = ["Lisière", "Ombre dense", "Structurant"]
    foliage_density = 0.85            # houppier fermé → ombre profonde de hêtraie
    fragilite_bois = 0.7           # D111 ②bis : bois dur
    pollination_mode = "wind"        # anémophile (chatons)
    pollination_radius_cm = 700.0
    reproduction_rate = 0.08         # faînée (mast) irrégulière — inerte depuis la zoochorie ②
    # FAÎNES traçables (zoochorie ②, D42). Nouaison ~wiy 21 au moteur [1 scénario] →
    # 7 semaines : faîne mûre début oct., tombée mi-oct.
    # Hêtre de jardin : quelques milliers de faînes une bonne année [odg] ; ~25 apex
    # → 150 par site. Faîne ~0,25 g de MS (+ cupule) → 0,002 (1 unité ≈ 250 g) [odg].
    fruitier = True
    fruit_semaines_maturation = 7
    fruits_par_site = 150
    fruit_masse     = 0.002
    glandee_periode_ans = 6.0   # faînée forte ~1 an sur 6 [odg]
    mange_par = ("geai", "ecureuil")   # zoochorie ⑤ : cueilli sur l'arbre, caché, parfois oublié
    longevity_years = 300
    rejet_souche = 0.2       # souche ② (D130) : rejette mal de souche — on recèpe un charme, pas un hêtre [ordre de grandeur]
    maturity_years = 30
    girth_max_cm = 35.0        # tronc mûr ~35 cm (pipe model, procédural)
    age_curve = [(0, 30, 18), (5, 200, 130), (10, 400, 260),
                 (20, 700, 400), (50, 1500, 650), (100, 2800, 950)]
    # --- Croissance procédurale (AUTOMNE VISIBLE ②) — ovoïde dense -----------------
    # Fiche : 400/220 à l'an 10. Branches montantes (55°). Gabarit à l'échelle du jardin
    # (12 m × 5 m). HORS golden.
    procedural_growth   = True
    port_archetype      = "ovoide_dense"
    growth_speed        = 0.95
    apical_dominance_base = 1.4
    auxin_release_scale = 400.0
    branch_angle        = 55.0
    max_height_cm       = 1200.0
    max_extent_cm       = 500.0
    foliage_halfwidth   = 60.0      # houppier ~220, porté par les branches


class BirchTree(PerennialWoody):
    """
    Betula pendula — Bouleau (Betulaceae, famille NEUVE déclarée à l'espèce comme
    l'a fait FirTree pour Pinaceae). PIONNIER de lisière : croissance rapide,
    stature moyenne (~1500-2000 cm), houppier LÉGER et clairsemé (foliage_density
    faible → ombre légère, sous-bois clair), écorce blanche, port élancé pleureur.
    Vie brève pour un arbre.
    """
    family = "Betulaceae"
    genus  = "Betula"
    name   = "Bouleau"
    feuillage = "fin"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    shade_tolerance = 0.75  # D111 ②ter : héliophile pionnier (le plus exigeant en lumière) (≠ défaut strate haute 0,90)
    rarity = "Établie"
    keywords = ["Pionnière", "Lisière", "Ombre légère"]
    foliage_density = 0.45           # houppier léger → sous-bois clair
    fragilite_bois = 1.5           # D111 ②bis : bois cassant, branches fines
    pollination_mode = "wind"        # anémophile (chatons)
    pollination_radius_cm = 600.0
    reproduction_rate = 0.20         # graines ailées abondantes, dispersion large
    longevity_years = 90
    rejet_souche = 0.2       # souche ② (D130) : rejette faiblement, souche de courte vie ; se régénère surtout par graine [ordre de grandeur]
    maturity_years = 10
    girth_max_cm = 14.0        # tronc mûr ~14 cm (pipe model, procédural) ; placeholder → F5
    age_curve = [(0, 40, 15), (5, 400, 120), (10, 800, 200),
                 (20, 1300, 300), (50, 1800, 420), (90, 2000, 480)]
    # --- Croissance procédurale (D91 ③) — pionnier élancé + port PLEUREUR ------------
    # Betula pendula : flèche DRESSÉE (leader net) + rameaux DISTAUX qui RETOMBENT
    # (levier gravitropique `gravitropism_gain`). Fiche : 750/180 à l'an 10. Leader
    # tenu par une dominance haute (2.8) + un release_scale long (800) : « pionnier
    # rapide » se lit sur la VITESSE, pas sur un étalement précoce. Coût assumé : les
    # latéraux n'arrivent qu'après l'an 5 (plus tôt, à cette vitesse, ils dépassent
    # le rayon de la fiche). Angle 60° + extension 2,5 m : le gain ploie les rameaux
    # dès l'an 10 (il croît avec l'éloignement rapporté à `max_extent_cm`). HORS golden.
    procedural_growth   = True
    port_archetype      = "dresse_pleureur"
    growth_speed        = 1.78      # pionnier rapide
    max_height_cm       = 1500.0
    max_extent_cm       = 250.0     # houppier LÉGER, élancé (plus étroit qu'un grand feuillu)
    apical_dominance_base = 2.8     # flèche élancée — leader net, houppier resserré
    auxin_release_scale = 800.0     # leader dressé longtemps (élancé, ≠ étalement précoce)
    branch_angle        = 60.0
    foliage_halfwidth   = 50.0      # NOTE hydrique : bouleau grêle = LE plus exposé
                                    # (root_r = canopy_r), à surveiller sur sable (mesuré
                                    # dans le monde de démo, cf. apres_port.md).
    gravitropism_gain   = 1.0       # rameaux distaux PENDANTS (Betula pendula) ; SEULE espèce
                                    # à régler ce levier (prépare le saule D23) — calibrer F5.


class HornbeamTree(PerennialWoody):
    """
    Carpinus betulus — Charme (Betulaceae, comme le bouleau). Arbre du BOCAGE au
    bois très dur, tronc CANNELÉ sinueux (« musclé »). Stature moyenne, houppier
    de densité moyenne, longévité intermédiaire. Supporte bien la taille (haies
    bocagères, charmilles) — mais ici, contenu de catalogue, pas de mécanique.
    """
    family = "Betulaceae"
    genus  = "Carpinus"
    name   = "Charme"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    shade_tolerance = 1.15  # D111 ②ter : semi-sciaphile (sous-étage de chênaie) (≠ défaut strate haute 0,90)
    rarity = "Établie"
    keywords = ["Bocage", "Haie", "Structurant"]
    foliage_density = 0.65           # houppier moyen
    fragilite_bois = 0.6           # D111 ②bis : bois très dur (« bois de fer »)
    pollination_mode = "wind"        # anémophile (chatons)
    pollination_radius_cm = 550.0
    reproduction_rate = 0.12         # samares en grappes
    longevity_years = 150
    rejet_souche = 0.8       # souche ② (D130) : l'essence de taillis par excellence (charmille, cépées) [ordre de grandeur]
    maturity_years = 15
    girth_max_cm = 18.0        # tronc mûr ~18 cm (pipe model, procédural)
    age_curve = [(0, 40, 20), (5, 250, 120), (10, 500, 220),
                 (20, 900, 340), (50, 1500, 520), (100, 2000, 650)]
    # --- Croissance procédurale (AUTOMNE VISIBLE ②) — ovoïde régulier du bocage ----
    # Fiche : 450/220 à l'an 10. Ramure fine et serrée, branches à 50°. Gabarit à
    # l'échelle du jardin (12 m × 5 m). HORS golden.
    procedural_growth   = True
    port_archetype      = "ovoide"
    growth_speed        = 1.07
    apical_dominance_base = 1.6
    auxin_release_scale = 400.0
    branch_angle        = 50.0
    max_height_cm       = 1200.0
    max_extent_cm       = 500.0
    foliage_halfwidth   = 60.0      # ovoïde ~220, porté par les branches


# ---------------------------------------------------------------------------
# ARBUSTE DE HAIE ET DE SOUS-BOIS (sprint ZOOCHORIE ③, D42) — l'espèce des caches
# d'écureuil, de mulot et de geai. Ajout « le catalogue grandit avec les idées ».
# ---------------------------------------------------------------------------

class HazelTree(PerennialWoody):
    """
    Corylus avellana — Noisetier, coudrier (Betulaceae, comme le bouleau et le
    charme). Arbuste en CÉPÉE de 4-6 m, des lisières et des sous-bois clairs.
    Trois signatures, toutes portées par des leviers existants :

      • TAILLIS — `rejet_souche` fort : recépé tous les 7-10 ans, il repart de souche
        (la souche vit bien plus longtemps que les tiges).
      • CHATONS PRÉCOCES — anémophile, il fleurit le premier de l'année. Limite du
        moteur : le forçage floral repart à 0 à l'équinoxe (wiy 1, `floraison.py`),
        donc AUCUNE espèce ne peut fleurir avant fin mars ; seuil minimal → il ouvre
        dès la 1ʳᵉ semaine du printemps (le réel : février). Pas de nectar ; le pollen
        offert aux butineurs n'a pas de canal par espèce au moteur (≠ `pollen_vibre`,
        par famille et réservé au bourdon) → noté, pas inventé.
      • NOISETTES traçables (`fruitier`) : nourriture du geai, de l'écureuil, du mulot
        (disperseurs ④-⑥) ; tombées, elles sèment (`recrue_par_fruits`, unifié ②).
    HORS scénario smoke et hors `full` → golden NEUTRE.
    """
    family = "Betulaceae"
    genus  = "Corylus"
    name   = "Noisetier"
    feuillage = "moyen"  # transpiration (D111 ①) : grandes feuilles rondes, molles
    nectar = 0.0         # anémophile : aucun nectar (D111 ⑦)
    shade_tolerance = 1.05  # D111 ②ter : semi-sciaphile (sous-bois clair, lisière) (≠ défaut 0,90)
    rarity = "Établie"
    keywords = ["Haie", "Lisière", "Taillis", "Noisettes"]
    foliage_density = 0.70           # cépée feuillue, ombre assez dense en été
    fragilite_bois = 1.0           # D111 ②bis : bois souple (on en tresse les gaules)
    pollination_mode = "wind"        # chatons mâles au vent, fleurs femelles minuscules
    pollination_radius_cm = 500.0
    reproduction_rate = 0.08         # inerte : la relève passe par les noisettes (②)
    # Chatons au tout début du printemps du moteur (cf. docstring). 1,0 °C·sem : franchi
    # dès la 1ʳᵉ semaine douce après l'équinoxe ; un gène tardif (σ ≈ 0,1) le recule
    # de ~2 sem. Le saule (4,0) ouvre juste après.
    bloom_forcing_gdd = 1.0
    bloom_duration = 3               # chatons qui pendent ~3 semaines [odg]
    # NOISETTES traçables. Noisetier de haie : ~1-2 kg de noisettes une bonne année,
    # soit ~1 000 fruits de ~1,5 g [odg] ; ~40-45 sites à 10 ans (bancs houppiers et
    # foret_ports, [1 forme chacun]) → 25 par site (~1 100 fruits une année forte). Noisette ~1,5 g de MS
    # (coque comprise) → 0,006 (1 unité ≈ 250 g de MS) [odg]. Nouaison à la fanaison des
    # chatons (~wiy 4-5) ; 18 sem → mûre début septembre, tombée (×1,3) vers la mi-octobre.
    fruitier = True
    fruit_semaines_maturation = 18
    fruits_par_site = 25
    fruit_masse     = 0.006
    graine_viabilite_ans = 1.0       # la noisette ne se garde pas : levée l'an suivant ou rien
    glandee_periode_ans = 2.0        # alternance forte/maigre ~1 an sur 2 [odg]
    mange_par = ("geai", "ecureuil")   # zoochorie ⑤ : cueilli sur l'arbre, caché, parfois oublié
    longevity_years = 80             # les tiges ; la souche, recépée, bien plus
    rejet_souche = 0.9       # souche ② (D130) : le taillis par excellence, recépé tous les 7-10 ans [ordre de grandeur]
    maturity_years = 8
    girth_max_cm = 8.0         # tige mûre ~8 cm (cépée de perches minces) ; placeholder → F5
    age_curve = [(0, 30, 15), (5, 250, 120), (10, 400, 200),
                 (20, 500, 250), (50, 550, 280), (80, 550, 280)]
    # --- Croissance procédurale — cépée, approchée par `buissonnant` -----------------
    # Pas d'archétype multi-tiges au moteur (MONO-COLLET, cf. figuier) : le port le plus
    # proche est le BUISSONNANT du figuier — dominance apicale modérée, débourrement bas,
    # couronne ouverte tôt. Gabarit 5 m × 2,5 m. Branches redressées (45°) : les perches
    # d'une cépée montent droit. HORS golden.
    procedural_growth     = True
    port_archetype        = "buissonnant"
    apical_dominance_base = 1.3
    growth_speed          = 1.0
    auxin_release_scale   = 400.0
    branch_angle          = 45.0
    max_height_cm         = 550.0
    max_extent_cm         = 300.0
    max_segments          = 90        # buissonnant ramifié (même borne que le figuier)
    foliage_halfwidth     = 70.0


# ---------------------------------------------------------------------------
# CONIFÈRE PERSISTANT (sprint équilibre invasion ⑤, D10) — source de BRF/aiguilles
# ---------------------------------------------------------------------------

class FirTree(PerennialWoody):
    """
    Abies alba — Sapin (Pinaceae, famille NEUVE déclarée à l'espèce).
    Conifère PERSISTANT (`deciduous=False` → il projette son ombre même l'hiver,
    ≠ les fruitiers caducs : levier d'ombrage permanent au nord) à croissance lente
    et longévité séculaire. Deux sources de mulch :
      • ses AIGUILLES tombées, récoltées (`mulch_source="aiguilles"`), font un mulch
        ACIDIFIANT (nature "aiguilles" : `ph_shift=-0.10`, `allelo=0.3` — il freine
        la levée férale ET fait baisser le pH, à réserver aux acidophiles type
        myrtille, cf. interconnexion avec la fenêtre pH) ;
      • ses rameaux ligneux BROYÉS (geste `broyer` sur son squelette) donnent du BRF.
    Anémophile (cônes mâles au vent). Sa fenêtre pH tire vers l'acide (`ph_opt=5.5`)
    — un conifère de sol acide, cohérent avec sa litière. HORS golden → NEUTRE.
    """
    family = "Pinaceae"
    genus  = "Abies"
    name   = "Sapin"
    feuillage = "aiguilles"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    shade_tolerance = 1.25  # D111 ②ter : sciaphile (sapin pectiné : régénère sous couvert) (≠ défaut strate haute 0,90)
    rarity = "Établie"
    keywords = ["Conifère", "Persistant", "Aiguilles", "Brise-vent"]
    deciduous = False                # PERSISTANT : ombre projetée toute l'année
    winter_strategy = "evergreen"
    foliage_density = 0.70           # houppier dense et sombre
    pollination_mode = "wind"        # cônes anémophiles
    pollination_radius_cm = 600.0
    reproduction_rate = 0.06         # cônes irréguliers
    ph_opt = 5.5                     # tire vers l'acide (conifère de sol acide)
    ph_tol = 1.3
    mulch_source = "aiguilles"       # récolté → stock aiguilles (④/⑤)
    longevity_years = 250
    # rejet_souche = 0 (défaut) : résineux, la souche coupée ne rejette pas (souche ②, D130)
    maturity_years = 20
    girth_max_cm = 25.0        # tronc mûr ~25 cm (pipe model, procédural)
    age_curve = [(0, 30, 15), (5, 200, 80), (10, 400, 130),
                 (20, 800, 200), (50, 1800, 350), (100, 3000, 500)]
    # --- Croissance procédurale (D91 ②) — FLÈCHE conique, conifère lent -----------
    # Cas atypique : le sapin garde une FLÈCHE dominante toute sa vie → port conique
    # `fleche` (≠ l'étalement `etale` des feuillus). On l'obtient par dominance apicale
    # HAUTE + relâchement d'auxine TRÈS long : le leader ne s'ouvre jamais vraiment, la
    # couronne reste ÉTROITE. Fiche : 450/130 à l'an 10, deux fois plus vite que le réel.
    # Latéraux à 85° (étages horizontaux), courts car tardifs (après l'an 5). foliage_
    # halfwidth 50 (ex 110) : ce sont maintenant ces étages qui portent la couronne ; un
    # jeune sapin reste LE cas exposé à la mort hydrique (root_r ≈ fhw). deciduous=False /
    # mulch_source / ph_opt INCHANGÉS (rôles D69). Aiguilles + verticille = rendu (T4).
    # HORS golden.
    procedural_growth     = True
    port_archetype        = "fleche"
    apical_dominance_base = 2.4       # HAUT : flèche tenue → cône serré
    growth_speed          = 1.07
    auxin_release_scale   = 650.0     # long : reste dressé (jamais decurrent)
    branch_angle          = 85.0
    max_height_cm         = 1200.0
    max_extent_cm         = 250.0
    foliage_halfwidth     = 50.0      # cône étroit cr~130 (cf. ci-dessus)
