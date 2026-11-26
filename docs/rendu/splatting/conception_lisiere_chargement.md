# Conception — lisière en splats et écran de chargement en mycélium (S3 du style homogène)

> Conçue en `/conception` le 2026-11-26 avec Nico. Troisième et dernier sprint de la séquence
> « style homogène » (`conception_reliquats_plantes.md` §2 : S1 reliquats → S2 arbres → **S3 lisière
> + chargement**). Familles (b) et (g) du programme D7 (`conception_precuisson_splats.md`).
> Sprint : `sprints/rendu/splatting/sprint_lisiere_chargement/`.
> **Rendu et outillage seuls : `data/code/` n'est jamais modifié, golden `bce813af…` intact.**

## 1. Constat (lu au code le 2026-11-26)

**Lisière.** Toute la ceinture autour du jardin est dessinée par `DecorLayer` (19 partials) : une
maille par palier (×0,5, ×1, ×2, ×4), construite une fois en tranches de fond, un atlas de CODES de
palette indexée (`DecorLayer.KitCodes.cs`) et le shader `decor_indexe.gdshader` (saison pied par pied,
neige, givre, vent). Trois écarts avec le style splat :
1. le **kit** (`DecorLayer.Kit.cs`) est encore peint à la règle : 10 formes (Herbe, HerbeHaute, Fleur,
   Roncier, SousBois, Feuillu, Conifere, Galet, Bloc, Roseau) × tailles × 3 variantes ;
2. les **arbres** (`DecorLayer.Arbres.cs`, `.Houppiers.cs`, `.Branches.cs`) ont un tronc cerné et des
   charpentières en traits droits, exactement le défaut que S2 a corrigé dans le jardin ;
3. au-delà de ×4 (`MaxZoom = 4`), la maille ×4 est simplement **grossie** : au bord du jardin en gros
   plan, gros pixels à côté de plantes en splats natifs.

**Chargement.** `world/WorldView.Chargement.cs` : fond uni, une touffe ×8, « Le jardin se prépare ».
Nico (2026-11-25) : « devenu moche ». La séquence bloque le fil principal deux fois
(`PlantRenderer.AssurerGerbes`, puis `_bridge.Init` + montage dans `StartSimulation`) : un écran
animé y gèlerait. Le pont sert déjà depuis `Task.Run` (pas, actions, champs) sous un verrou d'I/O.

**Reste de S2.** La recette « rameau aplati » du sapin (aiguilles ×8-×32) n'est pas cuite ; le bouquet
conifère de la lisière a besoin de la même pièce.

## 2. Décisions

| | Décision | Raison |
|---|---|---|
| **L1** (Nico) | **Arbres de lisière = silhouette améliorée** : on garde l'architecture (ombre, tronc, charpentières, enveloppe, bouquets) ; la charpente passe par `RubanTexture` avec l'écorce cuite de S2 de son essence, pied évasé, sapin en étages, bouquets feuillus et conifères en pièces splat. | Des centaines d'arbres. Des imposteurs cuits entiers exigeraient une variante par saison et par état (nu, neige) et perdraient la saison qui gagne le bois pied par pied. |
| **L2** (Nico) | **Paliers ×8-×32 = atlas par palier** : la géométrie de la maille ×4 sert telle quelle ; l'atlas des pièces est cuit 2×, 4×, 8× plus fin, mêmes UV, permuté au changement de palier → pixel natif partout. | La géométrie du décor est en px canvas : seule la résolution de la texture décide du grain. Coût mémoire seul, pas de géométrie en plus. |
| **L3** (Nico) | **Mycélium = carte des âges + mycorhize** : une illustration splat cuite hors ligne + une carte « date d'apparition » par pixel ; un shader révèle les pixels d'âge ≤ progression, avec un front lumineux aux pointes. Récit : une spore germe → les hyphes s'arborisent → rejoignent la racine d'une plantule (manteau mycorhizien) → un petit carpophore sort à 100 %. | Deux textures, progression continue, image de la qualité des portraits. « Symbiose » = la mycorhize. Barre de progression permise (E2 : philo #5 vaut pendant le jeu). |
| L4 | **Rameau aplati du sapin** cuit en S3 : il sert le bouquet conifère de la lisière ET le sapin du jardin ×8-×32. | Une recette, deux usages ; ferme le reste de S2. |
| L5 | **L'écran vit pendant tout le chargement** : `_bridge.Init` en `Task.Run` (verrou existant) ; `AssurerGerbes` hors du fil principal si son travail est de l'`Image` pure, sinon découpé en tranches entre images ; seul le montage (arbre de scène) reste bloquant, gel mesuré. | Un mycélium figé pendant l'essentiel du chargement ne vaut pas mieux que la touffe. |
| L6 | **Progression monotone pondérée** : poids par phase (gerbes, init, montage, cuisson du cadre) fixés par mesure ; pendant une phase de durée inconnue, avance asymptotique vers le plafond de la phase ; cuisson = 1 − file restante / file initiale ; jamais de recul (`max`). | Une barre qui recule ou bondit trahit le chargement ; elle doit pousser comme un être vivant. |
| L7 | **Adaptateur** `DecorLayer.KitSplats` sur le patron de `PlantRenderer.KitSplats.cs` : planche splat → format exact du kit actuel, mêmes clés (forme, taille, variante) ; interrupteur Maj+F11 / `SYMBIOSE_SPLATS=0` ; recette absente → kit généré, entier, avec avertissement. | Le reste du décor (semis, saison, vent, mailles) ne change pas. |

## 3. Modèle

### 3.1 Kit de lisière (①)
- Une recette splat par forme, en réutilisant les recettes du jardin quand le mot existe déjà
  (`feuille_ruban` pour les herbes, `fleuron` pour la fleurette, `feuille_composee` pour la ronce,
  `feuille_aiguille` / rameau aplati pour le conifère, masses feuillues de S2 ④ pour le bouquet
  feuillu…) ; galet, bloc et roseau sont des recettes neuves.
- Pièces cuites à la taille en px de chaque palier, comme le kit des plantes ; même format de codes
  (ton + orientation au canal B), donc la saison, la neige et le soleil réel restent au shader.

### 3.2 Arbres de lisière (②)
- La charpente (tronc + charpentières de `DecorLayer.Branches.cs`) devient une polyligne lissée posée
  par `RubanTexture` ; u en travers, v = longueur d'arc en cm → l'écorce garde son échelle.
- Les bandes d'écorce des 8 essences de lisière (chêne, hêtre, bouleau, charme, sapin, noyer, aulne,
  saule — toutes cuites en S2, `visuals/BandesCuites.cs`) sont **recopiées dans l'atlas du décor**,
  pour que la lisière reste UN envoi. Si la mesure dit que ce n'est pas possible proprement, deux
  envois au maximum, signalé.
- Pied évasé ; sapin en étages de rameaux de plus en plus courts vers le haut (même règle que le
  sapin du jardin en S2 ⑤).
- Le sapin du jardin ×8-×32 pose ses aiguilles en rameaux aplatis (L4).

### 3.3 Paliers ×8-×32 (③)
- Pour chaque palier au-delà de ×4, un atlas des pièces à la résolution du palier, **mêmes UV
  normalisées** que l'atlas ×4 ; la maille ×4 sert, on ne permute que la texture.
- Les grains procéduraux du shader (roche, eau, neige, givre, `ip` en px internes) sont constatés en
  capture au-delà de ×4 et calés sur la même règle (pixel natif au palier réel).
- Mémoire comptée dans le budget de précuisson (`BudgetCuisson`, 1 Go, E6) ; ~64 Mo à ×32
  [estimé, non mesuré] ; atlas des paliers non affichés libérables.

### 3.4 Mycélium (④)
- Recette `tools/splat/` : la scène (spore, hyphes, racine de plantule, manteau, carpophore) où
  chaque splat porte un **âge** ∈ [0, 1] ; deux rendus : couleur (palette pleine, lumière cuite,
  comme les portraits) et âge (pour chaque pixel, l'âge du splat le plus ancien qui le couvre
  visiblement, à définir par la maquette).
- Résolution : pixel entier de l'écran (480×270 ×4 ou 960×540 ×2), choisie par la maquette.
- Shader de l'écran : pixel visible si âge ≤ p ; front lumineux si p − ε < âge ≤ p ; le carpophore
  occupe les âges ≥ ~0,9.
- **Porte de décision** : si la carte des âges n'est pas nette (halos, pointillés au mélange
  gaussien), repli = N images cuites (≈ 32), choisies par p.

## 4. Tronçons

| # | Tronçon | Golden |
|---|---|---|
| ① | Kit de lisière en splats (recettes, planches, adaptateur, interrupteur) + recette rameau aplati | intact |
| ② | Arbres de lisière sur le bois de S2 (ruban, écorce dans l'atlas, pied, sapin en étages) + sapin du jardin ×8-×32 | intact |
| ③ | Atlas par palier ×8-×32 + grains procéduraux au-delà de ×4 | intact |
| ④ | Écran de chargement en mycélium (maquette → carte des âges, chargement non bloquant, progression) | intact |
| ⑤ | Revue ×0,5 → ×32, liste F5 exhaustive S1+S2+S3, clôture de la séquence | intact |

Ordre : ① avant ② (bouquets) et ③ (le kit à re-cuire par palier) ; ④ indépendant (peut passer après
③) ; ⑤ en dernier.

## 5. Coût et garde-fous

- **Par image : rien.** La maille du décor ne se construit qu'au changement de palier (tranches de
  fond, ~8 ms par image). Référence de construction : 30-37 ms par palier [VM, sprint FLUIDITÉ PC] ;
  les troncs en ruban l'alourdissent → mesure au ②, alerte au-delà de +50 %.
- Draw calls de la lisière : 1 aujourd'hui (+ `EauScintillement`) ; à garder (L1).
- Poids : `assets/splats/` 65 Mo, **alerte à 200 Mo**.
- Référence PC de Nico (rapport C du 2026-11-25, `full` seed 42, an 2, ×32, n=1 run) : FPS 23
  [charge 86-94 %], 87 draw calls — S3 ne doit pas la dégrader.
- Déterminisme : zéro `Random`, hash seulement ; deux cuissons = mêmes octets.
- Interrupteur conservé : Maj+F11 / `SYMBIOSE_SPLATS=0` → l'ancien dessin intact derrière chaque crochet.
- Interdits : `data/code/` (sauf lecture), `test_epaisseur_500ans`, DeepSeek dans les sous-agents,
  `tools/splat/vendor/`.
- Taille des fichiers : partials neufs (≤ 300 LDC chacun) ; on n'alourdit pas `DecorLayer.cs` (déjà
  422 lignes totales).
