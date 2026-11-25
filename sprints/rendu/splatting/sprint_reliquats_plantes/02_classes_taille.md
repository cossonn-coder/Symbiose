# ② Classes de taille précuites

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, la conception (`docs/rendu/splatting/conception_reliquats_plantes.md`),
et dans `../sprint_precuisson_splats/00_etat.md` les comptes rendus ② (« TAILLE »), ③
(« Échelle des organes ronds », « TAILLE NOMINALE ») et ④/⑤bis (défauts de TAILLE). Outil :
`tools/splat/cuire.js` et `tools/splat/README.md`.

## Objectif
Aujourd'hui, une pièce est cuite à UNE longueur nominale par recette (ovale 9 cm, dentée
15 cm, globe 2 cm…). Résultat : certaines pièces sont 1,5 à 2 fois trop grandes (fraise,
courgette, myrtille de loin, haricot), d'autres trop petites (rosette de la molène).
Décision E8 de Nico : **3 classes de taille précuites par recette**, et la vue choisit la
plus proche de la taille réelle de l'organe.

## À faire
1. **Inventaire des tailles réelles** par recette : pour chaque recette, la plage des
   tailles que la vue demande (fiches d'espèce × stades). `tools/splat/portraits/table_cs.js`
   lit déjà les tables C# de la vue (FichePort, etc.) : le réutiliser plutôt que recopier.
   En déduire 3 tailles par recette (étagement géométrique qui couvre la plage, médiane au
   centre). Une recette à plage étroite peut n'en avoir que 1 ou 2 (à justifier).
2. **Échelle √2 des organes ronds** (③, écart 5) : la caméra rend un disque de r cm à
   r × 0,55 px/cm, la vue à r × 0,39. Corriger pour que la pièce ait la taille du dessin
   d'avant à rayon égal.
3. **Cuisson** : un nouvel axe de taille dans `cuire.js` (le champ `taille` / `empriseCm`
   existe pour le kit ; s'en inspirer, ne pas casser le kit des touffes). Le manifeste
   expose la taille en cm de chaque pièce. Recuisson complète en parallèle (`xargs -P`,
   modèle du sprint (a)), en arrière-plan. Déterminisme : deux cuissons donnent les mêmes
   octets (contrôler sur une recette).
4. **Vue** : `PlantRenderer.Splats.cs` / `SplatsOrganes.cs` choisissent la classe la plus
   proche de la taille réelle de l'organe posé. La taille réelle est celle que l'ancien
   dessin utilisait ; repérer où il la calcule, ne pas l'inventer.
5. **Poids** : `du -sh assets/splats` avant/après. Alerte et arrêt au-delà de 200 Mo
   (D2). Les régénérations alourdissent l'historique git : régénérer une seule fois.

## Mesures attendues
- Temps de cuisson (mur, CPU), nombre de pièces, poids.
- Captures avant/après (Maj+F11 ou `SYMBIOSE_SPLATS=0` pour l'ancien dessin) : fraisier ×8,
  courgette ×16, myrtille et haricot ×1/×2, molène ×2. La taille d'une pièce doit être
  proche de celle de l'ancien dessin.
- Planche de contrôle des 3 tailles d'une recette, dans `mesures/`.

## Ne pas faire
- Ajouter des détails ou des recettes (c'est ③ et ④).
- Toucher `data/code/` ou `tools/splat/vendor/`.
- Lancer `test_epaisseur_500ans`, appeler DeepSeek.

## Fin
Build vert, golden `bce813af…` intact, LDC. Compte rendu ② dans `00_etat.md`, avec la
table recette → 3 tailles.
