# sprint_reliquats_plantes — état du sprint

**Conception FIGÉE le 2026-11-25** (`/conception`, Nico : « ok allons y ») →
`docs/rendu/splatting/conception_reliquats_plantes.md`. **S1 d'une séquence de 3 sprints**
pour un style homogène avant le F5 complet de Nico : S1 reliquats des plantes → S2 arbres
(rendu lissé, écorce cuite, brins de graminées, portraits d'arbres ; `/conception` à faire)
→ S3 lisière (b) + écran de chargement en mycélium (g) + liste F5 exhaustive.
**Prêt pour `/sprint-auto sprint_reliquats_plantes`.**
Golden : **`bce813af…` INTACT à tous les tronçons** (vue + outillage, `data/code/` jamais modifié).

## Carte des tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_memoire_x32.md` — budget de précuisson 1 Go, plafonds relevés, ×32 cuit | **fait 2026-11-25** `b5509b1d` |
| ② | `02_classes_taille.md` — 3 tailles par recette, correction du √2, recuisson | **fait 2026-11-25** `60d40f99` |
| ③ | `03_details_cuits.md` — inventaire + tous les détails en couches + sonde ×64 | **fait 2026-11-25** `c90e304c` |
| ④ | `04_recettes_neuves.md` — trèfle 3/4, thym, lavande, fétuque, anthères, cœur des fleurons | **fait 2026-11-25** `fca98c1a` |
| ⑤ | `05_portraits.md` — portraits ratés hors arbres + baies de la myrtille | **fait 2026-11-25** `1175e338` |
| ⑥ | `06_revue_paliers.md` — revue ×0,5→×32, finitions, section F5, clôture | **fait 2026-11-25** `03e792db` |

## Décisions (Nico, 2026-11-25)
- E1 Trois sprints en séquence, sans F5 entre eux.
- E2 (S3) Écran de chargement : philo #5 = pendant le jeu seulement ; le logo est un filament de mycélium qui s'arborise en splats et sert de barre de progression.
- E3/E4 (S2) Le bois est à reprendre, sans aucun joint visible, angles arrondis. RENDU SEUL : `sim/growth.py` n'est pas touché. Piste : tube lissé à travers les nœuds + bande d'écorce cuite par essence.
- E5 Précuisson maximale. E6 Budget mémoire de précuisson de 1 Go.
- E7 ×32 : relever les plafonds sous ce budget (pas de dessin de codes en direct).
- E8 3 classes de taille par recette + correction du √2.
- E9 Les brins et rubans des graminées passent en S2 (ruban lissé + texture cuite).
- E10 Tous les détails des feuilles présents quand on zoome, beaux à chaque palier.
- ×64 : sonde au ③ ; **proof of concept chanvre ×64 après S1-S3** (BACKLOG). Il faudra recuire par palier aussi le sol, la faune, le paillage, etc. (familles c-e).

## Fait vérifié
×32 (capture VM du 2026-11-25, n=1 par cas) : tomate en splats ; tournesol en dessin
direct, ni `[Splats]` ni `[Cuisson]` au journal (refus des plafonds de `PlantBaker`).
Détails : conception §4. Captures de la conception non versionnées (scratchpad).

## Règles du sprint
- Captures VM : `tools/capture_vm.sh` (lues au Read avant de conclure) ; charge (`uptime`) vérifiée avant toute mesure de temps.
- Poids `assets/splats/` mesuré à chaque tronçon ; alerte et arrêt au-delà de 200 Mo.
- Interdits : `test_epaisseur_500ans` ; DeepSeek dans les sous-agents ; `data/code/` ; `tools/splat/vendor/`.

## Compte rendu des tronçons
(rempli par chaque tronçon : fait, mesures, chemins des planches et captures)

### ① Mémoire et ×32 — fait 2026-11-25
- **Neuf `visuals/BudgetCuisson.cs`** : budget global `BudgetOctets` = 1 Go (E6, constante unique)
  sur pages d'atlas + planches de codes. Éviction des images de plantes à page DÉDIÉE (seules à
  rendre vraiment de la mémoire), par clé stricte = distance du centre de l'écran à l'emprise
  (+1e6 hors écran) : hors champ d'abord, puis la plus lointaine ; jamais plus proche que le
  demandeur (pas de ping-pong). Faisabilité vérifiée AVANT d'évincer. Repli = dessin direct,
  journalisé une fois (`[Cuisson] repli <espèce> : …`), retenté au balayage de 15 images.
- `PlantBaker` : `MaxSidePx` et `MaxAtlasPx` 2048/4096 → **16 384** (limite GPU) ; si les poses ne
  tiennent pas en largeur, on garde les premières (moins de poses, DrawImage retombe sur la plus
  couchée cuite). « Trop grande » (> 16 384) = repli journalisé, non retenté.
- `SplatPlanches` : date de dernier usage par planche ; au CHARGEMENT qui dépasse le budget, rend
  les plus anciennes (jamais celles des 2 dernières images), `Dispose` immédiat.
- Rapport C et F4 : ligne `[rendu …]` + `précuisson X/1024 Mo (pages, planches) · N en repli ·
  M évincées` ; même texte dans `[Cuisson] file vidée`.
- **Écart au kickoff (6)** : les planches ne sont PAS évincées pour faire place à une cuisson
  (prévu « planches puis plantes ») — mesuré budget abaissé à 80 Mo [n=2 runs] : la cuisson les
  rechargeait aussitôt → budget dépassé (95/80 Mo) + gel. Elles se régulent au chargement ; le
  budget reste dépassable de la taille des planches en usage.
- Mesures (VM llvmpipe, charge 3-6, n=1 run/cas) : **tournesol ×32** avant = feuilles vectorielles
  plates, aucune ligne `[Splats]` ; après = feuilles en splats, 1 page 33,6 Mo, précuisson 155 Mo
  (planches 121 dont `tete_soleil_x32` seule 95 Mo). **Pommier ×32** (`verger_floraison -c 60,60`)
  avant = rien cuit, fleurs vectorielles ; après = 3 arbres en splats, 97,6 Mo de pages, 127 Mo
  au total. ×16 : 40 Mo. Budget 80 Mo : 2 arbres en repli, stable, plus de dépassement.
- **À-coup** : la cuisson passe bien par `BakeQueue` (1 plante/image), mais le pinceau d'UNE plante
  est indivisible : tournesol ×32 1,5-2,4 s, pommier ×32 0,3-0,5 s [VM chargée, n=1-3], plus le
  1er chargement de planche ×32 (`tete_soleil_x32` 1,1-1,7 s). Une fois par plante et par palier.
- Taille des feuilles splat ×32 nettement plus petite que l'ancien vectoriel : attendu, c'est le ②
  (classes de taille). Tige du tournesol décalée de ~20 px écran entre avant/après [n=1] : à revoir
  au ⑥ si visible.
- Captures + journal : `mesures/01_tournesol_x32_{avant,apres}.png`,
  `mesures/01_pommier_x32_{avant,apres}.png`, `mesures/01_pommier_x16_apres.png`, `mesures/01_journal.txt`.
- Golden `bce813af…` INTACT ; build vert, 0 avertissement ; `assets/splats/` 26 Mo.

### ② Classes de taille — fait 2026-11-25
- **Neuf `tools/splat/lib/classes.js`** : par recette, `nominalCm` (dans la MESURE DE LA VUE : longueur
  `FeuillePosee.Long`, rayon du disque d'une tête/fruit, longueur d'un épi), `rond`, et 1-3 échelles k
  sur l'échelle ×√2. Une classe = la MÊME recette photographiée au zoom z·k (aucune resculpture) →
  la classe k = 1 garde ses planches **à l'octet** (vérifié : aucun PNG k = 1 modifié au `git status`) ;
  les autres vont dans `<recette>_x<z>_k<100k>.png`. Manifeste : `classes`, `taille_nominale_cm`, `rond`,
  et `echelle` + `taille_cm` par pièce. **√2 corrigé une fois, dans l'outil** : pour un organe `rond`,
  `taille_cm` = rayon sculpté × k × √2 (la taille du disque de l'ancien dessin qui a la même emprise).
- **Neuf `tools/splat/inventaire_tailles.js`** : relit les fiches (via `portraits/table_cs.js`) avec les
  formules recopiées des ports et propose les k ; sortie : `mesures/02_inventaire_tailles.txt`.
- `cuire.js` (axe des classes), `lib/planche.js` (champs, `.png.import` « keep » écrit pour toute planche
  neuve, planches d'une classe retirée effacées — motif strict), `lib/controle.js` (clé de fusion des
  couches + classe ; 1ʳᵉ ligne de la planche de contrôle = les classes à ×8).
- **Vue** : `SplatPlanches.Classe(recette, tailleCm)` (plus proche EN RAPPORT ; 0 = nominale) ; clé de pièce
  + échelle ; pièce VIDE (organe sous le pixel) → la classe au-dessus (comme le plancher d'un pixel de
  l'ancien dessin). Crochets : feuilles `fe.Long` ; limbe générique `2·rx/(PxPerCmX·√2)` ; têtes `r/pxx`
  (aigrette ×1,3) ; fruits `r/PxPerCmX` (ports, lianes, arbres) ; boule `r` ; corolle `FleurRayonCm` ;
  épi/panicule `len` ; épi du plantain 1,2 cm. Attaches qui dépendaient de la taille (boule 1,8 cm,
  ombelle 2,75 cm) × k. Fruits génériques (PaliersHauts), gousse, chaton, bouton : classe nominale.
- **Table recette → k (taille vue en cm)** : ovale 0,35/1/2 (3,2/9/18) · scie 0,71/1/1,41 · scie_gaufrée
  0,25/0,5/1 (2,3/4,5/9) · lancéolée 0,5/0,71/1 · lancéolée_gaufrée 0,5/1/2 · dentée 0,5/0,71/1 · spatule
  0,5/0,71/1 · lobée 0,35/0,71/1,41 (4,2/8,5/17) · cœur 0,35/1/2 · lierre 0,71/1 · palmée 0,5/1/1,41 · triade
  0,35/0,5/0,71 (4,9/7/9,9) · plume 0,18/0,35/0,71 (3,2/6,3/12,8) · ruban 0,125/0,25/0,35 (3,8/7,5/10,5) ·
  cuillère 0,71/1/1,41 · composée 0,35/1/1,41 (6,3/18/25) · paume, aiguille 1 ; têtes (rayon vu) :
  capitule, chapelet, ombelle, papillon, soleil, trompette 0,71 seule (√2 seul, une espèce) · bouquet
  0,71/1,41 · épi 0,5/0,71/1,41 · boule 0,35/0,71/1,41 · grappe 0,35/1,41 (2 espèces) · étoile 0,25/0,5/1 ·
  pendante 0,5/0,71/1 · corolle 0,5/0,71 ; fruit_globe 0,25/0,5/1 (0,7/1,4/2,8) · fruit_long 0,35/0,5/0,71 ;
  épis, panicule 0,71/1 ; gousse, chaton, bouton 1. Moins de 3 classes = plage étroite (≤ 2 espèces ou
  rapport < 1,6), justifié dans l'inventaire.
- **Écarts au kickoff (6)** : (a) **paume gardée à 1 classe** (courgette 21,6-30 cm contre 20) : sa planche
  ×32 est déjà à 2042×17 394 px, ×1,41 la doublerait (≈ 140 Mo RGBA en jeu) pour −33 % d'écart → F5 ;
  (b) les classes k = 0,5 / 0,25 / 2 donnent les MÊMES octets que la classe 1 d'un autre palier
  (ex. `x16_k50` = `x8`) : doublons acceptés (poids faible), dédoublonnage possible plus tard ;
  (c) 16 recettes n'ont plus de k = 1 (toutes les têtes rondes à une espèce, lobée, triade, plume, ruban,
  fruit_long, corolle) : leurs planches d'avant sont effacées (112 PNG + `.import`).
- **Mesures** (VM, charge 6-20 pendant la cuisson, n=1) : 34 recettes recuites, `xargs -P 10`, **3 h 02 de mur**,
  1 352 min CPU, 53 430 pièces ; plus long : `tete_soleil` 35 min, palmée et lancéolée gaufrée (k=2/1,41)
  les dernières. Déterminisme : 2 cuissons `tete_etoile` et `fruit_globe` identiques à l'octet, k = 1 =
  planches d'avant. **Poids `assets/splats/` 26 → 50 Mo** (47,5 Mo ; seuil 200). Journal :
  `mesures/02_journal_cuisson.txt`.
- Captures avant (`SYMBIOSE_SPLATS=0`) / après, `mesures/02_<espèce>_x<z>_{avant,apres}.png` (fraisier ×8,
  courgette ×16, myrtille et haricot ×1/×2, molène ×2) : courgettes à la taille du dessin (avant ~×2),
  fraises et fleurs du fraisier ramenées à celle du dessin (fleurs un peu plus petites), rosette de la
  molène à la taille du dessin (avant ~½), triades du haricot en k 0,35-0,71. **Restent** : l'épi de
  la molène, que l'ancien dessin étire le long de la hampe, est bien plus court en pièce (même cause
  qu'au ③ du sprint (a), la taille ne règle pas la FORME) ; paume de courgette pâle et plate (③ ancien).
  Planches de contrôle : `mesures/02_controle_{fruit_globe,feuille_ovale}.png` (1ʳᵉ ligne = classes).
- Golden `bce813af…` INTACT ; build vert, 0 avertissement. LDC : SplatPlanches 229 · Splats 163 ·
  SplatsOrganes 68 · cuire.js 170 · planche.js 69 · classes.js 50 · inventaire 60 (tous 🟢).

### ③ Détails cuits — fait 2026-11-25
- **Mécanisme = SUR-COUCHES** (écart au kickoff, (6)) : pas de couche ajoutée DANS la recette (une couche
  « vole » ses pixels au limbe → trous chez les espèces sans le détail, et recuisson de la base). Neuf
  `tools/splat/lib/details.js` : table recette → détails + paliers, un sculpteur par détail posé sur les
  SITES des limbes (ceux des trous D5 ; `limbe.js` rend aussi `pli`, `epais` ; `fruit_globe`, `tete_corolle`,
  `feuille_composee` rendent leurs sites). `cuire.js <recette> --details` sculpte la recette + ses détails
  (flux de hash 2000+variante, la feuille n'en dépend pas), photographie aux MÊMES vues/classes et n'extrait
  que les couches de détail (`codes.piece(…, part = 1/3)` : un poil fin n'est jamais majoritaire) →
  `<recette>_details.json` + planches. **Aucune planche de base recuite** (git : 0 fichier de base modifié ;
  non-régression `tete_corolle` recuit hors dépôt = octets identiques avec COUCHES 3 → 8).
- **Vue** : neuf `visuals/PlantRenderer.SplatsDetails.cs` (93 LDC) — table unique `SeuilsDetails`, qui porte
  quoi (marque de fiche + surface d'espèce), couleur par détail ; `SplatPlanches.Trouver(…, out classe,
  exacte)` (la sur-couche tombe sur la classe RÉELLEMENT posée, sans remonter). Crochets : `PoserPieceFeuille`
  (feuilles saines seulement ; revers : 1 feuille sur 3 posée en ton clair dès ×4, comme l'ancien `Ton(col,4)`)
  et `PoserCouches` (étamines, pruine du fruit). `DrawSurfaceFeuille` (poils/pruine/glandes vectoriels en
  anneau) n'est plus tracé sur une feuille-pièce (il l'était encore : visible sur `03_bourrache_x32_avant`).
- **Inventaire (grep)** — détail → espèces → palier ancien → fichier:ligne (HEAD) :
  | Détail | Espèces | Ancien | Source | Recettes cuites | Seuil retenu |
  |---|---|---|---|---|---|
  | nervures médiane + secondaires | toutes les feuilles à contour | ×8 médiane, ×16 sec., ×32 5 paires | PortTigeFormes:46-47, PortRosette:138-139, PortVolubile:175-176, PortTapis:93, PortRampante:66, FleurSnes:84 (`DetaillerLimbe`), Leaf:188/222, LeafOutline:180 | ovale, scie(+gaufrée), lancéolée(+gaufrée), dentée, spatule, lobée, cœur, lierre, paume, composée, triade | ×16 |
  | Nervures pâles (marque) | lierre | ×8 | PortTigeFormes:48 / Lianes:181 | lierre (palmées) | ×8 |
  | Duvet (marque) | molène, bourrache | ×8 | PortRosette:140, PortTigeFormes:49 | ovale | ×8 |
  | Éclat (marque) | basilic, poivron | ×4 | PortTigeFormes:43 | ovale | ×4 |
  | Revers (marque) | armoise, framboisier | ×4 | PortTigeFormes:41 | lobée, scie | ×4 (+ 1/3 retournées) |
  | Gouttes (marque) | drosera | ×8 | PortRosette:187 | cuillère | ×8 |
  | Poils (surface) | consoude, bourrache, tournesol, tomate, courgette, armoise, fraisier (+ phacélie, lavande, thym : non cuits) | ×32 | PaliersHauts:170/244 | ovale, lancéolée gaufrée, cœur, composée, paume, lobée, scie gaufrée | ×32 |
  | Pruine feuille (surface) | ail | ×32 | PaliersHauts:247 | ruban | ×32 |
  | Glandes (surface) | drosera | ×32 | PaliersHauts:249 | cuillère | ×16 |
  | Pruine fruit | myrtille | ×32 | PaliersHauts:148 | fruit_globe | ×32 |
  | Étamines | (`DrawEtamines`, Flower:122 : **code mort**, `DrawFlowerShape` n'est plus appelé) | ×32 | PaliersHauts:303 | tete_corolle | ×32 |
  Non cuits : poils de la phacélie (plume : lanières de 1-2 mm, aucun site de limbe), lavande et thym (masses
  dessinées, ④). Couleurs de santé (nécrose, taches, givre, criblage hors pièce) : peintes (D5).
- **Seuils** : lus sur `mesures/controle_<recette>_details.png` (base verte + détails en couleurs) — nervures
  secondaires sous le pixel à ×8, nettes dès ×16 ; poils lisibles à ×32 seulement (×16 : grésillent) ;
  étamines = une tache à ×8-×16 qui couvre le cœur, rayonnantes à ×32 ; glandes et perles lisibles dès ×16,
  perles seules dès ×8. Paliers cuits = un cran sous le seuil (choix possible au ⑥ sans recuire).
- **Mesures** (VM, charge 4-43 pendant la cuisson : machine partagée + captures) : 17 recettes, `xargs -P 12` +
  `-P 5`, **2 h 14 de mur** (16:42 → 18:56), **1 094 min CPU**, 19 602 pièces (990 vides). **Poids
  `assets/splats/` 50 → 63 Mo** (sur-couches 14 Mo, 146 planches) ; seuil 200 non atteint.
- **Captures** ×8/×16/×32 avant/après (`-l 2`, `planche_especes`) : `mesures/03_<espèce>_x<z>_{avant,apres}.png`
  pour bourrache, lierre, drosera, armoise, ail, fraisier (fleur), tomate. Lues : bourrache ×32 nervures +
  duvet + poils (avant : anneau de soies vectorielles autour de chaque pièce), lierre ×16 nervures pâles,
  drosera ×16 couronne de perles. Journal : `mesures/03_journal_cuisson.txt`.
- **Sonde ×64** (`feuille_composee` + poils, hors dépôt, 2 lacets × 3 variantes × 3 classes, VM chargée ~25) :
  base 94 s/pièce (k 1), 180 s (k 1,41 = ×90), 15 s (k 0,35) ; avec détails 144 / 297 / 19 s. Pièce k 1 =
  520×358 px, k 1,41 = 732×504. Planches pour 6 vues : base 87 Ko (k 1) / 132 Ko (k 1,41), détails 50 / 83 Ko
  → une recette complète (72 vues) ≈ 1-1,6 Mo par classe et par couche [extrapolé, n=6]. **Les splats se
  voient un par un** : bords en perles, rachis en anneaux, poils en points (`mesures/sonde_x64.png`, txt
  à côté). Rien dans la vue. Pour le chanvre ×64 : prévoir le coût d'une ×32 × ~4.
- Golden `bce813af…` INTACT ; build vert, 0 avertissement. LDC : details.js 139 · cuire.js 185 · codes.js 86 ·
  controle.js 81 · SplatsDetails 93 · Splats 167 · SplatPlanches 234 · PaliersHauts 221 (tous 🟢).

### ④ Recettes neuves — fait 2026-11-25
- **Recettes neuves** (`tools/splat/recettes/`) : `feuille_trefle` (3 folioles, ProfilFoliole de la vue, à plat,
  inclinaison 0 seule) + `feuille_trefle4` (4 folioles, même fabrique) ; `feuille_thym` (rameau ligneux 3,6 cm,
  6 nœuds de feuilles opposées 6-7 mm + bouquet terminal) ; `feuille_lavande` (touffe de 3 lames linéaires ~8 cm,
  bords enroulés) ; `panicule_fetuque` (panicule lâche, 4 rameaux retombants, épillets 0,5 cm). Noms préfixés
  `feuille_`/`panicule` → repris tels quels par `controle_feuilles.js` / `controle_organes.js`.
- **Classes** (`lib/classes.js`) : trèfle k 0,5/0,71/1 (foliole 1,5/2,1/3 cm ; la vue va de 1,8 à 3) ; thym,
  lavande, panicule de fétuque **1 classe** (taille FIXE dans la vue : `GrainCm`, aucune croissance).
- **Détails** (`lib/details.js`) : trèfle nervures + `chevron` (marque claire en V, ×16) ; thym/lavande `poils`
  à soies réduites (`poilsCm` 0,1 / 0,12 ; facteur exact 1 pour les recettes du ③, octets inchangés) ; `epi_ble`
  sur-couche `antheres` (×8, anthèse seulement) — `epi_ble.js` rend désormais les sites (1 épillet sur 3),
  sculpture de base inchangée, base NON recuite.
- **Fleuron** : cœur 0,28 → 0,4 × r (`corolle(…, coeur)`, défaut inchangé pour les autres têtes) → la couche cœur
  possède le pixel central à 3 px (avant : vide aux 3 tailles). À 2 px il reste sous le pixel : `FondreCouches`
  (KitSplats.cs) force le pixel de l'attache en `KitCoeur`. À 1 px, teinte des pétales (= ancien Fleuron.Point).
- **Vue** : neuf `visuals/PlantRenderer.SplatsHerbes.cs` (21 LDC) — crochets d'une ligne dans `DessinerTrefle`
  (Prairie.cs, toutes paliers, pétiole tracé dès ×8), `PoserMasse` (PortBuisson.cs, chaque grain → rameau/touffe,
  tous paliers, sur le dôme sombre), `DessinerFetuque` (Graminees.cs, organe dès ×2). `SplatsDetails.cs` : seuils
  `chevron` 16 / `antheres` 8, anthères gatées par `Floraison ≥ FloraisonSeuil`, couleurs (clair du limbe ; clair
  de la fleur). Ancien dessin intact derrière chaque crochet.
- **Écarts au kickoff (6)** : (a) **4 folioles NON tirées au hash dans la vue** : la rareté existe déjà côté MOTEUR
  (`sim/quatre_feuilles.py`, ~1 pied sur 200, cueillable par `recolter`, snapshot `quatre_feuilles`) ; un tirage
  vue créerait des trèfles à 4 feuilles non cueillables (faux indice, philo #5). La pièce 4 folioles est posée là où
  l'ancien dessin posait 4 folioles. (b) thym/lavande/fétuque à 1 classe (taille fixe). (c) anthères = sur-couche
  de `epi_ble` (pas une pièce). (d) 1ʳᵉ version du thym à 1,9 cm trop petite (`GrainCm` est le RAYON du disque
  dessiné) → recuite à 3,6 cm après capture.
- **Mesures** (VM, charge 4-13, n=1) : 11 cuissons `xargs -P 11`, **11 min 43 s de mur** (20:05:34 → 20:17:17 ;
  plus long `epi_ble --details` 702 s CPU), + recuisson thym 2 min. Pièces : trèfle 696 + 432 détails (×2 recettes),
  thym 232 + 48, lavande 232 + 48, panicule 168, `epi_ble` détails 576, fleuron 18. Journal `mesures/04_journal_cuisson.txt`.
  **Poids `assets/splats/` 63 → 65 Mo** (nouveaux fichiers 2,1 Mo ; seul existant modifié : `fleuron.json` + `fleuron_kit.png`).
- **Captures** (`planche_especes -l 2`, avant = `SYMBIOSE_SPLATS=0`) : `mesures/04_<trefle|thym|lavande|fetuque|ble>_x<1|8|16>_{avant,apres}.png`
  + `04_kit_{avant,apres}.png`. Lues : trèfle ×8 feuilles à 3 folioles en volume (même densité) ; thym ×8 rameaux
  hérissés sur le coussin (moins couvrant que les anciens disques : le dôme sombre se voit davantage) ; lavande ×8
  touffes de lames en volume (plus sombre que les traits clairs d'avant) ; fétuque ×16 panicules rousses en étoile ;
  kit : fleurons 2 et 3 px avec pixel jaune. Blé : banc à épis MÛRS (dorés), anthères chargées au journal
  (`epi_ble_details_x8/16/32`) mais à peine visibles ; non vérifiées en anthèse verte. Contrôles :
  `mesures/controle_{feuille_trefle,feuille_trefle4,feuille_thym,feuille_lavande,panicule_fetuque,fleuron}[_details].png`,
  `controle_epi_ble_details.png`. Aucune ligne `repli` au journal.
- **Reste dessiné sur les herbacées** : brins et rubans des graminées (S2) ; organes sous ×2 (seuil ⑤bis) ; folioles du
  volubile en losange (repli seul) ; trèfle de loin : plus rien (la tache hexagonale ne sert qu'en repli).
- Golden `bce813af…` INTACT ; build vert, 0 avertissement. LDC : SplatsHerbes 21 · Prairie 304 (🟡 préexistant, 303
  avant) · Graminees 208 · PortBuisson 149 · SplatsDetails 98 · KitSplats 179 · details.js 151 (tous 🟢 sauf Prairie).

### ⑤ Portraits — fait 2026-11-25
- **Outil seul** (`tools/splat/portraits/`, `cuire_portraits.js`) + 1 ligne de vue (fiche myrtille). Refaits :
  - **Tournesol** : la tête regarde la caméra (`teteFace`, azimut `FACE` tiré du lacet) — elle était de profil,
    pas trop petite (12,5 cm vrais sur 250 cm, s = 1 : le bornage n'y était pour rien).
  - **Échelle des têtes** = rayon nominal de `lib/classes.js` (rayon des FLEURS) au lieu de `rayonCm / 1,75`,
    qui pour une recette allongée englobe sa longueur (épi 5,1 au lieu de 1,4 ; grappe, chapelet, papillon,
    pendante) → ces têtes étaient toutes rabattues au plancher 0,5.
  - **Épi long** (`epiLong`) : `tete_epi` empilée sur le segment que la vue étire (tiers haut de la hampe,
    bout `EpiCm` de la tige, haut des cannes de lavande). **Molène** : hampe à la hauteur MOTEUR de ses
    `StadesHampe` (160 cm, comme `_hauteurLisseeCm` de la vue) + épi jaune. S'applique aussi aux rosettes
    à hampe (carotte 60, ail 50, bourse 40, mâche 18) et aux épis de basilic, menthe, armoise, plantain.
  - **Drosera** : limbe tiré vers le rouge (`MelangeFruit` 0,8, comme la vue) + sur-couches ③ `glandes` et
    `gouttes` sculptées sur les sites du limbe (`Portrait.poser(…, dmats)`) ; sol minimal 3 → 1,5 cm (jeune).
  - **Thym, lavande** : la masse = pièces ④ (`feuille_thym` / `feuille_lavande`, choix « Ruban → lames » de
    la vue) autour d'un cœur sombre en retrait (`creux`) ; fleurs du thym posées sur le coussin.
  - **Bois des buissons** à la couleur `Bois` de la fiche (lavande gris-vert, myrtille verte) au lieu du brun
    commun. **Tuteurs** (haricot, lianes) amincis et gris pâle. **Hiver nu** : tige aoûtée (jasmin).
  - **Chanvre** : feuilles palmées relevées vers la caméra (m ≥ 0,6) + épi empilé.
- **Myrtille — prémisse du kickoff fausse** : le moteur ne la noue PAS (`fruitier` absent de `Vaccinium`,
  `sim/engine/decompo.py:331` : non fruitière → `feconder` seul, aucun `Fruit` au snapshot). Ajouter `Fruit` à la
  fiche (`PortsFiches.cs`, `Fruit: new(0.45f)`) est **inerte en jeu** (la vue ne pose que les fruits du moteur ;
  sans ligne, `FruitParDefaut` 1,5 cm aurait servi) — ligne gardée pour le portrait et pour le jour où le moteur la
  rendra fruitière. Pas de capture en jeu avant/après (rien ne change). **Candidat dette** : myrtille non
  fruitière au moteur (docstring « baies comestibles », gène `appetence_fruit`) → baies jamais en jeu.
- **Candidat dette framboisier** : `Raspberry` persistant au moteur → portrait d'hiver feuillé ; le framboisier
  réel est caduc. Moteur non touché.
- **Encore faibles** : **chanvre** (300 cm dans 240 px : feuille de 20 cm = 14 px, doigts < 2 px — illisible tant
  que le portrait est cadré sur la plante entière) ; **thym** (le cœur ink est rendu en grands aplats lisses, les
  rameaux restent petits : coussin lisible mais pas fin) ; **plantain** (épi = tiers de la hampe comme la vue, plus
  long que le vrai) ; haricot (fleurs-papillons peu visibles). Arbres : S2.
- **Recuisson complète** 156/156, `xargs -P 10`, **21 min 07 s** de mur (20:57:00 → 21:18:07, charge 3-14) ;
  plus longs Fig mûre 873 s, Thyme mûre ~300-390 s [n=2]. Tous les PNG changent (palette élargie de 4 couleurs →
  quantification). **Déterminisme** : 15/15 portraits identiques à l'octet entre 2 cuissons (molène, drosera,
  chanvre, haricot, lavande). `portraits.json` régénéré : identique. Godot `--import` refait (156 `.import`
  inchangés) ; 340 `.import` parasites dans `docs/`/`sprints/` supprimés.
- **Mesures** : planches `mesures/controle_portraits_{1..6}.png` (relues espèce par espèce), journal
  `mesures/05_journal_portraits.txt`, encyclopédie `mesures/05_encyclo_{molene,drosera,thym}.png` (`-Z encyclo:… -P`).
  Poids : `assets/splats/` **65 Mo** (inchangé), `assets/portraits/` 2,1 Mo.
- Golden `bce813af…` INTACT ; build vert, 0 avertissement. LDC : ports_bas 145 · ports_hauts 118 · cuire_portraits
  137 · organes 91 · etats 56 · arbres 81 · PortsFiches 169 (tous 🟢).

### ⑥ Revue des paliers — fait 2026-11-25
- **Revue** : 16 espèces × 7 paliers × avant (`SYMBIOSE_SPLATS=0`) / après, `planche_especes -l 2 -n 170`
  (tomate, tournesol, fraisier, courgette, carotte, trèfle, plantain, blé, thym, lavande, lierre, haricot,
  drosera, bourrache, myrtille, molène) + monde `full`. 3 files Xvfb en parallèle, ~2 min par capture
  (VM, charge 4-12). Planches lues en montages (×0,5-×4 / ×8-×32, avant en haut) — hors dépôt :
  `/tmp/claude-1000/-home-nico-Nextcloud-projects-symbiose/6235938d-c586-4e51-a29a-fb714fef2dba/scratchpad/mont/`.
  **Aucun retour au dessin direct** sur la planche (0 repli sur 16 runs) ; pas de pièce vide vue.
- **3 finitions** (vue seule, `visuals/`) :
  1. **Tête du tournesol de face** (`PlantRenderer.Splats.cs`, `PoserTeteSplat`) : le lacet tiré au hasard la
     montrait de PROFIL (anneau pâle, cœur gris-brun) de ×2 à ×32, alors que l'ancien `PoserSoleil` et le
     portrait (⑤) la montrent de face. Lacet = direction caméra. `mesures/06_tournesol_tete_{avant,apres}.png`
     (×4 et ×2 : dessin | splat).
  2. **Poils et pruine de feuille fondus sur le limbe** (`PlantRenderer.SplatsDetails.cs`, `CouleurDetail`) :
     posés en blanc OPAQUE, les poils ×32 (tomate, fraisier, bourrache, tournesol…) lisaient comme l'**oïdium**
     (signe « blanc farineux » du moteur, philo #5). Couleur = limbe → blanc à l'alpha de l'ancien voile (0,55 ;
     pruine 0,5). Pruine du FRUIT inchangée. `mesures/06_tomate_poils_x32_avant_apres.png`.
  3. **Épi long empilé** (`PlantRenderer.Splats.cs`, `PoserEpiEmpile`) : une seule pièce `tete_epi` (8 cm × classe)
     laissait l'épi de la molène 3-4 fois trop court (constat ②) ; on empile les pièces sur le tiers haut de la
     hampe (pas 0,8 longueur, affinées vers la pointe, ≤ 24), comme `epiLong` du portrait (⑤). Épis courts
     (basilic, menthe, lavande) : 1 pièce, inchangés. `mesures/06_molene_epi_x8_dessin_avant_apres.png`
     (dessin | 1 pièce | empilé).
- **Mémoire de précuisson** (dernière ligne `[Cuisson] file vidée` de chaque palier, VM llvmpipe, n=1 run/cas) :
  planche, une espèce visée : ×4 ≤ 85 Mo · ×8 57-161 · ×16 55-416 · ×32 103-689 Mo (max tournesol ×32 689,
  bourrache ×32 671), **0 repli, 0 éviction**. Monde `full` : ×8 265 · ×16 693 · ×32 **927/1024 Mo, 2 replis
  + 2 évincées** (menthe, noyer hors champ). Planche molène après l'empilement : ×32 934 Mo, 4 replis (bambous,
  dactyle hors champ). Le budget ① fait son travail à ×32 ; il est presque plein.
- **ms par image** (médiane `[perf]` du palier, VM llvmpipe, charge 4-12 [n=1 run/cas] — non transposable au PC) :
  planche 370-630 ms (×8-×32), `full` 449-763 ms ; avant/après `full` du même ordre (×32 637 contre 670).
- **Vus, non corrigés** (pas de recette neuve au ⑥) → section F5 et S2/S3 : feuille du **plantain** trop large
  (pièce `feuille_lanceolee` générique, nervures pennées ; le plantain a des feuilles étroites à nervures
  parallèles — recette dédiée à prévoir) ; **thym** ×16-×32 : le dôme sombre plat domine, rameaux clairsemés ;
  **courgette** paume pâle et plate, 2 feuilles vues par la tranche à ×8 ; **bourrache** ×8-×32 feuilles
  bicolores (pli très contrasté) ; fraises **brunes** et ombelle de **carotte orange** (avant ET après : moteur ou
  fiche, pas le ⑥) ; tige du tournesol ×32 : **pas de décalage visible** sur cette planche (constat ① non
  reproduit) ; **drosera** : `-c` au pied vise le plantain voisin (2 essais) — revue faite au ③.
- **Dette** : myrtille non fruitière ajoutée à **D134** (déjà « myrtille et lierre fruitiers ») — pas de dette
  neuve (règle du tri). **Framboisier persistant au moteur** (caduc en vrai, portrait d'hiver feuillé) : candidat
  NON ouvert (règle « pas de nouvelle dette sans en fermer une ») → à l'orchestrateur.
- Golden `bce813af…` INTACT ; build vert, 0 avertissement. LDC : Splats 184 · SplatsDetails 98 (🟢).
  `assets/splats/` **65 Mo** (inchangé, rien recuit).

## F5 consolidé (S1, à jouer au F5 complet APRÈS S3 — base de la liste exhaustive de S3)
Mode d'emploi : banc `planche_especes` (40 adultes, fleurs et fruits posés), touche **L** = planche des
paliers ×0,5→×32 sur la plante visée ; **Maj+F11** compare à l'ancien dessin ; **C** (rapport) / **F4** donnent
`précuisson X/1024 Mo`. Monde `full` pour l'ensemble. Cocher espèce par espèce.

**Général (tous paliers)**
- [ ] Aucune bascule laide d'un palier au suivant (taille, détail qui apparaît/disparaît d'un coup).
- [ ] Sauts de classe de taille (feuille qui grandit : ×1,4 à ×2,8 d'un coup) : visibles ? gênants ?
- [ ] ×32 : tout est en volume (aucune plante en dessin plat) ; à-coup au 1ᵉʳ passage à ×32 (VM : 1-2 s par
      grande plante, une fois) acceptable sur le PC ?
- [ ] Mémoire (C) sur la HD 4600 : `full` ×32 ≈ 930/1024 Mo sur la VM, quelques plantes hors champ en repli —
      voit-on une plante PLATE à l'écran ? Le budget de 1 Go tient-il en VRAM ?
- [ ] Monde `full` ×1 : ensemble homogène, aucune plante qui « détonne ».

**Par espèce** (palier où regarder → ce qu'on vérifie)
- [ ] **Tomate** ×8-×32 : folioles en volume ; ×32 poils fins vert pâle (PAS de points blancs façon oïdium).
- [ ] **Tournesol** ×2-×32 : tête **de face**, cœur brun foncé, taille de l'ancien disque ; ×16-×32 nervures +
      poils ; tige ×32 non décalée des feuilles (constat ① non reproduit au ⑥).
- [ ] **Fraisier** ×8 : taille des feuilles et des fleurs ; ×32 poils discrets ; fraises : **brunes** sur la
      planche avant comme après — teinte de maturité voulue ?
- [ ] **Courgette** ×16 : paume (1 classe, jusqu'à −33 %) assez grande ? pâle et plate ? feuilles vues par la
      tranche ; fleur-trompette ×32.
- [ ] **Carotte** ×2-×16 : rosette plume, ombelle en pièce ; ombelle **orange** (avant comme après) : voulu ?
- [ ] **Trèfle** tous paliers : tapis de 3 folioles même densité ; V clair ×16 ; un pied `quatre_feuilles` en X.
- [ ] **Plantain** ×4-×32 : feuilles **trop larges et pennées** (pièce lancéolée générique) — recette dédiée ?
      épi plus long que le vrai.
- [ ] **Blé** ×8-×32 en fleur (vert) : anthères pâles ; brins et rubans encore dessinés (S2).
- [ ] **Fétuque** ×2-×16 : panicules rousses lisibles.
- [ ] **Thym** ×8-×32 : coussin de rameaux, ou **dôme sombre plat** trop visible entre eux ?
- [ ] **Lavande** ×8-×32 : touffes de lames trop sombres face au gris-vert d'avant ? épis.
- [ ] **Lierre** ×8 nervures pâles ; baies.
- [ ] **Haricot** ×1-×32 : triades, gousses, fleurs-papillons.
- [ ] **Drosera** ×8 perles, ×16 tentacules : trop chargé ? (revue faite au ③ ; le banc vise mal son pied).
- [ ] **Bourrache** ×8 duvet, ×32 nervures + duvet + poils : trop chargé ? feuilles **bicolores** (pli) trop
      contrastées ?
- [ ] **Molène** ×2-×16 : épi jaune **sur tout le tiers haut** de la hampe (empilé au ⑥) ; rosette à la taille
      du dessin ; duvet ×8.
- [ ] **Armoise / framboisier** ×4 : revers (1 feuille sur 3 claire). **Basilic / poivron** ×4 : éclat.
      **Ail** ×32 pruine. **Consoude** ×32 poils.
- [ ] **Myrtille** : baies JAMAIS en jeu (moteur, D134) — seulement au portrait.
- [ ] Fleurons des plantes sans fiche ×1-×2 : cœur jaune.

**Encyclopédie → Plantes (portraits, ⑤)**
- [ ] Tournesol de face ; molène grande hampe jaune ; drosera rouge (trop chargé ?) ; thym (cœur trop lisse ?) ;
      lavande ; myrtille baies bleues ; haricot/jasmin/lierre (tuteur effacé) ; chanvre (toujours une perche) ;
      hampes de carotte, ail, bourse et épis de plantain, basilic, menthe : trop hauts/longs ?

**Restes connus, hors S1** : bois, brins et rubans des graminées, portraits d'arbres (S2) ; lisière, écran de
chargement (S3) ; recette dédiée plantain (à placer) ; framboisier caduc au moteur (candidat dette).

## §REPRISE
**SPRINT S1 CLOS côté code le 2026-11-25** (①→⑥, golden `bce813af…` intact, refactor : rien à scinder, journal 201).
Prochaine étape : `/conception` de **S2 (arbres : bois lissé sans joint, écorce cuite, brins de graminées,
portraits d'arbres)**. F5 complet après S3, avec la section « F5 consolidé » ci-dessus.
Repères ⑥ : tête du tournesol de face et épi empilé (`PoserTeteSplat` / `PoserEpiEmpile`,
`visuals/PlantRenderer.Splats.cs`) ; couleur des poils/pruine (`CouleurDetail`, `PlantRenderer.SplatsDetails.cs`).

(ancienne reprise, toujours valable pour les outils)
Lire `CLAUDE.md`, ce fichier, la conception, puis le kickoff du premier tronçon « à faire »
(①②③④⑤ faits : prochain = ⑥ `06_revue_paliers.md`). Budget de précuisson : `visuals/BudgetCuisson.cs`.
Classes de taille : `tools/splat/lib/classes.js` (+ `inventaire_tailles.js`) ; toute recette neuve ou
recuite (③④) passe par elle — y ajouter son entrée (sinon k = 1 seule). Une recuisson complète coûte
~3 h de mur [VM, n=1] : ne recuire que les recettes touchées.
Détails (③) : toute recette neuve ou recuite qui porte un détail (④ : trèfle, thym, lavande…) ajoute
son entrée à `DETAILS` (`tools/splat/lib/details.js`) et recuit ses sur-couches (`cuire.js <r> --details`) ;
seuils et « qui porte quoi » dans `visuals/PlantRenderer.SplatsDetails.cs`. Une recette dont la base est
recuite DOIT recuire ses détails (même sculpture, sinon décalage).
Recettes neuves du ④ : `feuille_trefle(4)`, `feuille_thym`, `feuille_lavande`, `panicule_fetuque` (crochets :
`visuals/PlantRenderer.SplatsHerbes.cs`). Les portraits du ⑤ les utilisent (thym, lavande ; trèfle et fétuque via leurs fiches).
Portraits (⑤) : recuisson complète ~21 min [VM, n=1] ; après toute recuisson, `godot --headless --import` puis
supprimer les `.import` parasites de `docs/` et `sprints/`.
Outils hérités du sprint (a) : `SplatPlanches.Trouver` / `LireImage`, `PoserPieceSplat`,
`PoserPieceFeuille`, `PoserOrganeSplat`, `PoserFoliolesSplat`, `TouffeGerbe`,
`tools/splat/cuire.js`, `cuire_portraits.js`.
