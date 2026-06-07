# Sprint Maison·4 — **Maquette saisonnière 3 secteurs**

> **Kickoff autosuffisant.** Démarrage à froid. Lis ce fichier, puis
> `data/code/CONCEPTION_MAISON_OMBRE.md` (§9 maquette, §6 triage visuel), puis les
> sources, puis exécute. Carte blanche (conception figée). **Français.**
> **Prérequis : tronçons 1, 2, 3 faits** (monde + maison + ombre + phototropisme).
>
> Tronçon **outil seul, GOLDEN INTACT** : on ne touche pas au moteur, on **lit**
> l'état déjà calculé. Touche `tools/render_structure.py` +
> `tools/export_structure.py`. Lancement depuis `data/code/`.

## Ce que c'est, en une phrase
La maquette répond à la demande initiale de Nico : montrer des **secteurs
contrastés** (S plein soleil / NE semi-ombre / NO ombre) **autour de la maison**,
sur un **cycle annuel** — **4 images (1/saison, tous les 3 mois)** par secteur et
par plante testée — pour **voir** l'ombre déterministe de la maison + le
phototropisme à l'œuvre.

## Principe directeur (à NE PAS contourner)
- **Outil read-only.** On rejoue le **vrai moteur** (`grow_plant` + `LightField`
  + maison) sur des spécimens placés dans les secteurs S/NE/NO, on **projette en
  iso** et on émet le SVG. **Zéro logique écologique nouvelle**, zéro RNG, **golden
  intact** (comme le tronçon croissance·4 qui a posé `export_structure.py`).
- **Vrai `LightField` + maison** : contrairement à la maquette actuelle qui pousse
  « dans le vide » (`growth_factor=1.0`, aucune lumière), ici les spécimens
  poussent **dans un monde avec la maison** → ils reçoivent vraiment l'ombre et se
  penchent. C'est tout l'intérêt.
- **Grille `secteurs × 4 saisons × plantes` (Q6, §9)** : pour chaque secteur (S,
  NE, NO) et chaque plante testée, 4 panneaux (printemps/été/automne/hiver).
- **Subtil ET marqué (Q3)** : rendre les **deux** intensités de phototropisme
  côte à côte pour que **Nico tranche** la valeur finale à l'œil. (Lire la valeur
  retenue au tronçon 3 dans `00_etat.md`.)
- **Triage visuel (§6)** : on rend ce qui **enseigne** (ombre au sol, inclinaison
  des apex). Pas de gadget. Les organes/feuilles ne sont **pas** l'objet ici
  (toujours tronçon 5 de la croissance procédurale, hors sprint).

## Sources à lire (dans l'ordre)
1. `data/code/CONCEPTION_MAISON_OMBRE.md` §9 (maquette), §6 (triage), §2 (secteurs).
2. `tools/render_structure.py` — maquette SVG actuelle (projection iso `_iso`,
   `_panel`, `_grow`). **Base à étendre.**
3. `tools/export_structure.py` — pont JSON déterministe (mêmes spécimens/SEED).
4. `fields/light.py` + `world/building.py` — pour pousser les spécimens dans un
   vrai champ lumière avec la maison.
5. `sim/growth.py` — `grow_plant` (intègre le phototropisme depuis le tronçon 3).

## Plan suggéré (révisable)
1. Helper « pousser un spécimen dans le secteur S/NE/NO à saison `s` » : place la
   plante à la bonne position monde vs maison, alimente le `LightField` avec la
   maison, rejoue `grow_plant` le nombre de ticks voulu, snapshot à la saison.
2. Étendre `_panel`/`render` pour la grille `secteurs × 4 saisons × plantes`
   (titres clairs : secteur, saison, intensité tropisme).
3. Dessiner aussi l'**ombre projetée de la maison** sur le sol du panneau (c'est
   l'info pédagogique centrale) + l'inclinaison visible des apex.
4. Variante **subtil vs marqué** (2 colonnes ou 2 fichiers).
5. Mettre à jour `export_structure.py` en cohérence (mêmes spécimens) si le pont
   JSON doit refléter les nouveaux secteurs (pour un futur rendu Godot).

## Critères de succès (vérifier AVANT de clore)
- [ ] SVG lisible : pour chaque secteur (S/NE/NO) × 4 saisons × plante(s), un
      panneau ; ombre de maison visible ; apex penchés vers le clair.
- [ ] **Contraste évident** : S = plein soleil (plante droite, vigoureuse) vs NO =
      ombre (plante penchée, étiolée) ; NE intermédiaire ; variation saisonnière
      de l'ombre visible (hiver plus longue).
- [ ] **Subtil ET marqué** rendus côte à côte (Nico tranchera).
- [ ] **Déterministe** : relancer = SVG identique.
- [ ] **Golden + suite INTACTS** (outil read-only, aucune touche au moteur).
- [ ] `00_etat.md` mis à jour (tronçon 4 ✅ → sprint maison **clos côté Python** ;
      reste tronçon 5 Godot/C# = plus tard).

## Pièges connus
- Ne pas réintroduire de RNG dans l'outil (SEED fixe comme l'existant).
- Bien placer les spécimens en **coordonnées monde** vs maison (réutiliser les
  offsets/convention du tronçon 1-2), sinon l'ombre tombe à côté.
- La projection iso `_iso` est l'affichage ; la sim vit en cm 3D sol — ne pas
  mélanger les deux repères (cf. note du tronçon croissance·4).
