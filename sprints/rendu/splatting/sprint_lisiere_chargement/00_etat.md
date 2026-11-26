# sprint_lisiere_chargement — état (S3 du style homogène)

**Conception FIGÉE le 2026-11-26** (`/conception`, Nico : « vas-y ») → `docs/rendu/splatting/conception_lisiere_chargement.md`.
**CLOS côté code le 2026-11-26** (`/sprint-auto`, ①→⑤).
Source : `docs/rendu/splatting/backlog_splatting.md` (S3 = (b) lisière + (g) chargement),
`conception_reliquats_plantes.md` §2 (E2 : barre de progression permise à l'écran de chargement,
philo #5 = pendant le jeu seulement), `conception_bois_arbres.md` (C2 : `RubanTexture` réutilisable).
Golden attendu : `bce813af…` INTACT (vue + outillage, `data/code/` jamais modifié).

## Faits vérifiés au code (2026-11-26)
- Lisière = `DecorLayer` (19 partials) : UNE maille (ArrayMesh) par palier ×0,5/×1/×2/×4, un seul
  atlas de CODES (palette indexée, dialecte 2, `DecorLayer.KitCodes.cs`), shader `decor_indexe.gdshader`
  (saison par bouquet, neige, givre, vent). `MaxZoom = 4` : à ×8-×32 la maille ×4 est grossie.
- Kit du décor (`DecorLayer.Kit.cs`) : 10 formes peintes à la règle (Herbe, HerbeHaute, Fleur, Roncier,
  SousBois, Feuillu, Conifere, Galet, Bloc, Roseau) × 1-5 tailles × 3 variantes × 16 teintes.
- Arbres de lisière : silhouettes par essence (`DecorLayer.Arbres.cs`, 8 essences : chêne, hêtre,
  bouleau, charme, sapin, noyer, aulne, saule — toutes dans les 12 écorces de S2) ; dessin =
  ombre → tronc cerné → charpentières en traits (`DecorLayer.Branches.cs`) → enveloppe → bouquets du kit.
- Adaptateur existant pour les plantes : `PlantRenderer.KitSplats.cs` (planche splat → même format
  que le kit généré, interrupteur Maj+F11 / `SYMBIOSE_SPLATS=0`).
- Chargement (`world/WorldView.Chargement.cs`) : fond uni + touffe ×8 + « Le jardin se prépare ».
  Séquence : 2 images → `AssurerGerbes` (BLOQUANT) → `StartSimulation` (`_bridge.Init` BLOQUANT +
  montage) → cuisson du cadre (`BakeQueue.ModeChargement`, jusqu'au repos ou 30 s).
  Le pont a déjà un verrou d'I/O et sert déjà depuis `Task.Run` (step, action, fields).
- S2 laisse un reste : recette « rameau aplati » du sapin (aiguilles ×8-×32) non cuite.

## Décisions arrêtées (Nico, lot 1, 2026-11-26)
- **L1 Arbres de lisière = silhouette améliorée** : architecture gardée (ombre, tronc, charpentières,
  enveloppe, bouquets) ; charpente en `RubanTexture` + écorce cuite S2 (bandes recopiées dans l'atlas
  du décor → un seul envoi), pied évasé, sapin en étages, bouquets feuillus/conifères en pièces splat.
  Saison pied par pied, neige, vent : inchangés (shader). Raison : centaines d'arbres, imposteurs =
  une variante par saison/état et perte de la saison qui gagne le bois.
- **L2 Paliers ×8-×32 = atlas par palier** : même géométrie (maille ×4), atlas des pièces cuit 2×/4×/8×
  plus fin, permuté au changement de palier → pixel natif partout. ~64 Mo à ×32 [estimé, non mesuré],
  sous le budget 1 Go (E6). Grains procéduraux du shader (roche, eau, neige, givre) : constater au-delà
  de ×4 par capture et les caler sur la même règle.
- **L3 Mycélium = carte des âges + mycorhize** : image splat cuite hors ligne (illustration en palette
  pleine, comme les portraits) + carte « date d'apparition » par pixel ; le shader révèle âge ≤
  progression, front lumineux aux pointes. Récit : spore qui germe → hyphes qui s'arborisent →
  rejoignent la racine d'une plantule (manteau mycorhizien) → petit carpophore à 100 %. Porte de
  décision : maquette mesurée (carte des âges lisible au mélange gaussien ; repli = N images cuites).
- **L4 (Claude)** : rameau aplati du sapin cuit en S3, sert la lisière ET le sapin du jardin ×8-×32
  (reste de S2).
- **L5 (Claude)** : `_bridge.Init` part en `Task.Run` (verrou d'I/O existant) → l'écran vit pendant
  l'init ; montage seul sur le fil principal (gel mesuré). Progression MONOTONE pondérée par phases
  mesurées (gerbes, init, montage, cuisson du cadre = 1 − file restante / file initiale).

## Tronçons (golden `bce813af…` intact partout)
| # | Kickoff | État |
|---|---|---|
| ① | `01_kit_lisiere.md` — kit de lisière en splats + rameau aplati | **fait** (F5 attendu) |
| ② | `02_arbres_lisiere.md` — arbres de lisière sur le bois de S2 + sapin du jardin ×8-×32 | **fait** (F5 attendu) |
| ③ | `03_paliers_hauts.md` — atlas par palier ×8-×32 | **fait** (F5 attendu) |
| ④ | `04_chargement_mycelium.md` — écran de chargement en mycélium (porte : maquette) | **fait** (F5 attendu) |
| ⑤ | `05_revue_f5.md` — revue, liste F5 exhaustive S1+S2+S3, clôture | **fait** (F5 complet attendu) |
Ordre : ① avant ②③ ; ④ indépendant ; ⑤ en dernier.

## Compte rendu ① (2026-11-26)
- **Recettes** : fabrique `tools/splat/recettes/lisiere.js` + 10 `lisiere_<forme>.js` (planche `kit`,
  cases = `Tailles` de `DecorLayer.Kit.cs` recopiées dans `BOITES` — à garder en phase). Réutilisées :
  corolle de `fleuron` (fleurette, face tournée vers l'œil sinon 3×1 px), `feuille_composee` (roncier
  en dôme + 3 cannes), `feuille_plume` (sous-bois), `feuille_ovale` (bouquet feuillu en dôme),
  arc de `feuille_ruban` (herbes, feuilles du roseau), sculpteur mandataire des portraits (`place`).
  Neuves : `rameau_aplati.js` (L4, couches aiguilles | stomates, cuit aux 7 paliers pour ②),
  galet, bloc (deux pavés), roseau (tiges + massette en couche 1).
- **Outil** : `cuire.js` accepte `boites: [[w,h]…]` — zoom ajusté (≤ 10 photos, dichotomie) pour
  REMPLIR la case sans la dépasser. Chemin `tailles`/paliers inchangé (fleuron recuit identique à l'octet).
- **Adaptateur** `visuals/DecorLayer.KitSplats.cs` : couches fondues sur l'attache, pièce posée en
  bas-centre de sa case (= ancrage de `PoserPiece`), codes G copiés ; fleurette → orientation
  `OrientFleur`, cœur ton 4 ; massette → ton 0. Pièce absente → kit généré entier + avertissement.
- **Écart au kickoff** : la bascule Maj+F11 ne reconstruit PAS les mailles — les cases ne bougent
  pas d'une source à l'autre, l'atlas est réécrit en place et renvoyé (`DecorLayer.BasculerSplats`,
  appelé par `WorldView.Controls`). Non testable au banc (pas de touche simulée) → **F5**.
- **Mesures** (`mesures/01_*`) : banc F10 `full`, avant (`SYMBIOSE_SPLATS=0`) / après, ×0,5 ×1 ×2 ×4,
  -w 44. Effet net sur les bouquets de houppier (bulles → feuillage), roseaux dressés à massette,
  blocs anguleux ; herbes de prairie plus pâles et moins contrastées que les grains d'avant (à juger F5).
  Lecture du kit splat : 37-102 ms [VM chargée 4-8, n=2], une fois par partie. Maille ×2
  construite : 250-487 ms avant / 249-489 ms après [VM chargée, n=3 par côté, bruit > écart] → pas
  de régression visible. `assets/splats/` : 66 Mo (+0,8 Mo), sous l'alerte 200 Mo.
- Cuisson : `lisiere_conifere` ~25 min [VM chargée, n=1] (21 rameaux posés × 3 variantes) — à
  ne recuire que si la recette change.

## Compte rendu ② (2026-11-26)
- **Lisière** (`visuals/DecorLayer.Charpente.cs`, neuf) : fût, axe et charpentières en rubans (`RubanTexture`
  `Normales` + `PoserBandePeriodique` + `Verser` dans le lot du décor → passent par l'encodeur de sommets :
  plan, vent, phase du pied). Flancs = aplats orientés par la normale du ruban (soleil réel) ; fût à pied
  évasé (+60 % au sol, éteint à 15 %) et légère flèche au hash ; charpentière = courbe du 2ᵉ degré passant
  par départ/coude/bout (reste dans l'ellipse) ; plus de cerne. Sapin en étages (3-8 rangs de bouquets
  conifères, plus courts vers le haut, bouts retombants, enveloppe sombre entre deux rangs).
- **UN envoi gardé** : bandes branche + tronc des 8 essences (×4) recopiées dans l'atlas du décor
  (`RangerEcorces`, à la suite des étagères du kit ; palette de l'écorce, classe inerte pour le tronc,
  sans saison pour la branche). Accès brut : `BandesCuites.CodesBruts` (+ `d_cm` lu du manifeste),
  `Ecorces.CodesBruts`. Draw calls de la lisière inchangés (1 maille).
- **Écart au kickoff (mesuré)** : la bande ×4 réduite au-delà de 2 texels/px tourne au sel (bouleau gris
  tacheté à ×1-×2, capture du 1er essai). Règle ajoutée (`EcorceReductionMax` = 2) : on réduit d'abord le
  nombre de colonnes côte à côte (≤ 3, selon `d_cm`), et si même une colonne est trop réduite, pas de
  bande : le fût garde les stries procédurales (orient. 11/12) et le bouleau ses lenticelles. Résultat :
  écorce cuite sur les fûts larges à ×2, partout à ×4 ; ×0,5-×1 = ruban lissé + stries. ③ (atlas ×8-×32)
  devra recopier les bandes du palier (même `CodesBruts`).
- **Interrupteur** : Maj+F11 change aussi la géométrie → `_versionBois` + `SuivreBois` (appelé par
  `AvancerFond`) jettent les mailles. Non testable au banc (touche) → **F5**.
- **Sapin du jardin ×8-×32** (`PlantRenderer.SapinRameaux.cs`, neuf ; crochet dans `DrawFeuillesHouppier`) :
  un `rameau_aplati` tous les 8 cm de chaque rameau/brindille du petit bois, alternés ±0,45 rad, lacet et
  inclinaison du brin, même densité/tons/tri ; couche `stomates` = ton clair (`CouleurCouche`). Effet net :
  le poteau hérissé de tirets devient un sapin en rameaux plats (planches ×8, ×32).
- **Mesures** (banc `full -B`, forêt N, `-c 1000,-300`, ×1/×2/×4, été -w 6 / hiver -w 32 ; sapin :
  `-b houppiers -c 1775,1025 -l 2 -n 220 -w 28 -H` ; captures `mesures/02_*`, avant = HEAD ①). Sommets de
  la maille avant → après : ×1 129 684 → 149 112 (+15 %), ×2 149 532 → 187 650 (+25 %), ×4 149 532 →
  237 240 (+59 %) [n=2 saisons, identiques]. Construction : avant 250-410 ms, après 318-400 ms [VM chargée
  5-10, n=2 par palier] : bruit > écart, pas de hausse mesurable ; le 30-37 ms du kickoff est une
  référence PC, non reproduite ici → à relire au rapport C du PC. Draw calls : 1 maille, inchangé.
  `assets/splats/` 66 Mo (inchangé, rien cuit).
- Ripisylve : le banc F10 ne porte pas de dominante (pas d'aulne/saule semés) → non capturée, **F5**.
- **F5 ②** : Maj+F11 sur la lisière (bois reconstruit) ; ripisylve aulne/saule ; écorce du bouleau à ×4
  (marques grises denses, celles de la bande S2) ; sapin de lisière en étages (lisibilité, nombre de rangs) ;
  sapin du jardin ×8-×32 (pas de 8 cm, écart ±0,45 rad, ton des stomates).

## Compte rendu ③ (2026-11-26)
- **Atlas par palier** (`visuals/DecorLayer.Hauts.cs`, neuf) : au-delà de ×4, la maille ×4 reçoit un atlas k = 2/4/8
  fois plus fin, mêmes UV (case ×4 (x,y,w,h) → (kx,ky,kw,kh)). Contenu : atlas ×4 agrandi k×k (texels-codes
  des aplats + repli), puis pièces du kit cuites k× (`<recette>_hauts`, planches `x8/x16/x32`), puis bandes
  d'écorce du palier ×4k (`Ecorces.CodesBruts`) rééchantillonnées sur la case agrandie (tailles cuites ≠ k×
  celles de ×4 : 16×26 → 28×50 à ×8). Repli forme par forme si une recette `_hauts` manque.
- **Cuisson** : `cuire.js --echelles 2,4,8` (nouvelle option ; ×4 ni recuit ni touché). 10 recettes, 369 pièces,
  ~3 h 15 [VM chargée 7-10, n=1] (conifère 58 min, roseau 43 min, herbe haute 34 min). `assets/splats/` +0,5 Mo (67 Mo).
- **Permutation** : `_Draw` choisit la texture (`TextureDecor`), la couche devant suit ; `_Process` redessine au
  changement de palier même quand `ZoomMaille` reste 4. Un seul atlas haut vit (les autres rendus au GPU à
  l'image suivante), compté dans `BudgetCuisson` (ligne « lisière N Mo »).
- **Écart au kickoff (mesuré)** : construire ×32 sur le fil principal = 746 ms [VM chargée ~10, n=1] → à-coup neuf.
  Construction passée en tâche de fond (`Task.Run` pour les octets ; lectures Godot sur le fil principal) ; en
  attendant, l'atlas ×4 grossi (image d'avant ③). Reste au fil principal, 1ʳᵉ arrivée au palier : préparation
  56-107 ms (×8), 127-138 ms (×16), 378-396 ms (×32) + envoi GPU 9-13 / 40-44 / 155-306 ms
  [VM llvmpipe chargée, n=3 bords] ; les planches et bandes sont gardées → retours suivants : envoi seul.
  À relire au PC (rapport C) : si l'envoi ×32 gêne, découper l'envoi.
- **Mémoire mesurée** : ×8 1024×1612 = 6,3 Mo · ×16 2048×3224 = 25,2 Mo · ×32 4096×6448 = 100,8 Mo (> 64 Mo
  estimés : l'atlas ×4 fait 512×806 — 16 teintes × toutes les formes). Un seul vit → ≤ 101 Mo, sous 1 Go.
- **Grains du shader** : capture avant = pavés grossis (roche ×16 en blocs 4 px, tissage, écorce). L'uniform `zoom`
  valait `ZoomMaille` (≤ 4) → il vaut désormais le palier RÉEL (`DecorLayer.Vent.cs`) : tissage, roche, écorce,
  neige, givre, brume et calage du vent au pixel natif (même règle que ×0,5-×4 : plus de motifs en zoomant).
- **`EauScintillement`** : était ÉTEINT au-delà de ×4 (miroir périmé de MaxZoom) → allumé jusqu'à ×32, px du palier réel.
- **Captures** `mesures/03_avant|apres_{foret_x8,x16,x32, falaise_x16, riviere_x32}.png` (banc `full -B`, -w 2) +
  `03_controle_conifere_hauts.png`. Effet net : écorce de bouleau, herbes, fougères, galets et sol au pixel natif.
- **F5 ③** : zoom ×4→×8→×16→×32 sur chaque bord (à-coup ressenti à la 1ʳᵉ arrivée ×32 ; bascule « grossi → net »
  visible ~1 s) ; roche de falaise à ×16-×32 (grain natif très fin, lit comme du gravier : à juger) ; neige/givre
  à ×16-×32 en hiver (non capturés) ; étincelles de rivière à ×8-×32 (3 px natifs, discrètes) ; Maj+F11 à ×16.

## Compte rendu ④ (2026-11-26)
- **Porte de décision : CARTE DES ÂGES RETENUE (mesurée).** Âge d'un pixel = âge du splat PROPRIÉTAIRE (passe
  `splatId`), porté nativement par ink-studio (`born`, flag 512, `data[15]`). Maquette (`mesures/04_maquette_p*.png`,
  gauche = vue par la carte, droite = VÉRITÉ = ink rendu au temps t = p) : écart sur les pixels du mycélium
  p=0,1 : 37 px / 509 révélés · p=0,4 : 54 / 3 409 · p=0,7 : 43 / 7 246 · p=1 : 2 / 9 127 [n=1 cuisson] ; tous
  « manquants » au front (≤ 1 px de retard à la pointe, couvert par la lueur), 0-1 « en trop » ; ni halo ni
  pointillé à l'œil. Pas de repli en N images.
- **Écart au kickoff (conception)** : une seule image couleur ne peut pas montrer la racine NUE puis GAINÉE (le
  manteau en devient propriétaire → trous dans la racine avant p = 0,74). D'où **deux couches dans la texture
  couleur** : `mycelium_couleur.png` 960×270 = fond (scène SANS mycélium, rendue à part) | mycélium (pixels dont le
  propriétaire a un âge, couleurs de la scène complète → occlusions justes) ; `mycelium_ages.png` 480×270
  (gris = âge × 255, 0 réservé). Poids : 20,9 ko + 15,2 ko. Résolution 480×270 affichée ×4 (hyphes de 1 px nettes).
- **Scène** (`tools/splat/recettes/mycelium.js` + `cuire_mycelium.js`, README) : coupe de sol, spore → réseau à pousse
  SYNCHRONE (âge ∝ distance le long des hyphes, chimiotropisme vers la racine, anastomose), contact à 0,74, manteau =
  2 hyphes en hélice autour du pivot 0,74→0,88, carpophore (laccaire) 0,88→1 (pied ∝ hauteur, chapeau en dernier).
  196 649 splats, 1 105 nœuds, cuisson ~2,5 min [VM charge 3-4, n=2]. Zéro `Math.random` (hash `KIT.hash`).
- **Shader** `visuals/chargement_mycelium.gdshader` : âge ≤ p → mycélium, front = lueur sur 0,035 d'âge ; sinon fond.
- **Chargement non bloquant (L5), vérifié au code** : `PreparerGerbes` (octets + `Image`, hors fil) / `EnvoyerGerbes`
  (`ImageTexture`, fil principal) ; `StartSimulation` scindé en `PreparerMonde` (pont seul : init + warmup + snapshot,
  `Task.Run`) / `MonterMonde` (arbre de scène). Personne d'autre ne parle au pont pendant l'init (`_Process` et
  `_UnhandledInput` coupés par `_started`, sélecteur libéré, `_Input` n'écoute que la souris) ; `_ExitTree` attend
  la tâche avant `quit`. Chemin sans écran (`StartSimulation`) inchangé (capture smoke vérifiée).
- **Progression (L6)** `world/ProgressionChargement.cs` (classe pure) : parts {gerbes 0,01 · pont 0,46 · montage 0,05 ·
  cuisson 0,48} = durées mesurées ; τ pont 10 s ; cuisson = 1 − file restante / file max (`BakeQueue.FileEligibles`) ;
  max + lissage 1er ordre ; l'écran attend la valeur 1 (carpophore sorti) avant d'ouvrir. Filet 30 s conservé.
- **Mesures** (`capture_vm.sh -b full -J`, journal `[Chargement] phases`) : gerbes 386-395 ms (calcul 125 ms hors fil,
  envoi 15-17 ms) · pont 14,9 s (warmup 10,3-10,4 s) · montage 1,6-1,7 s dont **gel 1 396-1 432 ms** · cuisson
  15,0-15,6 s (20 images : la cuisson elle-même gèle ~0,75 s/image) · total 34,2-35,9 s [VM llvmpipe charge 3,4-4,4,
  n=2]. Avant (code ③) : tout le pont + montage gelés 19,6 s d'un bloc. Captures `mesures/04_chargement_image{02,30,
  56,66,74}.png` (spore → réseau → front à la racine → manteau → carpophore).
- **F5 ④** : le mycélium pousse pendant l'init (fluide, pas d'à-coup) ; gel du montage (~1,4 s VM) et cuisson du cadre
  saccadée (à relire au PC) ; lisibilité du récit (spore, mycorhize, champignon) ; texte « Le jardin se prépare » en
  bas, croisé par 2-3 hyphes (à juger) ; parts/τ à recaler sur les durées du PC (log `[Chargement] phases`).
- `PlantRenderer.TouffeChargement` n'a plus d'appelant (gardé, règle « ne jamais jeter de code »).

## Compte rendu ⑤ (2026-11-26)
- **Planches** (`capture_vm.sh -b full`, `-B` sauf friche ; avant = `SYMBIOSE_SPLATS=0`) → `mesures/05_*.png` (14) :
  ×1 ensemble été (A/B) · ×2 prairie printemps (A/B) · ×4 forêt automne (A/B) · ×8 friche été (A/B) · ×16 falaise
  neige (A/B) · ×32 forêt neige · ×4 rivière vent 0,8 + rotation D35 1 · ×32 prairie vent · ×0,5 rotation 2.
  Effet net : bouleaux de lisière à écorce cuite et pied évasé (contre fûts unis à traits noirs) ; ensemble ×0,5
  homogène, rotation propre. À juger (versé à la liste F5) : neige « camouflage » ×16-×32, rivière ×4 en aplats
  (famille (e), hors S3), friche ×8 clairsemée, prairie ×32 rare, bandes de sol nu de la prairie (préexistant).
- **Finition** : message de repli d'une planche haute absente → « forme ×4 agrandie » (`DecorLayer.KitSplats.cs`,
  point remonté par ③). Aucune recette neuve, aucun seuil changé (rien de laid mesuré qui en relève).
- **Perf** (`perf_vm.sh -b full`, VM llvmpipe charge 3,2-3,9 [n=6 relevés de 1 s, non transposable]) : ×0,5 243,8 ms
  [276 draw calls, cuisson en cours : 6 gels > 250 ms] · ×4 58,0 ms [71] · ×32 54,0 ms [57] — draw calls identiques à
  S2 (71/57).
- **Mémoire** (journal des captures, n=1) : atlas lisière ×16 25,2 Mo (préparation 151 ms + envoi 44 ms) · ×32 100,8 Mo
  (préparation 364-374 ms + envoi 303-330 ms, fil principal) ; précuisson ×32 forêt 637/1024 Mo (lisière 101),
  1 plante en repli (Alder). Kit splats lu 38-44 ms.
- **Refactor auto-léger** : fichiers touchés par S3 tous < 300 LDC sauf `WorldView.cs` **313** (🟡, était 303 avant S3,
  une responsabilité, signalé) ; `DecorLayer.Kit.cs` 246, `DecorLayer.cs` 231 → rien à scinder.
- **Clôture** : `journal/204_…` + `journal.md`, `backlog_splatting.md` (S3 et séquence CLOS). `BACKLOG.md` = index
  (inchangé, la ligne `rendu/splatting` pointe déjà le fragment). `DETTE.md` inchangé (aucune dette neuve ouverte :
  les restes vont à la liste F5, règle « pas de dette sans en fermer une »).

## F5 EXHAUSTIF — séquence « style homogène » S1 + S2 + S3 (à jouer en une fois)
Fusionne les sections « F5 consolidé » de S1 (`sprint_reliquats_plantes/00_etat.md`), S2
(`sprint_bois_arbres/00_etat.md`), le F5 du sprint (a) (`sprint_precuisson_splats/00_etat.md` §F5) et les
points ①→⑤ de S3. Une case = une observation. Chiffres VM = llvmpipe chargée, **non transposables au PC**.

**Outils du F5** : **L** planche des paliers ×0,5→×32 sur la plante visée · **F10** banc décor (4 motifs :
N forêt · E rivière · S falaise · O prairie ; la friche n'apparaît que hors banc, selon le seed) · **H** maison
+ lisière transparentes · **PgUp/PgDn** rotation D35 · **Maj+F11** ancien dessin (plantes, bois, lisière) ·
**C** rapport (précuisson X/1024 Mo, plantes en repli, `[Chargement] phases`) · **F4** perf · **Z** balayage
des à-coups de zoom. Bancs : monde `full` (ensemble), `planche_especes` (40 herbacées), `houppiers` /
`houppiers_25` (12 arbres, jouer jusqu'en hiver pour le bois nu), `verger_floraison`.

### 1. Écran de chargement (S3 ④)
- [ ] Au lancement, le mycélium pousse **pendant** l'init du moteur : animation fluide, sans à-coup (VM : le
      pont tourne désormais hors du fil principal).
- [ ] Récit lisible dans l'ordre : spore qui germe → hyphes qui s'arborisent → elles rejoignent la racine
      d'une plantule → manteau autour de la racine (mycorhize) → petit champignon (laccaire) à 100 %.
- [ ] Le front lumineux suit les pointes (ni halo, ni pointillé).
- [ ] Progression **monotone** : jamais de recul, pas de long palier figé ; l'écran n'ouvre qu'une fois le
      champignon sorti.
- [ ] Gel du montage du monde (VM ~1,4 s) : perceptible sur le PC ? Gênant ?
- [ ] Cuisson du cadre (dernière moitié de la barre) : saccadée (VM ~0,75 s/image) — acceptable sur le PC ?
- [ ] Texte « Le jardin se prépare » en bas : croisé par 2-3 hyphes — gênant ?
- [ ] Durée totale (VM 34-36 s) ; relever la ligne `[Chargement] phases` du journal pour recaler les
      parts (gerbes 0,01 · pont 0,46 · montage 0,05 · cuisson 0,48) et τ pont 10 s sur le PC.

### 2. Jardin, palier par palier (monde `full`, puis F10)
- [ ] ×0,5 et ×1 : ensemble homogène, aucune plante ni arbre qui « détonne » par son style.
- [ ] Aucune bascule laide d'un palier au suivant (taille, détail qui apparaît/disparaît d'un coup) ;
      sauts de classe de taille des feuilles (×1,4 à ×2,8 d'un coup) visibles ? gênants ?
- [ ] ×1 → ×2 : têtes, fleurs, fruits passent du dessin aux pièces — la bascule se voit-elle trop ?
- [ ] ×4 → ×8 : la lisière passe à l'atlas ×8 (bascule « grossi → net » ~1 s visible à la 1ʳᵉ arrivée).
- [ ] ×32 : tout est en volume (aucune plante en dessin plat). 1ʳᵉ arrivée à ×32 : à-coup (VM : 1-2 s par
      grande plante + préparation de l'atlas de lisière ~380 ms + envoi GPU 155-306 ms) — acceptable ?
      Les retours suivants à ×32 doivent être sans à-coup.
- [ ] Rotation D35 (PgUp/PgDn) à ×4 et ×32 : feuilles, bois et lisière tournent sans « sauter ».
- [ ] Vent fort : feuilles et rameaux suivent la tige sans clignoter ; bouquets et arbres de lisière plient.

### 3. Plantes herbacées (banc `planche_especes`, touche L)
- [ ] Feuilles, têtes et fruits en VOLUME, côté éclairé qui suit le soleil (heure qui tourne).
- [ ] `tailler` marche toujours au pied (taille au port).
- [ ] **Tomate** ×8-×32 : folioles en volume ; ×32 poils fins vert pâle (PAS de points blancs façon oïdium).
- [ ] **Tournesol** ×2-×32 : tête de face, cœur brun foncé ; ×16-×32 nervures + poils ; tige ×32 non décalée.
- [ ] **Fraisier** ×8 : taille feuilles/fleurs ; ×32 poils discrets ; fraises **brunes** — voulu ?
- [ ] **Courgette** ×16 : paume assez grande ? pâle et plate ? feuilles vues par la tranche ; trompette ×32.
- [ ] **Carotte** ×2-×16 : rosette plume, ombelle en pièce ; ombelle **orange** — voulu ?
- [ ] **Trèfle** tous paliers : tapis de 3 folioles, V clair ×16 ; un pied `quatre_feuilles` en X.
- [ ] **Plantain** ×4-×32 : feuilles trop larges et pennées (pièce générique) — recette dédiée ? épi trop long ?
- [ ] **Blé** ×8-×32 en fleur : anthères pâles. **Fétuque** ×2-×16 : panicules rousses lisibles.
- [ ] **Thym** ×8-×32 : coussin de rameaux, ou dôme sombre plat trop visible ?
- [ ] **Lavande** ×8-×32 : lames trop sombres ? épis. **Lierre** ×8 nervures pâles ; baies.
- [ ] **Haricot** ×1-×32 : triades, gousses, fleurs-papillons ; grimpe sur ses appuis.
- [ ] **Drosera** ×8 perles, ×16 tentacules : trop chargé ?
- [ ] **Bourrache** ×8 duvet, ×32 nervures + poils : trop chargé ? feuilles bicolores trop contrastées ?
- [ ] **Molène** ×2-×16 : épi jaune sur tout le tiers haut ; rosette à la taille du dessin ; duvet ×8.
- [ ] **Armoise / framboisier** ×4 revers ; **basilic / poivron** ×4 éclat ; **ail** ×32 pruine ; **consoude** ×32 poils.
- [ ] **Myrtille** : pas de baies en jeu (moteur, D134) — seulement au portrait.
- [ ] Fleurons des plantes sans fiche ×1-×2 : cœur jaune.
- [ ] Taille des feuilles de loin (×0,5-×2 : myrtille, haricot plus feuillus ; rosette de molène plus petite).

### 4. Arbres du jardin (banc `houppiers`, hiver nu ×8-×32 sauf mention)
- [ ] Tronc et charpentières sans marche ni coude ×4→×32 ; pied évasé ; cols de branche.
- [ ] Départ d'une branche posée devant le tronc : rond sombre — naturel ou « trou » ? Branche partie
      derrière : passe derrière.
- [ ] Branches en U (noyer, saule ; géométrie moteur) : acceptable ?
- [ ] Marche de couleur à certains nœuds (aulne ×16) : gênante ?
- [ ] Écorces grises (hêtre, noyer, charme, sapin) trop claires, confondues avec le bouleau de loin ?
- [ ] Écorce : fondu rameau/branche/tronc ; côté soleil/ombre ; neige et surbrillance par-dessus ; petit bois effilé.
- [ ] Squelette d'arbre mort : tube lisse gris uni — voulu ?
- [ ] Taille : surbrillance qui suit la courbe, coupe là où l'on vise (pommier, latéral du sapin).
- [ ] **Pommier** plaques gris-brun ; ×4 en fleur (`verger_floraison`) : bouquets (pompons trop gros ?), saut ×4→×8.
- [ ] **Cerisier** brun-rouge, lenticelles horizontales ; montée de floraison.
- [ ] **Noyer** losanges clairs (trop contrasté ?) · **Chêne** crevasses · **Hêtre** lisse · **Charme**
      cannelures · **Aulne** fissures sombres · **Saule** réseau, charpentières basses arquées.
- [ ] **Bouleau** blanc, lenticelles, base crevassée (VM : gris-bleu, pas noire) ; pleureur.
- [ ] **Noisetier** brun-rouge, lenticelles pâles · **Figuier** gris lisse (un tronc : moteur).
- [ ] **Sapin** ×1→×4 cône, étages, pointe ; **×8-×32 rameaux aplatis** (S3 ②, tous les 8 cm, ±0,45 rad,
      stomates clairs) : la masse tient-elle au saut ×4→×8 ? tronc gris très clair.
- [ ] Chatons (noyer, noisetier) en floraison réelle.

### 5. Graminées
- [ ] Dactyle/blé ×16-×32 nervures + cœur clair ; seigle/pâturin ×32 ; seigle retombant, directions variées.
- [ ] Pas de moirage gênant ; vent qui plie ; paille d'automne.
- [ ] Petites taches vert sombre sur les brins du dactyle ×16-×32 (VM) : qu'est-ce ?

### 6. Lisière (F10, chaque bord, ×0,5 → ×32, 4 saisons)
- [ ] **Prairie** (O) : herbes en arcs, fleurettes de face ; herbes **plus pâles / moins contrastées**
      qu'avant (S3 ①) — à garder ? ×32 : touffes splat belles mais rares sur un tissage uniforme ; ×2 : bandes de
      sol nu en damier (avant comme après, `05_x2_prairie_printemps_*`).
- [ ] **Forêt** (N) : bouquets de feuillage (plus de bulles), arbres de lisière à charpente en rubans,
      pied évasé, flèche légère ; écorce cuite sur les fûts larges dès ×2, partout à ×4 ; ×0,5-×1 ruban
      lissé + stries (seuil `EcorceReductionMax` = 2 : à juger).
- [ ] **Bouleau de lisière** ×4 : marques grises denses (celles de la bande S2) ; fûts très blancs de loin.
- [ ] **Sapin de lisière** en étages (3-8 rangs) : lisible ? nombre de rangs ?
- [ ] **Ripisylve aulne/saule** (au bord de la rivière, seed qui en porte) : jamais capturée au banc.
- [ ] **Rivière** (E) : roseaux dressés à massette ; étincelles d'eau jusqu'à ×32 (3 px natifs, discrètes ?) ;
      ×4 : eau et berge en grands aplats sans texture, berge de sable presque nue (`05_x4_riviere_vent_r1_ap`, famille (e) sol/eau).
- [ ] **Falaise** (S) : blocs anguleux ; roche ×16-×32 au grain natif très fin — lit-elle comme du gravier ?
- [ ] **Friche** (hors banc, seed avec E/O en friche) : ronciers en dôme + cannes, sous-bois en plumes ; ×8 très
      clairsemée (touffes rousses, fleurettes en points blancs de 3 px, capture ⑤) — assez vivante ?
- [ ] Saison par bouquet (automne qui gagne le bois), hiver : neige et givre sur la lisière à ×16-×32 — capture ⑤ :
      neige en grosses taches blanc/sable « camouflage » sur tout le sol (`05_x16_falaise_neige_ap`, `05_x32_foret_neige_ap`), à juger.
- [ ] ×8-×32 : herbes, fougères, galets, écorces au pixel natif (plus de gros pavés grossis).

### 7. Encyclopédie, magazine, portraits
- [ ] Encyclopédie → Plantes, espèce vue : un portrait « jeune » ; après `palier3` : les trois — le portrait
      change avec le niveau, reste net sur le PC ; libellés (« hiver (nu) ») utiles ?
- [ ] Magazine (après `palier3`) : portrait mûr à chaque offre.
- [ ] Portraits non-arbres : tournesol de face ; molène hampe jaune ; drosera (trop chargé ?) ; thym ;
      lavande ; myrtille baies bleues ; haricot/jasmin/lierre sans tuteur ; chanvre (toujours une perche) ;
      hampes de carotte, ail, bourse, épis de plantain, basilic, menthe trop hauts ?
- [ ] Portraits d'arbres : cerisier jeune en fleurs / mûr en cerises ; sapin conique ; bouleau blanc
      (marques invisibles à 240 px) ; figuier ; les 8 autres.
- [ ] Premier lancement de l'éditeur Windows : import des portraits et de `assets/chargement/` sans rien régler.

### 8. Interrupteur Maj+F11 (avant/après)
- [ ] Plantes : bascule immédiate pièces splat ↔ ancien dessin, à ×4 et ×32.
- [ ] Bois des arbres du jardin : ancien bois ↔ tube lissé.
- [ ] Lisière : kit généré ↔ kit splat **et** arbres reconstruits (bois de S2), à ×1, ×4 et ×16 (atlas haut).

### 9. Perf et mémoire (rapport C, F4, Z — sur le PC)
- [ ] Précuisson `full` ×32 (VM 926-934/1024 Mo, menthe et noyer en repli) : une plante PLATE visible ? Le
      budget de 1 Go tient-il en VRAM (HD 4600) ?
- [ ] Atlas de lisière ×32 = 100,8 Mo (un seul vit) : compté dans la ligne « lisière N Mo » du rapport.
- [ ] FPS par palier (F4) ×0,5 / ×4 / ×32 ; draw calls stables.
- [ ] Balayage Z : à-coups de zoom ×4↔×8↔×32 (1ʳᵉ arrivée vs retours).
- [ ] Rapport C : construction de la maille de lisière ×2/×4 (référence PC 30-37 ms avant S3).
- [ ] Journal : une recette `_hauts` manquante annonce désormais « forme ×4 agrandie » (plus « kit généré »).

## §REPRISE
**Séquence « style homogène » (S1 → S2 → S3) CLOSE côté code le 2026-11-26** (S3 ①→⑤, golden `bce813af…`
intact, build 0 avertissement). **Attend le F5 complet de Nico** : liste dans ce fichier, section « F5 EXHAUSTIF »
(9 sections). Ensuite : proof of concept ×64 (chanvre), puis familles (c)-(f) de `backlog_splatting.md`.
