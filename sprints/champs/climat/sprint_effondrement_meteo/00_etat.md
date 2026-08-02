# sprint_effondrement_meteo — 00_etat (état de sprint, FIGÉ 2026-08-02)

**Phase courante** : FIGÉ, prêt pour `/sprint-auto`. Conception close, 4 kickoffs écrits, 0 tronçon fait.
**Doc de conception** : `docs/champs/climat/conception_effondrement_meteo.md`.
**Carte des tronçons** : ① `01_impact_heterogene.md` (golden RE-FIGÉ) → ② `02_preavis_composite.md`
(intact) → ③ `03_couvertures.md` (neutre) → ④ `04_vue_encart_ciel.md` (intact). Perf-first, finit par la vue.
**§REPRISE (pour /sprint-auto)** : lancer les tronçons RESTANTS dans l'ordre 01→04. Golden re-figé UNE
fois au ①, annoncé (impacts météo spatialisés + médiation health résorbée) ; ②③④ le préservent.

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
