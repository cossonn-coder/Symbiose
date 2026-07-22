# CONCEPTION — Décomposition & Compost (parcelles de litière, squelettes, bac & pile, organes-fruits)

> **Statut : conception FIGÉE (2026-06-13, 4 rounds de design tranchés par Nico).**
> Prête pour l'implémentation. Sprint **GROS** → découpé en **6 sous-sprints
> indépendants** (§7). Fait suite à la gravure backlog « Sprint décomposition &
> compost » (2026-06-11, retour F5 t4). Relève majoritairement du **canal
> vertueux** (philo #1 : le joueur agit sur le MILIEU) ; les nouveaux gestes
> (composter, empiler, retourner, épandre) sont **bon marché**.
>
> **Re-figeage golden ANNONCÉ et LARGE** : ce sprint **remplace le champ
> scalaire `om_fresh`** par un modèle de **parcelles de litière** → re-figeage
> golden écolo **et** population (les vers lisent `om_fresh`), maîtrisé et
> documenté (§7). On en **profite pour raccourcir le smoke test** (trop long).
>
> **Absorbe la dette D19** (organes comestibles : un fruit traçable, mangeable,
> qui se déplète) et une partie de **D33** (état d'organe réel ≠ proxy de rendu).

---

## 0. L'intention (source de vérité du « quoi »)

Vision Nico (2026-06-13) : *« toute matière organique taillée doit être en
décomposition. Composter récupère la matière fraîche au pied d'un plot et la met
au bac. À l'automne les feuilles mortes sont au sol et servent d'OM. Toute plante
en sénescence, et les fleurs / feuilles / fruits qui vont au sol, servent d'OM.
Leur temps de compostage dépend de leur constitution : une feuille se décompose
plus vite que du bois, un fruit se décompose vite et attire des animaux. »*

Principe **non négociable** (philo #2) : aucune action ne touche la plante
directement par un bonus/malus ; elle modifie un **champ / un dépôt**, et la
réponse (microbes, vers, faune, succession) est **émergente** au tick suivant.

---

## 1. Modèle de parcelles de litière (remplace `om_fresh`)

### 1.1 Structure de données

La couche « fraîche » scalaire `om_fresh` (`fields/ecofields.py`) **disparaît
comme champ propre**. Chaque plot porte une **liste de parcelles** :

```
parcelle = { tissu: str, masse: float, age_sem: float }
plot(r, c).litiere : list[parcelle]
```

- **Fusion par tissu** (bornage déterministe, obligatoire) : au sein d'un plot,
  deux dépôts de **même `tissu`** fusionnent → `masse += masse`, `age_sem` =
  moyenne pondérée par la masse. Le nombre de parcelles par plot est donc borné
  par le **nombre de classes de tissu** (≤ 6), pas par le nombre de dépôts.
- **Granularité spatiale = plot** `(r, c)` (comme toute la chimie du sol). Un
  jitter de position est **purement cosmétique** (vue), jamais simulé.
- **`om_fresh` survit en LECTURE dérivée** : `om_fresh_at(r,c) = Σ masse` des
  parcelles du plot. Les lecteurs actuels (famine microbienne, vers, vitalité,
  snapshot, effet `inject_field om_fresh` des espèces) lisent cette somme → ils
  **continuent de marcher** sans changer de sémantique d'appel.

### 1.2 Taxonomie des tissus (constitution) — FIGÉE §1

| `tissu` | source | décompo (base/sem) | humifie→`om_active` | minéralise→`fertilite` |
|---|---|---:|---:|---:|
| `diffus`  | exsudats racinaires, fine racine (**parcelle permanente/plot**) | **très rapide** (~0.50) | faible (0.15) | fort (0.55) |
| `feuille` | abscission d'automne, mort des caducs | rapide (~0.25) | moyen (0.30) | fort (0.45) |
| `fleur`   | fleurs fanées tombées | rapide (~0.30) | faible (0.20) | fort (0.50) |
| `herbacé` | tiges molles, annuelles mortes, engrais vert, résidus de récolte | moyen (~0.15) | moyen (0.35) | moyen (0.35) |
| `fruit`   | fruits non récoltés tombés | rapide (~0.28) **+ signal animal (§4)** | faible (0.20) | fort (0.50) |
| `bois`    | taille de branches, squelette qui se fragmente | **très lent** (~0.02) | **fort (0.55, → humus)** | faible (0.10) |

> Valeurs **proposées, calibrage post-test** (placeholders, comme tous les docs
> conception). Le reste de chaque ligne (1 − humif − miner) est **respiré** (CO₂,
> perte nette — aucune création de matière, principe conservé du modèle v4).
> Idée directrice validée : `bois` **humifie fort vers l'humus** (structure du
> sol à long terme) ; `feuille`/`fruit`/`diffus` **minéralisent fort** (nutriments
> vite disponibles). C'est la pédagogie du « bois = structure, tendre = engrais ».

### 1.3 Cascade conservée

`om_active` (réserve) et `om_stable` (humus) **restent des champs scalaires**.
Les parcelles **sont** la nouvelle couche fraîche : chaque semaine, chaque
parcelle décompose `d = masse × base(tissu) × vitesse_micro × bonus_vers`
(la modulation microbiome + vers de `tick_decomposition` est **réutilisée**) ;
`d` se répartit humification (→ `om_active`), minéralisation (→ `fertilite`),
respiration (perdue) ; `masse -= d`, `age_sem += 1`. Une parcelle vidée (masse
≈ 0) est retirée (sauf la `diffus` permanente, qui peut tomber à 0 sans
disparaître).

La suite de la cascade (`om_active → om_stable → fertilite`, lessivage) est
**inchangée**.

### 1.4 Sémantique « famine microbienne » redéfinie (FIGÉE §6)

Aujourd'hui `famine = 1 − min(1, om_fresh / MICROBE_FOOD_REF)`. La parcelle
`diffus` **permanente** (exsudats là où des racines sont actives) garantit un
fond de carbone frais dans la rhizosphère. La formule est **conservée** avec
`om_fresh` = somme dérivée → la famine devient « microbes affamés là où **rien
ne pousse ni ne se décompose** » (pas de racines actives → pas d'exsudats → pas
de litière). Plus réaliste, et c'est l'unique changement de sens assumé.

### 1.5 Recâblage (rayon de souffle, à traiter au sous-sprint ①)

Lecteurs/écrivains de `om_fresh` à rerouter vers les parcelles :
- **Écrivains** → deviennent des **dépôts de parcelle** : `add_necromass`
  (mort/récolte, `engine.py`), exsudats (`EXUDATE_OM_SHARE`, `ecofields.py`),
  `inject_field om_fresh` des espèces (`plants/species.py` — engrais vert /
  paillage → parcelle `herbacé` ou `feuille`).
- **Lecteurs** → lisent la somme dérivée : famine microbienne, vers
  (`fields/population.py` : `om_fresh + om_active`), `vitalite()`, snapshot
  (`sim_server.py` expose `om_fresh` moyen + le **détail des parcelles**).

---

## 2. Dépôts — qui crée des parcelles

### 2.1 `tailler` dépose enfin (le point de départ de Nico)

Aujourd'hui `sim/actions.py:tailler` retire le sous-arbre via `atteindre_segment`
mais **ne dépose RIEN** (la masse coupée disparaît). Désormais : la masse du
sous-arbre coupé (∝ longueur/diamètre des segments retirés) **dépose une
parcelle `bois`** au plot. Le gain Vigueur du joueur (∝ maturité de l'organe
récupéré) est **inchangé** — on récupère ET on rend au sol.

### 2.2 Mort → **squelette persistant** qui se fragmente (FIGÉE round 2)

La structure procédurale **survit à la mort**. Nouvel état post-mortem de la
`PlantInstance` (ou drapeau `morte` + `stade_mort`) :

1. **`sèche`** (debout) : feuillage/organes mous **déposés immédiatement** en
   parcelles `feuille`/`fruit`/`fleur` ; ombre = **silhouette de bois nu**
   (ombre dégressive, §racines/lumière) ; **n'occupe PAS le plot** → la
   succession peut germer dessous (trouée de lumière, habitat — lien
   `CONCEPTION_COMPETITION_INTRAPLOT.md`).
2. **`couchée`** : après `T_seche` semaines, la structure tombe au sol (ombre ≈ 0).
3. **Fragmentation** : chaque semaine le squelette libère une fraction de sa
   masse de bois → parcelle `bois` au plot (vitesse ∝ décompo `bois`, modulée
   microbiome/vers). Squelette épuisé → plante retirée.

> Remplace le dépôt instantané `add_necromass(∝ hauteur)` actuel (`engine.py`
> aux ~6 sites de mort : sénescence, annual, bisannuel, compétition, dégâts).
> Le **bois** sort lentement (réaliste, et nourrit le sol sur des saisons) ; les
> **tissus mous** sortent vite. La hauteur reste le proxy de masse totale.

### 2.3 Abscission d'automne (événement saisonnier, FIGÉE round 2)

À l'**automne**, les plantes **caduques** (`deciduous`, `plants/base.py`)
larguent leur feuillage sur 1–2 semaines → parcelle `feuille` (masse ∝ proxy
`foliage_density_at × hauteur/canopée`). Les **persistants** gardent. Lisible et
saisonnier, peu de calcul.

### 2.4 Chute des fruits / fleurs non cueillis

Un **fruit** à maturité dépassée non récolté **tombe** → parcelle `fruit`
(fermentation, §4). Une **fleur** fanée tombe → parcelle `fleur`. (Le suivi
par-organe vient de §3.)

### 2.5 Écraser un mort → le met au sol (FIGÉE round 5, ajout Nico)

`sim/actions.py:ecraser_plante` appliqué à un **squelette** (`sèche` debout) le
**pousse au sol** (force le passage `sèche → couchée`) et **accélère sa
fragmentation**. Geste cohérent avec l'écrasement du vivant (même seam, philo #1).

---

## 3. Organes-fruits traçables (absorbe D19 ; ajout Nico round 4)

Les fruits cessent d'être un **proxy de rendu saisonnier** (`REPRO_BY_SEASON`
dans `tools/render_structure.py`) : ils deviennent un **état réel** porté par la
plante.

### 3.1 Modèle d'organe

```
fruit = { segment_id: int, maturite: float (0→1), masse: float }
```

- Apparaît aux sites reproducteurs (`organ_site` du profil d'espèce) en saison,
  **mûrit** semaine après semaine (`maturite` ↑ jusqu'à 1, puis sur-maturité).
- **Exposé au snapshot** (`sim_server.py`) → la **vue affiche la maturité**
  (couleur/taille du sprite — §6). Remplace/complète le hint `organ` du
  protocole 0.2.2.

### 3.2 `manger` ciblé (FIGÉE, ajout Nico)

`sim/actions.py:manger` cible **un fruit précis** (désigné à la souris, comme
`tailler` au segment, tranche 5) :
- **gain Vigueur ∝ `maturite` DU FRUIT** (un fruit vert nourrit peu, un mûr
  beaucoup ; un blet décline) — au lieu de la maturité globale de la plante ;
- **le fruit DISPARAÎT de la plante** (déplétion réelle — c'est exactement D19).

### 3.3 Cueillir vs laisser fermenter

Un fruit non cueilli, sa `maturite` dépassant 1, **tombe** (§2.4) → parcelle
`fruit` → fermentation (§4). **La cueillette est récompensée, la fermentation
pénalisée** (philo : le raccourci « je laisse tout au sol » s'use).

---

## 4. Attraction animale (succession sur le fruit ; FIGÉE round 3)

Une parcelle `fruit` émet un **signal selon son `age_sem`** (succession sur le
fruit), couplé aux 4 guildes existantes (`fields/population.py`, modèle
`CONCEPTION_VIE_MACRO.md` — **aucune 5ᵉ guilde**, trop lourd) :

- **Fruit frais tombé** → gonfle localement **`auxiliaire`** (frugivores,
  oiseaux : le verger nourrit la faune utile).
- **Fruit avancé / pourri** → gonfle **`ravageur`** (charognards, mouches) en
  **dominant** (pénalité de fermentation, incite à cueillir) **+ une petite
  fraction `auxiliaire`** (les *auxiliaires de décomposition* — cloportes,
  coléoptères : la décompo n'est jamais pur déchet). **Modélisation tranchée
  (Nico)** : pas de sous-guilde dédiée, juste cette fraction `auxiliaire` en
  plus du `ravageur`.

### 4.1 La pile à bois attire aussi (ajout Nico round 5)

La **pile à bois** (§5) est un **habitat persistant** (hôtels à insectes,
abris) → gonfle `auxiliaire` autour d'elle, comme la rondelle habitat de
`favoriser_auxiliaire`. La permaculture « le bois mort héberge la vie utile ».

---

## 5. Structures posables & boucle du joueur

Deux structures posées par le joueur (comme la rondelle habitat) :

| Structure | Accepte | Cinétique | Produit | Bonus annexe |
|---|---|---|---|---|
| **Bac à compost** | matière **tendre** (`feuille`/`fleur`/`herbacé`/`fruit`/`diffus`) — **refuse le `bois`** | **hybride** : mûrit seul (∝ constitution), `retourner` accélère | **compost mûr** (jauge mesurée) | — |
| **Pile à bois** | **`bois`** uniquement (BRF / hügelkultur) | **très lente** | **amendement bois** (humus forestier, biais structure) | **habitat `auxiliaire`** (§4.1) |

### 5.1 Gestes nouveaux

| Geste | Phase | Effet | Coût |
|---|---|---|---|
| `poser_bac` / `poser_pile` | **planification** (temps figé) | place la structure | `MODÉRÉ` |
| `composter(plot → bac)` | courant | déplace les parcelles **tendres** du plot vers le bac | `FAIBLE` |
| `empiler_bois(plot → pile)` | courant | déplace les parcelles **`bois`** du plot vers la pile | `FAIBLE` |
| `retourner(bac)` | courant | **accélère + homogénéise** la maturation (optionnel, récompense la maîtrise) | `FAIBLE`–`MODÉRÉ` |
| `epandre(bac → plot)` | courant | dépose du **compost mûr** sur un plot → **trio humus** | `FAIBLE` |

> **Aucune corvée punitive** (philo) : le bac **mûrit seul**, jamais bloqué ;
> `retourner` est un **bonus**, pas une obligation. Ce sont des actions sur le
> milieu → **bon marché** (le canal vertueux doit être le moins coûteux).

### 5.2 Maturation hybride (FIGÉE round 4)

Le bac mûrit passivement à une vitesse ∝ constitution moyenne de son contenu
(tendre vite, mélange plus lent) ; `retourner` multiplie la vitesse et lisse les
âges. Le contenu mûr s'accumule dans une **jauge `compost_mur`** (quantité
mesurée).

### 5.3 Épandage borné (FIGÉE round 5, ajout Nico)

`epandre` lit la **jauge `compost_mur`** : on **ne peut pas épandre plus que le
disponible** (la quantité est mesurée et affichée). Effet sur le plot ciblé =
**trio humus** : `+om_stable` (structure/rétention/mémoire), **ensemence
`microbiome`** (vie microbienne du tas), `+` un peu de `fertilite`. C'est un
**amendement complet**, pas un engrais. La **pile à bois** produit le même type
d'amendement, **biaisé structure** (`om_stable`) et plus lent.

---

## 6. Vue — états post-mortem & maturité (conçue ici, rendue quand Godot reprend)

> Non implémentable/testable tant que l'intégration Godot est en pause (décision
> Nico). On **conçoit**, on rendra plus tard, **on ajustera au besoin**.

- **Squelette** : `sèche` (debout, silhouette de bois nu) → `couchée` (au sol) →
  fragmentation. Le tronc/branches restent un **indice visible des semaines**.
- **Litière** : les parcelles au sol = litière rendue (tas par tissu, teinte par
  constitution ; feuilles d'automne lisibles).
- **Maturité-fruit à l'écran** : couleur/taille du fruit ∝ `maturite` (vert →
  mûr → blet) → le joueur **voit** quand cueillir.
- **Structures** : bac (jauge de compost mûr visible), pile à bois (sprites
  d'auxiliaires autour = habitat).

---

## 7. Coûts golden & découpage en 6 sous-sprints indépendants

**Re-figeage golden ANNONCÉ** : remplacer `om_fresh` par les parcelles touche
`tick_decomposition`, `add_necromass`, les ~6 sites de mort, les exsudats, les
injections d'espèces, et la population (vers). → **golden écolo ET golden de
population re-figés**, maîtrisés et expliqués. **On en profite pour RACCOURCIR le
smoke test** (`tests/test_golden.py`, aujourd'hui 2 tuiles × 4 ans = trop long)
— dérive localisée, annoncée.

| # | Sous-sprint | Contenu | Golden |
|---|---|---|---|
| ① | **Parcelles + cascade** | structure parcelle, fusion/bornage, `om_fresh` dérivé, parcelle `diffus`/exsudats, recâblage des lecteurs, famine redéfinie. **Raccourcir le smoke test.** | **re-figé + raccourci** |
| ② | **Dépôts vivant & mort** | `tailler`→`bois` ; mort→**squelette persistant** + fragmentation ; abscission d'automne ; `ecraser`-squelette→au sol | re-figé (morts) |
| ③ | **Organes-fruits traçables** | maturité par fruit, snapshot, `manger` ciblé (disparition), chute des non-cueillis *(absorbe D19)* | re-figé localisé |
| ④ | **Attraction animale** | fruit frais→`auxiliaire`, avancé→`ravageur`+frac. `auxiliaire` ; pile à bois→habitat | re-figé (population) |
| ⑤ | **Structures + gestes** | `poser`/`composter`/`empiler`/`retourner`/`epandre`, maturation hybride, jauge bornée, amendements bac & pile | event-driven (golden ~intact) |
| ⑥ | **Vue** *(Godot repris)* | post-mortem visible, litière, maturité-fruit, structures | — |

Chaque sous-sprint est une **unité testable** qui préserve (ou re-fige de façon
**maîtrisée**) le golden. Boucle CLAUDE.md : `0N` → travailler → vérifier/re-figer
golden → `00_etat.md` → commit → `/clear` → `0N+1`.

---

## 8. Philosophie & garde-fous

- **Philo #1** (agir sur le milieu) : composter/empiler/épandre sont le **canal
  vertueux bon marché** ; déraciner/écraser restent coûteux.
- **Philo #2** (émergence) : un dépôt modifie un **champ/une parcelle**, jamais
  la plante ; microbes, vers, faune, succession **répondent au tick suivant**.
- **Philo #4** (le sol porte la mémoire) : la litière → humus (`om_stable`) fait
  **grandir le sol** ; le bois mort héberge la vie.
- **Philo #6** (apprentissage diffus) : laisser pourrir les fruits → nuisibles ;
  cueillir & composter → sol vivant. **La conséquence enseigne, sans sermon.**
- **Déterminisme** (philo #3) : fusion de parcelles à ordre stable, pas de
  `Random` — golden reproductible.

---

## Annexe — knobs de calibrage (placeholders, post-test)

- `DECAY_BASE[tissu]`, `HUMIF[tissu]`, `MINER[tissu]` (table §1.2)
- `T_SECHE` (sèche→couchée), `FRAG_RATE` (fragmentation du squelette)
- abscission : fenêtre d'automne, masse ∝ proxy feuillage
- fruit : vitesse de maturation, seuil de chute (sur-maturité), seuils de
  signal `auxiliaire`/`ravageur` selon `age_sem`
- bac : vitesse passive ∝ constitution, multiplicateur `retourner`, rendement
  `compost_mur` ; pile à bois : vitesse, rendement, rayon d'habitat
- `epandre` : poids du trio (`om_stable` / `microbiome` / `fertilite`)
- coûts Vigueur des nouveaux gestes (`sim/actions.py:COUTS`)
- **golden** : nouvelle durée du smoke test (proposer 2 tuiles × **2 ans**)
