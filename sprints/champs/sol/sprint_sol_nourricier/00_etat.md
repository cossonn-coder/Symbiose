# Sprint SOL NOURRICIER (D120) — état partagé

**Conception FIGÉE le 2026-10-30** (`/conception D120`, Nico : oui à Q1-Q3). Doc :
`docs/champs/sol/conception_sol_nourricier.md`. Golden de départ `fecccded…`
(`python3 -m tests.test_golden` depuis `data/code/`) : **re-figé au ① puis au ②
(annoncé)**, intact ③④⑤. Filet C# : `dotnet build Symbiose.csproj`.
Mesures : `mesure_faim.py` (plantes + NPK), `sonde_betes.py` (bêtes), référence
avant sprint `faim42.log` (seed 42) — lancer depuis `data/code/` avec `PYTHONPATH=.`.

## Diagnostic de départ [seed 42, n=1 run]
NPK médian 1,01/1,01/1,01 → 0,03/0,40/0,01 en 91 sem. ; croissance aveugle à N/P/K
(vitalité 0,81-0,93 avec qi 0,00) ; voix plante dite dès s0 (seuil 1,2) ; 75-100 % des
bêtes « affamées » à populations stables ; hérisson sur 619/1 188 plots (→ D119).

## Décisions clés
- Recharge lente vers l'équilibre de la roche (`NUTRIENT_INIT_PAR_SOL`) ; lessivage
  passif seulement là où l'eau draine.
- Carence = croissance escomptée (patron allélopathie sur `growth_factor`), continue,
  avec plancher ; pas de mort (D41).
- Voix plante = 1 − facteur de nutrition (même source) ; voix bête = déficit de la
  population face à sa nourriture (grille de rendu, bit-identique).
- Mare NE remplie et peuplée dans `full` (aulne, sphaigne, rossolis, moustique, libellule).

## Tronçons
| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_recharge_sol.md` | re-figé `7791bfb8…` | **FAIT** 2026-10-30 |
| ② | `02_croissance_nutrition.md` | re-figé `4c696821…` | **FAIT** 2026-10-30 |
| ③ | `03_voix_justes.md` | inchangé `4c696821…` | **FAIT** 2026-10-30 |
| ④ | `04_mare_nord_est.md` | inchangé `4c696821…` | **FAIT** 2026-10-30 |
| ⑤ | `05_vue_mare_voix.md` | inchangé `4c696821…` | **FAIT** 2026-10-30 |

## Notes de tronçon
(chaque tronçon : fait, mesures avant/après, hash golden, écarts au kickoff)

### ① Recharge + lessivage lié à l'eau — FAIT (2026-10-30, non commité)
- `nutriments.py` : `equilibre_roche(soil_type)`, `recharge(stock, eq, taux)` (purs) ;
  `leach_factor(…, drainage_norm=1.0)` pondère la part passive par l'eau drainée.
- `matiere_organique.tick_decomposition(recharge_roche=True)` : lessivage × drainage,
  puis recharge APRÈS lessivage et AVANT l'uptake (étape 8) → rien n'annule la recharge
  avant lecture. Équilibre = `soil_type` (roche), jamais la valeur initiale du plot.
- `constants.py` : `RECHARGE_DEMI_VIE_ANS = {N 0.2, P 0.5, K 0.25}` → `RECHARGE`.
- **Écart conception (à valider par Nico)** : les demi-vies visées (N 1 an, K 2-3 ans,
  P 5 ans) ne tiennent PAS la cible ≥ 40 % : avec elles, NPK méd. an 2 [seeds 42/1/2,
  n=3] N 0,12-0,30 / K 0,05-0,38 (≈ 12-17 % d'éq. pour N). Le prélèvement de ~700-1 000
  plantes impose `stock ≈ eq − prélèvement/RECHARGE` → remontée ~5-10× plus rapide
  retenue (N ≈ 10 sem., K ≈ 13 sem., P ≈ 26 sem., hiérarchie N > K > P gardée).
- **Conteneurs** : `world/container.py` passe `recharge_roche=False` (pas de roche
  sous un pot → le substrat s'épuise vraiment ; non prévu au kickoff).
- Mesures (`mesure_faim.py`, 156 sem.) — NPK méd. tuiles brut, s104 (an 2) :
  avant [seed 42] 0,03/0,29/0,01 ; après 42 : 0,62/0,37/0,61 · 1 : 0,73/0,65/0,73 ·
  2 : 0,47/0,55/0,61. Ratio stock/équilibre roche (méd. tuiles), minimum sur an 2
  (s104-s156) [seeds 42/1/2, n=3] : N ≥ 0,48 · P ≥ 0,61 · K ≥ 0,56 → cible ≥ 0,40 tenue
  (aussi en an 1, min N 0,42 seed 2 s78). Jachère : test_lessivage cas 8, N 0,10 → éq.
  comblé ≥ 50 % en 52 sem. (cible tenue largement avec 10 sem. de demi-vie).
- Effet en jeu : plantes plus nombreuses (an 2 seed 42 : 702 → 988) ; mais `qi méd`
  retombe ~0,00-0,03 en an 3 et « faim » reste la voix dominante (P cité surtout) —
  attendu, c'est l'objet de ②/③.
- Golden `fecccded…` → **`7791bfb8cb5d1342084a21fb6bb5250eeaf536e76e187cdb88cd420b6038088e`**
  (n/p/k du smoke changent — objet du tronçon). `population_hash.txt` re-figé avec
  (`a60c4a31…` → `b3ff9d4b…`, même cause). Suites `tests/test_*.py` toutes vertes.
- Tests adaptés : `test_lessivage` (cas 1-7 isolent le lessivage avec
  `recharge_roche=False` ; cas 2/6 réécrits : sans drainage rien ne part ; + cas 8-9
  recharge). `test_scatter_lumiere_sol` : sa référence gather ignorait le LOD émetteur
  D67 (`SHADING_POWER_MIN`) — bug latent du test révélé par le nouveau monde, corrigé.
- **Pré-existants (hors ①, constatés avant modif)** : `tests/bancs/test_edaphique`
  plante (IndexError, témoin carence sans plante) ; `tests/bancs/test_succession` 4/6.
  ⚠ pour ② : le banc `carence_npk` (n=p=k 0,05) va désormais REMONTER vers l'éq. en
  12 sem. (oracle « n < 0,3 » faux) → le banc devra couper la recharge ou se réviser.

### ② Croissance escomptée par la nutrition — FAIT (2026-10-30, non commité)
- `sim/nutrition_plante.py` (neuf, 39 LDC) : `nutrition_plante(plant, eco, roots)` →
  `(facteur ∈ [0,4 ; 1], nutriment limitant | None)` + `facteur_nutrition` (facteur
  seul). Par nutriment : `ratio = min(1, stock moyen sous racines / equilibre_roche
  (eco.soil_type))` ; poids = `BESOIN[nut][stade] / max BESOIN[stade]` ; `sat = 1 −
  poids·(1 − ratio)` ; Liebig = min ; rampe `0,4 + 0,6·min(1, s/0,6)`. Carnivore : N
  ignoré ; P amplifié par la mycorhize (miroir `qi_local`). Stade sans besoin (≥ 4) → 1.
  **API prête pour ③** (le limitant est rendu ; voix = `1 − facteur`).
- `sim/engine/croissance.py` : `target_g *= facteur_nutrition(plant, eco, roots)` juste
  après l'escompte allélopathique, sur la MÊME liste `roots` (pas de relecture). Import
  `sim.nutrition_plante` depuis `sim.engine` : sens des couches respecté.
- Constantes placeholders locales au module : `NUTRITION_PLANCHER 0.4`,
  `NUTRITION_SEUIL_PLEIN 0.6`.
- **Sonde** `sonde_nutrition.py` (neuve, ce dossier ; tuiles terre jumelles, éq. vs
  n=p=k 0,05, 26 sem. dès s14). Mode `maintenu` (stock remis à 0,05 chaque semaine) —
  h max riche → carencé : haricot 198 → 121 cm (−39 %, segments 6 → 5, gf 0,93 → 0,44) ;
  tournesol 48,8 → 42,4 ; basilic 24,9 → 21,3 ; tous vivants à mi-course (plancher
  tient). Mode `libre` (recharge ① active) : haricot 162 cm. **Avant ② : carencé ≡
  riche au cm près** (croissance aveugle). [1 seed de banc, n=1]
- **Effet en jeu** (`full` seed 42, 156 sem., espion sur le facteur) : part des
  lectures < 1 : 44 % (s0-25) → 81 % (s78-103) → 96 % (s130-155) ; facteur médian 1,00 →
  0,74 → 0,65 ; plancher 0,40 atteint ; limitant cité P 59 k / N 26 k / K 3 k (P =
  semis, stade 0 qui demande surtout P). [seed 42, n=1]
- `mesure_faim.py` (156 sem.) — plantes / vitalité méd., avant② → après② :
  seed 42 : an1 466→465, an2 988→999, an3 1074→1088 · seed 1 : 335→338, 706→719,
  838→868 · seed 2 : 411→423, 862→885, 944→968 ; vitalité méd. 0,73-0,80 inchangée.
  Population viable (critère ≥ 50 % tenu : ≈ 101-103 %) [seeds 42/1/2, n=3]. NPK méd.
  quasi inchangés. ⚠ la population ne baisse PAS : la carence ralentit la taille des
  individus, pas le recrutement (germination/succession non touchées — voulu, philo #2).
- Perf (`full` seed 42, 104 sem., runs alternés) : avant 812,6 / 773,7 ms → après 803,8 / 793,0 ms ; moyenne +0,7 % [n=2, bruit inter-runs ±2,5 %] → budget ≤ +3 % tenu. Le monde « après » porte +1-3 % de plantes (inclus dans la mesure).
- Golden `7791bfb8…` → **`4c696821ed69d323165c5638021d69bde0930c4af546d4bf971ddcdca0daeea1`**
  (smoke : facteur < 1 sur 48 % des lectures an 0, 70 % an 1, méd. 0,79, min 0,40 →
  `growth_factor` des plantes change — objet du tronçon). `population_hash.txt`
  re-figé avec (`b3ff9d4b…` → `3416d328…`, même cause). Suites `tests/test_*.py` toutes
  vertes (hors 500 ans, non lancé).
- Pré-existants inchangés : `test_edaphique` IndexError (même ligne : le TÉMOIN du banc
  `carence_npk` n'a plus de plante — rien à voir avec ②) ; `test_succession` 4/6 (mêmes
  2 échecs pioneer). Banc `carence_npk` NON retouché (son oracle `n < 0,3` reste à
  réviser ; la sonde ② couvre le critère croissance).

### ③ Voix justes — FAIT (2026-10-30, non commité)
- **Plante** (`sim/voix_etres.py`) : « faim » = `_ramp(1 − facteur, 0, 1 − PLANCHER)`
  depuis `nutrition_plante` (②), nutriment cité = son limitant ; plus de lecture NPK
  / `FIELD_NORM` propre (`SEUIL_FAIM` supprimé). Dite ⇔ croissance escomptée ≥ 15 %.
- **Bête** (`fields/population/field.py`, grilles de rendu jamais relues par la
  dynamique) : `faim = (pop − cible)/pop × part_lieu` si la guilde décline, où
  `part_lieu` = part de la baisse de ce tick venant de la capacité (nourriture +
  habitat) vs de la survie (froid/photopériode/prédateurs/perturbation), au prorata
  des baisses relatives ; sans baisse nouvelle l'imputation précédente tient. Lu par
  `PopulationField.faim(r, c)` ; rampe voix `(0 ; 0,4)` → dite dès cible ≥ 10 % sous
  la population. `faim_fleurs`/`faim_proies` suivent la même grandeur.
- **Écart au kickoff (hypothèse réfutée par la mesure)** : la définition prescrite
  (déficit face à la seule capacité, puis face à `capacité×survie` avec partage
  log statique) donnait soit 0 % partout (pop ≪ capacité : la survie la tient
  toujours sous la capacité), soit 89 % d'affamés au déclin d'automne (froid imputé
  au lieu car la capacité est toujours < 1). D'où l'imputation par BAISSE du tick
  (3 grilles de rendu en plus : capacité/survie précédentes, part imputée).
- Mesures [seed 42, n=1] — **plantes**, voix dominante « faim » avant → après ③ :
  s0 32 % → 0 % · s52 89 % → 14 % · s104 92 % → 36 % · s156 92 % → 54 % (P méd.
  0,26 = carence réelle, cible de croissance vraiment escomptée). Sonde
  `sonde_nutrition.py` (colonne ajoutée) : sol riche 0/26 sem. faim dite (haricot) ;
  carencé maintenu 26/26 ; carencé libre 11/26 [1 banc, n=1].
- **Bêtes** (`sonde_betes.py` adaptée : présence > 0,05, déclin = densité < 97 % de
  la semaine précédente) : dit faim avant③ → après③ : s26 95 % → 0 % (déclin 5 %,
  pucerons qui déclinent sous les prédateurs : 0 % affamés) · s40 (automne) 95 % →
  13 % (déclin 96 % : rapace 92 %, coccinelle 43 %, papillon 93 % — proies/fleurs
  qui s'effondrent ; abeilles/bourdons/syrphes ≈ 0-1 % : photopériode) · s78 79 % →
  0 %. Affamés qui déclinent vraiment : 100 % (81 % papillon s40).
- Perf (`full` seed 42, 78 sem., runs alternés) : avant 747,2 / 693,3 ms → après 687,1 / 721,4 ms ; écart dans le bruit [n=2, bruit inter-runs ±4 %] → budget ≤ +2 % non contredit.
- Golden **inchangé** `4c696821…` ; `population_hash` inchangé `3416d328…`. Suites
  population / vision / infobulle_vivant / peripherie_voix / sim_server / vigueur vertes.
- Constat hors périmètre (pas touché) : dans `sonde_nutrition.py`, tournesol et
  basilic sont morts dès ~4 sem. sur les DEUX tuiles (riche comme carencée) — la
  mention « tous vivants à mi-course » du ② ne tient pas ; sans lien avec la carence.

### ④ Mare remplie et peuplée (tuile NE, `full`) — FAIT (2026-10-30, non commité)
- `sim/mare_initiale.py` (neuf, 42 LDC) : `poser_mare(tile, eco, seed)` appelé par
  `main.build_world_full` (donc `full`, `propre` et démo). Fond 3×3 (7..9, 4..6) plat
  à 2 cm, berge-anneau à 12 cm ; fond saturé + lame 1,2 + `marais_memory` 0,85 + état
  marais ; pH 4,8 (fond+berge) ; moustique 0,10 / libellule 0,05 amorcés ; semis
  fondateurs : 2 aulnes (berge sud), 3 sphaignes, 2 rossolis (sortis du stade semis).
- **Écart au kickoff n°1 (hypothèse réfutée par la mesure)** : le patron `tourbiere`
  seul ne tient PAS — cuvette sèche en 4 sem., plus marais vers s24-32 [seed 42] (lame
  évaporée 20 %/sem., sable qui boit). Ajout d'une **source** = nappe affleurante
  ponctuelle : `fields/ecofields/source.py` (`SourceMixin.tick_source`, 11 LDC, même
  geste d'affleurement que `tick_berge`), champ `EcoFields.sources` (liste, défaut
  None ⇒ no-op), appel `eco.tick_source()` juste après `tick_berge` dans
  `sim/engine/boucle.py`. Débits placeholders : fond 0,30, berge 0,03 /sem. Aucun
  paramètre d'hydrologie ni de population modifié. **À valider par Nico** (mécanisme
  neuf, philo #2 tenue : on écrit de l'eau dans le milieu, le marais émerge).
- **Écart n°2** : placement hors du coin nord-est de la tuile. Ce coin est à < 150 cm
  des bords nord/est du monde → sous la nappe de ceinture : au seed 1 (rivière en creux
  au nord, −75 cm) il était sec dès s16 (centre en eau 6/104 sem.). Au sud de la tuile
  (lignes ≥ 3, colonnes ≤ 7 : hors portée) la mare tient sur tous les seeds testés.
- Fond plat (pas de pente vers le centre) : la fraction ruisselée ne dépend que du
  signe de la pente → un fond creusé vidait 8 plots dans le central (3/9 en eau).
- Mesures `sonde_mare.py` (104 sem.) [seeds 42/1/2, n=3] — plot central lame>flaque
  ET marais : 104/104 sem. sur les 3 seeds ; semaines avec ≥ 5/9 plots du fond lame+
  marais : 98 / 90 / 100 sur 104 ; aulnes vivants an 2 (vitalité 1,0 ×2, 3 seeds) ;
  moustique et libellule présents en été an 1 (s16-36, dens. max 0,25-0,46) et an 2
  (s68-88, 0,23-0,44), absents l'hiver (photopériode) ; sphaignes vivantes et qui se
  ressèment ; 1 rossolis mort s63 au seed 1 (ombre 0,6), sinon 7/7 vivants.
- Golden **inchangé** `4c696821…`. Tests : `test_sim_server` 2 checks du monde `full`
  mis à jour (88 plantes = 81 + 7 ; marais à l'init = 9 plots NE seulement) → 307/307 ;
  `test_population`, `test_marais`, `bancs.test_hydrologie`, `test_bois_mort`,
  `test_automate_*`, `test_peripherie_pont`, `test_signes_legende` verts. Pas de C#.
- Pour ⑤ : la mare est en (7..9, 4..6) de la tuile NE (monde x 1650-1800, y 350-500
  cm), PAS dans le coin nord-est (le kickoff ⑤ dit « au nord-est » : vrai à l'échelle
  du monde). Les aulnes grandiront et ombreront vers le nord (cultures lignes 0..5 de
  la tuile NE) à long terme — conséquence émergente, à surveiller au F5.

### ⑤ Vue : mare lisible + voix vérifiées — FAIT (2026-10-30, non commité)
- `visuals/PuddleLayer.Mare.cs` (neuf, partial, 112 LDC) + `PuddleLayer.cs` (133 LDC) :
  un plot `marais` à `etat` vrai ET en eau (`eau_surface`) = **MARE** → eau opaque
  `24566b` (cœur `1f4a5c` si 4 voisins d'eau), 2 reflets horizontaux placés par hash
  entier du plot (pas `string.GetHashCode`, randomisé en .NET), **rive** de vase sur
  les arêtes sans voisin d'eau (coins MONDE projetés → suit la rotation D35). Plot
  marais voisin (8-connexité) d'une mare = **BERGE** (terre mouillée + mousse).
  Aucun champ neuf, aucun changement de pont (blocs `marais` [avec `etat`] et
  `eau_surface` déjà sérialisés). Même lot → **+0 draw call** (par construction).
- **Écarts au kickoff** : (a) chemin `tools/simserver/serialize.py` = en fait
  `data/code/tools/simserver/serialize.py` ; (b) le banc de capture n'a pas d'option
  pour ALLUMER la vision côté Python (`--capture-vision` n'impose que l'effet écran)
  → les voix sont relevées par les fonctions mêmes que sert `cmd_parler`
  (`sim/voix_etres`), script hors dépôt ; (c) la berge-anneau du ④ (lignes 6/10,
  colonnes 3/7) n'a PAS de `marais_memory` → la vue ne la dessine pas en berge (pas
  de donnée) : seule la rive l'évoque ; les plots du FOND à sec (marais sans lame)
  deviennent berge de vase.
- Captures [seed 42, `full`, été an 1 s25, centre 1725,425] ×1, ×2, ×4, ×8, ×16 :
  la mare se lit (eau sombre fermée par sa rive, reflets) ; 5/9 plots en eau à cet
  instant, 4 en vase. Libellule vue sur l'eau (×8). Quasi-noir dans le cadre de la
  mare : 0,00 % ×1/×2/×4 (avant ⑤ ×4 : 0,00 %) ; ×8 0,09 % = le merle posé au bord,
  hors eau (couleurs mare vérifiées L OKLab ≥ 0,39, `da_image.quasi_noir` faux).
- Plantes de mare : aulnes (×2) rendus en arbre ; rossolis = rosette à fleur blanche
  bien visible à ×16 ; **sphaigne = tapis translucide quasi invisible** (disques
  vert pâle, info-bulle « Sphagnum · tapis » au survol) → point F5, pas retouché
  (`PlantRenderer`, hors périmètre ⑤).
- Voix [seed 42, n=1, s61 printemps / s79 automne an 2] — plantes : faim DITE
  (≥ `SEUIL_DIRE`) 49 % / 62 %, faim DOMINANTE 27 % / 11 % (dominantes s79 :
  ravageurs 589, concurrence 120, faim 95 sur 888) ; bêtes présentes > 0,05 : faim
  dite 0 % (s61, 0 plot) / 0,3 % (53/17 519, s79). 10 phrases relevées :
  1. Minette (N) « Je suis bien ici. L'eau, la lumière, le sol : tout me va. »
  2. Trèfle (NO) « Trop de racines autour des miennes. Minette boit ce que je voudrais boire. »
  3. Trèfle (S) « On se bat sous terre, et Haricot y a le dessus. » / « Je cherche le phosphore sous moi, il n'y en a presque plus. »
  4. Trèfle (NE) « Mes feuilles sont criblées. J'attends mes alliés. » / « Il me manque le phosphore. Le reste du sol ne sert à rien sans lui. »
  5. Pâturin (O) « Je cherche l'azote sous moi, il n'y en a presque plus. »
  6. Trèfle (E) « La lumière ne m'arrive qu'en miettes. J'en voudrais plus. »
  7. lombric (NO) « Ce coin de jardin me convient. »
  8. coccinelle (NO) « Il y a de quoi vivre ici. Je reste. »
  9. moustique (mare NE 7,6) « J'ai senti La libellule. Il faut que je me terre. »
  10. hérisson (NO) « Je ne trouve pas où me cacher. Le sol est trop nu, trop remué. »
  ⚠ cloporte (NO 9,4) dit encore « rien à me mettre sous la dent » (compté hors
  faim D120, phrase de nourriture d'une autre source — à regarder au F5). Majuscule
  fautive « J'ai senti La libellule » (corpus voix, hors ⑤).
- Golden **inchangé** `4c696821…`. `dotnet build` vert (0 avertissement). Aucun
  processus Xvfb/Godot laissé.
- **F5 Nico** : mare reconnue au nord-est (tuile NE, sud de la tuile) à ×1-×4 ;
  libellules/moustiques sur l'eau en été ; sphaigne lisible ? ; sous vision (U),
  les plantes ne crient plus toutes famine ; un coin exploité réclame encore et
  pousse moins ; rive/reflets à calibrer (couleurs placeholders).

**SPRINT CLOS** (①→⑤ faits, ⑤ non commité au moment de l'écriture).

## §REPRISE
Sprint CLOS : reste le F5 de Nico (liste en note ⑤) puis DETTE/BACKLOG/journal.
Lire `CLAUDE.md` + ce fichier. Golden courant `4c696821…` (intact attendu ⑤). Mare : fond
(7..9, 4..6) de la tuile NE, source `eco.sources`, sonde `sonde_mare.py`. ⑤ : la voix bête lit
`PopulationField.faim` (grille de rendu, pas de version de pont à changer : le pont
ne sert que les phrases).
Lancement : `/sprint-auto sprint_sol_nourricier`.
