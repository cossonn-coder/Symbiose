# Sprint RANGEMENT DOCUMENTAIRE — état partagé

**Ouvert** : 2026-07-22 · **Origine** : brief amont « Réorganisation documentaire
+ protocole DeepSeek » · **Ampleur** : gros (≈500 fichiers) → 6 tronçons.

## Objectif

Rendre la doc navigable **par le titre** : `docs/` et `sprints/` rangés en
`type de feature / thème de feature`, dérivés des titres réels des 56
`CONCEPTION_*.md`. Puis graver le protocole de délégation DeepSeek.

## Décisions actées par Nico (2026-07-22) — ne pas ré-ouvrir

1. **Taxonomie à 8 types** (et non les 4 du brief, qui laissaient ~25 docs
   orphelins) : `meta · champs · vegetal · faune · joueur · narration · rendu ·
   perf`. Niveau 2 = thème. Mapping complet des 56 docs : voir `01_*.md`.
2. **Pivots modulés** : `BACKLOG.md` **éclaté physiquement** par thème.
   `journal/` (126 entrées datées) et `DETTE.md` (table des IDs `Dxx`) restent
   **canoniques** — chaque thème reçoit un fichier de **renvois** (liens), pas
   un fragment. Motif : la chrono du journal et la stabilité des `Dxx` (cités
   dans le code) sont la valeur ; les démembrer coûte plus qu'il ne rapporte.
3. **`CLAUDE.md` reste à la racine** — c'est le fichier d'instructions
   auto-chargé par Claude Code, pas un doc de philosophie. Jamais déplacé.
4. **Les 126 entrées de `journal/` ne sont PAS réécrites** — ce sont des
   comptes rendus historiques, fidèles à l'état du dépôt à leur date.
   `docs/ARBORESCENCE.md` porte la table « ancien chemin → nouveau » qui sert
   de clé de lecture pour tout l'historique. Seuls les fichiers **vivants**
   sont réécrits (cf. tronçon ④).

## Contraintes non négociables

- **`git mv` systématique** — l'historique git est préservé.
- **Zéro perte** : toute extraction laisse un pointeur à l'emplacement d'origine.
- **Le golden ne doit PAS bouger** (aucun code touché ; seul un commentaire de
  `world/SolTexture.cs` est concerné). Vérif à chaque tronçon :
  `cd data/code && python3 -m tests.test_golden`.
- **Français + accents** dans tout contenu ; noms de fichiers en `snake_case`
  sans accents.
- Ne rien **figer** qui ne l'était pas : conserver les mentions « FIGÉ » /
  « AMORCE » telles quelles.

## Périmètre découvert (mesuré le 2026-07-22)

| Cible | Volume |
|---|---|
| `docs/conception/` | 56 fichiers, 13 954 lignes |
| `sprints/` | 335 fichiers, ~60 dossiers |
| `journal/` + `journal_archive/` | 126 entrées |
| Occurrences `docs/conception` | 451 |
| Occurrences `sprints/<nom>` | 267 |

**Consommateurs de chemins hors docs** (à réécrire, tronçon ④) : `CLAUDE.md`,
`BACKLOG.md`, `DETTE.md`, `journal.md`, `world/SolTexture.cs`,
`.claude/skills/audit-projet/SKILL.md`, `.claude/skills/conception/SKILL.md`.
⚠️ Les deux skills codent `docs/conception/` en dur — les oublier les casse
silencieusement.

## Outils DeepSeek — état

Installés (`~/.local/bin/{ask,write,extract}-deepseek` → `~/Nextcloud/projects/
aria/bin/`). Clé dans `~/.config/deepseek.env`. **Vérifier qu'elle contient bien
`export`** (sans lui, les sous-processus Python ne la voient pas) et sourcer
explicitement avant appel : `. ~/.config/deepseek.env`.

## Avancement

- [ ] ① Structure + `ARBORESCENCE.md` (carte du mapping)
- [ ] ② `git mv` des 56 conceptions + études + meta
- [ ] ③ Backlog éclaté + renvois journal/dette par thème
- [ ] ④ Extractions enchâssées + réparation des liens vivants
- [ ] ⑤ Taxonomie appliquée à `sprints/`
- [ ] ⑥ `docs/agent/deepseek_protocol.md` + pointeur `CLAUDE.md`

## REPRISE

Rien n'est commencé. Démarrer au tronçon ① (`01_structure_carte.md`).
