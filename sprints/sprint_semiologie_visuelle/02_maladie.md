# T2 — Signe `maladie` / taches cryptogamiques

> Lire d'abord `00_etat.md` (invariants) + `CONCEPTION_SEMIOLOGIE_VISUELLE.md` §3.
> Couche **B pure** (C#). Golden trivialement préservé, build C# vert, F5 = Nico.

## But

Le signe `maladie` a DÉJÀ sa teinte couleur (`ColorantTints["maladie"] = 8a6a4a`,
brun), mais **aucune texture**. Or un lavis brun uni ne rend pas le caractère
**ponctué** des cryptogames (taches, pustules) et se **confond** avec le brun-vert
uniforme de l'asphyxie. On ajoute un canal texture **« taches »** pour distinguer
visuellement `maladie` (ponctué) de `asphyxie` (uniforme) — lisibilité philo #5/#6.

## Travail

### A. Capter l'intensité `maladie` comme canal texture

Dans `visuals/PlantRenderer.cs`, `SetSymptoms` :
1. Déclarer le champ (à côté des autres canaux texture, après T1 = `..., _ombre`) :
   ```csharp
   private float _ravageurs, _gel, _grele, _drought, _ombre, _maladie;
   ```
2. Remise à 0 dans `SetSymptoms` + `case` dans le `switch (cause)` :
   ```csharp
   case "maladie": _maladie = it; break;
   ```
   ⚠️ Ne PAS retirer `maladie` de `ColorantTints` : la teinte brune reste (canal
   couleur), on AJOUTE seulement la texture (les deux canaux coexistent, D33).

### B. Semis de taches dans `DrawLeafDamage`

`DrawLeafDamage` (`visuals/PlantRenderer.Organs.cs` ~ligne 385) pose déjà le
**criblage** (ravageurs/grêle → trous `LeafHoleColor`) et les **bords gelés**.
Ajouter un bloc **taches** sur le même modèle, posé au **hash** (stable inter-frames) :

- `if (_maladie > 0f)` → un **semis de petites taches brun foncé** ∝ intensité.
- Nombre de taches ∝ `_maladie` (ex. `Mathf.CeilToInt(_maladie * 5f)`, à régler).
- Position de chaque tache : angle + rayon dérivés de `Hash01(salt + k, i, j)`
  avec un **salt neuf** non collidé avec le criblage (le criblage utilise 23/29 ;
  prendre p.ex. 37/41) — sinon taches et trous se superposent exactement.
- Plus PETITES que les trous de criblage (pustules ponctuées, pas des morsures) :
  rayon ~ `r * 0.10f` à `0.14f` (le criblage est à `r * 0.22f`).
- Couleur : brun foncé dédié (constante neuve, ex. `LeafSpotColor = new Color("4a3320")`
  ou réutiliser un brun sombre existant — choisir le plus lisible sur le limbe).
- **Additif, cumulable** sans conflit avec criblage/bords gelés (canaux texture
  indépendants — invariant §1/D33).

## Vérifications

1. `dotnet build Symbiose.csproj` → **0 erreur, 0 warning**.
2. Golden inchangé : `cd data/code && python3 -m tests.test_golden` → `2ab026ad…`.
3. Relecture : salt des taches ≠ salt du criblage (pas de superposition exacte) ;
   taches plus petites que les trous ; `maladie` garde sa teinte brune (couleur)
   EN PLUS des taches (texture).

## Clôture (MAJ `00_etat.md`)

- Passer T2 ✅ dans la table.
- §REPRISE : entrée T2 = champ `_maladie`, semis de taches (salt choisi, nombre,
  rayon, couleur), hash golden vérifié, `dotnet build` vert.
- **Verdict F5 attendu (à écrire pour Nico)** : sur une plante malade, le limbe
  brun doit désormais porter un **semis de petites taches sombres** ponctuées,
  visuellement DISTINCT du brun-vert UNIFORME de l'asphyxie. Banc d'essai à exhiber :
  un monde infesté de pathogène (si un banc `maladie` existe ; sinon vérifier
  qu'aucune régression sur asphyxie — qui reste un aplat).
- Commit (ex. `feat(rendu) : T2 signe maladie — semis de taches cryptogamiques`).
