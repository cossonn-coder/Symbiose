# T1 — Palette SNES ~24 couleurs centrale + rampe branches sur l'âge

> Lire d'abord `00_etat.md` (invariants) + `docs/rendu/pixelart/conception_rendu_pixelart.md` §5/§7.
> Couche **B pure** (C#). Golden trivialement préservé, build C# vert, F5 = Nico.
> PREMIER tronçon : valide la palette sur un acteur déjà fait (les branches).

## But

Deux choses, toutes deux de **cohérence chromatique** :
1. **Figer une palette centrale SNES ~24 couleurs.** Aujourd'hui les teintes du rendu
   sont des hex ÉPARS dans plusieurs fichiers. On les regroupe dans **un seul fichier
   palette documenté** (rampes nommées partagées), comme livrable et contrainte de
   cohérence. C'est surtout du **rangement** : on NE change PAS l'apparence (mêmes hex),
   on les NOMME et les CENTRALISE.
2. **Ré-indexer la rampe de lignification des branches sur `AgeWeeks`** au lieu de
   `ThicknessCm`. C'est un raffinage : une rampe vert-tendre → olive → brun ∝ **âge du
   segment** (un jeune rameau reste vert plus longtemps, le vieux bois brunit).

## Contexte technique (état réel du code)

- **Les branches ont DÉJÀ leur rampe** : `PlantRenderer.Palette.cs`
  - `Lignification(s) = s.IsApex ? 0 : clamp(s.ThicknessCm / LignifyFullCm, 0, 1)`
    (`LignifyFullCm = 3.0`).
  - `WoodRamp(lig)` : `ApexColor`(`5ec46a`) → `WoodOlive`(`8a7a38`) → `WoodColor`(`7a5230`).
  - Câblé `PlantRenderer.cs:356-357` : `WoodRamp(Lignification(s))`, puis `DrawBranch`.
- **`Segment.AgeWeeks` existe** (`core/PlantStructure.cs:37`, `int`, transporté pont
  0.5.5). Les feuilles l'utilisent déjà (`Organs.cs:149`, `AgeWeeks / LeafMaturityWeeks`).
- **Hex épars à centraliser** (liste non exhaustive — repérer à `grep`) :
  - `PlantRenderer.cs` : `ApexColor 5ec46a`, `WoodColor 7a5230`, `CrownColor 3f7a4e`,
    `DeadWoodColor 6b5d4f`, `HighlightColor ffe66b`, `ColorantTints` (7 symptômes :
    `chlorose d8d24a`, `asphyxie 6e6a4a`, `secheresse b9a87a`, `senescence c4702a`,
    `maladie 8a6a4a`, `ombre c2c8a0`, `acclimatation 9db8b0`), `LeafSpotColor 4a3320`,
    `LeafHoleColor` (cf. Organs).
  - `PlantRenderer.Palette.cs` : `WoodOlive 8a7a38`, teintes hue-shift (constantes, PAS
    des couleurs de base — les LAISSER là, ce sont des paramètres d'éclairage).
  - `WorldView.Monde.cs` : `TerreColor 967a64`, `ArgileColor cd7434`, `SableColor f1e9bb`,
    `SolInconnu 777777`, `FondPierre 8d8881`, `FacadeColors[4]`, `ToitColors[4]`,
    `OmbreColor`.

## Travail

### A. Créer la palette centrale (nouveau fichier `visuals/Palette16.cs`)

- `internal static class Palette16` (namespace `Symbiose`), constantes `Color` **nommées
  par rôle** et regroupées en **rampes** commentées (sol / bois / feuillage sain /
  symptômes / structure-maison). Viser **~24 couleurs SNES** : si en regroupant on
  dépasse, FUSIONNER les teintes très proches (c'est l'intérêt de la contrainte) —
  documenter chaque fusion. Si on est en-dessous, tant mieux.
- **NE PAS changer l'apparence** : reprendre les **mêmes hex** existants, juste nommés.
  Toute fusion qui change un hex doit être **signalée** dans le commentaire + au F5.
- Remplacer dans `PlantRenderer.cs`, `PlantRenderer.Palette.cs`, `PlantRenderer.Organs.cs`
  et `WorldView.Monde.cs` les littéraux `new Color("…")` par `Palette16.Xxx`.
  ⚠️ **Surgical** : ne toucher QUE les déclarations de couleur, pas la logique de rendu.
  Les constantes d'éclairage (hue-shift `WarmHue`/`CoolHue`/`*Strength`, planchers
  `LitFactor*`, `ColorCoolShiftFloor`) NE sont PAS des couleurs de palette → les laisser.
- Garde-fou taille : `Palette16.cs` doit rester court (déclaratif). Si > ~350 lignes de
  code pur, signaler.

### B. Ré-indexer la rampe de branches sur `AgeWeeks`

Dans `PlantRenderer.Palette.cs`, `Lignification` :
- Remplacer l'index `ThicknessCm / LignifyFullCm` par `AgeWeeks / LignifyFullWeeks`.
- Ajouter une constante `LignifyFullWeeks` (à régler au F5 ; proposer une valeur
  cohérente avec le rythme du moteur, p.ex. **8** semaines — un rameau pleinement
  ligneux en ~2 mois). Apex toujours 0 (reste tendre).
- Garder `WoodRamp` inchangée (la rampe de couleurs ne change pas, seul son index change).
- Commenter le POURQUOI (âge = meilleur proxy de lignification que l'épaisseur pour un
  jeune rameau fin mais vieux ↔ un gros apex récent) — pédagogie exigée.

## Vérifications

1. `dotnet build Symbiose.csproj` → **0 erreur, 0 warning**.
2. Golden inchangé : `cd data/code && python3 -m tests.test_golden` → `2ab026ad…`.
3. Relecture : aucune teinte de rendu n'a changé de valeur SANS être signalée (le
   regroupement est iso-apparence sauf fusions documentées) ; les constantes
   d'éclairage sont restées hors palette ; rampe branches indexée sur `AgeWeeks`.

## Clôture (MAJ `00_etat.md`)

- Passer T1 ✅ dans la table.
- §REPRISE : entrée T1 = `Palette16.cs` créé (nb de couleurs final, fusions éventuelles),
  fichiers re-câblés, `LignifyFullWeeks` retenu, golden vérifié, `dotnet build` vert.
- **Verdict F5 attendu (à écrire pour Nico)** : l'apparence des plantes/sol doit être
  **identique** à avant (le rangement est invisible) SAUF (a) toute fusion de teinte
  signalée, (b) la lignification des branches qui suit désormais l'âge — un jeune
  rameau reste vert plus longtemps, le vieux bois brunit. Banc à exhiber : un arbre
  d'âges de segments variés (jeunes pousses vertes vs charpente brune).
- Commit (ex. `feat(rendu) : T1 palette SNES centrale + lignification sur l'âge — SS²`).
