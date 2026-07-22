"""
SYMBIOSE — sim/journal.py
Le LEDGER D'ÉVÉNEMENTS partagé (sprint Voix narratives, tronçon ②).
Spec de référence : `docs/narration/voix/conception_voix_narratives.md` §1.3/§1.4.

Substrat commun aux quatre voix narratives (carnet ③, encyclopédie ④, pages ⑤,
magazine ⑥). Il n'INTERPRÈTE rien : il se contente d'ENREGISTRER, semaine après
semaine, le flux d'`Evenement` que `sim/evenements.evenements(log)` extrait du
`log` texte du tick. Les voix sont des LECTEURS read-only de cet état.

GARDE-FOU DE COUCHE (identique à `vigueur.py` / `maitrise.py` / `evenements.py`) :
`journal` est au niveau `sim`, AU-DESSUS du tick. **`engine`/`fields`/`plants` ne
l'importent JAMAIS** — c'est le DRIVER (`tools/simserver/commands.py`) qui appelle
`consigner()` après chaque `tick_semaine()`, exactement comme le hook hors tick
décrit au §1.4. Il importe `sim.evenements` (①), rien de plus haut.

OPT-IN STRICT (le cœur du « golden intact ») : l'état `game_state["journal"]`
n'existe que si `ensure_player()` a été appelé. Le golden écologique tourne une
succession spontanée *sans joueur* → aucune clé `journal` → no-op total. Si le
golden bouge après ce tronçon, c'est une FUITE dans le tick (BUG), jamais un
re-figeage.

État (doc §1.3) :
    game_state["journal"][player] = {
        "entries": [ {semaine, zone, kind, cause, espece}, … ],  # append-only borné
        "resume":  { (kind, cause): count, … },                  # agrégat des repliés
    }
Append-only BORNÉ (run éternel → pas de journal infini) : on garde les
`JOURNAL_MAX` dernières entrées détaillées ; au-delà, la plus ancienne est
REPLIÉE dans `resume` (incrément du compteur `(kind, cause)`) avant d'être retirée
— exactement comme la morphogénèse borne ses segments. Le `resume` survit au save,
le détail ancien non (« je me souviens *qu'il a souvent fait sec ici*, plus du
détail de chaque semaine »).
"""
from __future__ import annotations

from sim.evenements import evenements

# --- Calibrage (PLACEHOLDER NOMMÉ, à régler post-test D12.4) ------------------
# Nombre maximal d'entrées détaillées conservées par joueur. Au-delà, la plus
# ancienne se replie dans `resume`. 200 = valeur proposée par le doc §1.3.
JOURNAL_MAX = 200


# --- État joueur (miroir de maitrise.ensure_player_maitrise) -----------------
def ensure_player(game_state: dict, player: str) -> dict:
    """Crée (si besoin) et renvoie la tranche journal d'un joueur. C'est le geste
    d'OPT-IN (§1.3) : tant que personne ne l'appelle, `game_state` n'a pas de clé
    `journal` et le tick reste un no-op strict (golden intact). Le serveur
    l'appelle indirectement via `consigner()` ; le golden ne l'appelle jamais."""
    journal = game_state.setdefault("journal", {})
    return journal.setdefault(player, {"entries": [], "resume": {}})


# --- Consignation hors tick (§1.4) -------------------------------------------
def consigner(game_state: dict, player: str, log: list[str], semaine: int) -> int:
    """Point d'entrée HORS TICK, appelé par le DRIVER après `tick_semaine()` et
    AVANT le vidage du `log`. Symétrique de `maitrise_detection.detecter()` et de
    `vigueur.tick_player_vigueur()`. PUR au sens golden : il LIT le `log`, n'avance
    aucun tick, ne touche aucun champ écologique, n'utilise aucun RNG.

    Pour chaque `Evenement` du flux (`evenements.evenements(log)`), il appende une
    entrée bornée à la tranche du joueur. Renvoie le nombre d'entrées ajoutées
    (utile aux tests ; sans valeur de gameplay)."""
    st = ensure_player(game_state, player)
    ajoutes = 0
    for ev in evenements(log):
        _appender(st, {
            "semaine": semaine,
            # `zone` = identité stable §1.3 : (tile_id, r, c). `pos` est (r, c) ou
            # None (aléa sans plante : ravageur de saison) → zone réduite au tile.
            "zone": (ev.tile_id, ev.pos[0], ev.pos[1]) if ev.pos else (ev.tile_id,),
            "kind": ev.kind,
            "cause": ev.cause,
            "espece": ev.espece,
        })
        ajoutes += 1
    return ajoutes


def _appender(st: dict, entree: dict) -> None:
    """Append BORNÉ (§1.3) : ajoute l'entrée, puis tant que `entries` dépasse
    `JOURNAL_MAX`, replie la PLUS ANCIENNE dans `resume[(kind, cause)] += 1` avant
    de la retirer. Le résumé agrège ce qu'on « se souvient en gros » ; le détail
    récent reste consultable. Bornage par la TÊTE (FIFO) : on perd le vieux, on
    garde le frais."""
    entries = st["entries"]
    entries.append(entree)
    while len(entries) > JOURNAL_MAX:
        vieux = entries.pop(0)
        cle = (vieux["kind"], vieux["cause"])
        st["resume"][cle] = st["resume"].get(cle, 0) + 1
