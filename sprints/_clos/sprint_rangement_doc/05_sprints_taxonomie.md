# ⑤ Taxonomie appliquée à `sprints/`

**Préalable** : lire `00_etat.md` et la taxonomie de `01_structure_carte.md`
(les 8 types et leurs thèmes sont les mêmes — ne pas en inventer de nouveaux).

## Arbitrage de ce tronçon

`sprints/` contient **335 fichiers** dans ~60 dossiers, dont une grosse majorité
sous `sprints/_clos/`. Traitement **asymétrique**, par cohérence avec la
décision 4 de `00_etat.md` (les archives ne se réécrivent pas) :

| Catégorie | Traitement |
|---|---|
| `sprints/_clos/**` | **inchangé** — ce sont des archives closes, leur valeur est historique. On n'y touche pas. |
| Sprints **actifs / non clos** | rangés en `sprints/<type>/<theme>/<nom_sprint>/` |
| `sprints/dette_kickoffs/**` | **inchangé** — indexé par `00_index.md`, cohérent en soi, adossé aux `Dxx` |
| `sprints/_clos/sprint_rangement_doc/` | **inchangé** (c'est ce sprint-ci) |

Motif : ranger 200 fichiers d'archives par thème coûte cher, casse les liens des
entrées de journal qui les citent, et n'aide personne — on ne cherche jamais un
sprint clos par thème, on le cherche par date via le journal.

## Règle de mapping

Un dossier de sprint hérite du thème de **sa conception homonyme**, telle que
tranchée dans la table de `01_structure_carte.md`. Exemples :

| Sprint actif | Destination |
|---|---|
| `sprint_allelopathie/` | `sprints/vegetal/allelopathie/` |
| `sprint_hydrologie_marecage/` | `sprints/champs/eau/` |
| `sprint_mycelium_interconnexions/` | `sprints/faune/mycelium/` |
| `sprint_perf_lod_ombre/` | `sprints/perf/lod/` |
| `sprint_voix_narratives_ui/` | `sprints/narration/voix/` |
| `sprint_integration_godot/` | `sprints/meta/` (transverse — pont + packaging) |
| `sprint_1..4_*.md`, `sprint_pommier_nouaison.md`… | `sprints/meta/` si transverse, sinon leur thème |

**Cas transverses → `sprints/meta/`** : tout sprint qui ne relève pas d'un thème
unique (intégration Godot, refactor, rangement, vue de rattrapage).

Établir la liste exacte des sprints **actifs** avant de bouger :
`ls -d sprints/*/ | grep -v '_clos\|dette_kickoffs\|sprint_rangement_doc'`.
En cas de doute sur un sprint sans conception homonyme, lire son `00_etat.md` —
son objectif donne le thème. Consigner tout arbitrage dans `00_etat.md`.

## Contraintes

- **`git mv` du dossier entier**, pas fichier par fichier.
- **Ne rien renommer à l'intérieur** — les `0N_*.md` gardent leur nom et leur
  numérotation (c'est l'ordre d'exécution de `/sprint-auto`).
- Le nom du dossier de sprint est **conservé** (`sprint_allelopathie/` reste
  `sprint_allelopathie/`, il est juste rangé sous son thème). Le chemin porte le
  thème, le nom porte l'identité.

## Répercussions

- `BACKLOG.md` cite des chemins de sprints (« kickoffs autosuffisants de
  `sprints/` ») → mettre à jour.
- `CLAUDE.md` §Backlog actif cite `sprints/sprint_integration_godot/00_etat.md`
  → mettre à jour.
- `.claude/skills/sprint-auto/SKILL.md` et `.claude/skills/conception/SKILL.md`
  prennent un **dossier de sprint** en argument → vérifier qu'ils tolèrent un
  chemin à deux niveaux (`vegetal/allelopathie`) et pas seulement un nom plat.
  **C'est le risque de régression principal du tronçon.**

## Vérification

- `ls sprints/` ne montre plus de `sprint_*` à plat (hors `_clos`,
  `dette_kickoffs`, `sprint_rangement_doc`).
- `git status` : uniquement des `R`.
- Lancer `/sprint-auto` **à blanc** sur un sprint déplacé (lecture du `00_etat.md`
  seule, sans exécution) pour confirmer que le chemin à deux niveaux passe.
- `cd data/code && python3 -m tests.test_golden` → **inchangé**.

## Commit

`docs(rangement) ⑤ : sprints actifs rangés par thème, archives _clos intactes`

Puis cocher ⑤ dans `00_etat.md`.
