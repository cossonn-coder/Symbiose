## 2026-06-29 — Sprint POMMIER NOUAISON — SPRINT TERMINÉ (investigation + correction)

**Objet.** Réparer un **check rouge stable** de la suite du pont :
`test_sim_server` était `205/206`, la rouge = *« le pommier pré-âgé a noué des
fruits réels (fin de floraison) — 0 fruits @ S52 »*
(`tests/simserver/morts.py::test_pommier_fruite`). La config **full** pré-vieillit
le pommier à `maturity_years` pour qu'il fleurisse dès l'an 1 ; il ne nouait
**aucun fruit**. Bug **pré-existant**, dormant depuis le **sprint THERMIQUE
(2026-06-18)** — confirmé NI causé NI aggravé par les sprints suivants (déjà rouge
sur la baseline `f7811b5`).

**Diagnostic (investigation AVANT correction).** Instrumentation d'un run
`seed=42 config="full"` semaine par semaine (`age_years`, `gdd_accum`,
`floraison`, `a_fleuri`, `pollen_recu`). Verdict : la chaîne casse au **premier
maillon, la floraison** — le pré-âge (`age_years=5 ≥ maturity_years=5`) et les
butineurs (pollen reçu 2.85→5.1) sont SAINS. La `floraison` du pommier **plafonne
à 0.350** et ne franchit jamais `SEUIL_FLEURI=0.5` → `a_fleuri` jamais armé → la
nouaison (front descendant de fanaison) ne se déclenche pas.

**Cause racine.** La floraison est une **double porte** : chaleur
(`gdd_accum ≥ gdd_floraison=200`) ET photopériode (`bloom_daylen 13.5–16.5 h`,
fenêtre ouverte S16→S34). Sous la météo seed 42 **re-figée au sprint thermique**
(printemps refroidi), l'accumulation GDD est plus lente et ne franchit 200 qu'à la
**semaine 34** — **dernière** semaine de la fenêtre photopériode. Les deux portes
ne coïncident donc qu'**UNE seule semaine** → un seul pas de montée florale
(`FLORAISON_MONTEE=0.35`) puis fanaison → pic 0.35 < 0.5. Régression de
**calibration/timing** : avant la dérive météo, le GDD franchissait 200 au
*milieu* de la fenêtre (plusieurs semaines de chevauchement).

**Arbitrage (remonté à Nico, point de design signalé au kickoff).** Choix entre
calibrer un knob de floraison du pommier ou réécrire le test. **Nico a tranché :
calibration `gdd_floraison` 200→130** (sur AppleTree uniquement, pas le défaut
global). La porte chaleur s'ouvre alors ~S29 (milieu de fenêtre) → ~5 semaines de
chevauchement → la floraison monte à ~0.95 → nouaison entomophile normale, **1
fruit noué à S37**.

**Correctif.** `plants/perennials.py::AppleTree` : ajout `gdd_floraison = 130.0`
(override du défaut `familles.py = 200`), avec commentaire pédagogique expliquant
la dérive thermique et la neutralité golden. **Aucun autre fichier moteur touché.**

**Invariant golden — PRÉSERVÉ (pas de re-figeage).** Le golden (smoke, 2 tuiles ×
4 ans) n'amène aucun pommier à 5 ans → `is_seed_bearing=False` → `cible=0` →
`floraison` reste 0 quel que soit ce seuil. Neutralité **prouvée empiriquement** :
hash **inchangé** `11eceeb9e80aec108dd46907c7e530e96d6040b486150944c4090c1c90b11ba0`
avec et sans le correctif.

**Vérifications.** `test_sim_server` **207/207** (le check pommier passe + son
sous-check fruit-détail s'active désormais : `{segment, maturite, masse}`) ·
`test_golden` PASS (hash identique) · `test_fruits` 24/24 · `test_biennial` PASS ·
suite complète verte.

**Reste.** Rien côté moteur. Le pont n'a pas bougé (aucun bump). C# non concerné.
