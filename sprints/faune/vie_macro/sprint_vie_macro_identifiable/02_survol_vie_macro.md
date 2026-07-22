# ② Découverte de la vie macro au survol (D60)

> Kickoff autosuffisant. Reprise à froid : `CLAUDE.md` + `00_etat.md` + ce fichier.
> Dépend de ① (backend unifié : `observer_espece` doit pouvoir découvrir des clés
> non-plantes). Golden **NEUTRE**. **Point F5** (survol Godot).

## Objectif
Étendre la posture naturaliste « on apprend ce qu'on REGARDE » à toute la vie
macro. Aujourd'hui seul le survol d'une PLANTE déclenche `observer`
(`world/WorldView.Observation.cs`). Ici : survoler un animal (faune trophique OU
butineur) ou un carpophore **découvre** son entrée d'encyclopédie.

## Backend (Python)
- **MODIFIER `tools/simserver/maitrise_pont.py:observer_espece`** — aujourd'hui il
  ne résout QUE les noms de classe de plantes (`_CLE_DE_NOM`). Le rendre
  **multi-règnes** :
  1. si `nom` ∈ `_CLE_DE_NOM` (nom de classe de plante) → clé plante (inchangé) ;
  2. sinon si `nom` est une clé animale connue (`FAUNE_ENCYCLO` de
     `fields/faune_encyclo.py`) → cette clé, type animal ;
  3. sinon si `nom == CLE_CHAMPIGNON` (`"champignon"`, de `sim/champignon_encyclo`)
     → cette clé ;
  4. sinon `None` → no-op (nom inconnu, pas de fausse découverte).
  Puis `observer(gs, player, cle)` (découvre + petit gain Vigueur, idempotent —
  inchangé). ⚠️ La vie macro envoie directement une **clé d'espèce** (le C# connaît
  déjà `puceron`, `abeille`… via `MacroLife.Especes`/`ForagerLayer`), pas un nom de
  classe : c'est pourquoi on teste la clé animale telle quelle, sans reverse-map.
- `cmd_observer` (`tools/simserver/maitrise_cmds.py`) reste inchangé : il passe
  déjà `msg.species` à `observer_espece`. Le C# enverra la clé d'espèce animale ou
  `"champignon"` dans ce même champ.

## Vue (C#) — POINT F5
- **MODIFIER `world/WorldView.Observation.cs`** — aujourd'hui `ObserveHoveredPlant`
  survole les plantes. Ajouter la **vie macro** :
  - Réutiliser le picking DÉJÀ existant `visuals/MacroLife.cs:SpeciesNear(wMonde,
    rayonCm)` (rend la clé d'espèce trophique sous le curseur — 10 espèces). Pour
    les **butineurs** (`NonDessine`, rendus par `ForagerLayer`), exposer un picking
    analogue (clé d'espèce butineur sous le curseur) si pas déjà là.
  - Même dédup que les plantes : un `HashSet<string> _especesMacroObservees` (ou
    réutiliser `_especesObservees` en préfixant, au choix — garder simple), et
    n'émettre `_bridge.Observer(cleEspece)` qu'à la 1ʳᵉ fois.
  - Carpophore : le survol d'un carpophore (rendu par `visuals/CarpophoreLayer.cs`)
    → `_bridge.Observer("champignon")` (la clé générique). Le picking carpophore
    peut être ajouté ici ou préparé pour ⑥ (hover carpophore) — au minimum, câbler
    l'observation champignon.
  - ⚠️ La vie macro n'est visible qu'au zoom ≥ `MacroLife.MinZoom` (4×) : le survol
    ne peut découvrir que ce qui est affiché — cohérent (on n'observe pas
    l'invisible). Pas de découverte au dézoom.
- `core/SimBridge.cs:Observer(string species)` existe déjà — le réutiliser tel
  quel (il envoie `{cmd:"observer", species:…}`).

## Ce qu'il NE faut PAS faire
- Ne PAS créer de progression de palier animal : la découverte les met à palier 1,
  et `maitrise_detection` ne les crédite jamais → ils restent à 1 (= 1 fiche mono).
  C'est voulu (décision Q1).
- Ne PAS ajouter d'espèces fongiques : champignon = 1 entrée générique (Q2).
- Ne PAS balayer un nouveau champ : `SpeciesNear` est déjà appelé (écrasement),
  on réutilise. Zéro coût perf moteur.
- Ne PAS toucher au tick / golden.

## Golden
NEUTRE. `observer_espece` vit dans le pont opt-in (hors tick). Test Python : une
clé animale connue → découverte (palier 1) ; `"champignon"` → découverte ; nom
inconnu → no-op. `dotnet build Symbiose.csproj` doit passer (filet compilation).

## Points F5 (Nico, sur Godot)
Survoler un puceron/une coccinelle/une abeille/un carpophore au zoom ≥ 4× →
l'entrée apparaît dans l'encyclopédie (onglet correspondant, visible après ⑥).
Avant ⑥ : vérifier dans les logs `[WorldView] survol → espèce observée : …`.
