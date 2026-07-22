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

- [x] ① Structure + `ARBORESCENCE.md` (carte du mapping) — 2026-07-22
- [x] ② `git mv` des 56 conceptions + études + meta — 2026-07-22
- [x] ③ Backlog éclaté + renvois journal/dette par thème — 2026-07-22
- [x] ④ Extractions enchâssées + réparation des liens vivants — 2026-07-22
- [x] ⑤ Taxonomie appliquée à `sprints/` — 2026-07-22
- [x] ⑥ `docs/meta/agent/deepseek_protocol.md` + pointeur `CLAUDE.md` — 2026-07-22

## REPRISE

**SPRINT TERMINÉ** (⑥ fait le 2026-07-22 — les 6 tronçons sont clos). Rien à
reprendre : la suite est un `git commit` puis, hors de ce sprint, la clôture
habituelle (journal + `BACKLOG.md`).

**Tronçon ⑥ fait** (golden **INCHANGÉ**, hash `57c166d8d362…` ; **aucun fichier
C# touché** → `dotnet build` non concerné). Livré :

- **`docs/meta/agent/deepseek_protocol.md`** (253 l.) — et non `docs/agent/…`
  comme l'écrivait le titre de la case ci-dessus : la taxonomie du ① range ce
  document sous le type `meta/`, thème `agent/` (le corps du kickoff citait déjà
  le bon chemin). §4 de `docs/ARBORESCENCE.md` et `README.md` du dossier mis à
  jour en conséquence.
- **Les 4 adaptations obligatoires** y sont écrites en toutes lettres : tests
  moteur ≠ boilerplate (§6.1), suspension **par nature de tâche** avec les cas
  `/conception` et `/sprint-auto` (§3-§5), interdiction `extract-chat` sur
  `~/.claude/projects/` (§6.2), français forcé dans les `--spec` (§6.3).
  S'y ajoute un **§1 Sécurité** en tête (incident de fuite du 2026-07-22) :
  ne jamais afficher ni copier la clé, aucun secret dans le dépôt, pas de
  `.bak` qui traîne.
- **Pointeur `CLAUDE.md`** : section « Délégation DeepSeek » de **9 lignes**,
  placée juste après l'en-tête (avant « Source de vérité »).
- **Test de bout en bout OK** du premier coup après correctif :
  `ask-deepseek --paths CLAUDE.md` a répondu en français correct.
- **Correctif hors dépôt** (nécessaire, sinon l'outil est inutilisable) :
  `~/.config/deepseek.env` ne contenait **pas** le mot-clé `export` —
  ajouté par `sed` **sans jamais afficher la valeur**, mode `600` reconfirmé,
  copie de sauvegarde supprimée dans la foulée.
- Point hérité corrigé : `06_protocole_deepseek.md` l.111 cite désormais
  `docs/champs/eau/dette_eau.md` (le fichier qui existe vraiment).

**Décision imprévue à connaître** : `extract-chat` ne sait lire qu'un
**transcript Claude Code `.jsonl`** — c'est-à-dire exactement la source que
l'adaptation 3 interdit. Le jeu ne produit rien dans ce format ; l'outil est
donc **de fait inutilisé sur Symbiose**, ce qui est écrit tel quel au §6.2
plutôt que de laisser croire à un usage courant.

**Tronçon ⑤ fait** (golden **INCHANGÉ**, hash `57c166d8d362…` ; **aucun fichier
C# touché** → `dotnet build` non concerné). Livré, en suivant
`05_sprints_taxonomie.md` :

- **42 `git mv`** (36 dossiers de sprint + 6 kickoffs `.md` à plat) →
  `sprints/<type>/<theme>/<nom_du_sprint>/`, **mêmes 8 types et mêmes thèmes**
  que `docs/`. Rien renommé à l'intérieur, numérotation `0N_*.md` intacte.
  `git status` : **212 lignes `R`**, aucun `D`+`A` — l'historique git suit.
  Comptage `find sprints -type f` : **340 avant, 340 après** (zéro perte).
- **Restent à plat, comme prévu** : `sprints/_clos/` (archives),
  `sprints/dette_kickoffs/` (index adossé aux `Dxx`) et
  `sprints/_clos/sprint_rangement_doc/` (ce sprint-ci) → **le chemin de CE fichier
  n'a pas changé**.
- **71 fichiers réécrits** (pointeurs `sprints/<nom>` → nouveau chemin), pilotés
  par la table de déplacement (pas de mapping inventé), avec frontière de mot
  pour ne pas confondre `sprint_voix_narratives` et `…_ui`. Dont **20 `.py`** :
  vérifié par `tokenize` que **zéro ligne hors commentaire/docstring** n'a bougé,
  `compileall` OK. **0 `.cs`**. `journal/`, `journal_archive/` et
  `sprints/_clos/sprint_rangement_doc/` volontairement **non réécrits** (décision 4 +
  ce dossier décrit l'ancien état).
- **`docs/ARBORESCENCE.md` §7 (neuf)** : carte des sprints, motif du traitement
  asymétrique, **table de traduction ancien → nouveau des 42 entrées** (§7.1,
  clé de lecture du journal) et **arbitrages de rattachement** (§7.2). En-tête
  « État » passé au ⑤.
- **Risque de régression principal traité** — les deux skills :
  `/sprint-auto` §0 sait désormais **résoudre un nom nu** en chemin
  (`find sprints -maxdepth 4 -type d -name '<nom>'`, ambiguïté → demander ;
  vérifié : **0 nom ambigu** aujourd'hui) et `<sprint>` y désigne le chemin
  résolu ; `/conception` crée son ossature sous
  `sprints/<type>/<theme>/sprint_<nom>/` — **interdiction explicite** de recréer
  du plat, symétrique de ce que le ④ a fait pour `docs/`.
- `CLAUDE.md` (§Arbo cible, §structure de sprint, §ouverture de session) et
  `BACKLOG.md` (intro) disent la nouvelle convention, pas seulement les
  nouveaux chemins.
- **Liens morts** : 1 lien relatif cassé par le déplacement, réparé
  (`sprints/champs/climat/sprint_vent_evapotranspiration/00_etat.md`, `../../`
  → `../../../../`). Il restait 5 « faux positifs » du scanner, **tous
  pré-existants** : 4 placeholders de prose (`…X.md`, `journal/<fichier>`,
  `...`) et 1 lien du kickoff `04_extractions_liens.md` — laissés tels quels,
  hors périmètre ⑤.

**Arbitrages de design pris dans le tronçon** (consignés en `ARBORESCENCE.md`
§7.2, à confirmer par Nico d'un mot) : trois sprints sans conception homonyme —
`sprint_perf_tick_on2` → `perf/scatter` (son propre `00_etat.md` le rattache à
`conception_perf_scatter_recue.md`) ; `sprint_senescence_rosee.md` →
`vegetal/sante` (c'est une **cause de mort**, pas un sujet d'eau) ;
`sprint_pommier_nouaison.md` → `vegetal/floraison`. Et **`sprint_vue_rattrapage`
→ `meta/`** comme `sprint_integration_godot`, au titre des transverses.

**Suivant : tronçon ⑥ (`06_protocole_deepseek.md`)** — `docs/meta/agent/
deepseek_protocol.md` + pointeur depuis `CLAUDE.md`. Point hérité à corriger au
passage (déjà signalé au ④) : `06_protocole_deepseek.md` l.111 cite en exemple
`docs/champs/eau/dette_hydrologie.md`, alors que le fichier réellement produit au
③ s'appelle `docs/champs/eau/dette_eau.md`.

**Tronçon ④ fait** (golden **INCHANGÉ**, hash `57c166d8d362…` ; `dotnet build
Symbiose.csproj` **VERT**, 0 avertissement / 0 erreur — un seul commentaire C#
touché, `world/SolTexture.cs`). Livré, en suivant `04_extractions_liens.md`
A/B/C :

- **A — extraction du thème enchâssé « éclairement (Z7) »** → nouveau
  `docs/champs/lumiere/conception_eclairement.md` (101 l.) : §1 = la conception
  reprise **verbatim** de `docs/meta/vision.md` (vérifié par `diff` contre
  `git show HEAD:`), §2 = la liste de clôture reprise **verbatim** de
  `docs/meta/backlog_historique.md`. Les **deux** emplacements d'origine gardent
  un **pointeur** (zéro perte). **Autres candidats examinés et NON extraits**
  (sections de docs de synthèse qui ont déjà leur doc de thème ailleurs — les
  démembrer les viderait) : `vision.md` § Vigueur / Paliers de maîtrise / Trois
  voix / Auxiliaires / Maison normande / Extension du terrain / Aléas météo ;
  `architecture.md` § Sol vivant Python v4 / Échelle spatiale. Liste consignée
  en clair dans `docs/ARBORESCENCE.md` **§5.3** (neuf).
- **B — liens réparés** : **405 fichiers** réécrits (dont **75** `data/code/*.py`
  et **5** C#), pilotés par un script dérivé de la table §5 de `ARBORESCENCE.md`
  (donc pas de mapping inventé). Trois formes traitées : chemin long
  `docs/conception/CONCEPTION_X.md` → nouveau chemin ; lien Markdown relatif
  `[`X.md`](…X.md)` → cible **recalculée** depuis le dossier du fichier ;
  mention nue `CONCEPTION_X.md` → chemin complet racine-relatif. **Zéro ligne de
  code touchée** (vérifié : tout le diff `.py`/`.cs` est en commentaire /
  docstring), `compileall` OK.
- **⚠️ les deux skills** (le point critique du tronçon) : `/conception` et
  `/audit-projet` ne codent plus `docs/conception/` en dur. `/conception` reçoit
  en §3.1 une **règle de choix du thème** explicite (8 types fermés, thème
  ouvert + `README.md` d'une ligne + **mise à jour obligatoire du §4 de
  `ARBORESCENCE.md`**, `snake_case` sans accents, préfixe `conception_`/`etude_`)
  et l'interdiction de recréer un `docs/conception/` à plat. `/audit-projet`
  balaie désormais `find docs -name 'conception_*.md'` + les fragments
  `docs/**/backlog_<theme>.md`.
- **C — note en tête de `journal.md`** : les entrées d'avant le 2026-07-22 citent
  les anciens chemins et ne sont **pas** réécrites → renvoi vers
  `docs/ARBORESCENCE.md` §5.
- **En-tête « État » de `docs/ARBORESCENCE.md` corrigé** (le point hérité du ②) :
  il décrivait encore les déplacements comme à venir.
- **Chasse aux liens morts** : **0** lien Markdown mort dans les fichiers vivants
  (script de contrôle du kickoff, étendu à tout le dépôt hors archives). Au
  passage, 8 liens **déjà morts avant ce sprint** réparés : les 3 sous-docs de
  `conception_maitrise.md` (désormais dans le même dossier) et 5 renvois de
  sprints clos vers `data/code/CONCEPTION_{METEO,VIGUEUR}.md` (morts depuis le
  refactor du 2026-06-15).

**Décision de périmètre prise dans le tronçon** (à connaître pour le ⑤) : le
critère de réécriture n'est pas « vivant vs archive » mais **« pointeur vs
récit »**. Un *pointeur* vers un document (même dans un sprint clos) est réparé
— il désigne le même doc, qui a juste déménagé. Un *récit* d'une migration
passée est laissé intact, comme le journal. Restent donc volontairement en
`docs/conception/` : `journal/` + `journal_archive/` (décision 4), la table de
traduction `docs/ARBORESCENCE.md` §5 (c'est son objet), `sprints/_clos/sprint_rangement_doc/`
(décrit ce sprint-ci) et `sprints/_clos/sprint_refactor_global/` (raconte la
**création** de `docs/conception/` en 2026-06-15). **Aucune autre occurrence
vivante** — vérifié par `grep -rIn` sur tout le dépôt, toutes extensions.

**Décision de design imprévue, à valider par Nico** : 4 documents **qui
n'existent pas encore** étaient cités en `docs/conception/CONCEPTION_*.md` par
les kickoffs de dette dormante. Il fallait leur donner un chemin cible, sinon le
skill les recrée à plat. Rattachement retenu (déductible de la taxonomie, mais
non tranché avant) : `CONCEPTION_MAGAZINE` / `CONCEPTION_CARNET` /
`CONCEPTION_PAGES_SECRETES` → `docs/narration/voix/` (ce sont 3 des 4 voix) ;
`CONCEPTION_TERRAIN` (extension du terrain **par maîtrise**) →
`docs/joueur/maitrise/`. Deux noms de docs purement hypothétiques
(`CONCEPTION_PHYSICOCHIMIE_SOL.md`, `CONCEPTION_DEBLOCAGE.md`, jamais créés sous
ce nom) ont été **laissés tels quels** : ils ne pointent sur rien.

**Signalé au ⑥** : `06_protocole_deepseek.md` l.111 cite en exemple
`docs/champs/eau/dette_hydrologie.md` — le fichier réellement produit au ③
s'appelle `docs/champs/eau/dette_eau.md`. Simple exemple en prose, à corriger
au passage.

**Suivant : tronçon ⑤ (`05_sprints_taxonomie.md`)** — taxonomie appliquée à
`sprints/` (traitement asymétrique : `_clos/`, `dette_kickoffs/` et
`sprint_rangement_doc/` **ne bougent pas** ; seuls les sprints actifs sont
rangés en `sprints/<type>/<theme>/`). Attention : le ④ a modifié le **contenu**
de nombreux fichiers sous `sprints/` (réparation de pointeurs) — cela n'entre
pas en conflit avec le ⑤, qui déplace des **dossiers** au `git mv`.

**Tronçon ③ fait** (golden **inchangé**, hash `57c166d8d362…` — aucun code
touché, aucun C# concerné). Livré, en suivant `03_pivots.md` A/B/C :

- **A — `BACKLOG.md` éclaté** : les 61 lignes du tableau principal réparties
  **verbatim** en **28 fragments** `docs/<type>/<theme>/backlog_<theme>.md` ;
  les sections historiques (Sprint 0 → Sprint 4) dans
  `docs/meta/backlog_historique.md` (+ les 7 « idées longue traîne » de fin de
  fichier, sans thème clair, sous leur propre titre) ; les deux sections
  « Pistes » vers `docs/champs/sol/backlog_generation_terrain.md` et
  `docs/rendu/pixelart/backlog_pixelart.md`. `BACKLOG.md` devient un **index de
  pointeurs** (intro + sprint en cours + table thème→fragment) et **garde** la
  table des kickoffs de dette dormante, qui est déjà un index.
  **Zéro perte vérifiée par diff** contre `git show HEAD:BACKLOG.md` : seules
  les 3 lignes de l'ancienne intro (« source unique », devenue fausse) ne se
  retrouvent pas telles quelles.
- **B — renvois journal** : **27** `journal_<theme>.md`, liens seuls vers les
  126 entrées de `journal/` + `journal_archive/` (titres lus dans les fichiers).
  Une entrée peut figurer dans plusieurs thèmes (11 le font). **Sautés faute de
  matière** (1 seule entrée, garde-fou de prolifération) : `rendu/pixelart`,
  `faune/mycelium`, `perf/scatter`.
- **C — dette** : colonne **`Thème`** ajoutée aux **88** lignes de `DETTE.md`
  (`grep -c '^| D'` inchangé avant/après) ; **19** `dette_<theme>.md` couvrant
  les **53 dettes ouvertes**, chacune dans **exactement un** fichier (vérifié)
  avec libellé court + lien — aucune description recopiée.
- `docs/ARBORESCENCE.md` §4 : **une note de convention** ajoutée (les trois
  fichiers de service d'un thème ne sont pas énumérés thème par thème).

**Décisions prises dans le tronçon** (pas d'arbitrage rouvert) : un thème =
**un** thème par ligne de backlog et par `Dxx` (pas de multi-rattachement, pour
que « chaque `Dxx` ouvert apparaisse dans exactement un fichier ») ; les renvois
journal, eux, sont multi-thèmes puisque la vérification ne l'interdit pas.

**Tronçon ② fait** (golden **inchangé**, hash `57c166d8d362…` — aucun code
touché, aucun C# concerné). Livré :

- **70 `git mv`** suivant `docs/ARBORESCENCE.md` §5 ligne à ligne : 56
  conceptions + 3 `maitrise/` + 4 `desktop/` + 5 `amorce/` + 2 études venues de
  `sprints/`. **Zéro écart de mapping** — la table §5 était exacte, aucune
  cible manquante, aucun doublon.
- `git status` : **70 lignes `R` et rien d'autre** — aucun `D`+`A` isolé, donc
  l'historique git est bien suivi sur les 70 fichiers.
- Comptage : `docs/**/*.md` passe de **110 à 112** (+2 = les deux études
  rapatriées de `sprints/`), `find docs -name 'conception_*.md'` = **56**.
- `docs/conception/`, `docs/desktop/` et `docs/amorce/` **n'existent plus**
  (vidés par les `git mv`, puis `rmdir` — git ne versionne pas les dossiers).
- Renommage appliqué : `CONCEPTION_X.md` → `conception_x.md`, et les deux
  `BRIEF_*.md` en capitales → `brief_champs_conception.md` /
  `brief_claude_web.md`. Les `maitrise/0N_*.md` gardent leur numérotation.

**Point laissé au ④ (pas un oubli, une limite de périmètre)** : l'en-tête
« **État** » de `docs/ARBORESCENCE.md` (lignes 8-10) dit encore que « les
déplacements ont lieu au tronçon ② » et que « la colonne ancien chemin décrit
encore la réalité du dépôt ». C'est désormais faux. Le ② interdisant toute
édition de contenu, la phrase est laissée telle quelle : **à corriger au ④**,
en même temps que les liens vivants.

**Suivant : tronçon ④ (`04_*.md`)** — extractions enchâssées + réparation des
liens vivants. Deux points hérités à traiter là, en plus de son propre
périmètre :

1. L'en-tête « **État** » de `docs/ARBORESCENCE.md` (lignes 8-10) dit encore que
   « les déplacements ont lieu au tronçon ② » — **faux depuis le ②**.
2. Les liens vivants vers `docs/conception/…` restent cassés (451 occurrences au
   relevé initial) ; s'y ajoutent désormais les **fragments de backlog**, qui
   citent verbatim d'anciens chemins `docs/conception/CONCEPTION_*.md` — ils
   sont du contenu **vivant** (pas des archives de journal) et entrent donc dans
   le périmètre de réparation du ④.
