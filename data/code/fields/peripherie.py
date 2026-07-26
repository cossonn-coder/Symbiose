"""
SYMBIOSE — fields/peripherie.py
La CEINTURE : état moteur de la périphérie du jardin (D73, tronçon ①).

Le jardin n'est pas une île. Autour de ses quatre bords cardinaux vit une bande
de 900 cm (`PROFONDEUR_CM`, alignée sur `DecorLayer.DepthCm` côté vue) décrite
par **4 secteurs agrégés** — pas par des `PlantInstance`. Simuler une lisière
comme N arbres réels ferait exploser `LightField` (dette D32) sans rien apporter :
ce qu'on veut d'une forêt vue du jardin, c'est sa hauteur, sa densité et son
essence dominante. Trois scalaires, pas trois cents arbres.

Spec : `docs/champs/peripherie/conception_peripherie.md` §4.1 (décisions D-1/D-4).

Périmètre de CE tronçon : on CRÉE l'état et sa génération déterministe, on ne
BRANCHE rien. Personne n'importe ce module dans la boucle → golden NEUTRE par
construction, exactement comme `sim/wind.py` au ① du sprint vent. Lumière, abri,
pluie de graines, nappe de berge et gestes forestiers = tronçons ②→⑦.

**D92 se referme ici.** La génération C# (`DecorLayer.BuildProfile`, hash
`decor|{seed}|{cote}`) produisait 96,0 % de terrains aux 4 côtés identiques et
**zéro falaise** sur 300 000 seeds : les clés ne différaient que par leurs bits
bas, et la falaise exigeait un voisin resté *prairie* — condition jamais réunie.
On repart d'un tirage franchement décalé par côté (deux grands premiers) et d'une
règle de falaise réalisable. Vérifié par `tests/test_peripherie.py`, pas par
intuition.

Couche `fields` : n'importe QUE `fields.noise` (le hash). Jamais `sim` — la couche
basse n'importe pas la haute.
"""

from __future__ import annotations

from fields.noise import _hash_noise

# --- Géométrie de la bande ------------------------------------------------
# Profondeur de la ceinture hors-jardin, en cm. Même valeur que
# `DecorLayer.DepthCm` côté Godot : quand le pont alimentera la vue (tronçon ⑦),
# les deux mondes parleront de la même bande.
PROFONDEUR_CM = 900.0

# Les 4 bords cardinaux. `cote` est un index, pas une chaîne : il sert d'entrée de
# hash et de clé de secteur dans le save.
NORD, EST, SUD, OUEST = 0, 1, 2, 3
COTES = (NORD, EST, SUD, OUEST)

# --- Canaux-sentinelles (philo #3 : zéro RNG vivant) ----------------------
# Comme `weather.py` (tranche 90_00x) et `wind.py` (90_01x), la ceinture réserve
# la tranche 91_00x : des coordonnées (r, c) très au-delà de la grille des plots,
# donc décorrélées de tout flux spatial du sol comme des tirages météo/vent.
K_TYPE    = (91_000, 0)   # type du secteur
K_ESSENCE = (91_001, 0)   # essence dominante d'un secteur boisé
K_HAUTEUR = (91_002, 0)   # hauteur de canopée
K_DENSITE = (91_003, 0)   # densité ligneuse
K_EAU     = (91_004, 0)   # ligne d'eau (rivière)
K_ROCHE   = (91_005, 0)   # altitude relative (falaise)

# Décalages par côté. LE BUG D92 EST ICI : faire varier une coordonnée d'une
# unité entre deux côtés ne suffit pas — après l'avalanche de `_hash_noise` les
# quatre côtés restaient corrélés. On décale de deux GRANDS PREMIERS distincts,
# un par axe, pour que chaque côté tombe dans une région de hash sans rapport.
DECALAGE_R = 7_919
DECALAGE_C = 104_729

# --- Distribution des types (§4.1) ---------------------------------------
# Poids cumulés lus dans l'ordre : ~35 % forêt, ~25 % rivière, ~30 % prairie,
# ~10 % friche. La FALAISE n'est jamais tirée — elle DÉRIVE d'une rivière voisine
# (couplage hérité de D58 §5.1) : c'est l'érosion fluviale qui met la roche à nu.
TYPES_TIRES = (("foret", 0.35), ("riviere", 0.60), ("prairie", 0.90), ("friche", 1.00))
TYPES = ("foret", "riviere", "falaise", "prairie", "friche")

# --- Essences (décision D-4) ---------------------------------------------
# Essences forestières du catalogue EXISTANT (`plants/catalogue.py`). L'essence
# fixe le comportement au recépage (tronçon ④ : hêtre et bouleau ne rejettent
# pas) et la densité d'ombre — un secteur n'a donc pas besoin d'une flore, juste
# d'une dominante.
ESSENCES_FORET = ("hetre", "charme", "bouleau", "aulne")
# RIPISYLVE : une forêt qui touche une rivière est une forêt de berge. Aulne et
# saule y sont les essences justes (racines dans l'eau, bois tendre). Le saule
# n'entre au catalogue qu'au tronçon ⑥ — ici ce n'est qu'une chaîne, aucun import,
# donc aucune dépendance à attendre.
ESSENCES_RIPISYLVE = ("aulne", "saule")

# --- Plages des scalaires (§4.1) -----------------------------------------
HAUTEUR_FORET_CM = (800.0, 2000.0)     # une lisière normande : 8 à 20 m
DENSITE_FORET    = (0.55, 0.95)        # canopée plus ou moins fermée
DENSITE_FRICHE   = (0.05, 0.25)        # ronces et jeunes ligneux épars
LIGNE_EAU_CM     = (-80.0, 40.0)       # cm relatifs au bord (négatif = en creux)
ALTITUDE_FALAISE_CM = (300.0, 1200.0)  # 3 à 12 m de roche au-dessus du jardin


def _tirage(seed: int, cote: int, canal: tuple[int, int]) -> float:
    """
    Tirage déterministe ∈ [0,1[ propre à (seed, côté, canal). `week=0` : la
    ceinture est une donnée de TERRAIN, pas de semaine — elle ne dérive pas dans
    le temps (seuls les gestes du joueur la changent, tronçon ④).
    """
    return _hash_noise(seed, 0,
                       canal[0] + cote * DECALAGE_R,
                       canal[1] + cote * DECALAGE_C)


def _entre(u: float, plage: tuple[float, float]) -> float:
    """Étale un tirage [0,1[ sur une plage fermée, arrondi (comparaisons stables)."""
    bas, haut = plage
    return round(bas + u * (haut - bas), 3)


def voisins(cote: int) -> tuple[int, int]:
    """
    Les deux bords ADJACENTS d'un bord cardinal (nord touche est et ouest ; il ne
    touche pas le sud, qui est à l'opposé). L'adjacence est symétrique : on ne
    privilégie pas le sens horaire, contrairement au C# — c'est une des raisons
    pour lesquelles la falaise n'apparaissait jamais.
    """
    return ((cote + 1) % 4, (cote + 3) % 4)


def secteur_neutre(cote: int) -> dict:
    """
    Secteur VIDE (prairie rase, aucun ligneux) — l'état neutre de référence. Tous
    les flux entrants (②③) doivent être nuls sur ce secteur : c'est ce qui rend la
    ceinture opt-in et garde le golden intact.
    """
    return {
        "cote": cote,
        "type": "prairie",
        "essence": None,
        "hauteur_canopee": 0.0,
        "densite_ligneuse": 0.0,
        # Mémoire de souche, posée par les gestes forestiers (tronçon ④) :
        # "vivante" = elle rejettera, "morte" = le vide restera à combler.
        "souche_memory": None,
        # Horloge de repousse, avancée par la cinétique (tronçon ④). En années :
        # trogne 5 ans, recépage 10, canopée refermée 30.
        "annees_depuis_coupe": 0.0,
        "ligne_eau": 0.0,
        "altitude_relative": 0.0,
    }


def generer_ceinture(seed: int) -> list[dict]:
    """
    Les 4 secteurs de la périphérie, tirés du seed du terrain (philo #3 et #7 :
    déterministe et jamais deux terrains pareils).

    Deux passages, comme le C# — mais avec les deux corrections de D92 :
      1. le type de chaque côté, sur un hash franchement décalé par côté ;
      2. le couplage rivière → falaise, dont la condition est *réalisable*.
    Puis un troisième passage pour l'essence, qui dépend du voisinage (ripisylve).
    """
    ceinture = [secteur_neutre(cote) for cote in COTES]

    # --- 1. Type de chaque bord -------------------------------------------
    for s in ceinture:
        u = _tirage(seed, s["cote"], K_TYPE)
        for nom, plafond in TYPES_TIRES:
            if u < plafond:
                s["type"] = nom
                break

    # --- 2. Couplage rivière → falaise ------------------------------------
    # La rivière a creusé : un bord qui la touche et qui n'est ni rivière ni forêt
    # montre sa roche. Le C# exigeait que ce voisin soit resté *prairie* APRÈS le
    # 1er passage et n'en regardait qu'un seul — d'où 0 falaise sur 300 000 seeds.
    # On lit les types du 1er passage figés dans `types_bruts` : sans ça, une
    # falaise créée tôt influencerait les suivantes selon l'ordre de parcours.
    types_bruts = [s["type"] for s in ceinture]
    for cote in COTES:
        if types_bruts[cote] != "riviere":
            continue
        for v in voisins(cote):
            if types_bruts[v] in ("riviere", "foret"):
                continue
            ceinture[v]["type"] = "falaise"

    # --- 3. Scalaires + essence -------------------------------------------
    for s in ceinture:
        cote, typ = s["cote"], s["type"]

        if typ == "foret":
            s["hauteur_canopee"] = _entre(_tirage(seed, cote, K_HAUTEUR),
                                          HAUTEUR_FORET_CM)
            s["densite_ligneuse"] = _entre(_tirage(seed, cote, K_DENSITE),
                                           DENSITE_FORET)
            # Ripisylve : on interroge les types BRUTS, pas les types corrigés —
            # une rivière reste une rivière au 2e passage, mais lire `types_bruts`
            # garde ce test indépendant de l'ordre des passages.
            bord_de_leau = any(types_bruts[v] == "riviere" for v in voisins(cote))
            palette = ESSENCES_RIPISYLVE if bord_de_leau else ESSENCES_FORET
            u = _tirage(seed, cote, K_ESSENCE)
            s["essence"] = palette[min(int(u * len(palette)), len(palette) - 1)]

        elif typ == "friche":
            # Pas d'essence dominante : une friche est un mélange instable de
            # pionnières, c'est justement ce qui la rend semencière (tronçon ③).
            s["densite_ligneuse"] = _entre(_tirage(seed, cote, K_DENSITE),
                                           DENSITE_FRICHE)

        elif typ == "riviere":
            s["ligne_eau"] = _entre(_tirage(seed, cote, K_EAU), LIGNE_EAU_CM)

        elif typ == "falaise":
            s["altitude_relative"] = _entre(_tirage(seed, cote, K_ROCHE),
                                            ALTITUDE_FALAISE_CM)

    return ceinture
