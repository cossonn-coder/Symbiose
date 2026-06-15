# Kickoff de CONCEPTION — compétition intra-plot (cohabitation & éclaircissage)

> **Kickoff autosuffisant** (démarrage à froid après `/clear`). Objectif : faire
> passer la **compétition intra-plot** de l'**intention** (gravée au backlog +
> Q4 du sprint planter) à une **conception FIGÉE** (décisions Q-par-Q tranchées
> par Nico), prête pour un kickoff d'implémentation séparé.
>
> **CE SPRINT NE PRODUIT PAS DE CODE.** Conception seule. Livrable unique :
> `data/code/CONCEPTION_COMPETITION_INTRAPLOT.md` (modèle proposé + décisions
> figées + découpage impl.), sur le modèle de `CONCEPTION_PLANTER_ARROSER.md` /
> `CONCEPTION_ECRASEMENT.md`.
>
> Règles projet : **moteur Python = source de vérité** ; **flux → contrainte →
> réponse émergente** (philo #2, jamais de bonus/malus direct) ; **pédagogie
> explicite** sur chaque choix ; **max 3 questions à la fois** en session ; ne
> rien créer d'autre sans « OK ». Ampleur conception : **petit/moyen** (les
> mécanismes de compétition existent **déjà** — voir §3 ; le sprint lève surtout
> un **verrou** et décide **comment l'éclaircissage résout**).

## 0. Cadrage (déjà tranché ailleurs — à intégrer dans la conception figée)

- **Empilement AUTORISÉ — c'est le but de CE sprint.** Q4 du sprint planter a été
  tranchée « EMPILEMENT AUTORISÉ » mais sa réalisation a été **renvoyée ici** :
  aujourd'hui une graine déposée sur un plot occupé **patiente**
  (`succession.py:64`), et la succession spontanée **saute** tout plot occupé
  (`succession.py:145`). Lever ce verrou = l'objet du sprint.
- **Le cœur écolo est touché → re-figeage golden MAÎTRISÉ attendu.** La
  germination tourne **dans le tick** (`succession`/`spring_flush` appelées par
  l'engine) ; relâcher le verrou fera germer des plots aujourd'hui exclus → le
  smoke test (2 tuiles × 4 ans) **dérivera** (plus de population). Dérive
  **localisée et annoncée**, pas un re-figeage muet (règle CLAUDE.md).
- **⚠️ Mécanisme à NE PAS inventer deux fois.** La **compétition est déjà
  émergente** dans le moteur (lumière asymétrique + uptake partagé, §3). Le
  risque du sprint est de **ré-empiler** un système de compétition redondant.
  Posture : **lever le verrou d'abord, MESURER ce que l'émergent produit, puis ne
  combler QUE les trous** (typiquement : un perdant qui stagne sans jamais mourir,
  et la densité intra-plot non comptée — §3, §5 Q3/Q4).

## 1. Pourquoi ce sprint, pourquoi maintenant

Le sprint planter/arroser vient de se clore (pont 0.3.3, commit `10e0f6b`). Il a
posé `planter` = **graine en attente** qui germe via la succession — mais sur
**plot libre seulement**. Tant que l'empilement n'est pas réalisé, deux semis ne
peuvent jamais se disputer une case : **une seule plante tente sa chance par
plot**. C'est une limitation structurelle qui bride à la fois la succession
spontanée (densité plafonnée artificiellement) et le geste `planter` (semer
dense = impossible).

La permaculture **vit** de cette compétition : on sème serré, le milieu
**éclaircit** (les vigoureux dominent, les chétifs fondent). C'est une des
leçons centrales du jeu (« ne pas semer serré dans un sol froid », déjà amorcée
par `damping_off`). La débloquer maintenant complète le modèle écologique avant
le packaging (t7).

## 2. L'intention (source de vérité du « quoi »)

- **Backlog** (`BACKLOG.md:42`) : « plusieurs plantes peuvent ESSAYER de pousser
  par plot, la compétition (lumière/eau/nutriments) fait l'**éclaircissage
  naturel** ».
- **Philo #2** (CLAUDE.md) : jamais de malus direct sur les plantes — **flux →
  contrainte écologique → réponse biologique émergente**. L'éclaircissage ne doit
  donc PAS être un « tirage du perdant » : il doit **émerger** de la rareté
  partagée (ombre, eau, nutriments) que les co-occupants se disputent.
- **Méthode scientifique** (philo #6) : semer dense est une **hypothèse** du
  joueur ; le milieu répond (certains lèvent, d'autres fondent) → observation →
  ajustement. Aucune densité n'est « interdite » ; c'est l'écosystème qui tranche.

→ Le « quoi » est posé. Ce sprint tranche le **« comment »** exact (les Q ci-dessous).

## 3. État du code vérifié (ancrages — 2026-06-13)

**Ce qui EXISTE déjà (la compétition est largement là) :**

- **Empilement déjà permis au niveau bas.** `world/tile.py:151 add_plant(cls,r,c)`
  crée une `PlantInstance` **sans vérifier l'occupation** (seulement `is_valid_plot`).
  Le verrou est donc **uniquement** dans la couche germination, pas dans le modèle
  de données. Plusieurs plantes peuvent coexister à la **même position**.
- **Compétition LUMIÈRE asymétrique — déjà émergente.** `fields/light.py:180
  light_received` ne filtre une plante que par ses **voisins PLUS HAUTS**
  (auto-ombrage exclu, tri hauteur décroissante). Conséquence : sur un plot
  partagé, **la plus haute ombre la plus basse** → `shade_memory` de la dominée
  monte (`engine.py:309`), sa photosynthèse/avancement chute. Dominance par la
  hauteur = déjà en place.
- **Compétition EAU/NUTRIMENTS — déjà émergente.** `engine.py:223 _apply_uptake`
  fait puiser chaque plante sur **toute son empreinte racinaire** `root_plots` ;
  deux empreintes qui se chevauchent **épuisent le même sol** (uptake séquentiel
  → le second trouve moins). `_apply_exudates` (`engine.py:252`) partage de même.
  La rareté souterraine partagée existe.
- **Détection de conflit — déjà câblée.** `world/tile.py:169 detect_conflicts`
  signale **2+ plantes vivantes partageant un plot** (couche `foliar` **ou**
  `root`) via `ConflictNotification`. **MAIS** : c'est **informatif seulement** —
  `resolved` n'est **jamais** positionné, **aucune mortalité de surpeuplement**
  n'en découle.
- **Mortalité densité-dépendante — existe, MAIS aveugle à l'intra-plot.**
  `sim/effects.py:349 _local_density` compte les plantes vivantes voisines via
  `plots_within_radius(r,c,1)` — qui **exclut le plot central** (`tile.py:131`).
  Donc **deux plantes sur la MÊME position ne se comptent pas** comme densité →
  `damping_off` (fonte des semis, `effects.py:363`), maladies fongiques et
  herbivorie **ne montent pas** entre co-occupants. **Trou** à combler (§5 Q4).

**Le verrou à lever (le seul) :**

- `sim/succession.py` — trois portes sautent les plots occupés **avant même** de
  calculer la niche :
  - `succession()` ligne 145 : `if (r,c) in occupied_roots: continue` + ligne 184
    `if any(p.position==(r,c) …): continue`.
  - `spring_flush()` ligne 226 : même skip `occupied_roots` + ligne 261.
  - `_lever_grains_en_attente()` ligne 64 : grain sur plot occupé → **patiente**
    (le « EMPILEMENT AUTORISÉ » de Q4 ne se réalise QUE quand on lève ceci).
- `occupied_roots` est bâti depuis `p.root_plots` + `p.position` de **toutes** les
  plantes vivantes (`succession.py:130`). La niche, elle, n'est calculée que sur
  plot libre aujourd'hui ; `niche_index` prend `root_density` = densité racinaire
  des **voisins** (`succession.py:152`) — **pas** l'occupation du plot lui-même.

**Contexte perf (à garder en tête, ne pas re-mesurer) :** D32 —
`LightField.compute` = **53 % du CPU**, coût **∝ surface de canopée**. Plus de
plantes co-germées = plus de canopée = plus cher. Un **cap** ou un **frein**
efficace n'est pas qu'esthétique : c'est aussi la perf (§5 Q2, §6).

## 4. Où ça atterrit dans la philosophie (pédagogie)

- L'éclaircissage **ne doit pas être codé comme un verdict** (« la plante X
  perd, on la tue »). Il doit **tomber** de la rareté partagée : la dominée reçoit
  moins de lumière (ombrée), boit dans un sol déjà épuisé, et — si serrée — subit
  davantage la fonte des semis / les maladies. Sa santé décline, elle meurt **par
  le système existant** (`_tick_senescence_health`, `engine.py:328`). C'est philo
  #2 jusqu'au bout : flux (lumière/eau) → contrainte (rareté) → réponse (déclin).
- **Semer dense devient une vraie décision** (pédagogie #6) : parfois payant
  (un survit, on a gagné du temps), parfois gâché (fonte des semis si sol froid &
  humide). Le joueur **apprend la densité de semis** par l'expérience, pas par une
  règle affichée — exactement la leçon de `damping_off`.
- **La cohabitation n'est pas que conflit** : multi-familles sur un plot = embryon
  de **guilde** (la base permaculture). Le sprint doit décider si l'intra-plot est
  seulement de la **rivalité** ou peut devenir de la **complémentarité** (§5 Q7).

## 5. Questions de conception à TRANCHER (le cœur du sprint)

> Chaque Q : **enjeu → options → reco** (penchant pédagogiquement justifié, **NON
> figé** — Nico tranche). À traiter par paquets de ≤ 3. Les sujets bio/éco sont
> présentés comme un **doc à étudier avec reco**, pas comme des arbitrages à froid.

### Paquet A — Lever le verrou (le geste structurant)
- **Q1 — Comment relâcher la porte de germination ?** Aujourd'hui les plots
  occupés sont **sautés avant** le calcul de niche (§3). Options : *(a)* supprimer
  le skip `occupied_roots` et **laisser la niche freiner** — mais `niche_index`
  regarde la densité des **voisins**, pas l'occupation du plot lui-même → il faut
  **injecter l'occupation du plot** comme un facteur baissant la niche (plot déjà
  raciné = niche basse = co-germination rare) ; *(b)* garder un skip mais **plafonné**
  (autoriser jusqu'à N plantes/plot, §Q2). *Reco : (a)* — relâcher le skip ET faire
  de l'occupation un **frein continu** dans la niche (pas une interdiction). C'est
  le plus « écologique » : un plot dense décourage la germination sans l'interdire,
  et ça réutilise la mécanique de niche existante.
- **Q2 — Cap dur du nombre de plantes par plot ?** Enjeu = perf (D32) + lisibilité
  visuelle (rendu Godot d'une pile illisible). Options : pas de cap (l'écologie
  borne seule) / cap dur (ex. 3–4 plantes/plot). *Reco : cap dur de sécurité*
  (perf + UX) **en plus** du frein écologique de Q1 — ceinture et bretelles, sans
  jamais que le cap soit la contrainte *visible* (l'écologie freine bien avant).
- **Q3 — L'émergent suffit-il à TUER le perdant, ou stagne-t-il ?** Enjeu : si la
  dominée se contente de stagner indéfiniment (ombrée mais vivante), il n'y a pas
  d'**éclaircissage**, juste un embouteillage permanent. *Reco : mesurer d'abord*
  (lever le verrou, simuler, observer si `_tick_senescence_health` finit par
  emporter les dominées). Si non → combler par Q4 (densité intra-plot), **pas** par
  une mort de surpeuplement ad hoc (qui violerait philo #2).

### Paquet B — L'éclaircissage (que la compétition RÉSOLVE, sans verdict)
- **Q4 — Compter les co-occupants dans `_local_density` ?** Enjeu : le **trou** du
  §3 — deux plantes même-position ne se comptent pas (centre exclu) → `damping_off`
  & maladies n'éclaircissent pas les semis serrés. Options : *(a)* inclure les
  co-occupants du plot central dans la densité → la **fonte des semis** devient le
  mécanisme naturel d'éclaircissage du semis serré (leçon permaculture directe) ;
  *(b)* laisser tel quel (compter seulement les voisins). *Reco : (a)* — c'est
  l'ajout le **plus émergent et le plus pédagogique**, et il réutilise un effet
  existant plutôt que d'en inventer un. À CALIBRER : poids d'un co-occupant vs un
  voisin (proposé chiffré en session).
- **Q5 — Asymétrie lumière : confirmer « le plus haut gagne ».** Aujourd'hui
  `light_received` donne l'avantage au plus haut (§3). Enjeu : est-ce le modèle
  voulu (dominance par la stature = réaliste) ou veut-on un avantage à
  l'**établi/ancien** (le premier levé) ? *Reco : garder « le plus haut gagne »*
  (déjà codé, réaliste, déterministe) ; l'antériorité joue **indirectement** (le
  premier levé est plus grand au moment où le second émerge).
- **Q6 — Graines plantées sur plot occupé : lèvent-elles maintenant ?** Aujourd'hui
  elles **patientent** (`succession.py:64`). Enjeu = c'est précisément le
  déblocage promis de Q4 (sprint planter). *Reco : OUI* — le grain lève même sur
  plot occupé, **sous le même frein de niche** que la succession (Q1). Semer dans
  un massif établi reste **possible mais peu probable** (niche basse) = réaliste.

### Paquet C — Diversité, golden & calibrage
- **Q7 — Plusieurs ESPÈCES/familles par plot, ou rivalité intra-spécifique seule ?**
  Enjeu : autorise-t-on la **polyculture émergente** (guilde) sur une case ?
  *Reco : aucune restriction d'espèce* — la cohabitation multi-familles est le
  cœur de la permaculture ; la complémentarité (ex. fixatrice d'azote sous une
  haute) émerge déjà des champs (fertilité, ombre). Pas de règle « une espèce par
  plot ».
- **Q8 — Re-figeage golden : périmètre de la dérive attendue.** Enjeu : la dérive
  doit être **localisée et expliquée** (plus de germinations → population plus
  dense), pas une dérive de comportement non-densité. *Reco : isoler le re-figeage*
  — vérifier que la dérive du hash s'explique **uniquement** par des germinations
  supplémentaires sur plots auparavant exclus (compter avant/après), l'annoncer
  dans le commit, re-figer maîtrisé.
- **Q9 — Calibrer le frein : combien de co-germinations en pratique ?** Enjeu :
  viser un éclaircissage **visible mais borné** (ni embouteillage, ni explosion
  perf D32). *Reco : caler le frein de niche (Q1) + le cap (Q2)* pour que, sur le
  golden, la densité augmente modérément (proposé chiffré en session, mesuré sur la
  simu). Le **rendu Godot** d'une pile (offsets visuels, profondeur) = volet vue
  ultérieur, hors scope conception.

## 6. Garanties (par construction)

- **Golden** : la germination est **dans le tick** → ce sprint **RE-FIGE le golden
  `7ee907d3…`** (dérive = population plus dense). **Re-figeage MAÎTRISÉ et annoncé**
  obligatoire : compter germinations avant/après, vérifier que la dérive s'explique
  **seulement** par l'empilement. Aucune autre mécanique de tick ne doit bouger.
- **Déterminisme** : on **réutilise les canaux de hash de germination existants**
  (`_hash_noise`, `succession.py`) — **aucun RNG neuf**. Lever le verrou ne doit
  pas introduire d'ordre non déterministe (itération plots déjà ordonnée).
- **Philo #2** : l'éclaircissage **émerge** (ombre + uptake partagé + densité) —
  **aucune mortalité « verdict »** ajoutée. La mort passe par
  `_tick_senescence_health` existant.
- **Perf (D32)** : le **frein de niche + cap** bornent la canopée totale → pas
  d'emballement du coût `LightField`.

## 7. Découpage pressenti de l'IMPL (à confirmer dans le kickoff d'impl, PAS ici)

Petit→moyen (peu de fichiers, mais cœur écolo). Probable : (1) **lever le verrou**
dans `succession.py` (skip `occupied_roots` → frein de niche + cap ; les 3 portes :
`succession`, `spring_flush`, `_lever_grains_en_attente`) — **golden RE-FIGÉ
maîtrisé**, tronçon le plus sensible, isolé ; (2) **densité intra-plot** dans
`_local_density` (`effects.py`) si Q3 montre que l'émergent ne tue pas — golden
re-figé maîtrisé ; (3) **tests** (co-germination effective, éclaircissage observé
sur N saisons, déterminisme byte-identique, cap respecté) + golden. Le **rendu
Godot** de la pile (offsets, lisibilité) = volet vue ultérieur.

## 8. Livrable & reprise

- **Livrable de CE sprint** : `data/code/CONCEPTION_COMPETITION_INTRAPLOT.md` —
  §1 intention (reprise §2), §2 modèle proposé (compétition émergente existante +
  les ajouts mappés sur le code §3), §3 **décisions FIGÉES** (Q1-Q9 tranchées par
  Nico), §4 découpage impl. Puis un kickoff d'implémentation autosuffisant (modèle
  `sprint_ecrasement_plantes.md`).
- **Reprise à froid** : « lis `sprints/sprint_competition_intraplot_conception.md` »
  (+ `sim/succession.py`, `sim/effects.py:349`, `fields/light.py:180`,
  `sim/engine.py:223` pour les ancrages ; `CONCEPTION_PLANTER_ARROSER.md` comme
  gabarit de structure de la conception figée).
