# Tronçon 02 — Acquisition Atelier + registre `OUTILS` → déblocage sécateur

> Tu démarres À FROID. Lis `CLAUDE.md`, `00_etat.md`, puis
> `docs/joueur/outils/conception_acquisition_outils.md` §B. **CŒUR de la dette D82.**

## Objectif
Donner au joueur un canal d'acquisition du sécateur (marqueur `posseder_secateur`)
que RIEN ne pose aujourd'hui → toute la chaîne taille (`couper`→`tailler`→
`bouturer`) est morte. Canal = l'**Atelier** du hub-maison (seule des 5 fonctions
non câblée), Vigueur seule, **miroir d'`acheter_au_magazine`** mais posant un
marqueur d'outil au lieu de déposer une graine.

## Le patron à copier
`sim/magazine.py::acheter_au_magazine(game_state, player, espece) -> bool`
(importé `tools/simserver/actions.py:21`, dispatché au verbe `acheter_magazine`
`actions.py:109`) : gate une offre + `spend` Vigueur + effet (dépose graine),
bool jamais d'exception. Ton `acquerir_outil` en est le jumeau, l'effet étant
`marquer_action` + `evaluer_deblocages`.

## Fichiers à toucher
1. **`sim/outils.py` (NEUF)** — jumeau de `sim/magazine.py` :
   - Registre **`OUTILS`** data-driven :
     `OUTILS = {"secateur": {"marqueur": "posseder_secateur",
     "cout_vigueur": <placeholder, calibrage F5>, "offre": True}}`.
     Un seul outil ; structure extensible (greffoir/bêche plus tard).
   - `offre_outils(game_state, player) -> list[str]` : outils dont `offre` est
     ouverte (ici : toujours `["secateur"]` — porte Vigueur seule, aucune maîtrise).
   - `acquerir_outil(game_state, player, outil) -> bool` : refus si hors offre ;
     `cost = OUTILS[outil]["cout_vigueur"]` ; `if spend(gs, player, cost) < 1.0:
     return False` ; puis `marquer_action(gs, player, OUTILS[outil]["marqueur"])`
     + `evaluer_deblocages(gs, player)` (import depuis `sim.actions.deblocage`).
     Idempotent : ré-acquérir un outil déjà possédé → pas de nouvelle dépense
     (vérifie le marqueur déjà posé, refuse proprement).
   - Respecte la règle de couches : `sim/outils.py` importe `sim.vigueur` +
     `sim.actions.deblocage`, jamais l'inverse.
2. `tools/simserver/actions.py` — verbe **`acheter_outil`** (patron
   `acheter_magazine`, `actions.py:109` : chemin Vigueur UNIQUE, sans tuile ;
   `outil = params.get("outil")` ; `bilan` rafraîchissant vigueur/vigueur_max ;
   message « sécateur acquis à l'atelier » / « acquisition refusée »). Expose
   `achete` dans le result comme `acheter_magazine`. **Bump protocole** (numéro
   libre après le tronçon 01) + entrée `version.py`.

## Golden
**INCHANGÉ** — acquisition opt-in hors tick, smoke sans joueur. `python3 -m
tests.test_golden` : hash figé.

## Tests ciblés
- État initial : `couper`/`tailler` **verrouillés** (`evaluer_deblocages` ne les
  liste pas ; ou le dispatch `couper` refuse). Vérifie via la table de déblocage.
- Après `acquerir_outil(gs, player, "secateur")` avec Vigueur suffisante :
  `posseder_secateur` marqué, `couper` **puis** `tailler` déverrouillés
  (`evaluer_deblocages` les rend), Vigueur débitée du `cout_vigueur`.
- Vigueur insuffisante : refus, marqueur NON posé, aucune dépense.
- Ré-acquisition : pas de seconde dépense.

## NE FAIS PAS
- Ne gate PAS l'acquisition sur une maîtrise (poule-œuf `taille` interdit).
- Ne touche pas `couper`/`tailler` (ils s'ouvrent seuls via la chaîne).
- Pas de logique de matériaux mulch ici (c'est le tronçon 03 — mais tu POSES
  l'infra Atelier que 03 réutilisera).
- Pas de re-figeage golden.

## Fin de tronçon
Mets à jour `00_etat.md` §REPRISE (02 fait, D82 levée côté moteur, prochain = 03)
et commit (`feat(moyens) ② : acquisition sécateur à l'Atelier — lève D82`).
