"""
SYMBIOSE — sim/actions/couts.py
Catalogue des coûts de base + le SEAM « coût d'action » de la maîtrise
(CONCEPTION_MAITRISE §4.2/§10.4). « Ce que les gestes coûtent », isolé des gestes
eux-mêmes. NEUTRE (1.0) tant qu'aucune maîtrise n'est acquise → les coûts en dur
d'avant restent identiques (golden Vigueur intact).
"""
from __future__ import annotations

from sim import maitrise as M   # couche savoir (D12) — lue ici pour atténuer les coûts
from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE   # reverse classe→clé (seam coût, §10.4)

# Paliers de coût, relatifs à la base 100 / +10 par semaine (spec §3.1, à
# calibrer post-test).
NUL    = 0.0
FAIBLE = 5.0
MODERE = 15.0
ELEVE  = 30.0
URGENCE_MULT = 1.5   # majoration des actions de phase « saison » (urgence, §3.1)

# Le hook de la conception (§3.5) devient réel : le geste de prélèvement de la
# récolte sélective coûte FAIBLE (remplace le `=0` neutre supprimé de l'engine).
HARVEST_VIGUEUR_COST = FAIBLE


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
    "planter":              FAIBLE,            # dépose une graine (phase planification, §3.2/Q7)
    "arroser":              MODERE,            # × URGENCE_MULT appliqué PAR-DESSUS si phase saison
    "recolter":             HARVEST_VIGUEUR_COST,
    "deraciner":            ELEVE,
    "ecraser":              MODERE,            # × URGENCE_MULT appliqué PAR-DESSUS (phase saison)
    "favoriser_auxiliaire": MODERE,
    "becher":               FAIBLE,
    "grelinette":           MODERE,
    "pailler":              MODERE,            # dépose du mulch au sol (phase planification, équilibre invasion ③ §2)
    "broyer":               MODERE,            # broie du bois → BRF (phase planification, équilibre invasion ④ §3.1)
    "tailler":              MODERE,            # geste direct sur le vivant (philo #1) — coût modéré
    "couper":               MODERE,            # geste BRUT ancêtre de tailler (palette D12) — même coût, sans choix de segment
    "manger":               NUL,               # coût NUL → cout_action renvoie 0 sans rien lire (§10.5)
    "poser_bac":            MODERE,            # pose une structure (phase planification, ⑤ §5.1)
    "poser_pile":           MODERE,
    "composter":            FAIBLE,            # déplace la litière tendre plot→bac (canal vertueux §5.1)
    "empiler_bois":         FAIBLE,            # déplace le bois plot→pile
    "retourner":            FAIBLE,            # accélère/lisse la maturation du bac (bonus §5.2, canal vertueux)
    "epandre":              FAIBLE,            # restitue le compost mûr au sol → trio humus (§5.3, canal vertueux)
    "poser_ruche":          MODERE,            # pose une ruche (phase planification, ⑥ §H.1)
    "recolter_miel":        HARVEST_VIGUEUR_COST,  # canal récolte (miel → Vigueur, ⑥ §I.2)
    "poser_pot":            MODERE,            # pose un POT mobile rempli (pots/bacs ④ §4)
    "poser_bac_culture":    MODERE,            # pose un BAC immobile N×M rempli (pots/bacs ④ §4)
    "deplacer_pot":         MODERE,            # déplace un pot — effort joueur SEUL (pots/bacs ④ §4)
    "poser_tuteur":         MODERE,            # pose un tuteur (planification, grimpantes ④ §6)
    "poser_treillis":       MODERE,            # pose un treillis (planification, grimpantes ④ §6)
    "poser_pergola":        MODERE,            # pose une pergola (planification, grimpantes ④ §6)
    "palisser":             MODERE,            # noue une canne sarmenteuse à un support (grimpantes ④ §6)
}

# Objets STATIQUES touchés par chaque geste (§10.4, terme 2 : technique + outil/
# structure requis). La CIBLE VIVANTE n'y est PAS (dynamique : elle dépend de la
# plante cliquée → l'appelant l'ajoute via `_objets_action`). Clés = strings au
# même titre que les espèces (maîtrise catalogue-agnostique, i1). Aucun de ces
# objets n'a d'état moteur aujourd'hui → `M.palier(...) == 0` → atténuation neutre
# 1.0 (dégradation gracieuse §10.5) ; la table les NOMME pour quand leur sprint
# (D29/D30/D31) les câblera. Reflète §10.4 telle quelle.
OBJETS_TOUCHES = {
    "planter":              ("semis",),                  # technique ; pas de cible vivante (on DÉPOSE une graine)
    "arroser":              ("arrosage", "arrosoir"),    # technique + outil ; on écrit un CHAMP, pas de cible vivante
    "recolter":             ("récolte", "sécateur"),
    "deraciner":            ("arrachage", "bêche"),
    "ecraser":              (),                          # geste brut, terme 2 vide (§10.4)
    "favoriser_auxiliaire": ("aménagement-habitat",),
    "becher":               ("bêchage", "bêche"),
    "grelinette":           ("ameublissement", "grelinette"),
    "pailler":              ("paillage",),       # technique ; on écrit un CHAMP, pas de cible vivante — sans état moteur → atténuation neutre 1.0
    "broyer":               ("broyage", "broyeur"),   # technique + outil (BRF, équilibre invasion ④) — sans état moteur → atténuation neutre 1.0

    "tailler":              ("taille", "sécateur"),
    "couper":               ("taille", "sécateur"),   # geste brut D12 : même technique/outil que tailler
    "manger":               (),                          # coût NUL → terme 2 vide (§10.5)
    "poser_bac":            ("compostage", "bac-à-compost"),
    "poser_pile":           ("compostage", "pile-à-bois"),
    "composter":            ("compostage",),
    "empiler_bois":         ("compostage", "pile-à-bois"),
    "retourner":            ("compostage", "fourche"),
    "epandre":              ("compostage", "amendement"),
    "poser_ruche":          ("apiculture", "ruche"),
    "recolter_miel":        ("apiculture", "équipement-apicole"),
    "poser_pot":            ("jardinage_hors_sol", "pot"),     # concept sans état moteur → atténuation neutre 1.0
    "poser_bac_culture":    ("jardinage_hors_sol", "bac"),
    "deplacer_pot":         ("jardinage_hors_sol",),
    "poser_tuteur":         ("palissage", "tuteur"),           # technique + outil (grimpantes ④ §6) — sans état moteur → neutre 1.0
    "poser_treillis":       ("palissage", "treillis"),
    "poser_pergola":        ("palissage", "pergola"),
    "palisser":             ("palissage",),                    # technique seule ; la cible vivante est ajoutée par _objets_action
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
