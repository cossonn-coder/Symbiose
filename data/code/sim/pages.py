"""
SYMBIOSE — sim/pages.py
LES PAGES SECRÈTES — troisième des quatre voix narratives (sprint Voix narratives,
tronçon ⑤, dette D18).
Spec de référence : `docs/conception/CONCEPTION_VOIX_NARRATIVES.md` §2.3 + §7.

Voix MULTIPLES (cinq registres éditoriaux), LORE PUR. Les pages ne débloquent
RIEN : ZÉRO effet mécanique (décision adoptée §2.3). Elles RÉSONNENT avec ce que
le joueur vit et récompensent l'exploration. Consultation au coffret du grenier
(UI Godot = dette D24, hors périmètre ici).

ÉTAT TRIVIAL & OPT-IN (le cœur du « golden intact ») :
    game_state["pages"][player] = set(ids révélés)
Tant que `ensure_player()` n'est pas appelé, aucune clé `pages` n'existe : le
golden tourne une succession spontanée *sans joueur* → no-op total (miroir strict
de `journal`/`maitrise`/`vigueur`). Si le golden bouge, c'est une FUITE (BUG),
jamais un re-figeage.

GARDE-FOU DE COUCHE (identique à `journal.py` / `carnet.py` / `encyclopedie.py`) :
`pages` est au niveau `sim`, AU-DESSUS du tick. **`engine`/`fields`/`plants` ne
l'importent JAMAIS** — c'est le DRIVER qui appelle `reveler_page()` hors tick,
exactement comme `consigner()`. Le seul RNG autorisé est `_hash_noise`
DÉTERMINISTE (robinet *hasard*) — jamais `random` (philo de design #3 : tout est
reproductible sur seed + semaine).

LES 3 ROBINETS (§2.3) — chacun révèle UNE page « due » non encore trouvée :
  - `"récompense"` : adossé à un SUCCÈS de maîtrise. `contexte["concept"]` cible
    le concept du succès → prochaine page due DE CE CONCEPT (une belle réalisation,
    une belle page). Aucune page de ce concept restante → `None`.
  - `"hasard"`     : aléa déterministe au passage de saison. `contexte` porte
    `seed` + `semaine` → `_hash_noise` choisit parmi les pages non trouvées (ancrage
    PROVISOIRE §4 : les marqueurs bouture/oiseau/vent n'existent pas encore).
  - `"fouille"`    : action joueur au grenier → prochaine page due GLOBALEMENT
    (déterministe, pas de RNG live).

ÉPUISABLE : une page n'est jamais re-révélée (déjà dans le set) ; quand il ne
reste rien pour le robinet sollicité, il est MUET (`None`) — c'est du bonus, pas
un game-feel de manque (§2.3).

« Page due » = pages NON trouvées triées par `palier_theme` croissant (tri stable
secondaire = `id`, ordre du corpus). Le robinet *récompense* restreint d'abord au
concept ; *fouille* prend la 1ʳᵉ due globale ; *hasard* tire dans le pool.
"""
from __future__ import annotations

from fields.noise import _hash_noise
from sim.pages_corpus import PAGES, ORDRE

# --- Canal _hash_noise dédié (décorrélé des autres consommateurs) -------------
# `_hash_noise(seed, week, r, c)` prend 4 entiers ; on lui passe un SALT constant
# en place de (r, c) pour réserver un canal « page » propre, exactement comme la
# population dédie `_SALT_CARPOPHORE`. Le doc écrit `_hash_noise(seed, semaine,
# "page")` — la chaîne devient ici ce salt entier (la signature réelle est en int).
_SALT_PAGE = 0x9A6E5  # « page » — canal réservé, sans collision avec les guildes


def ensure_player(game_state: dict, player: str) -> set:
    """Crée (si besoin) et renvoie le SET des pages trouvées d'un joueur. Geste
    d'OPT-IN (§2.3) : tant que personne ne l'appelle, `game_state` n'a pas de clé
    `pages` et le tick reste un no-op strict (golden intact). Le driver l'appelle
    indirectement via `reveler_page()` ; le golden ne l'appelle jamais.

    NB sérialisation (cycle save §CLAUDE) : l'état est un `set` (in-memory) ; au
    save JSON il faudra le convertir `set ↔ list` (D24, save pas encore câblé)."""
    pages = game_state.setdefault("pages", {})
    return pages.setdefault(player, set())


def pages_trouvees(game_state: dict, player: str) -> set:
    """Renvoie le SET des ids de pages révélées au joueur — ou `set()` vide si la
    clé n'existe pas (lecture PURE, ne crée AUCUNE clé → no-op golden). Read-only :
    c'est la consultation du coffret du grenier."""
    return set(game_state.get("pages", {}).get(player, set()))


def _due(trouvees: set, concept: str | None = None) -> list[str]:
    """Liste des pages « dues » (non trouvées), triées par `palier_theme` croissant
    puis par ordre du corpus (`id`) — tri STABLE et déterministe. Si `concept` est
    fourni, on restreint aux pages de ce concept (robinet *récompense*). PUR."""
    candidats = [pid for pid in ORDRE
                 if pid not in trouvees
                 and (concept is None or PAGES[pid]["concept"] == concept)]
    # `ORDRE` est déjà l'ordre du corpus → tri par palier_theme stable dessus.
    return sorted(candidats, key=lambda pid: PAGES[pid]["palier_theme"])


def reveler_page(game_state: dict, player: str,
                 robinet: str, contexte: dict | None = None) -> str | None:
    """Révèle UNE page via le `robinet` demandé et l'ajoute au set du joueur.
    Renvoie l'id révélé, ou `None` si le robinet est muet (rien de dû). HORS TICK :
    appelé par le DRIVER (passage de saison / action grenier), jamais par `engine`.

    ZÉRO EFFET MÉCANIQUE (§2.3, « Pièges » du kickoff) : la SEULE écriture est
    l'ajout de l'id à `game_state["pages"][player]` — aucun champ écologique, aucune
    plante, aucune Vigueur n'est touchée. Le robinet *hasard* est le seul à tirer un
    aléa, et c'est `_hash_noise` DÉTERMINISTE (reproductible sur seed + semaine).

    `contexte` selon le robinet :
      - "récompense" : {"concept": <concept du succès>} → page due de ce concept.
      - "hasard"     : {"seed": <int>, "semaine": <int>} → tirage déterministe.
      - "fouille"    : ignoré (prochaine page due globale)."""
    contexte = contexte or {}
    trouvees = ensure_player(game_state, player)

    if robinet == "récompense":
        dues = _due(trouvees, concept=contexte.get("concept"))
        choix = dues[0] if dues else None              # plus petit palier_theme dû
    elif robinet == "fouille":
        dues = _due(trouvees)
        choix = dues[0] if dues else None              # 1ʳᵉ due globale
    elif robinet == "hasard":
        dues = _due(trouvees)                           # n'importe quelle page non trouvée
        if not dues:
            choix = None
        else:
            # Ancrage DÉTERMINISTE (§2.3 / §4) : `_hash_noise(seed, semaine, salt)`
            # ∈ [0,1] → index stable dans le pool des dues. Même seed + même semaine
            # ⇒ même page (philo #3). `dues` est trié → l'index est reproductible.
            seed = int(contexte.get("seed", 0))
            semaine = int(contexte.get("semaine", 0))
            h = _hash_noise(seed, semaine, _SALT_PAGE, 0)
            idx = min(len(dues) - 1, int(h * len(dues)))
            choix = dues[idx]
    else:
        choix = None                                    # robinet inconnu → muet

    if choix is not None:
        trouvees.add(choix)
    return choix
