# sprint_frein_rejets_figuier — état (reliquat D130 : rejets de souche)

**Phase** : conception FIGÉE le 2026-11-09 (OK Nico), prêt pour `/sprint-auto`.
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
| ④ | `04_voix_et_mesure.md` — événement, carnet, encyclopédie, `diag_releve` voie `rejet`, 200 ans | à faire |
| ⑤ | `05_vue_godot.md` — voix `attente` (relève ⑤) + rejets visibles, `dotnet build`, F5, clôture D130 | à faire |

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

## §REPRISE
Exécution : `/sprint-auto sprint_frein_rejets_figuier`. Prochain tronçon = le
premier « à faire » (④ `04_voix_et_mesure.md` — parser les DEUX causes du log 🌳 : `[souche de @…]` et `[perte de couronne de @…]`). Chaque tronçon met à jour sa ligne + un § « Tronçon N — fait ».
