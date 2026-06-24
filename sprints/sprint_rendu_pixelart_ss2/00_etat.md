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
| T1 | Palette SNES ~24 couleurs centrale + rampe branches sur `AgeWeeks` | ⏳ à faire |
| T2 | Texture sol pré-cuite (relief sud + grain, 4 orientations D35) | ⏳ à faire |

## §REPRISE

(vide — sprint pas encore démarré)
