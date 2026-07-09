# T4 — Décor d'ambiance : ossature (VUE C#, golden inchangé)

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` + ce fichier.
> Conception : `docs/conception/CONCEPTION_RENDU_AMBIANCE.md` §5.1.

## Objectif
Poser l'**ossature du décor** autour du jardin : des **zones organiques sinueuses**
(forêt / rivière / falaise / **prairie fleurie par défaut**) réparties **par seed**,
plus les **chemins entre tuiles enherbés**. Cosmétique aujourd'hui, **extensible
demain** (couture `SurroundingsProfile`). Les MOTIFS détaillés (arbres, eau, roche)
sont le tronçon T5 — ici on pose l'**assise** : placement, tracés, teintes de base.

## Fichiers à toucher
- **Neuf** : `visuals/DecorLayer.cs` — Node2D **derrière** le sol (ZIndex négatif,
  **hors picking**), ajouté au monde (`AddWorld`) et **reconstruit à la rotation
  D35** comme `_ground` (positions en cm monde → `WorldToScreen` ⇒ suit le monde).
- `world/WorldView.cs` (ou le partial de build du monde) : instancier/brancher
  `DecorLayer` au build, le reconstruire au rebuild rotation. Lire comment
  `_ground` et la boussole cardinale sont construits/retournés (`WorldView.Monde.cs`).
- `visuals/Palette16.cs` : teintes de base (vert prairie, vert gazon chemin, bleu
  eau, gris roche, vert forêt lointaine).
- `world/WorldView.Monde.cs` : les **chemins** entre tuiles = aujourd'hui le fond
  gris `FondPierre` → basculer en **vert herbe** (gazon), grain léger.

## Modèle
- **`SurroundingsProfile`** (struct C#) calculée depuis le **seed du terrain**
  (lire le seed dans le snapshot s'il y est ; sinon hash stable de la disposition
  des tuiles). Pour chaque **secteur** autour du jardin (les 4 bords cardinaux, ou
  une découpe plus fine) : le **motif** (Foret/Riviere/Falaise/Prairie) et son
  **tracé de frontière sinueux** (ondulation par **bruit déterministe**, JAMAIS
  une ligne droite). **Prairie = défaut** des côtés non tirés.
- **Couplage rivière ↔ falaise** : si un secteur porte une rivière, la falaise qui
  la borde en dérive ; **pente de falaise** (douce/verticale/déversante) tirée du
  seed. (Le rendu fin est en T5 ; ici on fixe la donnée dans le profil.)
- **Zone décor** = une bande AUTOUR de `[0, WorldCm]` (marge extérieure), derrière
  le jardin. Rendu de base = aplats teintés **volumés** (≥ 2 valeurs, hue-shift
  sud) pour valider placement et tracés ; les détails viennent en T5.
- **Chemins enherbés** : remplacer le gris pierre inter-tuiles par un vert gazon
  (grain déterministe).

## Couture d'extensibilité (important, cosmétique MAINTENANT)
`SurroundingsProfile` doit être **structurée pour être alimentée plus tard par le
pont** (friche périphérique / extensions par maîtrise / parcelles d'accueil) SANS
réécriture : le calcul C#-depuis-seed d'aujourd'hui est le **repli par défaut**.
Prévoir un point d'entrée unique (ex. `BuildProfile(seed)` → remplaçable par
`BuildProfile(snapshotSurroundings)`). Ne PAS câbler le pont ici (dette D73).

## Contraintes
- **Statique** (build + rebuild rotation), **cullable**, **hors picking** (le
  décor ne doit pas intercepter les clics du jardin). **Déterminisme** total.
- **D35** : tout en cm monde → `WorldToScreen`, reconstruit à la rotation.

## Golden / build
- Vue pure → **golden inchangé**. `dotnet build` vert.

## Ne PAS faire
- Pas de terraforming / interaction (dette D73). Pas de lien pont (cosmétique).
- Pas de tracés droits. Pas de `Random`. Ne pas rendre le décor cliquable.

## F5 Nico
Un entourage sinueux différent selon le seed ; prairie par défaut ; chemins verts.
