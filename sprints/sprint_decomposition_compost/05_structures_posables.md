# Sous-sprint ⑤ — Structures posables & gestes : bac à compost, pile à bois, le canal vertueux du joueur

> **Kickoff autosuffisant (démarrage à froid).** Lire d'abord `00_etat.md`
> (§Acquis ①②③④) et `data/code/CONCEPTION_DECOMPOSITION_COMPOST.md` (**§5**
> surtout, + **§4.1** pile à bois → habitat, + §7 ligne ⑤, + §8 philo #1/#4/#6).
> ① a transformé la litière en **parcelles `{tissu, masse, age_sem}` par plot**
> (`eco.litiere`, fusion par tissu → au plus **une parcelle par tissu et par
> plot**) ; ②–④ ont rempli ces parcelles (taille→`bois`, mort→`herbace`/`feuille`,
> abscission, chute des fruits) et branché la faune (④ : fruit→guildes). ⑤ donne
> au joueur les **deux structures posables** qui ferment la boucle : déplacer la
> litière du sol vers un **bac à compost** (tendre) ou une **pile à bois**, la
> laisser mûrir, puis **épandre** l'amendement obtenu → **trio humus** sur un
> plot. C'est le **canal vertueux bon marché** (philo #1) : composter coûte
> `FAIBLE`, déraciner/écraser restent `MODÉRÉ`. ⑤ **n'implémente aucun rendu
> Godot** (⑥, intégration en pause) : on conçoit l'état moteur + le pont, la vue
> viendra.

> ## ⏩ AVANCEMENT — reprise à froid
> **Phases A+B FAITES (2026-06-15)** : A = modèle `Structure`/`eco.structures` +
> gestes `poser_bac`/`poser_pile`/`composter`/`empiler_bois` ; B = `tick_structures`
> (maturation confinée ∝ `TISSU.decay`, jauge `compost_mur`, masse qui fond) +
> geste `retourner` (drapeau `retourne_restant`, ×2 vitesse + lissage d'âges) +
> appel étape 4b dans `engine.py`. `test_structures.py` (48/48), **golden NEUTRE
> prouvé** (`908f591bee…`/`435e6f72…`). Décisions #1, #2, ⑤A et #3-volet-B figées.
> Détail dans `00_etat.md` §Acquis ⑤ Phase A & Phase B. **➡️ COMMENCER ICI = PHASE
> C** (`epandre` trio humus borné + amendement pile + pile→habitat + pont 0.3.5).
> Décision #3 (volets trio/habitat) à figer au début de C.

## Ampleur & risque (à lire avant de coder)
Sous-sprint **MOYEN à GROS** (le plus gros de la série après ①) : un **état
moteur neuf** (les structures et leur contenu), **5 gestes** nouveaux, une
**maturation** qui tick chaque semaine, une **jauge bornée**, deux types
d'amendement, et le **hook habitat de la pile** (§4.1, reporté de ④). Pour ne pas
tout brasser d'un coup, **découper en 3 phases internes** (modèle ② A/B/C),
chacune testable et préservant le golden :

| Phase | Contenu | Golden attendu |
|---|---|---|
| ~~**A**~~ ✅ | **Modèle de structure** (`eco.structures`) + `poser_bac`/`poser_pile` + `composter`/`empiler_bois` (déplacent les parcelles du plot vers la structure) | **NEUTRE prouvé** (2026-06-15) |
| ~~**B**~~ ✅ | **Maturation hybride** (`tick_structures`, passive ∝ constitution) + jauge `compost_mur` + `retourner` (accélère/lisse) | **NEUTRE prouvé** (2026-06-15) |
| **C** | **`epandre`** (bac → plot, trio humus borné par la jauge) + amendement **pile** (biais structure) + **pile → habitat `auxiliaire`** (§4.1) | **NEUTRE** (geste jamais déclenché par le golden) |

> **Risque #1 = re-figeage golden — mais ⑤ sera NEUTRE sur les 3 phases.** Comme
> ②A/③/④, le scénario du smoke test (succession pure, 2 tuiles × 2 ans) **ne pose
> aucune structure** : pas de `poser_*`, donc `eco.structures == []`,
> `tick_structures` est un no-op (boucle vide), aucun geste joueur. → les hash
> **doivent rester bit-identiques à ④**. **À PROUVER, pas à supposer** : si le
> hash dérive, c'est un **bug** (probablement `tick_structures` qui touche un
> champ même à zéro structure, ou un `poser_*` appelé par erreur dans un chemin
> de tick). Cibles **inchangées** : `smoke 908f591bee…`, `population 435e6f72…`.
>
> **Risque #2 = frontière de couches.** `plants ← fields ← sim ← engine`.
> L'**état** des structures et leur **maturation** sont une affaire de
> **décomposition** = couche `fields` (à côté de `litiere`/`tick_decomposition`,
> dans `ecofields.py`). Les **gestes** (poser/composter/…) sont des actions
> joueur = couche `sim` (`actions.py`), qui **lisent/écrivent** `eco.structures`
> et `eco.litiere` via une API propre, **sans** que `fields` n'importe `sim`.
> (Recommandé décision #1 : structures portées par `eco`, pas par `tile` — voir
> plus bas.)
>
> **Risque #3 = déterminisme.** Aucun `random`. La maturation est une fonction
> pure de (contenu, constitution, semaines). Itérer les structures dans un
> **ordre stable** (ordre d'insertion = ordre du joueur ; ne PAS itérer un
> `set`/`dict` non ordonné). Le contenu d'une structure réutilise la **fusion par
> tissu** de ① (`deposer_litiere` interne) → au plus une parcelle par tissu →
> ordre `TISSU_ORDER` connu.

---

## Acquis ①–④ réutilisés (la matière de ⑤ existe déjà)
- **`eco.litiere[r][c]`** : `list[Parcelle{tissu, masse, age_sem}]`, fusion par
  tissu (① — `deposer_litiere` est le **point d'entrée unique**, fusionne par
  tissu : masse +, age moyenné par la masse). `om_fresh_at(r,c)` = Σ masses
  (lecture dérivée). `TISSU` (table `{tissu: (decay, humif, miner)}`) et
  `TISSU_ORDER = ("diffus","feuille","fleur","herbace","fruit","bois")` figés §1.2.
  **`bois` humifie fort / minéralise peu** ; **tendres** (feuille/fleur/herbace/
  fruit) minéralisent fort. → c'est **exactement** la matière du bac (tendres) vs
  pile (bois).
- **`Parcelle`** (`ecofields.py:208`) : la brique de contenu réutilisable pour le
  contenu d'une structure (pas besoin d'un type neuf — décision #2).
- **`tick_decomposition`** (`ecofields.py:479`) : itère `eco.litiere`, trie par
  `TISSU_ORDER`, applique `decay/humif/miner` par tissu, vieillit `age_sem`,
  alimente `om_active`/`om_stable`/`fertilite`. → **patron exact** de
  `tick_structures` (phase B), mais sur le contenu confiné de la structure, et
  produisant `compost_mur` au lieu de modifier le sol directement.
- **Cascade humus** : `om_active` → `om_stable` → libération `fertilite`
  (conservée ①). `epandre`/amendement pile (phase C) injectent dans **`om_stable`
  + `microbiome` + `fertilite`** = le « trio humus » (§5.3).
- **Rondelle habitat** : `tile.stakes` (`StakeSlot`, `RONDELLE_TYPES` inclut
  `"auxiliaire"`), posée par `favoriser_auxiliaire` (`actions.py:540`) et **lue
  par `_stability_grid`** (`population.py:273`) comme terme-source d'habitat
  PERSISTANT du champ `auxiliaire`. → **patron pour la pile → habitat** (§4.1,
  phase C) : la pile gonfle `auxiliaire` autour d'elle, comme une rondelle.
- **Coûts & maîtrise** : `COUTS` (`actions.py:89`), `FAIBLE=5`, `MODERE=15`,
  `cout_action(...)` (allégé par la maîtrise), `spend(game_state, player, cost)`
  (contrat **binaire** : effet appliqué seulement si payé à ≥ 1.0). Tous les
  gestes ⑤ suivent ce contrat. Coûts §5.1 : `poser_*` = `MODÉRÉ` (planification) ;
  `composter`/`empiler`/`epandre` = `FAIBLE` ; `retourner` = `FAIBLE`–`MODÉRÉ`.
- **Ordre de tick** (`engine.py`, `tick`) : … `tick_decomposition` (795) →
  `tick_populations` (880, étape 13b) → `_abscission` (15b) → `_tick_fruits`
  (15c) → `_tick_skeletons` (16b, fin). → **`tick_structures` se place après
  `tick_decomposition`** (la maturation est une décompo confinée) et **avant**
  ou **après** les populations selon décision #3 (le hook habitat pile lu par
  `_stability_grid` doit être posé avant `tick_populations` pour agir dès le tick
  — mais la pile est posée en planification, donc déjà là : pas de contrainte
  d'ordre forte ; placer `tick_structures` juste après `tick_decomposition`).
- **Pont** : `tools/sim_server.py`, `ENGINE_VERSION = "0.3.4"`. Le snapshot
  exposera les structures (kind, plot, jauge) → **bump 0.3.4 → 0.3.5** (phase A
  ou C). Les verbes `poser_*`/`composter`/… s'ajoutent au routeur d'actions
  (même patron que `planter`/`manger`).

---

## Le modèle (conception §5, FIGÉE — on n'invente pas le « quoi »)

Deux structures posées par le joueur (comme la rondelle habitat) :

| Structure | Accepte | Cinétique | Produit | Bonus annexe |
|---|---|---|---|---|
| **Bac à compost** | matière **tendre** (`feuille`/`fleur`/`herbace`/`fruit`/`diffus`) — **refuse le `bois`** | **hybride** : mûrit seul (∝ constitution), `retourner` accélère | **compost mûr** (jauge `compost_mur`) | — |
| **Pile à bois** | **`bois`** uniquement (BRF / hügelkultur) | **très lente** | **amendement bois** (humus forestier, biais structure) | **habitat `auxiliaire`** (§4.1) |

### Gestes (§5.1)
| Geste | Phase | Effet | Coût |
|---|---|---|---|
| `poser_bac` / `poser_pile` | **planification** | place la structure (au plot ciblé) | `MODÉRÉ` |
| `composter(plot → bac)` | courant | déplace les parcelles **tendres** du plot vers le bac | `FAIBLE` |
| `empiler_bois(plot → pile)` | courant | déplace les parcelles **`bois`** du plot vers la pile | `FAIBLE` |
| `retourner(bac)` | courant | **accélère + homogénéise** la maturation (bonus, pas obligation) | `FAIBLE`–`MODÉRÉ` |
| `epandre(bac → plot)` | courant | dépose du **compost mûr** sur un plot → **trio humus** | `FAIBLE` |

### Maturation hybride (§5.2)
Le bac mûrit **passivement** à une vitesse ∝ constitution moyenne de son contenu
(tendre vite, mélange plus lent — on lit `TISSU[tissu]`) ; `retourner` **multiplie**
la vitesse et **lisse** les âges. Le contenu mûr s'accumule dans la jauge
**`compost_mur`** (quantité mesurée). **Aucune corvée punitive** (philo) : le bac
mûrit seul, jamais bloqué ; `retourner` est un **bonus**.

### Épandage borné (§5.3)
`epandre` lit `compost_mur` : on **ne peut pas épandre plus que le disponible**.
Effet sur le plot ciblé = **trio humus** : `+om_stable` (structure/rétention/
mémoire), **ensemence `microbiome`**, `+` un peu de `fertilite`. **Amendement
complet, pas un engrais.** La **pile à bois** produit le même type d'amendement,
**biaisé structure** (`om_stable`) et **plus lent**.

> **Lien pédagogique (philo #6)** : ④ a posé la moitié « laisser pourrir →
> nuisibles » ; ⑤ pose « cueillir & composter → sol vivant ». La conséquence
> enseigne, sans sermon.

---

## Décisions à figer en tout début de ⑤ (≤ 3, puis carte blanche)
> Conception FIGÉE ; 3 points d'**implémentation** à trancher AVANT de coder
> (les écrire dans `00_etat.md` §Acquis ⑤). Recommandations ci-dessous.

1. **Où vivent les structures & qui les ticke.** **Recommandé : sur `eco`**
   (`EcoFields.structures: list[Structure]`, init `[]`), **pas** sur `tile`. La
   maturation est une **décompo confinée** = couche `fields`, à côté de `litiere`
   ; `eco` connaît déjà `rows/cols` (le plot d'ancrage est `(r,c)`). Le tick
   `eco.tick_structures()` est appelé depuis `engine.tick` **juste après
   `tick_decomposition`**. *(Alternative : sur `tile`, comme `stakes` — mais alors
   la maturation devrait vivre côté `sim`/`engine` et relire `TISSU`, moins
   cohérent. Trancher et noter.)* **Invariant golden** : `structures == []` ⇒
   `tick_structures` est un no-op strict (zéro écriture de champ).

2. **Représentation de la structure & de son contenu.** **Recommandé : réutiliser
   `Parcelle`.** `Structure{kind: "bac"|"pile", plot: (r,c), contenu:
   list[Parcelle], compost_mur: float = 0.0}`. `composter`/`empiler` **retirent**
   les parcelles concernées de `eco.litiere[r][c]` et les **fusionnent** dans
   `contenu` (même fusion-par-tissu que ① — extraire un helper `_fusion_parcelle
   (liste, tissu, masse)` partagé, ou réutiliser un mini-`deposer` interne). Le
   **bac refuse `bois`** ; la **pile n'accepte que `bois`** (filtre par `tissu`).
   *(Alternative : contenu = `dict[tissu → (masse, age)]`. La liste de `Parcelle`
   colle mieux au reste du code et au tri `TISSU_ORDER`.)*

3. **Loi de maturation, jauge, et trio d'épandage (knobs placeholders).**
   - **Maturation** (phase B) : par semaine, chaque parcelle du contenu mûrit
     `d = MATUR_BASE × maturabilité(tissu) × (RETOURNE_MULT si retourné)` ; la
     masse mûrie passe dans `compost_mur`, le reste vieillit (`age_sem++`).
     `maturabilité(tissu)` ∝ `decay`/`miner` de `TISSU` (tendre vite, mélange
     lent ; `bois` dans la pile = très lent). `retourner` met un drapeau
     `retourne_jusqua` (N semaines) qui **multiplie** la vitesse et **lisse** les
     âges (moyenne pondérée). Placeholders : `MATUR_BASE ≈ 0.05/sem`,
     `RETOURNE_MULT ≈ 2`, pile `MATUR_BASE` divisé (≈ 0.01).
   - **Trio humus** (phase C) : `epandre(q)` borné par `compost_mur` (`q =
     min(demandé, compost_mur)`), décrémente la jauge, et sur le plot :
     `om_stable += q × W_STABLE`, `microbiome` **ensemencé** (`add` borné, pas un
     `set`), `fertilite += q × W_FERT`. Bac ≈ équilibré ; **pile biais structure**
     (`W_STABLE` plus fort, `W_FERT` plus faible). Placeholders : `W_STABLE ≈
     0.6`, `W_MICRO ≈ 0.3`, `W_FERT ≈ 0.3` (bac) ; pile `×(1.3, 0.5, 0.4)`.
   - **Pile → habitat `auxiliaire`** (§4.1, phase C) : **réutiliser le patron
     rondelle**. Recommandé **le plus sobre** : à `poser_pile`, poser une
     **rondelle `auxiliaire`** sur la tuile (déjà lue par `_stability_grid`,
     **zéro machinerie neuve**, exactement comme `favoriser_auxiliaire`). *(Si
     Nico veut un habitat LOCAL au plot de la pile, il faut un champ habitat par
     plot → plus lourd, à différer comme l'a été le placement local de
     `favoriser_auxiliaire`. Trancher : sobre par défaut.)*

---

## Plan d'implémentation (un fichier à la fois ; ordre = dépendances, par phase)

### Phase A — modèle + poser + composter/empiler
1. **`fields/ecofields.py`** — `@dataclass Structure{kind, plot, contenu, compost_mur}`
   (+ helpers d'**acceptation** : `bac` refuse `bois`, `pile` n'accepte que
   `bois`) ; `EcoFields.structures: list[Structure] = []` ; méthode
   `deposer_dans_structure(struct, tissu, masse)` (fusion par tissu interne,
   miroir de `deposer_litiere`). **Pas encore** de `tick_structures` (phase B).
   → *verify :* `import fields.ecofields` OK ; `structures == []` par défaut ;
   golden **doit** rester neutre (rien ne ticke encore).
2. **`sim/actions.py`** — `poser_bac`/`poser_pile` (coût `MODÉRÉ`, créent une
   `Structure` au plot, l'ajoutent à `eco.structures`) ; `composter(plot→bac)` /
   `empiler_bois(plot→pile)` (coût `FAIBLE`, **retirent** les parcelles
   acceptées de `eco.litiere[r][c]`, les déposent dans la structure). Entrées
   `COUTS` + `OBJETS_TOUCHES`/`_objets_action` (concept de maîtrise =
   `"compost"`/`"décomposition"` — vérifier la table de concepts existante).
   → *verify :* test unitaire dédié (déposer litière → composter → la parcelle a
   migré du plot vers le bac, masse conservée, `bois` refusé par le bac).

### Phase B — maturation + jauge + retourner
3. **`fields/ecofields.py`** — `tick_structures()` (patron `tick_decomposition` :
   itère `structures` dans l'ordre, mûrit le contenu ∝ constitution, alimente
   `compost_mur`, vieillit le reste ; drapeau `retourne` accélère/lisse).
   **No-op strict si `structures == []`.**
4. **`sim/engine.py`** — appeler `eco.tick_structures()` **juste après**
   `eco.tick_decomposition()` (≈ ligne 795). Une ligne. → *verify golden NEUTRE :*
   structures vides → boucle vide → hash inchangé (à PROUVER, cf. §Golden).
5. **`sim/actions.py`** — `retourner(bac)` (coût `FAIBLE`–`MODÉRÉ`, pose le
   drapeau d'accélération). → *verify :* test : bac retourné mûrit plus vite
   qu'un bac témoin (même contenu), déterministe (h1==h2).

### Phase C — epandre + amendement pile + habitat pile
6. **`sim/actions.py`** — `epandre(bac→plot, q)` (borné par `compost_mur`, trio
   humus, décrémente la jauge) ; amendement **pile** (même API, biais structure) ;
   **`poser_pile` pose la rondelle `auxiliaire`** (décision #3, patron
   `favoriser_auxiliaire`). → *verify :* test : épandre > jauge est tronqué à la
   jauge ; `om_stable`/`microbiome`/`fertilite` montent du bon ratio ; la pile
   biaise `om_stable` ; après `poser_pile`, `_stability_grid` voit la rondelle.
7. **`tools/sim_server.py`** — **bump 0.3.4 → 0.3.5** : snapshot expose
   `eco.structures` (`[{kind, plot, compost_mur}]`) ; routeur d'actions ajoute
   `poser_bac`/`poser_pile`/`composter`/`empiler_bois`/`retourner`/`epandre`
   (cibles : `target.plot`/`target.structure_index`, validés `int` + bornes,
   comme `tailler.segment`/`manger.fruit`). → *verify :* poignée de main OK
   (`engine_version 0.3.5`), `sim_server` 113+ verts, un aller-retour pose→
   composter→epandre via le pont.

### Transverse — test dédié + golden + doc
8. **`tests/test_structures.py`** (modèle : `test_fruits.py`,
   `test_attraction.py`) — couvre : acceptation (bac refuse bois, pile refuse
   tendre), migration plot→structure (masse conservée), maturation passive →
   `compost_mur` monte, `retourner` accélère, `epandre` borné + trio humus,
   biais pile, **déterminisme** (h1==h2), **neutralité** (zéro structure ⇒ tick
   identique au tick sans le code ⑤). → *verify :* `python3 -m tests.test_structures`.
9. **Golden + 11 suites + `00_etat.md` §Acquis ⑤ + `journal.md` + commit**
   (un commit par phase, ou un par sous-sprint selon la longueur — cf. boucle ②).

---

## §Golden — protocole (attendu NEUTRE sur les 3 phases, à PROUVER)
Comme ②A/③/④ : `git stash` du diff (ou comparer avant/après), lancer l'ancien
et le nouveau golden + le test population, **comparer les hash**.
- **Attendu** : `smoke 908f591bee…` et `population 435e6f72…` **inchangés**
  (bit-identiques à ④) — le golden ne pose **aucune** structure, `tick_structures`
  est un no-op.
- **Si dérive** → **NE PAS figer aveuglément** : c'est un **bug** (`tick_structures`
  écrit un champ à zéro structure, ou un `poser_*`/`tick_structures` mal placé
  dans le chemin de tick). Diagnostiquer, corriger, re-prouver la neutralité.
- Noter le résultat (neutre confirmé) par phase dans `00_etat.md`.

## Définition de terminé (DoD)
- [ ] **2 structures posables** (`poser_bac`/`poser_pile`, planification, `MODÉRÉ`)
      portées par `eco.structures` (ou décision #1 retenue).
- [ ] `composter`/`empiler_bois` **déplacent** les bonnes parcelles plot→structure
      (bac refuse `bois`, pile n'accepte que `bois`), masse **conservée**, `FAIBLE`.
- [ ] **Maturation hybride** (`tick_structures`, ∝ constitution) → jauge
      `compost_mur` ; `retourner` accélère/lisse (bonus, jamais blocage).
- [ ] **`epandre` borné** par la jauge → **trio humus** (`om_stable`+`microbiome`+
      `fertilite`) ; **pile** = amendement biais structure, plus lent.
- [ ] **Pile → habitat `auxiliaire`** (§4.1) : rondelle posée à `poser_pile`, lue
      par `_stability_grid` (ou décision #3 retenue).
- [ ] **Déterministe** (h1==h2 sur `test_structures`) ; **zéro structure ⇒ tick
      inchangé** (invariant golden prouvé).
- [ ] `tests/test_structures.py` vert ; pont **0.3.5** (snapshot structures +
      routeur des 6 gestes) ; `sim_server` verts.
- [ ] **Golden NEUTRE confirmé** (smoke `908f591bee…`, population `435e6f72…`
      inchangés) sur les 3 phases.
- [ ] **11 suites ciblées vertes** (génétique, croissance, maîtrise, vigueur,
      population, ombre, phototropisme, sénescence, signes, auxiliaires, fruits,
      attraction…). `main.py 5` `exit=0`, scores sains.
- [ ] `00_etat.md` §Acquis ⑤ + `journal.md` à jour ; commit `feat(décompo·
      compost) : sous-sprint ⑤ — structures posables (bac/pile, compost, épandage)`.

## Pièges (vécus aux sous-sprints précédents)
1. **Croire la dérive obligatoire.** ⑤ est **neutre** sur le golden (aucune
   structure posée). Si ça dérive, c'est un **bug**, pas « la dérive annoncée ».
2. **Déterminisme.** Aucun `random`. Itérer `structures` et le contenu dans un
   **ordre stable** (insertion + `TISSU_ORDER`). Ne **jamais** dépendre de
   l'ordre d'un `set`/`dict`.
3. **Frontière de couches.** État + maturation = `fields` (`ecofields.py`) ;
   gestes = `sim` (`actions.py`). `fields` **n'importe pas** `sim`/`engine`/`tools`.
4. **Conservation de masse.** `composter`/`empiler` **déplacent** (retirent du
   plot ET ajoutent à la structure) — ne pas dupliquer ni perdre de masse. Tester
   `Σ avant == Σ après`.
5. **Jauge bornée.** `epandre` ne doit **jamais** dépasser `compost_mur` (tronquer
   à la jauge, décrémenter du montant réellement épandu).
6. **Maturation passive — pas de blocage.** Le bac mûrit seul (philo : pas de
   corvée). `retourner` = **bonus** multiplicatif, jamais une condition de
   déblocage.
7. **`microbiome` ensemencé, pas saturé.** `epandre` fait `add` borné (ensemence),
   pas un `set` à 1.0 (philo #4 : le sol grandit, il ne se télécharge pas).
8. **Coûts = canal vertueux bon marché** (philo #1) : composter/épandre `FAIBLE`,
   poser `MODÉRÉ` (planification) — **toujours ≤** déraciner/écraser (`MODÉRÉ` ×
   urgence). Vérifier dans `COUTS`.

## Ce que ⑤ NE fait PAS (frontières)
- **Pas de rendu Godot** : sprites bac/pile, jauge à l'écran, tas de compost,
  auxiliaires autour de la pile = **⑥** (intégration en pause). ⑤ pose les
  **hooks** (snapshot structures, jauge mesurée) ; la vue les lira plus tard.
- **Pas de champ habitat LOCAL par plot** (placement fin) : la pile réutilise la
  **rondelle tuile** (sobre), comme `favoriser_auxiliaire` — le local est différé
  (D30/futur), décision #3.
- **Pas de retouche de la litière (①), des dépôts (②), des fruits (③) ni de
  l'attraction (④)** : ⑤ **consomme** la litière (la déplace vers les structures)
  et **produit** un amendement, sans changer comment la litière est créée ni
  comment la faune répond.
- **Pas de nouveau champ écologique** au-delà du trio existant (`om_stable`/
  `microbiome`/`fertilite`) : l'amendement réutilise la cascade humus de ①.
- **Pas de structure « bloquée/pleine »** ni de capacité max (pas dans la
  conception) — sauf si un test révèle un besoin de bornage, à noter alors.
