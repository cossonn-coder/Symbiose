# Entrée de conception — sprint « plante assemblée »

> Note d'entrée, **pas une conception figée** : matière brute à durcir en
> `/conception` (écrite le 2026-10-19 à la clôture du sprint PERF VUE, d'après le
> F5 de Nico). Bilan chiffré : `sprints/perf/lod/sprint_perf_vue/00_etat.md`
> (sections « Étalonnage PC reçu » et « F5 ressenti — réponses de Nico »).

## 1. Ce que Nico a dit (F5 du 2026-10-19, verbatim résumé)

- **×4 est le zoom où l'on a envie de rester.** ×2, ×1 et ×0,5 sont « horribles avec
  les gros blobs verts à la place des plantes ».
- Les **détails des feuilles** (×8 et plus) sont beaucoup plus visibles qu'avant, mais
  **il ne sait pas ce qu'il observe** (liseré brun autour des feuilles, taches noires).
- La **vie macro** n'est pas visible et ça ne le dérange pas ; **ce qu'il voit, il ne
  sait pas l'identifier**. Il ne voit pas les pullulations et ne sait pas où regarder.
- Fluidité : « beaucoup plus fluide, mais ça chute à moins de 10 FPS parfois ».

## 2. Trois axes à concevoir

### A. Silhouettes par palier au lieu de blobs (cœur du sprint)
Kit de sprites d'éléments réutilisables, silhouettes lisibles à ×0,5-×2, pixels plus
fins. Objectif : que les paliers bas cessent d'être repoussants, ×4 restant le zoom
de référence.

### B. Perf : deux chantiers mesurés, à absorber (D109)
1. **×4 à 60 FPS** : il reste ~12 ms par image, tout en rendu CPU (28,7 ms pour
   2 044 draw calls, ~14 µs chacun [PC, n=1]). Viser ≲ 1 000 draw calls à ×4.
   Regrouper les plantes cuites (D109 d) ne couvre qu'environ 400 draw calls : il
   faut **ventiler les ~1 600 autres sur le PC** (la VM llvmpipe ne réagit pas au
   nombre de draw calls de la même façon).
2. **Chute sous 10 FPS en accéléré** (Continu 3 s/semaine, ×8 : 5 FPS, 199 ms par
   image, seulement 936 draw calls [PC, n=1]) — ce n'est pas le nombre de draw calls.
   Indice : tick serveur s34 = 2 354 ms contre ≤ 1 495 ms au banc nominal du même
   jardin [n=1 chacun] → **hypothèse** de contention CPU Python ↔ Godot sur 2 cœurs
   (priorité réduite du serveur jamais vérifiée sous Windows). Suspects secondaires :
   `ForagerLayer` (70 butineurs, jamais optimisé), arrivée des semaines toutes les 3 s.
   Le rapport F4 n'a pas les postes : **mesurer d'abord** (banc E en mode accéléré au PC).

### C. Comprendre ce qu'on observe — légende des signes (décision de Nico)
- **Carnet** = ce qui est **observé** (« bord des feuilles bruni sur la tomate,
  semaine 34 »), voix descriptive.
- **Encyclopédie** = ce qui est **confirmé et appris** (le signe relié à sa cause).
  Cohérent avec le carnet descriptif → interprétatif (maîtrise) et la philo #5-#6.
- **Légende technique au survol de la souris**, pour les **plantes ET les animaux** :
  info-bulle qui nomme ce que le pointeur désigne (signe foliaire, bête). Affichage
  technique, hors fiction — à étiqueter comme tel, comme F6.
- Signes foliaires actuels (`visuals/PlantRenderer.PaliersHauts.cs`, dès ×16) :
  bord brun-noir = gel ; bord beige-brun = sécheresse ; petits trous sombres =
  ravageurs ou grêle ; petites taches brun foncé = maladie fongique.
- Existant à relire avant de concevoir : `docs/narration/semiologie/`
  (`conception_semiologie_visuelle.md`, `conception_semiologie_foliaire.md`) et
  `docs/narration/voix/conception_voix_narratives.md`. Le survol existe déjà
  (`G survol gènes`) : réutiliser plutôt que doubler.

## 3. Petit bug à embarquer
Légende F1 : la ligne sous « I vie macro (1 bête par espèce… » est coupée en bas de
l'écran (`world/WorldView.Hud.cs`, ~ligne 188).

## 4. Questions ouvertes pour la conception
- A, B, C dans un seul sprint ou C à part (narration ≠ rendu) ?
- Légende au survol : quel palier minimum, et que nomme-t-elle avant la maîtrise
  (un nom brut ? « tache sombre » ?) sans court-circuiter la méthode scientifique ?
