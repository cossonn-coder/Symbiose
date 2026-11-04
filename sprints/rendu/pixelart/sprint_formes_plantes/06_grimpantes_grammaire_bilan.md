# ⑥ Haricot, tomate, lierre, jasmin, grammaire, bilan — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (tous les bilans), conception §4.2, §4.5, §6, §7 ; `docs/rendu/pixelart/etude_brief_da_16bits.md` ; `sim/grimpe.py` et le champ `support` du pont ; `PlantRenderer.Flower.cs`, `PlantRenderer.Leaf.cs`.

## Objectif

Les 4 dernières espèces justes, et fleurs et feuilles en grammaire SNES partout.

## À faire

1. **Haricot, port volubile** : spires autour du support à la hauteur du pont, en grammaire SNES ; sans support, tas bas. Feuilles trifoliées, gousses. Vérifier d'abord ce que lit `sim/grimpe.py` et ce qu'envoie le pont.
2. **Tomate, lierre, jasmin** : gardent leurs segments et leur taille au segment. Recette de feuilles et fleurs d'après leur fiche ; supprimer l'aspect bonsaï aux paliers bas s'il persiste. Lierre : feuilles lobées, tapis au mur. Jasmin : folioles, petites fleurs blanches.
3. **Fleurs** (D118 B) : grammaire SNES pour toutes, y compris sur les arbres et les plantes déjà faites si le chemin est commun ; contour sélectif, 3 à 4 tons.
4. **Feuilles à ×32** (D118 B) : plus d'ovale vert uni, nervures à l'échelle. **Vrilles** : plus de spires hors grammaire.
5. **Mesure finale** : `mesures/apres.md`, en regard de `avant.md` : `mesure_silhouettes` sur les 40, à ×1 et ×4, cible conception §6 ; hauteur dessinée / `height_cm` ; `mesure_da` ; `perf_vm.sh` avant sprint / après sprint sur `full`. Captures de `full` à ×1, ×4, ×8, ×16, ×32, s9, s20, s34, s45. Lire les PNG et dire ce qui reste faible, sans arrondir vers le succès.
6. **Chiffre d'effet en jeu** : combien d'espèces présentes dans `full` en an 2 passent par un port, et capture d'une tuile à ×4 où on les distingue.
7. `dotnet build Symbiose.csproj` vert, golden, `tests/simserver`.
8. **Clôture** : `00_etat.md` §F5 (ressenti, court : une minute par palier, reconnaît-on sans info-bulle basilic, tournesol, blé, fraisier, lavande, courgette, haricot ? ombres ? tailler une menthe). `journal.md` + entrée `journal/` ; `DETTE.md` (D118 réduite au §7 de la conception, limite « taille sur trèfle » retirée de D127 si vérifiée, cadence et CPU du ⑤ reportés) ; `BACKLOG.md`.

## Golden

**INTACT** (vue pure).

## NE PAS

Traiter le hors-périmètre (conception §7), même « au passage ». Lancer `tests/test_epaisseur_500ans.py`.
