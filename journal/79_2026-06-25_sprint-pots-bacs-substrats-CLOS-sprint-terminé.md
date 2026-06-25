# 2026-06-25 — Sprint POTS, BACS & SUBSTRATS (①→⑤) — SPRINT MOTEUR TERMINÉ

> Exécution autonome (`/sprint-auto sprint_pots_bacs`) sur une conception
> **figée** (`docs/conception/CONCEPTION_POTS_BACS_SUBSTRATS.md`). 5 tronçons
> moteur enchaînés en sous-agents à contexte frais, golden **NEUTRE bit-identique
> sur tout le sprint** (smoke `2ab026ad…`, population `6056713d…`), aucun
> re-figeage. Reste ⑥ vue Godot **différée** (Option B). État détaillé :
> `sprints/sprint_pots_bacs/00_etat.md`.

## L'idée centrale
Un **conteneur** (pot mobile / bac immobile) est un **`EcoFields` miniature** :
zéro nouveau modèle chimique, tous les ticks existants tournent dessus. Le joueur
le compose avec un **substrat data-driven**, l'installe dans le jardin ; un petit
volume **rapetisse** la plante (effet nain émergent) ; un bac à **fond ouvert**
re-communique avec la tuile dessous (drainage, racines, microbiome). La liste de
conteneurs est **VIDE au repos** → le smoke n'en pose aucun → golden neutre.

## Tronçons
- **① substrat data-driven** (`9a5d5a7`) — `world/substrat.py` : `SubstratRecette`
  (frozen) + registre `SUBSTRATS` de 6 recettes (terreau, compost, drainant,
  lasagnes, terre, mycélium) initialisant champs + drainage, garde-fou à l'import.
  `tick_hydrology` gagne `drainage_override=None` (rétrocompatible). 17/17.
- **② conteneur EcoFields miniature** (`d13423f`) — `world/container.py` :
  `Container` + `make_container` (recette appliquée, `terre_jardin` en copie
  profonde isolée), étape boucle « 17b tick conteneurs » (défaut `[]` → no-op).
  **Décision tranchée** : le tissu `substrat` (recette mycélium) était dans
  `FAIM_N_TISSUS` mais absent de `TISSU`/`TISSU_ORDER` → on lui DONNE une cinétique
  de décompo (§2 exige « faim d'azote PUIS libération »), ajouté EN FIN de
  `TISSU_ORDER` (ordre tuile inchangé). 7/7.
- **③ confinement racinaire = effet nain HYBRIDE** (`8149acd`) — 3 leviers
  ÉMERGENTS (philo #2, zéro malus direct) : `volume_factor` amplifie le flux uptake
  rapporté au volume réel (pénurie via stress EXISTANTS), uptake borné aux cellules
  du pot, signal root-bound bridant la croissance segmentaire QUAND le réservoir
  sature. Params neutres `volume_factor=1.0` / `confinement=1.0`. Proxy de
  saturation = `current_height` (`PlantInstance.biomass` n'existe pas). Test :
  gradient nain 5L 19 cm < 75L 52 cm ≤ 200L 61 cm. 6/6.
- **④ mobilité + bacs N×M + pont snapshot** (`82589f3`) — `sim/actions/conteneurs.py`
  (façades `poser_pot` / `poser_bac_culture` / `deplacer_pot`). `deplacer_pot`
  débite la Vigueur JOUEUR seule et n'écrit que `x_cm/y_cm` (philo #2, lumière/ombre
  recalculées au tick suivant = émergent). Bacs immobiles. Snapshot : bloc
  `containers`. **Collision** `poser_bac` (déjà = bac à COMPOST) résolue par alias
  `poser_bac_culture`. Protocole pont **0.5.6 → 0.5.7**. test_mobilite 7/7,
  sim_server 205/206 (rouge « pommier pré-âgé » préexistant).
- **⑤ couplage fond ouvert + arc lasagnes — SPRINT MOTEUR CLOS** (`f824bd2`) —
  `tick_hydrology` **RETOURNE** les pertes de drainage (rétrocompatible, aucun
  appelant ne lit → golden neutre ; approche recommandée, pas de duplication de
  boucle). `Container` : champs `tile_eco`/`tile_rc`, **point 1** `_drainer_vers_tuile`
  (eau du fond → humidité tuile, POT+BAC), **point 2** racines descendent au
  root-bound → uptake tuile profond → effet nain LEVÉ (bac fond ouvert), **point 3**
  `_diffuser_vers_tuile` (microbiome/om bidirectionnel, masse conservée, bac fond
  ouvert seul ; pot fond fermé = drainage seul). Arc lasagnes validé (litière
  pré-chargée → décompo confinée → plante nourrie). Pont reste 0.5.7 (`fond_ouvert`
  déjà exposé en ④). test_couplage 8/8.

## Garde-fous tenus
- **Golden NEUTRE prouvé bit-identique à chaque tronçon** — aucun re-figeage sur
  tout le sprint (objectif annoncé en conception, tenu).
- Philo #2 (flux → contrainte → réponse, jamais de bonus/malus direct sur la
  plante) respectée sur les 3 effets sensibles : effet nain, mobilité, couplage.
- Règle d'interconnexion des acteurs honorée par le couplage fond ouvert.
- Couches respectées (`world` importe `fields`/`plants`/`sim.growth`, jamais
  l'inverse — vérifié, pas de cycle).
- C# **non touché** sur tout le sprint (vue ⑥ différée, Option B).

## Reste
- **⑥ vue Godot DIFFÉRÉE** : rendre pots/bacs/substrats visibles côté C#. Kickoff à
  écrire quand la vue reprendra. Aucun F5 requis sur le moteur (data pure).
- Knobs de calibrage post-test (volumes de référence, seuils root-bound,
  `COUPLAGE_DIFFUSION`, cinétique du tissu `substrat`) = placeholders, ajustables
  après observation.
