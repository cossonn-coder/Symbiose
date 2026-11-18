"""
SYMBIOSE — plants/physiologie.py
Paramètres d'espèce du BILAN CARBONE (D140 G, sprint plante vivante ①,
`docs/vegetal/sante/conception_plante_vivante.md` §1-§2).

📖 Pédagogie — l'unité de compte est la SEMAINE D'ENTRETIEN de la plante elle-même :
ce qu'elle respire en une semaine, active, à 15 °C. Tout s'exprime dans cette unité,
ce qui rend un chêne et un radis comparables sans biomasse absolue :
  - `reserve_semaines` : combien de semaines d'entretien l'ADULTE garde en réserve
    (amidon des racines, du bois, d'un bulbe). Un chêne tient une saison nue, un
    radis quelques jours ;
  - `photo_max`        : ce que la plante produit à plein régime, en multiples de son
    entretien (une annuelle héliophile court vite, un arbre vit de peu) ;
  - `cout_feuillage`   : ce que coûte de refaire TOUT son feuillage (un persistant
    coriace coûte plus cher qu'une herbacée tendre).

Défauts par FORME DE VIE (dérivée de l'existant : `ligneux`, `life_cycle`,
`deciduous`, `winter_strategy`, tolérance d'ombre de la strate mature), puis
surcharges par espèce (table `SURCHARGES`, une ligne commentée par espèce qui
s'écarte). Aucun gène créé (anti-doublon) : les tolérances existent déjà.

Couche `plants` : aucune dépendance vers `fields`/`sim` (règle de couches).
"""

from __future__ import annotations

# --- Défauts par forme de vie (conception §2) --------------------------------
RESERVE_DEFAUT = {"arbre": 40.0, "arbuste": 20.0, "vivace": 8.0,
                  "bisannuelle": 6.0, "annuelle": 3.0}
PHOTO_DEFAUT = {"arbre": 2.5, "arbuste": 3.0, "vivace": 3.0,
                "bisannuelle": 3.0, "annuelle": 4.0}
# Plante d'ombre : produit peu à plein régime (conception : 2), mais respire peu aussi ;
# 2,5 mesuré au ① pour que violette/lierre tiennent au nord de la maison (lumière
# reçue ~0,16, leur niche) — à 2,0 leur bilan d'été restait négatif.
PHOTO_SCIAPHILE = 2.5
SEUIL_SCIAPHILE = 1.3          # `shade_tolerance_base` au-delà = sciaphile (hêtre, lierre, violette)
FEUILLAGE_CADUC = 6.0          # feuilles annuelles minces d'un ligneux
FEUILLAGE_PERSISTANT = 10.0    # feuilles coriaces/cireuses gardées plusieurs années
FEUILLAGE_HERBACEE = 2.0       # feuillage tendre, bon marché

# Capacité de réserve d'une PLANTULE relativement à l'adulte. Pourquoi 0,05 : une
# graine apporte son albumen (quelques jours d'entretien), pas les réserves d'un
# adulte installé. La montée est LINÉAIRE de 0,05 à 1 sur l'index de stade (herbacées,
# arbustes) ou sur l'âge jusqu'à la 1re fructification (arbres à stade perpétuel) :
# simple, monotone, et c'est l'organe de réserve qui grossit avec la plante.
FACTEUR_PLANTULE = 0.05

# --- Surcharges par espèce (nom de classe → champs qui s'écartent du défaut) ---
SURCHARGES: dict[str, dict] = {
    # Annuelles cultivées et compagnes (défaut : réserve 3, photo 4, feuillage 2)
    "Tomato":     {},                                        # annuelle héliophile type
    "Pepper":     {"photo_max": 3.5},                        # frileuse, plus lente que la tomate
    "Bean":       {"reserve_semaines": 4.0},                 # gros cotylédons riches en amidon
    "Sunflower":  {"photo_max": 4.5, "cout_feuillage": 3.0},  # héliotrope à larges feuilles
    "Basil":      {"photo_max": 3.5},                        # tendre, frileux
    "Phacelia":   {},                                        # annuelle mellifère type
    "Borage":     {"cout_feuillage": 3.0},                   # grandes feuilles charnues
    "Mustard":    {},                                        # engrais vert rapide type
    "Zucchini":   {"cout_feuillage": 3.0},                   # très grandes feuilles
    "CornSalad":  {"photo_max": 3.0},                        # rosette d'hiver, vit de peu
    "Wheat":      {"reserve_semaines": 4.0},                 # chaume qui stocke avant l'épiaison
    "Rye":        {"reserve_semaines": 4.0},                 # idem, couvert d'hiver
    "Hemp":       {"photo_max": 4.5},                        # croissance explosive en plein soleil
    "BursaPastoris": {"reserve_semaines": 2.0},              # rudérale éphémère, tout dans la graine
    # Bisannuelles (défaut : réserve 6, photo 3)
    "Carrot":     {"reserve_semaines": 12.0},                # racine de réserve : tout l'an 1 y passe
    "Garlic":     {"reserve_semaines": 15.0},                # bulbe = organe de réserve
    "Molene":     {"reserve_semaines": 10.0},                # rosette à pivot charnu
    # Vivaces herbacées (défaut : réserve 8, photo 3, feuillage 2)
    "Clover":     {},                                        # vivace stolonifère type
    "Yarrow":     {"reserve_semaines": 10.0},                # rhizome traçant
    "Mint":       {"reserve_semaines": 12.0},                # rhizome envahissant
    "Comfrey":    {"reserve_semaines": 15.0, "photo_max": 3.5,
                   "cout_feuillage": 3.0},                   # racine charnue, grandes feuilles
    "Strawberry": {},                                        # vivace stolonifère type
    "Nettle":     {"reserve_semaines": 12.0},                # rhizome jaune très fourni
    "SweetViolet": {},                                       # sciaphile de sous-bois (défaut ombre)
    "Mugwort":    {"reserve_semaines": 10.0},                # souche ligneuse à la base
    "Sphagnum":   {"reserve_semaines": 4.0, "photo_max": 2.0},  # mousse : pas d'organe de réserve
    "Drosera":    {"reserve_semaines": 5.0, "photo_max": 2.0},  # petite rosette, hibernacle
    "MedicagoLupulina": {"reserve_semaines": 6.0},           # vivace de courte vie
    "PoaAnnua":   {"reserve_semaines": 4.0},                 # graminée minuscule, vie courte
    "Taraxacum":  {"reserve_semaines": 15.0},                # racine pivot charnue
    "Dactyle":    {"reserve_semaines": 10.0},                # grosse touffe de prairie
    "FetuqueRouge": {},                                      # graminée gazonnante type
    "PlantainLanceole": {"reserve_semaines": 10.0},          # souche courte et dure
    # Arbustes et sous-arbrisseaux (défaut : réserve 20, photo 3, feuillage 6/10)
    "Thyme":      {"reserve_semaines": 12.0, "cout_feuillage": 4.0},   # petites feuilles cireuses
    "Lavender":   {"reserve_semaines": 12.0, "cout_feuillage": 4.0},   # idem, sous-arbrisseau
    "Vaccinium":  {},                                        # sous-arbrisseau caduc type
    "Raspberry":  {"reserve_semaines": 15.0},                # cannes bisannuelles sur souche vivace
    "Ivy":        {},                                        # sciaphile persistant (défauts)
    "Jasmine":    {"reserve_semaines": 15.0},                # liane caduque, souche modeste
    "RunningBamboo": {"reserve_semaines": 30.0, "cout_feuillage": 6.0},  # rhizome massif, feuilles fines
    # Arbres (défaut : réserve 40, photo 2,5, feuillage 6 caduc / 10 persistant)
    "Fig":        {"reserve_semaines": 30.0, "photo_max": 3.0},  # méditerranéen, pousse vite
    "AppleTree":  {},                                        # fruitier type
    "CherryTree": {"reserve_semaines": 35.0},                # vie plus courte que le pommier
    "WalnutTree": {"reserve_semaines": 50.0},                # longévité 200 ans, bois dense
    "OakTree":    {"reserve_semaines": 60.0},                # 500 ans : réserves énormes, refait 2 feuillages
    "FirTree":    {"photo_max": 2.0},                        # aiguilles peu productives mais pérennes
    "BeechTree":  {"reserve_semaines": 50.0},                # sciaphile longévive
    "BirchTree":  {"reserve_semaines": 25.0, "photo_max": 3.0},  # pionnier rapide à vie courte
    "HornbeamTree": {},                                      # arbre de taillis type
    "Alder":      {"reserve_semaines": 30.0, "photo_max": 3.0},  # pionnier fixateur d'azote
    "Willow":     {"reserve_semaines": 30.0, "photo_max": 3.0},  # pionnier des berges, rejette fort
    "HazelTree":  {"reserve_semaines": 30.0},                # cépée de lisière
}


def forme_de_vie(cls) -> str:
    """'arbre' | 'arbuste' | 'vivace' | 'bisannuelle' | 'annuelle'. Arbre = stade
    perpétuel ligneux (pérennes à courbe d'âge) ; arbuste = autre ligneux."""
    if getattr(cls, "ligneux", False):
        return "arbre" if hasattr(cls, "age_curve") else "arbuste"
    if cls.life_cycle == "annual":
        return "annuelle"
    if cls.life_cycle == "biennial":
        return "bisannuelle"
    return "vivace"


def _defauts(cls) -> dict:
    forme = forme_de_vie(cls)
    photo = PHOTO_DEFAUT[forme]
    if cls.shade_tolerance_base() >= SEUIL_SCIAPHILE:
        photo = PHOTO_SCIAPHILE
    if forme in ("arbre", "arbuste"):
        feuil = FEUILLAGE_PERSISTANT if cls.winter_strategy == "evergreen" else FEUILLAGE_CADUC
    else:
        feuil = FEUILLAGE_HERBACEE
    return {"reserve_semaines": RESERVE_DEFAUT[forme], "photo_max": photo,
            "cout_feuillage": feuil}


_CACHE: dict = {}


def parametres_bilan(cls) -> dict:
    """Les 3 paramètres du bilan pour une espèce (défauts + surcharge), mémoïsés
    par classe (constantes d'espèce : jamais recalculées dans un tick)."""
    p = _CACHE.get(cls)
    if p is None:
        p = {**_defauts(cls), **SURCHARGES.get(cls.__name__, {})}
        _CACHE[cls] = p
    return p


def facteur_stade(plant) -> float:
    """Part de la capacité adulte atteinte ∈ [FACTEUR_PLANTULE, 1], monotone :
    sur l'âge (rapporté à la 1re fructification) pour un arbre à stade perpétuel,
    sur l'index de stade sinon."""
    cls = plant.plant_class
    n = len(cls.growth_stages)
    if n <= 1:
        mat = max(1.0, float(getattr(cls, "maturity_years", 0.0) or 0.0))
        part = min(1.0, max(0.0, plant.age_years / mat))
    else:
        part = min(1.0, plant.current_stage / (n - 1))
    return FACTEUR_PLANTULE + (1.0 - FACTEUR_PLANTULE) * part


def capacite_reserve(plant) -> float:
    """Capacité de réserve C (semaines d'entretien) = reserve_semaines × facteur_stade."""
    return parametres_bilan(plant.plant_class)["reserve_semaines"] * facteur_stade(plant)
