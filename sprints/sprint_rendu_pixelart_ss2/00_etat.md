# SS² Rendu pixel-art — Palette + Sol (état partagé)

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
| T2 | Texture sol pré-cuite (relief sud + grain, 4 orientations D35) | ⏳ à faire |

## §REPRISE

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
