# Sprint « Stabilisation perf en run éternel » — état vivant (carnet de bord)

> Carnet de conception (`/conception`). Phase A (challenge) EN COURS — rien n'est
> figé. Reprise à froid = lire `CLAUDE.md` + ce fichier.

## Sujet
La simulation du **monde complet 8 tuiles + maison + vie macro** ralentit énormément
au fil des années (turbo ~0,8 j/s à la 5e année) puis **plante**. Objectif : borner
le coût (CPU + mémoire) à horizon INFINI (philo #4 run éternel) sans trahir
l'émergence écologique (#1/#2/#7). Question annexe : réécrire le moteur en C/C++/C# ?

## Faits mesurés (Nico, profil inline borné)
- 8 tuiles : an1 s26 = 3088 ms/tick (360 plantes, 1254 segments) → an1 s52 = 6869 ms/tick
  (534 plantes, 2771 segments). Tick DOUBLE en ½ an, suit plantes (×1,5) et segments (×2,2).
- 2 tuiles / 6 ans : plantes 30→120, ms/tick 210→600 (suit les plantes) ; segments PAR
  plante plafonnés (~40, `_elaguer`). RSS tracemalloc croît linéairement 0,4→6,2 Mo,
  QUE Nico dit « indépendant des plantes/segments » → à PROUVER (tranche a).

## Diagnostic investigation (lecture seule, moi, 2026-07-05)
Trois moteurs, CONFIRMÉS/nuancés :

1. **Population NON bornée globalement** — CAUSE RACINE. Le verrou d'occupation a été
   DÉLIBÉRÉMENT LEVÉ au sprint « compétition intra-plot » (décision Q1/Q4) :
   `sim/succession.py:86-92` — un grain lève même sur plot occupé, la cohabitation est
   décidée par les champs réels, pas un terme d'occupation artificiel. Le recrutement
   féral n'est donc atténué QUE par `niche_index` (lumière-sol + densité racinaire) +
   `couverture_sol` (`succession.py:217`, couvert dense étouffe les adventices).
   Reproduction + ramets clonaux (ceux-ci DÉJÀ gatés couverture) ajoutent aussi.
   → Le frein émergent EXISTE des 2 côtés (recrutement: couverture ; mortalité:
   self-thinning par `shade_stress_damage`) mais il est TROP FAIBLE pour équilibrer :
   recrutement > mortalité → la population croît année après année.

2. **LightField super-linéaire** (`fields/light.py`, ~53 % CPU, D32). Deux boucles :
   - lumière REÇUE par plante (l.240-263) : pour chaque plante, parcourt les voisins
     PLUS HAUTS (tri décroissant + break) → **O(N²)** au pire (densité haute).
   - lumière-sol SCATTER (l.276-325) : coût ∝ plantes × bbox de capsule. Déjà élagué
     (D32 gather→scatter) mais toujours ∝ nombre × taille des plantes.
   → boucle de rétroaction avec (1) : plus de plantes → plus cher → et N grandit.

3. **Mémoire** — PAS de fuite « smoking gun » trouvée en lecture : `game_state["log"]`
   est purgé (`commands.py:156 gs["log"].clear()`), le journal des voix est FIFO borné
   (`sim/journal.py`, JOURNAL_MAX=200), la seedbank est bornée (plots × ≤27 espèces ×
   gènes). Les squelettes ligneux sont retirés à bois épuisé (`decompo.py:71`). La
   croissance RSS mesurée est donc plausiblement : (a) accumulation d'OBJETS plantes +
   squelettes ligneux qui traînent (chacun porte segments + genes + expression), (b)
   dicts seedbank par plot qui se remplissent jusqu'à ~27 espèces sur TOUS les plots,
   (c) overhead tracemalloc. « Indépendant des plantes » = HYPOTHÈSE À PROUVER par un
   profil mémoire PAR CATÉGORIE d'objets (tranche a). NE PAS affirmer avoir trouvé la
   fuite avant preuve.

## Question C/C++/C# — recommandation (à valider Nico)
**Rejeter la réécriture intégrale.** Le problème est ALGORITHMIQUE (N non borné +
O(N²) lumière), pas la vitesse du langage. Réécrire en C donnerait ~30-50× de constante
mais NE change PAS l'asymptote : un O(N²) sur N croissant explose en C aussi, juste plus
tard → on rachète quelques années d'éternel puis même mur. Or « run éternel » = horizon
infini → seul l'asymptote compte. Coûts d'une réécriture : jette « Python = source de
vérité » (invariant CLAUDE.md), casse Option B (Godot = vue), tue l'itération design
rapide, et devrait préserver le golden bit-à-bit (déterminisme flottant inter-langage =
très dur). → Ordre de ROI recommandé : (1) borner N + cache/LOD lumière EN PYTHON
(corrige l'asymptote, préserve tout) ; (2) SI une constante manque encore pour le 20×20,
vectoriser numpy la grille lumière ; (3) en dernier recours, noyau C/Cython pour la SEULE
fonction chaude `_point_in_capsule` (feuille), Python reste source de vérité. JAMAIS de
port intégral.

## Arbitrages TRANCHÉS (Nico, 2026-07-05)
- **A. Plafond population = ÉMERGENT + BACKSTOP.** Renforcer couverture→germination +
  self-thinning densité-dépendant jusqu'à l'équilibre recrutement=mortalité (#2/#7 OK),
  PLUS un cap dur PUR-perf placé très au-dessus du plateau, qui ne se déclenche jamais
  en jeu normal (filet anti-pathologie).
- **C. Périmètre = PYTHON PUR d'abord** (borner N + cache/LOD lumière). numpy et noyau
  Cython (`_point_in_capsule`) restent en RÉSERVE, activés SEULEMENT si les mesures
  post-optim l'exigent encore. PAS de port intégral, PAS de C# (rouvrirait D10).
- **Départ = PROFILEUR MÉMOIRE d'abord** (tronçon ①) : prouver la cause du crash avant
  tout code correctif.
- **B. Re-figeage golden** : ② lumière = BIT-IDENTIQUE (comme D32) → golden intact.
  ③ population = re-figeage MAÎTRISÉ possible (2 tuiles × 4 ans peut voir le self-thinning
  mordre) → annoncé par le kickoff, mesuré.

## Découpage FIGÉ (4 tronçons, perf-first, vue Godot en dernier)
- **① Profileur mémoire + colmatage** — `tools/profile_memoire.py` : tracemalloc PAR
  CATÉGORIE d'objets sur ~12 ans / 8 tuiles → NOMME ce qui croît linéairement. Si une
  catégorie croît INDÉPENDAMMENT de N (suspects : dict `species[r][c]` de la seedbank
  jamais purgé des espèces éteintes ; toute liste appendée par tick), la BORNER
  (cap/FIFO/prune) en préservant le golden. Diagnostic + colmatage ciblé. Golden INTACT.
- **② Spatial LOD LightField** — `fields/light.py` : spatial hash (bucket par plot) pour
  couper la boucle « lumière reçue » O(N²)→O(N·k) ; ne visiter que les capsules qui
  PEUVENT couvrir l'échantillon, dans le MÊME ordre hauteur-décroissante → produit
  flottant BIT-IDENTIQUE (golden intact, comme le gather→scatter D32). + cache géométrique
  réutilisable en temps figé. Golden INTACT (sinon = bug).
- **③ Capacité de charge émergente + backstop** — renforcer `couverture_sol`→germination
  (`succession.py`) + self-thinning densité-dépendant (voie `shade_stress_damage`/
  chronique) jusqu'à l'équilibre recrutement=mortalité ; + cap dur PUR-perf par tuile,
  très au-dessus du plateau. Re-figeage golden MAÎTRISÉ ANNONCÉ.
- **④ Vue Godot — banc d'observation perf** — compteur discret debug (ms/tick, N plantes,
  RSS) + banc F5 d'observation longue durée de la stabilisation. Golden INTACT.

## Leviers perf identifiés (à chiffrer finement en phase B)
- Spatial hash / partition des plantes → boucle lumière reçue O(N²)→O(N·k).
- Cache LightField : géométrie ne bouge qu'à la croissance (hebdo) ; réutilisable tel
  quel en temps figé (planification), recomputable à fréquence réduite en saison.
- Borner N (arbitrage A) → coupe l'asymptote à la racine.
- numpy vectorisation du scatter grille.
- Décimation macro (déjà pop-bornée, foragers n_max) — marge faible.

## §REPRISE
Phase B (figeage). Arbitrages tranchés (A/C/départ ci-dessus). Reste à écrire :
`docs/conception/CONCEPTION_PERF_RUN_ETERNEL.md` (dont le volet bio « capacité de charge /
self-thinning » à ÉTUDIER par Nico), puis kickoffs `01`→`04`, puis commit + maj
DETTE/BACKLOG/journal, puis message /clear + `/sprint-auto sprint_perf_run_eternel`.
Golden actuel = smoke 2 tuiles × 4 ans (hash dans `tests/test_golden.py`). Tronçons ①②④
golden INTACT ; ③ re-figeage MAÎTRISÉ annoncé.
