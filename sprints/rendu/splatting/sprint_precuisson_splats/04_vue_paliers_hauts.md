# ④ Vue Godot : les pièces splats aux paliers ×4 → ×32

Lire d'abord `docs/rendu/splatting/conception_precuisson_splats.md` (§3-4) et
`00_etat.md` (format, échelles, manifeste, mesures des ①②③).

## Existant (vérifié 2026-11-20)
- Planches + manifeste produits par ②③ (chemin et format dans `00_etat.md`).
- Paliers hauts : `visuals/PlantRenderer.PaliersHauts.cs` (×4 masses de feuillage
  + points ; ×8 organes ; ×16 symptômes ; ×32 intime) ; les organes sont dessinés
  dans leurs partials (`PlantRenderer.Leaf.cs`, `.LeafOutline.cs`, `.Flower.cs`,
  `.FleurSnes.cs`, `.PiecesFleur.cs`, `.Organs.cs`, `.FruitMur.cs`,
  `.FruitsArbre.cs`, `.FleursArbre.cs`, ports `.Port*.cs`, `.Houppier.cs`).
- Cuisson en jeu : `visuals/PlantBaker.cs` (pinceau, pages d'atlas communes
  `AtlasPages.cs`, poses de vent, file à budget `BakeQueue.cs`) ; palette indexée
  `visuals/PaletteIndexee.cs` + `palette_indexee.gdshader`.
- Textures du projet : chargées par `GD.Load<Texture2D>` (`core/SpriteLoader.cs:78`) ;
  les PNG versionnés ont un `.import` en `compress/mode=0` (sans perte),
  `mipmaps/generate=false` (ex. `assets/sprites/plants/basilic/basilic.png.import`).
  Politique `.uid` : `.gitignore` (D63, CLAUDE.md).
- Banc d'observation : `planche_especes` (`data/code/bancs/planche_especes.py`, une
  plante adulte par espèce, fleurs et fruits posés) ; capture sans écran sur la VM :
  `tools/capture_vm.sh -b planche_especes -z <palier> -c X,Y -o <dossier>` et
  `-l` (planche des paliers ×0,5→×32). Lire son en-tête.

## Objectif
1. **Charger les planches** dans la vue. Les codes par pixel doivent arriver
   INTACTS au shader (sans perte, sans filtrage, sans mipmap) : choisir le mode de
   chargement (import Godot ou lecture directe) et le JUSTIFIER, y compris pour un
   futur export du jeu (packaging t7). Vérifier qu'un import Godot sur la VM
   (capture) produit bien les mêmes octets.
2. **Assembler** : aux paliers ×4 → ×32, là où la vue dessine aujourd'hui une
   feuille, une masse de feuillage, une fleur, un fruit, un bourgeon ou (si ③ l'a
   livré) un tronçon de bois, poser la pièce splat :
   - choisie par **forme** (table « nom vue → recette » du manifeste), **vue la
     plus proche** de l'orientation 3D de l'organe dans le repère caméra
     (rotation D35 et pose de vent comprises), **variante au hash** (déterminisme),
     **degré de trou** selon l'état de dégâts déjà lu par la vue (D5) ;
   - posée à son **point d'attache**, au pixel entier ;
   - teintée par le **n° de palette** que la vue calcule déjà (espèce × saison ×
     santé × givre × maturité) : rien ne change dans le calcul des couleurs.
   Les couleurs de symptômes (nécrose, taches, givre) restent dessinées comme
   aujourd'hui (D5). L'ancien dessin vectoriel reste dans le code derrière un
   interrupteur (règle « conserver le code », mémoire `feedback_conserver_code`),
   pas supprimé.
3. **Coût** : mesurer avant/après le temps de cuisson par plante et la mémoire
   vidéo des planches (le rapport perf existant : touche Z / F4, cf.
   `world/WorldView.PerfReport.cs`) ; si ×16/×32 pèsent lourd, charger les planches
   d'un palier à la demande.
4. **Captures VM** du banc `planche_especes` à ×4, ×8, ×16, ×32 avant/après,
   examinées (outil Read) et rangées dans `00_etat.md` (chemins).

## Golden
**INTACT** (aucun fichier moteur). `dotnet build Symbiose.csproj` vert, 0 avertissement nouveau.

## Ne PAS faire
Toucher aux paliers ×0,5-×2 (c'est ⑤), au moteur, aux recettes (si une pièce
manque ou est fausse, la noter pour un retour en ②/③) ; supprimer l'ancien dessin.

## F5 (recette pour Nico, à écrire dans `00_etat.md`)
Banc `planche_especes`, ×4 → ×32, rotation de caméra (D35), vent fort : les
organes ont du volume, la lumière suit le soleil, aucune pièce ne « saute » en
tournant, la taille au segment marche toujours (`tailler`).
