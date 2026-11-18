# Sprint DÉPART DU JARDIN (D140 A+B+C) — état

> Conception FIGÉE le 2026-11-18 : `docs/vegetal/genetique/conception_depart_jardin.md`
> (à lire en entier). Hors périmètre : trèfle (D140 D, non mesuré — Nico), éclaboussures
> de pluie et Ctrl+molette des graines (D140 E-F).

## But
Un jardin qui démarre vivant et réaliste : pâturin anémophile et autogame, gènes muets
gratuits, limites de froid physiquement possibles, mort par froid consignée, monde `full`
ouvert mi-mai avec une plante mûre de chaque espèce, semis d'intérieur et repiquage.

## Décisions clés (Nico, 2026-11-18)
- A : pâturin = vent + autofécondation ≈ 0,9. B : caractère non exprimé (aucun lecteur
  pour l'espèce) = coût nul, gène porté et hérité.
- C : ouverture `full` en **semaine 10** (juste après les saints de glace) ; **au moins
  une plante MATURE de chaque espèce du catalogue**, arbres compris (âge = première
  fructification) ; garde-fou catalogue ⊂ `full` ; semis (existe) + graines déjà
  semées ; pot dans la maison (chaud, peu de lumière) + geste `repiquer` (choc de
  repiquage ∝ racines à l'étroit) ; repiquage différé = choix du joueur, l'automate
  repique quand les nuits passent au-dessus de la limite de froid.
- Gel impossible au-dessus de ≈ −0,5 °C ; tournesol non sensible au froid sans gel ;
  rythme du froid sans gel (`FROID_LESION_K`) inchangé.

## Faits vérifiés au code (2026-11-18)
- `full` = 15 espèces sur 52 ; départ via `BANC_WEEK_DEPART.get(config, 1)` (commands.py).
- 68 cultivées repiquées s1 mortes en 2 semaines [seed 42] ; nuits s1-s9 entre −2,8 et
  +5 °C, > 7 °C dès s10.
- `lim_gel` tomate +2,8 °C, basilic +1,2, poivron −4,4 (gène `rusticite_froid` de variété).
- Semis (`planter` → `GrainEnAttente` + `bell(T_sol)`) et pots (`deplacer_pot`) existent.

## Golden
Départ `db4d6b75…` → après ① **`98a050cf…`** (re-figé : divergence 100 % due à B —
A seul et la dérivation `_POLLEN_VIBRE_BOURDON` sont bit-identiques ; coût allégé dès s1
chez achillée, haricot, phacélie, pommier, tournesol, trèfle (gènes muets `pollen`,
`limite_froid`, `fixation_azote`, `allelopathie`) ; 1ʳᵉ divergence du log en s9 ;
`population_hash`/`vigueur_hash` intacts). ① **RE-FIGÉ annoncé** · ② **RE-FIGÉ → `25671775…`** (1ʳᵉ divergence s1 : la tomate du smoke ne gèle plus à une nuit > −0,5 °C — borne de la sève — et le tournesol n'a plus de lésion de froid sans gel ; σ_A des tendres bit-identique sur le smoke, chronique neutre) ·
③④⑤⑥ **INTACT**.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_paturin_genes_muets.md` — pâturin + gènes muets | **FAIT** 2026-11-18 (golden re-figé `98a050cf…`) |
| ② | `02_froid_tendres.md` — borne du gel, audit des tendres, chronique | **FAIT** 2026-11-18 (golden re-figé `25671775…`) |
| ③ | `03_monde_full_complet.md` — semaine 10, 52 espèces mûres, garde-fou, perf | **FAIT** 2026-11-18 (golden intact) |
| ④ | `04_semis_interieur_repiquer.md` — pot dans la maison + `repiquer` | à faire |
| ⑤ | `05_automate_repiquage.md` — repiquage différé par l'automate | à faire |
| ⑥ | `06_vue_banc.md` — palette, pots visibles, banc `depart_jardin`, clôture | à faire |

## Acquis du ①
- Registre `plants/caracteres.py` : champ `exprime` (prédicat sur la classe, None = toutes)
  + `couteux_exprimes(cls)` mémoïsé par espèce, lu par `cout_genetique`. Muets possibles :
  `nectar` (nectar d'espèce 0), `taille_fleur`/`guide_nectar` (ni nectar ni anthères
  poricides), `pollen` (ni vent ni poricide — la phacélie aussi !), `limite_froid`
  (`t_froid_lesion` None), `fixation_azote`, `allelopathie` (effets déclarés). Universels
  vérifiés au code : `rusticite_froid`, `limite_chaud`, `parfum` (ravageurs),
  `coriacite_feuille`, `mycorhization`.
- `FAMILLES_ANTHERES_PORICIDES` (caracteres.py) = source unique ; `registry._POLLEN_VIBRE_BOURDON`
  en dérive.
- Pâturin : `pollination_mode = "wind"`, autofécondation neutre 0,9 → fécondation ≥ 0,9.
- Test : `tests/test_genes_muets.py` (18/18).

## Acquis du ②
- `T_CONGELATION_SEVE = −0,5` (plants/base/instance.py) : `lim_gel` = min(borne, calcul) —
  point unique lu par dégâts (`reponse_thermique`), signes (`posture_thermique`) et pont.
- `SIGMA_GEL_TENDRE = 0,5` (caracteres.py) : σ_A de `rusticite_froid` surchargé
  (`genetique`) chez les 5 tendres sans endurcissement (tomate, poivron, basilic,
  haricot, courgette) → variétés entre ≈ −2,3 et −0,5 °C (poivron −4,4 → −2,1).
- Tournesol : `t_froid_lesion` None.
- Chronique : cause `froid` ajoutée à `CAUSE_DE_RAISON` ; la nuit froide (comme grêle,
  aléas, ravageurs) est loguée AVANT les en-têtes `[T0]` (boucle.py) → lignes sans
  tuile ; repli FIFO `(None, pos, espèce)` dans `chronique._appliquer` (log intact :
  il entre dans le golden). Vérifié monde `full` s1 : tomate/basilic → `froid`.
- Tests : `test_niche_thermique` [1b] (30/30), `test_chronique` (froid/gel sans en-tête).
- À noter : `brûlure (feuille échaudée)` tombe encore en `autre` (hors périmètre).

## Acquis du ③
- `sim/monde_complet.py` (neuf) : `SEMAINE_OUVERTURE = 10`, `AGE_ARBRES_DEMO` (déplacé de
  commands.py), table `PLACEMENTS` (45 plantes : 7 arbres + 38 herbacées, plots libres,
  niche par tuile), `SEMIS_OUVERTURE` (6 `GrainEnAttente` tuile S, dont haricot/courgette),
  `ouvrir_monde_complet(tiles, seed, semaine)`, `especes_matures(tiles)`.
  Herbacées : dernier stade + 1 an de squelette (lianes 3 ans, patron `planche_especes`) ;
  arbres : âge = max(11, `maturity_years`) (charme 11 → 15, chêne 25, hêtre 30, sapin 20,
  noyer 15). Pré-croissance prolongée de `semaine − 1` semaines (calendrier continu).
- `cmd_init` : `start_week` calculé AVANT la fabrique ; `full` ET `propre` (même monde,
  décidé) ouvrent en s10 ; `_pre_vieillir_ligneux` remplacé par `ouvrir_monde_complet`
  (logique déplacée, pas perdue). `main.py` et le smoke intouchés.
- Garde-fou : `tests/test_monde_full_complet.py` (7/7 ; « ajouter <espèce> au monde full »,
  vérifié en retirant le thym). `tests/simserver/base.py` : 91 → 136 plantes posées.
  `test_fleurs_lisiere` [5] : départ `week: 1` épinglé (son calendrier « mai-juin après
  15 pas » datait du départ s1). Suites `full` toutes vertes (test_sim_server 349/349).
- Vérifié : rien n'assume `week == 1` au 1er tick (chronique `_an` et `perf_annees`
  en semaines absolues ; 1ʳᵉ année de bilan = s10-s52, plus courte).
- Perf [3 paires alternées, charge VM 1,1-1,7 / 16 cœurs] : tick s10-s30 477 → 616 ms
  (+29 % [n=3, écart ±20 ms], juste sous le seuil de 30 %) ; init 1,3 → 3,8 s (×2,9 —
  pré-croissance des arbres de 15-30 ans). Vivants à s31 : 63 → 228.
- ⚠️ CONSTAT pour Nico (non corrigé, hors périmètre) : ouvrir en s10 provoque une
  HÉCATOMBE d'herbivorie dans les 6 premières semaines — DÉJÀ présente sur HEAD lancé
  à `week: 10` (91 plantes initiales → 16 vivantes à s16 ; aulnes, bouleau, charme
  morts « herbivorie »). Au départ s1 ils restent à vitalité 1,0. Cause mesurée :
  plantes neuves sans `stress_memory` (≈ 0,12-0,15 chez un arbre à s10 après un départ
  s1 ; gate `pressure > stress_memory·0,5`, perturbations.py) + auxiliaires à 0 à
  l'init (0,39 à s10 après un départ s1). Essai : amorcer `stress_memory` à la
  perturbation locale ne suffit pas (≈ 61/136 vs ≈ 40/136 à s17). Le chêne de 25 ans
  meurt d'herbivorie comme un semis (aucun effet de taille). Décision de design à
  trancher (amorcer la faune de saison ? la mémoire des plantes ? l'herbivorie selon
  la taille ?) — à verser en dette / conception, pas dans ce sprint sans accord.

## REPRISE
**SUSPENDU avant ④ (2026-11-18)** : hécatombe par herbivorie à l'ouverture, confirmée au F5 de Nico → DETTE.md D140 (G), CONÇU le 2026-11-18 : attendre la clôture de `sprints/vegetal/sante/sprint_plante_vivante/` puis `sprint_stress_au_bilan/` (les plantes vivent d'un bilan carbone, plus de PV — le choc de repiquage du ④ doit s'exprimer en feuillage/réserves, relire `docs/vegetal/sante/conception_plante_vivante.md`). Noms d'espèces en français → D141 (hors sprint).
Lire `CLAUDE.md`, ce fichier, puis le kickoff du premier tronçon « à faire » (④).
