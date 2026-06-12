"""
SYMBIOSE — sim/actions.py
Actions JOUEUR sur le vivant (D11, sous-sprint 2) — coûts/gains de Vigueur.
Spec de référence : `data/code/CONCEPTION_VIGUEUR.md` §3 (catalogue d'actions),
§3.5 (HARVEST_VIGUEUR_COST réel), §4 (Qi territorial, flag `harvested`).

Découpage des responsabilités (décision actée 2026-06-04) :
  - `sim/vigueur.py` : l'ÉTAT joueur + les primitives `spend`/`gain` + le cycle.
    « Combien j'ai et comment ça bouge. »
  - CE module : les CONSTANTES de coût + les ACTIONS. « Ce que les gestes coûtent
    et font. » Il orchestre spend/gain et les mutations écologiques (nécromasse).

Principe directeur (spec §0/§5) : ces actions sont event-driven, AU-DESSUS du
tick écologique déterministe. Le golden ÉCOLOGIQUE (`tests/test_golden.py`) est
une succession spontanée pure — il n'appelle JAMAIS ces fonctions, donc son hash
ne peut pas bouger. Si il bouge, c'est un bug (fuite dans le tick).

Solde insuffisant (décision actée) : on « dépense ce qu'on a » via le ratio
d'effort de `vigueur.spend`. Une action GRADUÉE (récolte) en sort tronquée (gain
∝ ratio) ; une action BINAIRE destructrice (déraciner/écraser) ne produit son
effet QUE si le coût est intégralement payé — forcer le vivant à vide draine la
Vigueur et n'accomplit rien (philo #1/#6, sans sermon).
"""
from __future__ import annotations

from sim.vigueur import spend, gain
from sim.vigueur_plante import maturite, vigueur_plante   # facteurs partagés (mutualisés, pas dupliqués)
from sim.growth import (atteindre_segment,   # seam de perturbation §F (sim→sim, pas de cycle : growth n'importe pas actions)
                        f_lignification, INTENSITE_PIED, SEUIL_DEGAT, COUPE_NETTE)  # calibrage écrasement (volet 2)
from sim.effects import necromass_biomass
from sim import maitrise as M   # couche savoir (D12) — orchestrée ici pour les gains ponctuels §4.3
from fields.population import DENSITE_PAR_SPRITE   # « un geste = un individu = un quantum » (D31.3 §5)
from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE   # reverse classe→clé (seam coût, §10.4)

# Paliers de coût, relatifs à la base 100 / +10 par semaine (spec §3.1, à
# calibrer post-test).
NUL    = 0.0
FAIBLE = 5.0
MODERE = 15.0
ELEVE  = 30.0
URGENCE_MULT = 1.5   # majoration des actions de phase « saison » (urgence, §3.1)

# Malus de microbiome local du bêchage (CONCEPTION_VIGUEUR §3.2, « biner/bêcher :
# microbiome ↓ » — la conception ne chiffrait pas l'ampleur). Knob sobre, calibrage
# post-test : microbiome est sur l'échelle [0, 3] (cf. ecofields), ce malus en
# retire ~1/6 localement — perceptible sans être brutal.
BECHAGE_MICROBIOME_MALUS = 0.5

# Le hook de la conception (§3.5) devient réel : le geste de prélèvement de la
# récolte sélective coûte FAIBLE (remplace le `=0` neutre supprimé de l'engine).
HARVEST_VIGUEUR_COST = FAIBLE

# Gain brut d'une récolte d'organe pleinement mûr (× maturité × effort).
HARVEST_GAIN_FULL = 15.0

# Fraction de `HARVEST_GAIN_FULL · maturité` rendue par `tailler` (décision #3) :
# tailler récupère un PEU de Vigueur (organe coupé), mais reste NET coûteux. Proxy
# `∝ maturité` en attendant les organes mûrs réels (tronçon 5) qui le raffineront.
GAIN_TAILLE_RATIO = 0.3

# Sources PONCTUELLES de Vigueur liées à la maîtrise (CONCEPTION_MAITRISE §4.3) —
# placeholders nommés, *calibrage D12.4*. La découverte motive (petit +), le
# franchissement de palier récompense l'effort (+ plus net). Event-driven, hors
# tick (comme toute la couche Vigueur).
GAIN_DECOUVERTE = FAIBLE    # « chaque découverte donne envie d'en savoir plus » (§4.3)
GAIN_SUCCES     = MODERE    # « un jardinier actif est un jardinier vigoureux » (§4.3)


# =========================================================================
# Seam COÛT D'ACTION (CONCEPTION_MAITRISE §4.2/§10.4) — second seam de la
# maîtrise (le premier, `palier_bonus`, vit dans `vigueur.py`). La maîtrise rend
# les gestes MOINS CHERS en Vigueur, *contextuellement* : selon ce que l'action
# touche. Modèle (§4.2) : `base × f_globale(player) × f_objets(player, objets)`,
# atténuation ∈ ]0,1]. NEUTRE (1.0) tant qu'aucune maîtrise n'est acquise → tous
# les coûts en dur d'avant restent identiques (golden Vigueur intact). Ce seam vit
# ICI (couche d'orchestration qui voit Vigueur ET Maîtrise), pas dans `maitrise.py`
# qui reste pur (sens de dépendance acté i2).
# =========================================================================

# Coûts de BASE par action — les littéraux d'avant, REGROUPÉS en table (ils
# deviennent la `base` du seam ; les constantes restent, on ne supprime rien).
COUTS = {
    "recolter":             HARVEST_VIGUEUR_COST,
    "deraciner":            ELEVE,
    "ecraser":              MODERE,            # × URGENCE_MULT appliqué PAR-DESSUS (phase saison)
    "favoriser_auxiliaire": MODERE,
    "becher":               FAIBLE,
    "grelinette":           MODERE,
    "tailler":              MODERE,            # geste direct sur le vivant (philo #1) — coût modéré
    "manger":               NUL,               # coût NUL → cout_action renvoie 0 sans rien lire (§10.5)
}

# Objets STATIQUES touchés par chaque geste (§10.4, terme 2 : technique + outil/
# structure requis). La CIBLE VIVANTE n'y est PAS (dynamique : elle dépend de la
# plante cliquée → l'appelant l'ajoute via `_objets_action`). Clés = strings au
# même titre que les espèces (maîtrise catalogue-agnostique, i1). Aucun de ces
# objets n'a d'état moteur aujourd'hui → `M.palier(...) == 0` → atténuation neutre
# 1.0 (dégradation gracieuse §10.5) ; la table les NOMME pour quand leur sprint
# (D29/D30/D31) les câblera. Reflète §10.4 telle quelle.
OBJETS_TOUCHES = {
    "recolter":             ("récolte", "sécateur"),
    "deraciner":            ("arrachage", "bêche"),
    "ecraser":              (),                          # geste brut, terme 2 vide (§10.4)
    "favoriser_auxiliaire": ("aménagement-habitat",),
    "becher":               ("bêchage", "bêche"),
    "grelinette":           ("ameublissement", "grelinette"),
    "tailler":              ("taille", "sécateur"),
    "manger":               (),                          # coût NUL → terme 2 vide (§10.5)
}

# Atténuations maximales — PLACEHOLDERS NOMMÉS, *calibrage D12.4*. Bornées < 1 pour
# garantir un PLANCHER strictement positif (atténuation jamais ≤ 0, §4.2) : même un
# joueur omniscient paie un coût résiduel. 0.0 redonnerait le coût en dur.
ATT_GLOBALE_MAX = 0.5   # réduction max par la connaissance écologique GÉNÉRALE (terme 1)
ATT_OBJET_MAX   = 0.5   # réduction max par la maîtrise d'UN objet concret à fond (terme 2)

# Reverse classe → clé catalogue (miroir de `_FAMILLE_DE_ESPECE` côté maitrise i2) :
# pour résoudre la clé d'espèce d'une `PlantInstance` cliquée. Dérivé des catalogues
# moteur, ne duplique aucune liste figée.
_CLE_DE_CLASSE = {
    cls: cle for cle, cls in {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}.items()
}


def _cle_espece(plant) -> str | None:
    """Clé catalogue d'une `PlantInstance` (reverse classe→clé), ou `None` si la
    résolution échoue. Dégradation gracieuse (kickoff §C) : un `None` fait traiter
    le geste comme « sans cible » (terme 2 sans espèce) plutôt que de planter."""
    return _CLE_DE_CLASSE.get(getattr(plant, "plant_class", None))


def _objets_action(action: str, plant=None) -> list[str]:
    """Objets touchés par un geste = la STATIQUE de la table (§10.4) ∪ la cible
    vivante dynamique (clé d'espèce) quand il y a une plante. La cible apporte le
    SPILLOVER famille gratuitement (sa maîtrise monte déjà via §3.1, i2)."""
    objets = list(OBJETS_TOUCHES[action])
    if plant is not None:
        cle = _cle_espece(plant)
        if cle is not None:
            objets.append(cle)
    return objets


def f_globale(game_state: dict, player: str) -> float:
    """Terme 1 (§4.2) — atténuation par la connaissance écologique GÉNÉRALE
    (concepts + vivants découverts), uniforme sur toute action. On lit la
    **complétude-ratio** de i2 (§3.2, ∈ [0,1] — « à quel point je maîtrise ce que
    je connais ») : naturellement bornée → atténuation propre sans log. Forme :
    `1 − ATT_GLOBALE_MAX · mesure`, décroissante vers le plancher `1−ATT_GLOBALE_MAX
    > 0`. PLACEHOLDER NOMMÉ → calibrage D12.4."""
    return 1.0 - ATT_GLOBALE_MAX * M.completude_ratio(game_state, player)


def f_objets(game_state: dict, player: str, objets_touches) -> float:
    """Terme 2 (§4.2) — atténuation par la maîtrise des objets CONCRETS touchés.
    Chaque objet contribue `1 − ATT_OBJET_MAX · palier/PALIER_MAX` ; un objet inconnu
    (palier 0) contribue **neutre 1.0**. On combine par MOYENNE des atténuations
    (sobre, bornée : reste ∈ [plancher, 1], jamais → 0 même avec beaucoup d'objets).
    `None`/`[]` → 1.0 (terme 2 absent). PLACEHOLDER NOMMÉ → calibrage D12.4."""
    if not objets_touches:
        return 1.0
    facteurs = [
        1.0 - ATT_OBJET_MAX * (M.palier(game_state, player, o) / M.PALIER_MAX)
        for o in objets_touches
    ]
    return sum(facteurs) / len(facteurs)


def cout_action(game_state: dict, player: str, action: str,
                objets_touches=None) -> float:
    """Le seam (§4.2). `base × f_globale × f_objets`, atténuation ∈ ]0,1]. Coût NUL
    préservé : si `base == 0` (manger, §10.5) → renvoie 0 SANS rien lire. NEUTRE à
    vide : sans maîtrise, `f_globale == f_objets == 1.0` → `cout_action == base`
    (non-régression du golden Vigueur). L'urgence (`ecraser`) reste un facteur
    SÉPARÉ appliqué par-dessus par l'appelant (ce n'est pas de la maîtrise)."""
    base = COUTS[action]
    if base == 0.0:
        return 0.0
    return base * f_globale(game_state, player) * f_objets(game_state, player, objets_touches)


# --- Ponts maîtrise → Vigueur (§4.3) : orchestration au-dessus des deux couches
# `sim/maitrise.py` reste PUR (il ne crédite pas la Vigueur lui-même) ; c'est ICI,
# la couche d'orchestration, qu'un événement de maîtrise se traduit en gain de
# Vigueur — exactement comme `manger`/`recolter` orchestrent déjà `gain`. La
# détection AUTOMATIQUE de ce qui déclenche ces gains (lecture des signaux du tick,
# §9) est branchée au tronçon i4 ; ici les appels restent explicites (injection).
def observer(game_state: dict, player: str, objet: str) -> bool:
    """Observer un objet → le DÉCOUVRE (§2.1, palier 0→1) et, si c'est une
    NOUVELLE découverte, crédite un petit gain de Vigueur (la motivation, §4.3).
    Idempotent : ré-observer un objet déjà connu ne re-crédite rien. Renvoie True
    ssi une nouvelle découverte a eu lieu."""
    nouveau = M.decouvrir(game_state, player, objet)
    if nouveau:
        gain(game_state, player, GAIN_DECOUVERTE)
    return nouveau


def crediter_succes(game_state: dict, player: str, objet: str) -> int:
    """Enregistre une preuve de maîtrise sur un objet (§2.2) et, à CHAQUE palier
    franchi, crédite la récompense de Vigueur (§4.3) — proportionnelle au nombre de
    paliers gagnés (une fournée qui franchit deux paliers récompense double).
    Renvoie le palier après mise à jour."""
    avant = M.palier(game_state, player, objet)
    apres = M.enregistrer_preuve(game_state, player, objet)
    if apres > avant:
        gain(game_state, player, GAIN_SUCCES * (apres - avant))
    return apres


def manger(game_state: dict, player: str, plant, eco) -> float:
    """Manger un organe nourricier mûr (spec §3.3, première ligne) — le pendant
    « ressourcement GRATUIT » de recolter. Coût **NUL** (§3.3) : aucune dépense.

    Gain ∝ **valeur vivante de l'organe** : on inaugure ENFIN la façade
    `vigueur_plante` comme MODULATEUR DE VALEUR (spec §1) — santé × maturité × Qi
    × gène. Un fruit éclatant nourrit plus qu'une feuille chétive sur sol pauvre.
    (recolter reste, lui, sur `maturite` seule : il met en BANQUE un produit mûr,
    tandis que manger ABSORBE la vitalité — sémantiques distinctes, recâblage de
    recolter sur la façade différé pour préserver sa propriété « net positif ».)

    No-op écolo (décision actée, philo #2) : la plante reste VIVANTE (≠ déraciner)
    et **aucun champ n'est touché**. L'organe est entièrement consommé par le
    joueur → rien ne retourne au sol (pas d'`add_necromass` ; le Qi part vers le
    joueur via `gain`, §4). Toucher `health`/`current_stage` serait un malus
    DIRECT sur la plante — interdit. La déplétion réelle (organe qui disparaît et
    repousse) + la valeur fine par type d'organe relèvent de **D19** ; les
    organes à gain NÉGATIF (manger un nuisible) relèvent de **D31**. v1 ne fixe
    que la comptabilité Vigueur du gain ⇒ manger est répétable (borné par
    `vigueur_max`). NE cible JAMAIS le bourgeon apical : couper l'apex est
    l'action `tailler` (réponse hormonale = **D29**), pas manger.

    Renvoie la valeur de l'organe consommé (gain nominal, avant plafonnement)."""
    gain_organe = HARVEST_GAIN_FULL * vigueur_plante(plant, eco)
    gain(game_state, player, gain_organe)   # coût NUL → pas de spend
    return gain_organe


def recolter(game_state: dict, player: str, plant, eco) -> float:
    """Récolte sélective d'un organe mûr (spec §3.3) — action GRADUÉE.
    Coût FAIBLE ; gain `+ ∝ maturité` ; le Qi est exporté vers le joueur
    (`harvested=True`, §4) tandis qu'une fraction de résidu retourne au sol. La
    plante reste VIVANTE. Si la Vigueur ne couvre pas le coût, l'effort est
    tronqué : gain ET résidu × ratio (récolte partielle). Sur du mûr, net positif
    (gain ≫ coût) — le canal de ressourcement légitime.
    Renvoie le ratio d'effort réalisé ∈ [0, 1]."""
    cost = cout_action(game_state, player, "recolter", _objets_action("recolter", plant))
    ratio = spend(game_state, player, cost)
    gain(game_state, player, HARVEST_GAIN_FULL * maturite(plant) * ratio)
    biomass = (plant.current_stage + 1.0) * 0.4   # même barème que le tick récolte
    eco.add_necromass(*plant.position, biomass * ratio, harvested=True)
    return ratio


def deraciner(game_state: dict, player: str, plant, eco) -> bool:
    """Déracinage d'une plante vivante (spec §3.3) — action BINAIRE destructrice.
    Coût ÉLEVÉ, aucun gain. À la mort, le Qi retourne AU SOL
    (`harvested=False`, §4 : nécromasse ∝ hauteur, comme toute mort naturelle).
    Tout-ou-rien : la plante ne meurt QUE si le coût est intégralement payé. À
    vide, la Vigueur est drainée et rien n'est accompli — le raccourci destructeur
    échoue quand on est épuisé.
    Renvoie True si la plante a effectivement été déracinée."""
    cost = cout_action(game_state, player, "deraciner", _objets_action("deraciner", plant))
    ratio = spend(game_state, player, cost)
    if ratio < 1.0:
        return False
    plant.health = 0
    eco.add_necromass(*plant.position, necromass_biomass(plant), harvested=False)
    return True


def _profondeur(segs: list, i: int) -> int:
    """Profondeur d'un segment dans l'arbre (collet = 0). Local à la sélection de
    cible (l'engine/test choisit le segment ; depuis Godot tronçon 4+ il viendra du
    clic). O(profondeur), borné par MAX_SEGMENTS."""
    d, p = 0, segs[i].parent
    while p is not None:
        d, p = d + 1, segs[p].parent
    return d


def _segment_cible(plant, cible: str) -> int | None:
    """Sélecteur déterministe du segment visé par un geste structurel (point ouvert
    §00 n°3, défaut sobre + signalé) :
      - `cible="apex"`    → l'apex MENEUR (apex à la hauteur de cime la plus haute) :
        l'écimage rabat la flèche.
      - `cible="branche"` → un LATÉRAL (apex non-meneur le plus profond) : l'égourmandage
        retire un gourmand SANS toucher la flèche → la dominance reste ~inchangée
        (elle émerge du choix de cible, pas d'une mécanique dédiée). Repli sur le
        meneur s'il n'existe aucun latéral.
    Renvoie `None` si rien n'est coupable (plante réduite au collet, protégé) : le
    geste reste alors un no-op géométrique (coût/gain conservés — on a quand même
    « taillé »)."""
    segs = plant.segments
    apexes = [i for i, s in enumerate(segs) if s.is_apex]
    if not apexes:
        return None
    z = lambda i: segs[i].base[2] + segs[i].dir[2] * segs[i].length_cm   # hauteur de cime (tip z)
    meneur = max(apexes, key=z)
    target = meneur
    if cible == "branche":
        laterals = [i for i in apexes if segs[i].parent is not None and i != meneur]
        if laterals:
            target = max(laterals, key=lambda i: _profondeur(segs, i))
    return target if segs[target].parent is not None else None   # collet (parent None) → rien à couper


def tailler(game_state: dict, player: str, plant, eco, *, cible: str = "apex",
            segment_id: int | None = None) -> bool:
    """Tailler (écimage si `cible='apex'`, égourmandage si `'branche'`) — geste DIRECT
    sur le vivant (philo #1 : permis mais coûteux), à RÉPONSE ÉMERGENTE (philo #2 :
    on appelle le seam structurel `atteindre_segment`, et c'est le tick de croissance
    suivant qui PRODUIT le débourrement — aucun « +X latéraux » codé en dur).

    `segment_id` (tranche 5 — taille au clic depuis Godot) : si fourni ET valide
    (existe, pas le collet `parent is None`), il REMPLACE le sélecteur déterministe
    `_segment_cible` — le joueur a désigné LA branche à la souris. Sinon (None ou
    invalide), comportement t4 inchangé : `cible` choisit apex/branche. Coût et
    gain identiques dans les deux voies — on ne tarife pas la précision.

    Binaire tout-ou-rien, sur le modèle de `deraciner` : le seam n'est appelé QUE si
    le coût (MODÉRÉ, allégé par la maîtrise via `cout_action`) est intégralement payé.
    Gain en Vigueur ∝ maturité (organe coupé récupéré, décision #3 — proxy raffiné au
    tronçon 5). `eco` est dans la signature par cohérence avec la famille des gestes
    (réservé : tailler n'écrit aucun champ écolo aujourd'hui).
    Renvoie True si le geste a été pleinement payé (et donc appliqué)."""
    cost = cout_action(game_state, player, "tailler", _objets_action("tailler", plant))
    if spend(game_state, player, cost) < 1.0:
        return False                          # Vigueur insuffisante → rien n'est écrit (structure intacte)
    seg_id = None
    if segment_id is not None:
        segs = plant.segments
        if 0 <= segment_id < len(segs) and segs[segment_id].parent is not None:
            seg_id = segment_id               # choix explicite du joueur (clic)
    if seg_id is None:
        seg_id = _segment_cible(plant, cible)
    if seg_id is not None:
        atteindre_segment(plant, seg_id, intensite=1.0)   # ≥ COUPE_NETTE → écimage du sous-arbre ciblé
    gain(game_state, player, HARVEST_GAIN_FULL * maturite(plant) * GAIN_TAILLE_RATIO)
    return True


def ecraser(game_state: dict, player: str, eco, r: int, c: int,
            guilde: str = "ravageur", urgence: bool = True) -> bool:
    """Écraser l'être vivant CLIQUÉ (spec §3.3) — action BINAIRE, RÉELLE (D31.3).
    Le geste suit la souris : on écrase le sprite désigné, QUELLE QUE SOIT sa
    guilde. Le sprite cliqué fournit le plot `(r, c)` ET la guilde (`ravageur`,
    `auxiliaire`, `pollinisateur`, `vers_de_terre`). Le code v1 codait `ravageur`
    en dur → on ne pouvait écraser QUE des nuisibles ; désormais on peut SE
    TROMPER (retour F5 Nico, 2026-06-12 : « il faut pouvoir être maladroit »).

    Coût MODÉRÉ × URGENCE (inchangé — ce geste reste le validateur du multiplicateur
    d'urgence). Effet : retire UN quantum (`DENSITE_PAR_SPRITE`, « un geste = un
    individu », §5) de la guilde ciblée au plot. `GridField.add` borne déjà ≥ 0.
    Tout-ou-rien (binaire) : l'effet n'est appliqué QUE si le coût est intégralement
    payé — forcer le geste à vide draine la Vigueur sans rien accomplir.

    `guilde` inconnue → refus EN AMONT de toute dépense (erreur de protocole, pas
    une maladresse de jeu) : le défaut `ravageur` n'est qu'une compat des appels
    historiques, le pont passe toujours la guilde explicitement.

    Pédagogie (philo #1+#6, sans sermon) : écraser un AUXILIAIRE ou un
    POLLINISATEUR se paie — la régulation/pollinisation locale chute, l'erreur
    d'identification s'apprend par la conséquence. Et le champ REPOUSSE depuis sa
    ressource → quelques semaines plus tard la densité REVIENT. Net négatif sec,
    le raccourci s'use. Le canal vertueux symétrique est `favoriser_auxiliaire`.
    Renvoie True si le geste a été pleinement payé (et donc appliqué)."""
    if guilde not in eco.populations:
        return False
    # Pas de cible vivante de catalogue (les guildes ne sont pas des espèces
    # câblées, D31) → terme 2 vide ; l'URGENCE reste un facteur SÉPARÉ par-dessus.
    cost = cout_action(game_state, player, "ecraser") * (URGENCE_MULT if urgence else 1.0)
    if spend(game_state, player, cost) < 1.0:
        return False
    eco.populations[guilde].add(r, c, -DENSITE_PAR_SPRITE)
    return True


def ecraser_plante(game_state: dict, player: str, plant, eco, *,
                   segment_id: int | None = None, urgence: bool = False) -> bool:
    """Écraser une PLANTE cliquée (volet 2, CONCEPTION_ECRASEMENT §5) — geste DIRECT
    sur le vivant (philo #1), à RÉPONSE ÉMERGENTE (philo #2). Le pied frappe le seam
    structurel partagé (`atteindre_segment`, le MÊME que `tailler`) avec une intensité
    modulée par la résistance de l'espèce et son âge (lignification, Q4) ; la déformation
    (régime DOUX → auxine baissée → ramification émergente au tick) ou l'écimage (régime
    NET) en DÉCOULENT — rien n'est écrit à la main sur la structure.

    `intensite = INTENSITE_PIED × (1 − resistance × f_lignification(age))`. Une espèce
    résistante (pâturin) ou un sujet âgé (tronc) restent DOUX (plient) ; un semis ou une
    espèce fragile (tournesol) passent NET (cassent).

    La MORT (Q3, sentier) : le rejet de souche (growth.py) ressuscitant toute plante sans
    apex, la structure SEULE ne peut pas tuer. En régime NET on entame donc la `health`
    (−1, geste direct comme `deraciner`), SAUF si l'espèce PROFITE de l'écrasement
    (`stimulation_ecrasement` haute → seuil non franchi : le basilic est écimé MAIS repart,
    le tournesol est décapité et meurt en ~3 passages). `health` est l'ENTIER 0-3 ; la
    modulation joue en SEUIL, pas en fraction. Cumulatif (Q5).

    `segment_id` : le segment désigné à la souris si fourni et valide, sinon le COLLET
    (segment 0, Q2) — écimer le collet d'un semis ne retire rien (collet protégé), c'est
    la santé qui réalise la mort. Coût = celui de `tailler` (MODÉRÉ, geste direct, Q6)
    × URGENCE éventuelle ; binaire (effet appliqué QUE si le coût est intégralement payé).
    Renvoie True si le geste a été pleinement payé (et donc appliqué)."""
    cost = (cout_action(game_state, player, "tailler", _objets_action("tailler", plant))
            * (URGENCE_MULT if urgence else 1.0))
    if spend(game_state, player, cost) < 1.0:
        return False                          # Vigueur insuffisante → rien n'est écrit
    cls = plant.plant_class
    age_weeks = max((s.age_weeks for s in plant.segments), default=0)   # ≡ proxy d'âge de growth.py
    intensite = INTENSITE_PIED * (1.0 - cls.resistance_ecrasement * f_lignification(age_weeks))
    intensite = max(0.0, min(1.0, intensite))   # le seam attend une intensité ∈ [0,1]
    seg_id = 0                                  # défaut : le collet (Q2)
    if segment_id is not None and 0 <= segment_id < len(plant.segments):
        seg_id = segment_id                     # segment désigné à la souris
    atteindre_segment(plant, seg_id, intensite)  # DOUX déforme / NET écime (+ auxine)
    if intensite >= COUPE_NETTE and (1.0 - cls.stimulation_ecrasement) >= SEUIL_DEGAT:
        plant.health -= 1                       # NET sur une espèce qui n'en profite pas → sentier
    return True


def favoriser_auxiliaire(game_state: dict, player: str, tile) -> bool:
    """Favoriser un auxiliaire (spec §3.2 / CONCEPTION_VIE_MACRO §5) — action sur
    le MILIEU, le pendant VERTUEUX d'« écraser ». Coût MODÉRÉ. Action binaire :
    effet appliqué seulement si le coût est intégralement payé.

    Effet (défaut SOBRE tranché, point ouvert #1) : pose une rondelle `auxiliaire`
    sur la tuile. Elle est DÉJÀ lue par `_stability_grid` (`population.py:273`)
    comme nectar/refuge → terme-source d'habitat PERSISTANT du champ `auxiliaire`,
    zéro machinerie neuve. Les rondelles sont au niveau TUILE (uniforme) ; le
    placement LOCAL d'habitat (hôtel à insectes à un plot précis) demanderait un
    champ habitat par plot — renvoyé à D30/futur (on ne crée pas de champ neuf pour
    cocher la case).

    Pédagogie : rien tout de suite, puis SEMAINES PLUS TARD les auxiliaires
    s'installent ET RESTENT (plancher d'habitat) → régulation émergente, durable —
    contraste avec « écraser » dont la pression revient.

    Renvoie True si payé ET une rondelle a pu être posée. Échec (et Vigueur tout de
    même dépensée, contrat binaire) si la Vigueur ne couvre pas le coût ; renvoie
    False sans effet si toutes les tiges sont déjà saturées (cas-bord : 10 tiges ×
    3 rondelles, jamais atteint en pratique)."""
    cost = cout_action(game_state, player, "favoriser_auxiliaire",
                       OBJETS_TOUCHES["favoriser_auxiliaire"])
    if spend(game_state, player, cost) < 1.0:
        return False
    for slot in tile.stakes:
        if slot.add("auxiliaire"):
            return True
    return False


def becher(game_state: dict, player: str, eco, r: int, c: int) -> bool:
    """Biner / bêcher — retourner la terre (spec §3.2). Action BINAIRE, coût FAIBLE
    (geste rapide, « fausse bonne idée »). Effet : tue la faune du sol → retire un
    quantum de `vers_de_terre` ET abaisse le `microbiome` local de
    `BECHAGE_MICROBIOME_MALUS`. Tout-ou-rien : appliqué seulement si payé.

    Pédagogie « visuel AVANT santé » (CONCEPTION_VIE_MACRO §5) : la chute de
    `vers_de_terre` fait DISPARAÎTRE des sprites de vers — feedback viscéral
    immédiat — *avant* la dette différée `microbiome ↓ → uptake ↓ → vigueur ↓` des
    plantes. Le joueur découvre le bon outil par la conséquence (philo #1/#6, sans
    sermon). Le jumeau qui PRÉSERVE est `grelinette`.
    Renvoie True si le geste a été pleinement payé (et donc appliqué)."""
    cost = cout_action(game_state, player, "becher", OBJETS_TOUCHES["becher"])
    if spend(game_state, player, cost) < 1.0:
        return False
    eco.populations["vers_de_terre"].add(r, c, -DENSITE_PAR_SPRITE)
    eco.microbiome.add(r, c, -BECHAGE_MICROBIOME_MALUS)
    return True


def grelinette(game_state: dict, player: str) -> bool:
    """Grelinette — ameublir SANS retourner (spec §3.2, principe no-dig). Action
    BINAIRE, coût MODÉRÉ. Le JUMEAU QUI PRÉSERVE de `becher` : même intention
    (décompacter) mais ne tue NI vers NI microbiome → no-op écologique côté Python
    pour l'instant. Livré dès maintenant (point ouvert #2, défaut sobre tranché)
    pour ancrer le couple pédagogique becher/grelinette : le contraste s'enseigne
    À L'ŒIL (les sprites de vers disparaissent après bêchage, restent après
    grelinette), pas par un texte.

    Son BÉNÉFICE propre (aération + infiltration ↑) attend le champ
    structure/compaction du sol → DIFFÉRÉ à D30 (on n'invente pas D30 ici). D'ici
    là, grelinette ne fait que dépenser la Vigueur du travail du sol sans dette
    biologique — c'est déjà le bon geste, son gain mécanique viendra.
    Renvoie True si le geste a été pleinement payé."""
    cost = cout_action(game_state, player, "grelinette", OBJETS_TOUCHES["grelinette"])
    return spend(game_state, player, cost) >= 1.0
