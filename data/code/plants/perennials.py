"""
SYMBIOSE — plants/perennials.py
Pérennes ligneuses (D21) — base commune polymorphe avec les annuelles.

Les arbres exposent la MÊME interface lumière que les annuelles
(height_at / canopy_radius_at / root_radius_at / foliage_density_at), si bien
que le LightField les traite à l'identique — zéro duplication. Seule la logique
de croissance diffère : annuelles = stades discrets, arbres = courbe d'âge
interpolée (`age_years` accumulé +1/52 par tick dans engine).

`foliage_density` est saisonnière : un arbre caduc ne projette aucune ombre
l'hiver (soleil d'hiver au sol sous un fruitier — levier permaculture majeur).

genetic_factor reste neutre (1.0) — l'héritage génétique est le Sprint
génétique/reproduction, pas ici.
"""

from __future__ import annotations
from plants.base import PlantBase, GrowthStage


class PerennialWoody(PlantBase):
    """
    Base des pérennes ligneuses. Surcharge l'interface lumière pour lire une
    courbe d'âge `age_curve` = liste triée de (age_years, hauteur_cm, rayon_cm).
    Hauteur et rayon interpolés linéairement entre points tabulés ; plateau aux
    extrémités. root_radius = canopy_radius × root_ratio.

    Un stade unique perpétuel garde la compatibilité avec les sous-systèmes
    indexés par stade (effets, strate, conflits) sans leur imposer la notion d'âge.
    """
    life_cycle = "perennial"
    winter_strategy = "dormant"
    deciduous = True
    root_ratio = 1.0
    # Constitution S (sprint SANTÉ & RÉSILIENCE ②) : les ligneuses établies sont
    # l'archétype slow-tough — bois pérenne, réserves profondes, elles PLIENT là où
    # une annuelle CASSE. Base commune aux 9 arbres du catalogue (un coup encaissé
    # est divisé par 1.25 dans `erode`) ; aucun arbre ne reste au défaut silencieux.
    resilience_base = 1.25
    # Niche herbivorie racinaire (③) : pivots profonds + fort partenariat mycorhizien
    # → le campagnol ronge le chevelu de surface mais l'arbre garde des racines
    # d'ancrage hors d'atteinte → il ENCAISSE mieux la perte d'uptake (÷1.3).
    root_loss_tolerance_base = 1.3
    age_curve: list[tuple] = []   # [(age_years, height_cm, canopy_radius_cm), ...]

    # --- Défauts procéduraux communs aux ligneux migrés (D91, §4 mutualisation) ---
    # Profil d'ÉCHELLE ARBRE répliqué du pommier (perennials.py AppleTree) : flèche en
    # peu de segments, bois quasi pérenne, insertion latérale horizontale (étalement),
    # feuillage assez large pour que les racines couvrent plusieurs plots (SURVIE
    # hydrique, cf. commentaire d'AppleTree). `procedural_growth` reste False sur la base :
    # la migration se fait PAR ESPÈCE (chaque arbre migré flippe le flag + surcharge son
    # gabarit `max_height_cm`/`max_extent_cm`/`growth_speed`/`auxin_release_scale`). Un
    # arbre NON migré garde son age_curve interpolée ; ces défauts ne sont alors lus par
    # personne (structure de segments inerte). Golden NEUTRE (seul AppleTree est ligneux
    # dans le smoke, et il surcharge tous ces champs).
    emit_length_cm        = 50.0    # flèche en peu de segments (comme le pommier)
    max_segments          = 70
    wood_persistence      = 4000    # ~la vie de l'arbre (sinon charpentières meurent en 1 an)
    branch_angle          = 70.0    # insertion assez horizontale → étalement
    foliage_halfwidth     = 50.0    # SURVIE hydrique (racines multi-plots) — départ, à ajuster F5
    port_archetype        = "etale"
    apical_dominance_base = 2.0

    # Fenêtre thermique de levée (sprint germination thermique ③) : défaut LIGNEUX
    # TEMPÉRÉ — un arbre de climat tempéré (pommier, cerisier, noyer, chêne) lève sur
    # sol frais de printemps. Le figuier méditerranéen surcharge vers plus chaud.
    # NB : les arbres ont `archetype=None` → ils ne sont PAS tirés par la succession
    # spontanée (WEED_CATALOGUE) ; cette fenêtre type le catalogue (③ « type TOUT »)
    # et servira la levée d'un grain planté/disséminé, pas un chemin du golden.
    t_germ_opt = 14.0             # ligneux tempéré : lève au frais du printemps
    t_germ_tol = 11.0             # large

    # --- Réponse à l'écrasement (volet 2, CONCEPTION_ECRASEMENT §4, Q4) ---
    # NB calibrage : la table §4 notait « base 0.1 × âge » pour les arbres, mais avec
    # la formule FIGÉE `intensité = INTENSITE_PIED·(1 − resistance·f_lignification(âge))`
    # une résistance de 0.1 laisse un tronc établi (f→1) à intensité 0.9 ≥ COUPE_NETTE :
    # toujours NET, donc écimable/tuable — ce qui CONTREDIT « tronc inécrasable ». On porte
    # donc une résistance HAUTE et on laisse la RAMPE d'âge (`f_lignification`) réaliser
    # l'intention : un SEMIS d'arbre (âge ≈ 0 → f ≈ 0 → résistance effective ≈ 0) s'écrase,
    # le TRONC établi (f → 1 → résistance pleine) plie (DOUX) — exactement Q4.
    resistance_ecrasement  = 0.9   # tronc établi inécrasable ; semis s'écrase via l'âge
    stimulation_ecrasement = 0.3

    # Stade unique : l'arbre ne « change pas de stade », il grandit avec l'âge.
    growth_stages = [GrowthStage(name="arbre", duration_weeks=0, strate="haute")]

    @classmethod
    def _interp(cls, age: float) -> tuple[float, float]:
        curve = cls.age_curve
        if age <= curve[0][0]:
            return curve[0][1], curve[0][2]
        if age >= curve[-1][0]:
            return curve[-1][1], curve[-1][2]
        for (a0, h0, r0), (a1, h1, r1) in zip(curve, curve[1:]):
            if a0 <= age <= a1:
                t = (age - a0) / (a1 - a0)
                return h0 + (h1 - h0) * t, r0 + (r1 - r0) * t
        return curve[-1][1], curve[-1][2]

    # Migration procédurale (tronçon 3bis) : un arbre `procedural_growth` (pommier)
    # dérive son empreinte de la STRUCTURE de segments comme les annuelles migrées —
    # on délègue alors à PlantBase (voie procédurale §G, qui lit inst.footprint). Les
    # arbres NON migrés (flag False, défaut) gardent l'age_curve interpolée au mot près.
    @classmethod
    def height_at(cls, inst) -> float:
        if cls.procedural_growth:
            return super().height_at(inst)
        h, _ = cls._interp(inst.age_years)
        return h * inst.growth_factor * inst.gene("hauteur")

    @classmethod
    def canopy_radius_at(cls, inst) -> float:
        if cls.procedural_growth:
            return super().canopy_radius_at(inst)
        _, r = cls._interp(inst.age_years)
        return r

    @classmethod
    def root_radius_at(cls, inst) -> float:
        if cls.procedural_growth:
            return super().root_radius_at(inst)
        _, r = cls._interp(inst.age_years)
        return r * cls.root_ratio

    @classmethod
    def foliage_density_at(cls, inst, saison: str | None = None) -> float:
        if cls.deciduous and saison == "hiver":
            return 0.0
        return cls.foliage_density if cls.foliage_density is not None else 0.6

    @classmethod
    def longevity(cls) -> float:
        """Override explicite par arbre ; repli = dernier point d'âge × 1,5."""
        if cls.longevity_years is not None:
            return cls.longevity_years
        return cls.age_curve[-1][0] * 1.5


# ---------------------------------------------------------------------------
# 5 ARBRES PREMIERS (D21) — courbe d'âge (age_years, hauteur_cm, rayon_cm)
# ---------------------------------------------------------------------------

class Fig(PerennialWoody):
    family = "Moraceae"
    genus  = "Ficus"
    name   = "Figuier"
    feuillage = "large"  # transpiration (D111 ①) : type de feuillage d'espèce
    rarity = "Établie"
    keywords = ["Fruitier", "Jardin", "Ombre dense"]
    t_germ_opt = 20.0             # MÉDITERRANÉEN : exige un sol chaud (≠ ligneux tempéré) (③)
    t_germ_tol = 8.0              # moyenne
    foliage_density = 0.75
    reproduction_rate = 0.15   # dispersion (M7) — gated par la lumière
    longevity_years = 80
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
    # MODÉRÉE (< 2.0 des autres arbres) : l'apex ne bride pas ses latéraux, la
    # couronne s'ouvre dès le jeune âge. auxin_release_scale reste au défaut (400) :
    # inutile de tenir un leader qu'on ne veut pas. Calibré (sonde §C, 520 ticks)
    # pour l'allure age_curve à l'an 10 (~421 cm haut / ~256 couronne ; cible 400/250).
    # Bas : gabarit plafonné à 500 cm (age_curve figuier plafonne à 20 ans). Large :
    # foliage_halfwidth généreux (houppier dense de figuier + survie hydrique).
    # max_segments RELEVÉ à 90 : un buissonnant ramifie légitimement plus qu'une flèche
    # decurrent ; au défaut 70 le cap AMPUTAIT la charpente (couronne non monotone). 90
    # reste BORNÉ (à l'an 10 ~79 seg → marge, run éternel préservé). MONO-COLLET : un seul
    # Segment(parent=None) — le multi-tronc est une OPTION F5 différée. HORS golden.
    procedural_growth     = True
    port_archetype        = "buissonnant"
    apical_dominance_base = 1.9       # MODÉRÉ (< 2.0) : débourre tôt → ramifie bas
    growth_speed          = 1.0       # bas (plafond age_curve ~500 cm)
    auxin_release_scale   = 450.0     # court : pas de leader séculaire à tenir
    max_height_cm         = 500.0     # plafond = dernier point age_curve (20 ans)
    max_extent_cm         = 300.0
    max_segments          = 90        # buissonnant ramifié → cap relevé (borné, cf. ci-dessus)
    foliage_halfwidth     = 95.0      # houppier large de figuier + survie hydrique


class AppleTree(PerennialWoody):
    family = "Rosaceae"
    genus  = "Malus"
    name   = "Pommier"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    rarity = "Établie"
    keywords = ["Fruitier", "Jardin", "Mellifère"]
    foliage_density = 0.60
    reproduction_rate = 0.15
    longevity_years = 70
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
    #   • emit_length_cm=50 : une flèche de 350 cm en ~7 segments → dominance facile
    #     à tenir (≠ 44 segments à 8 cm, physiquement hors plafond) ;
    #   • max_segments=70 : flèche + charpentières dans le plafond ; à l'an 10 ~55
    #     segments → marge confortable (le filet dur n'ampute jamais la flèche) ;
    #   • wood_persistence=4000 sem. (~la vie de l'arbre) : sans ça les charpentières
    #     d'un arbre sans apex actif mourraient en ~1 an → couronne effondrée ;
    #   • apical_dominance_base=2.0 : flèche tenue ~7 segments puis relâchée avec l'âge
    #     (AUXIN_RELEASE_SCALE) → l'étalement `etale` (couronne large) ÉMERGE vers l'an 7 ;
    #   • branch_angle=70° : insertion latérale assez horizontale → étalement marqué ;
    #   • foliage_halfwidth=50 : couronne isolée ~197 cm à l'an 10 (cible 200, -1,5 %).
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
    apical_dominance_base = 2.0
    branch_angle          = 70.0
    max_height_cm         = 700.0     # plafond (point 50 ans) — non atteint à l'an 10
    max_extent_cm         = 350.0     # plafond d'extension (point 50 ans) — non atteint à l'an 10
    emit_length_cm        = 50.0
    max_segments          = 70
    wood_persistence      = 4000
    girth_max_cm          = 18.0      # tronc mûr ~18 cm (pipe model, sprint lisibilité ligneuse — SEULE espèce qui l'exerce aujourd'hui, procedural_growth=True) ; placeholder → F5
    foliage_halfwidth     = 50.0      # couronne non nulle + racines viables (cf. ci-dessus)
    organ_site            = "lateral" # fructification latérale (lu au tronçon 5)
    fruitier              = True      # porte des fruits traçables (③ ; 1re fructif. à maturity_years=5)
    oidium_susceptibility = 0.3       # second porteur d'oïdium (humectation ④) — tavelure ET oïdium
    # Floraison PRINTANIÈRE (sprint FLORAISON & FRUCTIFICATION ①). L'ancien patch
    # `gdd_floraison=130` (qui plaçait la floraison en début d'automne, D84) est
    # ANNULÉ : avec le forçage thermique événementiel, un seuil BAS `bloom_forcing_
    # gdd=8` est franchi tôt (~S14-15) → le pommier fleurit au PRINTEMPS, comme dans
    # la vraie vie. `bloom_duration=3` : floraison courte (les pétales tombent vite).
    # Golden : le pommier du smoke a < 5 ans (maturity_years=5) → is_seed_bearing
    # False → floraison reste 0 quel que soit le seuil.
    bloom_forcing_gdd     = 8.0       # printemps précoce (~S14-15)
    bloom_duration        = 3         # floraison courte


class CherryTree(PerennialWoody):
    family = "Rosaceae"
    genus  = "Prunus"
    name   = "Cerisier"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    rarity = "Établie"
    keywords = ["Fruitier", "Intermédiaire", "Mellifère"]
    foliage_density = 0.60
    reproduction_rate = 0.15
    longevity_years = 60
    maturity_years = 5
    greffable = True           # ligneux fruitier greffé (palette ③, D8) ; Rosaceae → compatible pommier/framboisier
    bloom_forcing_gdd = 12.0   # printemps (~S16) — floraison de cerisier légèrement après le pommier (①)
    bloom_duration = 3         # floraison courte
    girth_max_cm = 15.0        # tronc mûr ~15 cm (pipe model, procédural)
    age_curve = [(0, 40, 25), (5, 250, 150), (10, 500, 280),
                 (20, 700, 380), (50, 900, 450), (100, 1000, 500)]
    # --- Croissance procédurale (D91 ①) — feuillu étalé, patron pommier ---
    # Calibré (sonde §C, 520 ticks) pour reproduire l'allure age_curve à l'an 10
    # (~504 cm haut / ~276 couronne ; cible 500/280). Défauts d'arbre hérités de
    # PerennialWoody ; on surcharge gabarit + vitesse + release_scale + couronne.
    # auxin_release_scale=600 : au défaut 400 la flèche s'étale trop tôt et sature le
    # cap segments (couronne effondrée, non monotone) ; à 600 le leader tient jusqu'à
    # ~500 cm puis débourre → étalement `etale` propre. foliage_halfwidth=140 porte la
    # couronne à ~276 ET garantit des racines multi-plots (survie hydrique). HORS golden.
    procedural_growth   = True
    growth_speed        = 1.20
    max_height_cm       = 1000.0    # plafond = dernier point age_curve (100 ans) — non atteint à 10 ans
    max_extent_cm       = 500.0
    auxin_release_scale = 600.0     # leader tenu jusqu'à ~500 cm avant de s'étaler
    foliage_halfwidth   = 140.0     # couronne ~276 + survie hydrique (racines multi-plots)


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
    rarity = "Climacique"
    keywords = ["Lisière", "Ombre dense", "Structurant", "Allélopathe"]
    foliage_density = 0.80
    pollination_mode = "wind"        # anémophile (chatons)
    pollination_radius_cm = 600.0
    reproduction_rate = 0.10   # glandée (mast) plus rare
    longevity_years = 200
    maturity_years = 15
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
    # --- Croissance procédurale (D91 ①) — grand feuillu ouvert, patron pommier ---
    # Calibré (sonde §C) pour ~620 cm haut / ~352 couronne à l'an 10 (cible 600/350).
    # Noyer = essence de longue vie (200 ans) → release_scale un peu au-dessus du
    # cerisier (leader dressé jusqu'à ~600 cm). foliage_halfwidth=160 pour sa large
    # couronne ouverte + racines multi-plots. HORS golden.
    procedural_growth   = True
    growth_speed        = 1.50
    max_height_cm       = 2500.0    # plafond = dernier point age_curve (100 ans)
    max_extent_cm       = 1000.0
    auxin_release_scale = 650.0     # longévif → flèche tenue jusqu'à ~600 cm
    foliage_halfwidth   = 160.0     # couronne ouverte ~352 + survie hydrique


class OakTree(PerennialWoody):
    family = "Fagaceae"
    genus  = "Quercus"
    name   = "Chêne"
    feuillage = "moyen"  # transpiration (D111 ①) : type de feuillage d'espèce
    rarity = "Sentinelle"
    keywords = ["Lisière", "Sujet structurant", "Centenaire"]
    foliage_density = 0.75
    pollination_mode = "wind"        # anémophile (chatons)
    pollination_radius_cm = 800.0
    reproduction_rate = 0.08   # glandée (mast) rare
    longevity_years = 500
    maturity_years = 25
    girth_max_cm = 40.0        # tronc mûr ~40 cm (pipe model, procédural)
    age_curve = [(0, 30, 20), (5, 200, 150), (10, 400, 300),
                 (20, 700, 450), (50, 1500, 800), (100, 3000, 1200)]
    # --- Croissance procédurale (D91 ①) — sujet centenaire, jeune chêne large-bas ---
    # Calibré (sonde §C) pour ~398 cm haut / ~307 couronne à l'an 10 (le chêne est
    # LENT en hauteur jeune, il prend son ampleur sur des siècles). L'ampleur
    # centenaire est portée par max_height_cm=3000 / max_extent_cm=1200 (age_curve
    # 100 ans), atteints sur la durée. NOTE calibrage (décision imprévue, cf. rapport) :
    # un auxin_release_scale très élevé (1500, suggéré au kickoff) fabrique un POTEAU
    # nu (l'apex ne relâche jamais → zéro latéral → couronne = foliage_halfwidth),
    # ce qui contredit `etale` et « grand & LARGE ». On garde release_scale modéré
    # (500 → couronne qui s'ouvre) et on porte la LARGEUR par foliage_halfwidth=185
    # (double dividende : survie hydrique du jeune chêne à racines encore courtes).
    # HORS golden.
    procedural_growth   = True
    growth_speed        = 0.95
    max_height_cm       = 3000.0    # plafond = dernier point age_curve (100 ans)
    max_extent_cm       = 1200.0
    auxin_release_scale = 500.0     # couronne qui s'ouvre (≠ poteau fastigié)
    foliage_halfwidth   = 185.0     # jeune chêne large-bas ~307 + survie hydrique


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
    rarity = "Climacique"
    keywords = ["Lisière", "Ombre dense", "Structurant"]
    foliage_density = 0.85            # houppier fermé → ombre profonde de hêtraie
    pollination_mode = "wind"        # anémophile (chatons)
    pollination_radius_cm = 700.0
    reproduction_rate = 0.08         # faînée (mast) irrégulière
    longevity_years = 300
    maturity_years = 30
    girth_max_cm = 35.0        # tronc mûr ~35 cm (pipe model, procédural)
    age_curve = [(0, 30, 18), (5, 200, 130), (10, 400, 260),
                 (20, 700, 400), (50, 1500, 650), (100, 2800, 950)]
    # --- Croissance procédurale (D91 ①) — grand houppier ample, ombre profonde ---
    # Calibré (sonde §C) pour ~398 cm haut / ~262 couronne à l'an 10 (cible 400/260).
    # Même arbitrage que le chêne (cf. rapport) : release_scale modéré (500) pour que
    # le houppier s'ouvre (un rs élevé ferait un poteau), largeur portée par
    # foliage_halfwidth=140. L'ampleur cathédrale séculaire vient de max_extent=950.
    # HORS golden.
    procedural_growth   = True
    growth_speed        = 0.95
    max_height_cm       = 2800.0    # plafond = dernier point age_curve (100 ans)
    max_extent_cm       = 950.0
    auxin_release_scale = 500.0     # houppier qui s'ouvre (≠ poteau fastigié)
    foliage_halfwidth   = 140.0     # houppier ample ~262 + survie hydrique


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
    rarity = "Établie"
    keywords = ["Pionnière", "Lisière", "Ombre légère"]
    foliage_density = 0.45           # houppier léger → sous-bois clair
    pollination_mode = "wind"        # anémophile (chatons)
    pollination_radius_cm = 600.0
    reproduction_rate = 0.20         # graines ailées abondantes, dispersion large
    longevity_years = 90
    maturity_years = 10
    girth_max_cm = 14.0        # tronc mûr ~14 cm (pipe model, procédural) ; placeholder → F5
    age_curve = [(0, 40, 15), (5, 400, 120), (10, 800, 200),
                 (20, 1300, 300), (50, 1800, 420), (90, 2000, 480)]
    # --- Croissance procédurale (D91 ③) — pionnier élancé + port PLEUREUR ------------
    # Betula pendula : flèche DRESSÉE (leader net) + rameaux DISTAUX qui RETOMBENT
    # (levier gravitropique `gravitropism_gain`, seul le bouleau le règle). Calibré
    # (sonde §C) : ~783 cm haut / ~270 couronne à l'an 10 (cible age_curve 800/200 ;
    # couronne volontairement un peu au-dessus de 200 → voir NOTE hydrique). Leader
    # tenu par une dominance haute (2.7) + un release_scale long (800, comme l'aulne
    # pionnier T2) : « pionnier rapide » se lit sur la VITESSE d'élongation, pas sur
    # un étalement précoce qui casserait la flèche élancée. HORS golden.
    procedural_growth   = True
    growth_speed        = 1.9       # pionnier rapide
    max_height_cm       = 2000.0    # plafond = dernier point age_curve (90 ans)
    max_extent_cm       = 400.0     # houppier LÉGER, élancé (plus étroit qu'un grand feuillu)
    apical_dominance_base = 2.7     # flèche élancée — leader net, houppier resserré
    auxin_release_scale = 800.0     # leader dressé longtemps (élancé, ≠ étalement précoce)
    foliage_halfwidth   = 70.0      # NOTE hydrique (état §3) : bouleau grêle = LE plus exposé
                                    # (root_r = canopy_r) → fhw généreux (>50 du pommier qui
                                    # survit) pour couvrir plusieurs plots au jeune âge ;
                                    # élargit un peu la couronne (270 vs 200) → arbitrage F5.
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
    rarity = "Établie"
    keywords = ["Bocage", "Haie", "Structurant"]
    foliage_density = 0.65           # houppier moyen
    pollination_mode = "wind"        # anémophile (chatons)
    pollination_radius_cm = 550.0
    reproduction_rate = 0.12         # samares en grappes
    longevity_years = 150
    maturity_years = 15
    girth_max_cm = 18.0        # tronc mûr ~18 cm (pipe model, procédural)
    age_curve = [(0, 40, 20), (5, 250, 120), (10, 500, 220),
                 (20, 900, 340), (50, 1500, 520), (100, 2000, 650)]
    # --- Croissance procédurale (D91 ①) — port moyen ovoïde du bocage ---
    # Calibré (sonde §C) pour ~504 cm haut / ~236 couronne à l'an 10 (cible 500/220).
    # Ovoïde plus étroit que le cerisier : même vitesse/release_scale mais
    # foliage_halfwidth plus modeste (100 vs 140) → houppier plus fermé. HORS golden.
    procedural_growth   = True
    growth_speed        = 1.20
    max_height_cm       = 2000.0    # plafond = dernier point age_curve (100 ans)
    max_extent_cm       = 650.0
    auxin_release_scale = 600.0     # leader tenu jusqu'à ~500 cm avant de s'étaler
    foliage_halfwidth   = 100.0     # ovoïde moyen ~236 + survie hydrique


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
    maturity_years = 20
    girth_max_cm = 25.0        # tronc mûr ~25 cm (pipe model, procédural)
    age_curve = [(0, 30, 15), (5, 200, 80), (10, 400, 130),
                 (20, 800, 200), (50, 1800, 350), (100, 3000, 500)]
    # --- Croissance procédurale (D91 ②) — FLÈCHE conique, conifère lent -----------
    # Cas atypique : le sapin garde une FLÈCHE dominante toute sa vie → port conique
    # `fleche` (≠ l'étalement `etale` des feuillus). On l'obtient par dominance apicale
    # HAUTE + relâchement d'auxine TRÈS long : le leader ne s'ouvre jamais vraiment, la
    # couronne reste ÉTROITE. Croissance LENTE (conifère). Calibré (sonde §C, 520 ticks)
    # pour l'allure age_curve à l'an 10 (~398 cm haut / ~130 couronne étroite ; cible
    # 400/130). foliage_halfwidth : cas le PLUS exposé à la mort hydrique (§1.3) — une
    # flèche sans latéraux a canopy_r ≈ foliage_halfwidth, donc root_r ≈ fhw. On le porte
    # à 110 pour que les racines couvrent ~2,2 plots (survie) TOUT en tenant la cible
    # étroite cr130 (la flèche n'ajoute quasi pas de spread latéral). deciduous=False /
    # mulch_source / ph_opt INCHANGÉS (rôles D69). Aiguilles + verticille = rendu (T4).
    # HORS golden.
    procedural_growth     = True
    port_archetype        = "fleche"
    apical_dominance_base = 2.8       # HAUT : flèche tenue → cône serré
    growth_speed          = 0.95      # LENT (conifère)
    auxin_release_scale   = 700.0     # TRÈS long : reste dressé (jamais decurrent)
    max_height_cm         = 3000.0    # plafond = dernier point age_curve (100 ans)
    max_extent_cm         = 500.0
    foliage_halfwidth     = 110.0     # cône étroit cr130 + racines multi-plots (survie)


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
    rarity = "Établie"
    keywords = ["Berge", "Fixatrice N₂", "Pionnière", "Zone humide"]
    foliage_density = 0.55           # houppier moyen, ombre légère de ripisylve
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
    maturity_years = 10
    bouturable = True                # rameau de saule/aulne piqué au bord de l'eau reprend
    girth_max_cm = 16.0              # tronc mûr ~16 cm (pipe model, procédural)
    age_curve = [(0, 40, 20), (5, 350, 120), (10, 700, 200),
                 (20, 1200, 320), (50, 2000, 450), (100, 2500, 550)]
    # --- Croissance procédurale (D91 ②) — pionnier étalé ÉLANCÉ de berge ----------
    # Cas atypique : l'aulne pousse VITE (pionnier) et HAUT (h10 ~700, le plus grand
    # des jeunes arbres migrés), houppier moyen ÉLANCÉ (`etale` mais plus étroit que le
    # chêne). Calibré (sonde §C, 520 ticks) : ~680 cm haut / ~233 couronne à l'an 10
    # (cible 700/200). growth_speed élevé (pionnier) ; auxin_release_scale MODÉRÉ (800) :
    # assez pour tenir une flèche de 7 m (à rs plus bas le leader s'étalait trop tôt,
    # saturait le cap segments et la hauteur stagnait à ~200), mais bien EN DEÇÀ du
    # séculaire — l'aulne est un pionnier à vie moyenne. foliage_halfwidth ÉTROIT (50)
    # pour la couronne élancée ; racines viables via le spread des latéraux (root_r ≈
    # cr ≈ 233, ~4,6 plots). Les family_effects (fixation N₂ Frankia) et
    # asphyxie_tolerance_base sont INDÉPENDANTS de la morphologie → INCHANGÉS (rôle hydro
    # D61 préservé, vérifié en test). HORS golden.
    procedural_growth   = True
    growth_speed        = 1.65        # pionnier rapide (h10 ~680)
    max_height_cm       = 2500.0      # plafond = dernier point age_curve (100 ans)
    max_extent_cm       = 550.0
    auxin_release_scale = 800.0       # tient la flèche de 7 m sans saturer le cap segments
    foliage_halfwidth   = 50.0        # houppier élancé cr~233 ; racines via spread latéral
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
    rarity = "Établie"
    keywords = ["Berge", "Trogne", "Bouture", "Mellifère précoce"]
    foliage_density = 0.50           # feuillage fin et lâche → ombre légère de bord d'eau
    pollination_mode = "insect"      # chatons NECTARIFÈRES (≠ aulne/bouleau anémophiles)
    reproduction_rate = 0.22         # graines cotonneuses innombrables, viabilité très courte
    seed_dispersal = "anemochore"    # aigrette de coton (vent + eau)
    ph_opt = 6.5                     # indifférent, tolère du frais au neutre
    ph_tol = 1.5
    asphyxie_tolerance_base = 3.0    # HÉLOPHYTE comme l'aulne : tient le sol gorgé
    t_germ_opt = 12.0                # lève au frais des berges de printemps
    t_germ_tol = 10.0
    longevity_years = 80
    maturity_years = 5
    bouturable = True                # bouture PROVERBIALE : un rameau piqué reprend seul
    bloom_forcing_gdd = 4.0          # fleurit AVANT les feuilles (~fin d'hiver) : 1ʳᵉ table
    bloom_duration = 3               # chatons brefs
    girth_max_cm = 22.0              # fût épais (une trogne épaissit) ; placeholder → F5
    age_curve = [(0, 50, 25), (5, 600, 220), (10, 1100, 380),
                 (20, 1700, 520), (50, 2200, 650), (80, 2400, 700)]
    # --- Croissance procédurale (patron aulne/bouleau) — pionnier PLEUREUR ---------
    # ⚠️ Valeurs NON calibrées à la sonde §C (le saule n'est semé nulle part : ni
    # golden, ni banc) — PLACEHOLDERS cohérents avec l'aulne (même stature, même
    # milieu) poussés d'un cran en vitesse, à recalibrer au F5 le jour où le joueur en
    # plante un. `gravitropism_gain` > celui du bouleau : rameaux franchement PENDANTS.
    procedural_growth   = True
    growth_speed        = 2.1        # le plus rapide du catalogue ligneux
    max_height_cm       = 2400.0     # plafond = dernier point age_curve (80 ans)
    max_extent_cm       = 700.0
    apical_dominance_base = 2.2
    auxin_release_scale = 750.0      # tient la flèche, puis s'ouvre en houppier ample
    foliage_halfwidth   = 60.0       # houppier lâche + racines multi-plots (survie)
    gravitropism_gain   = 1.4        # rameaux PENDANTS (port pleureur) — calibrer F5
