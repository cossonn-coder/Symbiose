# Tronçon ① — Module moteur `sim/quetes.py` + conditions cumulées

> Sprint QUÊTES (D79). Lire d'abord : `CLAUDE.md`, `00_etat.md`,
> `docs/joueur/automate/conception_quetes.md`. Golden : **INCHANGÉ**.

## Objectif
Poser le **système de quêtes MOTEUR côté joueur** (neuf, distinct du harnais
automate `tools/jardinier_auto/`) et faire fonctionner la première famille de
conditions : **`recolte_cumulee`** (« 10 patates récoltées »), comptée par un
**hook sur le geste joueur**.

## Contexte de vérité (déjà vérifié, ne pas re-débattre)
- **F1** : `tools/jardinier_auto/objectifs.py` est le harnais AUTOMATE. NE PAS
  le réutiliser ni l'importer. D79 est un module **moteur** neuf `sim/quetes.py`.
  On peut s'en INSPIRER pour la forme (dataclass frozen `Quete`, état séparé dans
  `game_state`, tri déterministe par `id`) mais le code est indépendant.
- **F2** : `sim/evenements.py` est un parseur de log — NE PAS l'utiliser pour
  détecter l'accomplissement. Le comptage cumulé est un **hook** (ci-dessous).
- Point de passage unique des gestes joueur sur plante :
  `tools/simserver/plante_route.py::route_plante(gs, player, verb, ...)` qui
  délègue aux façades `sim.actions`. Plantation/arrosage ont leurs routes dédiées
  (`plante_route.py`, `commands.py`). Le `recolter` réussi renvoie un ratio.

## À implémenter
1. **`sim/quetes.py`** (couche `sim`, jamais importée par `engine` → golden) :
   - `@dataclass(frozen=True) class Quete` : `id: str`, `donneur: str`,
     `condition` (voir ci-dessous), `recompense` (posé, traité ③/④),
     `declencheur` (posé, traité ③). La PROGRESSION vit hors du frozen, dans
     `game_state["quetes"]` (cf. F1/objectifs.py pour le pattern).
   - Représentation de condition = **mini-catalogue déclaratif** (§4 conception).
     Pour ①, un seul type actif : `("recolte_cumulee", geste, quantite, cible)`.
     Prévoir l'aiguillage par le 1er élément (tag) pour que ② ajoute ses types
     sans toucher l'existant.
   - État : `game_state["quetes"] = {id: {"quete", "progression", "semaine_debut",
     "semaine_fin"}}`, opt-in strict (aucune clé tant qu'aucune quête ajoutée →
     **golden intact**). Ordre d'insertion, toute LISTE triée par `id` (#3).
   - API : `ajouter_quete`, `quetes_actives`, `progression`, `est_accomplie`,
     `notifier_geste(game_state, player, verbe, plant)` (le HOOK : +1 sur chaque
     quête `recolte_cumulee` active servie par ce geste ; à l'atteinte de la
     quantité → close + **émet un événement au ledger** pour le carnet, cf. §7
     conception). Réutiliser l'idée `sert()`/`incrementer()` d'objectifs.py.
2. **Brancher le hook** : appeler `quetes.notifier_geste(...)` depuis
   `route_plante` (et la route de plantation si une quête `planter` est voulue)
   APRÈS un geste réussi. Le pont est une couche fine qui appelle le moteur —
   c'est le point de dispatch unique côté joueur. Import LÉGER.
3. **Consignation ledger** : à l'accomplissement, émettre une ligne de log
   parsable (cf. style `sim/evenements.py`) pour qu'une entrée carnet « j'ai
   porté … au voisin » puisse naître. NE PAS inventer un nouveau canal.

## Tests
- `tests/test_quetes.py` : ajout d'une quête `recolte_cumulee(recolter, 3,
  "tomate")`, 3 récoltes → accomplie, événement émis ; une récolte d'une autre
  espèce n'incrémente pas ; ordre déterministe ; opt-in (aucune quête → état
  vierge).
- `python3 -m tests.test_golden` → **hash INCHANGÉ** (opt-in, aucune quête dans
  le golden). Si le hash bouge, le hook fuit hors opt-in → corriger.

## Ne PAS faire
- Pas de condition d'état (tronçon ②). Pas de déclenchement auto / table de
  quêtes / voix (③). Pas de récompense effective (③/④). Pas de vue Godot (⑤).
- Ne pas toucher `tools/jardinier_auto/`. Ne pas re-parser le ledger.

## Fin de tronçon
Golden vérifié inchangé → maj `00_etat.md` (§REPRISE : ② prêt) → commit.
