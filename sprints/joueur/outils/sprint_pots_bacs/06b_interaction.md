# ⑥b Vue Godot — interaction poser / déplacer / planter (outil + clic)

> Lire `00_etat.md` + `06a_rendu_conteneur.md` (dont il dépend). **Option B**
> (Godot = VUE). Deuxième des 3 sous-tronçons de la vue ⑥. **Golden TRIVIALEMENT
> NEUTRE** : aucun fichier Python touché (les 4 verbes du pont existent DÉJÀ depuis
> ④). Décision Nico (2026-06-25) : **outil + clic** (homogène avec tous les autres
> gestes via `TryAction`), **PAS de drag&drop** (reporté). Filet :
> `dotnet build Symbiose.csproj` (F5 = Nico). Namespace `Symbiose`, GDScript INTERDIT.

## Objectif
Permettre au joueur de **poser** un pot / un bac, **choisir son substrat**,
**déplacer** un pot, et **planter** une graine dedans — exactement par le même
chemin que tous les autres gestes (sélection d'outil au clavier puis clic),
sans nouveau système d'input.

## Ce qui est DÉJÀ là (à réutiliser)
- **4 verbes du pont, routés** (④, `tools/simserver/conteneurs_route.py`, validés
  côté serveur) : `poser_pot`, `poser_bac_culture`, `deplacer_pot`,
  `planter_conteneur`. Leurs `target`/`params` attendus (à RELIRE dans le routeur
  pour les noms exacts) :
  - `poser_pot` : point de milieu `{tile, x_cm, y_cm}` (local tuile) + `substrat`
    + `volume`. Pose un pot mobile 1×1.
  - `poser_bac_culture` : idem + `rows`/`cols` + `fond_ouvert`. Bac immobile N×M.
  - `deplacer_pot` : `{container: <index>}` + nouvelle position `{x_cm, y_cm}`
    (MONDE). Refusé en amont si le conteneur n'est pas `mobile` (0 Vigueur).
  - `planter_conteneur` : `{container: <index>}` + `species` (clé catalogue).
    Place DIRECTEMENT (pas de succession en pot), consomme la banque-joueur.
  - **Index conteneur** = position dans la liste `containers` du snapshot
    (`target.container`, cf. `_containers_snapshot`).
- **Mécanique outil+clic = `world/WorldView.Actions.cs`** : table `Gestes`
  (`(Verb, Nom, Kind)[]`), sélection cyclique `CyclePalette` (Tab) / touches 1..9,
  `TryAction(canvasPos, shift)` qui résout la cible selon `Kind` puis `LaunchAction`.
  Le **cycle d'espèce `CycleSeed`/`_seeds`** (touche S) est le modèle exact pour un
  **cycle de substrat**. Désignation de plante/plot/structure : `FindPlant`,
  `FindPlot`, `FindNearestStructure` (modèles pour un `FindNearestContainer`).
- **`ScreenToWorld`/`_origins`** pour convertir clic → point monde / local tuile
  (cf. les cas `Kind=='m'` planter/arroser et `Kind=='q'` poser structure).

## À faire (tout dans `world/WorldView.Actions.cs` + le partial Conteneurs de ⑥a)
### A. Quatre entrées dans la table `Gestes`
Ajouter `poser_pot`, `poser_bac_culture`, `deplacer_pot`, `planter_conteneur`
avec des `Kind` adaptés :
- **poser_pot / poser_bac_culture** : `Kind` « point de milieu » (réutiliser la
  logique `'m'` : tuile sous le clic → `x_cm/y_cm` LOCAUX). Joindre `substrat`
  (cycle, cf. B) et `volume`/`rows`/`cols`/`fond_ouvert` (knobs de départ, ou un
  petit cycle ; placeholder raisonnable, calibrage F5).
- **deplacer_pot** : nouveau `Kind` « conteneur » → `FindNearestContainer(w,
  radius)` désigne le pot le plus proche du clic = `target.container` ; la
  **destination** = un second clic (ou Maj+clic) donnant la nouvelle `x_cm/y_cm`
  MONDE. Concevoir le geste à 2 temps proprement (1er clic = saisir, 2e = poser),
  en restant homogène avec `TryAction`. Refus mobile géré côté serveur (relayer).
- **planter_conteneur** : `Kind` « conteneur » → `FindNearestContainer` +
  `params.species` = l'espèce courante du cycle `_seeds` existant.

### B. Cycle de substrat (modèle = `CycleSeed`)
Une liste des 6 clés du registre `world/substrat.py` (les LIRE, ne pas les
inventer), une touche dédiée pour cycler, l'entrée courante jointe à `poser_pot`/
`poser_bac_culture`. HUD : afficher le substrat courant (cf. `UpdateActionHud`).

### C. `FindNearestContainer(Vector2 w, float radiusCm)`
Calqué sur `FindPlant`/`FindNearestStructure` : parcourt `_containers` (liste de
⑥a), renvoie l'**index snapshot** du conteneur dont le centre MONDE est le plus
proche sous le rayon, ou −1 (message clair « aucun conteneur ici »). Recherche
linéaire (poignée de conteneurs, pas de quadtree).

## Définition de done
- `dotnet build Symbiose.csproj` **vert**.
- Aucun fichier Python touché → golden **trivialement NEUTRE**.
- En F5 (Nico) : sélectionner « poser pot », cycler le substrat, cliquer une tuile
  → un pot apparaît (Vigueur débitée, snapshot mis à jour, ⑥a le dessine) ;
  « poser bac » → bac N×M immobile ; « déplacer » + 2 clics → le pot saute à la
  nouvelle position ; « planter (conteneur) » + graine → la plante pousse dedans
  (effet nain visible si petit volume). Le bac refuse le déplacement (message).
- MAJ `00_etat.md` (ligne ⑥b FAIT) + liste précise des points **F5** pour Nico
  (notamment l'ergonomie du déplacement 2 temps + les knobs volume/N×M par défaut).

## Pièges
- **Aucune pré-validation côté C#** : la vue DÉSIGNE, le serveur juge (coûts,
  bornes, mobilité, banque) et répond ACK/NAK — relayer son message (`_lastActionMsg`).
- `deplacer_pot` écrit la position MONDE ; `poser_*` envoie un point LOCAL tuile
  (le serveur résout le plot d'assise). Ne pas confondre les deux repères.
- Pipe occupé → mémoriser l'intention (`_queuedIntent`), comme les autres gestes.
- Au-delà de 9 entrées dans `Gestes`, seules les touches 1..9 ne suffisent plus :
  c'est `CyclePalette` (Tab) qui atteint tout — vérifier que les nouveaux gestes y
  sont accessibles.
- Le **substrat** ne se choisit qu'à la POSE (pas de re-substrat d'un conteneur
  existant dans ce sprint).
