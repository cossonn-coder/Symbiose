# ④ Vue : clé stable, gerbes et cuisson — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §5, `visuals/PlantRenderer.Kit.cs`, `.KitCodes.cs`, `.Assemblee.cs`, `.PaliersHauts.cs`, `.Organs.cs`, `.Bake.cs`, `.Ports.cs` (`DessinInchange`, `CleDuPort`), `.Arbres.cs` (`RecetteArbre`), `visuals/PlantBaker.cs`, `BakeQueue.cs`, `world/WorldView.Etalement.cs`.

## Objectif

Le socle qui rend la densité du ⑤ abordable, sans changer encore l'aspect des arbres (hors stabilité au hash).

## À faire

1. **Référence avant tout** : durée totale de cuisson, FPS, RAM sur `full` et sur un banc neuf `houppiers` (11 arbres isolés, 10 et 25 ans, à l'écart de la maison et des bords ; `foret_ports` n'est pas lisible : figuier à 1275,775, arbres à x 2275 > 2000) avec `tools/perf_vm.sh`. Vérifier la charge VM avant toute mesure de temps. `[n=…, VM, charge …]`.
2. **Clé stable** : `Hash01` reçoit aujourd'hui l'indice `i`, réindexé par `_rebuild` à chaque coupe. Clé dérivée de la base **et** de la direction quantifiées : deux segments frères partagent la même base, la base seule collisionne. Vérifier au code que base et direction ne changent plus après création, côté `data/code/sim/growth`, et le dire. Portée : `PlacerTouffes`, `AjouterTouffeAutour`, `DrawMassesFeuillage`, feuilles ×8 de `DrawOrgans`, `Lianes.cs`. Oracle : couper une branche ne déplace aucune feuille des autres branches (test C# ou capture avant/après).
3. **Atlas de gerbes** : partial neuf `PlantRenderer.Gerbes.cs`. Par forme de feuille, palier et variante au hash. Couche bois et couche feuilles séparées. Mêmes codes de palette que le kit. Chiffrer la RAM avant de fixer tailles et variantes ; à ×16 et ×32, pas de gerbe.
4. **Génération au chargement** : le jeu n'a pas d'écran de chargement à ce jour d'après un `grep` sur « Chargement » (à reconfirmer). Écran minimal dans la DA, sans chiffre (philo #5) : génération de l'atlas, puis cuisson du cadre de départ, puis ouverture du jeu. Vent : voir comment `PlantBaker` gère ses 8 poses, cuire ce qui est nécessaire au cadre.
5. **Recuisson si le dessin change** : étendre `DessinInchange` aux arbres, clé quantifiée (topologie, densité, floraison, fruits, symptômes, teinte). Un arbre inchangé ne repasse plus par `Invalidate`. Vérifier que l'automne et la santé restent vivants : ce sont des codes de palette, à confirmer au code.
6. **Mesures** après : durée totale de cuisson (critère arbitré par Nico), FPS, RAM, temps du chargement. Rapporter le nombre de recuissons par semaine avant/après.
7. `dotnet build Symbiose.csproj`, golden, `tests/simserver`, `tools/compte_ldc.py` sur les fichiers touchés. Bilan, commit.

## Golden

**INTACT** (vue pure).

## NE PAS

Toucher au moteur. Densifier ou modifier l'aspect : c'est le ⑤. Utiliser `Random`. Lancer `tests/test_epaisseur_500ans.py`.
