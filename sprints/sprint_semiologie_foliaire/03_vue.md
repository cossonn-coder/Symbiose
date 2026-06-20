# Tronçon ③ — Vue C# (canal couleur + canaux texture/forme)

> Sprint « sémiologie foliaire ». Conception :
> `docs/conception/CONCEPTION_SEMIOLOGIE_FOLIAIRE.md` (§3). Lire la conception
> + faire ①② d'abord. **F5 visuel = Nico** (Godot pas sur la VM).

## Objectif
Consommer `leaf_symptoms` côté Godot pour rendre les symptômes, en SÉPARANT deux
canaux pour que le cumul multi-signes reste lisible (pas de teintes boueuses).

## Travail
1. `visuals/PlantRenderer.cs` : retirer `_chlorose` / `SetChlorose(bool)` et
   généraliser `Chlorotic()` → une lecture de `leaf_symptoms`.
   - **Canal couleur** : choisir le symptôme COLORANT de plus forte intensité
     parmi `chlorose` (jaune inter-nervaire) / `asphyxie` (brun terne) /
     `secheresse` (désaturé) / `senescence` (jaune-rouge) / `maladie` (taches).
     Lerp de la couleur de feuille/apex/silhouette vers la teinte, ∝ intensité.
   - **Canaux texture/forme** (ADDITIFS, indépendants de la couleur) :
     `ravageurs` = limbe criblé/troué ; `grele` = limbe déchiré ; `gel` = bords
     noircis ; `secheresse` = géométrie tombante. Commencer simple (au moins le
     criblage ravageurs + la teinte) ; le reste peut être incrémental.
   - **Fallback** : `cause` inconnue → aucun effet (forward-compatible).
2. `visuals/PlantRenderer.Organs.cs:131` : adapter l'appel `Chlorotic(...)` au
   nouveau canal couleur.
3. Côté appelant (là où `SetChlorose` était poussé depuis le snapshot, chercher
   l'usage) : pousser `leaf_symptoms` à la place. Lecture TOLÉRANTE (champ absent
   sur un vieux snapshot → liste vide → plante saine).

## Vérifs
- `dotnet build Symbiose.csproj` vert (filet de compilation VM).
- F5 Nico : une plante chlorosée jaunit ; injecter (debug) un sol alcalin /
  une pression ravageur et vérifier la lisibilité du cumul (jaune + criblé).
- Pas de régression : plante saine = vert plein, aucune teinte parasite.

## Sortie
MAJ `00_etat.md` (③ clos). Clôturer **D33** dans `DETTE.md`. MAJ `journal.md`
(+ entrée `journal/`) : sprint sémiologie foliaire terminé. Commit.
