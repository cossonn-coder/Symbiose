# ③ Tiges à feuilles étagées — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (bilans ①②), conception §4.2, §4.5, §6 ; `fiches_herbacees.md`, socle `PlantRenderer.Ports*.cs`.

## Objectif

Les 12 espèces dressées se reconnaissent : tournesol, ortie, basilic, poivron, phacélie, bourrache, moutarde, armoise, chanvre, achillée, consoude, menthe.

## À faire

1. **Port tige** : nombre d'axes, ramification, phyllotaxie (opposée, alterne), étagement des feuilles, taille qui décroît vers le haut, sommet, tous paramétrés par la fiche. Le tournesol à gros capitule unique et l'achillée plumeuse en corymbe doivent sortir de la même grammaire.
2. **Feuilles** : formes neuves seulement si la fiche l'exige (chanvre palmé, ortie dentée, consoude large) ; d'abord `LeafShape`, `LeafOutline` et le kit.
3. **Paliers bas** : la silhouette distingue à ×1, sans masse en bonsaï.
4. **Mesure** : `mesure_silhouettes` (les 12 + couple menthe/basilic), captures de `full` et du banc à ×1, ×4, ×8, ×16, `mesure_da`, `perf_vm.sh` (conception §6). Lire les PNG.
5. `dotnet build Symbiose.csproj` vert, golden.

## Golden

**INTACT** (vue pure).

## NE PAS

Modifier le moteur. Écrire une fonction par espèce. Lancer `tests/test_epaisseur_500ans.py`.
