# Sprint RENDU AMBIANCE (D58) — état vivant (carnet de conception)

> Carnet de bord `/conception`, mis à jour à chaque décision. Reprise à froid :
> lire `CLAUDE.md` + ce fichier. NE FIGE RIEN tant que Nico n'a pas validé.

## Sujet
D58 — « Rendu graphique attractif » : vraies fleurs/feuilles par espèce, maison
normande dessinée, décor d'ambiance (forêt/rivière/falaise), **+ animation vent
des plantes** (addendum Nico).

## Phase courante
**FIGÉ (2026-07-09) — prêt pour `/sprint-auto`.** Conception :
`docs/rendu/ambiance/conception_rendu_ambiance.md`. 6 kickoffs `01`→`06` présents.
Golden préservé partout (T1 moteur NEUTRE, T2-T6 vue pure).

## Constat de cadrage (VÉRIFIÉ dans le code, 2026-07-09)
D58 date du 2026-07-02 et est **en partie déjà résorbée** depuis :
- **Feuilles par espèce = FAIT** — sprint feuillage clos : `PlantRenderer.Leaf.cs`
  (358 l), `enum LeafShape` 6 archétypes (Elliptique/Lancéolée/Cordée/Lobée/
  Composée/Aciculaire) mappés sur ~20 espèces + nervures + croissance progressive
  + litière (`LeafLitterLayer.cs`). Commit `ff1a52f`.
- **Couleur physiologique = FAIT** — D33 sémiologie foliaire close (`SetSymptoms`).
- **Palette + relief sol = FAIT** — SS② pixel-art (`Palette16.cs`, `SolTexture.cs`).
- **Champignons / faune / vrilles = FAITS** — `CarpophoreLayer`, `MacroLife`,
  `SupportRenderer`.
→ « vraies feuilles par espèce » n'est PLUS le sujet.

## Ce qui reste réellement sous D58 (4 chantiers hétérogènes)
1. **Fleurs par famille (forme)** — couleur/espèce FAITE (`OrganPalette.Flower`),
   mais silhouette encore **5 pétales génériques** ; manquent corolles par famille
   (ombelle Apiaceae, capitule Asteraceae…). Couche B pure, petit, lignée feuillage.
2. **Maison normande dessinée** — aujourd'hui placeholder procédural (D4 🟡,
   `WorldView.Monde.cs`, empreinte iso + 2 façades + toit gris). Cosmétique.
3. **Décor d'ambiance hors-jardin** (forêt/rivière/falaise) — **territoire NEUF**,
   aucune conception. Le monde simulé = 20×20 m ; le décor = ce qu'il y a AUTOUR.
4. **Animation vent des plantes** — **NEUF**, point dur (perf + paradigme).

## Drapeaux remontés (arbitrages en attente)
- **A. Vent vs perf (ROUGE).** Sprint perf rendu plantes clos le 2026-07-09
  (5 FPS → LOD silhouette + culling + plantes rendues STATIQUES, re-`_Draw`
  seulement au tick/zoom). Animer le vent = redessiner les plantes CHAQUE frame
  → rouvre exactement le poste qu'on vient de fermer. À concevoir **perf-first** :
  balancement par transform du Node2D (`_Process`, `skew`/rotation du canvas, GPU
  réutilise le buffer, ≈ gratuit) plutôt que re-`_Draw` des branches ; vent
  limité aux plantes proches / au-dessus d'un palier de zoom.
- **B. Décor : cosmétique pur vs relié moteur.** Règle d'interconnexion « tout
  coexiste ». Deux lectures : (i) backdrop 2D assumé cosmétique (comme le ciel
  météo `WeatherLayer`) ; (ii) représentation de la **friche périphérique**
  (canal d'acquisition #3) / des **extensions par maîtrise** (verger/mare/
  prairie) → relié au moteur. Tranche tout le découpage.
- **C. Procédural vs sprites peints.** Tout le rendu Symbiose est procédural
  déterministe (VM sans Godot/outils d'art → aucun bitmap peint possible côté
  agent). Reco = **rester procédural** (maison colombages + arbres de forêt
  dessinés en C#), cohérent plantes/sol/faune. Sprites peints = hors périmètre
  code (Nico/artiste produit les PNG, l'agent ne câble que le chargement).

## Décisions arrêtées (Nico, 2026-07-09)
- **AJOUT 2026-07-09 (post-figeage) — Feuilles fidèles au modèle réel (T6).**
  Nico : les feuilles restent « ovales ». Vérifié : `PlantRenderer.Leaf.cs`
  synthétise par **amas d'ellipses** → taches. Décision = **contours authorés par
  espèce** (~27), l'amas d'ellipses devenant le **repli LOD intermédiaire**.
  Fidélité livrée **au zoom rapproché ×16+** (physique du pixel : 2-5 px à ×4/×8,
  indistinguable). 3 paliers LOD. Nouveau partial `PlantRenderer.LeafOutline.cs`.
  Couche B pure, golden inchangé. → tronçon **T6**, kickoff `06_feuilles_fideles.md`.
- **Périmètre = 3 chantiers : fleurs-famille + maison normande + décor** (+ T6
  feuilles fidèles, ajouté ci-dessus).
  **Vent EXCLU** de ce sprint → reste ouvert (dette, à concevoir à part vu son
  enjeu perf/paradigme d'animation).
- **Décor = cosmétique MAINTENANT, extensible plus tard.** Backdrop 2D livré
  tout de suite ; prévoir une couture (`SurroundingsProfile`) pour brancher plus
  tard la friche périphérique / les extensions par maîtrise, sans la câbler ici.
- **Procédural déterministe partout** (reco C acceptée par défaut) : maison à
  colombages + décor dessinés en C#, zéro bitmap peint. Cohérent plantes/sol/faune.
- **Tout couche B pure → golden trivialement préservé** à chaque tronçon (rendu
  = vue passive, aucun moteur touché, aucun re-figeage).

## Conception détaillée (arrêtée par l'agent, bio/détails — à valider avant figer)
### Chantier 1 — Fleurs par famille (forme)
Calque du feuillage : `enum FlowerShape` + table `FlowerProfile[species]`, tracé
déterministe (hash) composant des primitives volumées (réutilise
`DrawVolumeEllipse`, invariant ≥2 valeurs). Archétypes fermés (~6), défaut
`Simple` : `Simple` (5 pétales radiaux — Rosaceae : pommier, fraisier ; bourrache),
`Ombelle` (Apiaceae : carotte), `Capitule` (Asteraceae : tournesol, souci,
achillée — disque + rayons), `Papilionacee` (Fabaceae : haricot, trèfle),
`Epi`/grappe verticale (Lamiaceae/Brassicaceae : lavande, thym, moutarde,
phacélie, consoude), `Clochette` (Ericaceae : myrtille). LOD : au dézoom →
`Simple` ou rien. Fichier : nouveau `PlantRenderer.Flower.cs`.
### Chantier 2 — Maison normande = GRANITE + ARDOISE (Cotentin, PAS colombages)
Réf. Nico (maçon+couvreur, Montmartin-sur-Mer/Coutançais). J'ABANDONNE
torchis/chaume. Étend le placeholder D35-aware (extraire `WorldView.Maison.cs`) :
- **Murs** : appareil de **moellons de granite gris-bleu à reflets roux**, joints
  chaux clairs beurrés → texture pierre 2-3 valeurs (grain par hash, cohérent
  `SolTexture`). **Chaînages d'angle** marqués (pierres harpées plus claires),
  **encadrements de baies en granite gris clair** (jambages + linteau + appui à
  larmier).
- **Pignon exposé (ouest/vent)** : **essentage d'ardoise** (bardage d'écailles)
  jusqu'à mi-hauteur, distinct du reste du mur.
- **Toit** : **ardoise gris-bleu foncé**, **forte pente (>45°)**, rangs d'écailles
  (pureau serré), faîtage ; **lucarne à bâtière** sur le versant sud ; débords /
  rives sobres. Remplace la pyramide plate actuelle par 2 pans pentus + croupe.
- **Ouvertures** : porte sud + fenêtres à petits carreaux (menuiserie sombre).
- **Cheminée(s)** : souche en **brique orangée** émergeant du faîtage (statique,
  PAS de fumée = animation différée avec le vent).
- D35 conservé (façades/pans indexés mur-monde). Palette16 étendu (granite gris-
  bleu/roux, granite clair, ardoise, brique orangée, joint chaux).
### Chantier 3 — Décor d'ambiance (organique, cosmétique ; terraforming = DETTE)
Réf. Nico. Nouveau `visuals/DecorLayer.cs`, Node2D DERRIÈRE `_ground` (ZIndex
négatif, hors picking), tournant avec le monde (D35). **Formes ORGANIQUES
sinueuses** (jamais droites, bruit déterministe) qui ouvrent/ferment des espaces.
- **4 motifs** répartis **par seed** autour du jardin (philo #7) : **forêt**
  (essences du catalogue, arbres ADULTES grande taille ; **lisière** depuis le
  bord du jardin s'enfonçant, **densité croissante** jusqu'à forêt profonde),
  **rivière** + **falaise** **COUPLÉES** (l'érosion fluviale a creusé la roche ;
  pente falaise variable douce/verticale/déversante), et **prairie verte fleurie**
  = motif par DÉFAUT du/des côté(s) non occupé(s).
- **Chemins entre tuiles = enherbés (gazon)**, plus le gris pierre `FondPierre`
  actuel → à basculer en vert herbe.
- Couture d'extensibilité : struct `SurroundingsProfile` (placement des zones)
  calculée en C# depuis le seed AUJOURD'HUI, structurée pour être alimentée PLUS
  TARD par le pont (friche périphérique, extensions par maîtrise, parcelles
  d'accueil ouvertes par le décor).
- **HORS PÉRIMÈTRE → DETTE NEUVE « terraforming »** : agir sur le paysage
  (barrage, coupe d'arbres, creuser la falaise, créer une mare…), comptabilisé
  avec conséquences. À concevoir séparément (moteur). Ici : décor cosmétique seul.

## Coût perf estimé (préliminaire)
- Fleurs-famille / maison / décor statique : couche B, ~gratuit (dessin au
  snapshot/init, pas par frame).
- **Vent : le seul poste sensible** — doit rester en transform-only par frame.

## Essences forestières AJOUTÉES au catalogue (Nico 2026-07-09)
Le catalogue a DÉJÀ : chêne (étalé), sapin (conique), noyer, cerisier, figuier,
pommier. On AJOUTE 3 essences normandes manquantes (chacune = vraie espèce
moteur `PerennialWoody` + ses 5 voix, règle projet) :
- **Hêtre** (Fagus sylvatica, Fagaceae = même famille que le chêne) — hêtraie
  cathédrale, port ovoïde dense, grand.
- **Bouleau** (Betula pendula, Betulaceae NEUVE) — pionnier de **lisière**,
  écorce blanche, port élancé pleureur clair.
- **Charme** (Carpinus betulus, Betulaceae) — bocage, tronc cannelé sinueux.
Aulne/saule de ripisylve LAISSÉS à la conception hydrologie (figée) → pas de
doublon. Ces espèces sont ajoutées au moteur mais NON plantées dans le scénario
smoke → **golden NEUTRE** (tronçon catalogue). Le DÉCOR les rend en silhouettes
adultes (voir ci-dessous) ; leur présence au catalogue leur donne encyclopédie +
voix (et prépare l'acquisition future canal #3 friche).

## Rendu procédural des ARBRES ADULTES du décor (réponse à la demande Nico)
Les arbres du décor sont un BACKDROP cosmétique HORS jardin → ils n'utilisent PAS
la structure de segments lourde de `PlantRenderer` (perf : des centaines d'arbres).
Ils sont **peints directement en silhouette ADULTE** — donc « déjà hauts et mûrs
au démarrage » PAR CONSTRUCTION (aucun âge, aucune croissance) :
- **Un arbre = tronc + houppier**, quelques primitives, dessiné UNE FOIS (statique,
  jamais re-`_Draw` par frame → cohérent avec l'exclusion du vent), cullé hors écran.
- **Houppier = amas d'ellipses volumées** (2-3 valeurs + hue-shift sud, invariant
  pixel-art) formant un « nuage » — PAS des branches individuelles (illisibles et
  coûteuses au backdrop). Nombre/placement des blobs = **hash(seed, index arbre)**.
- **Archétype de port par essence** (table C# `TreeSilhouette`, comme `LeafProfile`) :
  `Etale` (chêne, dôme large bas), `Ovoide` (hêtre, œuf dense haut), `Elance`
  (bouleau, houppier léger ouvert, tronc clair), `Sinueux` (charme, tronc cannelé),
  `Conique` (sapin, étages triangulaires). **Rayon de houppier = taille ADULTE**
  (table par essence) → maturité intégrée.
- **Tronc** : 1-2 formes fuselées (`WoodRamp` brun) + signature d'écorce
  (bouleau = clair à chevrons sombres ; charme = cannelures).
- **Couleur de feuillage par essence** (bouleau clair, hêtre vert profond, chêne
  moyen, sapin vert-bleu) + modulation automnale saisonnière optionnelle (réutilise
  `LeafColor`).
- **Lisière → forêt profonde** : densité d'arbres CROISSANTE en s'enfonçant depuis
  le bord (scatter déterministe hash, comme `MacroLife`/litière) ; bord = pionniers
  clairsemés (bouleau), profond = grands arbres denses (chêne/hêtre).
- **Profondeur** : tri par Y de base (les proches masquent les lointains) ; tout
  DERRIÈRE le jardin. **Perf** : quelques milliers de primitives statiques dessinées
  une fois, cullables ; repli = cuire la zone forêt en texture unique si besoin.

## Découpage (6 tronçons, tous golden préservé)
- **T1 — Essences forestières au catalogue** [MOTEUR, golden NEUTRE] : Hêtre,
  Bouleau, Charme (`plants/perennials.py` + `catalogue.py` + 5 voix chacune).
- **T2 — Fleurs par famille** [vue] (`PlantRenderer.Flower.cs`, `FlowerShape`+profils).
- **T3 — Maison normande** [vue] (extraire `WorldView.Maison.cs` ; granite+ardoise+
  pignon essenté+lucarne+cheminée brique, Palette16 étendu).
- **T4 — Décor : ossature** [vue] (`visuals/DecorLayer.cs` : zones organiques par
  seed = placement prairie/forêt/rivière/falaise sinueux + chemins enherbés +
  `SurroundingsProfile`).
- **T5 — Décor : forêt + rivière/falaise détaillés** [vue] (silhouettes d'arbres
  adultes par essence `TreeSilhouette` + lisière→profond ; rivière+falaise
  couplées, pente variable + reflets/dithering ; table décor ↔ essences T1).
- **T6 — Feuilles fidèles au modèle réel** [vue] (`PlantRenderer.LeafOutline.cs` :
  contours authorés par espèce ~27, volume + nervures, palier LOD ×16, repli
  archétype ellipses ; indépendant, dès après T1/T2).
Ordre : moteur d'abord (T1), puis vue (T2→T6). Règle « vue Godot en dernier »
satisfaite. F5 Nico à chaque tronçon. À figer aussi : **DETTE neuve terraforming**
+ **vent** (renvoyé) en dette.

## Carte des tronçons (exécution /sprint-auto)
- `01_essences_forestieres.md` — T1 [moteur, golden NEUTRE]
- `02_fleurs_famille.md` — T2 [vue]
- `03_maison_normande.md` — T3 [vue]
- `04_decor_ossature.md` — T4 [vue]
- `05_decor_motifs.md` — T5 [vue]
- `06_feuilles_fideles.md` — T6 [vue, indépendant]
Ordre imposé : T1 avant T5 (noms d'essences), T4 avant T5 (zones). T6 indépendant.

## Avancement
- **T1 — Essences forestières au catalogue : FAIT (2026-07-09).** Ajout des 3
  classes `PerennialWoody` (gabarit `OakTree`, contenu pur, aucune mécanique
  neuve) : `BeechTree` (Hêtre, Fagaceae, ombre dense), `BirchTree` (Bouleau,
  Betulaceae NEUVE, pionnier léger), `HornbeamTree` (Charme, Betulaceae, bocage)
  dans `plants/perennials.py` ; inscrites `hetre`/`bouleau`/`charme` dans
  `PERENNIAL_CATALOGUE` (`plants/catalogue.py`). Voix : **encyclopédie** 3 niveaux
  chacune (`sim/encyclopedie_corpus.py`, 38→41 fiches, assertion `test_encyclopedie`
  ajustée). **Magazine** = data-driven (dérive familles du catalogue → offre
  automatique, Fagaceae/Betulaceae, aucun code touché). Carnet (`CONCEPT_DE` keyé
  par événement, pas par espèce) et pages (lore optionnel) = pas d'entrée requise.
  **Golden NEUTRE — hash INCHANGÉ** `24ec11e7983595e71c4587fce8f558a1bec9eb5ec8511bf69ad76e9fdc2b6e91`.
  Suites vertes : golden, encyclopedie (68/68), magazine (23/23), genetique (20/20),
  carnet, pages, catalogue_mulch. NON committé (Nico commit).

- **T2 — Fleurs par famille : FAIT (2026-07-09).** Nouveau partial VUE
  `visuals/PlantRenderer.Flower.cs` (132 ldc) : `enum FlowerShape` (6 archétypes
  Simple/Ombelle/Capitule/Papilionacee/Epi/Clochette) + `record FlowerProfile`
  + table `FlowerProfiles[species]` (mappage par famille, défaut Simple) +
  dispatch `DrawFlowerShape` avec plancher de rayon (`FlowerFloorRadiusPx`) et
  repli LOD (`FlowerShapeMinZoom=4`, aligné feuilles). Chaque sous-corolle passe
  par `DrawVolumeCircle`/`DrawVolumeEllipse` (volume 2 valeurs, E4) ; jitter par
  `Hash01` (canaux 53/59/61 neufs, zéro Random). Couleur INCHANGÉE
  (`OrganPalette.Flower`). `PlantRenderer.Organs.cs` : ancien `DrawFlower`
  (5 pétales génériques) SUPPRIMÉ → migré en `DrawSimple` ; boucle fleurs appelle
  `DrawFlowerShape` avec index de site (déterminisme). Couche B pure, aucun moteur
  touché. **Golden INCHANGÉ** `24ec11e7983595e71c4587fce8f558a1bec9eb5ec8511bf69ad76e9fdc2b6e91`.
  `dotnet build` VERT (0 avert/0 err). LDC Organs.cs 313 (sous 400). NON committé.

- **T3 — Maison normande : FAIT (2026-07-09).** Rendu procédural granite+ardoise
  (réf. Nico Cotentin). Nouveau nœud dédié VUE `visuals/HouseNode.cs` (233 ldc,
  `Node2D` à `_Draw`) : murs = moellons de granite 2-3 valeurs + variété rousse
  au hash + joints chaux + chaînages d'angle (granite clair) + encadrements de
  baies à larmier ; **pignon ouest essenté d'ardoise** (écailles) ; **toit 2 pans
  pentus + croupe** en ardoise (rangs d'écailles pureau serré, faîtage) ; **lucarne
  à bâtière** sur le pan sud (dessinée seulement si sud visible → propre en
  rotation) ; ouvertures (porte sud + fenêtres à petits carreaux, menuiserie
  sombre) ; **souche de cheminée brique orangée** (PAS de fumée, différée D72).
  Éclairement par MUR-MONDE (D35 conservé) modulant la valeur du matériau, zéro
  Random (Hash01 partagé). Extraction : tout le rendu maison sorti de
  `WorldView.Monde.cs` → nouveau partial `world/WorldView.Maison.cs` (60 ldc,
  calcule la géométrie coins/faîte/segment + ombre portée animée inchangée + ghost
  H) ; Monde.cs allégé 155→96 ldc. `Palette16.cs` étendu (bloc MAISON NORMANDE :
  granite mur/clair/roux, joint chaux, ardoise 3 valeurs, brique cuite/ombre,
  menuiserie/vitre). Couche B pure, aucun moteur touché. **Golden INCHANGÉ**
  `24ec11e7983595e71c4587fce8f558a1bec9eb5ec8511bf69ad76e9fdc2b6e91`. `dotnet build`
  VERT (0 avert/0 err). LDC tous < 300. NON committé.

- **T4 — Décor ossature : FAIT (2026-07-10).** Nouveau Node2D VUE
  `visuals/DecorLayer.cs` (146 ldc) : `SurroundingsProfile` (couture d'extensibilité,
  point d'entrée unique `BuildProfile(seed)`), 4 secteurs cardinaux tirés du seed
  (prairie défaut / forêt / rivière), couplage rivière↔falaise + pente figée,
  frontières SINUEUSES (bruit déterministe 3-sinus, zéro Random), aplats volumés
  2 valeurs (lisière/fond) ; ZIndex −5 (derrière le sol), LOD `MaxZoom=4` (visible
  au dézoom), inerte (redraw au build + bascule LOD). **Branchement** dans
  `WorldView.cs` : champ `_decorLayer`, instancié+`Build(Seed)` dans `StartSimulation`
  (AddWorld → SubViewport, survit à RebuildWorld), re-`Build(Seed)` dans
  `RebuildWorld` (`WorldView.Camera.cs`) pour re-projeter à la rotation D35. Node2D
  inerte sans input → hors picking (jardin garde ses clics). **Chemins enherbés** :
  fond gris `FondPierre`→`GazonChemin` (`WorldView.Monde.cs` champ `FondChemin`,
  clear color `WorldView.cs`). Palette16 déjà étendu (bloc DÉCOR + `GazonChemin`).
  Couche B pure, aucun moteur touché. **Golden INCHANGÉ**
  `24ec11e7983595e71c4587fce8f558a1bec9eb5ec8511bf69ad76e9fdc2b6e91`. `dotnet build`
  VERT (0 avert/0 err). NON committé. Note : `Palette16.FondPierre` devient une
  couleur nommée non utilisée en code (catalogue palette conservé, réf. en commentaire).

- **T5 — Décor motifs : FAIT (2026-07-10).** Motifs détaillés peints par-dessus
  l'assise T4. Nouveau partial VUE `visuals/DecorLayer.Arbres.cs` (143 ldc) :
  `enum TreePort` (Etale/Ovoide/Elance/Sinueux/Conique) + `struct TreeSilhouette`
  + table `Silhouettes[species]` (clé nom d'espèce, contrat T1 : chêne/hêtre/
  bouleau/charme/sapin/noyer, port + feuillage + écorce + rayon houppier ADULTE +
  fût). `DrawForet` = scatter sur grille (u×depth) avec **gradient de lisière**
  (proba 0.25→0.92 vers le fond, `PickEssence` bouleau-pionnier au bord → chêne/
  hêtre au cœur, sapin/charme accents ~20 %), tri par Y écran (peintre). Arbre =
  tronc fuselé (chevrons bouleau) + houppier « nuage » d'ellipses volumées 2 valeurs
  (`DrawVolumeBlob` local static, réplique l'invariant pixel-art) par port. Dans
  `DecorLayer.cs` (226 ldc) : `_Draw` en 2 passes (assise puis `DrawMotif`),
  `DrawRiviere` (lit sinueux médian + reflets dithering ordonné 2 teintes),
  `DrawFalaise` (redans étagés 3 valeurs, nb de gradins = pente du profil),
  `DrawPrairie` (semis fleurs blanc/jaune par hash). `Palette16.cs` (77 ldc)
  étendu (bloc T5 : 5 feuillages, 3 écorces, 2 eaux, 3 roches, 2 fleurs). Tout
  statique/déterministe (zéro Random, hash `HashKey`/`Ondulation`), cullé par le
  LOD global. Couche B pure, aucun moteur touché. **Golden INCHANGÉ**
  `24ec11e7983595e71c4587fce8f558a1bec9eb5ec8511bf69ad76e9fdc2b6e91`. `dotnet build`
  VERT (0 avert/0 err). LDC tous < 300. NON committé.

- **T6 — Feuilles fidèles au modèle réel : FAIT (2026-07-10).** Nouveau partial
  VUE `visuals/PlantRenderer.LeafOutline.cs` (166 ldc) : contour de silhouette
  AUTHORÉ par espèce, tracé au **palier haut ×16+** UNIQUEMENT. `enum LeafMargin`
  (Entiere/Dentee/Lobee) + `record OutlineSpec` (Aspect/Marge/Lobes/LobeCut/Tip/
  BaseCut/Compound) + table `LeafOutlines[species]` couvrant **37 espèces**
  (toutes les feuillues du catalogue, clé = nom de classe Python). Contour
  SYNTHÉTISÉ depuis le descripteur compact réglé à la main (fidèle : chêne lobes
  arrondis+sinus, figuier palmatilobé, tomate/carotte/frêne composées pennées,
  pommier/cerisier ovale denté, pissenlit runciné, ortie cordée dentée…).
  `BuildLeafPolygon` = demi-limbe elliptique modulé par la marge (dents = sinus
  18 périodes + micro-jitter hash ; lobes = festons profonds), effilement du
  sommet (Tip), échancrure basale (BaseCut), refermé en miroir. `DrawVolumePolygon`
  = **E4 sur contour libre** : polygone ombré plein + copie réduite 0,8 décalée
  au SUD éclairée (croissant nord conservé, réplique `DrawVolumeEllipse`).
  `DrawCompoundOutline` = rachis + N folioles opposées obliques + terminale, chaque
  foliole un contour volumé. Nervures réutilisent `DrawLeafVeins` (penninerve/
  palmée/composée selon la topologie). **LOD 3 paliers** : dispatch branché dans
  `DrawShapeBySpecies` (`Leaf.cs`) — ×16+ contour fidèle (repli archétype si espèce
  non mappée), [4,16[ archétype d'ellipses inchangé, <4 tache. Zéro Random (hash
  canaux 41/51). Couche B pure, aucun moteur touché. **Golden INCHANGÉ**
  `24ec11e7983595e71c4587fce8f558a1bec9eb5ec8511bf69ad76e9fdc2b6e91`. `dotnet build`
  VERT (0 avert/0 err). LDC LeafOutline.cs 166, Leaf.cs 212 (tous < 300). NON committé.

## §REPRISE
Sprint FIGÉ — **TERMINÉ**. **T1 + T2 + T3 + T4 + T5 + T6 TOUS FAITS** (voir
Avancement). Tous couche B (sauf T1 moteur NEUTRE), golden INCHANGÉ partout
`24ec11e7983595e71c4587fce8f558a1bec9eb5ec8511bf69ad76e9fdc2b6e91`, `dotnet build`
vert. Reste : **commits** (T4/T5/T6 + décor NON committés) et **F5 Nico** (recette
par tronçon). Dettes ouvertes en parallèle : **D72 vent**, **D73 terraforming**
(dans DETTE.md). Note : `MakeLozenge` (Monde.cs) est du code mort PRÉEXISTANT
(référencé seulement en commentaires) — laissé en place, à signaler.
