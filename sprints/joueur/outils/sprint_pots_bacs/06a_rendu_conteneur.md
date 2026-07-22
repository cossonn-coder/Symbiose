# ⑥a Vue Godot — rendu statique conteneur + substrat (lecture seule)

> Lire `00_etat.md` (sprint moteur ①→⑤ CLOS) + conception §1, §7. **Option B**
> (Godot = VUE, moteur Python figé). Premier des 3 sous-tronçons de la vue ⑥.
> **Golden TRIVIALEMENT NEUTRE** : ce tronçon ne touche **aucun** fichier Python.
> Tout le moteur est déjà fait ; on ne fait que LIRE le snapshot et DESSINER.
> Décisions tranchées par Nico (AskUserQuestion 2026-06-25) : **placeholder
> procédural pixel-art** (pas de PNG, cohérent SS²/D34) ; **3 sous-tronçons**.
> Filet de compilation : `dotnet build Symbiose.csproj` (le **F5 visuel reste à
> Nico** — Godot n'est pas sur la VM). Namespace `Symbiose`, GDScript INTERDIT.

## Objectif
Rendre VISIBLE, en lecture pure depuis le snapshot, chaque conteneur posé : le
**pot** (tronc-cône iso) ou le **bac** (caisse N×M iso), avec son **substrat**
lisible à la teinte de la surface, et la/les **plante(s)** qu'il contient. Aucune
interaction (pose/déplacement = ⑥b). Aucun indice de couplage (= ⑥c).

## Ce qui est DÉJÀ là (à réutiliser, ne rien réinventer)
- **Snapshot `containers`** (pont 0.5.7, `tools/simserver/serialize.py::
  _containers_snapshot`) — liste, VIDE au repos. Par conteneur :
  `id` · `kind` (`"pot"`|`"bac"`) · `substrat` (clé du registre) · `volume`
  (litres) · `x_cm`/`y_cm` (**position MONDE absolue** — ⚠ ≠ plantes du bloc
  `plants`, qui sont en LOCAL tuile) · `mobile` · `fond_ouvert` · `rows`/`cols`
  (géométrie du mini-sol) · `plants` (forme compacte : `species`/`name`/`x_cm`/
  `y_cm`/`stage`/`stage_name`/`height_cm`/`dead`/`segments` + `leaf_symptoms`/
  `fruits` si vivante) · `eco_summary` (scalaires plot 0,0, gardés pour ⑥c).
- **Pattern de rendu = `visuals/CompostStructure.cs` + `world/WorldView.Compost.cs`**
  (à COPIER dans l'esprit) : un objet posable = **un Node2D dans la couche YSort
  `_objects`** (s'occulte en profondeur avec plantes/maison) ; **reconstruction
  pleine à chaque snapshot** (`ApplyStructures` : `QueueFree` les anciens nœuds +
  recrée) ; dessin iso dans `_Draw()` via `Footprint(halfCm)` (4 coins projetés
  en OFFSET qui tournent avec la vue) + extrusion verticale `* WorldView.PxPerCmZ`.
- **Projection** : `WorldToScreen(x_cm, y_cm)` (position du nœud), `WorldView.
  WorldToScreenOffset(dx, dy)` (empreinte au sol), `WorldView.PxPerCmZ` (hauteur),
  `PlotCm`. Le partial `WorldView.Compost.cs` montre l'usage exact.
- **Palette pixel-art** : `visuals/Palette16.cs` (27 couleurs nommées, SS² T1).
  Une teinte de substrat par recette s'y puise (cohérence palette).
- **La plante en pot** : se dessine avec le **`PlantRenderer` existant** (le bloc
  `plants[]` du conteneur a le même format `segments` que le bloc `plants` global
  → `PlantStructure.FromSnapshot` sait déjà lire). L'effet nain est **déjà dans le
  moteur** (`height_cm` réduit) → aucune logique de rapetissement côté vue.

## À faire
### A. `visuals/ContainerStructure.cs` (NOUVEAU) — placeholder procédural
Calqué sur `CompostStructure.cs`. Un `partial class Node2D`, `_Draw()` iso :
- **POT** = tronc-cône iso (cercle/losange du haut plus large que la base),
  hauteur ∝ une réf de volume (knob, calibrage post-F5). Empreinte 1 plot.
- **BAC** = caisse N×M iso (réutilise la logique 2 faces avant + dessus de
  `DrawBac`), empreinte `cols × rows` plots.
- **SUBSTRAT** = teinte de la **surface** (le dessus du conteneur) puisée dans
  `Palette16` par clé de substrat (terreau brun, drainant gris clair, lasagnes =
  fines strates, compost sombre, terre, mycélium clair…). Une `Dictionary<string,
  Color>` substrat→teinte, repli neutre si clé inconnue (lecture tolérante).
- Constructeur prend `kind`, `substrat`, `volume`, `rows`, `cols` (comme
  `CompostStructure(kind, mur, contenu, …)`).

### B. `world/WorldView.Conteneurs.cs` (NOUVEAU partial) — câblage lecture
Calqué sur `WorldView.Compost.cs` :
- une liste `_containers` (id, node, x_cm, y_cm…) pour la désignation de ⑥b ;
- `ApplyContainers(GArray containers)` : reconstruction pleine (QueueFree anciens
  + recrée), chaque conteneur = un `ContainerStructure` positionné à
  `WorldToScreen(x_cm, y_cm)` (position MONDE directe, **pas** d'origine de tuile
  à ajouter) et ajouté à `_objects` (YSort) ;
- pour chaque `plants[]` du conteneur : instancier/positionner un `PlantRenderer`
  (même chemin que les plantes du monde), ancré sur la position MONDE du conteneur.
  ⚠ **Vérifier le repère** des `x_cm/y_cm` des plantes du mini-sol (local cellule
  vs monde) en lisant `world/container.py::planter_dans` + `_containers_snapshot` ;
  les replacer correctement autour du centre du conteneur. Si l'intégration
  PlantRenderer est lourde, la livrer en B mais signaler tout point F5.
- **Lecture TOLÉRANTE** : snapshot sans clé `containers` (ancien) → rien dessiné,
  jamais de crash (comme `ApplyLitiere` pré-0.3.7).

### C. Brancher dans le dispatch du snapshot
Appeler `ApplyContainers(snapshot["containers"])` là où les autres blocs sont
appliqués (à côté de `ApplyStructures`/`ApplyLitiere` — voir le partial qui porte
`ApplySnapshot`, p.ex. `world/WorldView.Snapshot.cs`). Créer la liste/les layers
au `_Ready` si besoin (cf. `BuildLitterLayer`).

## Définition de done
- `dotnet build Symbiose.csproj` **vert**.
- Aucun fichier Python touché → golden **trivialement NEUTRE** (le rappeler dans
  le rapport, ne PAS relancer un re-figeage).
- Un conteneur présent dans un snapshot de test (ou posé à la main en ⑥b) se
  dessine : forme pot/bac, teinte de substrat, plante dedans, occultation correcte
  en profondeur (YSort), cohérent sous les 4 orientations de vue.
- MAJ `00_etat.md` (ligne ⑥a FAIT) + liste des points **F5** pour Nico.

## Pièges
- `x_cm/y_cm` du **conteneur** = MONDE absolu (ne PAS ajouter `_origins[tile]`) ;
  `x_cm/y_cm` des **plantes du conteneur** = à vérifier (repère cellule/monde).
- Reconstruction pleine = pas de fondu à tenir (la jauge/forme change peu) :
  trivial, comme reconstruire le sol à la rotation (cf. en-tête `Compost.cs`).
- Pas de chiffre en HUD primaire (philo #5) — `eco_summary` est réservé aux
  étiquettes/indices de ⑥c, ne rien en afficher ici.
- Hauteur/empreinte en placeholders chiffrés (knobs `const`) → calibrage post-F5
  par ces seules constantes (cf. `MasseRef` de `CompostStructure`).
