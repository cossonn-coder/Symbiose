"""
SYMBIOSE — plants/perennials/fruitiers.py
Les fruitiers : figuier, pommier, cerisier, noyer.
"""

from __future__ import annotations
from plants.perennials.base import PerennialWoody


# ---------------------------------------------------------------------------
# 5 ARBRES PREMIERS (D21) — courbe d'âge (age_years, hauteur_cm, rayon_cm)
# ---------------------------------------------------------------------------

class Fig(PerennialWoody):
    family = "Moraceae"
    genus  = "Ficus"
    name   = "Figuier"
    feuillage = "large"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    shade_tolerance = 0.85  # D111 ②ter : héliophile (méditerranéen de plein soleil) (≠ défaut strate haute 0,90)
    rarity = "Établie"
    keywords = ["Fruitier", "Jardin", "Ombre dense"]
    t_germ_opt = 20.0             # MÉDITERRANÉEN : exige un sol chaud (≠ ligneux tempéré) (③)
    t_germ_tol = 8.0              # moyenne
    foliage_density = 0.75
    fragilite_bois = 1.4           # D111 ②bis : bois tendre et cassant
    reproduction_rate = 0.15   # dispersion (M7) — gated par la lumière
    # Relève ligneuse ③ (D130) : la figue commune ne donne de graine FERTILE que
    # pollinisée par le blastophage (*Blastophaga psenes*), guêpe de l'aire
    # méditerranéenne qui ne passe pas un hiver plus froid que ~7 °C de moyenne au
    # mois le plus froid [ordre de grandeur]. En Normandie (≈ 4 °C) : figues sans
    # graine fertile → propagation par REJETS DE SOUCHE, au pied, APRÈS PERTE de la
    # partie aérienne (mort, puis perte de couronne au ③), PAS en continu
    # (sprint frein_rejets_figuier ② : l'ancien drageon de fond émettait 164 rejets
    # en 25 ans, tous en hiver). Porté par `rejet_souche` ci-dessous, lu par `sim.souche`.
    graine_si_hiver_min_c = 7.0
    # clonal_mode = "none" (défaut hérité) : plus d'émission de fond. `clonal_radius_cm`
    # retiré (inutile sans mode clonal) ; la portée des rejets est `sim.souche.RAYON_REJET_CM`.
    longevity_years = 80
    rejet_souche = 0.8       # souche ② (D130) : rejette vigoureusement du pied après gel ou coupe — la touffe normande repart de souche [ordre de grandeur]
    maturity_years = 5
    bouturable = True          # ligneux à bouture proverbiale : un rameau piqué reprend (palette ②)
    greffable = True           # ligneux fruitier : porte-greffe/greffon de greffe (palette ③, D8)
    bloom_forcing_gdd = 40.0   # figuier MÉDITERRANÉEN : fleurit plus tard que le pommier, en début d'été (~S20) (①)
    bloom_duration = 4
    girth_max_cm = 12.0        # tronc mûr ~12 cm (pipe model, procédural)
    age_curve = [(0, 30, 20), (5, 200, 150), (10, 400, 250), (20, 500, 300)]
    # --- Croissance procédurale (D91 ②) — buissonnant, BAS & LARGE ---------------
    # Cas atypique : le figuier ne fait PAS de flèche dominante, il DÉBOURRE tôt et
    # ramifie bas → port `buissonnant` étalé. On l'obtient par une dominance apicale
    # MODÉRÉE : l'apex ne bride pas ses latéraux, la couronne s'ouvre dès le jeune âge.
    # auxin_release_scale au défaut (400) : inutile de tenir un leader qu'on ne veut pas.
    # Fiche : 400/250 à l'an 10. Bas : gabarit plafonné à 550 cm. Large :
    # foliage_halfwidth généreux (houppier dense de figuier + survie hydrique).
    # max_segments RELEVÉ à 90 : un buissonnant ramifie légitimement plus qu'une flèche
    # decurrent ; au défaut 70 le cap AMPUTAIT la charpente (couronne non monotone). 90
    # reste BORNÉ (à l'an 10 ~79 seg → marge, run éternel préservé). MONO-COLLET : un seul
    # Segment(parent=None) — le multi-tronc est une OPTION F5 différée. HORS golden.
    procedural_growth     = True
    port_archetype        = "buissonnant"
    apical_dominance_base = 1.4       # MODÉRÉ : débourre tôt → ramifie bas
    growth_speed          = 0.95      # bas
    auxin_release_scale   = 400.0     # court : pas de leader séculaire à tenir
    max_height_cm         = 550.0
    max_extent_cm         = 400.0
    max_segments          = 90        # buissonnant ramifié → cap relevé (borné, cf. ci-dessus)
    foliage_halfwidth     = 90.0      # houppier large de figuier + survie hydrique
    fruitier              = True      # figues traçables (HOUPPIER ③)
    pollination_mode      = "self"    # figue commune : noue sans pollinisateur (et `nectar` 0 n'attire aucun butineur)
    fruit_semaines_maturation = 9     # [choix] noue s15-17 → mûre s23-25, tombe s26-28 [3 seeds] (fiche : août-oct.)
    # VERGER VIVANT ③ : cohortes. Figuier de jardin 4 m : 10-15 kg de figues de ~50 g, soit
    # ~200-300 figues [odg] ; ~30 apex → 8 par site. Masse : 1 unité de litière ≈ 250 g
    # de matière sèche (FEUILLE_PAR_PLOT 0,30 = ~300 g/m²/an de feuilles) ; figue 50 g
    # fraîche à ~20 % de MS = 10 g → 0,04 [odg].
    fruits_par_site = 8
    fruit_masse     = 0.04


class AppleTree(PerennialWoody):
    family = "Rosaceae"
    genus  = "Malus"
    name   = "Pommier"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.55  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    shade_tolerance = 0.85  # D111 ②ter : héliophile modéré (fruitier de lumière, supporte une mi-ombre) (≠ défaut strate haute 0,90)
    rarity = "Établie"
    keywords = ["Fruitier", "Jardin", "Mellifère"]
    foliage_density = 0.60
    reproduction_rate = 0.15
    longevity_years = 70
    rejet_souche = 0.5       # souche ② (D130) : rejette de souche, mais moins qu'une essence de taillis (et souvent du porte-greffe) [ordre de grandeur]
    graine_viabilite_ans = 2.0   # zoochorie ① (D42) : pépin viable ~2 ans en sol [ordre de grandeur]
    maturity_years = 5
    greffable = True           # ligneux fruitier greffé par excellence (palette ③, D8) ; même famille Rosaceae que cerisier/framboisier
    age_curve = [(0, 30, 20), (5, 200, 120), (10, 350, 200),
                 (20, 500, 280), (50, 700, 350)]
    # --- Profil de croissance procédurale (tronçon 3bis) ---
    # 1re LIGNEUSE migrée : l'empreinte (height/canopy/root) est dérivée de la
    # STRUCTURE de segments (§G), plus de l'age_curve. Cible de calibration =
    # l'allure dans la fenêtre du golden (10 ans → ~350 cm de haut, ~200 cm de
    # couronne, §E.3 « reproduire l'allure d'abord »). Le point 50 ans (700/350)
    # et la sénescence (~70 ans) sont HORS fenêtre golden → non exercés.
    # Valeurs CALIBRÉES via la sonde §C (growth_factor=1.0, cycle saisonnier réel,
    # 520 ticks) pour approcher ~350/~200 à l'an 10, montée monotone et bornée :
    #   • growth_speed=0.83 : l'apex monte ~0.83 cm/tick d'été → ~351 cm à l'an 10
    #     (et non vers l'an 5 comme à 1.5) sans atteindre le plafond max_height_cm ;
    #   • emit_length_cm=40 : une flèche de 350 cm en ~9 segments, tronc court
    #     (AUTOMNE VISIBLE ② : 50 → 40, les premières charpentières partent plus bas) ;
    #   • max_segments=70 : flèche + charpentières dans le plafond ; à l'an 10 ~54
    #     segments → marge confortable (le filet dur n'ampute jamais la flèche) ;
    #   • wood_persistence=4000 sem. (~la vie de l'arbre) : sans ça les charpentières
    #     d'un arbre sans apex actif mourraient en ~1 an → couronne effondrée ;
    #   • apical_dominance_base=1.2, auxin_release_scale=500 (AUTOMNE VISIBLE ②, ex 2.0
    #     et 400) : des latéraux dès l'an 5 au lieu de l'an 7, le bâton devient un arbre ;
    #   • branch_angle=70° : insertion latérale assez horizontale → étalement marqué ;
    #   • foliage_halfwidth=70 (ex 50) : couronne isolée ~200 cm à l'an 10 (fiche).
    #     CRITIQUE pour la SURVIE : root_r = PROC_ROOT_RATIO·canopy_r (k=1.0) et la
    #     jeune flèche n'a quasi pas de latéraux avant l'an 7 → à 30 la couronne ET
    #     les racines tiennent dans 1 plot ; tout le prélèvement d'eau (_apply_uptake,
    #     share=1/nplots) se concentre sur le plot-foyer qui s'assèche → drought_memory
    #     > 0.6 → mort par stress hydrique vers l'an 3. À 50 les racines couvrent
    #     plusieurs plots → prélèvement dilué → l'arbre survit sain les 10 ans (≠
    #     l'age_curve qui tabulait une couronne large dès l'an 5). Levier existant,
    #     scope minimal — pas de PROC_ROOT_RATIO par espèce.
    procedural_growth     = True
    port_archetype        = "etale"   # decurrent : dominance relâchée avec l'âge → couronne large
    growth_speed          = 0.83
    apical_dominance_base = 1.2
    auxin_release_scale   = 500.0
    branch_angle          = 70.0
    max_height_cm         = 700.0     # plafond (point 50 ans) — non atteint à l'an 10
    max_extent_cm         = 350.0     # plafond d'extension (point 50 ans) — non atteint à l'an 10
    emit_length_cm        = 40.0
    girth_max_cm          = 18.0      # tronc mûr ~18 cm (pipe model, sprint lisibilité ligneuse — SEULE espèce qui l'exerce aujourd'hui, procedural_growth=True) ; placeholder → F5
    foliage_halfwidth     = 70.0      # couronne non nulle + racines viables (cf. ci-dessus)
    organ_site            = "lateral" # fructification latérale (lu au tronçon 5)
    fruitier              = True      # porte des fruits traçables (③ ; 1re fructif. à maturity_years=5)
    # VERGER VIVANT ② : 17 → 15. La floraison recalée (plus tardive, pic plus haut donc
    # fanaison plus longue) fait nouer s11-13 ; à 17 les pommes tombaient en s34, après
    # la fenêtre de la fiche. À 15 : mûre s26-28, tombe ≤ s33 [verger_mur, seed 42, 3 ans].
    fruit_semaines_maturation = 15    # [choix] fiche : sept.-oct.
    # VERGER VIVANT ③ : cohortes. Pommier demi-tige de 3,5 m : 30-50 kg, soit ~200-300
    # pommes de ~150 g [odg] ; ~25 sites latéraux → 10 par site. Pomme 150 g fraîche à
    # ~15 % de MS = 22 g → 0,09 (1 unité ≈ 250 g de MS, cf. figuier) [odg].
    fruits_par_site = 10
    fruit_masse     = 0.09
    oidium_susceptibility = 0.3       # second porteur d'oïdium (humectation ④) — tavelure ET oïdium
    # Floraison PRINTANIÈRE (sprint FLORAISON & FRUCTIFICATION ①). L'ancien patch
    # `gdd_floraison=130` (qui plaçait la floraison en début d'automne, D84) est
    # ANNULÉ : avec le forçage thermique événementiel, un seuil BAS `bloom_forcing_
    # gdd=8` est franchi tôt (~S14-15) → le pommier fleurit au PRINTEMPS, comme dans
    # la vraie vie. `bloom_duration=3` : floraison courte (les pétales tombent vite).
    # Golden : le pommier du smoke a < 5 ans (maturity_years=5) → is_seed_bearing
    # False → floraison reste 0 quel que soit le seuil.
    # VERGER VIVANT ② : floraison fin avril à mi-mai, APRÈS le cerisier [odg, fiche
    # `fiches_arbres.md` « avr.-mai, avec les feuilles » ; pommiers à cidre normands
    # en pleine fleur début-mi-mai]. Seuil 8 → 15 : armé s6 à s8 selon l'année (wiy 1 ≈
    # 20 mars) au lieu de s5-s7, avant le cerisier [verger_mur, seed 42, 3 ans, n=1].
    # Montée 0,6 : pic 0,94 en 3 semaines (0,73 avant), la vraie pleine floraison.
    bloom_forcing_gdd     = 15.0      # fin avril - mi-mai
    bloom_duration        = 3         # floraison courte (~3 semaines bouton → chute) [odg]
    floraison_montee      = 0.6       # pleine floraison atteinte (pic ≥ 0,9) [choix]


class CherryTree(PerennialWoody):
    family = "Rosaceae"
    genus  = "Prunus"
    name   = "Cerisier"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.55  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    shade_tolerance = 0.80  # D111 ②ter : héliophile (≠ défaut strate haute 0,90)
    rarity = "Établie"
    keywords = ["Fruitier", "Intermédiaire", "Mellifère"]
    foliage_density = 0.60
    reproduction_rate = 0.15
    longevity_years = 60
    rejet_souche = 0.8       # souche ② (D130) : drageonne et rejette fort de souche (merisier : essence de taillis) [ordre de grandeur]
    graine_viabilite_ans = 2.0   # zoochorie ① (D42) : noyau viable ~2 ans en sol [ordre de grandeur]
    mange_par = ("merle",)       # zoochorie ④ : la cerise est cueillie, le noyau semé sous les perchoirs
    maturity_years = 5
    greffable = True           # ligneux fruitier greffé (palette ③, D8) ; Rosaceae → compatible pommier/framboisier
    # VERGER VIVANT ② : le cerisier fleurit AVANT le pommier, mi-avril [odg, fiche
    # `fiches_arbres.md` « avr., avant les feuilles » ; merisier/cerisier en Normandie,
    # pleine fleur ~10-20 avril]. Seuil 12 → 5 : armé s3-s5 (avant : s6-s8, après le
    # pommier, faux). Montée 0,6 : pic 0,94 au lieu de 0,73.
    bloom_forcing_gdd = 5.0    # mi-avril, avant le pommier
    bloom_duration = 3         # floraison courte (~2-3 semaines) [odg]
    floraison_montee = 0.6     # pleine floraison atteinte (pic ≥ 0,9) [choix]
    girth_max_cm = 15.0        # tronc mûr ~15 cm (pipe model, procédural)
    age_curve = [(0, 40, 25), (5, 250, 150), (10, 500, 280),
                 (20, 700, 380), (50, 900, 450), (100, 1000, 500)]
    # --- Croissance procédurale (AUTOMNE VISIBLE ②) — ovoïde étagé -----------------
    # Fiche : 500/250 à l'an 10. Angle 50° (branches montantes, ≠ pommier étalé) ; le
    # filet de `_elaguer` ne coupant plus la flèche, le plafond n'effondre plus la
    # couronne, le release_scale peut redescendre pour brancher dès l'an 4-5. HORS golden.
    procedural_growth   = True
    port_archetype      = "ovoide_etage"
    growth_speed        = 1.18
    apical_dominance_base = 1.2
    auxin_release_scale = 400.0
    branch_angle        = 50.0
    max_height_cm       = 1000.0
    max_extent_cm       = 500.0
    foliage_halfwidth   = 60.0      # couronne ~250 ; les latéraux portent les racines
    fruitier            = True      # cerises traçables (HOUPPIER ③)
    fruit_semaines_maturation = 7   # [choix] noue s9-12 → mûre s16-19, tombe s18-21 [3 seeds] (fiche : juin-juil.)
    # VERGER VIVANT ③ : cohortes. Cerisier de 5 m : 15-25 kg de cerises de ~7 g, soit
    # ~2 000-3 000 cerises [odg] ; ~27 apex → 90 par site. Cerise 7 g fraîche à ~17 %
    # de MS = 1,2 g → 0,005 (1 unité ≈ 250 g de MS, cf. figuier) [odg].
    fruits_par_site = 90
    fruit_masse     = 0.005


class WalnutTree(PerennialWoody):
    """
    Juglans regia — Noyer (Juglandaceae). EMBLÈME de l'allélopathie (sprint
    ALLÉLOPATHIE ⑤) : ses racines et sa litière libèrent la JUGLONE, un puissant
    inhibiteur qui « fait le vide » sous sa couronne (proverbe paysan : « rien ne
    pousse sous le noyer »). Émission FORTE via `inject_field variable="allelopathie"`.
    AUTO-TOLÉRANT (D2) : `allelopathie_sensibilite ≈ 0` — le noyer ne s'auto-inhibe
    pas (champ unique D4, l'auto-tolérance s'approxime par la sensibilité, choix
    surgical du kickoff ②).
    """
    family = "Juglandaceae"
    genus  = "Juglans"
    name   = "Noyer"
    feuillage = "large"  # transpiration (D111 ①) : type de feuillage d'espèce
    nectar = 0.0  # nectar d'espèce (D111 ⑦) : nourriture offerte au butineur
    shade_tolerance = 0.80  # D111 ②ter : héliophile strict (≠ défaut strate haute 0,90)
    rarity = "Climacique"
    keywords = ["Lisière", "Ombre dense", "Structurant", "Allélopathe"]
    foliage_density = 0.80
    pollination_mode = "wind"        # anémophile (chatons)
    pollination_radius_cm = 600.0
    # VERGER VIVANT ③ : dose anémophile 6 → 12. Les chatons de mai sur 2 semaines (②)
    # avaient divisé le pollen reçu par ~2. Mesure `verger_mur` (2 noyers à 4,5 m), part
    # nouée an 1/2/3 : noyer sous le vent 0,63/0,51/0,79, noyer isolé (ou au vent de
    # l'autre, qui ne reçoit que son propre pollen) 0,31/0,21/0,50 [seed 42, n=1 run par
    # dose, VM]. Cible [choix] : une paire noue au moins à moitié, un isolé ~0,2-0,35
    # (dichogamie). À 15, l'isolé monte à 0,25-0,55.
    anemo_dose = 12.0
    reproduction_rate = 0.10   # glandée (mast) plus rare
    longevity_years = 200
    rejet_souche = 0.5       # souche ② (D130) : rejette de souche jeune, capacité qui faiblit avec l'âge [ordre de grandeur]
    maturity_years = 15
    # VERGER VIVANT ② : chatons et fleurs femelles en MAI, sur 1 à 2 semaines [odg, fiche
    # `fiches_arbres.md` « chatons pendants verts, mai » ; Franquette, variété tardive
    # répandue en France, mi-fin mai]. Avant : défaut 60/6 → juin, 7 semaines. Seuil 28
    # → armé s8-s10 (début-fin mai) ; montée 0,7 → pic 0,91 en 2 semaines. Dichogamie non
    # modélisée. La dose anémophile se recale au ③ sur cette floraison.
    bloom_forcing_gdd = 28.0   # mai
    bloom_duration = 2         # chatons brefs [odg]
    floraison_montee = 0.7     # pic ≥ 0,9 en 2 semaines [choix]
    allelopathie_emission = 0.20     # FORT (juglone) — emblème ; arme l'autotox ④
    allelopathie_sensibilite = 0.05  # AUTO-TOLÉRANT : ne s'auto-inhibe pas (D2)
    family_effects = [
        {
            "type": "permanent",
            "trigger": "weekly",
            "action": "inject_field",
            "variable": "allelopathie",
            "amount": 0.20,
            "cible": "local",
            "description": "Juglone — forte allélopathie racinaire (rien ne pousse sous le noyer)"
        }
    ]
    girth_max_cm = 30.0        # tronc mûr ~30 cm (pipe model, procédural)
    age_curve = [(0, 40, 25), (5, 300, 200), (10, 600, 350),
                 (20, 1000, 550), (50, 1500, 750), (100, 2500, 1000)]
    # --- Croissance procédurale (AUTOMNE VISIBLE ②) — tête ronde et large ----------
    # Fiche : 600/350 à l'an 10. Gabarit tenu à l'échelle du jardin (12 m × 5,5 m de
    # rayon, ex 25 m × 10 m, l'age_curve n'est plus lue). Relâchement court + angle 70° +
    # entre-nœuds longs (70 cm) : peu de grosses branches, ouvertes tôt. HORS golden.
    procedural_growth   = True
    port_archetype      = "arrondi_large"
    growth_speed        = 1.42
    apical_dominance_base = 2.8
    auxin_release_scale = 300.0
    emit_length_cm      = 70.0
    max_height_cm       = 1200.0
    max_extent_cm       = 550.0
    foliage_halfwidth   = 55.0      # couronne ~350, portée par les branches
    fruitier            = True      # noix traçables (HOUPPIER ③) ; nouaison par le vent
    # [choix] fiche : sept.-oct. VERGER VIVANT ② : 9 → 15. Les 9 semaines compensaient une
    # floraison de juin (défaut 60 degrés-jours) ; fleuri en mai, le noyer noue s12-14 et
    # mûrit fin sept.-oct. [verger_mur, seed 42, 3 ans].
    fruit_semaines_maturation = 15
    # VERGER VIVANT ③ : cohortes. Noyer de 15-20 ans : 10-20 kg de noix, soit ~1 000-1 500
    # noix [odg] ; ~20 apex → 60 par site à nouaison pleine (le vent en noue la moitié
    # dans une paire). Noix avec son brou ~13 g de MS → 0,05 (1 unité ≈ 250 g de MS) [odg].
    fruits_par_site = 60
    fruit_masse     = 0.05
