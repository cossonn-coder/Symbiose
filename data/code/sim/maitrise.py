"""
SYMBIOSE — sim/maitrise.py
Couche MAÎTRISE JOUEUR (D12, tronçon i1) — le *cœur* de la maîtrise, miroir
structurel de la couche Vigueur (`sim/vigueur.py`).

Spec de référence : `data/code/CONCEPTION_MAITRISE.md`.
  §1   l'objet de maîtrise = unité atomique, paliers 0..5, catalogue-agnostique.
  §2.1 découverte (0→1) gratuite, par simple observation.
  §2.3 courbe de difficulté logarithmique : preuves(k) ≈ ceil(BASE·R**(k-1)).
  §2.4 réversibilité MONOTONE : un palier ne se perd jamais.
  §6   méta-état PAR AVATAR, vivant AU-DESSUS du tick écologique déterministe.

Principe directeur (§6, identique à la Vigueur) : cette couche ne fait JAMAIS
avancer la simulation écologique. Le golden écologique (`tests/test_golden.py`)
est une succession spontanée *sans joueur* → aucune clé `maitrise` → no-op
strict. Si le golden bouge, c'est un BUG (fuite dans le tick), pas un re-figeage.

Périmètre i1+i2 (le reste est gated, cf. `sprints/sprint_D12_impl/00_etat.md`) :
  - i1 : cœur (découverte, progression intra-objet, monotone, plafond).
  - i2 : AGRÉGATS dérivés (complétude-ratio §3.2, accumulation-log §3.2),
         SPILLOVER famille (§3.1, lit `plants/`), `palier_bonus` (§4.1).
  - PAS de seam `cout_action`                                  → i3
  - PAS de détection automatique de succès (zéro hook tick)    → i4
Ici, les preuves arrivent UNIQUEMENT par appel direct d'API (injection). Les
*sources ponctuelles de Vigueur* (§4.3 : gain à la découverte / au franchissement)
vivent dans la couche d'orchestration `sim/actions.py` — ce module reste pur
(il ne dépend PAS de `vigueur.py`), c'est `vigueur.palier_bonus` qui dépend de
LUI (sens naturel : la capacité de Vigueur dérive de la maîtrise, §4.1).
"""
from __future__ import annotations

import math

from plants.catalogue import PLANT_CATALOGUE, PERENNIAL_CATALOGUE

# --- Courbe de difficulté (§2.3) -------------------------------------------
# Nombre de preuves pour franchir k → k+1 : ceil(BASE * R**(k-1)).
# PLACEHOLDERS NOMMÉS — *à calibrer post-test (D12.4)*. Valeurs choisies pour
# rendre la courbe visible et croissante dans les golden (2, 4, 8, 16).
PREUVES_BASE = 2     # BASE — preuves pour le premier franchissement (1→2)
PREUVES_R    = 2     # R    — facteur géométrique (croissance des paliers)
PALIER_MAX   = 5     # transcendant (CLAUDE.md) — on ne franchit jamais au-delà

# --- Agrégats dérivés (§3.2) — PLACEHOLDERS NOMMÉS, *calibrage D12.4* ----------
# K du plafond/régen (§4.1) : palier_bonus = 1 + K·log1p(accumulation). Plus K
# est grand, plus la maîtrise gonfle la Vigueur max — mais le log écrase toujours
# (anti-super-héros §3.2). K=0 redonnerait le stub neutre 1.0.
PALIER_BONUS_K = 0.05
# Taux de spillover intra-famille (§3.1) : chaque palier de maîtrise acquis sur
# une espèce SŒUR (même famille, hors découverte) accélère d'autant la
# progression des autres. 0.0 désactiverait le spillover.
SPILLOVER_RATE = 0.5

# Mapping espèce → famille botanique, DÉRIVÉ des catalogues moteur (§10.0/§10.1) :
# la taxonomie REFLÈTE `plants/`, elle ne duplique aucune liste figée. Un objet
# absent de ce mapping (concept transversal, outil, structure…) n'a pas de famille
# → aucun spillover (§3.1 : le spillover ne concerne que les êtres vivants).
_FAMILLE_DE_ESPECE: dict[str, str] = {
    cle: cls.family
    for cle, cls in {**PLANT_CATALOGUE, **PERENNIAL_CATALOGUE}.items()
}


def famille_de(objet: str) -> str | None:
    """Famille botanique d'un objet de maîtrise s'il est une espèce du catalogue
    (§10.1), sinon `None` (concept transversal / outil / structure → pas de
    famille, donc pas de spillover §3.1)."""
    return _FAMILLE_DE_ESPECE.get(objet)


# --- État joueur (miroir de vigueur.ensure_player) -------------------------
def ensure_player_maitrise(game_state: dict, player: str) -> dict:
    """Crée (si besoin) et renvoie la tranche maîtrise d'un joueur. C'est le
    geste d'OPT-IN (§6) : tant qu'aucun joueur n'est enregistré, `game_state`
    n'a pas de clé `maitrise` et le tick reste un no-op strict (golden intact).

    Invariant : un objet n'entre dans `objets` qu'au palier ≥ 1 (découvert).
    L'absence d'un objet du dict EST son palier 0 (inconnu)."""
    mait = game_state.setdefault("maitrise", {})
    return mait.setdefault(player, {"objets": {}})


def palier(game_state: dict, player: str, objet: str) -> int:
    """Lecture pure du palier d'un objet ; `0` si l'objet est inconnu (jamais
    découvert). Ne crée RIEN (lecture d'un inconnu = 0, sans opt-in)."""
    mait = game_state.get("maitrise")
    if not mait:
        return 0
    st = mait.get(player)
    if not st:
        return 0
    o = st["objets"].get(objet)
    return o["palier"] if o else 0


# --- Découverte (§2.1, gratuite) -------------------------------------------
def decouvrir(game_state: dict, player: str, objet: str) -> bool:
    """Passage `0 → 1` par simple observation (§2.1) : gratuit, aucun succès
    requis. Idempotent : ne fait rien si l'objet est déjà découvert (palier ≥ 1).
    Renvoie `True` ssi une *nouvelle* découverte a eu lieu (i2 s'en servira pour
    le gain ponctuel de Vigueur, §4.3 ; ici on renvoie juste le booléen)."""
    st = ensure_player_maitrise(game_state, player)
    if objet in st["objets"]:               # déjà au palier ≥ 1 (invariant)
        return False
    st["objets"][objet] = {"palier": 1, "preuves": 0}
    return True


# --- Progression par preuves (§2.2/§2.3, monotone §2.4) --------------------
def preuves_requises(k: int) -> int:
    """Preuves pour franchir `k → k+1` (§2.3), `k ∈ {1,2,3,4}` (pas de
    franchissement au-delà de PALIER_MAX). Courbe géométrique ⇒ début rapide,
    haut paliers lents (un joueur qui sait enchaîne le début, ralentit vers
    l'expertise — cf. spec §2.3)."""
    return math.ceil(PREUVES_BASE * PREUVES_R ** (k - 1))


def _facteur_spillover(slice_joueur: dict, objet: str) -> float:
    """Facteur de vitesse de progression (§3.1) gonflé par la maîtrise des espèces
    SŒURS déjà découvertes (même famille). Chaque palier de maîtrise d'une sœur
    AU-DELÀ de la simple découverte (palier > 1) accélère d'autant (SPILLOVER_RATE)
    — « être avancé sur la tomate accélère l'aubergine ». Le seuil « ≥2 espèces
    découvertes » (§10.1) tombe naturellement : une sœur juste découverte
    (palier 1) ne transfère rien (palier−1 = 0). JAMAIS inter-famille ; objet sans
    famille (concept/outil) → 1.0 (pas de spillover)."""
    famille = famille_de(objet)
    if famille is None:
        return 1.0
    soeurs = sum(o["palier"] - 1 for cle, o in slice_joueur["objets"].items()
                 if cle != objet and famille_de(cle) == famille)
    return 1.0 + SPILLOVER_RATE * soeurs


def enregistrer_preuve(game_state: dict, player: str, objet: str) -> int:
    """Le cœur. Crédite une preuve à l'objet — pondérée par le SPILLOVER famille
    (§3.1) : sur une espèce dont les sœurs sont maîtrisées, une preuve « compte
    pour plus » — puis franchit autant de paliers que le crédit le permet
    (consommation CUMULATIVE : le reliquat reste au crédit du palier suivant).
    Renvoie le palier courant après mise à jour.

    Auto-découverte (défaut acté §i1) : enregistrer une preuve sur un objet
    inconnu le découvre d'abord (0→1) — une preuve implique qu'on l'a observé.

    MONOTONE (§2.4) : un palier ne redescend jamais ; il n'existe aucune
    fonction de décrément. Plafonné à PALIER_MAX (§1)."""
    st = ensure_player_maitrise(game_state, player)
    o = st["objets"].get(objet)
    if o is None:                           # auto-découverte (0→1) puis crédit
        o = {"palier": 1, "preuves": 0}
        st["objets"][objet] = o
    o["preuves"] += _facteur_spillover(st, objet)
    while o["palier"] < PALIER_MAX and o["preuves"] >= preuves_requises(o["palier"]):
        o["preuves"] -= preuves_requises(o["palier"])
        o["palier"] += 1
    return o["palier"]


# --- Agrégats dérivés (strate 2, §3.2) — CALCULÉS, jamais stockés en double ----
def _objets_decouverts(game_state: dict, player: str) -> dict:
    """Tranche `objets` du joueur (dict vide si aucune couche maîtrise / joueur).
    Lecture pure — ne crée AUCUNE clé (préserve le no-op golden)."""
    mait = game_state.get("maitrise")
    if not mait:
        return {}
    st = mait.get(player)
    return st["objets"] if st else {}


def accumulation_globale(game_state: dict, player: str) -> float:
    """Somme BRUTE de maîtrise sur TOUS les objets découverts — espèces ET concepts
    transversaux, même pool (§3.2). Matière première du plafond/régen de Vigueur,
    AVANT l'écrasement logarithmique (appliqué par `palier_bonus`, §4.1). Le terme
    « + activité » (§3.2) viendra avec la détection de succès (i4) ; ici, c'est
    Σ paliers."""
    return float(sum(o["palier"] for o in _objets_decouverts(game_state, player).values()))


def completude_ratio(game_state: dict, player: str) -> float:
    """Complétude = Σ paliers / (PALIER_MAX × nb objets DÉCOUVERTS) ∈ [0,1] (§3.2).
    Dénominateur = découverts SEULEMENT → aucune dilution quand le catalogue
    grossit (« à quel point je maîtrise ce que je connais »). Sert aux SEUILS de
    déblocage (magazine D13, terrain D15). 0.0 si rien n'est découvert."""
    objets = _objets_decouverts(game_state, player)
    if not objets:
        return 0.0
    return sum(o["palier"] for o in objets.values()) / (PALIER_MAX * len(objets))


def palier_bonus(game_state: dict, player: str) -> float:
    """Multiplicateur de maîtrise (§4.1) qui REMPLIT le stub de `sim/vigueur.py`
    (plafond Vigueur max et régen passive sont × ce scalaire). Alimenté par
    l'accumulation-log → rendements décroissants (anti-super-héros §3.2) :

        1 + K · log1p(accumulation_globale).

    NEUTRE (1.0) tant qu'aucune maîtrise n'est acquise (log1p(0) = 0) → un
    `game_state` sans couche maîtrise garde un bonus de 1.0 : le golden Vigueur
    reste INTACT, le découplage §4.1 tient (D12 ne fait que *remplir* la valeur)."""
    return 1.0 + PALIER_BONUS_K * math.log1p(accumulation_globale(game_state, player))
