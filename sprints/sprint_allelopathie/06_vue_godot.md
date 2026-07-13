# ⑥ Vue Godot — overlay + indices diégétiques

> Kickoff autosuffisant. Reprise à froid = `CLAUDE.md` + `00_etat.md` + ce fichier
> + `CONCEPTION_ALLELOPATHIE.md` §F. Prérequis : ①→⑤ faits. Golden **INTACT**
> (aucune ligne moteur touchée). F5 visuel = Nico (Godot pas sur la VM ;
> `dotnet build Symbiose.csproj` = filet de compilation).

## Objectif

Rendre l'allélopathie **perceptible** : overlay debug technique + indices
diégétiques (philo #5, pas de chiffres). Exposer le champ au snapshot par le pont.
**Aucune modification moteur** → golden intact.

## Fichiers à toucher

### Pont (Python → snapshot), sans toucher la sim
- `tools/sim_server.py` (ou le module d'export snapshot) — exposer `allelopathie`
  par tuile en **liste creuse des foyers > 0** (patron de `alarme` : ne sérialiser
  que les plots non nuls, pas la grille pleine). Incrémenter la version de protocole
  du pont (cf. `00_etat.md` pour la version courante). **Lecture seule** du champ,
  aucune écriture moteur.

### Godot (C#, namespace `Symbiose`)
- `visuals/FieldOverlay.cs` — ajouter `allelopathie` à la **heatmap debug F6**
  (comme les autres champs de sol) : zone d'inhibition visible en mode technique.
- Indices **diégétiques** (profondeur laissée au F5) : halo de **sol nu/pelé** sous
  un émetteur fort (terre sans levée autour du noyer/armoise), graines qui ne lèvent
  pas. Réutiliser la sémiologie de rendu existante (ne pas inventer un système neuf) ;
  si trop coûteux, se limiter à l'overlay F6 + noter la dette d'indice diégétique.

## Golden attendu

**INTACT.** Ce tronçon ne touche que la vue + l'export snapshot (lecture seule).
Lancer `python3 -m tests.test_golden` → hash **inchangé**. Toute dérive = un fichier
moteur a été touché par erreur → annuler.

## Compilation / F5

- Filet VM : `dotnet build Symbiose.csproj` doit passer (compilation C#).
- Propager le code par **git push** vers `cossonn-coder/Symbiose` (le F5 tourne sur
  le Windows de Nico). Ne jamais faire transiter le code Godot par un file-sync.
- **F5 visuel = Nico** : overlay F6 `allelopathie` visible + halo de sol nu sous un
  émetteur fort. Consigner le verdict F5 dans `00_etat.md`.

## Ce qu'il NE faut PAS faire

- Ne PAS toucher une ligne de la simulation (golden intact obligatoire).
- Ne PAS afficher de chiffres/barres en HUD primaire (overlay = mode debug F6 assumé ;
  indices de jeu = diégétiques, philo #5).
- Ne PAS sérialiser la grille pleine (liste creuse des foyers > 0, comme `alarme`).
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Vérif

Golden intact + `dotnet build` OK + push + F5 Nico (overlay + indice de sol nu).
Clôture du sprint : finaliser `00_etat.md`, `DETTE.md`, `BACKLOG.md`, `journal.md`.
