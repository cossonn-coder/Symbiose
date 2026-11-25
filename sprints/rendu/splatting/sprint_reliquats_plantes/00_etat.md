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
| ② | `02_classes_taille.md` — 3 tailles par recette, correction du √2, recuisson | à faire |
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

## F5 (à remplir par les tronçons, consolidé au ⑥)
- ① À ×32 sur un tournesol et un pommier : les feuilles et les fleurs sont en volume (splats).
  L'à-coup au premier passage à ×32 (gel d'environ 1-2 s par grande plante sur la VM) est-il
  gênant sur le PC ? Touche C : lire `précuisson X/1024 Mo` sur la HD 4600.

## §REPRISE
Lire `CLAUDE.md`, ce fichier, la conception, puis le kickoff du premier tronçon « à faire »
(① fait : prochain = ② `02_classes_taille.md`). Budget de précuisson : `visuals/BudgetCuisson.cs`.
Outils hérités du sprint (a) : `SplatPlanches.Trouver` / `LireImage`, `PoserPieceSplat`,
`PoserPieceFeuille`, `PoserOrganeSplat`, `PoserFoliolesSplat`, `TouffeGerbe`,
`tools/splat/cuire.js`, `cuire_portraits.js`.
