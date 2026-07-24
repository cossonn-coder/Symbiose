"""
SYMBIOSE — sim/quetes_corpus.py
CORPUS des LETTRES — le contenu éditorial des quêtes (D79, tronçon ③).
Spec : `docs/joueur/automate/conception_quetes.md` §7 (voix du donneur) + §3 (V1).

Miroir structurel des autres corpus (`concept_corpus.py`, `pages_corpus.py`,
`geste_corpus.py`) : DONNÉE PURE, aucun import moteur, aucune écriture, aucun RNG.
Ici, la donnée est une table de `Quete` (le contrat mécanique vit dans
`sim/quetes.py`) portant en plus son `texte_lettre`.

VOIX (V1, conception §3/§7) : chaque quête arrive comme une LETTRE ANONYME signée
d'un prénom — une plume du « monde social », PAS un PNJ (ni figure, ni dialogue,
ni récurrence obligatoire). Registre chaleureux ; JAMAIS directif (philo #6) : la
lettre pose un DÉSIR, jamais une méthode (« j'aimerais voir un tournesol géant »,
pas « plante ici et arrose trois fois »). Le *comment* appartient au joueur et à
son écologie (#1).

FAMILLES DÉMONTRÉES (conception §4) : au moins une condition de chaque famille —
`recolte_cumulee` (compteur/hook), `hauteur_min` / `floraison_min` /
`nombre_vivant_min` (snapshot). Une lettre vise sciemment le « kiwi » (grimpante
absente du catalogue, D26/F3) : cible INATTEIGNABLE assumée jusqu'à D26 — la
lettre existe, le rêve reste ouvert (#4, jamais d'échec).

DÉCLENCHEURS (déterministe, zéro RNG — conception §4) :
  - `None`            → la lettre est disponible d'emblée ;
  - `("palier", objet, seuil)` → arrive quand la maîtrise de `objet` ≥ `seuil` ;
  - `("saison", semaine_min)`  → arrive à partir de la semaine `semaine_min`.

RÉCOMPENSES (V3, catalogue déclaratif ouvert — SIMPLES au ③) :
  - `None`                     → plaisir pur (combler le désir suffit) ;
  - `("graine", espece)`       → un lot en banque de graines ;
  - `("page",)`                → une page secrète débloquée ;
  - `("vigueur", montant)`     → crédit de Vigueur joueur (PAS un buff plante, #2) ;
  - `("maitrise", objet, poids)` → crédit de maîtrise (une preuve pondérée).
RÉCOMPENSES MATÉRIELLES rares (V3, tronçon ④ — un ACTEUR neuf apparaît, jamais un
buff #2) :
  - `("vivace", espece, annees)`  → une pérenne LIGNEUSE déjà enracinée depuis
                                     `annees` ans (instanciée puis poussée par le vrai
                                     chemin de croissance) apparaît dans le jardin ;
  - `("structure", kind)`         → une structure permanente (`bac` à compost) posée.
"""
from __future__ import annotations

from sim.quetes import Quete

# --- La table des lettres ---------------------------------------------------
# Dict id → Quete. L'ordre de PARCOURS pour le déclenchement est le tri par `id`
# (déterminisme, cf. `quetes.evaluer_declencheurs`) — l'ordre littéral ci-dessous
# est purement lisible.
QUETES_CORPUS: dict[str, Quete] = {

    "lettre_cageot_tomates": Quete(
        id="lettre_cageot_tomates",
        donneur="Marcel",
        texte_lettre=(
            "Dis donc, voisin, tes plants de tomates ont fière allure cette "
            "année. Si le cœur t'en dit, je t'échangerais bien un plein cageot "
            "de belles rouges contre un pot de ma confiture de coings.\n"
            "— Ton voisin Marcel"),
        condition=("recolte_cumulee", "recolter", 4, "tomate"),
        recompense=None,                       # plaisir pur (base V3)
        declencheur=None),                     # disponible d'emblée

    "lettre_kiwi_reve": Quete(
        id="lettre_kiwi_reve",
        donneur="Léa",
        texte_lettre=(
            "Tonton, c'est vrai que les kiwis ça grimpe super haut ? "
            "J'aimerais trop en voir un qui monte jusqu'au ciel !\n"
            "— La petite Léa"),
        condition=("hauteur_min", "kiwi", 5.0),   # cible inatteignable (F3/D26)
        recompense=None,
        declencheur=("saison", 8)),

    "lettre_lavande_amelie": Quete(
        id="lettre_lavande_amelie",
        donneur="Amélie",
        texte_lettre=(
            "L'odeur de la lavande en fleur me rappelle les étés du Sud de mon "
            "enfance. Un beau carré bien mauve, ce serait un vrai bonheur pour "
            "le nez quand je passe devant chez toi.\n"
            "— Ta voisine Amélie"),
        condition=("floraison_min", "lavande", 6),
        recompense=("maitrise", "lavande", 1.0),
        declencheur=("palier", "lavande", 1)),

    "lettre_tournesol_geant": Quete(
        id="lettre_tournesol_geant",
        donneur="Léa",
        texte_lettre=(
            "Coucou ! J'ai vu dans un livre des tournesols plus grands qu'un "
            "bonhomme. J'aimerais tellement en voir un vrai, un géant, avant "
            "la fin de l'été...\n"
            "— La petite Léa"),
        condition=("hauteur_min", "tournesol", 2.5),
        recompense=("graine", "tournesol"),
        declencheur=("saison", 4)),

    "lettre_trefle_de_mamie": Quete(
        id="lettre_trefle_de_mamie",
        donneur="Bertrand",
        texte_lettre=(
            "Derrière la maison de ta grand-mère, il y avait un tapis de trèfle "
            "en fleur où bourdonnaient les abeilles tout l'été. Ce coin-là me "
            "manque, tu sais.\n"
            "— Ton oncle Bertrand"),
        condition=("floraison_min", "trefle", 5),
        recompense=("page",),
        declencheur=("palier", "trefle", 2)),

    "lettre_verger_pommiers": Quete(
        id="lettre_verger_pommiers",
        donneur="Marcel",
        texte_lettre=(
            "On parlait l'autre jour de faire un petit verger dans le coin. "
            "Quelques pommiers qui tiennent debout et donnent un peu d'ombre, "
            "ce serait déjà un beau début, non ?\n"
            "— Ton voisin Marcel"),
        condition=("nombre_vivant_min", "pommier", 3),
        recompense=("vigueur", 30.0),
        declencheur=("palier", "pommier", 2)),

    # --- Récompenses MATÉRIELLES rares (④) --------------------------------------
    "lettre_vieux_pommier_gaston": Quete(
        id="lettre_vieux_pommier_gaston",
        donneur="Gaston",
        texte_lettre=(
            "Voisin, je me fais vieux et mon verger me dépasse. Toi qui sais si "
            "bien mener les pommiers, laisse-moi t'offrir l'un des miens — un beau "
            "sujet de six ans, déjà en âge de fleurir. Il sera mieux chez toi.\n"
            "— Le vieux Gaston"),
        condition=("nombre_vivant_min", "pommier", 2),
        recompense=("vivace", "pommier", 6),       # pérenne enracinée depuis 6 ans (④)
        declencheur=("palier", "pommier", 3)),

    "lettre_bac_compost_odette": Quete(
        id="lettre_bac_compost_odette",
        donneur="Odette",
        texte_lettre=(
            "Mon mari en avait fabriqué deux, de ces grands bacs à compost, et je "
            "n'ai jamais eu l'usage du second. Il prend la poussière au fond du "
            "hangar. Passe donc le chercher, il fera merveille chez toi.\n"
            "— Ta voisine Odette"),
        condition=("recolte_cumulee", "recolter", 5, "tomate"),
        recompense=("structure", "bac"),           # structure permanente posée (④)
        declencheur=("saison", 12)),
}
