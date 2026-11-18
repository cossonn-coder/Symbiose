"""
SYMBIOSE — sim/signes_corpus_thermique.py
CORPUS des signes THERMIQUES par paliers (D139, sprint niche thermique ④).
Spec : `docs/vegetal/genetique/conception_niche_thermique.md` §6.

DONNÉE ÉDITORIALE PURE, même schéma que `sim/signes_corpus.SIGNES` (qui la fusionne) :
`vu` / `concept` / `carnet` D-I / `fiche` 1-3. Un fichier à part pour garder le corpus
principal court (une responsabilité : la gamme froid → chaud).

Deux familles :
  - MARQUES événementielles `froid` et `brulure` (`gel` vit dans le corpus principal),
    triées par `semiologie.leaf_symptoms` comme les autres ;
  - PALIERS d'annonce et de gravité de `sim/engine/posture_thermique.py` (pendant,
    violacé, effondré ; replié, flétri à midi, bords jaunis). Ils ne sont pas des
    `leaf_symptoms` : la vue les reçoit en `palier_thermique` et les dessine en
    POSTURE ; le joueur qui les survole les consigne au carnet (`observer`).
Le palier « translucide » EST la marque `froid`, « noirci » EST `gel`, « brûlé » EST
`brulure` : une seule entrée par signe, pas de doublon.

Concept de maîtrise : `météo` pour tous (celui du gel) — descriptif dessous,
interprétatif au palier. Philo #1 au niveau 3 : on agit sur le MILIEU, jamais sur la
plante. Jamais lu par le tick → golden NEUTRE.
"""
from __future__ import annotations

_D = "descriptif"
_I = "interprétatif"

SIGNES_THERMIQUES: dict[str, dict] = {
    # ─────────────────────────────── froid ───────────────────────────────
    "pendant": {
        "vu": "feuilles pendantes, molles, au petit matin",
        "concept": "météo",
        "carnet": {
            _D: "Les feuilles de {e} {l} pendaient ce matin, molles, semaine {s}.",
            _I: "{e} {l} baisse les feuilles au petit matin : la nuit frôle ce qu'elle supporte, le froid n'est pas loin.",
        },
        "fiche": {
            1: "Au lever du jour, les feuilles pendent le long de la tige, sans tache ni couleur nouvelle ; elles se relèvent quand l'air se réchauffe.",
            2: "Annonce du froid : la nuit approche la limite que l'espèce supporte. La plante ralentit, ses cellules perdent un peu de turgescence — aucun tissu n'est encore touché.",
            3: "C'est le moment d'agir sur le milieu : voile ou cloche pour la nuit, paillage qui garde la chaleur du sol, abri d'un mur. Ou laisser faire, et voir qui tient.",
        },
    },
    "violace": {
        "vu": "feuilles pendantes teintées de violet",
        "concept": "météo",
        "carnet": {
            _D: "J'ai vu les feuilles de {e} {l} se teinter de violet, semaine {s}.",
            _I: "{e} {l} vire au violet : elle a accumulé le froid des nuits, et ses pigments la protègent — elle tient, mais elle est à la limite.",
        },
        "fiche": {
            1: "Le limbe se teinte de violet ou de pourpre, surtout au revers et sur les nervures, après plusieurs nuits fraîches.",
            2: "Froid prolongé : la plante fabrique des anthocyanes, pigments qui la protègent quand le froid freine sa photosynthèse. Un signe d'endurance, pas encore de blessure.",
            3: "Une plante qui violit endure : un sol couvert, un abri du vent du nord, une lisière, lui donnent les quelques degrés qui la font passer.",
        },
    },
    "froid": {
        "vu": "taches translucides, comme détrempées, sur les feuilles",
        "concept": "météo",
        "carnet": {
            _D: "J'ai vu des taches translucides, comme détrempées, sur les feuilles de {e} {l}, semaine {s}.",
            _I: "{e} {l} a pris froid sans geler : ces taches d'eau, ce sont ses cellules qui lâchent sous le frais — elle vient d'un pays chaud.",
        },
        "fiche": {
            1: "Des plages translucides, d'aspect détrempé, apparaissent sur le limbe après une nuit fraîche, puis brunissent.",
            2: "Lésion de froid sans gel : chez les plantes des pays chauds, les membranes se figent dès une dizaine de degrés. Le dégât s'accumule nuit après nuit, sans un cristal de glace.",
            3: "On ne réchauffe pas une plante, on choisit son moment et sa place : semer après les nuits froides, contre un mur qui rend la chaleur du jour, sous voile au printemps.",
        },
    },
    "effondre": {
        "vu": "plante noircie, affaissée sur elle-même",
        "concept": "météo",
        "carnet": {
            _D: "{e} {l} s'est affaissée, noircie, semaine {s}.",
            _I: "Le gel a eu raison de {e} {l} : ses tissus éclatés ne la portent plus, elle s'effondre — sa matière retournera au sol.",
        },
        "fiche": {
            1: "Après une nuit de gel, la plante noircie s'affaisse, tiges molles, feuilles collées.",
            2: "Effondrement : le gel a crevé trop de cellules ; la plante ne tient plus sa forme. Il lui reste peu de vigueur, un gel de plus l'emporte.",
            3: "On ne la relève pas : on la laisse au sol nourrir la litière, et la prochaine fois on choisit une lignée plus rustique, ou l'on prépare la nuit (voile, paillage) avant le gel annoncé.",
        },
    },
    # ─────────────────────────────── chaud ───────────────────────────────
    "replie": {
        "vu": "feuilles repliées de profil face au soleil",
        "concept": "météo",
        "carnet": {
            _D: "Les feuilles de {e} {l} se repliaient de profil au soleil, semaine {s}.",
            _I: "{e} {l} replie ses feuilles au soleil : elle offre la tranche à la chaleur, elle approche de ce qu'elle supporte.",
        },
        "fiche": {
            1: "Aux heures chaudes, le limbe se plie le long de la nervure ou se tourne de profil, offrant sa tranche au soleil ; il se rouvre le soir.",
            2: "Annonce de la chaleur : la feuille approche la température où la plante cesse de pousser. Se mettre de profil réduit l'énergie reçue — une parade, pas encore un dégât.",
            3: "Une ombre légère aux heures chaudes, un sol couvert qui garde l'eau, un voisin plus haut : le milieu rafraîchit mieux que tout arrosage d'urgence.",
        },
    },
    "fletri_midi": {
        "vu": "feuilles flétries à midi, qui se redressent le soir",
        "concept": "météo",
        "carnet": {
            _D: "J'ai vu {e} {l} flétrir en plein midi puis se redresser le soir, semaine {s}.",
            _I: "{e} {l} s'affaisse à midi : il fait chaud et elle a soif — ses feuilles ne se refroidissent plus en transpirant.",
        },
        "fiche": {
            1: "En plein midi, les feuilles pendent, molles ; le soir venu, elles se redressent.",
            2: "Chaleur et soif : faute d'eau, la plante ferme ses stomates ; elle ne transpire plus, sa feuille s'échauffe au-dessus de l'air et perd sa turgescence. Elle frôle la brûlure.",
            3: "C'est l'eau du sol qui la sauve : paillage épais, sol riche en humus qui retient l'eau, ombre aux heures chaudes. La plante abreuvée reste à la température de l'air.",
        },
    },
    "bords_jaunis": {
        "vu": "bords des feuilles jaunis, plante qui ne grandit plus",
        "concept": "météo",
        "carnet": {
            _D: "J'ai vu jaunir le bord des feuilles de {e} {l}, et elle ne grandit plus, semaine {s}.",
            _I: "{e} {l} jaunit par les bords et s'arrête : la chaleur dépasse ce qu'elle supporte, elle ne pousse plus et ne noue pas.",
        },
        "fiche": {
            1: "Le bord du limbe jaunit, la plante cesse de grandir, les fleurs ne donnent pas de fruits.",
            2: "Stress de chaleur : au-delà de sa limite, la plante suspend sa croissance et sa fécondation (le pollen devient stérile). Le tissu tient encore.",
            3: "On lui donne de l'ombre et de l'eau par le milieu : arbres et grandes plantes en lisière, sol couvert, plantation qui suit la course du soleil.",
        },
    },
    "brulure": {
        "vu": "taches sèches et blanchies, bord des feuilles grillé",
        "concept": "météo",
        "carnet": {
            _D: "J'ai vu des taches sèches et blanchies, le bord grillé, sur les feuilles de {e} {l}, semaine {s}.",
            _I: "Le soleil a brûlé {e} {l} : assoiffée, sa feuille a dépassé l'air de dix degrés, et le tissu a cuit.",
        },
        "fiche": {
            1: "Des plages sèches, blanchies ou brun clair, apparaissent sur les feuilles les plus exposées ; le bord grille et se recroqueville.",
            2: "Échaudage : une feuille assoiffée au soleil ne se refroidit plus et monte bien au-dessus de l'air. Au-delà de sa limite, le tissu meurt et ne se répare pas.",
            3: "La parade est l'eau et l'ombre, en amont : sol couvert, humus qui retient l'eau, ombre légère l'été. Une plante bien abreuvée ne brûle pas.",
        },
    },
}
