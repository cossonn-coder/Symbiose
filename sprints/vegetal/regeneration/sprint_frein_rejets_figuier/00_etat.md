# sprint_frein_rejets_figuier — état (reliquat D130 : rejets de souche)

**Phase** : **CLOS** le 2026-11-09 (①→⑤), **F5 validé** par Nico le même jour, D130 fermée (lot Q).
Doc : `docs/vegetal/regeneration/conception_rejets_de_souche.md`.
Golden `a10b7225…` **INCHANGÉ** attendu sur les 5 tronçons.

## Pourquoi (mesuré le 2026-11-09, verger_mur, seed 42, n=1 run, VM)
- Espion 25 ans : 164 rejets de figuier, **164 en hiver** ; lumière au plot ≥ 0,7
  pour 163, couverture 0 pour 164 → les portes du clonal sont ouvertes en
  dormance. Cascade : 4 générations en 25 ans (un rejet est mère à 5 ans).
- Sans l'hiver : 0 rejet en 25 ans (portée 100 cm < couronne ~250 cm ; lumière
  sous la mère 0,25 < 0,30 l'été). Tout ou rien → c'est le modèle, pas un réglage.
- Golden : 36 ramets de trèfle, 0 en hiver [smoke, n=1 run] → ① neutre attendu.

## Décisions (Nico, 2026-11-09)
- Q1 **A** : rejet de souche = réponse à la perte de la partie aérienne ; plus
  d'émission de fond pour le figuier ; au pied, sans gate lumière à la naissance.
- Q2 **comme dans la nature** : déclencheurs = mort ET grosse perte de couronne
  (casse, neige, cladoptose, effondrement, taille joueur) ; souche vivante lue
  sur les mémoires de dommage au pied (ombre, sécheresse, asphyxie, racines
  rongées, pourridié), pas sur une cause.
- Q3 le trou hivernal générique (toutes clonales) est traité dans ce sprint
  (golden re-figé autorisé ; mesuré inutile).
- Q4 trait `rejet_souche` pour tous les ligneux selon leur capacité réelle.
- Q5 gel des rameaux d'un ligneux adulte → dette **D131**.
- Q6 le ⑤ vue de `sprint_releve_ligneuse` est absorbé par le ⑤ d'ici.

## Tronçons
| # | kickoff | état |
|---|---|---|
| ① | `01_dormance_clonale.md` — pas d'émission clonale en hiver (toutes clonales) | **fait** 2026-11-09 |
| ② | `02_souche_a_la_mort.md` — trait `rejet_souche`, souche vivante, rejets à la mort, figuier sans drageon | **fait** 2026-11-09 |
| ③ | `03_perte_de_couronne.md` — mémoire `perte_couronne`, rejets d'un arbre vivant (taille = recépage) | **fait** 2026-11-09 |
| ④ | `04_voix_et_mesure.md` — événement, carnet, encyclopédie, `diag_releve` voie `rejet`, 200 ans | **fait** 2026-11-09 — 3 critères tenus |
| ⑤ | `05_vue_godot.md` — voix `attente` (relève ⑤) + rejets visibles, `dotnet build`, F5, clôture D130 | **fait** 2026-11-09 — F5 validé |

## Tronçon 1 — fait (2026-11-09)
- `sim/clonal.py::emettre_ramets` : retour immédiat si `saison_de(wiy_de(week))
  == "hiver"`, avant tout tirage. Import depuis le module racine `calendrier`
  (couche basse, pas de cycle ; `sim.engine` importe `sim.clonal`).
- Test neuf `tests/test_dormance_clonale.py` (figuier mûr, plein soleil, 4 ans :
  hiver 0 ramet, saisons actives 29) ; vérifié ROUGE sans la garde (8 en hiver).
- `test_figuier_realiste` (c) inchangé et vert : 29 rejets en 200 sem. (plein
  soleil imposé → les saisons actives émettent encore ; réécrit au ②).
- Golden `a10b7225…` **INCHANGÉ** ; `test_evenements` 42/42, `test_quatre_feuilles`,
  `test_phototropisme` 11/11 verts.
- Mesure `full`, seed 42, 5 ans [n=1 run, VM chargée] : seul le trèfle est
  clonal dans ce monde (pas de figuier en `full`). Avant 1119 ramets dont 117
  en hiver ; après 1016, 0 en hiver (printemps 268, été 467, automne 281). L'été
  récupère une partie de la place laissée libre.
- Le figuier n'émet désormais plus que hors hiver (en verger_mur : 0 attendu,
  mesure du 2026-11-09) — transitoire jusqu'au ②.

## Tronçon 2 — fait (2026-11-09)
- Trait `rejet_souche` (`plants/base/familles.py`, défaut 0) ; valeurs du kickoff
  sur les 11 arbres (`perennials/`), sapin laissé au défaut (commenté).
- Figuier : `clonal_mode` hérité `"none"`, `clonal_radius_cm` **retiré** (inutile) ;
  commentaire relève ③ réécrit.
- Critère pur `souche_vivante(plant)` dans `sim/effects/perturbations.py` (à côté
  de `seuil_ombre`, évite un cycle d'import) ; figé dans `deposer_mort` sur
  l'instance (`souche_vivante`, `souche_traitee`, `plants/base/instance.py`).
  Seuils lus au code : ombre `seuil_ombre`, sécheresse `DROUGHT_DAMAGE_THRESHOLD`
  0,6, asphyxie `ASPHYXIE_HEALTH_SEUIL` 0,10. **Écart** : racines rongées et
  pourridié n'ont PAS de seuil de nuisance (rabot de l'eau dès 0, `engine/racines.py`)
  → `SEUIL_RACINES_ATTEINTES = 0,2` = début du signe « parasite » (`voix_etres`).
- `sim/souche.py::emettre_rejets_souche`, câblé `sim/engine/boucle.py` étape 9f
  juste après `emettre_ramets`. N = round(rejet_souche×4) (figuier 3, pommier 2,
  bouleau 1), rayon 60 cm, plot valide seulement (ni lumière ni couverture), clones,
  hashs week·67/71 (+k). Le squelette porte la souche (vérifié : retrait à bois
  ~épuisé, décroissance géométrique ⇒ bien plus d'un hiver) — pas de liste tuile.
- **Log** : `    🌳 Rejet de souche : {nom} @{plot} ×{n} [souche de @{plot_mort}]`.
  **Écart** : 🌳 et non 🌱 — `sim/evenements` lit toute ligne 🌱 comme une avance
  (germination fantôme) ; 🌳 y est ignoré. Le ④ doit parser CE format.
- Tests : `test_rejets_souche` neuf (a-e verts) ; `test_figuier_realiste` (c)
  réécrit (vivant ⇒ 0 rejet de fond) ; `test_dormance_clonale` porté sur le
  framboisier (le figuier n'est plus clonal ; revérifié rouge sans la garde : 8).
  `test_banque_semis`, `test_evenements` 42/42, `test_stress_chronique`,
  `bancs.test_verger_mur` verts. Golden `a10b7225…` **INCHANGÉ**.
- Taille : `sim/engine/boucle.py` passe à 301 LDC (bande vigilance, une seule
  responsabilité) — à surveiller au `/refactor` de fin de sprint.

## Tronçon 3 — fait (2026-11-09)
- `PlantInstance.perte_couronne` (`plants/base/instance.py`, défaut 0).
- `sim/souche.py` : `noter_perte_couronne(plant, tombes)` (volume `l × ép²`, forme
  de `deposer_bois_tombe` ; bois avant = restant + tombé) ; émission étendue aux
  arbres vivants (`_vague` factorisée), `boucle.py` NON touché (même étape 9f).
- Sites d'incrément vérifiés au code (pas de point commun propre : `_rebuild` sert
  aussi l'élagage de croissance) : `sim/engine/branches.py::mort_des_branches`
  (toutes causes de la semaine en un appel) + `sim/actions/gestes.py::tailler`.
  L'élagage naturel de `grow_plant` (9c) ne compte PAS (pas dans la liste du kickoff).
- **Écart 1** : composition `1 − (1−m)(1−f)` au lieu de `m += f` — la somme
  surestimait une taille en plusieurs coupes (0,89 pour 0,71 réellement ôté).
- **Écart 2** : l'oubli (×0,94/sem, `PERTE_COURONNE_OUBLI`) n'a lieu QU'HORS hiver
  (l'oubli = la couronne qui repousse) ; sinon une taille d'hiver serait oubliée
  avant le printemps (×0,94¹³ ≈ 0,45 → 0,7 tombait sous 0,5). Pas de drapeau neuf.
- Déclencheur ≥ `SEUIL_PERTE_COURONNE` 0,5, hors hiver : épisode consommé
  (mémoire → 0) même si la souche est épuisée ; N = round(rejet_souche × 4 × m).
  Tuile saturée → l'épisode attend. Chemin mort : `return` → `continue` (équivalent).
- **Log** (à parser au ④) : `    🌳 Rejet de souche : {nom} @{plot} ×{n} [perte de
  couronne de @{plot_arbre}]` ; la mort garde `[souche de @…]`.
- Mesure [labo, figuier/sapin de 10 ans, n=1 arbre] : figuier taillé au ras en
  hiver → perte 0,72, 2 rejets au 1ᵉʳ printemps (sem. 53), aucun en 2 ans ensuite ;
  sapin au ras (0,70) → 0 ; casse de 2 branches (`branches_a_casser`) → 0,058, 0.
- Tests `test_rejets_souche` (f)(g)(h)(i) ajoutés, (a)-(e) verts. Golden
  `a10b7225…` **INCHANGÉ**. Verts : `test_bois_mort`, `test_vigueur`,
  `test_evenements`, `test_figuier_realiste`, `test_dormance_clonale`,
  `test_squelette_herbacees`, `test_croissance`, `bancs.test_verger_mur`.

## Tronçon 4 — fait (2026-11-09)
- **Événement** `sim/evenements.py` : `_RE_REJET` lit les DEUX formats 🌳
  (`[souche de @…]` → cause `souche`, `[perte de couronne de @…]` → `perte_couronne`),
  kind `rejet`, **pos = l'arbre** (2ᵉ @), pas le 1ᵉʳ rejet. L'API historique
  `_evenements` reste muette sur 🌳. Test `test_evenements` [B6] (46/46).
- **Carnet** : `("rejet", souche|perte_couronne)` → concept existant `rejet_de_souche`
  + 4 gabarits D/I (le mort d'ombre/soif ne repart pas ; taillé au ras = recépé).
- **Encyclopédie** (N2) : une phrase de capacité par arbre à `rejet_souche > 0`
  (figuier, pommier, cerisier, noyer, chêne, hêtre, bouleau, charme, aulne ; saule
  déjà couvert au N3) ; sapin « ne rejette pas » ; figuier corrigé (rejets après
  mort/perte de tête, pas en continu).
- **Outil** `tools/diag_releve.py` : voie `rejet` = événement `rejet` même tuile,
  même espèce, ≤ `PORTEE_REJET_PLOTS` 2 plots de l'arbre (le log ne porte que le
  1ᵉʳ rejet).
- **Mesure verger_mur, seed 42, 200 ans** [n=1 run, VM charge ~0,6-3, 102 min] :
  | espèce | fondateurs (morts) | recrues | mûres | remplacement | vivants an 200 |
  |---|---|---|---|---|---|
  | cerisier | 1 (1) | 76 graine + 23 rejet | 67 | 67 [n=1 run] | 12 |
  | pommier | 1 (1) | 54 graine + 6 rejet | 50 | 50 [n=1 run] | 0 (dernier mort sem 8972) |
  | noyer | 2 (2) | 61 graine + 2 rejet | 24 | 12 [n=1 run] | 7 |
  | figuier | 1 (1) | 6 rejet | 5 | 5 [n=1 run] | **0** (dernier mort sem 9133) |
  Fourré max **4** (cerisier, sem 2873) contre 193 au ④ de la relève ; ligneux
  vivants 7-29 sur tout le run (350 à l'an 200 avant). **Les 3 critères sont tenus,
  aucun calibrage.** Cascade du figuier freinée : 2 vagues de 3 rejets (mort du
  fondateur sem 2690 par sénescence, puis d'un rejet sem 5986 par sénescence) ;
  les 6 autres rejets meurent d'ombre → souche morte → plus de rejet.
- **Constat pour Nico** : le figuier (et le pommier) s'éteignent avant l'an 200
  [n=1 run]. « ≤ 10 » est tenu, mais 0 n'est pas « une poignée ». Cohérent avec le
  modèle (un arbre mort d'ombre ne repart pas, pas de graine fertile) ; à lire au F5,
  pas un calibrage du ④.
- **Perf `full`** tick médian an 3/4/5 : avant (worktree `ac9f758`) 1087/1095/1039 ms,
  après 992/1071/1030 ms, soit −9/−2/−1 % [seed 42, n=1 run par côté lancés en
  parallèle, VM charge ~3] → critère ≤ +10 % tenu.
- Golden `a10b7225…` **INCHANGÉ**. Verts : `test_evenements` 46/46, `test_carnet`
  19/19, `test_encyclopedie` 70/70, `test_rejets_souche`, `test_peripherie_voix`
  91/91, `test_journal`, `test_pages`, `test_figuier_realiste`, `test_dormance_clonale`.
  Tailles : `sim/evenements.py` 211 LDC, `sim/carnet.py` 239, `diag_releve` 165.

## Tronçon 5 — fait (2026-11-09)
- **Voix `attente`** (`sim/voix_etres.py::besoins_plante`) : un ligneux ombragé dont
  `shade_memory` ≤ `seuil_ombre(plant)` dit `attente` au lieu de `ombre` (même
  intensité, même rampe 0,2→0,8) ; au-delà du seuil → `ombre` ; herbacée → `ombre`.
  Import `sim.effects.perturbations.seuil_ombre` (même couche `sim`, pas de cycle :
  rien dans `sim.effects` n'importe `voix_etres`). **Écart** : `attente_anonyme` ajouté
  (sans ombreur identifié, sinon le gabarit `{voisin}` manquait) — miroir de
  `ombre_anonyme`. Corpus : 2 thèmes × 2 variantes (`sim/voix_etres_corpus.py`).
  Note : la règle vaut pour tout ligneux, pas seulement les semis (un grand arbre
  ombragé sous 0,55 dit aussi qu'il attend une trouée) — conforme au kickoff.
- **Voix d'un rejet** : `voix_etres` n'a AUCUN thème d'origine/naissance (que des
  besoins mesurés) et l'instance ne garde pas sa voie de naissance → rien inventé.
- **Rendu** : un rejet = `tile.add_plant` (clone), sérialisé par la même boucle
  `tile.plants` que toute plante (`tools/simserver/serialize.py`), aucun filtre
  ramet/clone côté pont ni C# → **aucun code C#**. Pont **inchangé** (aucun champ
  du snapshot ne bouge, pas de bump).
- Test neuf `tests/test_voix_attente.py` 10/10 (hauteurs posées dans le contexte :
  un arbre non poussé mesure ~1 cm). Verts : `test_sim_server` 322/322,
  `test_mare_vivante` 14/14, `test_infobulle_vivant` 31/31, `test_vision` 38/38,
  `test_rejets_souche`. Golden `a10b7225…` **INCHANGÉ**. `dotnet build` vert (0 erreur).
  Tailles : `voix_etres.py` 145 LDC, corpus 74.
- Clôture faite : `DETTE.md` D130 « code fait, reste F5 » + reliquat chiffré (figuier
  et pommier éteints ~an 173-176, à trancher par Nico) ; `BACKLOG.md` ; relève → CLOS.
  **Reste à l'orchestrateur** : entrée `journal/` + index `journal.md`, commit.
- **F5 Nico** : (1) turbo `verger_mur` : plus de colonie de figuiers, le figuier
  reste seul ; (2) tailler sévèrement le figuier → au printemps, quelques rejets au
  pied ; (3) mort d'un fruitier âgé → rejets au pied du squelette (sauf sapin et
  arbre mort d'ombre) ; (4) survoler un jeune arbre sous un fruitier → « j'attends… ».

## §REPRISE
Sprint CLOS côté code. Reste : F5 Nico (§Tronçon 5) ; le reliquat D130 (extinction
figuier/pommier vers l'an 173-176) est à trancher par Nico. Suite : D42 (dispersion animale).

## F5 — validé (2026-11-09)
Nico : « ça fonctionne » (verger_mur, seed 42, an 9, après `git pull`). Une taille large des rameaux ne fait pas rejeter (0 à 3 % du bois [an 8, n=1 run, VM]) : il faut recéper au ras du tronc. Reliquats acceptés : extinction ~an 175, étêtage selon la part de bois perdue.
