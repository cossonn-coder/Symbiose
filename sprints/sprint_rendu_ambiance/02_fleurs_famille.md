# T2 — Fleurs par famille (VUE C#, golden inchangé)

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` + ce fichier.
> Conception : `docs/conception/CONCEPTION_RENDU_AMBIANCE.md` §3.

## Objectif
Donner à chaque fleur une **forme par famille botanique** (aujourd'hui : corolle
générique 5 pétales ; seule la couleur est par espèce via `OrganPalette.Flower`).
**Copier le patron déjà en place pour les feuilles** (`visuals/PlantRenderer.Leaf.cs` :
`enum LeafShape` + `LeafProfile[species]` + tracé déterministe) et le décliner
pour les fleurs.

## Fichiers à toucher
- **Neuf** : `visuals/PlantRenderer.Flower.cs` (partial de `PlantRenderer`, garde
  `Organs.cs` court — garde-fou taille). Y déplacer/écrire le tracé des fleurs.
- Lire `visuals/PlantRenderer.Organs.cs` (fleur actuelle 5 pétales + `OrganPalette`),
  `visuals/PlantRenderer.Leaf.cs` (le patron à copier), `visuals/PlantRenderer.Palette.cs`
  (`DrawVolumeEllipse`, hue-shift).

## Modèle
- `enum FlowerShape { Simple, Ombelle, Capitule, Papilionacee, Epi, Clochette }`.
- `readonly record struct FlowerProfile(FlowerShape Shape, int Count, float Aspect)`
  + table `FlowerProfiles[species]`, en regard de `OrganPalette`. Défaut = `Simple`.
- **Mappage par famille** (cf. tableau §3.1 du doc) : Rosaceae/bourrache→`Simple`,
  Apiaceae→`Ombelle`, Asteraceae→`Capitule`, Fabaceae→`Papilionacee`,
  Lamiaceae/Brassicaceae→`Epi`, Ericaceae→`Clochette`. Mapper les espèces déjà
  présentes dans `OrganPalette` ; le reste → `Simple`.
  - La famille est connue côté moteur. Si elle n'est pas déjà dans le snapshot,
    soit l'y exposer (petit champ `family` par plante, re-bump `ENGINE_VERSION`
    = simple transport, golden inchangé), soit tenir une table espèce→archétype
    directement en C# (plus simple, aucun pont). **Préférer la table C#** sauf si
    la famille est déjà transportée.
- **Tracé déterministe** : chaque archétype compose des **primitives volumées**
  (chaque sous-corolle via `DrawVolumeEllipse` → invariant ≥ 2 valeurs, jamais
  d'aplat). Placement des sous-corolles par **hash** du segment (jitter stable,
  zéro `Random`). Réutiliser la couleur `OrganPalette.Flower` de l'espèce.
  - `Capitule` = disque central + couronne de rayons ; `Ombelle` = N taches sur
    pédicelles rayonnants ; `Epi` = pile verticale ; `Papilionacee` = étendard +
    2 ailes + carène ; `Clochette` = corolle tubulaire ; `Simple` = l'existant.

## Perf / LOD (ne pas régresser le sprint perf du 2026-07-09)
- **Plancher de rayon** : sous ~2-3 px écran, une corolle composée retombe sur
  une tache simple 1 valeur.
- Respecter le **palier organes** existant (`OrganDetailMinZoom`) : au dézoom,
  retour à `Simple` ou aucune fleur. Ne pas dessiner d'organes sous le LOD
  silhouette. Rester sous le plafond d'organes (`MaxFruits`, proxy fleurs).

## Golden / build
- **Vue pure → golden inchangé** (aucun moteur touché ; si champ `family` exposé,
  c'est du transport → golden inchangé, vérifier quand même
  `python3 -m tests.test_golden`).
- `dotnet build Symbiose.csproj` **vert** (filet de compilation VM).

## Ne PAS faire
- Pas de `Random`. Pas d'aplat. Pas de re-`_Draw` par frame nouveau. Pas de fleur
  au-dessus du plafond d'organes. Ne pas toucher la couleur (déjà par espèce).

## F5 Nico
Vérifier à l'œil que carotte (ombelle), tournesol/souci (capitule), haricot
(papilionacée), lavande/moutarde (épi), myrtille (clochette), pommier (simple)
ont des corolles distinctes ; et la bascule LOD au dézoom.
