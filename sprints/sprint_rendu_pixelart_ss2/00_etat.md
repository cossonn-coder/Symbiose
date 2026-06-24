# 🏁 SS² RENDU PIXEL-ART — CLOS (Palette + Sol)

> Sous-sprint **②** du cap rendu pixel-art 16-bit (Chrono Trigger).
> Conception figée : `docs/conception/CONCEPTION_RENDU_PIXELART.md` §5/§7/§8.
> Mémoire : `project_rendu_pixelart.md`. Reprise sans contexte : lire CE fichier
> puis le kickoff `0N_*.md` du tronçon en cours.

## Cap du sprint

La partie PLANTES de SS② Palette est **déjà faite** (commit `23b5613`,
`PlantRenderer.Palette.cs` : rampes + hue-shift + lumière sud, câblées
`PlantRenderer.cs:356-360`). Restent **deux résiduels** :

1. **Figer la palette SNES ~24 couleurs** — les teintes sont aujourd'hui des hex
   ÉPARS ; on les regroupe en une palette centrale documentée (livrable + contrainte
   de cohérence). + petit raffinage : **ré-indexer la rampe de branches sur l'âge**.
2. **Sol** — dernier aplat (`WorldView.Monde.cs`, losange `Polygon2D` uni). Le
   remplacer par une **texture pré-cuite en C#** (relief lumière-sud + grain dithering,
   **4 orientations D35**, filtre Nearest), cuite en une seule passe.

## Invariants (à NE JAMAIS casser)

- **Couche B pure** (Godot/C#, `visuals/` + `world/`). Le moteur Python n'est pas
  touché → **golden trivialement préservé** : `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646`.
  Le relancer reste OBLIGATOIRE en fin de tronçon (`cd data/code && python3 -m tests.test_golden`)
  pour prouver qu'aucun fichier moteur n'a bougé.
- **`dotnet build Symbiose.csproj` → 0 erreur, 0 warning** (filet de compilation ;
  le **F5 visuel reste à Nico**, Godot pas sur la VM). Si le shell ne trouve pas
  `dotnet` : `export PATH="$HOME/.dotnet:$PATH"`.
- **Déterminisme au hash** (`Hash01`/`HashKey`), JAMAIS de `Random` (philo design #3).
- **Nearest partout** : toute `ImageTexture` cuite doit avoir le filtre Nearest.
- Namespace `Symbiose`, un fichier = une responsabilité, ~350 lignes de code pur max
  (commentaires pédagogiques exclus et exigés).
- **Pas de re-figeage du golden** : ce sprint ne le prévoit PAS. S'il bouge → bug,
  pas un nouveau hash à figer.

## Avancement

| Tronçon | Sujet | État |
|---------|-------|------|
| T1 | Palette SNES ~24 couleurs centrale + rampe branches sur `AgeWeeks` | ✅ fait |
| T2 | Texture sol pré-cuite (relief sud + grain, 4 orientations D35) | ✅ fait |

## §REPRISE

### T2 — fait (non commité, Nico commit) — CLÔT LE SPRINT
- **`world/SolTexture.cs` créé** : `internal static class SolTexture`, cuit le
  losange de sol en UNE passe via `BakeLozenge(Color soil, int orientation)` →
  `ImageTexture` ~39×20 px. Contenu : (1) **relief lumière-sud** — `lum` ∝
  projection signée du pixel sur l'axe nord→sud-MONDE, passée à un **`HueShift`
  HSV répliqué** de `PlantRenderer.Palette.cs` (mêmes `WarmHue`/`CoolHue` et
  forces → cohérence chromatique sol↔plantes) ; sud = chaud/clair, nord =
  froid/sombre. (2) **grain dithering 3 valeurs** — `Hash01(2,x,y)` quantifié
  −1/0/+1 (même mix xorshift que `PlantRenderer.Hash01`, **zéro Random**),
  faible amplitude. Hors losange (`|x/hw|+|y/hh|>1`) → **alpha 0**.
- **Amplitudes (à régler F5)** : `ReliefAmp=0.22`, `GrainStep=0.05`.
- **Méthode grain RETENUE = hash pixel** (pas Bayer 4×4) : sur 39×20 px un Bayer
  régulier quadrillerait visiblement ; le hash donne un grain désordonné mais
  rejouable. À arbitrer F5 si Bayer préféré (commenté dans le fichier).
- **4 orientations D35** : `SolTexture.SouthDir(orientation)` rejoue le quart de
  tour linéaire `(dx,dy)→(dy,−dx)` + projection iso SANS muter l'orientation
  globale de la vue (effet de bord écarté). Le bombé suit donc le sud du JARDIN.
- **Approche nœud RETENUE = `Sprite2D` par plot** (pas Polygon2D texturé) :
  centrage auto sur la Position, aucun UV losange à mapper → le plus direct.
  `TextureFilter = Nearest` sur chaque sprite (invariant).
- **Cuisson CACHÉE** : `WorldView.Monde.cs` ajoute `_soilTexCache` (clé
  `(soil, _orientation)`) + helper `GroundTexture(soil)` → ≤ 4 sols × 4 orient =
  16 cuissons sur toute la session, jamais une par plot ni recuite à chaque
  rotation. Cache = champ d'instance → survit à `RebuildWorld`.
- **`BuildGround` recâblé** (surgical) : `MakeLozenge` remplacé par un `Sprite2D`
  portant `GroundTexture(soilName)`, positionné comme avant (`WorldToScreen`).
  **Damier ±5 % conservé** via `Modulate` par plot (texture partagée). Boussole,
  cardinaux, maison, ombre : INCHANGÉS. `MakeLozenge` conservé (code non jeté,
  désormais inutilisé, **0 warning** au build — la SDK Godot ne le signale pas).
- **Golden INCHANGÉ** : `2ab026ad…` (couche B pure, moteur Python non touché).
- **`dotnet build` VERT** : 0 erreur, 0 warning.

### Verdict F5 attendu (Nico) — T2
Le sol n'est plus un aplat : chaque plot montre un **léger bombé** (sud plus
clair/chaud, nord plus sombre/froid) ET un **grain** de terre. Au quart-de-tour
(D35) le bombé **suit le sud du jardin** (comme la maison), il ne reste pas collé
à l'écran. Les 3 types de sol restent distincts ; pas de carré opaque hors
losange. À régler éventuellement : `ReliefAmp`/`GrainStep` (amplitudes), choix
hash vs Bayer pour le grain. Verser tout défaut en dette ciblée.

### Reste à faire à la CLÔTURE (Nico, au commit)
- Journal : entrée `journal/NN_2026-…_sprint-rendu-pixelart-ss2-CLOS.md` + index.
- Mémoire : MAJ `project_rendu_pixelart.md` (SS² CLOS : sol + palette).
- Commit (ex. `feat(rendu) : T2 sol texturé relief+grain 4 orientations — SS² CLOS`).

### T1 — fait (non commité, Nico commit)
- **`visuals/Palette16.cs` créé** : `internal static class Palette16`, **27 couleurs**
  nommées par rôle en rampes (bois 4, feuillage 2, symptômes 7, texture 1, sol 5,
  maison façades[4]+toits[4]+ombre). **AUCUNE fusion** : les 2 seules paires proches
  (FondPierre↔FaçadeEst d≈13 ; ToitEst↔ToitOuest d≈11) sont des distinctions VOULUES
  pour la lisibilité de la rotation D35 → fusionner aurait changé l'apparence (interdit).
  Iso-apparence stricte : mêmes hex, juste nommés/centralisés.
- **Re-câblés** (littéraux → `Palette16.Xxx`, surgical, logique de rendu intacte) :
  `PlantRenderer.cs` (Apex/Wood/Crown/DeadWood/Highlight + 7 ColorantTints),
  `PlantRenderer.Palette.cs` (WoodOlive), `PlantRenderer.Organs.cs` (LeafSpotColor),
  `WorldView.Monde.cs` (Terre/Argile/Sable/Inconnu/FondPierre + Facades/Toits/Ombre).
  Les constantes d'ÉCLAIRAGE (hue-shift, planchers calotte) LAISSÉES en place (pas
  des couleurs de palette). Palettes par espèce (Organs) et autres acteurs (litière,
  macro, compost, butineurs) NON touchés (hors scope kickoff).
- **Volet B** : `Lignification(s)` indexée sur **`AgeWeeks / LignifyFullWeeks`** (=8,
  à régler au F5) au lieu de `ThicknessCm / LignifyFullCm`. `WoodRamp` inchangée.
  Apex toujours 0. `LignifyFullCm` (3.0) CONSERVÉE — encore utilisée par le seuil
  feuille `LeafMaxThickCm = LignifyFullCm*0.5` côté Organs (cf. POINTS DE VIGILANCE).
- **Golden INCHANGÉ** : `2ab026ad…` (couche B pure, moteur Python non touché).
- **`dotnet build` VERT** : 0 erreur, 0 warning.

### Verdict F5 attendu (Nico)
Apparence plantes/sol **identique** à avant (rangement invisible), SAUF la
**lignification des branches qui suit désormais l'âge** : un jeune rameau reste
vert plus longtemps, le vieux bois brunit. Banc à exhiber : un arbre aux segments
d'âges variés (jeunes pousses vertes vs charpente brune).

### POINTS DE VIGILANCE (à arbitrer avec Nico, NON traités en T1, hors scope)
1. **Découplage invariant E5** : `LeafMaxThickCm` (Organs) cale le seuil « feuille ⟹
   segment vert » sur la bascule vert→olive de la rampe, qui dépendait de l'ÉPAISSEUR
   (`LignifyFullCm*0.5=1.5 cm`). Depuis volet B la rampe dépend de l'ÂGE → un segment
   fin (donc feuillu) mais VIEUX (`AgeWeeks≥4`) peut virer olive sous ses feuilles.
   Le commentaire `DrawPetiole` « JAMAIS brune par construction » n'est plus
   garanti par construction. À observer au F5 (probablement bénin : fin = jeune en
   pratique) ; si gênant, ré-aligner le seuil feuille sur l'âge plutôt que l'épaisseur.
2. **Flux muet `AgeWeeks==0`** : structure.json + snapshot émettent `age_weeks`
   (0.5.5) → données live OK. Mais un flux qui l'omettrait → `lig=0` (vert apex) sur
   un tronc épais établi (cf. note PlantStructure.cs:209). Pré-existant, pas aggravé
   par T1 sur les flux réels.
