# Sprint CALENDRIER UNIQUE (D122) — état partagé

**Conception** : `docs/champs/climat/conception_calendrier_unique.md` (figée le 2026-10-30).
**Où on en est** : ① FAIT (banc + `mesures/avant.md`, golden intact) ; ② FAIT ; ③ FAIT
(② et ③ NON commités, à committer par l'orchestrateur) ; ④ à lancer.

## Décisions clés (Nico, 2026-10-30)

- **C1** L'année commence à l'**équinoxe de printemps** (wiy 1 ≈ 20 mars) : on décale le
  CLIMAT de 11 semaines (T min/HR max/vent wiy 4 → 45, solstice 25 → 14), on garde
  les étiquettes de saison (printemps 1-13 … hiver 40-52).
- **C2** Un seul calendrier en couche basse : `data/code/calendrier.py` (racine, zéro
  dépendance) ; `sim/engine/calendrier.py` le ré-exporte ; les copies locales le lisent.
- **C3** **Mesurer d'abord, recalibrer après** : banc de mesure figé avant, rejoué après.
- **C4** Soleil (déclinaison par saison) hors périmètre.
- **C5** (2026-10-30, après ②) Herbivorie printanière : **réveil THERMIQUE des ravageurs**
  (option 1, philo #2 — on agit sur la population, pas sur le seuil d'effet plante).
  Ajouté au kickoff ③ comme point 0.
- **C5bis** (2026-10-30, précision Nico pendant ③) : une mortalité PARTIELLE des semis est
  acceptable (génétique, météo, emplacement, ravageurs) — seule l'hécatombe systématique
  est refusée ; et « les ravageurs viennent quand il y a déjà des plantes pour les
  nourrir » → la population suit la ressource hôte avec un délai de colonisation, en plus
  de la porte thermique. Seuil 0,015 et formule `herbivory_pressure` intouchés.

## Carte des tronçons

| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_banc_mesure.md` — banc `bancs/mesure_calendrier.py` + `mesures/avant.md` | intact | **fait** |
| ② | `02_calendrier_unique.md` — `calendrier.py` + décalage des 4 courbes + `mesures/apres_decalage.md` | **re-figé LARGE** `4c696821…` → `a3dfbec3…` | **fait** |
| ③ | `03_recalibrage.md` — fenêtres au mois réel (aléas, champignons, abscission) + seuils sur écarts mesurés + bancs F5 + `mesures/apres_recalibrage.md` | **re-figé** `a3dfbec3…` → `bfe6f889…` | **fait** |
| ④ | `04_vue.md` — audit C# saisonnier, `dotnet build`, protocole F5 « une année » | intact | à faire |

## Chiffres AVANT (①, `mesures/avant.md`)

- Glace de la mare (tourbière) : 10 / 11 / 1 sem. au **printemps** [n=3 ans, VM], 0-1 en hiver.
- T_air hebdo jamais < 0 : 0 sem. de gel en 3 ans [n=3 ans, VM] ; T min annuelle en
  hiver (an 1, s51) ou printemps (an 2 s9, an 3 s1) [n=3 ans, VM].
- Pommier (`floraison_saisons`) : bloom s14-s15 = **été** [n=3 ans, VM] ; recouvrement
  0/2 puis 2/2 sem. ; 0-2 fruits. Jour le plus long s25 (été, `daylength`).
- Tomates du smoke : disparues s23 (été) an 1 ; abscission 1ʳᵉ s35 chaque année ;
  carpophores (coprin seul) été/automne/hiver, jamais au printemps [n=3 ans, VM].
- Pommier du smoke : jamais fleuri en 3 ans → indicateur 4 lu sur `floraison_saisons`.

## ② — résultat

- `data/code/calendrier.py` (racine, zéro import) = source unique : `SAISONS`, prédicats,
  `SEMAINE_HIVER`, `wiy_de`, `W_T_MIN = 45`, `W_SOLSTICE_ETE = 14`. `sim/engine/calendrier.py`
  = ré-export. Branchés : `weather._saison_meteo`/`temp_norm`/`humidite_air`, `wind.wind_at`,
  `precroissance`, `growth/phases._season_factor`, `population/constants` (+ défauts
  `vie_macro`/`field` = `W_SOLSTICE_ETE`).
- Golden `4c696821…` → `a3dfbec3588192e4…` : plomberie seule vérifiée bit-identique (phases
  remises à 4/25 → ancien hash) → la dérive vient UNIQUEMENT des 2 constantes de phase.
  `population_hash.txt` `3416d328…` → `b0e3b7fa…` (photopériode décalée).
- Tests mis à jour (semaine climatique figée, décalage uniforme −11) : `test_faune_dediee`
  (solstice d'hiver 51→40, 7→48, 25→14), `test_population` (hiver profond 44-49→33-38,
  46/30/25→35/19/14 ; moustique : pluie coupée, le smoke fait désormais une flaque de fin d'hiver).

| Indicateur [n=3 ans, VM] | Avant | Après ② | Réalité (§4) |
|---|---|---|---|
| T min annuelle | s51/s9/s1 (hiver/print.) | s43-44 (hiver) | ✅ |
| T max annuelle | s29/s26 (aut./été) | s18-19 (été) | ✅ |
| Jour le plus long | s25 (été, fin) | s14 (été, ≈21 juin) | ✅ |
| Glace mare (tourbière) | 10/11/1 sem. printemps | 9 hiver an 1 ; 2 printemps an 2 | ✅ (quasi) |
| Gel T_air<0 | 0 | 0 (T min +0,3 °C) | à juger F5 |
| Pommier bloom_week | s14-15 (été) | s4-5 (≈ mi-avril, printemps) | ✅ |
| Recouvrement fleur×butineurs | 0/2, 2/2, 2/2 | 0/2, 2/2, 2/2 | an 1 rouge |
| Tomates smoke | mortes s23 (été) | mortes **s5** (printemps) — **herbivorie** | 🔴 |
| 1ʳᵉ abscission | s35 (+12 à +16 °C) | s35 (+4 à +8 °C) — mi-nov. | 🔴 tardive (③ : 30-36) |
| Carpophores | coprin été/aut./hiver an 2-3 | rosé des prés 2 (été an 2) seul | 🔴 fenêtres (③) |

## ③ — résultat

- **Point 0 (C5 + C5bis), deux leviers sur le FLUX, mesurés tous les deux nécessaires** :
  (a) `resources._monoculture_grid` : sol NU → habitat 0 (avant : 0 famille = monoculture
  « maximale » = 1 → le puceron tenait 0,45 de capacité sur tout le sol nu et tombait
  d'emblée sur chaque semis) ; (b) rampe thermique PAR GUILDE (`TrophicSpec.t_cold_zero/
  t_warm_full`, défaut = 3→15 °C global → autres guildes bit-identiques) ; puceron et
  doryphore `T_RAV_COLD/FULL` = 9→19 °C (`registry.py`) ; limace inchangée. Sonde : (a)
  seul ne suffisait pas (bourrache morte s6) ; (a)+(b) → 7 suites vertes.
- Aléas, champignons au mois réel (§5, tels quels sauf tempête gardée 27-52 comme le
  kickoff). Abscission 30-36 **+ pivot `ABSCISSION_BASE` 38 → 34** (écart : 38 tombait hors
  de la fenêtre, la borne aurait tout fait). `bois_chute_semaine` relus : aucun ne contredit
  son intention (thym/lavande 48, myrtille 46 = hiver ; framboisier 38 ≈ mi-déc.) → inchangés.
- Bancs F5 : `effondrement` 1309 → **217** (aléas recalés : la frappe 1310 devenait un Orage ;
  218 = Grêle locale i=2,0, ciel composé 2,0 dès 215) ; tests liés (`test_meteo_heterogene`,
  `test_couvertures`, `test_ciel_compose`) suivis. Départs 9/12/20 conservés (intentions
  remplies : s9 ≈ mi-mai 13 °C).
- Tests (règles de ②, semaine climatique −11) : `test_fongique` (fenêtres), `test_mycelium`
  (40 → 36), `test_population` (décollage jugé sur plots plantés ; redoux avec un hôte),
  `tests/bancs/test_climatique` (acclimatation + germination départ s42),
  `tests/bancs/test_biotique` (étalement 16 → 5), `test_senescence` (isolation météo
  complétée : vent + rôle fongique lisaient encore les aléas → pommier mort de sécheresse
  à 58,3 ans au lieu de sénescence à 59,8).
- Golden `a3dfbec3…` → **`bfe6f889e172932a…`** ; `population_hash` `b0e3b7fa…` → `6007f2cd…`.
- Suites : **92/94 vertes** [hors 500 ans]. 2 rouges PRÉEXISTANTES (rouges à `e38ae8a`) :
  `tests/bancs/test_succession` (pioneer domine) ; `tests/bancs/test_edaphique` (plantait en
  IndexError à HEAD et en ② ; atteint désormais « n du sol reste bas » : n=0,42 > 0,3).
  Les 3 oracles `tests/bancs` rouges depuis ② (hors des 7) sont vertes.

| Indicateur [n=3 ans, VM] | Avant | Après ② | Après ③ |
|---|---|---|---|
| T min annuelle | s51/s9/s1 | s43-44 (hiver) | −0,3 s4 / +0,3 s44 / −0,6 s2 (gelée tardive avril) |
| Gel T_air<0 | 0 | 0 | 1 sem. printemps an 1 et an 3 (avril) |
| Pommier bloom_week | s14-15 (été) | s4-5 | s5-6 (≈ fin avril) |
| Recouvrement fleur×butineurs | 0/2, 2/2, 2/2 | idem | idem — an 1 rouge (F5) |
| Tomates smoke | mortes s23 | mortes s5 (herbivorie) | mortes s21 (été) an 1 |
| Pression ravageur > 0,015, plots plantés avril [n=1 seed, 2 ans] | — | 11/56 ; 56/95 | **0/56 ; 27/97** |
| Idem été (wiy 13-20, an 2) | — | 263/263, pmax 0,124 | 261/261, pmax 0,116 |
| 1ʳᵉ abscission | s35 (+12 à +16 °C) | s35 (mi-nov.) | **s31 (+11,3 °C, ≈ fin oct.)** |
| Carpophores (coprin) | été/aut./hiver | rosé 2 seul | été/aut. an 2 ; print. (mai)/été/aut. an 3 |
| Neige | — | 1 sem. hiver an 2 | 1 sem. hiver an 2 |

## Points F5 / candidats dette (③)

- Recouvrement fleur×butineurs **an 1 = 0/2** : pas la porte photopériodique (jour 13,9 h
  en s5 > `daylen_full` des butineurs précoces) → colonisation depuis zéro l'an 1 ; pas
  forcé (critère : « ne pas forcer »). À juger F5.
- Gelée tardive en avril : T min annuelle tombe au printemps certaines années — réaliste
  (saints de glace), à confirmer F5.
- `effondrement` re-calé à 217 : contraste voile/nu à revoir au F5 (comme avant).
- `resources.py` 379 LDC (🟡, +1 ligne) — préexistant, responsabilité unique.

## Ce qui reste

④ (vue C# + protocole F5 « une année »). Garde-fous : ne JAMAIS lancer
`tests/test_epaisseur_500ans.py` ; mesures ≤ 3 ans.

## §REPRISE

Lire `CLAUDE.md` + ce fichier + `04_vue.md`. ② et ③ sont dans l'arbre de travail, non
commités. Lancer : `/sprint-auto sprint_calendrier_unique` (reprend à ④).
