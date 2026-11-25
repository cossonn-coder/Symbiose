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
| ① | `01_memoire_x32.md` — budget de précuisson 1 Go, plafonds relevés, ×32 cuit | **fait 2026-11-25** (non commité) |
| ② | `02_classes_taille.md` — 3 tailles par recette, correction du √2, recuisson | **fait 2026-11-25** (non commité) |
| ③ | `03_details_cuits.md` — inventaire + tous les détails en couches + sonde ×64 | à faire |
| ④ | `04_recettes_neuves.md` — trèfle 3/4, thym, lavande, fétuque, anthères, cœur des fleurons | à faire |
| ⑤ | `05_portraits.md` — portraits ratés hors arbres + baies de la myrtille | à faire |
| ⑥ | `06_revue_paliers.md` — revue ×0,5→×32, finitions, section F5, clôture | à faire |

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

## F5 (à remplir par les tronçons, consolidé au ⑥)
- ① À ×32 sur un tournesol et un pommier : les feuilles et les fleurs sont en volume (splats).
  L'à-coup au premier passage à ×32 (gel d'environ 1-2 s par grande plante sur la VM) est-il
  gênant sur le PC ? Touche C : lire `précuisson X/1024 Mo` sur la HD 4600.
- ② Maj+F11 pour comparer : fraisier ×8, courgette ×16, myrtille et haricot ×1/×2, molène ×2, une
  carotte, un pommier fruité. Les pièces ont-elles la taille de l'ancien dessin ? Les sauts de classe
  (une feuille qui grandit passe d'une classe à l'autre, ×1,4 à ×2,8 d'un coup) se voient-ils ?
  Feuilles de courgette (une seule classe, jusqu'à −33 %) : assez grandes ? Épi de la molène trop court.

## §REPRISE
Lire `CLAUDE.md`, ce fichier, la conception, puis le kickoff du premier tronçon « à faire »
(①② faits : prochain = ③ `03_details_cuits.md`). Budget de précuisson : `visuals/BudgetCuisson.cs`.
Classes de taille : `tools/splat/lib/classes.js` (+ `inventaire_tailles.js`) ; toute recette neuve ou
recuite (③④) passe par elle — y ajouter son entrée (sinon k = 1 seule). Une recuisson complète coûte
~3 h de mur [VM, n=1] : ne recuire que les recettes touchées.
Outils hérités du sprint (a) : `SplatPlanches.Trouver` / `LireImage`, `PoserPieceSplat`,
`PoserPieceFeuille`, `PoserOrganeSplat`, `PoserFoliolesSplat`, `TouffeGerbe`,
`tools/splat/cuire.js`, `cuire_portraits.js`.
