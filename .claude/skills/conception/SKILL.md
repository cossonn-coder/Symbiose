---
name: conception
description: >-
  Durcit une conception Symbiose EN CONVERSATION puis la fige en sprint prêt
  pour /sprint-auto. Part d'un doc de conception existant
  (docs/<type>/<theme>/conception_*.md) OU d'un sujet neuf à concevoir : challenge les hypothèses
  bio/éco, débusque les trous (effets oubliés, couplages non vus), vérifie la
  philo de design #1-#7, chiffre le coût perf, propose un découpage en tronçons
  perf-first préservant le golden, et remonte les arbitrages à Nico. Ne fige
  RIEN sans accord. Une fois figé : écrit les kickoffs autosuffisants
  (00_etat.md + 0N_*.md), commit, et donne le message exact pour /sprint-auto.
  Tient un état autosuffisant sur disque EN CONTINU (00_etat.md dès le 1er
  échange) → reprise à froid sans compact ni HANDOFF manuels, sans intervention
  de Nico. C'est le maillon AMONT de /sprint-auto (concevoir → figer), jamais
  l'exécution. Usage : /conception <doc ou sujet>  (ex. /conception CONCEPTION_VENT)
---

# /conception — durcir une conception puis la figer en sprint

Tu **conçois avec Nico**, tu n'exécutes pas. Ce skill couvre la phase amont du
workflow projet : **concevoir en conversation → durcir → figer en kickoffs
autosuffisants**. L'exécution des tronçons, elle, est le métier de
`/sprint-auto` (aval). Tu t'arrêtes là où `/sprint-auto` commence.

Règle cardinale du projet : **« concevoir en conversation d'abord, ne créer un
fichier que sur OK »**. Toute la phase A (challenge) est un **dialogue** ; tu
n'écris ni le **doc de conception final** ni les **kickoffs** avant la phase B,
**après l'accord explicite de Nico** sur la conception. La **seule** exception
est le **carnet de bord** `00_etat.md` (voir §0bis) — persister ce qui a déjà
été tranché n'est pas figer.

## 0bis. État autosuffisant EN CONTINU — autonomie contexte (fin du compact manuel)

Une conception longue fait gonfler le contexte. **Tu ne demandes JAMAIS à Nico
de lancer un `/compact` ni de « lire `HANDOFF.md` ».** À la place, **dès le
premier échange** tu tiens un **état vivant sur disque**, autosuffisant, mis à
jour à **CHAQUE décision arrêtée** : `sprints/<type>/<theme>/sprint_<nom>/00_etat.md`
(crée le dossier tôt, choisis un `<nom>` de sprint provisoire dès que le sujet est
cerné). `<type>/<theme>` = **le même couple** que celui choisi en §3.1 pour le doc
de conception — un sprint est rangé comme sa conception (cf. §7 de
`docs/ARBORESCENCE.md`). **Ne jamais recréer un `sprints/sprint_<nom>/` à plat.**

- Cet `00_etat.md` est le **handoff permanent** : phase courante, **décisions
  arrêtées** (une ligne + rationale courte chacune), **questions ouvertes /
  options en balance**, coût perf estimé, **§REPRISE** (quoi lire + prochaine
  étape précise). Il grandit avec le dialogue et sert de mémoire reconstructible.
- **Reprise à froid** (après auto-compaction ou `/clear`) : tu lis `CLAUDE.md` +
  ce `00_etat.md` et tu **continues sans perte, sans intervention de Nico**.
  L'auto-compaction du harness devient un simple **filet sans conséquence**
  (l'état vit sur disque). Ceci **remplace**, pour le travail de conception, le
  protocole `HANDOFF.md` générique du `CLAUDE.md` global : pas de HANDOFF, pas de
  message « contexte bas », pas d'attente d'une action de Nico.
- **Nuance** avec « ne créer un fichier que sur OK » : `00_etat.md` est un
  **carnet de bord** (il persiste ce qui a DÉJÀ été discuté/tranché), PAS
  l'artefact figé. Le doc `CONCEPTION_*.md` final et les kickoffs `0N` restent la
  **phase B**, après accord global. Écrire l'état en continu est la règle, pas
  une entorse.
- **Flux cible** (demande Nico) : `/conception <sujet>` → on tranche le design
  ensemble (l'`00_etat.md` enregistre au fil de l'eau) → **tu finis seul** la
  conception une fois les grands arbitrages faits → tu rédiges les kickoffs `0N`
  autosuffisants → prêt pour `/sprint-auto`.

## 0. Argument

`/conception <doc ou sujet>` :
- un nom de doc existant (`CONCEPTION_VENT`, ou le chemin
  `docs/champs/climat/conception_vent_evapotranspiration.md`) → tu pars de ce doc ;
- un **sujet neuf** (« rosée nocturne D38 », « zoochorie D42 ») → tu pars de la
  conversation et de la dette concernée, il n'y a pas encore de doc.

Si l'argument manque, déduis le sujet du contexte ; en cas de doute, **demande**.

## 1. Cadre — lis les invariants AVANT de challenger

Charge-toi le contexte qui rend ta critique pertinente (lecture seule) :

1. `CLAUDE.md` (racine) — **philo de design #1-#7** et garde-fous (taille
   fichiers, déterminisme, un fichier = une responsabilité, français, source de
   vérité Python).
2. Le doc de conception cible s'il existe
   (`docs/<type>/<theme>/conception_*.md` — carte : `docs/ARBORESCENCE.md`).
3. La **dette liée** (`DETTE.md`) et le **backlog** (`BACKLOG.md`) — couplages,
   dettes croisées, ce qui est déjà conçu/implémenté autour.
4. Les **conceptions voisines** qui partagent des champs/mécaniques (pour ne pas
   diverger ni dupliquer).
5. Au besoin, le code source de vérité (`data/code/`) pour vérifier ce qui
   existe RÉELLEMENT (un champ, une fonction, un gène) avant de t'appuyer dessus.

> **Délégation DeepSeek — c'est ici qu'elle rapporte le plus** (protocole
> `docs/meta/agent/deepseek_protocol.md`, **§4** — à lire avant le premier appel).
> Le corpus est large et on ignore *où* le sujet vit : l'**inventaire d'ouverture**
> (« quels docs/sprints touchent déjà ce sujet ? »), l'**anti-doublon** (« ce gène /
> ce champ / cet effet existe-t-il déjà ? » — l'incident `resilience_base` était
> exactement ça) et la **carte des couplages** (« qui lit ce champ ? ») passent par
> `ask-deepseek`. Les points 2 à 4 ci-dessus, eux, se lisent **en clair** : ce sont
> les documents que la conception va durcir, et un trou se voit dans l'interstice
> entre deux phrases, pas dans un résumé.
>
> Trois réflexes : **(a)** toute `--question` exige explicitement « en français,
> accents corrects » (§6.3) ; **(b)** tout ce qui va se **graver** (kickoff,
> `00_etat.md`, `DETTE.md`, `BACKLOG.md`) se revérifie au `grep` ou par lecture
> ciblée — le projet est déterministe, une réponse DeepSeek n'est pas reproductible ;
> **(c)** `ask-deepseek` **n'est pas exhaustif sur un gros corpus** (§7.1) : fais le
> balayage toi-même, ne lui délègue que la lecture des candidats.

## 2. Phase A — challenger (DIALOGUE, ne fige rien)

Passe la conception au crible sur ces axes. Sortie = une **critique structurée
à l'écran** + les **arbitrages** à remonter (pas une édition de fichier).

- **Hypothèses bio/éco** — réalisme écologique. Une hypothèse fausse ou
  simplifiée à l'excès se signale ici.
- **Trous** — effets oubliés, **couplages non vus**. Applique la règle
  d'**interconnexion des acteurs** (« tout coexiste » : plantes ↔ faune ↔
  champignons ↔ sol ↔ structures). Une mécanique neuve qui n'interagit avec rien
  est suspecte.
- **Philo de design #1-#7** — en particulier : jamais bonus/malus direct sur les
  plantes (#1/#2 : flux → contrainte écologique → réponse émergente),
  **déterminisme / zéro RNG vivant** (#3), run éternel (#4), indices visuels pas
  de chiffres en HUD (#5), sagesse écologique (#6), hétérogénéité (#7). Toute
  proposition qui les viole est un drapeau rouge.
- **Cohérence vocabulaire/projet** — pas de retour du lexique roguelike proscrit,
  pas de divergence avec les conceptions figées.
- **Coût perf** — **chiffre-le**. Réflexe scatter/LightField (élaguer plutôt que
  balayer tout), budget indicatif **≤ +10 % de tick par tronçon**, cache si un
  calcul géométrique se répète. Une idée coûteuse se conçoit perf-first ou se
  reporte.

Pour les sujets **bio/éco hors de l'expertise de Nico** : ne lui balance pas des
questions à trancher — **produis un court doc à étudier** (les mécanismes, les
options, ta reco), puis laisse-le décider en connaissance de cause.

Remonte les arbitrages par lots de **3 questions maximum**. Itère jusqu'à ce que
la conception soit **arbitrée et stable**. À **chaque** arbitrage tranché,
**reporte-le aussitôt dans `00_etat.md`** (§0bis) : l'état doit rester
reconstructible à tout instant, sans dépendre de ce fil de conversation.

## 3. Phase B — figer (UNIQUEMENT après accord explicite)

Quand Nico a validé la conception (« OK », « vas-y », « lets go »), matérialise.
**Un fichier à la fois**, sauf synchro cohérente explicitement demandée.

1. **Doc de conception** — crée/durcis `docs/<type>/<theme>/conception_<sujet>.md` :
   il doit refléter la conception arbitrée, pas la version challengée.

   **Où le ranger** (sprint de rangement documentaire, 2026-07-22) — la doc est
   rangée sur **deux niveaux, type puis thème** ; ne recrée JAMAIS un
   `docs/conception/` à plat :
   - **type** parmi les **8, fermé** : `meta · champs · vegetal · faune ·
     joueur · narration · rendu · perf`. Si aucun ne convient, c'est
     probablement un doc transverse → `meta/`. **On n'ouvre pas un 9ᵉ type
     sans Nico.**
   - **thème** : ouvert. S'il n'existe pas, crée le dossier avec son
     `README.md` d'**une ligne**, et **ajoute la ligne correspondante au §4
     de `docs/ARBORESCENCE.md`** (la carte doit rester exacte).
   - **nom de fichier** en `snake_case` **sans accents**, préfixé
     `conception_` (une conception) ou `etude_` (une étude préparatoire) ;
     **contenu en français accentué**.

   Référence complète — principe, les 8 types, où ranger un doc neuf, et la
   table « ancien chemin → nouveau » qui traduit tout l'historique :
   [`docs/ARBORESCENCE.md`](../../../docs/ARBORESCENCE.md).
2. **Découpage en tronçons** — autant de **sous-sprints autosuffisants** que la
   conception l'exige (souvent 3-6, **davantage si nécessaire**), **perf-first**,
   chacun une unité logique testable. Pas de plafond rigide, mais évite le
   **sur-découpage** : chaque tronçon relancé à froid repaie son amorçage, donc
   ne morcelle pas une unité logique en miettes. Chaque tronçon **préserve le
   golden** OU
   le **re-fige de façon maîtrisée et annoncée** (dérive localisée + expliquée +
   prévue par le kickoff — `/sprint-auto` refuse tout re-figeage non prévu).
   **RÈGLE PERMANENTE (Nico 2026-07-03)** : le découpage se termine TOUJOURS par
   un **tronçon vue Godot** (rendu + pont si besoin + éventuel banc d'observation
   F5), golden intact. On ne diffère plus le rendu C# en dette séparée ; rattacher
   au passage toute dette de vue Godot pertinente au sujet. Un sprint sans son
   tronçon vue est incomplet (cf. mémoire `feedback_vue_godot_toujours`).
3. **Ossature du sprint** sous `sprints/<type>/<theme>/sprint_<nom>/` (§0bis) :
   - `00_etat.md` — **déjà vivant depuis la phase A** (§0bis) : tu le
     **finalises** en état de sprint (~20 lignes : où on en est, décisions clés,
     carte des tronçons, ce qui reste, **§REPRISE**), désormais mis à jour par
     chaque tronçon d'exécution.
   - `01_*.md`, `02_*.md`… — **kickoffs autosuffisants**. Test décisif : un
     sous-agent qui démarre **à froid** (il ne sait RIEN de cette conversation)
     doit pouvoir implémenter le tronçon en lisant seulement `CLAUDE.md` +
     `00_etat.md` + son kickoff. Chaque kickoff dit : objectif, fichiers à
     toucher, modèle/formules, golden attendu (inchangé / re-figé + raison),
     ce qu'il NE faut PAS faire, points F5 éventuels.

## 4. Phase C — livrer

1. **git** — vérifie l'arbre propre AVANT (garde-fou projet + incident Nextcloud
   2026-05-29). Si sale, préviens, ne stash/commit pas de toi-même.
2. **Commit** (doc + kickoffs), message style projet en HEREDOC, terminé par
   `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>`. Jamais `push`,
   jamais `--no-verify`, ajoute les fichiers nommément (pas de `git add -A`).
3. Mets à jour la **dette** (passe l'entrée concernée à « conçu, prêt à
   implémenter ») et `journal.md` si une décision notable a été prise.
4. **Message final à Nico** — donne-lui le **message exact** à écrire après le
   `/clear` (garde-fou : toujours fournir le message littéral) :

   > Conception figée, sprint `<nom>` prêt (N tronçons, golden <inchangé / re-figé
   > au tronçon X annoncé>). Tu peux `/clear`, puis lance :
   > `/sprint-auto sprint_<nom>`

## 5. Ce que ce skill ne fait JAMAIS

- **Implémenter le moteur** — pas de code de simulation, pas de modif `data/code/`
  au-delà d'une lecture de vérification. Écrire la sim est le métier de
  `/sprint-auto` (qui exécute les kickoffs que TU produis).
- **Figer sans accord** — la phase B ne démarre pas tant que Nico n'a pas validé
  la conception.
- **Sur-découper** — autant de tronçons que nécessaire, mais pas de morcellement
  gratuit (chaque tronçon à froid repaie son amorçage).
- **Inventer un re-figeage golden non maîtrisé** — tout re-figeage prévu par un
  kickoff doit être justifié (dérive localisée, expliquée).
