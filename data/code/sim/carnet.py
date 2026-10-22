"""
SYMBIOSE — sim/carnet.py
Le CARNET AUTO — première des quatre voix narratives (sprint Voix narratives,
tronçon ③, dettes D14 + D43).
Spec de référence : `docs/narration/voix/conception_voix_narratives.md` §2.1 + §5.

Voix « je », à la première personne. Le carnet est un LECTEUR read-only du ledger
②  (`sim/journal.py`) : il ne consigne RIEN, n'avance aucun tick, n'utilise aucun
RNG. Pour chaque entrée du ledger il choisit un CONCEPT (table `CONCEPT_DE`, §5.0)
puis un REGISTRE :

  - DESCRIPTIF tant que le concept n'est pas maîtrisé (palier < SEUIL_CARNET) —
    « Le plant de tomate fait grise mine. »
  - INTERPRÉTATIF dès que le palier du CONCEPT atteint le seuil — « Encore la
    soif : ce sol draine trop vite, je le sais maintenant. »

Le registre se recalcule À LA CONSULTATION (révélation rétroactive, décision B du
doc §0) : une vieille note « se comprend » quand on finit par maîtriser sa cause.
Le palier lu est celui du CONCEPT de l'entrée (pas de l'espèce) — maîtriser
*l'eau* éclaire toutes les notes de soif, pas seulement celles d'une espèce.

GARDE-FOU DE COUCHE (identique à `journal.py` / `maitrise.py`) : `carnet` est au
niveau `sim`, AU-DESSUS du tick. **`engine`/`fields`/`plants` ne l'importent
JAMAIS.** Il lit `game_state["journal"]` (②) et `maitrise.palier` (D12). Pas de
joueur consigné → `carnet_lire` renvoie `[]` (no-op golden, jamais de crash).

CORPUS = LIVRABLE ÉDITORIAL (doc §5) : les tables ci-dessous sont de la DONNÉE
recopiée fidèlement du doc, pas de la logique. Ne pas réécrire les gabarits.
"""
from __future__ import annotations

from sim import maitrise
from sim.signes_corpus import SIGNES
from sim.champignon_encyclo import FICHES_CHAMPIGNON

# --- Calibrage (PLACEHOLDER NOMMÉ, à régler post-test D12.4) ------------------
# Palier du CONCEPT à partir duquel la note bascule en interprétatif (décision B
# du doc §0). Le réglage d'aide « interprétatif anticipé » (Options, défaut NON,
# cf. CLAUDE.md) ramène ce seuil à 1 pour le joueur concerné — voir `_seuil`.
SEUIL_CARNET = 3
SEUIL_ANTICIPE = 1

# Concept de repli quand une paire (kind, cause) n'est pas tabulée (§5.0) : on ne
# crashe JAMAIS sur un événement inattendu (kickoff « Pièges »), on le range sous
# un concept neutre et on garde un gabarit générique (cf. _GABARIT_FALLBACK).
CONCEPT_FALLBACK = "observation"


# --- Table CONCEPT_DE[(kind, cause)] → concept (doc §5.0, VERBATIM) -----------
# Quel concept de maîtrise « gate » le registre de chaque entrée. Les causes de
# reproduction (auto/biparental/introgr.) mappent toutes vers `reproduction`,
# comme le doc l'écrit en une seule ligne ; la « levée (reprise) » est un cas
# spécial dont le concept EST sa cause (eau/lumière/météo) → traité par code dans
# `_concept_de` plutôt que par une entrée figée.
CONCEPT_DE: dict[tuple[str, str | None], str] = {
    ("germination", None):        "succession",
    ("stagnation", "sec"):        "eau",
    ("stagnation", "noyé"):       "eau",
    ("stagnation", "ombre"):      "lumière",
    ("stagnation", "froid"):      "météo",
    ("floraison", None):          "pollinisation",
    ("nouaison", None):           "pollinisation",
    ("reproduction", "auto"):        "reproduction",
    ("reproduction", "biparental"):  "reproduction",
    ("reproduction", "introgr."):    "reproduction",
    ("reproduction", None):          "reproduction",
    # Émission clonale (sprint LUXURIANCE ②/④) : la colonie perpétue la lignée SANS
    # graine (clone). Cause = le MODE (stolon/rhizome/drageon) → même concept
    # « reproduction », mais le gabarit distingue le tapissage doux (stolon) de la
    # colonie qui court (rhizome, « envahissante à surveiller »).
    ("ramet", "stolon"):             "reproduction",
    ("ramet", "rhizome"):            "reproduction",
    ("ramet", "drageon"):            "reproduction",
    # Bouture PAR LE JOUEUR (sprint PALETTE DE GESTES ②) : multiplication végétative
    # DÉLIBÉRÉE — le greffon prélevé est un clone, comme le ramet spontané, mais
    # l'acte est volontaire. Même concept « reproduction » → le carnet bascule en
    # interprétatif au seuil du concept (§6). Câblé ici pour quand le pont journalise
    # une bouture réussie au ledger ; texte via le gabarit générique (gracieux).
    ("bouture", None):               "reproduction",
    # Greffe PAR LE JOUEUR (sprint PALETTE DE GESTES ③) : soudure aérien/racinaire —
    # le porte-greffe adopte l'identité aérienne du greffon (D8). Comme la bouture,
    # c'est une multiplication VÉGÉTATIVE délibérée (pas de graine, pas de brassage)
    # → même concept « reproduction ». Le carnet bascule en interprétatif au seuil du
    # concept (§6) ; texte via un gabarit dédié ci-dessous (le découplage aérien/
    # racinaire mérite sa note distincte du clonage à l'identique de la bouture).
    ("greffe", None):                "reproduction",
    ("mort", "sénescence"):       "sénescence",
    ("mort", "asphyxie"):         "eau",
    ("mort", "gel"):              "météo",
    ("mort", "conflit"):          "compétition",
    ("ravageur", None):           "ravageurs",
    # Herbivorie RACINAIRE du campagnol (sommet trophique ①) : même concept de
    # maîtrise « ravageurs » que le nuisible de saison — le joueur y apprend la
    # régulation top-down (le super-prédateur ② en fera une boucle). Le carnet
    # bascule en interprétatif au seuil du concept « ravageurs » (§6).
    ("ravageur", "rongeur_racinaire"): "ravageurs",
    ("abscission", None):         "décomposition",
    ("acclimatation", None):      "adaptation",          # D43 (doc §5.1 dernière ligne)
    # Rosée & gelée blanche (sprint météo→champs ⑤) : aléas CLIMATIQUES nocturnes,
    # gatés par le concept « météo » → le carnet bascule en interprétatif au seuil
    # météo (D12), exactement comme le froid/gel (cohérent §6 du doc de conception).
    ("rosee", None):              "météo",
    ("gelee_blanche", None):      "météo",
    # Transport éolien de la litière (sprint VENT ⑦, §5.6) : le vent charrie la
    # matière de surface et la dépose sous le vent → un fait de DÉCOMPOSITION (la
    # litière qui s'amasse au pied d'un abri amorce l'humus de demain), gaté par le
    # concept « décomposition » comme l'abscission.
    ("transport_litiere", None):  "décomposition",
    # Carnivorie végétale (hydrologie & marécages ⑥) : la Drosera prélève la nuée
    # de moustiques → azote INTERNE (elle échappe à la faim d'azote). Concept NEUF
    # « carnivorie » (gate le registre du carnet ; palier défaut → descriptif tant
    # qu'il n'est pas maîtrisé). Le joueur y apprend le flux insectes→azote et la
    # niche du manque comblé par la chasse (§5, doc voix).
    ("carnivorie", None):         "carnivorie",
    # Levée de la molène sur terre viciée (sprint MÉMOIRE D'INOCULUM ③) : l'indicatrice
    # ne germe QUE sur inoculum élevé (porte `arch_inoculum`) → sa germination porte la
    # cause `sol_vicie` (posée par `evenements.py`) et gate le registre sous le concept
    # NEUF « maladie ». Concept propre au carnet (comme carnivorie/sénescence, hors
    # `encyclopedie_types.CONCEPTS`) : reste descriptif tant que non maîtrisé.
    ("germination", "sol_vicie"): "maladie",
    # PAYSAGE de la ceinture (sprint PÉRIPHÉRIE ⑥) : les gestes de lisière, d'eau et de
    # roche, et les réponses du terrain. Quatre concepts NEUFS propres au carnet (comme
    # carnivorie/maladie, hors `encyclopedie_types.CONCEPTS`) → la note reste descriptive
    # tant qu'ils ne sont pas maîtrisés. Le concept est choisi sur ce que le geste
    # ENSEIGNE, pas sur l'outil employé :
    #   - abattre → `brise_vent` : ce qu'on perd d'abord, c'est l'écran (le vent entre,
    #     la rafale décroche derrière ce qui reste) ;
    #   - receper → `rejet_de_souche` : la souche vit ou meurt, toute la leçon du taillis ;
    #   - eteter  → `lisiere` : la seule coupe qui prélève SANS défaire la lisière
    #     (densité conservée : abri, corridor et ombre restent) ;
    #   - endiguer/deriver/creuser + rupture d'ouvrage → `eau` (concept existant : on
    #     déplace l'eau, on ne la crée pas) ;
    #   - entailler + éboulis → `erosion` : la terre qui descend, seule trace lisible
    #     de l'irréversible.
    ("coupe", "abattre"):         "brise_vent",
    ("coupe", "receper"):         "rejet_de_souche",
    ("coupe", "eteter"):          "lisiere",
    ("terrassement", "endiguer"): "eau",
    ("terrassement", "deriver"):  "eau",
    ("terrassement", "creuser"):  "eau",
    ("terrassement", "entailler"): "erosion",
    ("rupture", None):            "eau",
    ("eboulis", None):            "erosion",
}

# Concept de la « levée (reprise) » : doc §5.0 dit « = la cause (eau / lumière /
# météo) ». La reprise hérite donc du concept de ce qui la bloquait. On mappe la
# cause de reprise (sec/noyé → eau, ombre → lumière, froid → météo) ; cause None
# → succession (reprise spontanée).
_CONCEPT_LEVEE: dict[str | None, str] = {
    "sec": "eau", "noyé": "eau", "ombre": "lumière", "froid": "météo",
    None: "succession",
}


def _concept_de(kind: str, cause: str | None) -> str:
    """Concept qui gate le registre d'une entrée (§5.0). Cas spécial « levée » :
    son concept EST sa cause (la reprise se comprend quand on maîtrise ce qui
    bloquait). Toute paire inconnue → CONCEPT_FALLBACK (jamais de crash, kickoff
    « Pièges »)."""
    if kind == "levée":
        return _CONCEPT_LEVEE.get(cause, "succession")
    return CONCEPT_DE.get((kind, cause), CONCEPT_FALLBACK)


# --- Table GABARIT[(kind, cause, registre)] → texte (doc §5.1, VERBATIM) ------
# Voix interne 1ʳᵉ personne. Slots : {e} = espèce, {l} = lieu (dérivé de la zone),
# {s} = saison/semaine. Recopié des 2 colonnes du doc §5.1 (descriptif | interpré-
# tatif). La « levée (reprise) » porte la cause `=cause levée` dans le doc → on la
# tabule sous cause None (le gabarit ne dépend pas finement de la cause de reprise).
_D = "descriptif"
_I = "interprétatif"
GABARIT: dict[tuple[str, str | None, str], str] = {
    ("germination", None, _D): "Une pousse de {e} a levé {l}.",
    ("germination", None, _I): "{e} a germé {l} : le sol a enfin atteint sa chaleur de réveil — et mes lignées semblent lever un peu plus tôt chaque année.",

    # Molène sur terre viciée (sprint MÉMOIRE D'INOCULUM ③) — descriptif = ce qu'on VOIT
    # (elle prospère là où le reste peine, philo #5) ; interprétatif = la cause comprise
    # au seuil « maladie » (le sol chargé d'inoculum qu'il faut faire reposer/tourner).
    ("germination", "sol_vicie", _D): "Une rosette laineuse de {e} s'est installée {l}, là où le reste peine.",
    ("germination", "sol_vicie", _I): "{e} lève {l} : elle prospère sur cette terre lasse que les maladies passées ont chargée — le signe qu'il faut la laisser reposer, ou y tourner les familles.",

    ("stagnation", "sec", _D): "Le plant de {e} {l} fait grise mine, feuilles molles.",
    ("stagnation", "sec", _I): "Encore la soif {l} — ce sol draine trop vite pour {e}, je le sais maintenant.",
    ("stagnation", "noyé", _D): "{e} {l} a le pied dans l'eau, plus rien ne bouge.",
    ("stagnation", "noyé", _I): "Trop d'eau {l} : les racines de {e} étouffent, le sol ne ressuie pas.",
    ("stagnation", "ombre", _D): "{e} {l} s'étire, pâle, tiges filantes.",
    ("stagnation", "ombre", _I): "L'ombre {l} bride {e} — elle file chercher la lumière qu'on lui vole.",
    ("stagnation", "froid", _D): "{e} {l} est figée depuis le coup de froid.",
    ("stagnation", "froid", _I): "Le froid {l} a mis {e} en pause : sous son seuil, rien ne pousse.",

    ("levée", None, _D): "{e} {l}, longtemps à l'arrêt, est repartie.",
    ("levée", None, _I): "{e} {l} repart — j'ai levé ce qui la bloquait, et ça a payé.",

    ("floraison", None, _D): "{e} {l} s'est couverte de fleurs.",
    ("floraison", None, _I): "{e} fleurit {l} : la table est mise pour les butineurs, la nouaison se joue là.",
    ("nouaison", None, _D): "Des fruits se forment sur {e} {l}.",
    ("nouaison", None, _I): "Nouaison {l} — le pollen reçu a porté, le fruit grossira.",

    ("reproduction", None, _D): "{e} a essaimé alentour {l}.",
    ("reproduction", None, _I): "{e} se ressème {l} : la lignée se perpétue, le brassage a eu lieu.",

    # Émission clonale (sprint LUXURIANCE ②/④) : gabarits PAR MODE — le stolon
    # tapisse doucement (auto-limité par la lumière), le rhizome COURT (à surveiller).
    ("ramet", "stolon", _D): "{e} {l} a poussé un coulant : une jeune pousse s'y enracine.",
    ("ramet", "stolon", _I): "{e} tapisse {l} par stolons — un clone de la mère, tant que la lumière atteint le sol ; le couvert se densifie tout seul.",
    ("ramet", "drageon", _D): "Un rejet de {e} a percé le sol tout près {l}.",
    ("ramet", "drageon", _I): "{e} drageonne {l} : la souche relance des clones à ses pieds, la touffe s'épaissit.",
    ("ramet", "rhizome", _D): "{e} {l} a ressurgi un peu plus loin, hors de la touffe mère.",
    ("ramet", "rhizome", _I): "{e} court {l} par ses rhizomes — un clone loin de la mère, même à l'ombre : à surveiller, la colonie gagne vite.",

    # Greffe PAR LE JOUEUR (sprint PALETTE DE GESTES ③) : soudure aérien/racinaire.
    # Descriptif = ce qu'on VOIT (la reprise, philo #5) ; interprétatif = le découplage
    # compris au seuil du concept reproduction (racines de l'un, couronne de l'autre).
    ("greffe", None, _D): "La greffe de {e} {l} a pris : le rameau soudé repart.",
    ("greffe", None, _I): "{e} greffé {l} : les racines de l'hôte portent désormais une autre couronne — j'ai marié deux plantes en une, ce que la graine ne sait pas faire.",

    ("mort", "sénescence", _D): "Le vieux pied de {e} {l} s'est éteint.",
    ("mort", "sénescence", _I): "{e} {l} a bouclé son cycle — la sénescence, pas un accident ; sa nécromasse nourrit déjà le sol.",
    ("mort", "asphyxie", _D): "{e} {l} a dépéri puis succombé.",
    ("mort", "asphyxie", _I): "Noyée {l} : l'excès d'eau prolongé a fini par tuer {e}.",
    ("mort", "gel", _D): "{e} {l} a été emportée par le gel.",
    ("mort", "gel", _I): "Le gel {l} a eu {e} — au-delà de sa rusticité, rien à faire.",
    ("mort", "conflit", _D): "{e} {l} a cédé la place à plus vigoureux.",
    ("mort", "conflit", _I): "Éclaircissage naturel {l} : {e} a perdu la course à la lumière et aux ressources.",

    ("ravageur", None, _D): "Des bestioles s'affairent sur {e} {l}.",
    ("ravageur", None, _I): "Pression de ravageurs {l} — si les auxiliaires sont là, l'équilibre se rétablit seul.",
    ("abscission", None, _D): "{e} {l} laisse tomber ses feuilles.",
    ("abscission", None, _I): "Abscission {l} : {e} se déleste avant l'hiver, sa litière amorce l'humus de l'an prochain.",

    ("acclimatation", None, _D): "Le feuillage de {e} {l} a pris un éclat cireux, glauque.",
    ("acclimatation", None, _I): "{e} {l} s'est acclimatée — et ses descendants naîtront pré-armés contre ce stress.",

    # Rosée & gelée blanche (sprint météo→champs ⑤) — aléas de tuile, sans espèce
    # ({e} = « le couvert »). Descriptif = ce qu'on VOIT le matin (philo #5) ;
    # interprétatif = la cause comprise au seuil météo (le sol nu/clair condense).
    ("rosee", None, _D): "Au matin {l}, le couvert perlait de gouttes scintillantes.",
    ("rosee", None, _I): "Rosée {l} — la nuit claire a fait condenser l'air sur le sol froid ; cette eau du matin freine la soif et abreuve la petite faune.",
    ("gelee_blanche", None, _D): "Une fine pellicule de givre blanc couvrait le sol {l} ce matin.",
    ("gelee_blanche", None, _I): "Gelée blanche {l} : sous le ciel dégagé le sol a gelé sa rosée ; le givre fondra et rendra son eau au réchauffement.",

    # Transport éolien de la litière (sprint VENT ⑦) — phénomène de tuile, sans
    # espèce ({e} = « le couvert »). Descriptif = ce qu'on VOIT après le coup de vent
    # (philo #5) ; interprétatif = la cause comprise au seuil décomposition (l'abri
    # piège la matière, qui s'y décompose et enrichit le coin).
    ("transport_litiere", None, _D): "Après le coup de vent {l}, les feuilles mortes s'étaient amassées le long de l'abri.",
    ("transport_litiere", None, _I): "Le vent {l} a charrié la litière jusqu'à l'abri : là où il ralentit, la matière s'amasse et nourrira ce coin de terre.",

    # Carnivorie végétale (hydrologie & marécages ⑥). Descriptif = ce qu'on VOIT
    # (la nuée qui se creuse au-dessus du rossolis, philo #5) ; interprétatif = la
    # cause comprise au seuil « carnivorie » (le flux insectes→azote qui affranchit
    # la plante de la faim d'azote sur la tourbe pauvre).
    # PAYSAGE de la ceinture (sprint PÉRIPHÉRIE ⑥) — faits de SECTEUR : ni plot ni
    # tuile (le côté du terrain est dans la ligne de log, pas dans la zone) → ces
    # gabarits n'emploient PAS le slot {l}, sauf l'éboulis qui est bien tenu par une
    # tuile. {e} = l'essence coupée (« le couvert » si le bord n'en portait pas).
    # Descriptif = ce que je VOIS le jour même (philo #5) ; interprétatif = la cause
    # comprise au seuil du concept (le vent, la souche, l'eau déplacée, la terre nue).
    ("coupe", "abattre", _D): "J'ai abattu la lisière d'un bord — {e}. Tout est à terre, le bois jonche le sol.",
    ("coupe", "abattre", _I): "Abattu, ce bord de {e} : avec lui tombe l'écran qui coupait le vent — ce qui reste debout prendra les rafales de plein fouet, et la trouée mettra une vie d'homme à se refermer.",
    ("coupe", "receper", _D): "J'ai recépé un bord au ras du sol — {e}. Il ne reste que les souches.",
    ("coupe", "receper", _I): "Recépé, ce bord de {e} : la souche est vivante, elle relancera des rejets plus drus que la tige que j'ai prise — couper, chez lui, c'est faire durer.",
    ("coupe", "eteter", _D): "J'ai rabattu la tête des arbres d'un bord — {e}. Les troncs sont restés debout.",
    ("coupe", "eteter", _I): "Étêté, ce bord de {e} : le rideau tient, le sol reste couvert, et la tête sera refaite dans quelques années — c'est le prélèvement qui ne défait rien.",

    ("terrassement", "endiguer", _D): "J'ai relevé l'eau au bord ; la terre des premiers rangs est plus sombre.",
    ("terrassement", "endiguer", _I): "J'ai endigué : je n'ai pas fait d'eau, je l'ai retenue ici — elle manquera en aval, et mon barrage ne tiendra pas si je ne reviens pas.",
    ("terrassement", "deriver", _D): "J'ai fait descendre l'eau du bord ; les premiers rangs s'assèchent déjà.",
    ("terrassement", "deriver", _I): "J'ai dérivé : le bord se vide, et c'est le jardin qui devra rendre l'eau au fossé — ce qu'on retire ici manque là.",
    ("terrassement", "creuser", _D): "J'ai creusé au bord ; le fond est encore sec, mais il est plus bas que tout le reste.",
    ("terrassement", "creuser", _I): "J'ai creusé une mare : l'eau viendra seule au point le plus bas, et elle restera — un creux, contrairement à une digue, ne rompt jamais.",
    ("terrassement", "entailler", _D): "J'ai entamé la roche à la pioche ; la paroi a reculé, la pierre est à vif.",
    ("terrassement", "entailler", _I): "J'ai entaillé la falaise : rien ne la fera revenir, l'ombre qu'elle portait est perdue, et la roche nue descendra sur mes rangs des années durant.",

    ("rupture", None, _D): "L'ouvrage d'eau du bord a lâché ; l'eau a changé de niveau toute seule.",
    ("rupture", None, _I): "Ma digue a rompu : je l'avais laissée sans y revenir et l'eau a repris ses aises — un ouvrage se surveille, une forme se contente d'exister.",

    ("eboulis", None, _D): "De la terre nue est descendue sur les premiers rangs {l}.",
    ("eboulis", None, _I): "Le sol part {l} : le bord que j'ai dénudé n'a plus rien pour le tenir, et il descend chez moi — grumeaux enfouis, humus dilué.",

    ("carnivorie", None, _D): "La nuée de moustiques se raréfie au-dessus de {e} {l}.",
    ("carnivorie", None, _I): "{e} chasse {l} : ses feuilles gluantes piègent les insectes, et cet azote de proies la nourrit là où le sol tourbeux, trop pauvre, n'offre rien — elle mange ce qu'elle ne peut puiser.",
}

# Signes OBSERVÉS au survol (sprint PLANTE ASSEMBLÉE ⑥, `sim/signes.py`) : une note
# `kind="signe"`, `cause=<signe>`. Concept et gabarits D/I vivent dans le corpus
# éditorial des signes (source unique, partagée avec l'encyclopédie et la vue) ; on
# les VERSE ici dans les deux tables, le reste du carnet ne change pas.
for _signe, _corpus in SIGNES.items():
    CONCEPT_DE[("signe", _signe)] = _corpus["concept"]
    for _reg, _gabarit in _corpus["carnet"].items():
        GABARIT[("signe", _signe, _reg)] = _gabarit

# Fructifications OBSERVÉES au survol d'un carpophore (sol qui respire ⑤,
# `sim/champignon_voix.py`) : une note `kind="fructification"`, `cause=<espèce>`.
# Concept (saprophytie/mycorhize/parasitisme/sosies) et gabarits D/I vivent dans le
# corpus fongique (source unique) ; les gabarits n'emploient pas {e} — la note ne
# nomme jamais le champignon (le nom se mérite dans l'info-bulle).
for _cle, _fiche in FICHES_CHAMPIGNON.items():
    CONCEPT_DE[("fructification", _cle)] = _fiche["concept"]
    for _reg, _gabarit in _fiche["carnet"].items():
        GABARIT[("fructification", _cle, _reg)] = _gabarit

# Gabarit générique quand la paire (kind, cause) n'a pas de texte dédié (§5.0 ne
# tabule pas tous les croisements possibles). Jamais un crash, jamais une chaîne
# vide — une note neutre mais lisible.
_GABARIT_FALLBACK = {
    _D: "Quelque chose s'est passé du côté de {e} {l}.",
    _I: "{e} {l} — un événement que je commence à comprendre.",
}

# Reproduction : les 3 causes (auto/biparental/introgr.) partagent le gabarit
# `reproduction None` ci-dessus → on neutralise la cause pour la clé de gabarit.
_KIND_CAUSE_NEUTRE = {"reproduction"}


# --- Lieu lisible dérivé de la zone (slot {l}) -------------------------------
def _lieu(zone: tuple) -> str:
    """Libellé de lieu (slot `{l}`) dérivé de la `zone` du ledger : `(tile_id, r,
    c)` ou `(tile_id,)`. On reste FACTUEL et stable (« sur T0 en (2,3) ») plutôt
    que de prétendre un « coin nord-est » qui supposerait de connaître la
    géométrie réelle de la tuile (hors périmètre ③). L'UI Godot (D24) pourra
    enjoliver ce libellé ; le carnet Python garde une zone non ambiguë."""
    if not zone:
        return "au jardin"
    tid = zone[0]
    # Événement HORS TUILE (marqueur émis avant tout en-tête `[T0]` : geste de
    # paysage sur la ceinture, ouvrage rompu…) → `tile_id` est None. On rend « au
    # jardin » plutôt que « sur None » (le libellé reste factuel, jamais faux).
    if tid is None:
        return "au jardin"
    if len(zone) >= 3:
        return f"sur {tid} en ({zone[1]},{zone[2]})"
    return f"sur {tid}"


# --- Sélection du registre ---------------------------------------------------
def _reglage_anticipe(game_state: dict, player: str) -> bool:
    """Flag du réglage d'aide « interprétatif anticipé » (Options, défaut NON, cf.
    CLAUDE.md). Quand il est ON, le carnet bascule en interprétatif dès le palier
    1 (`SEUIL_ANTICIPE`) — pour qui veut révéler les causes tôt, au prix de la
    méthode scientifique. Le menu Options n'est pas encore exposé en Python : on
    lit un flag OPTIONNEL `game_state["options"][player]["carnet_anticipe"]` posé
    par le driver, défaut False.
    # TODO(options): brancher le flag réel quand le menu Options sera implémenté."""
    opts = game_state.get("options", {})
    return bool(opts.get(player, {}).get("carnet_anticipe", False))


def _seuil(game_state: dict, player: str) -> int:
    """Seuil de bascule effectif pour ce joueur : SEUIL_CARNET, ou SEUIL_ANTICIPE
    si le réglage d'aide est actif."""
    return SEUIL_ANTICIPE if _reglage_anticipe(game_state, player) else SEUIL_CARNET


def _registre(game_state: dict, player: str, concept: str) -> str:
    """Registre d'une entrée selon le palier du CONCEPT (révélation rétroactive,
    décision B) : interprétatif dès que `palier(concept) ≥ seuil`, descriptif
    sinon. Lecture pure de `maitrise.palier` (ne crée aucune clé)."""
    if maitrise.palier(game_state, player, concept) >= _seuil(game_state, player):
        return _I
    return _D


def _texte(kind: str, cause: str | None, registre: str, espece: str | None,
           zone: tuple, semaine: int) -> str:
    """Texte final d'une entrée : gabarit `(kind, cause, registre)` avec ses slots
    remplis (`{e}`/`{l}`/`{s}`). La reproduction neutralise sa cause pour la clé.
    Paire absente du corpus → gabarit générique (jamais de crash, kickoff)."""
    cle_cause = None if kind in _KIND_CAUSE_NEUTRE else cause
    gabarit = GABARIT.get((kind, cle_cause, registre)) or _GABARIT_FALLBACK[registre]
    # Espèce absente (aléa sans plante : ravageur de saison) → libellé neutre.
    nom = espece if espece else "le couvert"
    return gabarit.format(e=nom, l=_lieu(zone), s=semaine)


# --- API publique ------------------------------------------------------------
def carnet_lire(game_state: dict, player: str, filtre: dict | None = None) -> list[dict]:
    """Renvoie le carnet FORMATÉ d'un joueur (doc §2.1) : une liste d'entrées
    `{semaine, zone, concept, registre, texte}`, dans l'ordre chronologique du
    ledger. PUR (lecture seule). Sans tranche `journal` pour ce joueur → `[]`
    (golden-safe). Le registre est recalculé MAINTENANT (révélation rétroactive).

    `filtre` optionnel (indexation §2.1), tout champ est ET-combiné :
      - `{"concept": "eau"}`     → seulement les notes du concept donné ;
      - `{"espece": "tomate"}`   → seulement les notes d'une espèce (clé catalogue,
                                    retour F5 : suivre une espèce découverte) ;
      - `{"zone": (tid, r, c)}`  → seulement une zone ;
      - `{"saison": s}`          → seulement une semaine (slot {s})."""
    journal = game_state.get("journal")
    if not journal:
        return []
    st = journal.get(player)
    if not st:
        return []

    out: list[dict] = []
    for e in st["entries"]:
        concept = _concept_de(e["kind"], e["cause"])
        if not _passe_filtre(e, concept, filtre):
            continue
        registre = _registre(game_state, player, concept)
        out.append({
            "semaine": e["semaine"],
            "zone": e["zone"],
            "concept": concept,
            "registre": registre,
            "texte": _texte(e["kind"], e["cause"], registre,
                            e["espece"], e["zone"], e["semaine"]),
        })
    return out


def _passe_filtre(entree: dict, concept: str, filtre: dict | None) -> bool:
    """Indexation §2.1 : une entrée passe si elle satisfait TOUS les critères du
    `filtre` (concept / zone / saison). `filtre` None ou vide → tout passe."""
    if not filtre:
        return True
    if "concept" in filtre and concept != filtre["concept"]:
        return False
    if "espece" in filtre and entree["espece"] != filtre["espece"]:
        return False
    if "zone" in filtre and entree["zone"] != filtre["zone"]:
        return False
    if "saison" in filtre and entree["semaine"] != filtre["saison"]:
        return False
    return True
