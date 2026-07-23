# T4 — Transitions, échelle/LOD détail & banc d'observation F5

**Sprint :** LISIBILITÉ DÉCOR (reprise D58) · **Type :** rendu / ambiance · **Golden : INCHANGÉ.**
Lire d'abord `00_etat.md`. T1 (forêt) + T2 (rivière) + T3 (falaise) faits. **Dernier tronçon = la
vue Godot** : on soigne les transitions, on recale l'échelle des détails, et on pose le **banc F5**.

## Contexte minimal
Deux problèmes transversaux restent après T1-T3 :
1. **Démarcation décor↔jardin** molle : le décor doit se distinguer nettement du sol cultivé
   (lisière/berge/pied de falaise franc), pas fondre dedans.
2. **Échelle détail/distance** : les détails fins (reflets, fleurs de prairie `DrawPrairie`, chevrons
   du bouleau) sont calibrés vue proche et invisibles à la distance d'observation (zoom large où le
   décor est justement vu). Le décor est visible `CurrentZoom ≤ MaxZoom=4` (zoom steps
   0.5/1/2/4/8/16/32).
Rendu C# pur (`_Draw` statique) — **aucun moteur, aucun golden touché**.

Fichier moteur = source de vérité : **NON concerné**. Ne PAS lancer `test_golden`.
Filet : `dotnet build Symbiose.csproj` (0 erreur / 0 warning).

## Objectif
Décor **démarqué** du jardin sur les 4 motifs, détails **calibrés à la distance** via un LOD 2
niveaux, et un **banc d'observation** qui permet à Nico de valider la lisibilité des 4 motifs d'un
regard au F5. Déterministe (**zéro `Random`**), pixel-art (`Palette16`).

## Fichiers à toucher
- `visuals/DecorLayer.cs` (lisière, LOD détail, prairie, éventuel helper de seuil zoom, banc).
- `visuals/DecorLayer.Arbres.cs` (si le LOD détail concerne les chevrons/silhouette de cime).
- MAJ doc : `docs/rendu/ambiance/conception_lisibilite_decor.md` (§ « état livré » en fin).

## Ce qu'il faut faire
1. **Lisière nette côté jardin** sur les 4 motifs : renforcer la frange de transition déjà posée par
   `DrawSecteur` (bande claire côté jardin) — p.ex. un rang d'ombre/arbustes bas en forêt, une berge
   franche en rivière (déjà T2), un pied d'éboulis en falaise (déjà T3), pour que la frontière se lise
   au lieu d'un fondu. Garder le tracé sinueux (jamais droit).
2. **LOD détail à 2 niveaux.** Introduire un seuil (p.ex. `DetailZoom = 2f`) : la **masse et la
   silhouette** (assises, houppiers volumés, surface d'eau, face de falaise) se dessinent à toute
   distance visible ; les **détails fins** (reflets fins, fleurs de prairie, chevrons bouleau) ne se
   dessinent qu'à `CurrentZoom ≥ DetailZoom`. Cela recale l'échelle ET **allège** le dessin au dézoom
   (perf, cf. garde-fou D66/D67). Recalibrer au passage la taille des détails restants pour qu'ils
   soient lisibles dans leur plage de zoom.
3. **Banc d'observation F5.** Fournir un moyen déterministe d'exposer les **4 motifs côte à côte**
   (un des 4 bords en forêt, un en rivière, un en falaise, un en prairie) pour valider la lisibilité
   d'un regard. Deux pistes acceptables — choisir la plus simple et la DOCUMENTER dans `00_etat.md` :
   - un **seed de démo** connu qui produit les 4 motifs (le trouver en balayant `BuildProfile`), noté
     dans `00_etat.md` comme « seed banc décor » — **sans** modifier la distribution par défaut ; OU
   - un **toggle debug** (touche F, cohérent avec les overlays debug existants type F6) qui force un
     profil des 4 motifs **uniquement quand activé**, off par défaut.
   Ne PAS altérer la distribution normale par seed (philo #7).
4. **MAJ doc** : ajouter une courte section « état livré » à `conception_lisibilite_decor.md`
   (ce qui a été fait T1-T4, seed/toggle du banc, points F5 restants pour Nico).

## Ce qu'il NE faut PAS faire
- Ne PAS introduire de `Random`/`GetHashCode` visuel.
- Ne PAS changer la distribution des motifs par seed (banc = démo/debug seulement).
- Ne PAS re-densifier la forêt pour « remplir » (perf) — le LOD va dans l'autre sens.
- Ne PAS lancer `test_epaisseur_500ans` ni aucun test long.

## Vérification
- `dotnet build Symbiose.csproj` = 0 erreur / 0 warning.
- `python3 tools/compte_ldc.py visuals/DecorLayer.cs visuals/DecorLayer.Arbres.cs visuals/Palette16.cs`
  — **rester ≤ 400** par fichier. `DecorLayer.cs` cumule T2+T3+T4 : s'il franchit 400, le **signaler**
  dans `00_etat.md` comme candidat `/refactor` (scission par responsabilité en fin de sprint), ne pas
  scinder soi-même ici.
- **Golden : rien à relancer** (aucun changement moteur). Le confirmer dans `00_etat.md`.
- Point F5 (Nico) : les 4 motifs se lisent et se distinguent d'un regard ; décor démarqué du jardin ;
  détails nets dans leur plage de zoom.

## Fin de tronçon (fin de sprint)
Mettre à jour `00_etat.md` (sprint CLOS, §REPRISE = terminé, seed/toggle banc noté), commit
(`feat(lisibilite-decor T4) : transitions + LOD détail + banc F5 + doc`). Puis clôture standard du
sprint : MAJ `DETTE.md` (D58 : lisibilité décor résorbée) + `BACKLOG.md` + `journal.md`, et lancer
`/refactor` auto-léger si un fichier a dépassé la bande.
