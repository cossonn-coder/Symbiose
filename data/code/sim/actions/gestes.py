"""
SYMBIOSE — sim/actions/gestes.py
Les gestes JOUEUR sur le MILIEU et sur le VIVANT (D11) : manger, planter, arroser,
récolter, déraciner, tailler, écraser (vivant/plante), favoriser un auxiliaire,
bêcher, grelinette. Coûts/gains de Vigueur via le seam `couts.cout_action`.

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
from sim.vigueur_plante import maturite, vigueur_plante, sante, qi_local   # facteurs partagés (mutualisés, pas dupliqués)
from sim.growth import (atteindre_segment,   # seam de perturbation §F (sim→sim, pas de cycle : growth n'importe pas actions)
                        f_lignification, INTENSITE_PIED, SEUIL_DEGAT, COUPE_NETTE)  # calibrage écrasement (volet 2)
from sim.effects import deposer_mort   # mort → squelette persistant (②B), point d'entrée unique
from fields.ecofields import BOIS_PAR_CM, ECRASER_FRAG_BOOST   # litière `bois` (taille/écimage) + boost fragmentation (②)
from fields.population import DENSITE_PAR_SPRITE   # « un geste = un individu = un quantum » (D31.3 §5)
from fields.alarme import declencher_alarme, ALARME_DEPOT   # phéromone d'alarme apienne (⑦ §J)
from fields.seedbank import GrainEnAttente          # dépôt de `planter` (germination différée, distinct de la banque-sol)
from .couts import cout_action, _objets_action, OBJETS_TOUCHES, URGENCE_MULT

# Dose d'humidité d'un arrosage (CONCEPTION_PLANTER_ARROSER §4, Q9), échelle [0,3].
# Calée sur l'aléa « Pluies » (`+0.5`) : un geste = une bonne pluie locale. Cap 3.0
# appliqué dans `arroser` ; le tick (évaporation × drainage) la fait redescendre.
DOSE_ARROSAGE = 0.5

# Malus de microbiome local du bêchage (CONCEPTION_VIGUEUR §3.2, « biner/bêcher :
# microbiome ↓ » — la conception ne chiffrait pas l'ampleur). Knob sobre, calibrage
# post-test : microbiome est sur l'échelle [0, 3] (cf. ecofields), ce malus en
# retire ~1/6 localement — perceptible sans être brutal.
BECHAGE_MICROBIOME_MALUS = 0.5

# Gain brut d'une récolte d'organe pleinement mûr (× maturité × effort).
HARVEST_GAIN_FULL = 15.0

# Fraction de `HARVEST_GAIN_FULL · maturité` rendue par `tailler` (décision #3) :
# tailler récupère un PEU de Vigueur (organe coupé), mais reste NET coûteux. Proxy
# `∝ maturité` en attendant les organes mûrs réels (tronçon 5) qui le raffineront.
GAIN_TAILLE_RATIO = 0.3


def manger(game_state: dict, player: str, plant, eco, *, fruit_index=None) -> float:
    """Manger un organe nourricier mûr (spec §3.3, première ligne) — le pendant
    « ressourcement GRATUIT » de recolter. Coût **NUL** (§3.3) : aucune dépense.

    Deux modes (③ absorbe D19) :

    • CIBLÉ (`fruit_index` fourni) — on consomme UN fruit traçable précis
      (`plant.fruits[fruit_index]`). Gain ∝ **maturité de CE fruit** : un fruit
      vert nourrit peu, un fruit éclatant beaucoup. Le fruit DISPARAÎT ensuite
      (déplétion réelle D19) → il ne tombera pas en litière et ne sera pas
      remangé. La valeur reprend les autres facteurs de la façade `vigueur_plante`
      (santé × Qi × gène) mais SUBSTITUE la maturité de l'organe à celle de la
      plante. Index hors-borne ⇒ repli sur le mode générique (no-op de sécurité).

    • GÉNÉRIQUE (legacy, `fruit_index=None`) — pas de fruit ciblé : on inaugure la
      façade `vigueur_plante` comme MODULATEUR DE VALEUR (spec §1), santé ×
      maturité-plante × Qi × gène. C'est le chemin historique (carnet/tests
      vigueur D1-D4) — conservé pour les organes non encore tracés (feuille,
      fleur) et la rétro-compatibilité.

    (recolter reste, lui, sur `maturite` seule : il met en BANQUE un produit mûr,
    tandis que manger ABSORBE la vitalité — sémantiques distinctes, recâblage de
    recolter sur la façade différé pour préserver sa propriété « net positif ».)

    No-op écolo (philo #2) : la plante reste VIVANTE (≠ déraciner) et **aucun
    champ n'est touché**. L'organe est entièrement consommé par le joueur → rien
    ne retourne au sol (le Qi part vers le joueur via `gain`, §4). Toucher
    `health`/`current_stage` serait un malus DIRECT — interdit. Les organes à gain
    NÉGATIF (manger un nuisible) relèvent de **D31**. NE cible JAMAIS le bourgeon
    apical : couper l'apex est l'action `tailler` (D29), pas manger.

    Renvoie la valeur de l'organe consommé (gain nominal, avant plafonnement)."""
    if fruit_index is not None and 0 <= fruit_index < len(plant.fruits):
        fruit = plant.fruits.pop(fruit_index)   # déplétion réelle (D19) : l'organe disparaît
        gain_organe = (HARVEST_GAIN_FULL * sante(plant) * fruit.maturite
                       * qi_local(plant, eco) * plant.gene("vigueur"))
    else:
        gain_organe = HARVEST_GAIN_FULL * vigueur_plante(plant, eco)
    gain(game_state, player, gain_organe)   # coût NUL → pas de spend
    return gain_organe


def planter(game_state: dict, player: str, tile, eco, species: str,
            r: int, c: int) -> bool:
    """Planter (spec §3.2 / CONCEPTION_PLANTER_ARROSER §2.1, Q1) — geste sur le
    MILIEU, canal VERTUEUX (philo #1). Le geste **ne fait PAS pousser** une plante :
    il DÉPOSE une graine (`GrainEnAttente`) qui germera plus tard via la
    **succession ordinaire**, quand le plot sera libre ET la niche favorable. On
    enseigne ainsi « le bon moment » (planter hors saison → ça ne lève pas →
    hypothèse, philo #6) ; aucun semis n'est spawné directement (philo #2 : pas
    d'écriture directe sur le vivant, c'est le tick qui lèvera).

    Source = **banque-joueur uniquement** (Q2) : `PlayerSeedBank.take(species)`
    (FIFO, gènes hérités). **Refus si lot vide** — EN AMONT de toute dépense (on ne
    paie pas la Vigueur d'un semis qu'on ne peut pas faire ; symétrique du refus de
    protocole d'`ecraser`). Les gènes de la graine sont copiés TELS QUELS dans le
    grain (PAS de moyennage banque-sol → la sélection D17/D22 garde son sens).

    `cultive=True` (Q5/B) est posé sur le dépôt et **transmis à la plante** quand
    elle germe (`maitrise_detection.marquer_replante` → cultivé vs féral, §9.4).

    Coût **FAIBLE**, phase planification (Q7) ; binaire tout-ou-rien (sur le modèle
    de `deraciner`) : la graine n'est retirée de la banque QUE si le coût est
    intégralement payé — forcer le geste à vide draine la Vigueur sans rien
    déposer, et la graine est conservée. **Empilement autorisé** (Q4) : on ne
    refuse JAMAIS un plot occupé ; la graine **patiente** (la succession ne lève
    que sur plot libre). `eco` est réservé (cohérence avec la famille des gestes +
    routage du pont) : le dépôt n'écrit aucun champ écolo.
    Renvoie True si la graine a été déposée."""
    bank = game_state.get("player_seed_bank")
    if bank is None or bank.count(species) == 0:
        return False                          # lot vide (Q2) — aucune Vigueur dépensée
    cost = cout_action(game_state, player, "planter", _objets_action("planter"))
    if spend(game_state, player, cost) < 1.0:
        return False                          # Vigueur insuffisante → graine conservée
    seed = bank.take(species)
    tile.grains_en_attente.setdefault((r, c), []).append(
        GrainEnAttente(species=species, genes=dict(seed.genes),
                       cultive=True, player=player,
                       semaine_depot=game_state.get("week", 0))
    )
    return True


def arroser(game_state: dict, player: str, eco, r: int, c: int,
            urgence: bool = False) -> bool:
    """Arroser (spec §3.2 / CONCEPTION_PLANTER_ARROSER §2.2, Q8-Q12) — geste sur le
    MILIEU, canal VERTUEUX (philo #1). Canon philo #2 : on écrit UNIQUEMENT le champ
    `eco.humidite` au plot cliqué (`+DOSE_ARROSAGE`, cap 3.0, CUMULATIF) — RIEN
    d'autre. La plante « se débrouille » avec l'humidité du sol au tick suivant
    (Q12 a) : sa stagnation « sec » se lève si l'eau remonte, l'excès → asphyxie
    (modèle eau, tick). On n'écrit JAMAIS un attribut de la plante.

    Transitoire par construction : `tick_hydrology` (évaporation × drainage) fait
    REDESCENDRE l'apport → ré-arroser COÛTE = l'usure de la solution facile (philo
    #1). La diffusion (`HUMIDITY_INERTIA`, au tick) mouille naturellement autour
    (Q8) — on n'écrit que le plot cliqué. Cumuler les doses peut franchir le seuil
    d'excès → noyade (§2.3) : arroser n'est bénéfique QUE dosé (fausse bonne idée
    si abusé).

    DEUX phases (Q10) : planification (prévention, coût simple) ET saison (réaction,
    `urgence=True` → `× URGENCE_MULT`). Coût **MODÉRÉ**. Binaire tout-ou-rien (modèle
    `deraciner`) : le champ n'est mouillé QUE si le coût est intégralement payé —
    forcer le geste à vide draine la Vigueur sans rien arroser.
    Renvoie True si le geste a été pleinement payé (et donc appliqué)."""
    cost = (cout_action(game_state, player, "arroser", OBJETS_TOUCHES["arroser"])
            * (URGENCE_MULT if urgence else 1.0))
    if spend(game_state, player, cost) < 1.0:
        return False                          # Vigueur insuffisante → champ intact
    h = eco.humidite.at_plot(r, c)
    eco.humidite.set(r, c, min(3.0, h + DOSE_ARROSAGE))
    return True


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
    deposer_mort(plant, eco)   # squelette persistant (②B), point d'entrée unique
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
    tronçon 5).

    Décompo·compost ② (intention Nico : « toute matière taillée doit être en
    décomposition ») : la masse du sous-arbre RÉELLEMENT retiré (`Σ length_cm ×
    BOIS_PAR_CM`) retombe en litière `bois` au plot-foyer (philo #2 : on dépose,
    le tick décompose). On récupère ET on rend au sol — le gain Vigueur est
    inchangé. Rien retiré (DOUX/collet) → rien déposé.
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
        removed = atteindre_segment(plant, seg_id, intensite=1.0)   # ≥ COUPE_NETTE → écimage du sous-arbre ciblé
        masse_bois = sum(s.length_cm for s in removed) * BOIS_PAR_CM
        eco.deposer_litiere(*plant.position, "bois", masse_bois)    # no-op si masse_bois ≤ 0
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
    # ⑦ §J.1 : écraser une ABEILLE libère une phéromone d'alarme locale → les
    # abeilles du rayon piquent le curseur (réaction temps réel, côté Godot). Le
    # geste reste possible (philo #1) mais émergemment puni — aucun malus en dur ici.
    if guilde == "abeille":
        declencher_alarme(eco, r, c, ALARME_DEPOT)
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
    # ②C.2 : écraser un SQUELETTE (mort) → on le pousse au sol (seche → couchee) et on
    # accélère sa fragmentation (dépôt immédiat d'une part du bois restant). Même philo
    # que l'écrasement du vivant ; pas de `health` (déjà mort), pas de seam structurel.
    if plant.morte:
        if plant.stade_mort == "seche":
            plant.stade_mort = "couchee"
        chute = plant.bois_restant * ECRASER_FRAG_BOOST
        if chute > 0.0:
            eco.deposer_litiere(*plant.position, "bois", chute)
            plant.bois_restant -= chute
        return True
    cls = plant.plant_class
    age_weeks = max((s.age_weeks for s in plant.segments), default=0)   # ≡ proxy d'âge de growth.py
    intensite = INTENSITE_PIED * (1.0 - cls.resistance_ecrasement * f_lignification(age_weeks))
    intensite = max(0.0, min(1.0, intensite))   # le seam attend une intensité ∈ [0,1]
    seg_id = 0                                  # défaut : le collet (Q2)
    if segment_id is not None and 0 <= segment_id < len(plant.segments):
        seg_id = segment_id                     # segment désigné à la souris
    removed = atteindre_segment(plant, seg_id, intensite)  # DOUX déforme / NET écime (+ auxine)
    # ② : un écimage NET casse du bois au sol (même logique que `tailler` ; le coup
    # de pied qui brise une branche la met en litière). Vide en régime DOUX/collet.
    masse_bois = sum(s.length_cm for s in removed) * BOIS_PAR_CM
    eco.deposer_litiere(*plant.position, "bois", masse_bois)   # no-op si masse_bois ≤ 0
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
