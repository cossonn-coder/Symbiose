# ⑥ Portraits : 3 par espèce, plantes entières en splats

Lire d'abord `docs/rendu/splatting/conception_precuisson_splats.md` (D3, D6, §5) et
`docs/rendu/splatting/prototype/` (le rendu visé : `tomate_final.png`).

## Existant (vérifié 2026-11-20)
- Outil `tools/splat/` + recettes d'organes (②③).
- Grammaire des espèces dans la VUE : `visuals/PlantRenderer.PortsFiches.cs`
  (une ligne par espèce, clé = nom de classe Python ; ports `FormePort`, feuilles,
  têtes, marques, couleurs ; palettes aussi dans `PlantRenderer.Organs.cs`),
  ports dessinés par `PlantRenderer.Port*.cs`, arbres par `.Houppier.cs` /
  `.Arbres.cs` ; fiches botaniques sources :
  `docs/vegetal/croissance/fiches_herbacees.md`.
- Espèces : 54 classes distinctes dans `data/code/plants/catalogue.py` (tables
  `PLANT_CATALOGUE`, `PERENNIAL_CATALOGUE`, `WEED_CATALOGUE`, `ESPECES_SPONTANEES`,
  `FLORE_SPONTANEE` — recompter).
- Structure moteur d'une plante : `data/code/tools/export_structure.py` (`_grow`).

## Objectif
1. Une recette **plante entière par port** (7 `FormePort` + arbres), paramétrée par
   la ligne de l'espèce. **La table des espèces n'est PAS recopiée à la main** dans
   l'outil JS : choisir une source unique (export de la table depuis le C# —
   `dotnet` est sur la VM —, ou lecture d'un fichier commun ; ne pas modifier la
   vue pour ça au-delà du strict nécessaire) et le justifier. Si l'espèce a une
   structure moteur parlante (tige, segments d'arbre), s'en servir comme squelette
   (esprit fidélité, comme le prototype).
2. **3 portraits par espèce** (D6) : jeune · mûre en pleine saison (fleurs/fruits si
   l'espèce en porte) · fin de cycle ou hiver (feuillage d'automne, nu, graines…
   selon l'espèce). Palette pleine et lumière cuite, comme le prototype (ce sont des
   illustrations, PAS au format palette indexée). Taille fixe commune, fond
   transparent ou uni (choisir selon ce que l'encyclopédie peut afficher).
3. Les portraits (162 prévus) rangés avec un manifeste (espèce → 3 fichiers) ; une
   **planche de contrôle** de tous les portraits, examinée espèce par espèce (outil
   Read) : signaler celles qui ne ressemblent pas à leur espèce.
4. Poids et temps de cuisson mesurés ; alerte D2 si ça dérape.

## Golden
**INTACT**.

## Ne PAS faire
Toucher au moteur ; inventer des espèces ; modifier les pièces du jardin (②③) ;
afficher les portraits en jeu (c'est ⑦).
