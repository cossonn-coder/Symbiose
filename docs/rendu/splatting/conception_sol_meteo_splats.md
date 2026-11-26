# Conception — sol, litière, eau, neige et météo en splats (famille (e)) + POC ×64

> Conçue en `/conception` le 2026-11-26 avec Nico (lot 1 arbitré, puis « carte blanche »).
> Famille (e) du programme D7 (`conception_precuisson_splats.md`) ; reprend la règle L2 de
> `conception_lisiere_chargement.md` (pixel natif par palier). Sprint :
> `sprints/rendu/splatting/sprint_sol_meteo_splats/`.
> **Vue et outillage seuls : `data/code/` (pont `tools/simserver` compris) n'est jamais modifié,
> golden `bce813af…` intact.**

## 1. Constat (lu au code le 2026-11-26)

- **Sol** : `world/SolTexture.cs` cuit UN losange de 39×20 px par (type de sol × orientation D35),
  3 types (terre, argile, sable) ; `SolMaillage` + `SolMateriau` = une maille par tuile (flancs +
  dessus). La caméra (`Camera2D`, paliers ×0,5→×32) grossit ce losange : **à ×32, un texel du sol
  = 32×32 px d'écran**. C'est l'écart le plus visible avec les plantes et la lisière.
- **Couches au sol**, toutes en polygones à couleurs littérales, hors palette indexée (elles ne
  suivent pas le soleil réel) : `CouvertureLayer` (tapis vert + agrégat des petites plantes),
  `LitterLayer` (amas), `LeafLitterLayer`, `StrawLitterLayer`, `DeadWoodLayer`, `MulchLayer` +
  `MulchMotifs` (paille, BRF, aiguilles, feuilles), `PuddleLayer` (+ `.Eau`, `.Mare` avec
  `eau_mare.gdshader`, `.Signaux`), `SnowLayer` (un losange blanc par tuile), `TracesSolLayer` +
  `TracesSolMotifs` (traces de gestes, craquelé à hystérésis).
- **Météo** : `WeatherLayer` = CanvasLayer « vitre » (traits de pluie et de grêle, points de neige,
  stries de vent, flash d'orage) ; `EclaboussuresLayer` (gouttes au sol) ; `LeafFallLayer` (chute
  des feuilles). La brume n'existe qu'en lisière et au ciel (shaders).
- **Données disponibles** (snapshot, sans toucher au pont) : `couverture`, `litiere` (tissu,
  masses, âges, bois), `paillage` (profondeur, nature), `eau_surface` (lame), `marais`, `sol_sec`
  (humidité des seuls plots < 0,5), `traces_sol`, `temperature[tile].snow` (un scalaire par tuile),
  `weather`. **Pas d'humidité complète par plot** → « sol mouillé plus sombre » impossible ici.
- **Écorce** : les bandes ne sont cuites qu'à ×4-×32 ; réduites aux petits paliers elles tournent au
  sel (seuil `EcorceReductionMax` = 2, `DecorLayer.Charpente.cs` ; `EcorceMinPx`, `PlantRenderer.Ecorce.cs`).
- **×64** : `ZoomSteps` s'arrête à ×32 ; seule une sonde existe (une feuille composée hors jeu,
  `sprint_reliquats_plantes/mesures/sonde_x64.png`, ~94 s par pièce [VM chargée, n=6]). Le POC
  chanvre ×64 prévu « après S1-S3 » n'a jamais été fait.

## 2. Décisions

| | Décision | Raison |
|---|---|---|
| **E1** (Nico) | **Sol = tapis de matériaux pavables** pour le fond continu + **kit de pièces** pour les objets épars + **eau au shader** (seul son lit est cuit). | « Tout en grains posés » : coût CPU ∝ surface, explose à ×0,5. « Une texture par plot » : ~5 Go à ×32 pour le monde. L'eau qui reflète n'est pas un nuage de splats. |
| **E2** (Nico) | **Météo = pièces cuites, taille par palier**, plafonnée (×8) pour ne pas masquer le jardin. | Cohérence avec le reste ; un flocon de 5 mm ferait 125 px à ×32. |
| **E3** (Nico) | **Écorce sous ×4 jointe** en tronçon court : bandes cuites à ×0,5/×1/×2. | Même outil, même règle (pixel natif), le F5 complet attend l'homogénéité ; un sprint à part repaierait l'amorçage. |
| **E4** (Claude, carte blanche) | **POC chanvre ×64 en avant-dernier tronçon** de ce sprint, derrière un interrupteur de banc. | Le sol est ce qui manque pour que ×64 ait un sens (une plante ×64 sur un sol aux texels de 64×64 serait incohérente). |
| E5 | **Une géométrie, plusieurs palettes** : ~10 géométries de matériaux ; humus, tourbe, vase, argile, sable = palettes sur les géométries de terre. | Principe fondateur (ton = volume, la palette fait la teinte). |
| E6 | **Seuil par hauteur** : le ton du matériau du dessous sert de hauteur ; l'eau remplit les creux d'abord, la neige mince reste dans les creux, chaque couverture « mord » le fond par ses bosses. | Bords organiques, plus de losanges ; la flaque grandit comme une vraie flaque ; zéro donnée neuve. |
| E7 | **Pas de réduction d'une cuisson fine** : chaque palier a sa cuisson. | Réduire au plus proche = sel (vu en S3 ②) ; moyenner des CODES (palette, ton, orientation) est faux ; cache GPU. (Question de Nico, 2026-11-26.) |
| E8 | **Interrupteur conservé** : Maj+F11 / `SYMBIOSE_SPLATS=0` → les anciennes couches, intactes. | Comparer avant/après au F5 ; repli sûr. |

## 3. Modèle

### 3.1 Matériau pavable (①②)
- Une **scène de splats posée sur un plan horizontal, en tore** de côté P (cm monde) : un splat
  qui sort d'un bord rentre par l'autre → image sans couture.
- Photographiée par une **caméra orthographique iso 2:1**, la même projection que
  `WorldView.WorldToScreen` (losange 39×19,5 px par plot de 50 cm à ×1). L'image d'un plan
  périodique en monde est périodique sur le réseau iso : la cellule rectangulaire = boîte
  englobante du losange de côté P, soit 78×39 px à ×1 pour P = 1 m, 2496×1248 px à ×32 [calculé
  depuis `TileWPx`/`TileHPx`]. **Le ① vérifie au code la projection** (rotation D35 comprise) et
  mesure la couture en texels (0 attendu, patron `cuire_ecorces.js`).
- Texel = format des planches splat (codes : ton + orientation ; la palette est posée par la vue).
- **Période** : P = 1 m de ×0,5 à ×32 ; **P = 50 cm à ×64** (au-delà de ×32 la période est divisée
  par 2 à chaque palier → mémoire constante par matériau et par palier, ~12,5 Mo brut [calculé]).
- **Variantes à bord commun** contre la répétition : les splats qui touchent le bord de la cellule
  sont communs, l'intérieur varie ; 4 variantes à ×0,5-×4, 2 à ×8, 1 à ×16+ (à ×32 une cellule
  de 1 m est plus large que l'écran). Variante choisie au hash de la cellule.
- **Géométries** (liste de départ, ② peut fusionner) : terre fine, terre motteuse, sable/gravier,
  herbe rase, paille, BRF (copeaux), aiguilles, feuilles mortes (litière dense), neige, craquelé ;
  + **flanc** (coupe de terre, pavée horizontalement).

### 3.2 Le tapis du sol (③④)
- Le shader du sol (successeur de `SolMateriau`, dialecte palette indexée) lit :
  - une **carte des champs par tuile** (1 texel par plot, mise à jour SEULEMENT quand le snapshot
    change la donnée) : quantités filtrées (couverture, litière, paillis, lame d'eau, marais, sec)
    et catégories au plus proche (type de sol, nature du paillis, teinte du tapis) ;
  - les **matériaux du palier courant** (une texture par géométrie ou un tableau de textures).
- **Ordre des couches** (bas → haut) : terre (palette du type de sol) → craquelé (plots secs, même
  hystérésis qu'aujourd'hui) → marais (palette tourbe) → tapis d'herbe rase (teinte de l'espèce
  dominante, agrégat des petites plantes compris) → litière fine → paillis (géométrie de sa nature) →
  **eau** → **neige**. Chaque couche apparaît là où `quantité > 1 − hauteur du dessous`.
- **Eau** : pixel d'eau = palette eau + reflet du ciel (nébulosité) + liseré au bord du seuil ;
  pendant la pluie, ronds d'impact (shader, hash). La **mare** garde `eau_mare.gdshader` ; sa rive
  et son fond deviennent vase/tourbe du tapis.
- **Rotation D35** : le grain reste attaché au sol monde quand la vue pivote (UV dérivées des
  coordonnées monde, pas de l'écran). Un matériau isotrope sert les 4 orientations.
- Le relief bombé « lumière du sud » de `SolTexture` disparaît : le soleil réel éclaire le grain
  par ses orientations (comme les plantes). Les flancs du micro-relief restent.

### 3.3 Objets épars (⑤)
- Feuilles mortes, tiges couchées, bois mort (brindille, branche, souche), traces de gestes : les
  couches existantes gardent leur logique (semis au hash, masse, âge, grosseur) ; seule la source
  graphique devient un kit de pièces splat par palier (patron `PlantRenderer.KitSplats.cs`),
  recettes réutilisées quand le mot existe (feuilles du jardin en palette morte, limbes, écorces).

### 3.4 Météo (⑥)
- Pièces : goutte-strie (3 inclinaisons selon le vent), flocon (4 poses qui tournoient), grêlon,
  couronne d'éclaboussure (4 poses). Taille = taille réelle au palier, **plafonnée à ×8**.
- Mouvement : fonction du temps au hash (inchangé), nombre borné, un lot.
- Feuilles en chute (`LeafFallLayer`) : pièces de ⑤. Flash d'orage et brume : inchangés.

### 3.5 POC ×64 (⑧)
- Palier ×64 ajouté derrière un interrupteur de banc (hors jeu normal) ; chanvre cuit à ×64 ;
  matériaux du tapis visibles dans la scène cuits à ×64 (P = 50 cm). Ne cuire que ce que la
  scène montre.
- Livrable : **une capture ×64** (chanvre sur son sol) + mesures (temps de cuisson, poids des
  planches, mémoire, ms par image [VM]) + liste de ce qui reste grossi à ×64 (faune, structures,
  lisière…).

## 4. Tronçons

| # | Tronçon | Golden |
|---|---|---|
| ① | Atelier des matériaux pavables (tore, iso, variantes, couture) — **porte de décision** | intact |
| ② | Bibliothèque des matériaux (~10 géométries × 7 paliers) | intact |
| ③ | Vue : tapis du sol (carte des champs, seuil par hauteur, terre/couverture/litière/paillis/neige) | intact |
| ④ | Vue : eau, marais, mare, craquelé, éclaboussures au sol | intact |
| ⑤ | Vue : objets épars en pièces (feuilles, tiges, bois mort, traces) | intact |
| ⑥ | Vue : météo en pièces cuites (pluie, grêle, neige, couronnes, feuilles en chute) | intact |
| ⑦ | Écorce sous ×4 (bandes ×0,5/×1/×2, jardin + lisière) | intact |
| ⑧ | POC ×64 (chanvre + son sol, interrupteur de banc, capture, mesures) | intact |
| ⑨ | Revue ×0,5 → ×32 (+×64), liste F5 de la famille (e), clôture | intact |

Ordre : ① → ② → ③ → ④ ; ⑤ ⑥ ⑦ indépendants après ① ; ⑧ après ② ③ ; ⑨ en dernier.

## 5. Coût et garde-fous

- **Par snapshot** : réécrire les cartes des champs des tuiles dont la donnée a changé
  (< 1 ms [estimé]) ; les `_Draw` des couches fusionnées dans le tapis disparaissent.
- **Par image** : les mêmes mailles de sol, fragment plus lourd (~4 lectures de texture par pixel).
  Risque = HD 4600 à 1920×1080 → **rapport C au PC** : pas sous 21 FPS à ×4, pas au-dessus de
  143 draw calls (référence du 2026-11-26). Sur la VM (llvmpipe), seuls les volumes se lisent.
- **Mémoire** : seuls les matériaux du palier courant vivent, comptés dans `BudgetCuisson` (1 Go,
  119 Mo utilisés au PC [rapport du 2026-11-26]).
- **Poids git** : `assets/splats/` 67 Mo, alerte 200 Mo ; ~4 Mo par matériau tous paliers
  [estimé, non mesuré] → mesuré à ①②. Le POC ×64 ne cuit que sa scène.
- **Cuisson** : durée inconnue (conifère de lisière ~58 min [VM chargée, n=1]) → mesurée au ①,
  parallélisée comme `cuire_ecorces.js` (`--liste | xargs -P`).
- Déterminisme : zéro `Random`, hash seulement ; deux cuissons = mêmes octets.
- Philo #5 : chaque signe d'aujourd'hui reste lisible (sol nu/tapissé, litière, nature du paillis,
  flaque, marais, mare, neige, craquelé, traces) ; aucun chiffre.
- Interdits : `data/code/` (sauf lecture), `test_epaisseur_500ans`, DeepSeek dans les sous-agents,
  `tools/splat/vendor/`.
- Taille des fichiers : partials neufs ≤ 300 LDC ; shader du tapis en fichier `.gdshader` propre.
