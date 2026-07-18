# 2026-07-18 — Sprint FLORAISON & FRUCTIFICATION (grappe D84 + D86) — CLOS

Sprint figé par `/conception` (journal 124), exécuté en 3 tronçons. Corrige la
floraison à contretemps/fugace (D84) et la fructification quasi nulle (D86) par un
**forçage thermique événementiel**, puis rend le tout observable au F5.

## ① Moteur floraison retypée (forçage thermique événementiel) — FAIT

`sim/engine/floraison.py` : `_tick_floraison` réécrit. La **double porte**
GDD-depuis-S1 + photopériode est remplacée par un **événement de durée bornée** :
`gdd_accum` armé au franchissement d'un seuil `bloom_forcing_gdd` BAS et par
saison-cible → `bloom_week` posé (1×/an), fenêtre `[bloom_week, +bloom_duration)`,
**porte photopériode SUPPRIMÉE** (c'est elle qui créait le recouvrement nul S34).
`FLORA_GENE_SHIFT` recalibré **200→20** (à seuils bas, 200 rendait un pied précoce
négatif). État neuf par-plante `bloom_week` (reset annuel, hors `_PLANT_ATTRS`).
Données espèce : `bloom_forcing_gdd`/`bloom_duration` par saison-cible (pommier 8/3
printemps, cerisier 12/3, figuier 40/4 été, tournesol 55/8, tomate 40/6, courgette
50/8, fraisier 10/4, violette 6/4 printemps précoce, armoise 180/5 automne jour-court
approximé). Patch pommier `gdd_floraison=130` RETIRÉ.

**Golden RE-FIGÉ MAÎTRISÉ** `3076c154…`→`f3239042…` : le DIGEST d'état final est
bit-identique, seules ~6 lignes de LOG diffèrent (proba herbivorie décalée de ~0.003
sur une bourse-à-pasteur déjà mourante — la floraison qui monte enfin active le champ
ressource pollinisateur, la vie macro ondule). `population_hash` re-figé aussi
(`papillon` seul, densité = nectar). Dérive 100 % floraison. Tests : `test_floraison_forcage`
NEUF 9/9, `test_desync_phenologie` 7/7, `test_fruits` 24/24.

## ② Nouaison calibrée (D86 secondaire) — FAIT

Démarche perf-first. Banc de mesure NEUF `bancs/mesure_nouaison.py` (hors registre)
qui lit la dose `pollen_recu` EXACTE d'un pommier mûr sous le monde full. Mesure : un
pommier bien visité intègre ~1.55 de pollen → `g(1.55)=0.44` avec `POLLEN_DEMI=2.0`,
sous la cible « belle floraison = beaucoup de fruits ». **Levier UNIQUE `POLLEN_DEMI`
2.0→1.0** (`sim/engine/decompo.py`) → `g(1.55)=0.61` (≥0.5), invariant sans plancher
intact (`g(0)=0`). Anémophilie inchangée (`ANEMO_DOSE_COEF=6.0≫1.0`). **Golden NEUTRE**
`f3239042…` (aucune fruitière ne noue dans le smoke). Butineurs NON touchés (0 agent en
floraison printanière = magnitude inutile).

## ③ Vue Godot + banc F5 — FAIT

Câblage vue déjà en place (désync ②③ du sprint DÉSYNC PHÉNOLOGIE) : `serialize.py`
exporte `floraison`, `PlantRenderer.Organs.cs` porte les fleurs sur `Floraison≥0.5`.
Vérifié INTACT après ①/② — aucun re-câblage.

- **Palettes C# (vue seule)** : 3 espèces devenues observables retombaient sur le
  défaut jaune → entrées ajoutées. `Palettes` : `Strawberry` (fleur blanche/fruit
  rouge), `SweetViolet` (fleur violette), `Mugwort` (capitules jaune-verdâtre ternes).
  `FlowerProfiles` : Strawberry/SweetViolet → Simple 5, Mugwort → Capitule 6. Autres
  silhouettes par famille déjà correctes.
- **Banc F5 NEUF `floraison_saisons`** (`bancs/biotique.py` §6, registré) : 1 tuile
  ensoleillée, pommier mûr (printemps + fruit) + violette (printemps précoce) +
  bourrache/tournesol (été) + armoise (automne). AUCUNE floraison pré-armée (≠
  `verger_floraison`) → placement saisonnier NATUREL. Pollinisateurs laissés ÉMERGENTS
  → **le décalage phénologique est exposé**. Banc isolé + anti-gel (patron `grimpantes`).
  Apparaît auto dans le sélecteur F5 (liste dynamique).
- **Diagnostic annuel NEUF `bancs/mesure_floraison.py`** (hors registre, sœur de
  `mesure_nouaison.py`) : imprime semaine par semaine la `floraison` de chaque espèce +
  la densité des 5 pollinisateurs → table de RECOUVREMENT, flag `*` sur les fenêtres
  « fleur ouverte mais butineurs < 0.05 ». Sortie confirmée : violette S15-18 + pommier
  S16-18 (butineurs ~0.00, `*`), bourrache/tournesol S22-31 (pic butineurs ~0.01),
  armoise S35-39 ; chaque floraison DURE 5-6 sem.

**Golden ③ INTACT** `f3239042…` (vue + bancs/diagnostics hors smoke/full = neutre).
`dotnet build Symbiose.csproj` VERT (0 err/0 warn). `test_biotique` 12/12.

## Décalage phénologique — remonté au ②, DÉCISION DESIGN réservée à Nico

La floraison printanière (pommier/violette S14-18) précède le pic d'activité
pollinisatrice (été S26-31) → recouvrement faible au printemps → nouaison entomophile
pénalisée en monoannuel (`test_sim_server::test_pommier_fruite` rouge, 0 fruit @S52).
Ni `POLLEN_DEMI` ni le débit butineurs n'y peuvent rien (0 agent × débit = 0).
**Non corrigé** (hors scope) — le banc `floraison_saisons` + `mesure_floraison.py`
l'EXPOSENT pour la décision : décaler la floraison printanière / réchauffer la porte
pollinisatrice de printemps / accepter la fructification pluriannuelle.

## État final

D84 + D86 → ✅ RÉSOLUS (reste F5 Nico + décision décalage). Golden `f3239042…`,
`population_hash` `ccd448bd…`. Non commité (Nico commit). Fichiers : `sim/engine/floraison.py`,
`plants/base/{instance,familles}.py`, `plants/perennials.py`, `plants/species/*`,
`sim/engine/decompo.py`, `bancs/{biotique,mesure_nouaison,mesure_floraison}.py`,
`bancs/__init__.py`, `tests/{golden_hash,population_hash}.txt`, `tests/test_floraison_forcage.py`,
`visuals/PlantRenderer.{Organs,Flower}.cs`. Points F5 : `sprints/sprint_floraison_fructification/00_etat.md §POINTS F5`.

## Post-scriptum — décalage phénologique TRANCHÉ (Nico, même jour)

Sur le décalage résiduel du §précédent, Nico tranche : **réchauffer la porte
d'activité des pollinisateurs, GLOBAL à toutes les guildes** (« au printemps ils
sont actifs, les pruniers/cerisiers sont butinés dès la sortie de l'hiver »).

**Diagnostic affiné (code + banc)** : la porte PHOTOPÉRIODIQUE des pollinisateurs
précoces est DÉJÀ ouverte au printemps — osmie « abeille des vergers »
(`daylen_min/full 10/12.5`) et bourdon (`9.5/12`) atteignent leur pleine
phénologie dès S13-14 (jour ≈ 13 h). Le vrai verrou est la porte THERMIQUE de
`PopulationField.tick` : `warmth = (temp−T_COLD_ZERO)/(T_WARM_FULL−T_COLD_ZERO)`
avec `6/24 °C` → au printemps frais (~7-8 °C) `warmth ≈ 0.08`, ce qui écrase la
`survie = phenology·warmth·…` **même** photopériode ouverte et fleurs présentes.

**Correctif** (`fields/population/constants.py`) : `T_COLD_ZERO 6→3 °C`,
`T_WARM_FULL 24→15 °C`. `warmth` sature désormais dès 15 °C → toute la faune est
pleinement active sur la belle saison fraîche. **Global** (choix Nico) : ne
concerne pas que les pollinisateurs — campagnol, limace, coccinelle, lombric…
voient aussi leur saison active élargie.

**Mesure** (banc `mesure_floraison`) : osmie/bourdon pendant la floraison du
pommier (S15-18) passent de `~0.001-0.002` à `0.002-0.006` (×2-3) ; la courbe
annuelle entière monte (été : syrphe `0.012→0.019`). En absolu la densité reste
modeste sur ce banc (petite tuile, moyenne sur plots vides — la densité LOCALE
aux plots fleuris est plus haute) → **magnitude à confirmer au F5**.

**Golden re-figé maîtrisé (autorisé par le choix explicite de Nico)** :
`golden_hash f3239042… → 57c166d8…` et `population_hash ccd448bd… → 5824ee3f…`
(faune plus dense → herbivorie modifiée, chaîne déterministe traçable au seul
changement des 2 constantes thermiques). Tests verts : fruits 24/24, floraison
9/9, desync 7/7, vent 54/54, population (invariants + hash).
