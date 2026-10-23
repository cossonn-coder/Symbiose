---
name: refactor
description: >-
  Résorbe la dette de TAILLE du dépôt Symbiose : scinde les fichiers au-dessus de
  la bande (≤300 norme / 300-400 vigilance / >400 découpage requis, LDC pur via
  tools/compte_ldc.py) en paquets/classes par RESPONSABILITÉ, sans changer le
  comportement. Refactor PUR golden-gaté : le golden doit rester INCHANGÉ à chaque
  scission (s'il bouge, le découpage a introduit un bug → on annule, on ne fige
  jamais). Deux modes : auto-léger en fin de /sprint-auto (ne traite que ce que le
  sprint vient de faire dépasser) ; ciblé /refactor <fichier|module> pour les gros
  chantiers historiques. Édite directement, un fichier à la fois, commit par
  scission. C'est le maillon qui RÉSORBE ce que /audit-projet DÉTECTE.
  Usage : /refactor [fichier|module]  (sans argument = mode auto-léger / dépassements récents)
---

# /refactor — résorber la dette de taille, golden préservé

Tu **scindes**, tu ne **réécris** pas. Ce skill prend un fichier devenu trop
gros et le **réorganise par responsabilité** (paquet Python, classes C#) **sans
changer une virgule de comportement**. Le golden est le juge : un refactor pur
le laisse **strictement inchangé**. S'il bouge, ce n'est pas un refactor, c'est
une régression — tu **annules**, tu ne re-figes **jamais** (différence cardinale
avec `/sprint-auto`, dont les tronçons peuvent re-figer un golden maîtrisé).

Tu es le maillon **aval** de la chaîne : `/audit-projet` (ou `compte_ldc`)
**détecte** le dépassement, toi tu le **résorbes**.

## 0. Argument & modes

`/refactor [fichier|module]` :
- **sans argument → mode auto-léger.** Lance `python3 tools/compte_ldc.py
  --seuil 400 $(find data/code -name '*.py' -not -path '*/__pycache__/*')` (depuis
  la racine) et liste les fichiers **> 400 LDC pur** (zone rouge). En enchaînement
  de `/sprint-auto`, **restreins-toi aux fichiers que le sprint vient de faire
  dépasser** (croise avec `git diff --name-only` du sprint) — la dette reste
  attachée à son créateur, on ne refactore pas tout le dépôt par surprise.
- **`/refactor <fichier>`** (ex. `/refactor fields/population.py`) → cible **ce
  fichier**, même chantier historique de plusieurs centaines de lignes.
- **`/refactor <module>`** (ex. `/refactor fields/ecofields`) → le paquet entier.

La **bande** (rappel `CLAUDE.md`) : ≤300 = 🟢 norme ; 300–400 = 🟡 toléré si une
seule responsabilité ; **> 400 = 🔴 découpage requis**. Tu traites en priorité le
rouge ; un 🟡 ne se scinde **que** si Nico le demande nommément.

Annonce à Nico la liste des fichiers que tu vas scinder avant de commencer.

## 1. Préconditions — vérifie AVANT de toucher au moindre fichier

Si une seule échoue : **stop net**, explique, ne touche à rien.

1. **git propre** (`git status`). Règle projet « vérifier git avant tout sprint »
   + incident Nextcloud 2026-05-29. Arbre sale → préviens, ne stash/commit pas de
   toi-même.
2. **Golden vert et noté.** `cd data/code && python3 -m tests.test_golden` : capte
   le hash **AVANT** tout changement. C'est ta référence d'invariance pour toute la
   session. S'il est déjà rouge, **stop** (on ne refactore pas sur une base cassée).
3. **Le fichier dépasse vraiment.** Re-mesure au `compte_ldc.py` ; un fichier en
   zone verte ne se scinde pas « pour faire joli ».

## 2. Méthode — un découpage PUR, par responsabilité

Le seul objectif : faire repasser le fichier sous la bande **en préservant le
comportement bit-à-bit**. Donc :

- **Identifie les responsabilités** réellement présentes (plusieurs classes ? un
  gros bloc de constantes/données séparable ? des helpers d'un sous-domaine ?).
  Le découpage suit la **logique**, pas un coup de hache à la ligne 300.
- **Python → paquet.** `fichier.py` devient `fichier/` avec `__init__.py` qui
  **ré-exporte l'API publique** (les imports appelants restent intacts — couche
  `plants ← fields ← sim ← engine ← main` inchangée, imports absolus). Chaque
  sous-module = une responsabilité.
- **C# → un fichier par classe**, ou `partial` quand l'état est fortement partagé
  (chemins `res://` inchangés, namespace `Symbiose` conservé — C# résout par type).
- **Ne jette JAMAIS de code** (garde-fou projet). Tu **déplaces**, tu ne supprimes
  pas ; le code mort se signale, ne se purge pas.
- **Ne touche pas aux commentaires pédagogiques** : ils sont exigés au cœur des
  fichiers, ils voyagent avec le code qu'ils expliquent. On ne gagne pas des
  lignes en les sacrifiant (ils ne comptent déjà pas dans les LDC pur).
- **Zéro changement de comportement** : pas de « tant qu'on y est » (renommer une
  variable, corriger un bug entrevu, optimiser). Si tu vois un bug, tu le
  **signales** à Nico, tu ne le corriges pas dans le même geste (sinon le golden
  bouge et tu ne sais plus si c'est le split ou le fix).

## 3. Boucle — un fichier à la fois, golden après chaque scission

Pour chaque fichier ciblé, dans l'ordre :

1. **Scinde** selon §2 (paquet / classes).
2. **Golden + tests.** `cd data/code && python3 -m tests.test_golden` → **doit être
   INCHANGÉ** (même hash qu'au §1.2). Lance aussi les suites ciblées touchées
   (`python3 -m tests.test_<sujet>`) et, si du C# bouge, `dotnet build
   Symbiose.csproj` (PATH `~/.dotnet`). Re-mesure `compte_ldc.py` : chaque morceau
   doit être repassé **sous 400** (viser ≤300).
3. **Verdict :**
   - **Golden inchangé + tests verts + build vert** → **commit** ce seul fichier
     scindé (message style projet, HEREDOC terminé par
     `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>` ; ajoute les
     fichiers nommément, jamais `git add -A`). Fichier suivant.
   - **Golden bougé OU test rouge OU build rouge** → **le découpage a cassé qqch.**
     Annule (`git checkout`/restaure l'état pré-scission), **ne commit pas**, et
     **ne re-fige surtout pas** le golden. Diagnostique ou remonte à Nico. Un
     refactor pur ne change pas le golden : un golden qui bouge = un import oublié,
     un ordre d'init modifié, un état partagé scindé à tort.

Pour un **gros** fichier (plusieurs centaines de lignes, ex. `population.py`),
tu peux déléguer la scission à un **sous-agent** au contexte frais (prompt
autosuffisant : « scinde CE fichier par responsabilité en paquet, golden
INCHANGÉ obligatoire, ne change aucun comportement, ne commit pas ») pour garder
ton propre contexte léger — mais **tu** vérifies le golden et **tu** commit.

En fin de passe, pousse (`git push origin main`) une fois le travail fini, sans demander (règle Nico 2026-10-23). Jamais `--no-verify`/`--no-gpg-sign`.

## 4. Mode auto en fin de /sprint-auto

`/sprint-auto` t'appelle à sa **dernière étape**, une fois tous les tronçons clos
et le golden au vert. Tu tournes alors en **auto-léger** : tu ne traites que les
fichiers **que ce sprint a fait passer en zone rouge** (croise `compte_ldc` avec
les fichiers touchés par le sprint). Objectif : la dette de taille ne s'**accumule
pas** sprint après sprint, elle est résorbée pendant qu'elle est petite et
fraîche. Si rien n'a dépassé, dis-le et ne fais rien. Si un dépassement résiste
(découpage non trivial, responsabilité enchevêtrée), **ne force pas** : signale-le
comme dette à traiter en mode ciblé, ne casse pas la clôture du sprint.

## 5. Ce que ce skill ne fait JAMAIS

- **Changer le comportement** — pas de fix de bug, pas de renommage, pas d'optim
  « au passage ». Refactor pur, golden inchangé. Un bug vu se **signale**.
- **Re-figer le golden** — contrairement à `/sprint-auto`, aucun re-figeage n'est
  jamais légitime ici (un split qui bouge le golden est un bug, pas une dérive
  maîtrisée).
- **Jeter du code** — on déplace, on ne supprime pas ; le code mort se signale.
- **Refactorer tout le dépôt sans demande** — en mode auto, seulement ce que le
  sprint vient de faire déborder ; sinon, seulement la cible nommée.
- **Concevoir / implémenter une mécanique** — c'est le métier de `/conception` puis
  `/sprint-auto`. Toi tu réorganises l'existant, rien de plus.
