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

Le ① a créé l'état et sa génération déterministe. Le ② y ajoute la GÉOMÉTRIE
MONDE de la bande (§ en fin de fichier) et branche `light`/`abri` dessus : un
secteur devient un obstacle global de plus, du même type que la maison. Pluie de
graines, nappe de berge et gestes forestiers = tronçons ③→⑦.

Opt-in par construction : sans ceinture (`None`) ou sur une ceinture NEUTRE
(prairie rase), `occulteurs` et `obstacles_abri` renvoient des listes VIDES →
lumière et abri strictement inchangés → golden intact.

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

from constants import PLOT_CM
from fields.noise import _hash_noise

# --- Géométrie de la bande ------------------------------------------------
# Profondeur de la ceinture hors-jardin, en cm. Même valeur que
# `DecorLayer.DepthCm` côté Godot : quand le pont alimentera la vue (tronçon ⑦),
# les deux mondes parleront de la même bande.
PROFONDEUR_CM = 900.0

# Côté du jardin en cm (monde 20×20 m, échelle actée). Miroir EXACT de
# `WorldView.WorldCm = 2000f` côté Godot : la ceinture est le seul endroit du
# moteur qui a besoin de l'emprise GLOBALE du jardin (les tuiles, elles, ne
# connaissent que leur propre `origin_*_cm`).
MONDE_CM = 2000.0

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
    Secteur VIDE (prairie rase, aucun ligneux) — l'état neutre de référence pour
    tout ce qui dépend d'une HAUTEUR ou d'une DENSITÉ ligneuse : ombre, abri,
    turbulence (②) et pluie de graines forestière (③) y sont strictement nuls.

    ⚠️ Ce n'est PAS un secteur « mort » pour autant (précision ③) : son type est
    `prairie`, et une prairie sème des graminées et porte un peu d'effet de
    lisière — c'est de l'écologie, une prairie n'est pas du béton. Le vrai
    interrupteur opt-in qui garde le golden intact est l'ABSENCE de ceinture
    (`game_state["ceinture"]` non renseigné ⇒ aucun flux appelé du tout).
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


# ---------------------------------------------------------------------------
# GÉOMÉTRIE MONDE — la ceinture vue comme des OBSTACLES (tronçon ②)
# ---------------------------------------------------------------------------
# Le moteur sait déjà traiter un « obstacle global en coordonnées MONDE » : la
# maison est un rectangle balayé dans `light.compute` et une capsule dans
# `abri._obstacles`. Un secteur de lisière n'est RIEN DE PLUS que cela. On ne
# construit donc aucun masque d'horizon : on fabrique ici, à partir de l'état
# agrégé, les mêmes primitives que la maison — et `light`/`abri` les consomment
# avec leurs helpers existants.

# Seuls ces deux types interceptent le soleil et le vent. Une `prairie` est rase,
# une `riviere` est au niveau du sol, une `friche` n'a pas de hauteur
# (`hauteur_canopee` reste à 0) : elles n'ombrent ni n'abritent rien.
TYPES_OCCULTANTS = ("foret", "falaise")


def rect_secteur(cote: int) -> tuple[float, float, float, float]:
    """
    Emprise MONDE `(x0, y0, x1, y1)` en cm de la bande d'un bord cardinal.

    Repère du sol de `light.py` : **x = Est, y = Sud** (donc le Nord est en y
    négatif). Le jardin occupe `[0, MONDE_CM]²` ; chaque bande s'étend de
    `PROFONDEUR_CM` VERS L'EXTÉRIEUR. Miroir de `DecorLayer.EdgePoint`.
    """
    w, d = MONDE_CM, PROFONDEUR_CM
    if cote == NORD:
        return (0.0, -d, w, 0.0)
    if cote == EST:
        return (w, 0.0, w + d, w)
    if cote == SUD:
        return (0.0, w, w, w + d)
    return (-d, 0.0, 0.0, w)          # OUEST


def _hauteur_occultante(secteur: dict) -> float:
    """Hauteur d'interception d'un secteur : canopée pour un bois, roche pour une
    falaise. 0 pour tout le reste (aucune ombre, aucun abri)."""
    if secteur["type"] == "foret":
        return secteur["hauteur_canopee"]
    if secteur["type"] == "falaise":
        return secteur["altitude_relative"]
    return 0.0


def occulteurs(ceinture) -> list[tuple[float, float, float, float, float, float]]:
    """
    Occulteurs de LUMIÈRE de la ceinture : `(x0, y0, x1, y1, hauteur_cm, opacite)`
    en coordonnées MONDE — le format que `light.compute` sait balayer
    (`_point_in_swept_rect`, exactement comme la maison).

    L'opacité d'un bois est sa `densite_ligneuse` (ombre PARTIELLE, multiplicative,
    contrairement au mur plein de la maison) ; une falaise est opaque (1.0, la roche
    ne filtre pas). Aucune règle saisonnière ici : c'est `solar_slice` qui produit
    l'ombre longue d'hiver et l'ombre courte d'été (conception §3.1).

    `None`/liste vide → liste vide → `light.compute` strictement inchangé.
    """
    out = []
    for s in ceinture or ():
        hauteur = _hauteur_occultante(s)
        opacite = 1.0 if s["type"] == "falaise" else s["densite_ligneuse"]
        if hauteur <= 0.0 or opacite <= 0.0:
            continue
        x0, y0, x1, y1 = rect_secteur(s["cote"])
        out.append((x0, y0, x1, y1, hauteur, opacite))
    return out


def obstacles_abri(ceinture) -> list[tuple[float, float, float, float, float]]:
    """
    Obstacles de VENT de la ceinture : `(cx, cy, hauteur_cm, rayon_cm, porosite)`
    en coordonnées MONDE — le format 5-uplet de `abri._obstacles` (la maison et
    les plantes y portent `porosite = None`, ce qui garde leur branche historique).

    Un secteur est une capsule TRÈS LARGE : centrée au milieu de la bande (donc à
    `PROFONDEUR_CM / 2` au-delà du bord), de rayon = demi-longueur du bord. Même
    approximation grossière que la demi-diagonale de la maison — on ne raffine pas
    la forme d'un agrégat de 20 m de large.

    La porosité φ = `1 − densite_ligneuse` pilote DEUX grandeurs dans `abri.py` :
    la réduction du vent moyen (linéaire) et le surcroît de rafale (quadratique).
    Une falaise est imperméable (φ = 0) : abri maximal, turbulence maximale.
    """
    out = []
    for s in ceinture or ():
        hauteur = _hauteur_occultante(s)
        if hauteur <= 0.0:
            continue
        x0, y0, x1, y1 = rect_secteur(s["cote"])
        densite = 1.0 if s["type"] == "falaise" else s["densite_ligneuse"]
        out.append(((x0 + x1) / 2.0, (y0 + y1) / 2.0,
                    hauteur, MONDE_CM / 2.0, 1.0 - densite))
    return out


# ---------------------------------------------------------------------------
# PLOTS DE BORD — la décroissance vers l'intérieur (tronçon ③)
# ---------------------------------------------------------------------------
# Les flux entrants NON géométriques (pluie de graines, nappe de berge, champ de
# lisière) ne portent pas loin : ils s'atténuent en quelques plots depuis le bord.
# On ne balaie donc JAMAIS la grille pour un effet de bord (réflexe D32) — on
# n'itère que la BANDE de plots réellement atteinte, et chaque plot arrive avec
# son poids de décroissance. Un seul helper pour les trois flux : la géométrie de
# la ceinture est une responsabilité de CE module, pas de ses consommateurs.


def plots_de_bord(cote: int, rows: int, cols: int,
                  tile_origin: tuple[float, float],
                  portee_cm: float):
    """
    Itère `(r, c, poids)` : les plots d'une tuile atteints par le secteur `cote`,
    avec un poids ∈ ]0, 1] qui DÉCROÎT LINÉAIREMENT avec la distance au bord du
    jardin (1 au contact, 0 à `portee_cm`, rien au-delà).

    `tile_origin` = offset MONDE de la tuile en cm (même argument que
    `light.compute`/`abri`) : le centre du plot `(r, c)` est à
    `(c·PLOT_CM + PLOT_CM/2 + ox, r·PLOT_CM + PLOT_CM/2 + oy)` dans le repère sol
    (x = Est, y = Sud). La distance au bord considéré est donc `y` au NORD,
    `MONDE_CM − y` au SUD, `x` à l'OUEST, `MONDE_CM − x` à l'EST.

    Coût : on ne parcourt QUE l'axe perpendiculaire au bord (≤ 40 itérations) et,
    pour les seules rangées dans la portée, l'axe parallèle → O(portée × côté),
    jamais O(rows × cols). Générateur : aucune liste intermédiaire allouée.
    Une tuile trop loin du bord ne rend RIEN (boucle vide) — une ceinture n'agit
    que sur les tuiles qui la touchent.
    """
    if portee_cm <= 0.0:
        return
    ox, oy = tile_origin
    # Les bords NORD/SUD décroissent le long des LIGNES (axe y), EST/OUEST le long
    # des COLONNES (axe x) — un seul code pour les quatre côtés.
    axe_lignes = cote in (NORD, SUD)
    n = rows if axe_lignes else cols
    origine = oy if axe_lignes else ox
    for i in range(n):
        centre = i * PLOT_CM + PLOT_CM / 2.0 + origine
        dist = centre if cote in (NORD, OUEST) else MONDE_CM - centre
        if dist < 0.0 or dist >= portee_cm:
            continue
        poids = 1.0 - dist / portee_cm
        if axe_lignes:
            for c in range(cols):
                yield i, c, poids
        else:
            for r in range(rows):
                yield r, i, poids
