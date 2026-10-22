# ②bis Les branches meurent — ombre, météo, arbustes, bois mort initial

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (§② : la plomberie existe, mais 0 branche
tombe en pratique), conception §2.
**Golden** : RE-FIGÉ annoncé si un ligneux du smoke perd une branche (élagage par l'ombre ou
casse) ; sinon le constater inchangé. Une seule fois, en fin de tronçon, hash consigné.
**Accord Nico (2026-10-22)** : causes (a) ombre ET (b) météo ; arbustes ligneux inclus ;
bois mort présent dès l'état initial. Objectif : nourrir les champignons du bois (③④).

## Constat (vérifié par ②)
`sim/growth/phases.py::_elaguer` ne tue que le bois sans apex depuis `wood_persistence`
(4 000 sem. pour les arbres, `plants/perennials.py`) ou au-delà de `max_segments` (70-90,
jamais atteint) → 0 branche tombée sur 10 ans, 0 plot de bois sur `full` 104 sem. [n=1 run].
Le relais `grow_plant` → `tombes` → `sim/engine/decompo.py::deposer_bois_tombe` → litière
`bois` est en place et testé (`tests/test_bois_mort.py`) : il suffit de produire des `tombes`.

## A. Élagage naturel par l'ombre (cladoptose) — ligneux procéduraux
Écologie : une branche basse que la couronne prive de lumière coûte plus qu'elle ne
rapporte ; l'arbre la laisse mourir, elle sèche puis tombe. Un héliophile (bouleau, cerisier)
s'élague vite ; un sciaphile (hêtre, charme, if) garde ses branches basses longtemps.
- Intention : un sous-arbre LATÉRAL (jamais le collet ni l'axe porteur du leader) dont la
  lumière reçue reste sous un seuil pendant une durée D meurt et est renvoyé dans `tombes`.
  Seuil et D dérivés de la tolérance à l'ombre existante (`shade_tolerance_effective`,
  `phases.py`) — PAS de nouvelle donnée si celle-ci suffit.
- Proxy de lumière d'une branche : la lumière-sol au plot sous son extrémité
  (`sim/growth/geometrie.py::_light_at`, grille `LightField` qui intègre déjà l'ombre des
  voisins ET de la propre couronne) — à confirmer ou remplacer par mieux, à coût ≈ O(segments).
- Compté seulement en saison feuillée (un arbre défeuillé n'a pas de signal d'ombre).
- État « semaines à l'ombre » : préférer un calcul sans état (âge du segment + lumière
  courante) ; si un compteur par segment est indispensable, l'ajouter à `Segment`
  (`plants/base/stades.py`) AVEC `to_dict`/`from_dict` à défaut 0 (save JSON lisible).
- Cible [ordre de grandeur, à consigner avec n] : un arbre adulte (10 ans) laisse tomber
  quelques branches par an (2-6) ; un jeune arbre isolé en plein soleil, ~0.

## B. Casse par la météo — ligneux procéduraux
- **Tempête** : vent local spatialisé `eco.vent.at_plot` × pic de rafale × `eco.turbulence`
  (patron exact de `sim/engine/mortalite.py::_wind_damage`, qui ne vise aujourd'hui que les
  semis). Au-delà d'un seuil, casser k sous-arbres latéraux, k croissant avec la sévérité ;
  choix des branches DÉTERMINISTE (hash de bruit, jamais de RNG vivant), de préférence
  longues et fines (bras de levier). Un arbre abrité casse moins qu'un exposé (D104).
- **Neige / givre** : la charge casse surtout les persistants (feuillage gardé l'hiver :
  sapin, lierre…) et les longues portées. Lire l'état neige existant (`sim/weather.py`
  « Neige », manteau neigeux) — ne pas créer de nouvel aléa.
- Fragilité du bois = DONNÉE par espèce (bouleau, saule, peuplier, figuier fragiles ;
  chêne, charme, hêtre solides), constante de classe avec défaut neutre.
- Les branches cassées passent par le MÊME relais `tombes` → `deposer_bois_tombe`.
  Placement : là où `eco` et la météo du tick sont connus (couche `sim/engine`) ; la
  coupe structurelle elle-même reste une fonction PURE de `sim/growth` (pas d'`eco` dedans).

## C. Arbustes et sous-arbrisseaux ligneux (inclus, Nico)
- Le critère « ligneux » actuel (`sim/effects/perturbations.py::frac_bois_mort` =
  présence d'`age_curve`, donc `PerennialWoody` seul) exclut lierre (procédural mais
  `PlantBase`), framboisier, thym, lavande, myrtille et autres sous-arbrisseaux. Le
  remplacer par une DONNÉE d'espèce explicite (`ligneux`) posée sur tout le catalogue
  (vrais ligneux : arbres, arbustes, lierre, framboisier, thym, lavande, romarin, sauge,
  myrtille… — audit du catalogue, liste consignée dans `00_etat.md`). Effet voulu aussi à
  la mort : ces plantes laissent désormais un squelette de bois (`deposer_mort`).
- Ligneux SANS structure procédurale : chute de bois par une donnée d'espèce (masse
  annuelle de bois mort + saison de chute), déposée au plot de la plante. Biologie :
  framboisier = cannes de 2 ans qui meurent après fructification (fin d'été-automne) ;
  thym/lavande = bois sec à la base (hiver) ; myrtille = rameaux âgés. Masse ∝ taille/âge
  de la plante, calée sur `BOIS_MORT_PAR_CM3` pour rester du même ordre que les arbres.

## D. Bois mort dans l'état initial
- Config `full` (et `propre`, même fabrique) : dès la semaine 0, de la litière `bois`
  sous la couronne des ligneux existants (branches déjà tombées) et quelques pièces
  isolées (souche, branche) réparties DÉTERMINISTIQUEMENT (hash de la graine) sur les
  tuiles. Âges VARIÉS (pour que tous les stades de décomposition se voient au ⑧).
- Placement : la fabrique d'init (`tools/simserver/commands.py` config `full`, à côté du
  pré-vieillissement des fruitiers, ou `main.py::build_world_full`) — vérifier lequel est
  partagé par `full`/`propre` et ne PAS toucher la config `smoke` (golden).
- Le champ « âge du bois » exposé au pont par ② doit refléter ces âges.

## Mesure & vérif
- `mesures/bois_mort.py` (créé par ②) étendu : plots avec bois > 0 à sem. 0, 52, 104 ;
  branches tombées/an par cause (ombre / tempête / neige / arbuste) ; mycélium max/médian ;
  graine 1521550718, monde `full`, 104 sem. [n=1 run, à écrire]. Avant (②) : 0 plot, mycélium
  max 0,24.
- Tests : étendre `tests/test_bois_mort.py` (un sous-arbre ombragé finit par tomber ; un
  sous-arbre éclairé non ; la tempête casse plus l'exposé que l'abrité ; un arbuste non
  procédural dépose du bois ; init `full` contient du bois ; déterminisme 2 runs identiques).
- **Perf** : surcoût ≤ +5 % de tick par rapport à l'état après ② (D114 déjà ouverte,
  ne pas la résorber ici ; signaler si dépassé, sans brider).
- Pont : bump `version.py` seulement si le snapshot change.

## Ne PAS faire
Pas de C# (⑧). Pas de champignon (③). Pas de nouvel aléa météo. Pas de RNG vivant.
Pas de test 500 ans.
