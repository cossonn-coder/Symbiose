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
from sim.effects import necromass_biomass
from sim import maitrise as M   # couche savoir (D12) — orchestrée ici pour les gains ponctuels §4.3
from fields.population import DENSITE_PAR_SPRITE   # « un geste = un individu = un quantum » (D31.3 §5)

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

# Sources PONCTUELLES de Vigueur liées à la maîtrise (CONCEPTION_MAITRISE §4.3) —
# placeholders nommés, *calibrage D12.4*. La découverte motive (petit +), le
# franchissement de palier récompense l'effort (+ plus net). Event-driven, hors
# tick (comme toute la couche Vigueur).
GAIN_DECOUVERTE = FAIBLE    # « chaque découverte donne envie d'en savoir plus » (§4.3)
GAIN_SUCCES     = MODERE    # « un jardinier actif est un jardinier vigoureux » (§4.3)


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
    ratio = spend(game_state, player, HARVEST_VIGUEUR_COST)
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
    ratio = spend(game_state, player, ELEVE)
    if ratio < 1.0:
        return False
    plant.health = 0
    eco.add_necromass(*plant.position, necromass_biomass(plant), harvested=False)
    return True


def ecraser(game_state: dict, player: str, eco, r: int, c: int,
            urgence: bool = True) -> bool:
    """Écraser un nuisible (spec §3.3) — action BINAIRE, désormais RÉELLE (D31.3).
    L'aveu de la v1 (« aucune entité nuisible n'existe encore ») est levé : le
    champ `ravageur` (D31.1/D31.2) fournit l'entité ciblable, et le sprite cliqué
    fournit le plot `(r, c)`.

    Coût MODÉRÉ × URGENCE (inchangé — ce geste reste le validateur du multiplicateur
    d'urgence). Effet : retire UN quantum (`DENSITE_PAR_SPRITE`, « un geste = un
    individu », §5) de `ravageur` au plot ciblé. `GridField.add` borne déjà ≥ 0.
    Tout-ou-rien (binaire) : l'effet n'est appliqué QUE si le coût est intégralement
    payé — forcer le geste à vide draine la Vigueur sans rien accomplir.

    Pédagogie (philo #1, sans sermon) : le champ REPOUSSE depuis sa ressource
    (l'hôte-feuillage est toujours là) → quelques semaines plus tard la pression
    REVIENT. Net négatif sec, le raccourci s'use. Le canal vertueux symétrique est
    `favoriser_auxiliaire` (régulation émergente, durable).
    Renvoie True si le geste a été pleinement payé (et donc appliqué)."""
    cost = MODERE * (URGENCE_MULT if urgence else 1.0)
    if spend(game_state, player, cost) < 1.0:
        return False
    eco.populations["ravageur"].add(r, c, -DENSITE_PAR_SPRITE)
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
    if spend(game_state, player, MODERE) < 1.0:
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
    if spend(game_state, player, FAIBLE) < 1.0:
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
    return spend(game_state, player, MODERE) >= 1.0
