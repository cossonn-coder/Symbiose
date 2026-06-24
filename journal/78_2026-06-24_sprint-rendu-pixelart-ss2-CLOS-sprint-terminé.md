# 2026-06-24 — Sprint RENDU PIXEL-ART SS² (Palette + Sol) — CLOS

> Sous-sprint **②** du cap rendu pixel-art 16-bit (Chrono Trigger). Couche B
> pure (Godot/C#), moteur Python non touché → golden trivialement préservé.
> Conception figée : `docs/conception/CONCEPTION_RENDU_PIXELART.md` §5/§7/§8.
> Exécuté en autonome via `/sprint-auto` (orchestrateur + 2 sous-agents frais).

## T1 — Palette SNES centrale + lignification sur l'âge (`d860bac`)

- **`visuals/Palette16.cs` créé** : `internal static class Palette16`, **27
  couleurs** nommées par rôle en rampes (bois 4, feuillage 2, symptômes 7,
  texture 1, sol 5, maison façades[4]+toits[4]+ombre). **Aucune fusion** : les
  2 paires proches (FondPierre↔FaçadeEst ; ToitEst↔ToitOuest) sont des
  distinctions VOULUES pour la lisibilité de la rotation D35. Iso-apparence
  stricte : mêmes hex, juste centralisés/nommés.
- **Re-câblés** (littéraux → `Palette16.Xxx`, surgical) : `PlantRenderer.cs`,
  `PlantRenderer.Palette.cs`, `PlantRenderer.Organs.cs`, `WorldView.Monde.cs`.
  Constantes d'ÉCLAIRAGE (hue-shift) laissées en place. Palettes par espèce et
  autres acteurs (litière, macro, compost, butineurs) hors scope, non touchés.
- **Volet B** : `Lignification` indexée sur `AgeWeeks / LignifyFullWeeks` (=8)
  au lieu de l'épaisseur du segment. `WoodRamp` inchangée, apex=0.

## T2 — Sol pré-cuit relief + grain, 4 orientations D35 (`a35d5b0`)

- **`world/SolTexture.cs` créé** : `internal static class SolTexture`, cuit le
  losange de sol en UNE passe via `BakeLozenge(soil, orientation)` →
  `ImageTexture` ~39×20 px. (1) **relief lumière-sud** : `lum` ∝ projection
  signée du pixel sur l'axe nord→sud-MONDE, passée à un `HueShift` HSV répliqué
  de `PlantRenderer.Palette.cs` (cohérence chromatique sol↔plantes) ; sud
  chaud/clair, nord froid/sombre. (2) **grain dithering 3 valeurs** au
  `Hash01` déterministe (zéro Random ; hash pixel retenu plutôt que Bayer 4×4,
  qui quadrillerait visiblement sur 39×20 px). Hors-losange → alpha 0.
- **`Sprite2D` par plot** portant la texture cuite partagée, filtre Nearest.
  Cache `(soil, orientation)` ⇒ ≤ 16 cuissons par session, jamais recuit à la
  rotation. Damier ±5 % conservé via `Modulate`. `MakeLozenge` conservé
  (inutilisé, non jeté). Boussole, cardinaux, maison, ombre inchangés.

## Invariants

- **Golden INCHANGÉ** `2ab026ad…` sur les 2 tronçons (couche B pure).
- **`dotnet build` VERT** : 0 erreur, 0 warning (confirmé orchestrateur).

## Points F5 à valider (Nico) + vigilance

- **T1** : apparence identique sauf la **lignification désormais sur l'âge**
  (jeune rameau vert plus longtemps, vieux bois brun). Régler `LignifyFullWeeks`
  (8). VIGILANCE — découplage invariant E5 : `LeafMaxThickCm` (seuil feuille)
  reste calé sur l'ÉPAISSEUR ; un segment fin mais vieux peut olivir sous ses
  feuilles (probablement bénin : fin = jeune en pratique). Si gênant, ré-aligner
  le seuil feuille sur l'âge.
- **T2** : bombé sud clair/chaud, nord sombre/froid ; suit le sud du jardin au
  quart-de-tour (D35) ; 3 sols distincts ; pas de carré opaque hors losange.
  Réglages ouverts : `ReliefAmp=0.22`, `GrainStep=0.05`, hash vs Bayer.

SS² CLOS (Palette + Sol). Cap rendu pixel-art : SS① + SS² faits, F5 visuel = Nico.
