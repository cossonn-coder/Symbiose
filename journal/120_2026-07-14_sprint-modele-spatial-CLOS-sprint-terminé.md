# 2026-07-14 — Sprint MODÈLE SPATIAL — CLOS (`/sprint-auto`)

Exécution autonome des 3 tronçons figés (`sprints/sprint_modele_spatial/`,
conception FIGÉE 2026-07-14, doc `docs/conception/CONCEPTION_MODELE_SPATIAL.md`).
Trois plaintes de Nico : (1) « les plots sont trop restrictifs » ; (2) « plusieurs
plantes devraient pouvoir pousser au même endroit » ; (3) « les clones ne
ressemblent pas aux plantes clonées ». Diagnostic cardinal : **le moteur faisait
déjà ~80 % de la demande** — position plante déjà CONTINUE (`x_cm/y_cm`), empreinte
déjà variable par plante, verrou d'occupation déjà levé, cohabitation arbitrée par
`niche_index`. L'écart PERÇU venait du **placement** (recentrage systématique au
centre du plot → superposition visuelle) et de la **morphogénèse amorcée par
position** (clone décorrélé de sa mère). D'où 2 chantiers seulement, chirurgicaux.

## Tronçons livrés (①→③)

- **① Placement sous-plot** (`6b2480d`) — deux cas distincts. **Plantée par le
  joueur** = position au PIXEL CLIQUÉ EXACT : `planter` reçoit `x_cm/y_cm`, le
  grain (`GrainEnAttente`) les porte, la levée place la plante PILE là (le pont
  route `target.get("x_cm")` — fini la perte du pixel dans `_plot_at`).
  Event-driven → golden NEUTRE pour ce cas. **Férale** (succession spontanée) =
  offset hashé déterministe `_offset_subplot` (canaux `week×53`/`×59`, décorrélés)
  borné [10, 40] cm DANS le plot → plot-foyer (chimie 50 cm) INCHANGÉ, fini le
  centrage. **Golden RE-FIGÉ par le cas féral** (positions férales dérivent →
  `x_cm/y_cm` sont dans `_PLANT_ATTRS` → lumière/empreintes), prévu :
  `240f10219e…` → **`4f6c4f31e0…`**.

- **② Identité morphologique héritable** (`810c732`) — champ `form_seed` +
  `branch_count` sur `PlantInstance` (hors `_PLANT_ATTRS`), fabrique déterministe
  `form_seed_at()` dans `fields/noise.py`, posée aux 2 sites de levée
  (`succession.py`) et **COPIÉE au ramet** (`clonal.py`, `branch_count` remis à 0).
  `_debourrement` amorce l'aléa de branche par `form_seed` + ordinal
  `branch_count` (`_hash_noise(fs, 0, k, …)`) au lieu de position+semaine → le clone
  REJOUE la séquence : sa k-ième branche tire le même angle que la k-ième de la
  mère = **air de famille**, divergence fine ensuite par lumière/phototropisme. Le
  ramet reste juvénile (pas de head-start — philo #2). **Golden NEUTRE** contre
  l'attente du kickoff : le digest capture les scalaires `_PLANT_ATTRS` + gènes,
  PAS les `segments`/angles de branche — silhouettes reseed (vérifié empiriquement
  footprint `b929…`→`67f1…`) mais aucun scalaire capté ne bouge sur la fenêtre
  2 tuiles × 2 ans. `golden_hash.txt` laissé intact ; suites croissance 67/67,
  phototropisme 11/11, sénescence PASS.

- **③ Banc d'observation + F5** (`f79dcf7`) — banc `modele_spatial` (registre
  `BANCS`, sélectionnable `init config="modele_spatial"`) : un framboisier mature
  qui essaime des drageons à l'air de famille + un trio de trèfles au MÊME plot
  posés à des positions sous-plot distinctes (plus de superposition). Composition
  PURE de l'état moteur (plantes du catalogue + Engine), AUCUN changement moteur →
  **golden INTACT**. Runner `python3 -m bancs.modele_spatial` asserte `form_seed`
  hérité sur une lignée clonale + positions du trio distinctes.

## Bilan

- **Golden final : `4f6c4f31e0…`** (1 seul re-figeage, le cas féral de ①, prévu et
  annoncé ; ② prévu re-figé mais s'est révélé neutre — le digest ne capture pas les
  angles de branche).
- **Refactor auto-léger : no-op** — aucun fichier passé en rouge (>400 LDC pur) par
  ce sprint ; `actions.py` reste à 391 (jaune, préexistant, +4 lignes seulement).
- **Perf** : négligeable (une passe au placement ; ② remplace une clé de hash, pas
  un coût runtime).
- **Dette repérée hors périmètre** : `tests/test_sim_server.py` échoue 268/271 sur
  3 checks `engine_version 0.5.28` vs `0.5.29` — **préexistant au sprint** (bump du
  sprint allélopathie ⑥ non propagé aux checks `conteneurs.py`/`voix.py`/
  `structures.py`). NON causé par ce sprint, non corrigé (chirurgie) → à traiter à
  part.

**Reste F5 Nico** (checklist du banc `modele_spatial`) : plantes moins alignées au
centre ; trio de trèfles au même plot non superposé ; drageons du framboisier au
port de la mère mais plus jeunes ; option `planter` au pixel exact.
