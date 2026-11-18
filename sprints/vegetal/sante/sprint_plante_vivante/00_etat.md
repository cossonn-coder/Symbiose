# Sprint PLANTE VIVANTE (D140 G, sprint A) — état

> Conception FIGÉE le 2026-11-18 : `docs/vegetal/sante/conception_plante_vivante.md`
> (à lire en entier). Suite : `sprints/vegetal/sante/sprint_stress_au_bilan/` (B).
> Ce sprint débloque `sprints/vegetal/genetique/sprint_depart_jardin/` (reprise au ④).

## But
Les plantes n'ont plus de PV : elles vivent d'un bilan carbone (photosynthèse −
entretien − part racinaire), tiennent un `feuillage` et des `reserves`, meurent de
famine ou de destruction. Herbivorie par atteinte (la limace ne mange pas le
chêne), souches à réserve finie (fin de la cascade de rejets), ouverture du monde
`full` à mortalité partielle.

## Décisions clés (Nico, 2026-11-18)
- Règle de dégât actuelle aberrante → refonte des dégâts, des cibles de chaque
  ravageur et de leurs effets. Mesuré : la faune n'est pas en cause (pré-rouler
  la faune AGGRAVE : 130/136 morts vs 121).
- Plantes sans PV ; tout le vivant végétal passe au bilan (sprints A puis B).
- `vitalite` = lecture dérivée (réserves × feuillage) ; écrire 0 = destruction.
- Plus de mort ni de guérison au sort ; causes de mort : famine, destruction,
  défaillance hydraulique, racines perdues, fin de cycle, vieillesse (§5).
- Unité = semaine d'entretien ; 3 paramètres d'espèce neufs (`reserve_semaines`,
  `photo_max`, `cout_feuillage`) dans `plants/physiologie.py` ; tout le reste
  réutilisé (plage thermique D139, tolérances, gènes de feuille).
- Critère d'ouverture (`full`, seed 42, s10→s30) : 0 arbre posé mort ; ≤ 25 %
  d'herbacées posées mortes hors fin de cycle ; ≤ 4 rejets par arbre mort.

## Golden
Départ `25671775…` (fin du ③ de `sprint_depart_jardin`). ① **INTACT** ·
② **RE-FIGÉ annoncé** (modèle de vie) · ③ **RE-FIGÉ annoncé** (herbivorie seule,
preuve par neutralisation) · ④ intact attendu · ⑤ ⑥ **INTACT**.
Perf de référence à mesurer au ① (tick `full` s10-s30, commit de départ).

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_socle_bilan.md` — bilan en ombre + paramètres 52 espèces + banc | **FAIT** (golden intact, non commité) |
| ② | `02_bascule_vie.md` — vitalité dérivée, famine, `erode` = tissus | à faire |
| ③ | `03_herbivorie_atteinte.md` — chaque ravageur mange ce qu'il atteint | à faire |
| ④ | `04_souches_reserve.md` — réserve de souche, rejets sans souche propre | à faire |
| ⑤ | `05_ouverture_mesure.md` — critères `full` s10→s30 + âge de la chronique | à faire |
| ⑥ | `06_vue_banc.md` — pont, rendu du feuillage, info-bulle, banc, clôture | à faire |

## Acquis du ① (2026-11-18)
- `plants/physiologie.py` : 3 paramètres par forme de vie + `SURCHARGES` des 52 espèces
  (commentées), `capacite_reserve` = reserve_semaines × facteur_stade (0,05 → 1,
  linéaire sur l'index de stade ; sur `age_years/maturity_years` pour les arbres à
  stade perpétuel — l'index seul ne bougeait pas pour eux).
- `sim/bilan.py` (pur) appelé en fin de `_update_physiology` ; champs `feuillage`,
  `reserves`, `bilan_net` dans `PlantInstance` (hors `_PLANT_ATTRS`). Lus par personne.
- **Écarts à la conception (calibrage mesuré)** : (1) `f_T` côté chaud ferme de
  `lim_chaud` à `lim_brul`, pas à `lim_chaud` — `t_feuille` est le pic du jour le plus
  chaud, et la plupart des herbacées ont `lim_chaud` 28-30 °C sous un pic d'été
  ordinaire de 29-30 °C : un arrêt net éteignait leur production tout l'été ;
  (2) `LUM_SATURATION` 0,4 (sur `light_eff`) ; (3) sciaphile `photo_max` 2,5 (2,0
  laissait violette/lierre en déficit au nord de la maison). Optimum thermique =
  `temp_min_growth + 8 °C` (D139 n'a pas d'optimum explicite).
- Banc `tests/test_bilan.py` vert : niche d'été > 0 pour les 43 espèces de
  PLACEMENTS ; plantule sous ombre < 0 ; chêne adulte défolié en continu tient 20 sem
  (réserves 0,29) ; semis de chêne (C = 3,5 sem) vide en 2 sem ; défolié une fois →
  feuillage refait en 7 sem, réserves au plus bas 0,87 ; caduc en hiver ≤ 30 %.
- `bilan_net` monde `full` s18 [seed 42, n=1, herbivorie neutralisée en mémoire,
  `mesures/bilan_par_espece.py`] : négatifs **myrtille −0,46, menthe −0,19, saule
  −0,12** (ombre de la maison/du sapin : lumière effective < 0,2 — placements hors
  niche, **à surveiller au ⑤**) ; ble +0,05, violette +0,06, bambou +0,12, lierre
  +0,13, consoude +0,16, framboisier +0,25 ; tous les autres +0,3 à +2,6 (tournesol).
  Semaine de canicule s24 (T_air 24,9) : la plupart en négatif (−0,1 à −2), attendu.
- Perf tick `full` s10→s30 [3 paires alternées, charge 1-2] : 9,27 s → 9,29 s (bruit).
- Suites : tout vert sauf `test_peripherie` (70/71) et `test_population` — **déjà
  rouges au commit de départ** (vérifié sur un worktree HEAD), sans lien.
- À savoir pour ② : une plantule de vivace (C = 0,4 sem) dormant l'hiver dépense ~0,9
  sem → elle mourrait de famine dès le branchement ; le facteur de stade des herbacées
  ou `DORMANCE` (0,1) sera à revoir quand la vitalité lira les réserves.

## Diagnostic d'origine (2026-11-18, seed 42, n=1 par cas)
Ouverture s10 → morts des 136 posées à s21 : tel quel 121 ; faune pré-roulée 130 ;
prédateurs seuls pré-roulés 97 ; `stress_memory` amorcée 0,12 → 49. Semis de
chêne : vagues de rejets ×3 (9 → 27 → 75 → 153, s20-s32), toutes à < 1,5 m d'un
arbre mort. Scripts jetables : instrumenter `herbivory_pressure` et compter les
naissances par espèce/semaine via `SimServer().cmd_init({"config":"full","seed":42})`
puis `engine.tick_semaine()`.

## REPRISE
① fait (non commité au moment de l'écriture). Lire `CLAUDE.md`, ce fichier, la
conception, puis `02_bascule_vie.md`. Lancer : `/sprint-auto sprint_plante_vivante`.
