# sprint_releve_ligneuse — carnet de bord de conception (D130)

**Sujet** : la relève des arbres meurt toujours à l'ombre de ses parents (D130,
Nico 2026-11-06, après la chronique 200 ans de D127).
**Phase** : conception FIGÉE le 2026-11-06, prêt pour `/sprint-auto`.

## Constats vérifiés au code (2026-11-06)
1. Recrutement direct ligneux = `MortaliteMixin._reproduction`
   (`sim/engine/mortalite.py:155`), reste du « M7 provisoire » : chaque semaine,
   un arbre mûr (`is_seed_bearing` = âge ≥ maturité, TOUTE l'année) fructifie avec
   p = `reproduction_rate` (noyer 0,10, figuier 0,15…) ; la recrue est posée sur le
   plot le plus lumineux (`eco.lumiere.at_plot`, seuil 0,35) dans
   `RESEED_RADIUS_CM` = 150 cm (+1 plot) autour du parent. Ce n'est relié ni aux
   fruits traçables (HOUPPIER ③) ni à la saison des fruits.
2. Les caducs ont `foliage_density_at(.., "hiver") = 0` → un tirage en hiver voit
   le sol sous la couronne éclairé. Hypothèse (à confirmer par le diag) : des
   recrues posées en hiver sous la couronne, dans l'ombre pleine l'été suivant.
3. Ombre → mort : `shade_stress_damage` (`sim/effects/perturbations.py:350`) :
   p = 0,10 × sévérité / tolérance, sévérité depuis `shade_memory` > 0,55
   (lerp 0,10/sem de 1 − lumière reçue). Aucun terme d'âge ni de taille.
   Taux 0,10 borné par l'invariant sciaphile de `test_stress_chronique`.
4. Croissance : `ok_light = light >= 0.2` (`sim/engine/croissance.py:156`) →
   sous 0,2 la plante stagne (pas d'avance de stade). Cladoptose et réveil de
   bourgeon dérivés de la tolérance effective.
5. Tolérances : noyer 0,80, cerisier 0,80, pommier 0,85, figuier 0,85 (héliophiles) ;
   hêtre 1,30, sapin 1,25, charme 1,15 (sciaphiles, `perennials/forestiers.py`).
6. Aucun canal de dispersion animale (D42 ouverte, T4 de la complétude). Seule
   l'anémochorie déplace un dépôt (banque-sol, pas le recrutement direct).
7. Figuier : `pollination_mode = "self"` ; en Normandie la figue commune n'a pas
   de graine fertile (pas de blastophage) — ses 9 recrues sont botaniquement
   fausses (à trancher).
8. `verger_mur` coupe la banque-sol (`germination_candidates = []`) et
   l'herbivorie : seule voie de recrutement = le direct ci-dessus.

## Données (run D127, verger_mur, seed 42, 200 ans, n=1 run, VM)
30 recrues, 25 morts sur 34 par ombre, 0 recrue adulte.

## Diag par recrue (verger_mur, seed 42, 75 ans, n=1 run, VM, 2026-11-06)
Script hors dépôt (scratchpad de session, perdu au /clear) : `SimServer` +
`cmd_step_week`, suivi par `id(p)` des plantes absentes au départ, lumière
`light_received` et `shade_memory` toutes les 13 semaines.
- 20 recrues [n=1 run], TOUTES nées en semaine 39 de l'année.
- Mortes : lumière d'été reçue 0,25 à 0,55, `shade_memory` 0,55 à 0,77 au moment
  des dégâts ; vie de 272 à 2 538 semaines. Survivantes à l'an 75 : lumière d'été
  0,5 à 0,8.
- L'arbre le plus proche d'une recrue morte est à 71-361 cm : le parent fondateur
  OU une autre recrue (fratrie posée dans le même rayon de 150 cm).
- Le « stade » ne dit rien pour un arbre : un seul stade `arbre` (durée 0), la
  taille vient des segments.
- **Cause structurelle** : `RESEED_RADIUS_CM` 150 cm < rayon de couronne d'un
  fruitier adulte → toute recrue naît sous la couronne d'un parent. Le seuil de
  pose (lumière > 0,35) est sous le seuil de dégât d'un héliophile (dégât dès
  lumière < ~0,45 en été, `shade_memory` > 0,55) : le moteur pose des recrues là où
  il les tue ensuite.
- L'hypothèse « pose en hiver sous couronne nue » (constat 2) est écartée : pose en
  semaine 39.

## Décisions arrêtées (Nico, 2026-11-06)
- Q1 Critère de fin REFORMULÉ : chaque espèce ligneuse se remplace au moins une
  fois par génération (taux de remplacement ≥ 1) ; sous le parent pour les
  sciaphiles (banque de semis), en trouée ou au loin pour les héliophiles ; sans
  fourré. (Le « une pousse auprès du parent, de son vivant » est faux pour un
  héliophile.)
- Q2 Périmètre : A (banque de semis : un petit ligneux supporte une ombre plus
  profonde, stagne au lieu de mourir, repart à la trouée) + C (pose cohérente :
  seuil de pose aligné sur la tolérance, rayon de dispersion par espèce) dans CE
  sprint. B (dispersion animale) = sprint suivant, via D42.
- Q3 Figuier : réalisme. Pas de graine fertile sans son pollinisateur
  (blastophage) → propagation par rejets de souche. Conçu pour d'autres climats :
  la fertilité dépend d'une condition climatique, pas d'un « non » codé en dur.

## Constats complémentaires (2026-11-06)
9. Golden : seul ligneux du smoke = Pommier (< 5 ans, ne se reproduit pas).
   Espion sur `shade_stress_damage` pendant `tests.test_golden` : 104 évaluations,
   3 fois `shade_memory` > 0,55, 0 dégât [smoke, n=1 run, VM] → A golden NEUTRE
   attendu (le tirage `_hash_noise` est sans état).
10. `growth_factor` (lumière intégrée) règle la vitesse de `grow_plant` → un semis
   ombragé pousse lentement et repart quand la lumière revient : la reprise à la
   trouée existe déjà, il manque seulement la survie.
11. `sim/clonal.py` a déjà le mode `drageon` (framboisier, portée 40 cm, gate
   lumière au sol 0,30). `_mature()` y lit le dernier stade : un arbre (un seul
   stade « arbre ») serait « mûr » dès sa naissance → pour un arbre (`age_curve`),
   lire `maturity_years`. Framboisier sans `age_curve` → inchangé.
12. Climat = constantes de module `sim/weather.py` (T_MOY 11 °C, T_AMP 7 °C →
   mois le plus froid ≈ 4 °C). Pas de climat paramétrable aujourd'hui.

## Conception FIGÉE (OK Nico 2026-11-06)
Doc : `docs/vegetal/regeneration/conception_releve_ligneuse.md`. Golden
`a10b7225…` INCHANGÉ attendu sur les 5 tronçons.

| # | kickoff | état |
|---|---|---|
| ① | `01_banque_de_semis.md` — seuil d'ombre d'un ligneux monte avec la petitesse (`seuil_ombre`), signe `ombre` aligné | **fait** (golden `a10b7225…` intact) |
| ② | `02_pose_coherente.md` — arbre : rayon de chute = couronne, seuil de pose = survie d'un semis | **fait** (golden `a10b7225…` intact) |
| ③ | `03_figuier_realiste.md` — graine fertile si climat du blastophage, rejets `drageon`, `_mature` d'arbre, voix | à faire |
| ④ | `04_mesure_releve.md` — `tools/diag_releve.py`, verger_mur 200 ans, perf `full`, calibrage borné | à faire |
| ⑤ | `05_vue_godot.md` — voix `attente` du semis, rejets visibles, `dotnet build`, F5 | à faire |

## Tronçon 1 — fait (2026-11-06)
- `sim/effects/perturbations.py` : `H_GAULE` 200 cm, `SEUIL_SEMIS` 0,75,
  `seuil_ombre(plant)` (herbacée 0,55 ; ligneux : 0,75 → 0,55 linéaire en la
  hauteur `height_at`) ; `shade_stress_damage` l'utilise (seuil + sévérité).
- `sim/semiologie.py` : signe `ombre` rampe de `seuil_ombre(plant)` à 1.
- Test neuf `tests/test_banque_semis.py` (a/b/c verts). Contre-factuel : avec
  l'ancien seuil 0,55 le pommier à lumière 0,35 meurt S153 ; avec `seuil_ombre`
  il vit 5 ans.
- **Point pour le ④** [labo, lumière imposée, n=1 run, VM] : à lumière 0,35 le
  semis POUSSE (~28 cm/an, `growth_factor`) ; `shade_memory` d'été plafonne à 0,64
  et le seuil le rejoint vers ~130 cm (an 5, vitalité 0,20 en fin d'an 5) → à
  0,35 constant la banque est un SURSIS (~6 ans), pas une attente indéfinie.
  L'ombre fait donc pousser le semis jusqu'à sa propre mort : à trancher au
  calibrage (`H_GAULE`, ou croissance freinée sous ombre).
- La dormance hivernale fait redescendre `shade_memory` (−0,05/sem,
  `mortalite.py`) : le test lit le MAX de saison, pas l'état final.
- Golden `a10b7225…` inchangé ; `test_stress_chronique`, `test_signes`,
  `test_signes_legende`, `test_plasticite` verts. C# non concerné.

## Tronçon 2 — fait (2026-11-06)
- `sim/engine/mortalite.py` `_reproduction` bloc 3 : arbre (`age_curve`) → rayon
  de recherche `int(canopy_radius_at(parent) // 50) + 1` plots, seuil de pose
  `1 − SEUIL_SEMIS` (0,25, import `sim.effects.perturbations`, couche sim→sim OK) ;
  non-arbre inchangé (`radius_plots`, 0,35). Plot le plus lumineux conservé
  (commenté). Banque-sol et anémochorie non touchées.
- `tests/test_banque_semis.py` (d) recrue à 350 cm sous une couronne imposée de
  400 cm (hors de l'ancien rayon 150 cm + 1 plot → contre-factuel : 0 recrue avant) ;
  (e) tuile à lumière < 0,25 → 0 recrue.
- `canopy_radius_at` vérifié en cm, non nul : pommier labo 70 cm de 1 à 5 ans,
  100 cm à 6 ans, 112 cm à 7 ans [labo, n=1 run, VM].
- **Point pour le ④** : un fruitier à peine mûr (couronne ~70 cm → rayon 2 plots)
  sème désormais PLUS PRÈS (2 plots) qu'avant (4 plots), et sous un seuil plus BAS
  (0,25 < 0,35) : la recrue naît sous la couronne, en banque de semis (①). C'est
  la conception ; à mesurer au ④ (taux de remplacement, fourré éventuel).
- Golden `a10b7225…` inchangé ; `test_banque_semis` (a-e), `test_evenements`,
  `test_maitrise_detection`, `test_stress_chronique`, `bancs.test_verger_mur` verts.
  C# non concerné.

## §REPRISE
Exécution : `/sprint-auto sprint_releve_ligneuse`. Prochain tronçon = le premier
« à faire » du tableau (③ `03_figuier_realiste.md` au 2026-11-06). Chaque tronçon met à jour sa ligne + un § « Tronçon N — fait ».
