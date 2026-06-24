# Tronçon ⑤ — Sélecteur Godot + F5 + bilan D47

> Sprint « bancs d'essai ». État : `00_etat.md`. Dernier tronçon : rendre les
> bancs choisissables à l'écran, valider au F5, et consolider le bilan D47.
> **Golden NEUTRE** (aucune mécanique moteur ; au plus un bump de pont si un champ
> de protocole est ajouté).

## Objectif
Nico choisit un banc au lancement sans éditer d'argument, observe à l'écran, et
le sprint tranche définitivement chaque anomalie D47.

## Périmètre

### 1. Sélecteur côté Godot (C#)
- Aujourd'hui le banc s'active déjà par le champ `config` de la commande `init`
  (`tools/simserver/commands.py:45`) ; côté C#, l'`init` part de `SimBridge`
  (`core/SimBridge.cs`) appelé au démarrage de la scène `WorldView`
  (`world/WorldView*.cs`). Le sélecteur n'est qu'un **moyen de passer une autre
  `config`** que `full`.
- Mécanisme MINIMAL (à privilégier — Nico apprend le C#/Godot, garder simple) :
  un petit menu (OptionButton / liste) au lancement listant les noms de `BANCS`
  (+ `full`/`smoke`), qui passe la `config` choisie à `SimBridge.Init(...)`. La
  liste des bancs peut être **demandée au serveur** (petite commande `list_bancs`
  renvoyant `BANCS.keys()`) ou **codée en dur côté C#** dans un premier temps
  (plus simple ; la source reste Python, le C# n'est qu'un menu). Choisir le plus
  simple et le NOTER.
- **Filet de compilation** : `dotnet build Symbiose.csproj` sur la VM doit passer
  (le F5 visuel reste à Nico — Godot n'est pas sur la VM).

### 2. F5 (Nico)
- Pour chaque banc : lancer, observer que le signe attendu apparaît à l'écran
  (sauf `ombre_dense`, muet tant que dette 0.5.2 non levée — attendu).
- Confronter écran ↔ oracle : oracle vert + écran muet ⇒ bug **rendu C#** (le
  verser en dette ciblée, ex. mapping couleur/texture manquant).

### 3. Bilan D47 (consolidation)
- Rassembler dans `00_etat.md` (et reporter dans `DETTE.md`, entrée D47) le verdict
  de chaque anomalie tranchée aux ②③④ :
  - C2 (asphyxie muette), C3 (criblage fantôme), C4 (chaîne floraison),
    C5 (Solanaceae), C6 (NPK pauvres).
  - Pour chacune : **bug réel** (→ correctif fait, ou dette ciblée créée) vs
    **artefact de la carte `full`** (→ clos, documenté).
- Mettre à jour D47 dans `DETTE.md` : rayer ce qui est tranché, isoler les bugs
  résiduels en dettes propres.

## Vérifs
- Golden inchangé `2ab026ad…` (bump de pont SEULEMENT si `list_bancs` ajouté —
  alors documenter la version dans `version.py`).
- `dotnet build Symbiose.csproj` OK.
- F5 Nico : chaque banc montre son signe (hors `ombre_dense`).

## Sortie
MAJ `00_etat.md` : ⑤ clos = **SPRINT TERMINÉ**. Bilan D47 consolidé dans
`DETTE.md`. MAJ `BACKLOG.md` (l.46 : « conception à écrire » → sprint livré) et
`journal.md`. Commit. Mémoire : statut projet + verdict F5.
