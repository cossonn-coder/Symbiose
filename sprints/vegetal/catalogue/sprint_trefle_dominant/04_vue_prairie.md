# ④ Vue : tapis de trèfle, quatre feuilles, formes des neuves — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (bilans ① à ③), conception §3.

## Objectif

Un trèfle qui ressemble à du trèfle, un tapis et pas des tiges isolées, et trois espèces neuves reconnaissables.

## À faire

1. **Regarder d'abord** : capture du trèfle actuel `tools/capture_vm.sh -b full -w 30 -z 8`, et lire le chemin de dessin d'une herbe : `visuals/PlantRenderer.cs`, `PlantRenderer.LeafOutline.cs`, `PlantRenderer.Organs.cs` (288 LDC), `PlantRenderer.Flower.cs`.
2. **Trèfle** : feuilles basses à trois folioles arrondies, tige courte, fleur en boule blanche ; plusieurs ramets d'un plot se lisent en tapis continu. Rien par plante qui multiplie les draw calls : lot existant.
3. **Quatre feuilles** : quatre folioles sur le pied signalé par le pont, lisible à ×8 et plus, à peine décelable à ×4. Le clic de récolte fonctionne ; retour par la Vigueur et le carnet, pas de marqueur HUD.
4. **Neuves** : dactyle en touffe haute à panicules, fétuque en brins fins, plantain en rosette à épi, sur le patron de `LeafOutline` et des palettes d'organes. Ortie : vérifier qu'elle se lit bien. Ajouter les trois à tout registre C# concerné (`grep Taraxacum visuals`), tailles de fichier surveillées.
5. **Mesure** : captures `full`, ×1, ×4, ×8, ×16, s9, s20, s34, an 3. Lire les PNG. `tools/perf_vm.sh` avant/après : draw calls et FPS `[n=…, VM]`, budget : draw calls constants.
6. `dotnet build Symbiose.csproj` vert.
7. **Clôture** : `00_etat.md` §F5, ressenti de 2 minutes : la prairie bouge-t-elle d'une année à l'autre ? Le trèfle ressemble-t-il à du trèfle ? Trouver un trèfle à quatre feuilles fait-il plaisir ?

## Golden

**INTACT** (vue pure).

## NE PAS

Modifier le moteur. Redessiner les autres plantes (D118). Lancer `tests/test_epaisseur_500ans.py`.
