"""
SYMBIOSE — sim/actions/paysage.py
Les gestes JOUEUR sur le PAYSAGE : sylviculture (④) puis eau & roche (⑤) de la
ceinture périphérique (sprint PÉRIPHÉRIE, D73). Spec :
`docs/champs/peripherie/conception_peripherie.md` §3.3 (le phénomène), §3.4 (l'eau),
§4.3 (les gestes), §4.4 (les cinétiques), §4.5 (l'érosion), §5 (la comptabilité).

Trois gestes que le paysan distingue et que le jeu doit distinguer :

  • `abattre` — l'arbre meurt. Trouée franche, lumière au sol, structure perdue.
  • `receper` — coupe au ras de la souche. Sur une essence qui REJETTE, l'arbre ne
                meurt pas : il rajeunit. C'est un flux de bois renouvelable.
  • `eteter`  — la trogne : on prend la tête, le tronc reste et vieillit.

Ce n'est pas leur effet immédiat qui enseigne (les trois font tomber du bois), c'est
l'ASYMÉTRIE DE LEURS CINÉTIQUES : 5 ans, 10 ans, 30 ans. Rien ne l'annonce, rien ne
bloque le geste destructeur (philo #6) — abattre toute la lisière sud DOIT être
possible ; c'est le jardin qui répond, pas un avertissement.

Le ⑤ ajoute les gestes du MILIEU PUR — la philo #1 dans sa forme la plus nette, on ne
touche aucun être vivant :

  • `endiguer` / `deriver` — relever / abaisser la ligne d'eau d'un secteur en eau.
                     Le joueur découvre qu'il a **déplacé** l'eau, pas créé : la
                     berge se gorge ici, s'assèche là. Un OUVRAGE, donc : il se rompt
                     sans entretien (8 ans, `tick_ouvrages`).
  • `creuser`      — le geste EXISTANT (`sim/actions/gestes.py`) appliqué à une autre
                     cible : une MARE de bordure. Aucun verbe de plus.
  • `entailler`    — retirer de la roche à une falaise. IRRÉVERSIBLE, et c'est tout
                     le contenu du geste : rien ne la fait revenir, jamais.

Et leur conséquence la plus lisible, l'ÉROSION (`bordure.tick_erosion`) : un couvert
rasé ou une roche mise à nu déposent des colluvions sur les plots du bord. C'est la
seule trace qu'une coupe excessive laisse DANS LE SOL, et le seul canal qui rende
l'irréversible visible (philo #5).

Séparation des responsabilités (un fichier = une responsabilité) :
  - `fields/peripherie.py` — l'ÉTAT du secteur, sa mutation (`couper_secteur`) et sa
    cinétique de retour (`tick_repousse`). Pur, sans joueur.
  - CE module — la couche JOUEUR : gate d'outil, coût de Vigueur, retour de matière
    au sol, trace au ledger. Aucune règle écologique n'est dupliquée ici.

⚠️ JUSTIFICATION DU COÛT (décision D-3, conception §5) : le coût de Vigueur est ÉLEVÉ
au titre de l'EFFORT PHYSIQUE, **pas** au titre d'« action directe sur le vivant »
(philo #1). L'arbre périphérique est un AGRÉGAT de secteur, pas une `PlantInstance` ;
fonder un barème sur cette fiction se paierait plus tard, quand la ceinture gagnera
d'autres gestes. Abattre coûte cher parce qu'on abat un arbre à la hache.

GARDE-FOU DE COUCHE / GOLDEN : event-driven, AU-DESSUS du tick, comme tout
`sim/actions`. Le golden écologique est une succession spontanée SANS joueur → il
n'appelle jamais ces fonctions et n'a pas de clé `ceinture` → hash intact. S'il bouge,
c'est une fuite dans le tick (BUG), pas un re-figeage.
"""
from __future__ import annotations

from fields.peripherie import (COTES, NOMS_COTES, couper_secteur, plots_de_bord,
                               creuser_secteur, deplacer_ligne_eau,
                               entailler_secteur, porte_eau)
from sim.vigueur import spend
from .couts import cout_action, OBJETS_TOUCHES
from .deblocage import est_debloque

# Masse de litière `bois` déposée sur un plot de bord AU CONTACT, par cm de hauteur
# retirée et à densité ligneuse 1.0. PLACEHOLDER de calibrage F5, du même ordre que
# `BOIS_PAR_CM` (0.03 par cm de segment taillé) : une lisière de 15 m à densité 0.75
# rase rend ici ~2.2 par plot de contact, soit quelques dizaines d'unités sur la
# bande — l'équivalent de plusieurs squelettes d'arbres, ce qui est la bonne échelle.
BOIS_COUPE_PAR_CM = 0.002

# Le bois tombe PRÈS du bord : deux rangées de plots (le houppier déborde d'un mètre
# sur le jardin, le tronc reste dehors). On ne charrie pas le bois au milieu du
# potager — c'est au joueur d'aller le chercher (`empiler_bois`, `broyer`).
BOIS_PORTEE_CM = 100.0
# Grosseur du bois de coupe (⑦bis) : houppier et rémanents (le tronc reste dehors),
# branches de 5-8 cm → décompo de plusieurs années.
BOIS_COUPE_DIAM_CM = 6.0

# Marqueur de log, style des marqueurs du tick (🌱 🪦 🍂 …). Le ledger des voix le
# consomme HORS tick (`sim/journal.consigner`) ; le parseur de `sim/evenements.py`
# l'apprendra au tronçon ⑥ — d'ici là une ligne non reconnue est ignorée sans dommage
# (patron `sim/quetes._consigner_accomplissement`).
MARQUEUR_COUPE = "🪓"
LIBELLE_GESTE = {"abattre": "Abattage", "receper": "Recépage", "eteter": "Étêtage"}


def _secteur(game_state: dict, cote: int) -> dict | None:
    """Le secteur de ce bord dans la ceinture courante, ou `None` s'il n'y a pas de
    ceinture (jardin sans périphérie posée) ou si le côté n'existe pas. Lecture
    PURE : ne crée aucune clé (le golden n'a pas de `ceinture`)."""
    ceinture = game_state.get("ceinture")
    if not ceinture or cote not in COTES:
        return None
    for s in ceinture:
        if s["cote"] == cote:
            return s
    return None


def _deposer_bois(game_state: dict, cote: int, masse_contact: float) -> float:
    """Fait tomber le bois coupé au SOL, en parcelles de litière typées `bois`, sur
    les plots du bord concerné de chaque tuile (poids décroissant avec la distance
    au bord, `plots_de_bord`). Renvoie la masse totale déposée.

    ⚠️ Le bois est une MATIÈRE POSÉE, pas une jauge (conception §5, précision Nico) :
    il n'existe PAS de nature `"bois"` dans `mulch_stock` (`NATURES_MULCH` = paille ·
    brf · aiguilles · feuilles) et il ne faut pas en créer une. Le joueur va chercher
    le bois là où il est tombé : `empiler_bois` (→ pile, qui devient un habitat — le
    bac, lui, REFUSE le bois) ou `broyer` (→ BRF, avec sa faim d'azote D40). Créditer
    un stock court-circuiterait tout le circuit décompo/structures et remplacerait
    une matière qu'on VOIT par un compteur qu'on lit (philo #5).

    Une tuile qui ne touche pas ce bord ne reçoit RIEN (`plots_de_bord` rend un
    générateur vide) — on ne balaie jamais la grille (réflexe D32)."""
    if masse_contact <= 0.0:
        return 0.0
    total = 0.0
    ecos = game_state.get("eco") or {}
    for tile in game_state.get("tiles") or ():
        eco = ecos.get(tile.tile_id)
        if eco is None:
            continue
        for r, c, poids in plots_de_bord(cote, eco.rows, eco.cols,
                                         (tile.origin_x_cm, tile.origin_y_cm),
                                         BOIS_PORTEE_CM):
            masse = masse_contact * poids
            eco.deposer_litiere(r, c, "bois", masse, BOIS_COUPE_DIAM_CM)
            total += masse
    return total


def _consigner(game_state: dict, verbe: str, secteur: dict, cinetique: str) -> None:
    """Trace au LEDGER (conception §5, forme 2) : une ligne de log PARSABLE dans le
    canal existant `game_state["log"]`, que `sim/journal.consigner` verse au ledger
    des voix après le tick (carnet, encyclopédie du geste D60, détection de maîtrise).
    Le geste est ENREGISTRÉ, jamais SCORÉ — aucun compteur d'impact cumulé, aucune
    jauge (philo #5). No-op silencieux hors serveur (pas de clé `log`)."""
    log = game_state.get("log")
    if log is None:
        return
    essence = secteur.get("essence") or secteur["type"]
    note = "" if cinetique == verbe else " (la souche ne rejettera pas)"
    log.append(f"  {MARQUEUR_COUPE} {LIBELLE_GESTE[verbe]} "
               f"({NOMS_COTES[secteur['cote']]}) : {essence}, "
               f"souche {secteur['souche_memory']}{note}")


def _couper(game_state: dict, player: str, verbe: str, cote: int) -> bool:
    """Tronc commun des trois gestes forestiers. Renvoie True si le geste a été
    pleinement payé (et donc appliqué).

    Ordre des portes — « refuser sans rien coûter » (patron `planter`/lot vide) :
      1. pas de ceinture / côté inconnu → erreur de protocole, aucun effet ;
      2. geste non ouvert pour cet avatar → **l'outil manque** (`GESTE_UNLOCK` :
         hache pour abattre, serpe pour recéper, avoir recépé pour étêter). Sans
         hache on ne fait rien et **ça ne coûte rien** : l'outil est un pré-requis
         physique, pas une maladresse de jeu à sanctionner. Le pont gate déjà la
         palette en amont ; ce gate est la ceinture de sécurité côté moteur ;
      3. rien de ligneux à couper (secteur rase) → aucun effet. On ne « débroussaille »
         pas une prairie ni une rivière ;
      4. Vigueur — binaire tout-ou-rien (modèle `deraciner`) : le secteur ne bouge
         QUE si le coût est intégralement payé. Forcer le geste à vide draine la
         Vigueur et n'abat rien.
    """
    secteur = _secteur(game_state, cote)
    if secteur is None:
        return False
    if not est_debloque(game_state, player, verbe):
        return False
    if secteur["densite_ligneuse"] <= 0.0 and secteur["hauteur_canopee"] <= 0.0:
        return False
    if verbe == "eteter" and secteur["hauteur_canopee"] <= 0.0:
        return False                          # pas de tête à rabattre

    cost = cout_action(game_state, player, verbe, OBJETS_TOUCHES[verbe])
    if spend(game_state, player, cost) < 1.0:
        return False                          # secteur ET bord intacts

    densite = secteur["densite_ligneuse"]     # ce qui est DEBOUT au moment du coup
    hauteur = secteur["hauteur_canopee"]
    cinetique = couper_secteur(secteur, verbe)
    # Retour de matière ∝ au volume réellement retiré (densité × hauteur retirée) :
    # abattre et recéper prennent la même chose (c'est tout l'intérêt du taillis),
    # étêter n'en prend que la tête.
    retiree = max(0.0, hauteur - secteur["hauteur_canopee"])
    _deposer_bois(game_state, cote, BOIS_COUPE_PAR_CM * densite * retiree)
    _consigner(game_state, verbe, secteur, cinetique)
    return True


def abattre(game_state: dict, player: str, cote: int) -> bool:
    """Abattre la lisière d'un bord (hache, coût TRÈS ÉLEVÉ). La trouée s'ouvre :
    densité effondrée, canopée à terre, souche MORTE. La lumière et le vent entrent
    au jardin dès le tick suivant (`light`/`abri` relisent la ceinture, leurs caches
    invalident sur hauteur et densité) — et la structure ne reviendra qu'en 30 ans,
    même si les ronces comblent le vide en 4 (`tick_repousse`). Le bois tombe au sol
    sur les plots du bord.

    Geste destructeur JAMAIS bloqué (philo #6) : on peut raser les quatre côtés."""
    return _couper(game_state, player, "abattre", cote)


def receper(game_state: dict, player: str, cote: int) -> bool:
    """Recéper la lisière d'un bord (serpe, coût ÉLEVÉ) — couper au ras pour que ça
    repousse plus fort. Sur charme, aulne ou saule la souche est VIVANTE et le
    peuplement revient en 10 ans : un flux de bois renouvelable, l'inverse d'une
    ressource qu'on épuise. Sur hêtre ou bouleau, la souche ne rejette pas et
    **le geste est un abattage** — 30 ans. Rien ne le dit avant, rien ne l'empêche :
    ça s'apprend en le faisant, ou à l'encyclopédie une fois la maîtrise acquise."""
    return _couper(game_state, player, "receper", cote)


def eteter(game_state: dict, player: str, cote: int) -> bool:
    """Étêter la lisière d'un bord (serpe, coût ÉLEVÉ) — la TROGNE : on prend la
    tête, le tronc reste. La densité ligneuse est CONSERVÉE (aucune tige retirée),
    seule la hauteur est rabattue de ~40 %, et la tête revient en 5 ans. C'est le
    prélèvement le plus fréquentable — l'arbre étêté vit plus vieux que l'arbre
    libre, son tronc se creuse et devient un habitat."""
    return _couper(game_state, player, "eteter", cote)


# ---------------------------------------------------------------------------
# EAU & ROCHE (tronçon ⑤) — le milieu pur
# ---------------------------------------------------------------------------
# Aucun de ces gestes ne touche un être vivant : on déplace de l'eau et de la terre,
# et le jardin répond (philo #1/#2). Le coût est un coût d'EFFORT, comme pour la
# sylviculture — un chantier de terrassement, pas une agression du vivant.

MARQUEUR_TERRE = "⛏"
LIBELLE_TERRE = {
    "endiguer": "Endiguement", "deriver": "Dérivation",
    "creuser": "Mare creusée", "entailler": "Entaille de falaise",
}


def _payer(game_state: dict, player: str, verbe: str) -> bool:
    """Débit de Vigueur binaire tout-ou-rien (modèle `deraciner`/`_couper`) : renvoie
    True ssi le coût a été intégralement payé. À appeler APRÈS les portes métier, pour
    que « refuser » ne coûte JAMAIS rien."""
    cost = cout_action(game_state, player, verbe, OBJETS_TOUCHES[verbe])
    return spend(game_state, player, cost) >= 1.0


def _consigner_terre(game_state: dict, verbe: str, secteur: dict,
                     detail: str) -> None:
    """Trace au LEDGER d'un geste d'eau ou de roche (jumeau de `_consigner`, marqueur
    distinct). Enregistré, jamais scoré — aucun compteur d'impact cumulé (philo #5,
    décision D-3). No-op silencieux hors serveur (pas de clé `log`)."""
    log = game_state.get("log")
    if log is None:
        return
    log.append(f"  {MARQUEUR_TERRE} {LIBELLE_TERRE[verbe]} "
               f"({NOMS_COTES[secteur['cote']]}) : {detail}")


def endiguer(game_state: dict, player: str, cote: int) -> bool:
    """Endiguer un bord en eau (bêche, coût ÉLEVÉ) — relever la ligne d'eau d'un pas.

    Le moteur n'écrit RIEN d'autre que `ligne_eau` : c'est `tick_berge` (③) qui pousse
    ensuite l'eau dans les pores du bord, `tick_hydrology` qui capture le surplus en
    lame de surface, `tick_ruissellement` qui l'étale vers les creux et `tick_marais`
    qui en tire la mémoire puis le marécage. Le joueur, lui, constate qu'il a
    **déplacé** l'eau — et que gorger une berge demande plusieurs passages.

    Pose un OUVRAGE : sans y revenir, il rompt vers 8 ans et l'eau reprend son cours
    (`tick_ouvrages`). Refaire le geste EST l'entretien."""
    secteur = _secteur(game_state, cote)
    if secteur is None or not est_debloque(game_state, player, "endiguer"):
        return False
    if not porte_eau(secteur):
        return False                          # rien à endiguer sur un bord à sec
    if not _payer(game_state, player, "endiguer"):
        return False                          # secteur intact
    ligne = deplacer_ligne_eau(secteur, +1)
    _consigner_terre(game_state, "endiguer", secteur, f"ligne d'eau {ligne:.0f} cm")
    return True


def deriver(game_state: dict, player: str, cote: int) -> bool:
    """Dériver un bord en eau (bêche, coût ÉLEVÉ) — abaisser la ligne d'eau d'un pas :
    le bord s'assèche, et si la ligne passe en creux le lit APPELLE l'eau du jardin.
    C'est le geste qui enseigne l'autre moitié de la leçon : ce qu'on retire ici
    manque là. Pose le même OUVRAGE qu'`endiguer`, avec la même fragilité — un fossé
    non entretenu se comble."""
    secteur = _secteur(game_state, cote)
    if secteur is None or not est_debloque(game_state, player, "deriver"):
        return False
    if not porte_eau(secteur):
        return False
    if not _payer(game_state, player, "deriver"):
        return False
    ligne = deplacer_ligne_eau(secteur, -1)
    _consigner_terre(game_state, "deriver", secteur, f"ligne d'eau {ligne:.0f} cm")
    return True


def creuser_peripherie(game_state: dict, player: str, cote: int) -> bool:
    """Creuser une MARE dans un bord de ceinture.

    ⚠️ Ce n'est PAS un geste de plus : c'est le verbe `creuser` EXISTANT
    (`sim/actions/gestes.py`, geste de BASE à la bêche) appliqué à une autre CIBLE.
    Même entrée de `COUTS`, même `OBJETS_TOUCHES`, même déblocage, même fiche
    d'encyclopédie — seule la cible change (un secteur au lieu d'un plot). Créer un
    `creuser_mare` aurait dédoublé un geste que le joueur pense déjà comme un seul.

    Une excavation est une FORME, pas un artefact : elle relève la ligne d'eau ET sa
    valeur naturelle, donc elle ne rompt jamais (contrairement à un barrage). On ne
    creuse pas la roche à la bêche → refusé sur une falaise, sans rien coûter."""
    secteur = _secteur(game_state, cote)
    if secteur is None or not est_debloque(game_state, player, "creuser"):
        return False
    if secteur["type"] == "falaise":
        return False                          # la roche ne se creuse pas à la bêche
    if not _payer(game_state, player, "creuser"):
        return False
    ligne = creuser_secteur(secteur)
    _consigner_terre(game_state, "creuser", secteur, f"ligne d'eau {ligne:.0f} cm")
    return True


def entailler(game_state: dict, player: str, cote: int) -> bool:
    """Entailler une falaise (pioche, coût TRÈS ÉLEVÉ) — retirer un pas de roche.

    **Le seul geste du jeu dont on ne revient pas**, et c'est délibéré : aucune
    cinétique de retour, `entaille_cm` ne décroît jamais. *Certaines échelles ne nous
    appartiennent pas.* Rien ne l'annonce et rien ne l'empêche (philo #6) — le jardin
    répond de deux manières : l'ombre portée diminue (② relit `altitude_relative`,
    les caches lumière/abri invalident sur la hauteur) et la roche mise à nu part en
    ÉROSION, indéfiniment (`bordure.tick_erosion`).

    Refusé — sans rien coûter — hors falaise ou sur une roche déjà rasée : il n'y a
    alors plus rien à entailler."""
    secteur = _secteur(game_state, cote)
    if secteur is None or not est_debloque(game_state, player, "entailler"):
        return False
    if secteur["type"] != "falaise" or secteur["altitude_relative"] <= 0.0:
        return False
    if not _payer(game_state, player, "entailler"):
        return False
    retiree = entailler_secteur(secteur)
    _consigner_terre(game_state, "entailler", secteur,
                     f"{retiree:.0f} cm de roche retirés, "
                     f"il reste {secteur['altitude_relative']:.0f} cm")
    return True
