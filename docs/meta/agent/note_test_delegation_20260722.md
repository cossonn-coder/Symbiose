# Note — test de la délégation DeepSeek (2026-07-22)

> **Provenance** : corps rédigé par `write-deepseek` (`--lang markdown`) à partir de
> deux réponses `ask-deepseek`, puis **revérifié ligne à ligne par Claude** contre
> les fichiers sources. Premier test grandeur nature du protocole gravé le même jour
> (`deepseek_protocol.md`). Les faits ci-dessous ont été confirmés par lecture directe ;
> ce qui n'a pas résisté à la revérification est consigné en §Réserves.

## État des sprints

Sprints dont un **tronçon d'exécution** reste inachevé (≠ validation visuelle F5) :

- `sprints/meta/sprint_integration_godot/00_etat.md` — Tranche 7 (packaging) : partie VM
  faite, reste le gel Windows par Nico. Trois cases à valider avant clôture du sprint.
- `sprints/meta/sprint_vue_rattrapage/00_etat.md` — tronçon « 04 — Packaging (tranche 7) »
  marqué « ⬜ (VM faite) », mention « EN COURS (2026-06-16) » (étage 1 gel PyInstaller +
  étage 2). **Ces deux entrées désignent le même chantier** : le packaging.

Sprints dont il ne reste que la **validation visuelle F5 par Nico** (tronçons clos côté
moteur) : `sprint_perf_run_eternel`, `sprint_voix_narratives_ui`, `sprint_perf_tick_on2`,
et tous les autres hors `_clos/` (mycélium, allélopathie, floraison…).

## Dette d'automate

**D79 — Système de quêtes complet** — suite logique de D78 (✅ FAIT). Reste l'habillage
ludique : sources diégétiques, objectifs à condition d'ÉTAT, panneau de quêtes Godot, voix
narratives des donneurs. Priorité 🟡. **Dépendance levée** (D78 terminé). Périmètre en
tronçons : absent.

**D81 — Correctifs F5 du panneau automate** — (a) objectif démo codé en dur sur `tomate`,
qui meurt tôt, donc l'onglet reste bloqué `0/5` ; fix = cible robuste du monde de démo.
(b) vérifier le binding Maj+A. Priorité 🟢. Aucune dépendance. Périmètre : absent.

**D87 — Automate dirigé par le but (planification des prérequis)** — extension majeure de
D78/④ : planification à rebours / moyens-fins au-dessus du cœur réactif Liebig,
déterministe. Reste à concevoir : représentation de la chaîne de prérequis, articulation
avec Liebig, prérequis manquants. Priorité 🟡 (gros). **Dépendances D84 et D86 levées**
(RÉSOLU 2026-07-18) ; couplé à D79, ouverte. Périmètre : absent.

→ Lecture de Claude (jugement, hors périmètre DeepSeek) : **D87 est la plus mûre pour un
`/conception`** — dépendances dures levées, périmètre décrit, explicitement étiqueté « gros
morceau `/conception` ». D79 est mûre mais **subordonnée** (une quête = un objectif + sa
chaîne, donc D87 la précède). D81 n'est pas un sujet de conception : correctif C# de vue.

## Réserves (ce que la revérification a corrigé)

- `ask-deepseek` a signalé trois sprints à tronçon non terminé (run_eternel,
  voix_narratives_ui, tick_on2) avec un **doublon** (run_eternel cité deux fois) et a
  **manqué les deux seules entrées réellement inachevées** : le packaging
  (`sprint_integration_godot`, `sprint_vue_rattrapage`).
- Sa conclusion « aucun autre sprint avec tronçon non terminé » est **fausse**.
- La rubrique INDÉTERMINÉ, explicitement demandée, n'a pas été produite.
- Sur D87, il n'a pas relevé que D86 porte encore « Reste F5 : confirmer visuellement que
  le pommier noue au printemps » — dépendance levée sur le papier, non confirmée en jeu.
- En revanche **toutes ses citations sont exactes au mot près** (vérifiées sur
  `DETTE.md:88,90,96` et les trois `00_etat.md`) : il lit réellement, il ne brode pas.
  Son mode de défaillance est le **rappel partiel**, pas l'invention.
