# T3 — Cohérence palette SS² + diagnostic F5 (C2/C3)

> Lire d'abord `00_etat.md` (invariants) + `CONCEPTION_SEMIOLOGIE_VISUELLE.md`
> §5 (palette SS²) et §6 (diagnostic C2/C3). Couche **B pure** (C#). DERNIER
> tronçon → CLÔT le sprint. Golden trivialement préservé, build C# vert, F5 = Nico.

## But

Deux choses, toutes deux de **lisibilité** (pas de nouveau signe) :
1. **Cohabitation palette** : depuis SS² (`CONCEPTION_RENDU_PIXELART.md` §5, commit
   `23b5613`), les feuilles passent par un **hue-shift** (lumière/volume) APRÈS la
   teinte de symptôme. Le hue-shift d'ombre tire vers le **bleu froid** → côté nord,
   un symptôme **jaune** (chlorose, sénescence) peut **verdir** et perdre en
   lisibilité. Il faut s'assurer que les symptômes restent lisibles sous la palette.
2. **Diagnostic C2/C3** : instrumenter le protocole F5 (cause moteur → attendu écran)
   pour trancher les suspects rendu hérités des bancs d'essai (D47).

## Contexte technique

Ordre de rendu actuel (le BON ordre, à conserver) :
`SymptomTint(albédo)` → puis `HueShift` / `DrawVolumeEllipse` (lumière + volume).
Le symptôme est la **couleur de base**, l'éclairage passe par-dessus. Le risque
n'est pas l'ordre mais l'**amplitude** du hue-shift froid quand un colorant fort
est présent. `_colorAmount` (dans `PlantRenderer.cs`) mesure justement la force du
colorant dominant (0 = tissu sain).

## Travail

### A. Atténuer le hue-shift froid quand un symptôme colore fort (repli §5)

- Repérer où le hue-shift d'ombre/volume s'applique aux feuilles (`DrawVolumeEllipse`
  / `HueShift` côté `PlantRenderer.Palette.cs` + `.Leaf.cs` nervures).
- **Repli conçu** : réduire la force du hue-shift FROID (sud→nord) ∝ `_colorAmount`
  — quand un symptôme colore franchement le limbe, on ne le laisse pas reverdir/
  bleuir au point de devenir illisible. Garder un hue-shift PLEIN sur tissu sain
  (`_colorAmount = 0` → comportement SS² inchangé, pas de régression esthétique).
- Implémentation suggérée : un facteur `shiftScale = Mathf.Lerp(1f, K, _colorAmount)`
  (K < 1, p.ex. 0.5, à régler au F5) multipliant l'amplitude du shift froid. Rester
  **surgical** : ne pas refondre la palette, juste borner l'amplitude sous symptôme.
- ⚠️ Cas `ombre` (T1) : son délavé `b8c8a0` est proche du froid du hue-shift —
  vérifier qu'il reste DISTINCT côté nord. Si l'atténuation ci-dessus ne suffit pas,
  relever légèrement la valeur/chaleur de `b8c8a0` (note §5 de la conception).

### B. Protocole de diagnostic C2/C3 (livrable = doc, pas de mécanique)

Le §6 demande un tableau **cause → attendu écran → verdict** à instrumenter avec
les bancs d'essai (oracle vert moteur ↔ écran muet = bug rendu C#). NE PAS coder
de nouveau système : produire/compléter un **mémo de protocole F5** (dans la
clôture `00_etat.md`, ou un court `docs/conception/` si Nico préfère) listant :
- **C2** (asphyxie) : vérifier que l'**intensité** d'asphyxie se LIT à l'écran
  (banc `asphyxie_argile`) — teinte brun-vert proportionnelle, pas binaire.
- **C3** (ravageurs) : comparer **témoin vs infesté** (banc `infestation_ravageur`)
  — le criblage doit être visiblement plus dense côté infesté.
- Pour chaque : cause moteur, banc qui la force, attendu écran, verdict (OK / bug
  rendu → dette ciblée).

## Vérifications

1. `dotnet build Symbiose.csproj` → **0 erreur, 0 warning**.
2. Golden inchangé : `cd data/code && python3 -m tests.test_golden` → `2ab026ad…`.
3. Relecture : tissu SAIN (`_colorAmount = 0`) garde le hue-shift SS² PLEIN
   (aucune régression sur les plantes non stressées).

## Clôture (MAJ `00_etat.md` → SPRINT CLOS)

- Passer T3 ✅ + bannière **🏁 SPRINT SÉMIOLOGIE VISUELLE — CLOS** dans `00_etat.md`.
- §REPRISE : entrée T3 = atténuation hue-shift (facteur K retenu), ajustement
  éventuel de `b8c8a0`, mémo protocole C2/C3, hash golden vérifié, `dotnet build` vert.
- **Bilan dette** : marquer **D48 levée** + **dette 0.5.2 levée** (mapping `ombre`,
  faite en T1) dans `DETTE.md`. Vérifier le suivi D47 (C2/C3 désormais
  instrumentés → mettre à jour son statut).
- **Verdict F5 attendu (à écrire pour Nico)** : parcourir les bancs `ombre_dense`,
  `asphyxie_argile`, `infestation_ravageur` ; chaque symptôme reste lisible côté
  nord (pas de reverdissement/bleuissement) ; tissu sain inchangé vs SS². Verser
  tout bug rendu confirmé en dette ciblée.
- **Journal** : écrire une entrée de clôture `journal/NN_2026-…_sprint-semiologie-visuelle-CLOS.md`
  + l'indexer dans `journal.md` (mémoire partagée de fin de sprint).
- Commit (ex. `feat(rendu) : T3 cohérence palette + diagnostic C2/C3 — SPRINT CLOS, D48 levée`).
