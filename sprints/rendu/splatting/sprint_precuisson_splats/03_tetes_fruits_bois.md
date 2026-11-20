# ③ Têtes, fleurs, fruits, bourgeons, bois

Lire d'abord `docs/rendu/splatting/conception_precuisson_splats.md` (§3-4) et
`00_etat.md` (format et mesures du ①, bibliothèque du ②).

## Existant (à lire, ne pas modifier)
- `visuals/PlantRenderer.PortsFiches.cs` : `enum FormeTete` (14 : Capitule,
  Bouquet, Chapelet, Epi, Ombelle, Boule, Grappe, Soleil, Etoile, Pendante,
  Corolle, Trompette, Papillon, Aucune).
- Fleurs : `PlantRenderer.Flower.cs`, `.FleurSnes.cs`, `.PiecesFleur.cs`,
  `.FleursArbre.cs`, `.GerbesFleurs.cs` ; fruits : `PlantRenderer.Organs.cs`
  (`FruitPoint`, couleur ∝ maturité), `.FruitMur.cs`, `.FruitsArbre.cs` ;
  fleurons du kit des paliers bas : `PlantRenderer.Kit.cs` (point, bouton, étoile).
- Bois : `DrawSegments` (paliers hauts) et tiges des paliers bas
  (`PlantRenderer.Assemblee.cs`) ; arbres `PlantRenderer.Houppier.cs`, `.Arbres.cs`.
- Le prototype a déjà une grappe de tomates avec calices (`docs/rendu/splatting/prototype/tomate.js`, fonction `grappe`).

## Objectif
1. Une recette par **forme de tête** et par **forme de fruit** réellement dessinée
   par la vue (inventorier ce que les fichiers ci-dessus dessinent : globe, baie,
   gousse, pomme… — ne cuire que ce qui sert), plus les **fleurons** du kit et les
   **bourgeons**. Un fruit est cuit UNE fois : sa maturité est une affaire de
   palette (vert → mûr → pourri), pas d'image (conception §3).
2. **Bois** : des tronçons d'écorce (cylindre court, quelques diamètres, vues V)
   pour les paliers où le bois est large (×8 et plus, vérifier les épaisseurs en
   px). **Mesurer la couture** : poser 5 tronçons bout à bout selon un vrai
   segment de pommier (`data/code/tools/export_structure.py`, spécimen « Pommier · an 10 »)
   sur la planche de contrôle et regarder les joints. Si les joints se voient,
   ne pas livrer le bois en splats : le consigner (la vue gardera son bois
   dessiné) — pas de bricolage.
3. Planche de contrôle + poids + temps, comme ②.

## Golden
**INTACT**.

## Ne PAS faire
Toucher au C# ; cuire une variante de couleur (maturité, saison) ; régénérer les
feuilles du ②.
