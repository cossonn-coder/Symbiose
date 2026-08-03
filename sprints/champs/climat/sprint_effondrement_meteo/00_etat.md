# sprint_effondrement_meteo — 00_etat (état de sprint, FIGÉ 2026-08-02)

**Phase courante** : EN COURS. ①②③ FAITS. Reste ④.
**Doc de conception** : `docs/champs/climat/conception_effondrement_meteo.md`.
**Carte des tronçons** : ① `01_impact_heterogene.md` ✅ FAIT (golden RE-FIGÉ) → ② `02_preavis_composite.md`
✅ FAIT (golden INTACT) → ③ `03_couvertures.md` ✅ FAIT (golden NEUTRE/INTACT) → ④ `04_vue_encart_ciel.md` (intact). Perf-first, finit par la vue.
**§REPRISE (pour /sprint-auto)** : lancer le tronçon RESTANT ④. Golden re-figé au ①
(`22768f339ac41bb20b1604bb29672bb3b209ee62ec659b1c8369dd31ccd6cfb8`), CONFIRMÉ INTACT au ②③ ; ④ le PRÉSERVE.
④ consommera `sim.ciel.ciel_semaine` (structure `CielSemaine` prête à sérialiser) ET, pour le rendu des
structures posées (placeholders), exposera `eco.couvert_pose`/`eco.ombre_pose` (déjà au registre `get_field`).

## ① Impact hétérogène — FAIT (2026-08-03, NON commité, Nico commit)
- **(a) Averse concentrée par le relief** : `tick_hydrology` module la part `pluie_event>0`
  par l'altitude locale (creux ×(1+coef), hauteur ×(1−coef)) ; sécheresse/calme = uniforme
  bit-identique. Constante `RELIEF_APPORT_COEF=0.5` (`fields/ecofields/constants.py`).
- **(c) `scope="local"` honoré** : `sim/weather.py::patch_local(seed,week,rows,cols)` (2 canaux
  sentinelles `K_PATCH_R/C`, `PATCH_FRAC=0.42`) → la grêle ne frappe qu'un PATCH ; `boucle.py`
  passe une `severity_fn` (sév hors patch = 0) à `_mediated_damage`. `scope="global"` inchangé.
- **(b) Canicule sur ombre/évaporation** : DÉJÀ acquis avant ① (Canicule ∈ TEMP_DRIVEN → T_air
  chaud → évaporation lit T_sol spatial ombre/soleil). Aucun code. Vérifié.
- **(d) Médiation health météo** : DÉJÀ résorbée avant ① (Gelée tardive ∈ TEMP_DRIVEN via
  `_mediated_damage` ; Grêle interceptée hors `appliquer_alea`). AUCUN événement météo n'atteint
  la voie `health` plate. Reste `health` = ravageurs (limaces/chenilles), canal HORS météo → hors ①.
- **Golden re-figé** : dérive dans la fenêtre smoke = UNIQUEMENT le relief d'averse (Pluie
  prolongée ; aucune Grêle dans le smoke → patch neutre ici). Cascade humidité→diffusion/lessivage/
  rosée/givre, TOUTES numériques infimes, **survie IDENTIQUE** (0 plante flippée). Localisée + maîtrisée.
- **Test ajouté** : `tests/test_meteo_heterogene.py` (seed 12345, week 1310 = an 26 s10, Grêle i=1.94) —
  variance spatiale de survie > 0 corrélée au patch (in-patch 0 % vs out 100 %) + plancher ∝ abri
  (paillage 3 → 176 survivants vs nu 54). PASS.

## ② Préavis dramatique du composé + `ciel_semaine` — FAIT (2026-08-03, NON commité, Nico commit)
- **Nouveau module `sim/ciel.py`** (frère de `weather.py`, couche `sim`, 47 LDC pur, 🟢) — SRP :
  `weather.py` = météo pure, `ciel.py` = LECTURE agrégée. Read-only sur la fonction météo, zéro RNG,
  aucun champ de sim touché.
- **(a) `convergence(seed, week, horizon=3)`** : scalaire PUR = somme des intensités sévères
  (≥ `SEUIL_SEVERE=0.8`) dans une fenêtre resserrée de `forecast`. Monte à l'approche d'un composé
  (un coup exceptionnel OU plusieurs rapprochés). `est_compose` = `convergence ≥ COMPOSE_SEUIL=1.8`
  (calibré ~0.8 composé/an sur seed 12345, F5 ajustable — non gravé au golden).
- **(b) Signe intensifié** `SIGNE_COMPOSE` (3 libellés voix naturaliste, « l'hiver de tous les dangers »)
  + `NOM_COMPOSE`. Le signe perceptif est TOUJOURS montré dès qu'un composé approche (ciel qui s'assombrit
  pour tous, §5) ; seul le NOM est masqué sous le palier.
- **(c) `ciel_semaine(seed, week, palier_climat=0, horizon=2)` → `CielSemaine` (@dataclass frozen)** :
  agrège événement courant + nébulosité (`weather_state`), signes 1-2 sem en avant (`weather_signs`),
  convergence, signe composé, nom composé masqué par palier (`NOMMAGE_PALIER=4` = expertise). Prêt à
  sérialiser par le pont en ④.
- **Golden INTACT** : `22768f339ac41bb20b1604bb29672bb3b209ee62ec659b1c8369dd31ccd6cfb8` (re-vérifié).
- **Test ajouté** : `tests/test_ciel_compose.py` — convergence(1308, an 26 approche Grêle i≈1.94) > semaine
  calme (1300) ; `ciel_semaine` pur (2 appels égaux) ; nom du composé seulement si palier ≥ 4. PASS.

## ③ Couvertures posables (voile / cloche / ombrière) — FAIT (2026-08-03, NON commité, Nico commit)
- **Champs de MILIEU sur `eco`** (nouveau mixin `fields/ecofields/couvertures_posees.py`,
  `CouverturePoseeMixin`, 42 LDC 🟢) : `couvert_pose` (voile/cloche, écran physique) et `ombre_pose`
  (ombrière), 2 `GridField` [0,1] ALLOUÉS PARESSEUSEMENT (None au repos → zéro RAM, readers `couvert_at`/
  `ombre_at` rendent 0.0). PERSISTANTS (aucun tick propre). Déclarés dans `container.py` + exposés au
  registre `get_field` (overlay F6 / pont ④).
- **Voie GEL/GRÊLE (voile+cloche)** : `couvert_at` s'AJOUTE au couvert dans `thermique.t_min_nuit_at`
  (gel nocturne) ET à la protection LOCALE dans `mortalite._mediated_damage` (grêle) — jamais un
  multiplicateur direct sur la plante (philo #1/#2).
- **Voie CANICULE/SÉCHERESSE (ombrière)** : `eco.appliquer_ombrieres()` (1 ligne dans `boucle.py`, JUSTE
  après `tick_light`, avant thermique/hydro) atténue la lumière-SOL → moins de gain solaire → sol plus
  frais → moins d'évaporation. **Décision de design** (§6) : on atténue la lumière-SOL (grille lue par la
  thermique), PAS le `received` par-plante → l'ombrière REFROIDIT sans (encore) brider la photosynthèse ;
  un vrai occulteur géométrique dans `LightField.compute` est différé (le refroidissement/anti-évaporation
  est l'effet visé, 00_etat audit canicule « impact via évaporation »).
- **Gestes** `sim/actions/couvertures.py` (`poser_voile`/`poser_cloche`/`poser_ombriere`, 27 LDC 🟢) modelés
  sur `poser_tuteur` : PLANIFICATION, coût MODÉRÉ, binaire. Câblés : `couts.COUTS`+`OBJETS_TOUCHES`
  (technique NEUVE `protection-climatique`), `deblocage.GESTE_UNLOCK` (maîtrise concept `météo` ≥ 1),
  `palette.FAMILLE_CIBLE` (=`plot`), ré-export `actions/__init__.py`.
- **Voix** : 3 fiches GESTE × 3 niveaux (`geste_corpus.py`) + 1 fiche TECHNIQUE `protection-climatique`
  (`technique_corpus.py`) + ajout au set `encyclopedie_types.TECHNIQUES`. `test_encyclopedie` 68/68.
- **Golden INTACT** : `22768f339ac41bb20b1604bb29672bb3b209ee62ec659b1c8369dd31ccd6cfb8` (re-vérifié) — rien
  posé dans le smoke → champs None → readers neutres → NEUTRE par construction.
- **Test ajouté** : `tests/test_couvertures.py` — sous le collapse connu (seed 12345, week 1310, Grêle
  i≈1.94), les plots du PATCH VOILÉS gardent + de survivants que découverts ; + neutralité (`eco` neuf =
  champs None, readers 0) + gestes-milieu (voile/cloche → `couvert_pose`, ombrière → `ombre_pose` + lumière
  atténuée). PASS. Non-régression : meteo_heterogene / ciel_compose / gestes_manuels / palette / encyclopedie.

---
**[HISTORIQUE CONCEPTION ci-dessous]**
**Phase (archivée)** : A (challenge / dialogue) — RIEN de figé. Attente réponses Nico (3 questions posées).
**Origine** : trouvaille du sprint MESURE `optim_vie_macro` (Dette C + décision n°2, 2026-08-02).
`sprints/perf/faune/sprint_optim_vie_macro/00_etat.md` + `mesures/RESULTATS_review_2026-08-02.txt`.
**Type/thème** : `champs/climat` (doc cible futur : `docs/champs/climat/conception_effondrement_meteo.md`).

## Le fait, re-vérifié au CODE (2026-08-02)
- `weather_state(seed, week)` calculé **1 fois/semaine** (`sim/engine/boucle.py:95`), AUCUN paramètre de tuile.
- Fan-out identique aux **8 secteurs** : `eco.temperature.fill(temp_now)` (:117), gel (:130-146),
  grêle/WEATHER_ALEA/orage (:148-167) — boucle `for tile in self.tiles`.
- `weather_at` (`sim/weather.py:124`) : événement GLOBAL seedé, pas de tuile. Les 8 secteurs vivent
  la MÊME semaine météo → une semaine catastrophe (gel tardif + double tempête + pluie) effondre le
  jardin ENTIER simultanément.
- Mesure (3 seeds, tuile isolée, SANS jardinier) : ~1 chute ≥25 % / 7,9 ans PAR tuile ; météo partagée
  ⇒ **jardin entier ~1-3 fois/partie**, amplitude jusqu'à 0,13 pl/plot (médiane ~0,65).

## Faits de code décisifs (verrouillent le design)
- **`event.scope="local"` (Grêle/Orage) est DÉCLARÉ mais JAMAIS LU** (grep `.scope` dans `sim/` = vide) →
  localisation déjà voulue = **dormante**. Levier bas-coût.
- **Impact déjà partiellement localisé** : gel via `t_min_nuit_at(eco,r,c,temp_now,nebul)` (paillage/
  nébulosité/rayonnement local) ; grêle via patch hash. Température STOCKÉE reste uniforme (`fill`).
- **Appareil de préparation §6 (conception_meteo) = PARTIEL** : brise-vent (périphérie D73/haies),
  `poser_tuteur`, paillage → EXISTENT. **voile d'hivernage / cloche / ombrière → N'EXISTENT PAS** (gestes).
- Signes + forecast : `weather_signs`/`forecast`/`is_signed` IMPLÉMENTÉS (`sim/weather.py:216-334`).
  Palier maîtrise « météo/climat » = conçu (conception_meteo §5), câblage UI côté Godot/D12.
- Ombrage inter-tuiles ABSENT par design (CLAUDE.md) : light strictement intra-tuile.

## Reframe proposé (ma lecture, à valider Nico)
« Voulu vs subi » = FAUX binaire. Décomposition :
1. La collapse-EVENT est **voulue** (philo #4 run éternel + sol/seedbank ; philo transcendant
   « les perturbations entretiennent l'engagement »). Non ouvert. Ouvert = la DOSE.
2. Ce qui la rend **subie** = 3 défauts séparables : (a) **globale/synchronisée** (8 secteurs, 0 survivant)
   → viole #7 hétérogénéité + tue la leçon permaculture (microclimat/abri) ; (b) invisible (préavis non
   ressenti) ; (c) non-atténuable (couvertures non construites + mesure faite SANS jardinier = plancher
   non préparé).
3. Levier TENTANT MAIS FAUX : décorréler la météo par secteur → absurde à 20 m (masse d'air unique) ET
   casse le système de signes (§4 suppose UN ciel à lire) + palier maîtrise climat.
4. Levier JUSTE (reco) : **event global** (réalisme + signes intacts), **IMPACT spatialement hétérogène**
   → « l'exposé flanche, l'abrité tient et re-sème » au lieu de « tout meurt ». = vraie permaculture
   (microclimats d'impact : exposition, inertie, abri, poche de gel), satisfait #7/#6/#1.

## DÉCISIONS NICO (2026-08-02) — grands arbitrages tranchés
- **Q1 = OUI, reframe endossé** : garder l'effondrement, cibler son UNIFORMITÉ globale via un IMPACT
  hétérogène. Événement météo reste GLOBAL (signes/forecast/palier maîtrise intacts). PAS de
  décorrélation par secteur.
- **Q2 = plancher ÉMERGENT** `f(abri, paillage, diversité)` — pas de chiffre gravé. Jardin bien conçu →
  survivants garantis (~0,45) ; jardin nu → chute profonde (~0,13). La borne émerge du milieu.
- **Q3 = TOUT** : impact hétérogène + lisibilité (préavis dramatique du composé) + gestes de couverture
  manquants (voile/cloche/ombrière) + vue Godot. Sprint GROS.

## AUDIT CODE (2026-08-02) — impact déjà majoritairement spatialisé
| canal | lecture | statut |
|---|---|---|
| Gel | `t_min_nuit_at(eco,r,c)` couvert litière/neige + nébul + wind chill local | ✅ local |
| Tempête/verse | `_wind_damage` lit `eco.vent.at_plot` (abri D73) | ✅ local |
| Fongique/pluie | humidité locale + vent local + dispersion spores | ✅ local |
| Grêle/orage | `event.scope="local"` DÉCLARÉ mais JAMAIS LU → 8 secteurs uniformes | ❌ dormant |
| Sécheresse/Pluie | `eco.apply_weather(var,delta)` = fill UNIFORME tuile | ❌ uniforme |
| Canicule chaleur | `temperature.fill` uniforme ; impact via évaporation | ⚠️ brancher ombre locale |
→ Le sprint FINIT une spatialisation à moitié faite (pas un système neuf). Perf quasi-neutre.

## DÉCOUPAGE PROPOSÉ (4 tronçons, perf-first, finit par la vue) — à valider avant figeage
- **① Impact hétérogène (cœur, golden RE-FIGÉ annoncé)** : spatialiser sécheresse/pluie (drainage/
  altitude local) + canicule (ombre/évaporation locale) + honorer `scope="local"` (patch) + élargir
  la dispersion des tampons (abri/paillage/inertie/neige) + médiation complète (résorber voies `health`
  plates) → plancher émergent ∝ abri. Test : sous collapse connu (seed 12345 an 26), abrité survit /
  exposé flanche.
- **② Préavis dramatique + « ciel de la semaine » (lisibilité, golden INTACT)** : détection de convergence
  sur le `forecast` PUR (cluster haute intensité en fenêtre courte) → signe diégétique intensifié, read-only,
  déterministe, zéro RNG. PLUS un helper Python **`ciel_semaine`** qui agrège les signes lisibles (1-2 sem
  en avant) + le niveau de convergence, prêt à exporter (équivalent Python de l'encart Godot, CLAUDE.md).
  PAS de HUD/chiffre (philo #5). Rattaché palier maîtrise climat.
- **③ Couvertures posables (voile/cloche/ombrière, golden NEUTRE hors pose)** : 3 gestes agissant par
  le milieu (couvert froid / protection grêle / ombre chaud), déblocage maîtrise, voix des gestes.
- **④ Vue Godot : ENCART « ÉTAT DU CIEL » + couvertures + banc F5 (golden INTACT)** :
  **encart diégétique** (demande Nico 2026-08-02) = fenêtre rapprochée sur le ciel (couleur/nuages/halo/
  brume/lumière) qui CONDENSE les signes de `ciel_semaine` et **s'assombrit à l'approche du composé** →
  permet d'anticiper la météo de la semaine suivante SANS icône calendrier ni chiffre (philo #5, §4).
  Masque de maîtrise : ciel toujours montré (signal parfait), nommage selon palier. + pont exporte
  `ciel_semaine` + rendu structures (placeholders) + banc F5 (seed 12345 an 26 : encart vire au plomb
  PUIS zone abritée survit / exposée meurt).

## §REPRISE
Grands arbitrages TRANCHÉS (Q1-Q3 ci-dessus). Prochaine étape : Nico valide le DÉCOUPAGE ci-dessus
(feu vert « vas-y/fige ») → PUIS phase B : doc `docs/champs/climat/conception_effondrement_meteo.md`
+ kickoffs `01..04` + commit + message /sprint-auto. Tant que pas de feu vert explicite sur le
découpage : NE PAS créer le doc ni les kickoffs (règle « ne créer que sur OK »). Rien à implémenter.
