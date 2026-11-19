# ② Noms des espèces en français à l'écran (ferme D141)

Lire d'abord `docs/vegetal/sante/conception_lisibilite_bilan.md` (§2.2) et l'entrée D141
de `DETTE.md`.

## Objectif
Nico ne doit plus jamais lire un nom de classe anglais (`Comfrey`, `OakTree`). Constaté au
F5 : étiquette de survol « Comfrey · adulte », rapport perf F4 « espèces : Comfrey×3
OakTree×4 ».

## Faits vérifiés au code (2026-11-19)
- Chaque classe d'espèce porte déjà `name` en français accentué (`Pepper.name = "Poivron"`,
  `Comfrey` → « Consoude », `Yarrow` → « Achillée millefeuille »). Vérifie les 52 espèces du
  catalogue (arbres compris) ; complète celles qui n'en auraient pas.
- Le pont envoie `species = cls.__name__` (`tools/simserver/serialize.py` ~l.154 et ~l.643)
  et un `name` par plante (`PlantInstance.name`, `plants/base/instance.py` ~l.519 — vérifie
  ce qu'il contient).
- C# : `core/PlanteLue.cs` compose `Tag = $"{Species} · {stage_name}"` ;
  `world/WorldView.PerfReport.cs` affiche les clés de `par_espece` ;
  `world/DossierPlantePanel.cs` lit `name`.
- 10 sites `__name__` dans `tools/simserver/*.py` : fais l'inventaire de ceux qui finissent
  à l'écran (rapport perf `par_espece`, chronique, pires ticks…) et de ceux qui servent
  d'identifiant.

## Modèle
- Source unique : `cls.name`. Le pont expose un **nom affiché** par plante (clé neuve, ou
  `name` s'il vaut déjà le nom d'espèce — à toi de trancher proprement) ; la clé
  identifiante `species` **reste** le nom de classe (ports, sprites, tables C# s'en servent).
- Tout texte humain (étiquette, info-bulle, dossier plante, rapport F4, chronique, logs du
  carnet s'ils montrent une classe) passe par le nom affiché.
- Bump de version du pont si une clé est ajoutée (`tools/simserver/version.py`).

## Preuves
- Snapshot JSON HEAD vs après : seules les clés/valeurs de nom changent (le golden ne voit
  pas le pont, cf. mémoire projet).
- Tests du pont verts ; un test qui échoue si un nom affiché ressemble à un nom de classe
  (pas d'espace ni d'accent ET CamelCase) pour toutes les espèces.
- `dotnet build Symbiose.csproj` vert ; capture VM d'une étiquette si le banc de capture
  le permet.

## Golden
**INTACT** (`8f2dd7ad…` ou le hash re-figé au ①, voir `00_etat.md`). S'il bouge : régression.

## À ne pas faire
Pas de réglage de langue, pas de table de traduction neuve (décision Nico). Ne renomme pas
`species`. Pas de modification moteur hors exposition du nom.

## F5
Étiquette de survol et rapport F4 en français (« Consoude · adulte », « Consoude×3 Chêne×4 »).
