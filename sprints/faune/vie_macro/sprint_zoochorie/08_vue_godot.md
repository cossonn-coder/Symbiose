# ⑧ Vue Godot — les semeurs à l'écran (D42)

Lire d'abord : `CLAUDE.md` (Godot = VUE, C# seulement, `dotnet build
Symbiose.csproj` = filet, F5 = Nico), `00_etat.md`, doc
`docs/faune/vie_macro/conception_zoochorie.md`. Faits : ①-⑦ (moteur, voix, bancs
`verger_mur` et `nucleation`). Golden : hash courant dans `00_etat.md`, **inchangé**
dans ce tronçon.

## Objectif
Que Nico **voie** au F5 : le merle sur le cerisier et sur le perchoir, le geai,
l'écureuil dans les cimes, le mulot sous le paillis ; glands, faînes, noisettes sur
les arbres ; le noisetier ; un perchoir posable ; des semis qui lèvent sous les
perchoirs.

## Travail
1. **Faune** — pour `geai`, `ecureuil`, `mulot`, ajouter les entrées là où `merle` en
   a une (grep `"merle"` dans `visuals/` et `world/` : `FauneSilhouettes.cs`,
   `MacroLife.cs`, `FieldOverlay.cs` au moins). Palette SNES de la DA
   (`design_da_snes_mignon`) : geai beige-rosé, bande bleue à l'aile ; écureuil roux ;
   mulot brun-fauve, ventre clair. Comportement d'affichage : l'écureuil est dessiné
   dans les couronnes, le mulot au sol et surtout la nuit si le rendu distingue
   jour/nuit (sinon rien d'inventé). Vérifier comment le pont exporte les champs
   (`tools/simserver/commands.py`, liste `eco0.populations.keys()`) : les guildes
   neuves y sont normalement d'office.
2. **Fruits à coque** — `visuals/PlantRenderer.Organs.cs`, dictionnaire `Palettes`
   (clé = nom de CLASSE Python) : `OakTree` (gland vert → brun), `BeechTree` (faîne
   bogue brun-roux), `HazelTree` (noisette vert pâle → brun clair, chatons jaunes en
   fleur). Vérifier que les arbres émettent bien `fruits` dans le snapshot (déjà le
   cas pour le noyer).
3. **Noisetier** — palette d'organes + tout ce qu'un ligneux neuf demande côté vue
   (grep `BeechTree` / `"Hêtre"` dans le C# pour la liste).
4. **Perchoir** — `visuals/SupportRenderer.cs` / `world/WorldView.Support.cs` : type
   `perchoir` (piquet fin avec une traverse en tête) ; icône de geste
   (`world/GesteIcon.cs`) et entrée dans la palette des gestes, sur le patron de
   `poser_tuteur`. Protocole du pont : version incrémentée au ④ — l'aligner ici.
5. **Bancs F5** — rendre `nucleation` lançable comme les autres bancs (`init
   config="nucleation"` côté `tools/simserver/commands.py`, et la liste des bancs côté
   C# si elle existe — `world/WorldView.BancCleStable.cs`).
6. Dette de vue liée au sujet : rattacher toute dette de rendu faune/fruits ouverte
   dans `DETTE.md` qui concerne ces bêtes ou ces fruits (grep), sinon rien.

## Vérifications
- `dotnet build Symbiose.csproj` sans erreur ni nouvel avertissement.
- Banc capture VM si disponible (Xvfb → PNG, cf. mémoire rendu pixel-art) : une
  image du banc `nucleation` vue de dessus, jointe au compte rendu.
- Golden **inchangé** (aucun fichier `data/code/` moteur touché ; seul le pont).

## Points F5 pour Nico (liste courte, ressenti seul)
1. Banc `nucleation` : les semis de cerisier lèvent-ils lisiblement sous le perchoir
   et l'arbre mort ?
2. Geai, écureuil, mulot : reconnaissables au zoom ×8 ?
3. Glands / noisettes : visibles sur l'arbre en septembre ?
4. Poser un perchoir : le geste se trouve-t-il ?

## Ne PAS faire
- Pas de GDScript. Pas de logique de simulation en C#.
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Clôture
`00_etat.md` → CLOS côté code ; `DETTE.md` D42 → « CLOS côté code, F5 attendu » ;
`BACKLOG.md` ; entrée `journal/` + pointeur `journal.md` ; dettes de §7 du doc
ouvertes (numéros libres suivants).
