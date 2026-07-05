# Tronçon ③ — Capacité de charge émergente + backstop sécurité

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` + `CONCEPTION_PERF_RUN_ETERNEL.md`
> **§4 en entier** (le volet bio) + §2(M1). Lancement depuis `data/code/`.
> Fichiers cœur : `sim/succession.py`, la voie de mort par stress chronique, un cap tuile.

## Objectif
Faire **plafonner naturellement** la population de plantes (aujourd'hui non bornée →
cause racine du ralentissement, M1) en **resserrant deux freins écologiques DÉJÀ présents**
jusqu'à l'équilibre `recrutement = mortalité` à une densité propre à chaque tuile (plateau,
pas croissance sans fin). PLUS un **cap dur PUR-perf** par tuile, très au-dessus du plateau,
qui ne se déclenche jamais en jeu normal (disjoncteur anti-pathologie).

**Philo (impératif)** : #2 flux → contrainte → réponse émergente ; #7 hétérogénéité (le
plateau varie par tuile). **INTERDIT** : tout terme direct « −santé si trop de voisins »
(malus direct sur la plante). On agit sur le MILIEU (couvert, lumière reçue), la plante
répond. Lire `CONCEPTION_PERF_RUN_ETERNEL.md` §4.3 pour la frontière ✅/❌.

## Les deux vis à resserrer (mécanismes existants)

### Vis A — suppression de germination par la couverture
`sim/succession.py:217` : `if eco.couverture_sol.at_plot(r, c) >= COUVERTURE_ADVENTICE_SEUIL:`
supprime déjà la levée des adventices sous couvert dense. Aujourd'hui **trop permissif**.
Deux réglages possibles (choisir/combiner en mesurant) :
- **abaisser** `COUVERTURE_ADVENTICE_SEUIL` (le tapis étouffe plus tôt) ;
- rendre la réponse **graduée** plutôt que binaire : au lieu d'un seuil dur, atténuer la
  proba/niche de germination de façon continue avec `couverture_sol` (ex. facteur
  `1 - couverture` appliqué à `niche`) → une fenêtre de plus en plus étroite à mesure que
  le couvert se ferme. Flux (ombre du couvert) → contrainte (fenêtre réduite) → réponse.
Vérifier aussi que **reproduction** (`_reproduction`) et **ramets clonaux**
(`sim/clonal.py`, déjà gaté couverture) respectent le même frein — la vis doit serrer TOUS
les canaux de recrutement, pas seulement les adventices.

### Vis B — self-thinning (mort par stress chronique du dominé)
La voie `shade_stress_damage` (sprint « mort par stress chronique », voir
`sim/engine/mortalite.py` / la fonction de dégât d'ombre) tue déjà une plante durablement
sous-éclairée. Aujourd'hui **trop lente** pour compenser le recrutement. Resserrer la
sensibilité : une plante dont la **lumière reçue** (`eco.lumiere.light_received`) reste
sous son seuil vital plus longtemps/plus fort accumule le stress plus vite → meurt. C'est
l'auto-éclaircie (§4.1) : dans un peuplement dense, les dominés meurent, la densité
plafonne. **Aucun comptage de voisins** : c'est la lumière reçue (déjà baissée par les
dominantes via la boucle d'ombre) qui porte la contrainte — flux → contrainte → réponse.

**Calibrage = le cœur du tronçon.** L'objectif chiffré : sur le monde 8 tuiles, `N(t)` doit
**se stabiliser** (plateau) au lieu de croître linéairement. Instrumenter avec le profileur
① / `profile_tick` : ticker ~15-20 ans et vérifier que N atteint un plateau (qui varie par
tuile selon fertilité/lumière → #7 préservé). Itérer les réglages A/B jusqu'au plateau.
Ne PAS viser une densité précise arbitraire : viser la STABILISATION.

## Backstop de sécurité (hors gameplay)
Ajouter un **cap dur par tuile** sur `len(tile.plants vivantes)`, placé **très au-dessus**
du plateau émergent observé (ex. 3-5×). S'il est atteint, **bloquer le recrutement** de ce
tick sur cette tuile (aucune nouvelle levée/repro/ramet) et logger un avertissement debug
(`⚠ cap perf tuile T atteint`). Ce n'est PAS une mécanique visible : c'est un disjoncteur.
Placer la valeur en constante NOMMÉE commentée « PUR-perf, jamais atteint en jeu normal ».
En régime équilibré (vis A/B calibrées) il ne fire jamais → aucun effet observable.

## Golden attendu
**RE-FIGÉ MAÎTRISÉ — ANNONCÉ.** Resserrer germination + self-thinning **change le long
terme** ; la fenêtre du golden (2 tuiles × 4 ans) peut voir le self-thinning mordre (des
plantes du smoke meurent plus tôt, des adventices ne lèvent plus). Procédure :
1. Implémenter, lancer `python3 -m tests.test_golden` → il ÉCHOUE (attendu).
2. **Comprendre et VÉRIFIER la dérive** : inspecter le nouveau log/digest, confirmer
   qu'elle est bien l'effet du frein resserré (moins de plantes tardives / mortalité de
   dominés accrue) et RIEN d'autre (pas de NaN, pas de chaos, ordre déterministe).
3. Re-capturer : `python3 -m tests.test_golden --capture`. **Documenter** dans `00_etat.md`
   ET dans le message de commit : ancien hash `061934db…` → nouveau hash, en une phrase de
   justification (« self-thinning resserré : dérive localisée attendue, déterminisme
   intact »). Le backstop cap NE doit PAS fire dans le smoke (sinon la valeur est trop
   basse → la relever).
Le re-figeage doit rester **localisé et explicable**. Si la dérive est chaotique/globale
(le monde s'effondre), le réglage est trop agressif → adoucir.

## Ce qu'il NE faut PAS faire
- ❌ Aucun malus direct sur la plante (« −santé si N voisins > k ») — VIOLE #2.
- ❌ Pas de plafond arbitraire qui SCULPTE la population de gameplay (le cap est un
  disjoncteur haut, pas une règle visible).
- Ne PAS toucher la lumière (tronçon ②) ni la mémoire (①).
- Ne PAS lancer `test_epaisseur_500ans`.
- Ne PAS introduire de RNG (déterminisme #3).

## Fin de tronçon
`00_etat.md` : réglages A/B retenus, plateau N observé (par tuile), cap posé + valeur,
ancien→nouveau hash golden justifié. Commit (message : re-figeage annoncé).
