---
name: sprint-auto
description: >-
  Exécute en autonome les tronçons RESTANTS d'un sprint Symbiose dont la
  conception est DÉJÀ figée (kickoffs 0N_*.md autosuffisants présents). Encode
  la boucle « lis 0N → bosse → golden → maj 00_etat → commit → clear → 0N+1 »
  sans intervention de Nico : chaque tronçon part dans un sous-agent au contexte
  frais (= /clear automatique), l'orchestrateur supervise, vérifie et commit.
  À déclencher seulement APRÈS conception figée, jamais pour concevoir.
  Usage : /sprint-auto <dossier-sprint>  (ex. /sprint-auto sprint_decomposition_compost)
---

# /sprint-auto — exécution autonome d'un sprint figé

Tu es l'**orchestrateur**. Ton contexte principal reste **léger** : tu ne fais
que lancer des sous-agents, lire leurs rapports courts, vérifier, commiter.
Le travail lourd vit dans des **sous-agents au contexte frais** (l'équivalent
fonctionnel du `/clear` entre tronçons, en automatique).

**Mode de fonctionnement choisi par Nico : « jamais s'arrêter, rapport final ».**
Tu enchaînes tous les tronçons restants d'une traite. Tu NE t'arrêtes PAS pour
demander une validation F5 ni pour confirmer un choix. **Seule exception** : un
**échec bloquant** (voir §4) où continuer empilerait du travail sur une base
cassée — là tu stoppes et livres le rapport en avance.

## 0. Argument

`/sprint-auto <dossier-sprint>` — le nom du dossier sous `sprints/`
(ex. `sprint_decomposition_compost`). Si l'argument manque, déduis le sprint en
cours depuis le contexte / `journal.md` ; en cas de doute, **demande** (ne devine
pas le mauvais sprint).

## 1. Préconditions — vérifie TOUT avant de lancer le moindre sous-agent

Si une seule échoue : **stop net**, explique à Nico, ne lance rien.

1. **git propre & à jour** (`git status`). Règle projet « vérifier git avant
   tout sprint » + incident Nextcloud du 2026-05-29. Si l'arbre est sale,
   préviens et demande quoi faire — ne commit/stash pas de toi-même.
2. Le dossier `sprints/<sprint>/` existe et contient `00_etat.md` + des
   kickoffs `0N_*.md`.
3. **Conception figée.** Lis `00_etat.md` (notamment §REPRISE et les marqueurs
   ✅/CLOSE/⏳) pour établir la **liste ordonnée des tronçons RESTANTS**. Pour
   chaque tronçon restant, un kickoff `0N_*.md` **autosuffisant** doit exister.
   S'il manque, ou si le sprint est encore en phase conception : **stop** —
   « la conception n'est pas figée, on la fait d'abord ensemble ». Cette skill
   **n'exécute que**, elle ne conçoit jamais (cf. règle « conception en
   conversation d'abord »).
4. Si tous les tronçons sont déjà clos : dis-le, ne lance rien.

Annonce à Nico la liste des tronçons que tu vas enchaîner, puis démarre.

## 2. Boucle orchestrateur — STRICTEMENT séquentielle

Les tronçons dépendent les uns des autres (le témoin passe par `00_etat.md`).
**Jamais en parallèle.** Pour chaque tronçon restant, dans l'ordre :

### a. Lance UN sous-agent (Agent, subagent_type `general-purpose`)

Prompt autosuffisant (le sous-agent démarre à froid, il ne sait rien) :

> Tu travailles sur le projet Symbiose dans `/home/nico/Nextcloud/projects/symbiose`.
> Lis d'abord `CLAUDE.md` (racine), puis `sprints/<sprint>/00_etat.md`, puis le
> kickoff `sprints/<sprint>/0N_*.md`. **Implémente UNIQUEMENT ce tronçon 0N**,
> rien d'autre, en respectant toutes les règles du projet (déterminisme, philo
> de design, un fichier = une responsabilité, ~350 lignes de code pur max,
> français, GDScript interdit / C# namespace Symbiose, moteur Python source de
> vérité).
>
> Avant de finir, OBLIGATOIRE :
> - Lance le golden : `cd data/code && python3 -m tests.test_golden`. Note s'il
>   est **inchangé** ou **re-figé** (et dans ce cas le nouveau hash + la raison).
>   Un re-figeage n'est légitime QUE s'il est **explicitement prévu par le
>   kickoff** ; sinon c'est une régression à corriger, pas à figer.
> - Si tu touches du C# : `dotnet build Symbiose.csproj` (filet de compilation ;
>   le F5 visuel reste à Nico). Note vert/rouge.
> - Mets à jour `sprints/<sprint>/00_etat.md` (avancement du tronçon + §REPRISE).
> - **NE COMMIT PAS, ne push pas.** Laisse les changements en place, je commit.
>
> Rends un rapport en **moins de 200 mots** : (1) ce que tu as fait, (2) golden
> inchangé / re-figé+hash+raison, (3) build C# vert/rouge/non concerné,
> (4) fichiers touchés, (5) points qui exigent une validation **F5** de Nico,
> (6) tout blocage ou décision de design imprévue rencontrée.

### b. Vérifie (trust but verify)

`git diff --stat` ; relance le golden toi-même si le rapport est ambigu. Le
rapport du sous-agent décrit ce qu'il **comptait** faire, pas forcément ce qui
est sur le disque.

### c. Décide

- **Sain** (golden inchangé OU re-figeage prévu par le kickoff ; build vert ou
  non concerné ; pas de blocage) → **commit** (message style projet, HEREDOC,
  terminé par `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>`), puis
  tronçon suivant.
- **Échec bloquant** → voir §4. Tu stoppes.

Garde-fous à chaque commit : jamais `push`, jamais `--no-verify`/`--no-gpg-sign`,
jamais `git add -A` aveugle (ajoute les fichiers du tronçon nommément).

## 3. Fin de sprint (tous les tronçons clos)

1. Mets à jour `journal.md` (index de pointeurs) + l'entrée détaillée dans
   `journal/` selon la convention du projet.
2. Mets à jour la mémoire auto si des **décisions de design / feedback notables**
   ont émergé (sinon, rien — pas de bruit).
3. Supprime `HANDOFF.md` s'il existe et est devenu obsolète.
4. **Rapport final à Nico** : tronçons faits, hash golden final, **liste précise
   des points F5 à valider**, ce qui reste éventuellement.

## 4. Échec bloquant = la seule cause d'arrêt anticipé

Stoppe immédiatement (ne commit pas du cassé, ne lance pas le tronçon suivant)
si :
- le golden casse de façon **non prévue** par le kickoff ;
- un tronçon **re-fige le golden sans que le kickoff le prévoie** (viole la règle
  sacrée « tout re-figeage maîtrisé et annoncé ») ;
- `dotnet build` reste **rouge** et le sous-agent ne l'a pas résolu ;
- le sous-agent signale un **blocage** ou une **décision de design imprévue** que
  le kickoff ne tranche pas.

Dans tous ces cas : laisse l'état tel quel (sain commité, cassé non commité),
puis livre un **rapport** clair (où ça bloque, ce qu'il faudrait décider/corriger).
C'est le « rapport final », simplement plus tôt.

## 5. Ton propre contexte

Tu restes léger (rapports courts). Si l'alerte « contexte bas » arrive malgré
tout, applique le protocole handoff habituel du CLAUDE.md global (écrire
`HANDOFF.md`, prévenir Nico, ne pas lancer `/compact` toi-même) — puis reprends
après compaction sur le tronçon suivant.
