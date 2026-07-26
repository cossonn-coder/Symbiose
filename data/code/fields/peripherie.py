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
# Noms diégétiques des bords, dans l'ordre des index — pour les lignes de log des
# gestes (④) et pour la vue (⑦). Jamais utilisés comme clé d'état.
NOMS_COTES = ("nord", "est", "sud", "ouest")

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
        # Coupe EN COURS de repousse (tronçon ④) : le geste dont la cinétique
        # s'applique, `None` quand le peuplement est reconstitué (ou jamais coupé).
        "geste_coupe": None,
        # Cibles de repousse : le peuplement MÛR d'avant la première coupe. C'est ce
        # vers quoi la cinétique ramène le secteur — le terrain garde son identité,
        # une lisière recépée redevient CETTE lisière-là, pas une lisière moyenne.
        "densite_avant": 0.0,
        "hauteur_avant": 0.0,
        "ligne_eau": 0.0,
        "altitude_relative": 0.0,
        # --- Eau & roche (tronçon ⑤) --------------------------------------
        # OUVRAGE d'eau en place (`endiguer`/`deriver`), `None` = aucun. Un ouvrage
        # est un ARTEFACT : il demande un entretien perpétuel, et se rompt sans lui
        # (`tick_ouvrages`). Une mare CREUSÉE n'est pas un ouvrage — c'est une forme
        # donnée au terrain, elle ne rompt pas.
        "ouvrage": None,
        "annees_depuis_ouvrage": 0.0,
        # Ligne d'eau NATURELLE = celle d'avant les travaux, mémorisée à la pose du
        # premier ouvrage. C'est là que la rupture ramène l'eau (jamais à zéro : le
        # terrain garde son identité, cf. `densite_avant`).
        "ligne_eau_naturelle": 0.0,
        # Roche RETIRÉE cumulée par `entailler`, en cm. IRRÉVERSIBLE : aucune
        # cinétique ne la fait décroître, jamais. C'est la cicatrice du terrain, et
        # la source permanente d'érosion de la falaise entaillée.
        "entaille_cm": 0.0,
        # Verrou du signe diégétique d'éboulis (« 1ᵉʳ éboulis », conception §7) : le
        # signe est émis UNE fois par épisode d'érosion, pas chaque semaine. Il se
        # ré-arme quand le couvert est revenu et que le sol cesse de partir.
        "erosion_signalee": False,
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


# ---------------------------------------------------------------------------
# SYLVICULTURE — la coupe et sa repousse (tronçon ④)
# ---------------------------------------------------------------------------
# La MUTATION de l'état d'un secteur et sa CINÉTIQUE de retour vivent ici, avec
# l'état qu'elles transforment ; la couche JOUEUR (gate d'outil, coût de Vigueur,
# bois déposé au sol, trace au ledger) vit dans `sim/actions/paysage.py`. Un
# secteur n'est pas une `PlantInstance` : c'est un agrégat, on ne simule pas N
# arbres (D32) — ce qu'on coupe, ce sont ses trois scalaires.
#
# Le matériau pédagogique du tronçon est l'ASYMÉTRIE DE RÉVERSIBILITÉ
# (conception §3.3/§4.4) : trois gestes qui se ressemblent au moment du coup de
# lame et que DIX ANS séparent. Rien n'est annoncé, rien n'est bloqué (philo #6).

# LE fait discriminant de la sylviculture : toutes les essences ne rejettent pas de
# souche. Charme et aulne sont des taillis classiques, le saule rejette très vite
# (il entre au catalogue au tronçon ⑥). Hêtre et bouleau rejettent très mal ⇒
# **recéper une hêtraie, c'est l'abattre**, et le joueur ne l'apprend qu'en le
# faisant (ou en lisant l'encyclopédie une fois la maîtrise acquise).
ESSENCES_QUI_REJETTENT = frozenset({"charme", "aulne", "saule"})

# Cinétiques par geste : `(densité résiduelle, fraction de hauteur conservée,
# durée de retour en années)`. Une densité résiduelle `None` signifie « densité
# CONSERVÉE » (l'étêtage ne retire pas de tige, il rabat les têtes).
# Chiffres calés sur le réel (conception §4.4) : noisetier 7-9 ans, charme 10-12,
# saule têtard 3-5, canopée tempérée refermée en 25-40 ans. Zéro tirage (philo #3) :
# la repousse est une fonction de `annees_depuis_coupe`, pas un pari.
CINETIQUES = {
    "abattre": (0.10, 0.00, 30.0),   # l'arbre meurt ; la STRUCTURE est lente à revenir
    "receper": (0.20, 0.00, 10.0),   # la souche rajeunit — un flux, pas un gisement
    "eteter":  (None, 0.60,  5.0),   # la trogne : on prend la tête, le tronc dure
}

# Après un ABATTAGE, le vide ne reste pas vide : ronces et semis pionniers le
# comblent en ~4 ans. Mais ce couvert-là n'est pas une forêt — la canopée, elle,
# met 30 ans. On exprime les deux lignes de la table §4.4 sans machinerie : la
# densité prend le MAXIMUM des deux courbes (plancher pionnier tôt, canopée
# ensuite). Plafond aligné sur `DENSITE_FRICHE` — une trouée EST une friche.
DENSITE_PIONNIERE = DENSITE_FRICHE[1]
DUREE_PIONNIERES_ANS = 4.0

# La ceinture vieillit en ANNÉES (cinétiques décennales) là où le tick avance en
# semaines. Constante locale : `constants.py` ne porte que l'échelle spatiale.
SEMAINES_PAR_AN = 52.0


def couper_secteur(secteur: dict, geste: str) -> str:
    """Applique une coupe (`abattre`/`receper`/`eteter`) à UN secteur et renvoie le
    geste dont la CINÉTIQUE s'appliquera réellement.

    Ce retour n'est pas une coquetterie : un `receper` sur une essence qui ne rejette
    pas EST un abattage, et c'est écrit là, littéralement — la souche est morte, donc
    la repousse suit la courbe de l'abattage (30 ans) et non celle du taillis (10).

    Écrit trois traces dans le milieu (conception §5, décision D-3) — jamais un
    compteur : les scalaires effondrés, la `souche_memory` (« elle rejettera » /
    « le vide restera à combler ») et l'horloge remise à zéro. Les cibles de repousse
    mémorisent le peuplement mûr par un MAXIMUM : recouper avant reconstitution
    n'efface pas la mémoire du terrain.

    PURE (aucun RNG, aucun coût, aucun champ écologique touché) — la couche joueur
    est au-dessus.
    """
    rejette = secteur.get("essence") in ESSENCES_QUI_REJETTENT
    if geste == "eteter":
        souche = "vivante"                       # le tronc reste debout et vivant
    elif geste == "receper" and rejette:
        souche = "vivante"                       # la souche a de la mémoire
    else:
        souche = "morte"
    enregistre = "abattre" if (geste == "receper" and not rejette) else geste

    densite_res, frac_h, _duree = CINETIQUES[enregistre]
    secteur["densite_avant"] = max(secteur.get("densite_avant") or 0.0,
                                   secteur["densite_ligneuse"])
    secteur["hauteur_avant"] = max(secteur.get("hauteur_avant") or 0.0,
                                   secteur["hauteur_canopee"])
    if densite_res is not None:
        # `min` et pas affectation : une friche clairsemée ne DEVIENT pas plus dense
        # parce qu'on l'a coupée (bornes, test ⑥).
        secteur["densite_ligneuse"] = min(secteur["densite_ligneuse"], densite_res)
    secteur["hauteur_canopee"] = round(secteur["hauteur_canopee"] * frac_h, 3)
    secteur["souche_memory"] = souche
    secteur["geste_coupe"] = enregistre
    secteur["annees_depuis_coupe"] = 0.0
    return enregistre


def tick_repousse(ceinture, semaines: float = 1.0) -> None:
    """Fait vieillir les coupes de la ceinture d'un pas de tick — O(4), appelé une
    fois par semaine depuis `sim/engine/boucle.py` AVANT la lumière et l'abri (qui
    lisent la hauteur et la densité du tick).

    **No-op strict** si `ceinture` est absente (cas du golden) ou si aucun secteur ne
    porte de coupe en cours (`geste_coupe is None`) ⇒ aucune écriture, digest intact.

    Déterministe (philo #3) : interpolation linéaire de la valeur résiduelle vers la
    cible mémorisée, sur la durée de la cinétique. Aucun tirage — « l'arbre repousse
    peut-être » n'existe pas. La coupe cesse d'être une coupe quand le peuplement est
    reconstitué ; `souche_memory` reste, elle, comme trace persistante du milieu.
    """
    for s in ceinture or ():
        geste = s.get("geste_coupe")
        if not geste:
            continue
        s["annees_depuis_coupe"] = round(s["annees_depuis_coupe"]
                                         + semaines / SEMAINES_PAR_AN, 6)
        t = s["annees_depuis_coupe"]
        densite_res, frac_h, duree = CINETIQUES[geste]
        cible_d, cible_h = s["densite_avant"], s["hauteur_avant"]
        avance = min(1.0, t / duree) if duree > 0.0 else 1.0

        if densite_res is not None:
            # Départ borné par la cible : sur une friche déjà clairsemée, la coupe
            # n'a rien retiré → la « repousse » ne doit rien ajouter non plus.
            depart = min(densite_res, cible_d)
            d = depart + (cible_d - depart) * avance
            if geste == "abattre":
                # Plancher pionnier, lui aussi borné par la cible : une friche coupée
                # ne devient pas plus fournie qu'elle ne l'était.
                pionnieres = min(DENSITE_PIONNIERE, cible_d)
                d = max(d, pionnieres * min(1.0, t / DUREE_PIONNIERES_ANS))
            s["densite_ligneuse"] = round(min(1.0, max(0.0, d)), 3)

        depart_h = cible_h * frac_h
        s["hauteur_canopee"] = round(max(0.0, depart_h
                                         + (cible_h - depart_h) * avance), 3)
        if avance >= 1.0:
            s["geste_coupe"] = None              # peuplement reconstitué


# ---------------------------------------------------------------------------
# EAU & ROCHE — le milieu pur, et son asymétrie (tronçon ⑤)
# ---------------------------------------------------------------------------
# Après le bois qui repousse, la roche qui ne repousse pas. Ces mutations sont la
# forme la plus nette de la philo #1 : le joueur ne touche AUCUN être vivant, il
# déplace de l'eau et de la terre — et tout le reste (berge gorgée, marécage,
# éboulis) ÉMERGE des circuits déjà en place (conception §3.4, §4.3, §4.5).
#
# Trois asymétries, gravées dans les données et non dans un discours :
#   • l'eau se DÉPLACE et jamais ne se crée : `ligne_eau` monte d'un côté, et c'est
#     tout ce que le moteur sait — le joueur découvre le reste au bord du jardin ;
#   • un OUVRAGE se rompt (8 ans sans entretien), une FORME creusée reste ;
#   • une ENTAILLE de falaise ne se referme jamais, et le matériau mis à nu part.
#
# Comme la sylviculture ci-dessus : mutations PURES (aucun RNG, aucun coût, aucun
# champ écologique touché), la couche joueur est dans `sim/actions/paysage.py`.

# Pas d'un geste sur la ligne d'eau, en cm. Un geste ne bascule pas un régime : il
# faut plusieurs passages pour gorger une berge, ce qui fait de l'endiguement un
# CHANTIER (philo #1 : l'usure de la solution facile). Bornes = plage un peu plus
# large que celle du générateur (`LIGNE_EAU_CM`) : le joueur peut dépasser ce que la
# nature avait posé, pas de plusieurs ordres de grandeur.
LIGNE_EAU_PAS_CM = 30.0
LIGNE_EAU_BORNES = (-150.0, 120.0)

# Une MARE creusée en périphérie : elle amène l'eau à fleur de terrain au bord. Petit
# et positif — une mare n'est pas un barrage, elle ne gorge pas 20 m de jardin.
MARE_LIGNE_EAU_CM = 20.0

# Un ouvrage d'eau non entretenu se rompt vers 8 ans (conception §4.4). Refaire le
# geste EST l'entretien : il remet l'horloge à zéro. Zéro tirage (philo #3) — « le
# barrage tiendra peut-être » n'existe pas ; il tient tant qu'on y retourne.
OUVRAGE_RUPTURE_ANS = 8.0
MARQUEUR_RUPTURE = "🚧"

# Roche retirée par coup de pioche, en cm. Gros (1,5 m) : entailler une falaise de
# 3 à 12 m doit être un chantier de quelques gestes, pas de cinquante.
ENTAILLE_PAS_CM = 150.0

# --- Érosion : de l'état du secteur à une intensité (conception §4.5) ------
# Le sol ne part pas dès qu'on touche à la lisière : il faut que le couvert soit
# VRAIMENT ouvert (seuil de dénudation) — une éclaircie n'érode pas, une coupe rase
# oui. Au-dessus du seuil, l'intensité rampe linéairement jusqu'à 1 (sol nu total).
EROSION_DENUDATION_MIN = 0.25
# Entaille au-delà de laquelle la cicatrice de falaise érode à pleine intensité :
# deux coups de pioche mettent la roche franchement à nu.
ENTAILLE_REFERENCE_CM = 2.0 * ENTAILLE_PAS_CM


def porte_eau(secteur: dict) -> bool:
    """Ce secteur a-t-il une ligne d'eau sur laquelle agir ? Une `riviere` en a une
    par nature ; tout autre secteur en acquiert une si le joueur y a creusé une mare.
    Une falaise n'en a jamais (on ne creuse pas la roche à la bêche)."""
    return secteur["type"] == "riviere" or secteur["ligne_eau"] != 0.0


def deplacer_ligne_eau(secteur: dict, sens: int) -> float:
    """Endigue (`sens = +1`) ou dérive (`sens = -1`) : décale la ligne d'eau d'un pas
    et (re)pose l'OUVRAGE. Renvoie la nouvelle ligne d'eau.

    La ligne d'eau NATURELLE est mémorisée au premier ouvrage seulement : refaire le
    geste ensuite entretient l'ouvrage (horloge à zéro) sans réécrire la référence —
    sinon la rupture ne ramènerait jamais l'eau au-delà du dernier passage. Une mare
    creusée AVANT l'ouvrage fait donc partie de la nature du terrain : elle survit à
    la rupture, l'ouvrage non. C'est la distinction forme/artefact, dans deux lignes.

    PURE : aucun champ écologique touché. Ce que la nouvelle ligne d'eau fait au
    jardin est le travail de `tick_berge` (③) puis de l'hydrologie — le joueur
    n'écrit pas d'humidité, il déplace une nappe (philo #2)."""
    if secteur["ouvrage"] is None:
        secteur["ligne_eau_naturelle"] = secteur["ligne_eau"]
    bas, haut = LIGNE_EAU_BORNES
    secteur["ligne_eau"] = round(min(haut, max(bas, secteur["ligne_eau"]
                                               + sens * LIGNE_EAU_PAS_CM)), 3)
    secteur["ouvrage"] = "endiguer" if sens > 0 else "deriver"
    secteur["annees_depuis_ouvrage"] = 0.0
    return secteur["ligne_eau"]


def creuser_secteur(secteur: dict) -> float:
    """Creuse une MARE dans un secteur de ceinture — le geste `creuser` EXISTANT
    appliqué à une autre cible, pas un geste de plus (kickoff ⑤ §A).

    Une excavation est une FORME donnée au terrain, pas un artefact : elle relève la
    ligne d'eau *et* sa valeur naturelle, donc elle ne rompt jamais et survit à la
    rupture d'un barrage posé après. Exactement le statut du `creuser` de plot, qui
    baisse `altitude` définitivement.

    Renvoie la nouvelle ligne d'eau. PURE."""
    _, haut = LIGNE_EAU_BORNES
    ligne = round(min(haut, secteur["ligne_eau"] + MARE_LIGNE_EAU_CM), 3)
    secteur["ligne_eau"] = ligne
    secteur["ligne_eau_naturelle"] = round(
        min(haut, secteur["ligne_eau_naturelle"] + MARE_LIGNE_EAU_CM), 3)
    return ligne


def entailler_secteur(secteur: dict) -> float:
    """Entaille la falaise : retire un pas de roche. Renvoie la hauteur RÉELLEMENT
    retirée (0.0 si la roche est déjà rasée — il n'y a alors plus rien à entailler).

    IRRÉVERSIBLE, et c'est le contenu du geste : `entaille_cm` ne décroît jamais et
    aucune entrée de `CINETIQUES` ne concerne la falaise. `tick_repousse` ne la
    regarde pas — elle ne boucle que sur `geste_coupe`, qu'`entailler` ne pose pas.
    Certaines échelles ne nous appartiennent pas (conception §4.4).

    Deux conséquences, toutes deux déjà supportées : l'ombre portée diminue (② lit
    `altitude_relative` via `_hauteur_occultante`) et la roche mise à nu part en
    érosion (`erosion_secteur` → `bordure.tick_erosion`). PURE."""
    avant = secteur["altitude_relative"]
    if avant <= 0.0:
        return 0.0
    retiree = min(avant, ENTAILLE_PAS_CM)
    secteur["altitude_relative"] = round(avant - retiree, 3)
    secteur["entaille_cm"] = round(secteur["entaille_cm"] + retiree, 3)
    return retiree


def tick_ouvrages(ceinture, semaines: float = 1.0) -> list[str]:
    """Fait vieillir les OUVRAGES d'eau de la ceinture — O(4), à côté de
    `tick_repousse` (étape 1c de `sim/engine/boucle.py`). Renvoie les marqueurs de log
    des ruptures (liste VIDE le reste du temps).

    Un ouvrage non entretenu se rompt à `OUVRAGE_RUPTURE_ANS` : la ligne d'eau revient
    à sa valeur naturelle et l'ouvrage disparaît. Rien n'avertit (philo #6) ; le
    ledger, lui, le consigne. Leçon : l'artefact demande un entretien perpétuel — ce
    qui est cohérent avec le run éternel (#4), où rien n'est jamais « fini ».

    **No-op strict** sans ceinture (cas du golden) ou sans ouvrage posé. Déterministe :
    un seuil sur une horloge, aucun tirage (philo #3)."""
    lignes: list[str] = []
    for s in ceinture or ():
        if not s.get("ouvrage"):
            continue
        s["annees_depuis_ouvrage"] = round(s["annees_depuis_ouvrage"]
                                           + semaines / SEMAINES_PAR_AN, 6)
        if s["annees_depuis_ouvrage"] < OUVRAGE_RUPTURE_ANS:
            continue
        s["ligne_eau"] = s["ligne_eau_naturelle"]
        s["ouvrage"] = None
        s["annees_depuis_ouvrage"] = 0.0
        lignes.append(f"  {MARQUEUR_RUPTURE} l'ouvrage d'eau "
                      f"({NOMS_COTES[s['cote']]}) a rompu : "
                      f"l'eau reprend son cours ({s['ligne_eau']:.0f} cm)")
    return lignes


def erosion_secteur(secteur: dict) -> float:
    """Intensité d'érosion ∈ [0,1] d'un secteur : ce que son sol nu lâche vers le
    jardin. PURE, dérivée du SEUL état du secteur (aucun champ lu).

    Deux sources, combinées par MAXIMUM (le pire des deux gouverne, elles ne
    s'additionnent pas — un même mètre carré ne part pas deux fois) :
      • la DÉNUDATION d'une coupe = fraction du couvert perdue par rapport au
        peuplement mûr mémorisé (`densite_avant`). Elle se REFERME d'elle-même quand
        `tick_repousse` ramène la densité : l'érosion s'arrête quand la végétation
        revient, sans qu'aucune ligne ne le dise. Un `eteter` conserve la densité →
        n'érode PAS : la trogne est le prélèvement fréquentable, y compris ici ;
      • la CICATRICE d'une falaise entaillée, qui ne se referme jamais et érode donc
        en permanence — le seul retour qui rend l'irréversible visible (philo #5).

    Sous `EROSION_DENUDATION_MIN` : strictement 0. Une éclaircie n'érode pas ; il faut
    avoir vraiment ouvert le couvert. Au-dessus, rampe linéaire jusqu'à 1."""
    cible = secteur.get("densite_avant") or 0.0
    denude = 0.0
    if cible > 0.0:
        denude = max(0.0, 1.0 - secteur["densite_ligneuse"] / cible)
    roche = min(1.0, (secteur.get("entaille_cm") or 0.0) / ENTAILLE_REFERENCE_CM)
    brut = max(denude, roche)
    if brut <= EROSION_DENUDATION_MIN:
        return 0.0
    return round((brut - EROSION_DENUDATION_MIN)
                 / (1.0 - EROSION_DENUDATION_MIN), 4)
