# Maîtrise — §10 · Taxonomie des objets de maîtrise (D12.3)

> Partie 3/3 de la conception des paliers de maîtrise. Index :
> [`../CONCEPTION_MAITRISE.md`](../CONCEPTION_MAITRISE.md).
> Amont : [`01_modele.md`](01_modele.md) (le modèle),
> [`02_succes_par_axe.md`](02_succes_par_axe.md) (le succès, D12.1).

> **Sous-sprint D12.3 (2026-06-04), conception seule.** Remplit le point §8.3.
> Précédé d'une **lecture des catalogues moteur** (le point de vigilance acté) : la
> taxonomie **reflète** `plants/` (espèces) + `sim/actions.py` &
> `CONCEPTION_VIGUEUR.md` §3.2/§3.3 (actions) — elle n'invente **aucun** catalogue
> parallèle. Reste ouvert : le **câblage** des objets outil/structure/technique
> (n'existent pas encore dans le moteur → sprints d'action D29/D30/D31) ; les Nᵢ et
> atténuations → calibrage D12.4.

## 10.0 Le pivot — la taxonomie reflète les catalogues, n'en crée pas

Deux catalogues réels existent déjà ; D12.3 ne fait que les **déclarer comme
objets de maîtrise** sans dupliquer leur contenu :

- **Espèces** — `plants/catalogue.py` (`PLANT_CATALOGUE` + `PERENNIAL_CATALOGUE`) :
  **17 espèces** réparties sur **11 familles** botaniques.
- **Actions** — `sim/actions.py` (4 gestes codés sur le vivant) + le catalogue
  *conçu* de `CONCEPTION_VIGUEUR.md` §3.2 (milieu) / §3.3 (vivant) / §3.4
  (ressourcement).

Les catégories **outil / structure / technique** (§1) **n'ont aucun support
moteur** (seuls 4 gestes sur le vivant sont codés). D12.3 les **déclare** comme
objets de maîtrise — patron §9.5 — mais leur **câblage** suit les sprints qui les
introduiront (D29 taille/auxine, D30 structure du sol, D31 vie macroscopique, +
sprints d'action-milieu). **Déclarer ≠ câbler** : la structure data les accueille
(§0), le moteur les remplira plus tard.

## 10.1 Catégorie « être vivant » — le catalogue d'espèces actuel

| Famille | Espèces (clé catalogue) | Spillover §3.1 |
|---|---|---|
| **Solanaceae** | tomate, poivron | ✅ (≥2 espèces) |
| **Fabaceae** | haricot, trèfle, minette | ✅ |
| **Asteraceae** | tournesol, achillée, pissenlit | ✅ |
| **Rosaceae** | pommier, cerisier | ✅ |
| Lamiaceae | basilic | — (singleton) |
| Poaceae | pâturin | — |
| Boraginaceae | phacélie | — |
| Brassicaceae | bourse_pasteur | — |
| Moraceae | figuier | — |
| Juglandaceae | noyer | — |
| Fagaceae | chêne | — |

**Le spillover est data-driven sur la famille réelle, pas sur une liste figée.**
Les 5 familles « cœur » de `plants/base.py` (Solanaceae, Fabaceae, Asteraceae,
Lamiaceae, Poaceae) **ne sont pas privilégiées** : Rosaceae (deux arbres) spille
exactement comme Solanaceae. Une famille ne **spille** qu'à partir de **2 espèces
découvertes** ; les singletons actuels attendent que le catalogue grossisse
(D23/D26) — ils rejoindront le spillover **sans toucher la structure** (tout le
sens du pivot §0). Les adventices (bourse, minette, pâturin, pissenlit) sont des
objets de maîtrise au même titre : **on peut maîtriser une pionnière**.

> D31 ajoutera **auxiliaires / nuisibles** comme objets « être vivant » quand ils
> auront une vitalité propre (cf. §7). Leur regroupement (ordre, guilde) — support
> d'un éventuel spillover — sera fixé alors.

## 10.2 Catégorie « concept transversal »

Six concepts (les mêmes qu'en §1/§9.3), chacun objet de maîtrise à part entière :

> **météo/climat · sol/microbiome · eau · lumière · succession · pollinisation**

Leur **succès** est déjà défini (§9.3). Ils alimentent **les deux mesures
globales** (§3.2) **et** le **terme global** de `cout_action` (§10.4, terme 1) —
**jamais** le terme par-objet : la connaissance écologique est **holistique**
(mieux comprendre l'eau allège *un peu toute* action, pas seulement « arroser »).

## 10.3 Catégories « outil / structure / technique » — déclarées, non câblées

Inventaire **dérivé des actions** de `CONCEPTION_VIGUEUR.md` §3.2/§3.3 (rien
d'inventé hors du catalogue d'actions) :

- **Outils** — *geste qualifié, l'objet qui rend le geste précis* :
  arrosoir, grelinette, bêche, sécateur.
- **Structures** — *aménagement persistant, prouve sa fonction pendant un stress
  (§9.5)* : tuteur, voile d'hivernage, brise-vent, treillis/palissage, serre,
  aménagement-habitat (hôtel à insectes / nichoir / point d'eau / bande fleurie).
- **Techniques / gestes** — *savoir-faire, son issue émergente prouve la maîtrise
  (§9.5)* : semis, arrosage, paillage, amendement, pose-structure,
  bouturage/division/marcottage, drainage, inoculation, aménagement-habitat,
  ameublissement (grelinette), bêchage, récolte, arrachage, **taille**.

Aucun de ces objets n'a d'état moteur aujourd'hui. Ils sont **déclarés** ici pour
que `cout_action` (§10.4) puisse les **nommer** ; le **niveau** de chacun ne
montera que lorsque le sprint correspondant câblera son succès (§9.5).

## 10.4 La donnée que lit `cout_action` — objets touchés par action

Livrable central de D12.3 : pour **chaque action**, la liste d'objets que
`cout_action(player, action, objets_touches)` lit (§4.2).

**Rappel du modèle (§4.2), précisé ici :**

- **Terme 1 — global** `f_globale(player)` : agrégat de **tous** les concepts +
  êtres vivants découverts (la « connaissance écologique générale »). Allège
  **uniformément** toute action. *Les concepts vivent ici, jamais dans le terme 2.*
- **Terme 2 — par-objet** `f_objets(player, objets_touches)` : maîtrise des objets
  **concrets** que CE geste manipule. **Décision D12.3** — le terme 2 est l'union :
  1. **la technique** que l'action incarne (toujours — tout geste qualifié est une
     technique qui s'affûte) ;
  2. **l'être vivant cible** s'il y en a un (→ **spillover famille** §3.1) ;
  3. **l'outil** si le geste en requiert un ;
  4. **la structure** si le geste en pose / emploie une.

> **Réconciliation avec l'exemple §4.2.** Cet exemple (`tailler(framboisier)` lit
> `framboisier + sécateur + global`) était *pré-taxonomie* et son espèce
> (framboisier, Rubus/Rosaceae) est **illustrative** (hors catalogue actuel).
> D12.3 le **raffine** en honorant les catégories §1 : l'**outil** (sécateur) et
> la **technique** (taille) sont **deux objets distincts** — maîtriser le sécateur
> (précision du geste) n'est pas maîtriser *quand/comment* tailler. `tailler` lit
> donc `{taille, sécateur, espèce(→famille), global}`.

**Table des objets touchés** (— = aucun ; *cursive* = objet pas encore câblé côté
moteur ; les **espèces** existent déjà au catalogue, donc non cursivées) :

| Action (phase) | Technique | Outil | Structure | Cible vivante (→ famille) |
|---|---|---|---|---|
| **semer / planter** (planif.) | *semis* | — | — | espèce semée |
| **arroser** (saison) | *arrosage* | *arrosoir* | — | — (agit sur `humidite`) |
| **pailler / mulcher** (planif.) | *paillage* | — | — | — |
| **amender** (planif.) | *amendement* | — | — | — |
| **poser une structure** (planif.) | *pose-structure* | — | *voile / brise-vent / tuteur / serre…* | — |
| **multiplier végét.** (planif.) | *bouturage / division / marcottage* | — | — | pied-mère |
| **drainer** (planif. / saison) | *drainage* | — | — | — |
| **inoculer** (planif.) | *inoculation* | — | — | — |
| **favoriser un auxiliaire** (planif.) | *aménagement-habitat* | — | *hôtel / nichoir / point d'eau* | — (*futur auxiliaire, D31*) |
| **grelinette** (planif.) | *ameublissement* | *grelinette* | — | — |
| **biner / bêcher** (planif.) | *bêchage* | *bêche* | — | — |
| **récolter** (—) | *récolte* | *sécateur* (opt.) | — | espèce récoltée |
| **tailler / éclaircir** (—) | *taille* | sécateur | — | espèce taillée |
| **déraciner** (—) | *arrachage* | *bêche* (opt.) | — | espèce |
| **écraser** un nuisible (saison) | — *(geste brut, peu d'affût)* | — | — | *nuisible (D31)* |
| **manger** (—) | — *(coût NUL → §10.5)* | — | — | espèce (organe) |
| **méditer / observer** (—) | — | — | — | — *(coût NUL, jamais taxé)* |

Les actions **sur le milieu** n'ont **pas de cible vivante** (philo #2 : on agit
sur un champ, la plante répond par émergence) — leur terme 2 se réduit à
technique (+ outil / structure). Les actions **sur le vivant** ajoutent l'espèce
ciblée → **spillover famille gratuit** (§4.2 : pratiquer la taille du cerisier
fait monter *l'objet cerisier* → tailler / récolter / bouturer le cerisier **et**
le pommier (Rosaceae) deviennent moins chers).

## 10.5 Implications & ce qui reste

- **Actions gratuites / triviales** : `observer` et `méditer` (coût NUL, §3.4) et
  `manger` (coût NUL, §3.3) → `cout_action` renvoie 0, terme 2 **vide** : aucune
  technique à lire (rien à alléger). Elles restent objets de **découverte** (voir
  une espèce qu'on mange l'inscrit, §2.1), mais ne portent pas de technique.
- **C'est une donnée, pas un calibrage.** La table fixe *quels* objets chaque
  action lit ; *combien* chaque maîtrise allège (atténuations) et les Nᵢ → **D12.4**
  (post-test).
- **Extensible sans toucher la structure** (§0) : une espèce ajoutée (D23/D26)
  rejoint « être vivant » et sa famille ; un outil / une structure introduit(e) par
  un sprint d'action rejoint sa catégorie et se **branche** sur les actions
  concernées via cette même table. La taxonomie **grandit en largeur**, le modèle
  ne bouge pas.
- **Câblage & dégradation gracieuse** : transformer les objets *en cursive* en
  objets à niveau réel suit les sprints qui les introduisent (D29 taille, D30
  structure du sol, D31 auxiliaires/nuisibles, + sprints d'action-milieu). Jusque-là
  `cout_action` peut déjà **lire** les espèces et concepts réels (terme 1 + cible
  vivante) ; les termes outil / structure / technique restent **neutres (1.0)** tant
  qu'ils ne sont pas câblés.
