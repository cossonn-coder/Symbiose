# Sprint VENT & ÉVAPOTRANSPIRATION (D37) — état partagé

> **État léger** (mis à jour en fin de chaque tronçon). Le **design figé** vit dans
> [`docs/conception/CONCEPTION_VENT_EVAPOTRANSPIRATION.md`](../../docs/conception/CONCEPTION_VENT_EVAPOTRANSPIRATION.md)
> — chaque kickoff `tN_*.md` y renvoie pour le détail. Repars à froid : lis ce
> fichier + le `tN_*.md` du tronçon courant + la/les §§ de conception citées.

## En une phrase
Introduire le **vent** comme facteur micro-climatique complet et **enrichir
l'évaporation** (rayonnement + vent) pour rééquilibrer la rosée → résout **D37**
(vent continu) et **D39** (`test_senescence` rouge : pommier asphyxié à 19,5 ans).
**Contrainte #1 = perf** (Nico : « peur que le moteur soit trop lent »).

## Décisions figées (Nico, 2026-06-29)
- Périmètre = **D37 complet** + tous les effets (thigmo, dégât étiolées, semis
  intérieur/extérieur, régimes nul/risées/venturi, vent↔nébulosité, pollinisation/
  dispersion, maladies fongiques, wind chill, transport litière/neige).
- Découpage **perf-first 8 tronçons** (⓪→⑦, §8 conception). ⓪→② débloquent D39 à
  coût ~nul ; ③ (abri spatial) = seul morceau cher, isolé/caché/mutualisé/reportable.
- **D32 intégré au tronçon ⓪** : optim scatter de la boucle lumière-sol, **mesurée
  ×6 plancher, golden-safe** (`tools/diag_light_coverage.py`). Verrou = test
  d'équivalence bit-à-bit.
- **Re-figeage golden LARGE assumé** dès ② (nébulosité dynamique + évaporation).
- « Arbres en drapeau » = hors périmètre (dette).

## Carte des tronçons
| # | Fichier | Coût | Golden | Statut |
|---|---------|------|--------|--------|
| ⓪ | [`t0_reference_perf_scatter.md`](t0_reference_perf_scatter.md) | mesure+gain | **INTACT** `11eceeb9…` | ✅ fait |
| ① | [`t1_vent_masse_air.md`](t1_vent_masse_air.md) | O(1) | **neutre** `11eceeb9…` | ✅ fait |
| ② | [`t2_evapotranspiration.md`](t2_evapotranspiration.md) | marginal | **re-fige LARGE** → D39 vert | ⏳ |
| ③ | [`t3_abri_spatial.md`](t3_abri_spatial.md) | **À BUDGÉTER** | re-fige | ⏳ |
| ④ | [`t4_thigmomorphogenese.md`](t4_thigmomorphogenese.md) | négligeable | re-fige | ⏳ |
| ⑤ | [`t5_pollinisation_dispersion.md`](t5_pollinisation_dispersion.md) | négligeable | re-fige | ⏳ |
| ⑥ | [`t6_maladies_fongiques.md`](t6_maladies_fongiques.md) | négligeable | re-fige | ⏳ |
| ⑦ | [`t7_transport_voix.md`](t7_transport_voix.md) | amorti | re-fige | ⏳ |

## Référence perf + scatter (tronçon ⓪, 2026-06-29 — D32 SOLDÉE)
- **Base mesurée** (`tools/profile_tick.py`, monde smoke 2 tuiles/96 plots/51
  plantes, 52 sem échauffement) AVANT : tick **59.2 ms**, `LightField.compute`
  **34.1 ms** (57.6 %). APRÈS scatter : tick **52.3 ms**, `compute` **25.8 ms**
  (49.4 %). Boucle lumière-sol seule : **×6.0 plancher** (`diag_light_coverage`,
  monde dense 79 % ombré = pire cas ; le monde réel 1600 plots est ~20× plus
  clairsemé → gain réel >> ×6).
- **Golden INTACT** `11eceeb9e80aec108dd46907c7e530e96d6040b486150944c4090c1c90b11ba0`
  (optim pure, bit-à-bit). Verrou : `tests/test_scatter_lumiere_sol.py` (PASS).
  Non-régression : `test_phototropisme`, `test_ombre_maison`, `test_sim_server`
  (207/207) verts.
- **Budget X fixé** : ce tronçon a **baissé** le tick (−12 %). Règle pour ①→⑦ :
  aucun tronçon n'ajoute plus de **~+10 %** au tick complet (≈ +5 ms sur la base
  52 ms) sans justification ; ③ (abri spatial) seul à risque → mesurer seul,
  réutiliser la même bbox/scatter que la lumière (levier 2, mutualisation).

## Masse d'air (tronçon ①, 2026-06-29 — golden NEUTRE)
- **Nouveau module `sim/wind.py`** (62 LDC pur), calqué sur `weather.py` : canaux
  décorrélés `K_WIND/K_DIR/K_GUST` en tranche 90_01x, zéro RNG vivant.
  - `wind_at(seed, week) → WindState(force, direction)` : force de fond (canal +
    saisonnalité hiver-venteux, opposée à `temp_norm`), écrasée haute par
    Tempête/Orage (continuise le dégât ponctuel) ; **direction O(1)** (somme de 3
    sinusoïdes basse fréquence — PAS de marche cumulée O(week), évite ~4 ms/tick
    en fin de partie).
  - `gust_profile` (§2.2 régimes intra-jour, enveloppe SUBTICKS=4 : risées + brise
    de fin de journée) ; `nebulosite_dynamique` (§2.3, le vent chasse la couverture
    figée) — **calculés, NON branchés** (le câblage aval = tronçon ②).
- **Golden INTACT** `11eceeb9e80aec108dd46907c7e530e96d6040b486150944c4090c1c90b11ba0`
  (module non lu par la boucle — vérifié par `test_vent.py::test_non_cable`).
  Non-régression : `test_sim_server` 207/207.
- **Test neuf** `tests/test_vent.py` (18/18) : déterminisme, bornes, saisonnalité
  hiver>été, réactivité Tempête, isolement golden-neutre.
- **Perf** : `wind_at` ~24 µs/call, **plat** quelle que soit la semaine (O(1)) →
  ~0.05 % d'un tick 52 ms même appelé chaque tick au ②. Budget +10 % très tenu.

## Boucle de travail (rappel CLAUDE.md)
Lancer `tN` → coder → **mesurer ms/tick avant/après** (budget §7B) → golden (intact
ou re-figeage annoncé) → MAJ ce fichier → commit → `/clear` → lancer `tN+1`.

## Clôture du sprint
- Rouvrir/MAJ **D39** dans `DETTE.md` (récidive via rosée, re-résolu par le fond).
- Solder **D37** + **D32** (scatter). MAJ `journal.md` (index) + entrée `journal/NN_…`.
- Supprimer `HANDOFF.md` (devenu obsolète).

## REPRISE (démarrage à froid)
« lis `sprints/sprint_vent_evapotranspiration/00_etat.md` puis
`t2_evapotranspiration.md` » → exécuter le tronçon ② (évapotranspiration enrichie
+ branchement de la nébulosité dynamique `sim/wind.py::nebulosite_dynamique` dans
`weather_state`, débloque D39) — **re-figeage golden LARGE attendu et annoncé**.
Penser à lire `sim/wind.py` (déjà écrit au ①, fonctions pures prêtes à câbler).
Tronçons ⓪ (réf perf + scatter D32) et ① (masse d'air `sim/wind.py`) = ✅ faits,
golden intact `11eceeb9…`.
