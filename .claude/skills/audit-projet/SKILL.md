---
name: audit-projet
description: >-
  Passe le projet Symbiose au crible sur trois plans — conception, code, tests —
  et écrit un rapport de santé priorisé (rouge/jaune/vert) dans AUDIT.md (+
  résumé à l'écran). LECTURE SEULE : il diagnostique, ne corrige rien, ne touche
  ni au moteur ni à la dette. Conception = cohérence des docs
  docs/<type>/<theme>/conception_*.md
  entre eux et avec la philo #1-#7, trous, conceptions figées non implémentées,
  dérives de vocabulaire. Code = cohérence Python (vérité) ↔ C# (vue), garde-fous
  (taille fichiers via tools/compte_ldc.py, zéro RNG vivant, un fichier = une
  responsabilité, voix narratives des espèces), code mort. Tests = golden (hash
  consignés vs réels), suites vertes/rouges, dette périmée ou à rouvrir. Chaque
  constat est relié à la dette (Dxx) ou au sprint concerné.
  Usage : /audit-projet [conception|code|tests]  (sans argument = les trois)
---

# /audit-projet — bilan de santé conception / code / tests

Tu **diagnostiques**, tu ne répares pas. Ce skill est en **LECTURE SEULE** sur
le projet : il lit, mesure, relance les tests, et produit un **rapport priorisé**.
Le seul fichier qu'il écrit est `AUDIT.md` (le rapport lui-même). Il ne modifie
ni `data/code/`, ni les docs, ni `DETTE.md`, et ne commit pas de lui-même.

## 0. Argument

`/audit-projet [plan] [sujet]` :
- **sans argument** → audite les **trois** plans en entier ;
- `plan` ∈ {`conception`, `code`, `tests`} → audite **toute** cette catégorie ;
- `plan <sujet>` → audit **ciblé** sur un sujet de la catégorie : un doc précis
  (`conception CONCEPTION_VENT`), un module/champ (`code light`), une suite ou un
  système (`tests croissance`).

Annonce à Nico le périmètre retenu avant de commencer.

## 1. Méthode commune

- **Lecture seule.** Aucune correction. Si tu vois un bug, tu le **consignes**,
  tu ne le corriges pas (un audit qui répare brouille son propre verdict).
- **Relie chaque constat** à une entrée de `DETTE.md` (Dxx) ou au sprint
  concerné. Un constat orphelin (rattaché à rien) est lui-même un signal.
- **Priorise** chaque constat : 🔴 (cassé / viole un invariant / golden rouge),
  🟡 (dette ou divergence à surveiller), 🟢 (sain, ou dette assumée sous
  contrôle). Reprends les marqueurs déjà utilisés dans `DETTE.md`.
- **Distingue le neuf du connu.** Une dette déjà tracée et maîtrisée n'est pas une
  alerte ; une divergence **non encore tracée** en est une (à signaler comme « à
  ouvrir en dette »).
- Charge d'abord `CLAUDE.md` (philo #1-#7 + garde-fous) — c'est le **référentiel**
  contre lequel tu juges.

## 2. Plan CONCEPTION

Source : `docs/<type>/<theme>/conception_*.md` (les 56 conceptions sont rangées
par type puis thème — carte et table « ancien chemin → nouveau » dans
`docs/ARBORESCENCE.md` ; balayage : `find docs -name 'conception_*.md'`),
`DETTE.md`, les fragments `docs/**/backlog_<theme>.md` + l'index `BACKLOG.md`,
et `journal.md` (index de pointeurs vers `journal/`).
Si un `<sujet>` est donné (ex. `conception CONCEPTION_VENT`), **restreins** l'audit
à ce doc + ses couplages directs ; sinon balaie tous les docs.

- **Cohérence inter-docs** — deux docs qui se contredisent sur un même champ /
  une même mécanique = 🟡/🔴.
- **Cohérence avec la philo #1-#7** — une conception figée qui viole un invariant
  (bonus/malus direct sur les plantes, RNG vivant, chiffres en HUD primaire…) =
  🔴.
- **Trous / effets oubliés** — couplages non vus (règle d'interconnexion des
  acteurs : une mécanique qui n'interagit avec rien est suspecte). Pour creuser
  un doc précis, le skill `/conception` est l'outil dédié (challenge approfondi).
- **Figé mais non implémenté** — conceptions arbitrées dont l'implémentation
  traîne : croise les docs « FIGÉ » avec la dette « conçu / 🟡 impl. » et le code
  réel. Liste-les (c'est du backlog mûr, pas un bug).
- **Dérives de vocabulaire** — lexique **roguelike proscrit** (run, shop
  inter-run, extinction terminale, héritage entre runs) réapparu quelque part =
  🟡. `grep -ri` les termes bannis dans `docs/` et les commentaires.

## 3. Plan CODE

Source : `data/code/` (Python, vérité), les `.cs` (C#, vue), `tools/`.

- **Garde-fou taille fichiers** — lance `python3 tools/compte_ldc.py` (depuis la
  racine). Tout fichier > **~350 lignes de code pur** non signalé/justifié = 🟡.
  Note le pire cas mesuré.
- **Déterminisme / zéro RNG vivant** — `grep -rn "random\." data/code/sim
  data/code/fields` : tout appel RNG **dans le chemin du tick** (hors
  `weather_at`/`_hash_noise` purs, hors outils offline) = 🔴 (viole philo #3).
- **Un fichier = une responsabilité** — repère les fichiers fourre-tout
  (plusieurs concepts non liés).
- **Cohérence Python ↔ C#** — la divergence est tracée par D10 (PathogenPressure)
  et D24 (portage). Vérifie qu'aucune **nouvelle** divergence non tracée n'est
  apparue (une mécanique Godot sans équivalent Python = 🔴, cf. CLAUDE.md).
- **Voix narratives des espèces** — règle « toute plante = ses 5 voix »
  (encyclopédie / carnet / pages / magazine / événements). Repère une espèce du
  catalogue qui serait muette = 🟡.
- **Complétude de l'écosystème (D61)** — référentiel =
  `docs/meta/calibrage/conception_completude_ecosysteme.md` (matrice fonctionnelle
  téléonomique : chaque flux a source ET puits). Lecture croisée référentiel ↔
  catalogues réels (`plants/catalogue.py`, `fields/population/registry.py`, le
  mycélium). Signale : **(a) fonctions orphelines** = lignes ⚠️ encore ouvertes
  de la matrice §2 (priorisées §3) → reco « ouvrir `/conception <sujet>` » ;
  **(b) espèces conçues-non-implémentées** = 🔵 du pipeline §4 dont le doc source
  est marqué implémenté (statut à passer ✅) ou qui traîne ; **(c) espèce hors-sol
  téléonomique** = présente au catalogue mais rattachée à AUCUNE fonction §2 →
  le référentiel doit être mis à jour (garde-fou anti-dérive). Croise le contrôle
  « 5 voix » ci-dessus (fonction bouchée par une fiche muette = 🟡). Priorité au
  bouclage trophique (une boucle ouverte au sommet, ex. super-prédateur absent,
  = 🔴). Ciblable via l'argument `ecosysteme`.
- **Code mort / orphelin** — signale-le, **ne le supprime pas** (garde-fou projet
  « ne jamais jeter de code »).
- **Performance par fonctionnalité** — chaque mécanique a un budget. Profile
  (`cd data/code && python3 tools/profile_tick.py`, + `tools/diag_light_coverage.py`
  / `tools/diag_fields_span.py`) et **attribue le coût aux postes**
  (LightField, champs `EcoFields`, populations, abri…). Deux questions :
  - **Dérive dans le temps ?** Un coût ∝ taille des canopées (LightField, D32)
    explose quand la végétation mûrit → 🔴/🟡 même si le tick instantané d'un
    monde jeune paraît sain. Repère tout poste qui grossit avec l'âge du jardin.
  - **Pérennité à l'échelle cible ?** Le coût tient-il sur le **monde réel
    1600 plots** et en **sim accélérée** (rejeu 500 ans, génération de terrain),
    pas seulement sur le smoke ? Rappelle la marge gameplay (tick vs 60 s/semaine).
  Toute fonctionnalité dont le coût n'est pas borné ou non profilé = 🟡 à tracer.

## 4. Plan TESTS

Source : `data/code/tests/`, hash golden consignés dans `journal.md`/`DETTE.md`.
L'audit porte sur l'**ÉTAT** des tests (vert/rouge, hash) ET sur la **COUVERTURE
par TYPE** : la batterie doit permettre d'**ajuster les valeurs qui règlent le
jeu**. Audite la présence de chaque famille :

- **Smoke / golden** — `cd data/code && python3 -m tests.test_golden`. Hash obtenu
  vs **dernier consigné** (journal/dette) : divergence non annoncée = 🔴
  (re-figeage sauvage) ; conforme = 🟢.
- **Non-régression** — les `tests/test_*.py` ciblés (génétique, croissance,
  vigueur, population, sénescence…). Liste **vertes / rouges** ; chaque rouge =
  🔴 nommée.
- **Longue durée** — rejeu sur des centaines d'années sans crash ni dérive (cf.
  `main.py`, 500+ ans). Existe-t-il un test/banc qui le verrouille ? Absent = 🟡.
- **Équilibrage / calibrage** — les nombreuses valeurs « post-test »
  (placeholders D12.4 et consorts) ont-elles un **banc qui mesure l'effet d'un
  réglage** (trajectoire, contraste témoin vs traité) ? Un paramètre de jeu sans
  banc d'équilibrage = 🟡 (on règle à l'aveugle). C'est l'apport central de ce plan.
- **Chaînes critiques** — une mécanique majeure récente sans test dédié = 🟡.
- **Manques de TYPE** — signale explicitement les **familles absentes** (ex. aucun
  banc d'équilibrage pour tel système), pas seulement les tests rouges.
- **Dette de test à rouvrir** — type D39 (test re-cassé par une source introduite
  plus tard). Croise la dette « test » avec l'état réel.
- Build C# si pertinent : `dotnet build Symbiose.csproj`, vert/rouge.

## 5. Sortie — AUDIT.md

Écris **un seul** `AUDIT.md` à la racine du projet (écrase le précédent ; git en
garde l'historique). L'audit n'est **pas qu'une liste de défauts** : porte une
**critique constructive** qui dit aussi **ce qui est bien** (solide, à préserver),
**ce qui est intéressant** (piste prometteuse à creuser), **ce qui est mauvais**
(à revoir), **ce qui est bloquant** (🔴, empêche d'avancer). Structure :

```
# AUDIT SYMBIOSE — <date du jour>

## Synthèse  (compte 🔴 / 🟡 / 🟢 par plan, les alertes 🔴 bloquantes en tête)
## Points forts  (ce qui est bien / intéressant — explicitement valorisé)

## Conception   (constats priorisés, chacun → Dxx ou sprint)
## Code          (idem + mesures : pire fichier ldc, postes de perf, golden hash)
## Tests         (état + couverture par TYPE : smoke / non-rég / longue durée /
                  équilibrage ; manques de famille)

## À ouvrir en dette  (constats neufs non encore tracés dans DETTE.md)
```

Chaque ligne de constat : `🔴/🟡/🟢 — description courte — (Dxx | sprint_X | NEUF)`.
**Affiche à l'écran** la **Synthèse** + les **Points forts** + les 🔴 (le détail
vit dans le fichier). Puis **commit `AUDIT.md`** (Nico l'a autorisé), message
style projet en HEREDOC terminé par
`Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>` ; pousse (`git push origin main`) une fois le travail fini, sans demander (règle Nico 2026-10-23), jamais
`--no-verify`, ajoute `AUDIT.md` nommément.

## 6. Ce que ce skill ne fait JAMAIS

- **Corriger** le code, les docs ou la dette — il diagnostique. Le seul fichier
  qu'il écrit **et commit** est `AUDIT.md` (autorisé par Nico) ; il ne touche à
  rien d'autre.
- **Re-figer le golden** — il le lance pour le LIRE, jamais pour figer un hash.
- **Modifier `DETTE.md`** — il propose « à ouvrir en dette », c'est Nico qui tranche.
