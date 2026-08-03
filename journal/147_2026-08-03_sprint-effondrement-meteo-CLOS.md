# 2026-08-03 — Sprint EFFONDREMENT MÉTÉO PARTAGÉE (D104) — CLOS

`/sprint-auto`, tronçons ①→④. Solde **D104** : la météo restait un tirage
**global fanné à l'identique** aux 8 secteurs → une semaine à malchance composée
effondrait le **jardin entier le même hiver** (viole #7, tue la leçon
microclimat/abri). Verdict de conception (Nico, 2026-08-02) : l'effondrement est
**voulu** (#4 : seedbank/succession repeuplent), c'est son **uniformité** qui est
le défaut. Levier retenu : **événement global conservé** (signes/forecast/palier
maîtrise intacts), **impact spatialement hétérogène**, plancher de survie
**émergent** `f(abri, paillage, diversité)` — aucune constante gravée.

**Golden `9ad035f18…` → `22768f339ac41bb20b1604bb29672bb3b209ee62ec659b1c8369dd31ccd6cfb8`**
(re-figé UNE fois au ①, **prévu**) ; ②③④ le **préservent** bit-à-bit.
`dotnet build` VERT au ④.

## ① Impact hétérogène (`db10b96`, golden RE-FIGÉ prévu)
- **`scope="local"` honoré** : `weather.patch_local(seed,week,rows,cols)` (canaux
  sentinelles `K_PATCH_R/C`, `PATCH_FRAC=0.42`) → la grêle ne frappe qu'un patch
  déterministe ; `boucle.py` passe une `severity_fn` nulle hors patch à
  `_mediated_damage`.
- **Averse concentrée par le relief** : `tick_hydrology` module la part
  `pluie_event>0` par l'altitude locale (creux ×(1+coef), hauteur ×(1−coef)),
  `RELIEF_APPORT_COEF=0.5` ; sécheresse/calme/conteneurs restent uniformes
  bit-identiques.
- `test_meteo_heterogene` (seed 12345, week 1310) : variance spatiale de survie
  > 0 (in patch 0 % / out 100 %) + plancher ∝ abri (paillage 176 vs nu 54).
- **Dérive golden = relief d'averse sur Pluie prolongée UNIQUEMENT** (le smoke
  n'a aucune Grêle → patch neutre) ; cascade humidité→diffusion/lessivage/rosée
  numérique infime, **survie identique** (0 plante flippée). Localisée, maîtrisée.
- **Écarts vs kickoff (prémisses déjà acquises, donc pas de code)** : (b) canicule
  déjà spatiale via évaporation ∝ T_sol ; (d) médiation health météo déjà résorbée
  (Gelée/Grêle passent par `_mediated_damage`) — le seul `health` plat restant =
  ravageurs (limaces/chenilles), **canal hors météo**, laissé hors ①.

## ② Préavis dramatique du composé + `ciel_semaine` (`30aa890`, golden INTACT)
- Module frère read-only **`sim/ciel.py`** (`weather.py` reste la météo pure),
  zéro RNG, aucun champ de sim touché :
  - `convergence()` : scalaire pur = **somme des intensités sévères** (≥0.8σ) sur
    une fenêtre `forecast` de 3 sem ; `est_compose` au-delà du seuil. Somme (pas
    comptage) car le collapse de référence est un **coup unique très fort**
    (Grêle 1.94σ) — un comptage ne le détecterait jamais.
  - `SIGNE_COMPOSE`/`NOM_COMPOSE` = signe intensifié « l'hiver de tous les
    dangers » (donnée, voix naturaliste), nom **masqué sous le palier expertise**.
  - `ciel_semaine()` → `CielSemaine` (`@dataclass frozen`) : événement +
    nébulosité + convergence + signes 1-2 sem, **prêt à sérialiser** pour ④.
- `test_ciel_compose` : convergence à l'approche de l'an 26 > semaine calme ;
  pureté (deux appels identiques) ; masque de nommage au palier.

## ③ Couvertures posables voile/cloche/ombrière (`0261e4d`, golden NEUTRE)
- Mixin **`fields/ecofields/couvertures_posees.py`** : deux `GridField [0,1]`
  alloués **paresseusement** (None au repos → neutralité par construction),
  `couvert_pose` (voile/cloche) + `ombre_pose` (ombrière), readers neutres.
- Voile/cloche → **couvert additionnel** lu par `t_min_nuit_at` (gel) + protection
  grêle locale dans `_mediated_damage`. Ombrière → `appliquer_ombrieres()` (1 ligne
  dans `boucle.py` après `tick_light`) atténue la **lumière-sol** → moins de
  chaleur/évaporation (anti-canicule). Tout **par le milieu**, jamais de
  multiplicateur direct sur la plante (#1/#2).
- Gestes `poser_voile/cloche/ombriere` (`sim/actions/couvertures.py`, modelés sur
  `poser_tuteur`), câblés couts/déblocage (maîtrise `météo`)/palette/`__init__` ;
  voix : 3 fiches geste + technique neuve `protection-climatique`.
- `test_couvertures` : voile atténue le collapse + neutralité + gestes-milieu.
- **Décision** : l'ombrière atténue la lumière-**sol** (grille lue par thermique/
  hydro), pas le `received` par-plante — occulteur géométrique du LightField
  différé ; l'effet visé (audit canicule « impact via évaporation ») est atteint.

## ④ Vue Godot : encart « état du ciel » + couvertures + banc F5 (`78657ee`, golden INTACT)
- **Pont** (`serialize.py`, protocole **0.5.42 → 0.5.43**) : bloc `ciel` sérialisant
  `sim.ciel.ciel_semaine` + blocs creux `couvert_pose`/`ombre_pose`. Nommage gaté
  **côté moteur** (le pont lit le palier météo D12 serveur-side et le passe à
  `ciel_semaine` ; `nom_compose` joint au palier ≥ 4) — Godot reste bête.
- **Encart `world/SkyPanel.cs`** : diégétique (fond clair→couvert→**plomb** ∝
  convergence, nuages/halo/brume, liseré rouge battant si composé). **Zéro chiffre/
  barre/icône calendrier** (#5). Perceptif toujours affiché, nom gaté.
- **Placeholders `visuals/CoverLayer.cs`** : voile/cloche (drap translucide) +
  ombrière (filet hachuré).
- **Banc F5 `bancs/climatique.py::effondrement`** : tuile 16×11, moitié voilée,
  seed 12345, Grêle sem. 1310 → à la frappe **abrité 41/96 vs exposé 5/80** vivants.
- Câblage `WorldView.Ciel.cs` (partial neuf) + hooks `WorldView.cs`/`.Snapshot.cs`.
- **Décisions imprévues** : (a) le palier météo n'était pas un champ du snapshot →
  masquage du nommage **dans le pont** (plus propre) ; (b) couvertures non exposées
  au snapshot (seulement registre F6) → 2 blocs creux ajoutés ; (c) **tension
  irréductible** anticipation vs contraste de fauche (chaque tick durcit les
  semis) → départ 1309 privilégie le contraste, laissé au calibrage F5.

## Refactor auto-léger
**No-op** : aucun fichier touché ne dépasse 400 LDC pur ; le plus haut,
`serialize.py` à 368 (🟡 vigilance, SRP sérialisation du pont), reste sous la barre.

## Suites de tests
- `test_golden` : re-figé au ①, intact ②③④.
- Neufs verts : `test_meteo_heterogene`, `test_ciel_compose`, `test_couvertures`.
- Pré-existants rouges NON causés par le sprint (reproduits sans les changements) :
  `test_vent` 52/54, `test_sim_server` 269/270 (pommier pré-âgé).

## Reste F5 Nico
- Encart : se lit-il d'un regard ? S'assombrit-il assez tôt / assez nettement ?
  Compromis du départ (sem. 1309 : ciel déjà lourd à l'arrivée, pas de virage
  clair→plomb net mais fauche franche) à arbitrer.
- Zone abritée survit-elle visiblement au banc `effondrement` ?
- Nommage au palier maîtrise au bon moment ?
- Calibrages : `RELIEF_APPORT_COEF`/`PATCH_FRAC` (① — l'eau flaque-t-elle dans les
  creux ? la grêle frappe-t-elle un coin crédible ?), `SEUIL_SEVERE=0.8`/
  `COMPOSE_SEUIL=1.8`/`NOMMAGE_PALIER=4` (②), doses/emprises couvertures
  (`VOILE_COUVERT=0.85`, `CLOCHE_COUVERT=0.95`, `OMBRIERE_OMBRE=0.5`, rayons ③).

**DETTE D104 → ✅ CLOS.** Reste **F5 Nico** (aucun bug connu).
Banc : `init config="effondrement"`.
