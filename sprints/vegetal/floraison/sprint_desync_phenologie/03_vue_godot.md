# Tronçon ③ — Vue Godot : fleurs & teinte automnale par-plante + détail dès ×1 (C#)

> Kickoff autosuffisant. Lis `CLAUDE.md` (racine) + `00_etat.md` (ce dossier) +
> `docs/vegetal/floraison/conception_desync_phenologie.md` (§1bis, §3, §5 tronçon ③),
> puis exécute. **Prérequis : tronçons ① et ② CLOS** (le snapshot expose
> `floraison` et `automne` par-plante).
> Filet de compilation : `dotnet build Symbiose.csproj` (le F5 visuel reste à
> Nico). GDScript INTERDIT — tout en C#, namespace `Symbiose`.

## Objectif
Débrancher la vue de la **saison globale** (cause moitié-cachée du bug, doc §1bis)
et rendre le détail visible dès le zoom ×1 :
1. **Fleurs** dessinées ∝ `floraison` **par-plante** (remplace le proxy saisonnier
   `_structure.Organ == "flower"`).
2. **Teinte automnale** du feuillage ∝ `automne` **par-plante** (remplace le switch
   `season` global dans `LeafColor`).
3. **LOD** : segments ET organes visibles dès ×1 (seuils `4→1` et `8→1`), la
   silhouette n'étant gardée qu'au palier « monde entier » ×0.5. Culling = filet
   perf déjà en place.

## Principe (NE PAS dévier)
- **Golden intact** : ③ est 100 % C#/rendu, il ne touche pas le moteur Python.
- **Lecture pure du snapshot** : on lit `floraison`/`automne` fournis par ②, on ne
  recalcule aucune phénologie côté vue.
- Tolérance de version : un snapshot pré-② n'a pas les clés → défauts sûrs (fleur
  = proxy actuel en repli, `automne` = 0). Garder la lecture `ContainsKey` comme
  pour `fruits`/`organ` (`core/PlantStructure.cs::FromSnapshot`).

## A. Lire les deux hints dans le DTO
Fichier `core/PlantStructure.cs`.
1. Ajouter deux champs au DTO `PlantStructure` (près de `FoliageDensity`/`Organ`) :
   ```csharp
   public float Floraison;    // 0..1, scalaire moteur (②) — pilote la densité de fleurs
   public float Automne;      // 0..1, phénophase de coloration par-plante (②)
   ```
2. Dans `FromSnapshot` (lecture tolérante, comme `fruits`/`organ`) :
   ```csharp
   if (plant.ContainsKey("floraison"))
       ps.Floraison = (float)plant["floraison"].AsDouble();
   if (plant.ContainsKey("automne"))
       ps.Automne = (float)plant["automne"].AsDouble();
   ```
   Défauts `0f` si absents (snapshot pré-②).

## B. Fleurs ∝ floraison par-plante
Fichier `visuals/PlantRenderer.Organs.cs`, bloc `--- FLEURS ---` (~ligne 300).
Remplacer la porte proxy-saisonnier :
```csharp
if (_structure.Organ == "flower")           // AVANT : proxy REPRO_BY_SEASON global
```
par un seuil sur le scalaire moteur par-plante :
```csharp
if (_structure.Floraison >= FloraisonSeuil) // APRÈS : état moteur désynchronisé
```
- `FloraisonSeuil` : constante (~0.5, à côté des autres constantes de rendu du
  fichier). Optionnel/bonus si simple : moduler le **nombre** ou la **taille** des
  fleurs par `_structure.Floraison` (floraison montante = quelques fleurs, pic =
  pleine floraison). Rester sobre — le seuil binaire suffit à casser la synchronie ;
  ne pas sur-concevoir.
- La silhouette de fleur reste `DrawFlowerShape` par famille (inchangée).
- **Repli** : si le snapshot n'a pas `floraison` (champ = 0), aucune fleur — le
  proxy `Organ` n'est plus consulté (② est le prérequis ; on ne garde pas deux
  chemins). Documenter ce choix en commentaire.

## C. Teinte automnale ∝ automne par-plante
Toujours `visuals/PlantRenderer.Organs.cs` + `LeafColor` (défini ~ligne 166 du
même fichier).
- `DrawOrgans` lit aujourd'hui `string season = WorldView.CurrentSeason;` (~ligne
  203) et le passe à `LeafColor(pal, season, h)` (~ligne 261). `LeafColor` fait un
  `switch (season)` avec un cas `"automne"` (~ligne 168-171) → **flip global** au
  passage de saison.
- **Remplacer** ce switch global par un **mélange continu** piloté par
  `_structure.Automne` (par-plante) : couleur d'été (feuillage vert de la palette)
  → couleur d'automne (`AutumnLeaves[...]`) interpolée par `automne ∈ [0,1]`.
  Signature suggérée : `LeafColor(pal, _structure.Automne, h)` (remplacer le
  paramètre `season` par le scalaire `float automne`). Ainsi :
  - `automne = 0` → teinte estivale (comportement actuel été).
  - `automne` monte → rougissement **progressif**, à la **semaine propre** de la
    plante (donc étalé entre individus).
  - `automne = 1` → pleinement automnal, juste avant que `FoliageDensity` ne fasse
    disparaître la feuille.
- **Printemps clair** (×1.25, cf. commentaire ~ligne 163) : la légère éclaircie
  printanière peut être conservée si tu la re-câbles proprement (bonus), mais la
  priorité est de **tuer le flip automnal global**. Ne pas régresser l'hiver : la
  disparition du feuillage est déjà gérée par `FoliageDensity` (0 en hiver caduc),
  indépendante de la teinte.
- Ne PAS casser `SymptomTint` (sénologie foliaire) ni le repli T3 `_coolShiftScale`
  posés autour de la boucle feuilles — la teinte automnale se compose AVANT eux
  (couleur de base), les symptômes restent posés par-dessus.

## D. LOD — détail dès ×1
Fichier `visuals/PlantRenderer.cs`.
```csharp
private const float SegmentDetailMinZoom = 4f;   // → 1f
private const float OrganDetailMinZoom   = 8f;   // → 1f
```
- Abaisser **les deux à `1f`** (doc §3, décision Q3). Résultat : segments et
  organes rastérisés dès ×1 ; seul le palier ×0.5 (« monde entier ») garde la
  **silhouette** (les gardes `WorldView.CurrentZoom < SegmentDetailMinZoom`, lignes
  ~408/417/463, basculent alors sous ×1 seulement).
- Vérifier qu'aucune autre logique ne suppose `SegmentDetailMinZoom == 4`
  (p. ex. `MacroLife.MinZoom = 4` est **indépendant** — ne pas y toucher).
- **Culling** (`WorldView.Camera.cs::CullPlants`) est le filet perf, déjà en place :
  ne rien y changer.

## Build (filet de compilation)
`dotnet build Symbiose.csproj` doit être **vert**. Corrige toute erreur de
compilation (signatures, casts Variant). Le F5 visuel reste à Nico.

## Golden
Aucune touche Python → `python3 -m tests.test_golden` **inchangé** (le relancer
par acquit de conscience, il ne doit pas bouger).

## Points de VÉRIF F5 (à consigner pour Nico — NE PAS auto-valider)
- **Détail dès ×1** : feuilles + segments lisibles au zoom ×1 (aire large × plantes
  minuscules). Si bruit sous-pixel / illisible → escape hatch : remonter un seuil
  d'un cran (documenté doc §3).
- **Perf** : FPS tenu à ×1 sur une scène chargée (culling = filet).
- **Désync VISIBLE** : fleurs qui sortent à des semaines différentes selon les
  pieds ; feuillage qui rougit/tombe de façon étalée ; **plus de flip** de tout le
  jardin au tick du passage de saison.

## Vérif de sortie
- `dotnet build Symbiose.csproj` vert.
- `python3 -m tests.test_golden` inchangé.
- Mettre à jour `00_etat.md` (§REPRISE + statut ③ CLOSE + liste des points F5),
  puis commit.

## Ne PAS faire
- Pas de GDScript. Namespace `Symbiose`. Un fichier = une responsabilité.
- Ne PAS recalculer la phénologie côté vue (lecture pure des hints ②).
- Ne PAS toucher au moteur Python ni re-figer le golden.
- Ne PAS toucher `CullPlants` ni `MacroLife.MinZoom`.
- Ne PAS lancer `test_epaisseur_500ans` (interdit).
