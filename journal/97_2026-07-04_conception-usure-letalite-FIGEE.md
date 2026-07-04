# 2026-07-04 — Conception USURE, PAS PUNITION (D64 reframé) — FIGÉE

`/conception` sur D64 (« une plante saine meurt en un tick »). **Phase A =
enquête terrain, pas spéculation.** Repro instrumenté du banc `grimpantes`
(seed 42).

## Diagnostic D64 RÉFUTÉ
La dette accusait « herbivorie létale + mortalité de fond ». Faux : à la densité
observée (ravageur ≈ 0,012), `herbivory_pressure` calcule `pressure = 0,012 ×
0,20 = 0,0024 < seuil 0,005` → **l'herbivorie ne tire jamais**. La vraie cause est
le **système de conflit spatial** (`_resoudre_conflits`/`detect_conflicts`/
`regress`) :
- une même paire (Tournesol↔Haricot) génère **deux** `ConflictNotification`
  (un `foliar`, un `root`) résolus **séparément dans le même tick** → **double
  régression** jeune→semis→mort (mesuré w11→w12) ;
- `regress()` est **létal** au stade 0 (`health=0`) → une seule relation tue une
  plante saine (viole philo #1/#2/#6) ;
- `loser()` = le plus jeune par `age_weeks`, remis à 0 à la montée de stade →
  **grandir te désigne perdant** (rétroaction perverse).

## Ancrage : le code violait une conception DÉJÀ figée
`CONCEPTION_COMPETITION_INTRAPLOT.md` (Q3, 2026-06-13) avait tranché : « la mort du
perdant **émerge** du déclin de santé — **jamais** de mortalité verdict », et
décrivait `detect_conflicts` comme informatif. `_resoudre_conflits` faisait
l'inverse. Le sprint **aligne le code**, il n'invente pas.

## Mesure (regress-kill neutralisé, 1 an)
Le tournesol (le plus haut) survit ; le haricot (dominé) accumule `shade_memory`
0,07→0,69 (> seuil 0,6) et décline lentement (santé 3→2 à w52) → **dépérissement
émergent par ombrage** = la mort de Q3. **Aucun zombie** → §2.3 (densité
co-occupants) **inutile** (sa condition : « seulement si embouteillage »).

## Décisions figées (Nico, AskUserQuestion)
- **Modèle C (hybride)** : conflit = notification, résolution non-létale ; mort
  émergente (ombre/racines/sénescence).
- **Cap de létalité chronique** : voies de fond {herbivorie, mortalité de fond,
  stress hydrique, ombre, maladie fongique} bornées à **−1 santé/tick** ; aigu
  (fonte/gel/grêle/vent) exempt. Santé **0-3 conservée**.
- **Séquencement** : ce sprint borné D'ABORD ; la **luxuriance** ensuite.

## Livrables
`docs/conception/CONCEPTION_USURE_LETALITE.md` + `sprints/sprint_usure_letalite/`
(00_etat + 01 conflit non-létal + 02 cap chronique + 03 vue Godot/F5). **3
tronçons**, golden : ① **re-figé** `a6c2f651…`→`a1c9c51f…` (mesuré), ② neutre
(re-figeage localisé pré-autorisé), ③ intact. Volet (b) D64 (lisibilité
auxiliaires) **subsumé par D60**. Vrai objectif « luxuriance par stratification »
extrait en **D65** (conception séparée : densification clonale + champ couverture
+ empilement visible + empreinte par espèce taille+silhouette). Prêt pour
`/sprint-auto sprint_usure_letalite`.
