# 2026-07-22 — Sprint RANGEMENT DOCUMENTAIRE — CLOS (`/sprint-auto`, ①→⑥)

**Objectif** : rendre la doc navigable **par le titre**. `docs/` et `sprints/`
rangés en `type de feature / thème de feature`, taxonomie dérivée des titres
réels des 56 `CONCEPTION_*.md`. Puis graver le protocole de délégation DeepSeek.

**Ampleur** : gros (≈500 fichiers touchés, aucun comportement modifié).
**Golden `57c166d8d3626444e0fc9b88b360edc62c047927f7608c45fefae35a6bba08da`
INTACT sur les 6 tronçons — zéro re-figeage**, ce qui est l'invariant du sprint :
aucune ligne de code n'a été écrite, seuls des commentaires ont été réécrits 1:1.

## Décisions structurantes (Nico, en amont — ne pas ré-ouvrir)

1. **Taxonomie à 8 types**, et non les 4 du brief initial qui laissaient ~25 docs
   orphelins : `meta · champs · vegetal · faune · joueur · narration · rendu ·
   perf`. Niveau 2 = thème (33 thèmes).
2. **Pivots modulés** — `BACKLOG.md` est **éclaté physiquement** par thème, mais
   `journal/` (126 entrées datées) et `DETTE.md` (table des `Dxx`) restent
   **canoniques** : chaque thème reçoit un fichier de **renvois** (liens), pas un
   fragment. Motif : la valeur du journal est sa **chronologie** et celle de la
   dette la **stabilité des identifiants `Dxx`** (cités jusque dans le code) —
   les démembrer coûte plus qu'il ne rapporte.
3. **`CLAUDE.md` reste à la racine** : c'est le fichier d'instructions auto-chargé
   par Claude Code, pas un document de philosophie. Jamais déplacé.
4. **Les 126 entrées de `journal/` ne sont PAS réécrites** — ce sont des comptes
   rendus historiques, fidèles à l'état du dépôt **à leur date**. C'est
   `docs/ARBORESCENCE.md` qui porte la table « ancien chemin → nouveau » et sert
   de **clé de lecture** de tout l'historique. Seuls les fichiers **vivants** ont
   été réécrits.

## Tronçons

**① Arborescence + carte** (`6043bb1`) — 41 dossiers créés (8 types × thèmes),
chacun ancré par un `README.md` d'une ligne (git ne suit pas les dossiers vides).
`docs/ARBORESCENCE.md` grave le principe de rangement, ce qui **ne bouge pas** et
pourquoi, la carte type → thème → documents, la table complète « ancien → nouveau »
(56 conceptions + 14 autres sources) et la règle de rangement d'un doc neuf.
Rien n'est déplacé à ce stade — la carte d'abord, le déménagement ensuite.

**② 70 `git mv`** (`bf8d4c4`) — application de la table §5 ligne à ligne, jamais
par boucle automatique : 56 `CONCEPTION_X.md` → `conception_x.md` dans leur
type/thème, plus `maitrise/` (3), `desktop/` (4), `amorce/` (5, briefs en
capitales normalisés) et 2 études rapatriées de `sprints/`. `docs/conception/`,
`docs/desktop/` et `docs/amorce/` disparaissent. **`git status` = 70 `R` exactement,
aucun `D`+`A` isolé** → historique git intégralement préservé. La table §5 s'est
révélée exacte : zéro écart de mapping.

**③ Pivots backlog / journal / dette** (`ed889bf`) — `BACKLOG.md` éclaté
**verbatim** en 28 fragments `backlog_<theme>.md` (+ archives Sprint 0→4 et longue
traîne dans `meta/backlog_historique.md`, + 2 sections « Pistes »), zéro perte
vérifiée par diff contre `git show HEAD:BACKLOG.md` ; `BACKLOG.md` devient un index
de pointeurs et conserve la table des kickoffs de dette dormante. 27
`journal_<theme>.md` (liens seuls ; 3 thèmes sautés faute de matière) et 19
`dette_<theme>.md` couvrant les 53 dettes ouvertes, **chaque `Dxx` dans exactement
un thème**. `DETTE.md` gagne une colonne `Thème` (88 lignes, compte inchangé).

**④ Extraction + réparation des liens vivants** (`7f1f464`) — le tronçon à risque.
Extraction du thème enchâssé « éclairement Z7 » vers
`docs/champs/lumiere/conception_eclairement.md` (verbatim, diff vérifié), pointeurs
laissés à l'emplacement d'origine. **406 fichiers réécrits** par un script piloté
par la seule table §5 (aucun mapping inventé) : chemins longs, liens Markdown
relatifs recalculés, mentions nues. **Zéro ligne de code touchée** — le diff
`.py`/`.cs` est en commentaires seuls (80 fichiers, +100/−99). Les deux `SKILL.md`
qui codaient `docs/conception/` **en dur** sont dépiégés (les oublier aurait cassé
`/audit-projet` et `/conception` **silencieusement**) ; `/conception` reçoit en
prime la règle de choix du thème et l'interdiction de recréer `docs/conception/`
à plat. 8 liens Markdown morts réparés, dont **5 l'étaient depuis juin** ; il n'en
reste aucun. Un avertissement en tête de `journal.md` renvoie vers la table.

**⑤ Taxonomie appliquée à `sprints/`** (`a6237ec`) — 42 `git mv` (36 dossiers de
sprint + 6 kickoffs à plat) vers `sprints/<type>/<theme>/`, **mêmes 8 types et
thèmes que `docs/`** ; `_clos/`, `dette_kickoffs/` et `sprint_rangement_doc/`
restent à plat. 71 fichiers de pointeurs réécrits (frontière de mot pour ne pas
confondre `sprint_voix_narratives` et `sprint_voix_narratives_ui`). **Risque de
résolution traité** : `/sprint-auto` résout désormais un nom nu par `find`
(0 ambiguïté vérifiée) et `/conception` crée sous `<type>/<theme>/` ; `CLAUDE.md`
et `BACKLOG.md` énoncent la convention. Zéro perte : 340 fichiers avant/après,
`git status` = 205 `R` + 7 `RM` + 69 `M`, aucun `D` ni `A` ; les 20 `.py` touchés
vérifiés **par `tokenize`** (rien hors commentaire/docstring).

**⑥ Protocole DeepSeek** (`2a19498`) — `docs/meta/agent/deepseek_protocol.md`
(253 l.) : sécurité de la clé **en premier**, outils et signatures réelles,
règle de partage **par nature de tâche** (repérage factuel → `ask-deepseek` /
jugement → Claude, jamais par skill), les deux garde-fous (pipeline en deux temps,
revérification `grep` de tout ce qui se grave — une réponse DeepSeek n'est ni
reproductible ni traçable, or le projet est déterministe par principe), les cas
`/conception` et `/sprint-auto`, les 4 adaptations Symbiose. Pointeur de 9 lignes
en tête de `CLAUDE.md`.

### Cadre `/sprint-auto` (arbitrage à retenir)

Bien plus restrictif que `/conception`, pour une raison **structurelle** :
`/conception` **cherche** (corpus large, on ignore où ça vit) tandis que
`/sprint-auto` **modifie** (fichiers déjà désignés par le kickoff, et il faut le
**texte exact** pour éditer — un résumé est inutilisable pour un `Edit`).
✅ cartographie d'**impact imprévue**, vérification Python ↔ C# au tronçon vue.
❌ lire le code que le tronçon va modifier, **générer du code moteur** (le golden
est un hash : du code non relu ligne à ligne qui doit préserver un hash exact est
précisément le scénario qui le casse), diagnostiquer un golden qui a bougé.
**Capteur** : un sous-agent qui a besoin de fouiller révèle un **kickoff incomplet**
— au même titre que la taille d'un fichier révèle une dette de refactor.

## Constats consignés

- **`extract-chat` est de fait inutilisé sur Symbiose** : il ne lit que des
  transcripts Claude Code `.jsonl`, soit exactement la source **interdite** (la
  clé DeepSeek a fuité dans un transcript le 2026-07-22). Le jeu ne produit rien
  dans ce format.
- Le correctif « `export` » de `~/.config/deepseek.env` est **hors dépôt**, valeur
  jamais affichée ; aucun secret dans le dépôt (scan vérifié).
- 4 documents **non encore créés** mais cités par les kickoffs de dette dormante
  ont reçu un chemin cible : `conception_{magazine,carnet,pages_secretes}` →
  `docs/narration/voix/`, `conception_terrain` → `docs/joueur/maitrise/`.
- Repéré hors périmètre : `data/code/sprints/sprint_modele_spatial/` est un
  **dossier vide non suivi par git** — laissé tel quel (règle « ne rien supprimer »).

**Refactor auto-léger : no-op** — le sprint n'a ajouté aucune ligne de code et
aucun fichier touché ne dépasse 400 LDC pur (max : `test_faune_dediee.py` 383).

**Golden final `57c166d8…`.** Aucune validation F5 requise : sprint documentaire
de bout en bout, `dotnet build` vert au tronçon ④.
