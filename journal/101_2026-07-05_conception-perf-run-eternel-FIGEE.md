# 2026-07-05 — Conception STABILISATION PERF EN RUN ÉTERNEL (D66) — FIGÉE

`/conception` (phase A = investigation lecture seule, phase B figée). Déclencheur :
Nico, F5 turbo/continu — le monde complet **8 tuiles + maison + vie macro** ralentit
énormément au fil des années (turbo ~0,8 j/s à la 5e année) puis **PLANTE**.

## Enjeu
Philo #4 « run éternel » = jardin à horizon **infini** → coût (CPU + mémoire) **borné**.
Un moteur dont le coût croît avec l'âge du jardin trahit la promesse du jeu.

## Diagnostic (investigation lecture seule, aucun fichier moteur touché)
Trois moteurs de la dérive :
- **M1 — population non bornée = cause racine.** Le verrou d'occupation a été
  délibérément retiré au sprint compétition intra-plot (Q1/Q4, `sim/succession.py:86-92`).
  Le recrutement féral n'est plus freiné que par `niche_index` + `couverture_sol`
  (`succession.py:217`). Les freins émergents EXISTENT des deux côtés — recrutement
  (couvert étouffe les adventices) et mortalité (self-thinning par `shade_stress_damage`)
  — mais **trop faibles pour équilibrer** : recrutement > mortalité → N croît chaque année.
- **M2 — LightField O(N²)** : boucle « lumière reçue par plante » (`fields/light.py:240-263`,
  ~53 % CPU, dette D32 dont le scatter SOL est déjà soldé). Rétroaction avec M1.
- **M3 — mémoire** : PAS de fuite smoking-gun en lecture (`log` purgé `commands.py:156`,
  journal des voix FIFO borné 200, seedbank bornée, squelettes retirés `decompo.py:71`).
  Croissance RSS plausiblement objets plantes/squelettes + dicts seedbank → **à PROUVER**
  par profileur par catégorie (tronçon ①).

## Question C/C++/C# — REJETÉE
Problème **algorithmique** (N non borné + O(N²)), pas la vitesse du langage. Le C donne
~30-50× de constante mais **ne change pas l'asymptote** : un O(N²) sur N croissant explose
en C aussi, juste plus tard → seul l'asymptote compte en run éternel. Une réécriture
jetterait « Python source de vérité », casserait Option B (Godot = vue) et exigerait un
déterminisme flottant bit-à-bit inter-langage (très dur). Reco retenue : Python pur.

## Arbitrages Nico (2026-07-05)
- Plafond population = **ÉMERGENT + backstop sécurité** : renforcer couverture→germination
  + self-thinning densité-dépendant jusqu'à l'équilibre recrutement=mortalité (plateau qui
  varie par tuile → #7) ; PLUS un cap dur PUR-perf très au-dessus du plateau, jamais
  déclenché en jeu normal (disjoncteur). PAS de plafond arbitraire de gameplay (violerait #2).
- Périmètre = **Python pur d'abord** (borner N + cache/LOD lumière). numpy et noyau Cython
  `_point_in_capsule` en RÉSERVE, activés seulement si les mesures l'exigent. Pas de C#.
- Départ = **profileur mémoire** (prouver le crash avant tout code).

## Découpage figé (4 tronçons perf-first, vue en dernier)
① **Profileur mémoire** par catégorie (`tools/profile_memoire.py`, 12 ans/8 tuiles) +
colmatage des accumulateurs indépendants de N [golden INTACT] → ② **Spatial LOD
LightField** (spatial hash O(N²)→O(N·k), **bit-identique** comme D32) + cache géométrique
temps figé [INTACT] → ③ **Capacité de charge émergente** (vis couverture→germination + vis
self-thinning) + backstop cap tuile [RE-FIGÉ maîtrisé ANNONCÉ] → ④ **Vue Godot** banc
d'observation perf (compteur debug ms/tick·N·RSS + banc F5 longue durée) [INTACT].

## Livrables
`docs/conception/CONCEPTION_PERF_RUN_ETERNEL.md` (dont §4 volet bio « capacité de charge /
self-thinning » à ÉTUDIER par Nico) + `sprints/sprint_perf_run_eternel/` (00_etat + 01→04).
Golden de départ = `061934db09ad646a01f19b8f4d0b677f13438e87bce2f8531527be425e7c22a8`.
Dette D66 ouverte, backlog mis à jour. **Prêt pour `/sprint-auto sprint_perf_run_eternel`.**
