# Sprint FLORAISON & FRUCTIFICATION — état (carnet de bord /conception)

> Grappe **D84 (floraison à contretemps + fugace) + D86 (nouaison quasi nulle)**.
> Ouvert le 2026-07-18. Diagnostic-first. **PHASE A (challenge) en cours — rien
> n'est figé, pas de code moteur.** Préalable biologique à D87.

## Phase courante
**TRONÇONS ① ET ② IMPLÉMENTÉS le 2026-07-18** (floraison retypée + nouaison calibrée).
Reste ③ (vue Godot + banc F5). Voir §AVANCEMENT ①/② et §REPRISE.

> Historique : **FIGÉ (phase B) le 2026-07-18** — conception validée par Nico +
> 3 kickoffs autosuffisants. Aucune écriture moteur faite par la conception.

## AVANCEMENT ① — moteur floraison (forçage thermique événementiel) — FAIT

**Implémenté** (Python pur, pas de C#) :
- `plants/base/instance.py` : état neuf `bloom_week: int = -1` (semaine de
  franchissement, reset annuel), hors `_PLANT_ATTRS`.
- `plants/base/familles.py` : `gdd_floraison`/`bloom_daylen_min`/`bloom_daylen_max`
  RETIRÉS → `bloom_forcing_gdd: float = 60.0` + `bloom_duration: int = 6`.
- `sim/engine/floraison.py` : `_tick_floraison` réécrit (forçage ÉVÉNEMENTIEL :
  armement `bloom_week` au franchissement, fenêtre `[bloom_week, +bloom_duration)`,
  porte photopériode + `daylength` SUPPRIMÉES). **`FLORA_GENE_SHIFT` recalibré
  200 → 20** (à seuils bas, 200 rendait un pied précoce négatif). `T_BASE_FLORAISON`,
  montée/descente, `is_seed_bearing`, gène-tempo : conservés.
- `plants/perennials.py` : AppleTree patch `gdd_floraison=130` RETIRÉ → `bloom_forcing_gdd
  =8` / `duration=3` (printemps S14) ; CherryTree 12/3 ; Fig 40/4 (méditerranéen, été).
- `plants/species/*` : Sunflower 55/8, Tomato 40/6, Zucchini 50/8, Strawberry 10/4,
  Phacelia 38/6, Borage 45/7, Comfrey 50/8, SweetViolet 6/4 (printemps très précoce),
  Mugwort 180/5 (automne, jour-court approximé §2.5).
- `bancs/biotique.py` (`etalement_floraison`) : ADAPTÉ (référençait l'ancien modèle) —
  plants posés au stade mature + `ETAL_GDD_PRECHARGE 100 → 20` (juste sous le plus bas
  seuil) pour que le seuil par lignée redevienne la contrainte bindante → étalement OK.
- Tests : `test_desync_phenologie` adapté (`gdd_floraison`→`bloom_forcing_gdd`, comm.
  SHIFT 200→20) ; **test neuf `tests/test_floraison_forcage.py`** (placement/étalement/
  neutralité, 9/9).

**Décisions de calibrage retenues** : voir table ci-dessus. Placement vérifié sous la
météo réelle : pommier arme **S14** (printemps), tournesol **S22** (été), armoise **S34**
(automne). Étalement cohorte σ>0, neutralité g=1 exacte.

### Golden — RE-FIGÉ MAÎTRISÉ ×2 (cause floraison UNIQUE, confirmée par diff)
- **`tests/golden_hash.txt`** : `3076c154…` → **`f3239042ed405102a2369245adbbc4a3f3dec216a7e9fc5ac01861ffa539da1a`**.
  Cause : le **DIGEST d'état final est bit-identique** ; seules **6 lignes de LOG**
  diffèrent — un décalage de ~0.003 de la proba `herbivorie p=` sur une Bourse-à-pasteur
  déjà mourante. Chaîne : la floraison monte désormais réellement (le fix) → le champ
  ressource pollinisateur `Σ(floraison×préférence)` (nul avant car rien ne fleurissait)
  s'active → la vie macro ondule → proba campagnol décalée. AUCUN fruit ne noue dans le
  smoke (litière `fruit`=0). Dérive 100 % floraison, état inchangé.
- **`tests/population_hash.txt`** : `8f27b6b2…` → **`ccd448bd3d7cc6018e563cf0f08c95351db9af47ce6f9e358be7a34acc59cd03`**.
  Cause : golden de CHAMP des densités macro ; diff par-guilde = **`papillon` seul**
  (−0.018), tous les autres guildes bit-identiques. Densité papillon = nectar =
  `Σ(floraison×préférence)` → décalage de timing floral. Dérive 100 % floraison.

### Tests ciblés — état
VERTS : `test_golden` (re-figé), `test_population` (re-figé), `test_desync_phenologie`
(7/7), `test_fruits` (24/24), `test_floraison_forcage` (9/9, NEUF), `bancs.test_biotique`
(12/12, étalement réparé), + sweep complet de la suite (croissance, vigueur, senescence,
catalogue, encyclopédie, vent, ruche, marais, mycelium… tous verts).
**test_epaisseur_500ans NON lancé** (interdit).

ROUGE — `test_sim_server::test_pommier_fruite` : le pommier « full » noue **0 fruit @ S52**
(baseline : 1 fruit @ S38). **Attendu et documenté** : la floraison pommier est replacée
au PRINTEMPS (S14) ; l'entomophilie SANS PLANCHER (philo #2) ne noue pas faute de
pollinisateurs assez denses si tôt → c'est **exactement la D86-secondaire (dose nouaison)
que le tronçon ② doit calibrer** (`POLLEN_DEMI`/débit butineurs). Le kickoff ① interdit de
toucher la nouaison. NON corrigé ici — à résoudre au ②.
> `test_sim_server` porte aussi **3 échecs PRÉ-EXISTANTS** sans rapport (attend
> `engine_version 0.5.28`, le code est déjà `0.5.30` — dette de test d'un sprint
> antérieur, non touchée).

## AVANCEMENT ② — nouaison calibrée (D86 secondaire) — FAIT

**Démarche perf-first : MESURE puis tuning du levier le plus simple.**

- **Banc de mesure NEUF** `data/code/bancs/mesure_nouaison.py` (hors golden, hors
  registre `BANCS[]` — script diagnostic exécutable, sœur de `tools/diag_population.py`).
  Monde `full` (seed 42, mêmes tuiles/faune/pré-vieillissement que le serveur),
  enveloppe READ-ONLY de `_tick_fruits` pour lire la dose `pollen_recu` EXACTE vue par
  la nouaison + densités des 5 types de pollinisateurs sur la tuile du pommier.
- **Ce que le banc a mesuré** (pommier verger, `insect`, 1 organ_site) :
  1. **Magnitude** — un pommier BIEN VISITÉ intègre **~1.55 de pollen** sur sa
     floraison → `g(1.55)=0.437` avec `POLLEN_DEMI=2.0` → **sous** la cible « belle
     floraison = beaucoup de fruits » (frac≥0.5). ← **le levier ②**.
  2. **Timing (HORS scope ②, à signaler)** — la floraison pommier est replacée en
     PRINTEMPS PRÉCOCE (S12-16, ①) alors que la population de pollinisateurs, gâtée
     par `warmth` (T_COLD_ZERO=6 °C) + nectar, ne culmine qu'en été (pic ~0.20 à
     S26-31 vs **~0.01-0.05 à la floraison**). Le dépôt pendant la fenêtre florale est
     donc **~0** (n_agents≈round(0.02×n_max)=0) ; le pollen n'arrive qu'à S18, APRÈS
     la nouaison. → cause profonde du « aucune / une seule pomme » = **désaccord
     phénologie florale ↔ activité pollinisatrice**, PAS la dose. Ni `POLLEN_DEMI` ni
     le débit butineurs n'y peuvent rien (0 agent × débit = 0).
  3. **1 organ_site** sur l'arbre de démo → plafond structurel de 1 fruit (artefact de
     structure, hors scope).
- **Levier retenu = `POLLEN_DEMI` 2.0 → 1.0** (`sim/engine/decompo.py`), levier UNIQUE
  et le plus simple. `g(1.55)=0.61` (≥0.5) : un arbre bien visité noue une fraction
  significative. Invariant intact (`g(0)=0`, sans plancher). Débit butineurs NON touché
  (0 agent en floraison = magnitude inutile ; risque golden population évité). La rampe
  Monod est partagée par `wind` (anémophilie) : `ANEMO_DOSE_COEF=6.0 ≫ 1.0` → toujours
  ≈plein (comm. anemophilie.py:38 mis à jour).
- **Effet net** : en régime établi (pollen reporté d'une année sur l'autre), le verger
  noue **1 fruit** (round(0.61×1) = 1) au lieu de **0** (round(0.437×1) = 0).

### Golden ② — INCHANGÉ (neutre)
- `tests/golden_hash.txt` **INCHANGÉ** = `f3239042ed405102a2369245adbbc4a3f3dec216a7e9fc5ac01861ffa539da1a`
  (celui de ①). `POLLEN_DEMI` n'est lu QUE par `frac_nouaison`, appelée uniquement
  quand une fruitière mûre noue — or **aucune** ne noue dans le smoke (2 tuiles × 4 ans,
  litière `fruit`=0). Neutre, comme prévu au kickoff.
- `tests/population_hash.txt` **INCHANGÉ** = `ccd448bd…` (butineurs non touchés).

### Tests ciblés ② — état
VERTS : `test_golden` (inchangé), `test_population` (inchangé), `test_fruits` (24/24 —
`pollen=100` donne toujours `g=0.99`≈plein, `pollen=0`→0 : sémantique conservée, AUCUNE
valeur de dose à ajuster), `test_vent` (54/54, anémophilie), `test_ruche` (20/20),
`test_desync_phenologie` (7/7), `test_floraison_forcage` (9/9).
**test_epaisseur_500ans NON lancé** (interdit).

> `test_sim_server::test_pommier_fruite` reste ROUGE (0 fruit @ S52) : il ne déroule
> qu'**un an** → tombe sur la fenêtre de timing où le pollen n'est pas encore arrivé.
> Le levier ② corrige la MAGNITUDE, pas le TIMING phénologie↔pollinisateurs → **décision
> design attendue de Nico** (cf. point ②-2 ci-dessus : décaler légèrement la floraison
> pommier, ou réchauffer la porte pollinisatrice de printemps, ou accepter la
> fructification en régime pluriannuel). HORS scope du calibrage ②.

## Carte des tronçons
- **① `01_moteur_floraison.md`** — forçage thermique événementiel (retype
  `floraison.py`, données espèces, retrait patch pommier 130 + porte photopériode,
  recalibrage `FLORA_GENE_SHIFT`, état `bloom_week`). Golden re-figé maîtrisé SI
  fruitier mûr noue dans le smoke, sinon neutre.
- **② `02_nouaison_calibrage.md`** — dose nouaison (mesure puis tuning
  `POLLEN_DEMI`/débit butineurs, invariant « sans plancher »).
- **③ `03_vue_godot_banc.md`** — vue déjà branchée (désync ②③) : palettes fleur +
  banc F5 floraison→pollinisation→nouaison→fruit. Golden intact.

## Diagnostic CONFIRMÉ (empirique, sonde GDD/photopériode + lecture code)

Modèle actuel de floraison (`sim/engine/floraison.py`) = **DOUBLE PORTE** :
1. Forçage thermique : `gdd_accum` cumule `max(0, T−6 °C)` chaque semaine, **remis
   à 0 à la semaine 1**. Porte ouverte quand `gdd_accum ≥ gdd_eff`
   (`gdd_eff = gdd_floraison − FLORA_GENE_SHIFT·(g−1)`, `FLORA_GENE_SHIFT=200`).
2. Photopériode : `daylength(wiy) ∈ [bloom_daylen_min, max]` (défaut **[13.5, 16.5] h**).
+ garde de maturité (`is_seed_bearing`).
`floraison ∈[0,1]` RELAXE vers 1 si les 2 portes ouvertes (montée 0.35/tick),
vers 0 sinon (descente 0.50/tick). La vue C# dessine les fleurs sur
`floraison ≥ 0.5` (désync ③, plus de proxy saisonnier).

**Sonde annuelle sous la météo du jeu** (T_MOY=11, T_AMP=7, pic S30 ; solstice
S25) :
| grandeur | fait |
|---|---|
| Fenêtre photopériode [13.5–16.5 h] | ouverte **S16 → S34** (jour ≥ 13.5 h) |
| GDD cumulé franchit **130** (pommier) | **S29** |
| GDD cumulé franchit **200** (DÉFAUT, toutes les autres espèces) | **S35** |

### Cause racine
- **Le cumul GDD-depuis-S1 place toute floraison en fin d'été / automne.** Le
  printemps (S11–S18) n'a quasi aucun degré-jour (T franchit 6 °C seulement ~S11,
  montée lente). Un arbre à floraison PRINTANIÈRE (pommier, cerisier : avril-mai
  = S14–18 dans la vraie vie) est structurellement impossible : le modèle n'a
  **aucun mécanisme de floraison de printemps**.
- **D84 pommier « début automne » ✅** : `gdd_floraison=130` (déjà rabaissé à la
  main de 200→130 au sprint thermique !) franchi **S29** → fleurit **S29–34 =
  début automne** (automne = S27+). Le patch 130 n'a fait que le sortir du « zéro
  floraison » sans corriger le placement.
- **D86 « aucun fruit sauf une pomme » ✅** : **toutes les espèces sauf le
  pommier** gardent `gdd_floraison=200` (défaut) → GDD franchi **S35** alors que
  la photopériode **ferme S34** → **recouvrement = 0 semaine** → `floraison`
  **ne monte JAMAIS** → jamais de nouaison → **aucun fruit**. Seul le pommier
  (patché 130) fleurit → seule espèce qui fructifie. D'où « une seule pomme ».
- **D84 fugacité « disparaissent aussitôt » ✅** : pour toute espèce dont le GDD
  franchit près du bord fermant (S33–34), le recouvrement est de **0–2 ticks** →
  `floraison` fait 1 pas de 0.35 (< SEUIL_FLEURI 0.5) puis redescend → **flash**
  jamais compté comme « fleuri ». Le pommier a ~5 semaines (S29–34) → seul à
  tenir.
- **Aggravant desync** : `FLORA_GENE_SHIFT=200` (sprint DÉSYNC) rend un pied
  précoce (g>1) plus tôt → étale la variance mais **ne corrige pas le placement**
  structurel (le pommier golden g≈1.199 → gdd_eff≈90 → S26, toujours fin d'été).
- **D86 secondaire (nouaison)** : même quand la floraison marche (pommier), le
  pommier est `insect` → `frac_nouaison = pollen/(pollen+2)` sans plancher. Si la
  densité butineurs est faible dans la démo → dose faible → peu de fruits. À
  distinguer de la cause structurelle.

### « Semaine 6-7 » RÉSOLU (Nico 2026-07-18)
Comptées **depuis le début de l'automne** → `wiy` **S33-34**. = exactement le
**bord fermant** de la fenêtre photopériode (ferme S34). Les « espèces du sud »
(seuil défaut 200, franchi S35) attrapent **0-1 tick** de recouvrement juste
avant fermeture → le **flash fugace**. Pommier (S29-34) et espèces du sud
(S33-34) = **le même empilement d'automne**. Diagnostic entièrement cohérent, plus
aucune pièce manquante.

## ARBITRAGES TRANCHÉS (Nico 2026-07-18)
- **Direction = B — Typage phénologique par espèce.** Chaque espèce porte une
  **saison-cible** de floraison ; `floraison` = **cloche** autour de la cible ;
  le GDD n'est plus la porte primaire ; le gène-tempo `phenologie_florale`
  décale l'individu DANS la fenêtre (désync conservée). (A recalibrage et C
  chill+forçage écartés.)
- **Nouaison (D86 secondaire) = OUI, dans ce sprint** (calibrage dose
  butineurs / `POLLEN_DEMI` une fois la floraison replacée).

## Modèle B — FORÇAGE THERMIQUE ÉVÉNEMENTIEL (raffiné Nico 2026-07-18, ARBITRÉ)
Nico précise : chaleur = **variation continue** (météo+ensoleillement) qui **avance
la DATE** de floraison (année chaude → précoce) ; désync par gène ; biologiquement
juste. → on GARDE `gdd_accum` (signal thermique continu) et on l'utilise comme
**déclencheur événementiel** ; on SUPPRIME la porte photopériode dure.
Remplacer la double-porte de `_tick_floraison` par, PAR plante vivante :
```
si wiy == 1:  gdd_accum = 0 ;  bloom_week = −1        # reset annuel
gdd_accum += max(0, temp_locale − T_BASE)            # temp.at_plot(r,c) : météo + ombre/ensoleillement
gdd_eff = bloom_forcing_gdd(espèce) − FLORA_GENE_SHIFT·(g − 1)   # seuil individuel (g>1 → précoce)
si bloom_week < 0 et is_seed_bearing(plant) et gdd_accum ≥ gdd_eff:
    bloom_week = wiy                                  # FRANCHISSEMENT → armement (1×/an)
en_fleur = (0 ≤ bloom_week) et (wiy < bloom_week + bloom_duration(espèce))
cible = 1.0 si en_fleur sinon 0.0
floraison += (cible − floraison)·(MONTEE si cible>flor sinon DESCENTE)
```
- **Deux corrections clés vs aujourd'hui** : (1) floraison = **événement de durée
  bornée** (armé au *franchissement*, fane après `bloom_duration` sem) → plus de
  fugacité, plus de floraison éternelle ; (2) **seuils `bloom_forcing_gdd` BAS et
  par saison-cible** (pommier/cerisier printemps, tomate/tournesol été, aster/
  lierre automne) + **porte photopériode SUPPRIMÉE** (c'est elle qui créait le
  recouvrement nul S34).
- **Données espèce neuves** : `bloom_forcing_gdd` (seuil de forçage, bas→printemps
  … haut→automne) + `bloom_duration` (**fixe en semaines par espèce** — Nico
  2026-07-18 ; pommier ~3 sem, tournesol long). État neuf par-plante :
  `bloom_week` (petit int, reset annuel). `gdd_accum` **conservé** (déjà là).
- **Calibrages actés** : pommier = **printemps** → **annuler le patch
  `gdd_floraison=130`** (perennials.py:197-207) au profit d'un seuil de forçage
  bas. `FLORA_GENE_SHIFT` **recalibré à la baisse** (~15-30 ; 200 face à des seuils
  bas rendrait un pied précoce négatif) → ±1-2 sem à ±σ.
- **Limite assumée** : fleurisseurs de **jours courts** (aster, lierre) approximés
  par « seuil élevé → franchi en automne » (résultat juste, mécanisme non
  photopériodique). Second type jour-court = extension future si demandé, pas
  maintenant (un seul mécanisme = simplicité).
- Gène-tempo, garde de maturité, relaxation montée/descente : **conservés**.
  Clones (gène copié) synchrones, semis étalés : conservé. Ombre maison →
  accumulation plus lente → floraison plus tardive à l'ombre : interconnexion
  gratuite (règle « tout coexiste »).

## Découpage pressenti (À FIGER en phase B seulement — 3 tronçons)
1. **① Moteur floraison retypée** — `sim/engine/floraison.py` + données espèces
   (`plants/base/familles.py` défauts + `perennials.py`/`species/*` cibles) +
   `sim/semiologie.py` si un signe reflète la floraison. Retirer `gdd_accum`.
   Tests : placement (chaque espèce fleurit dans SA saison) + étalement (σ>0 via
   gène) + neutralité g=1 hors placement. **Golden re-figé maîtrisé SI un fruitier
   mûr fleurit/noue dans le smoke** (→ litière `fruit`→eco hachés) ; sinon NEUTRE
   — à confirmer à l'implémentation, annoncé dans le kickoff.
2. **② Nouaison calibrée** — `sim/engine/decompo.py` (`_tick_fruits`,
   `frac_nouaison`, `POLLEN_DEMI`) + `sim/reproduction.py` (dose butineurs) :
   mesurer `pollen_recu` d'un pommier mûr sur floraison SAINE, tuner pour une
   nouaison significative **sans plancher** (0 pollinisateur → 0 fruit). Golden
   selon fruits dans le smoke.
3. **③ Vue Godot + banc F5** (règle projet : vue = dernier tronçon) — le scalaire
   `floraison` est DÉJÀ exporté (désync ②) et lu par la vue (désync ③, fleurs sur
   `Floraison≥0.5`) → sans doute AUCUN changement de rendu, seulement : vérifier
   palettes de fleur printemps/été/automne, banc d'observation
   floraison→pollinisation→nouaison→fruit sur l'année, F5 Nico. Golden intact.

## §REPRISE
**Tronçons ① ET ② FAITS** (non commités — Nico commit). Prochaine action = **tronçon ③
`03_vue_godot_banc.md`** (vue Godot + banc F5, dernier tronçon, golden intact).

État ② : `POLLEN_DEMI` calibré 2.0→1.0 (`sim/engine/decompo.py`), banc de mesure
`bancs/mesure_nouaison.py` posé, golden + population INCHANGÉS, tous les tests ciblés
verts. Symptôme résiduel documenté : `test_sim_server::test_pommier_fruite` reste rouge
car il est monoannuel et heurte le **désaccord de timing phénologie florale (printemps
précoce) ↔ activité pollinisatrice (été)** — HORS scope ②, **décision design attendue
de Nico** (voir §AVANCEMENT ② point 2 + encart `test_pommier_fruite`).

Pour reprendre ③ : `03_vue_godot_banc.md` + `PlantRenderer.Organs.cs` (fleurs sur
`Floraison ≥ 0.5`, déjà branché) + palettes fleur printemps/été/automne + banc
d'observation F5 floraison→pollinisation→nouaison→fruit.
