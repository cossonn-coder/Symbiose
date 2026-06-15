# Sprint — Le sol vivant (boucle rhizosphère)

**Statut** : à faire
**Prérequis** : aucun bloquant — sprint **Python pur** sur le moteur de
vérité (`data/code/`). Indépendant des sprints Godot/C#. Git à jour avant
de démarrer.
**Estimation** : 2 à 4 sessions
**Objectif** : faire passer le sol de **décor réactif** à **organisme**.
Les racines nourrissent le sol (exsudats), le sol leur rend des services
(minéralisation, protection, uptake), et une **vitalité émerge** de cette
boucle. Tout en Python déterministe, validé sur `main.py`.

> Ce kickoff dérive du dossier d'étude `sprints/etude_sol_vivant.md` —
> lis-le en entier avant de commencer, c'est le « pourquoi » biologique de
> chaque tâche. Ce fichier-ci est le « comment ».

---

## Avant de commencer

1. **`CLAUDE.md`** — sections « Source de vérité » (Python = canon) et
   philosophies #1 (agir sur le milieu) et #4 (sol = mémoire vivante).
2. **`sprints/etude_sol_vivant.md`** — le dossier de fond : Partie 1 (bio),
   Partie 2 (état moteur), Partie 3 (chantiers A/B/C), Partie 4 (ordre).
3. **`journal.md`** — dette **D10** (divergence OM : Python mono-compartiment
   v3 vs C# tri-compartiment v4). Ce sprint la résout **côté Python**.
4. **Memory** — `project_python_source.md`, `project_status.md`,
   `feedback_design.md` (flux > action directe), `project_game_vision.md`.
5. **Code Python à lire (source de vérité)** :
   - `data/code/fields.py` — `EcoFields`, `organic_matter` (mono,
     ~l.424), décomposition/minéralisation (`DECAY_RATE` l.37,
     `decompose` ~l.561), `plant_uptake` (~l.613), `inject_patch` (~l.698)
   - `data/code/engine.py` — `_apply_uptake` (~l.145), usages de
     `root_plots` (~l.220, l.352)
   - `data/code/models.py` — `root_plots` (~l.72), enrichissements scriptés
     par famille (`inject_field` / `organic_matter` ~l.320, l.434)
6. **Code C# de référence pour l'OM v4** : `core/GridField.cs:EcoFields`
   possède déjà `OmFresh / OmActive / OmStable`. **On aligne Python
   dessus** (sens de la dette D10 acté ci-dessous).

---

## Décisions actées (validées par Nico, 2026-06-02)

À partir de `etude_sol_vivant.md` Partie 5 :

1. **Séquence du cœur** : **B → A** (racines spatiales d'abord, puis boucle
   rhizosphère). Précédé du **socle OM v4**.
2. **Vigueur du sol** : **grandeur dérivée** `vitalite(r,c)` calculée à la
   demande — **pas de nouveau `GridField` stocké** (respecte la décision #2 :
   le Qi territorial = les champs existants).
3. **Ampleur de ce sprint** : on pousse jusqu'à l'**étape 3** (vitalité
   lisible). Les **mycorhizes (chantier C)** sont **différées** en extension
   future (palier de maîtrise avancé).
4. **Sens de D10** : on **remonte** les avances du C# vers Python (OM
   tri-compartiment). Python reste le canon, mis à jour.

---

## Tâches dans l'ordre

### Étape 0 — Socle : OM v4 en Python (fresh / active / stable)

Aujourd'hui `fields.py` a un seul `organic_matter`. On le scinde en trois
compartiments en cascade, comme le C# l'a déjà :

- `om_fresh` — débris récents, sucres : décroît vite, nourrit les microbes.
- `om_active` — partiellement digéré : réserve de fertilité, vitesse moyenne.
- `om_stable` (humus) — très lent : structure + rétention d'eau + mémoire.

À coder :
- Trois `GridField` à la place de `organic_matter` dans `EcoFields`
  (init, `to_dict`/clés, `summary`).
- **Cascade** dans la décomposition (ex-`decompose`) :
  `fresh → active → stable`, chacun avec son taux. La **minéralisation
  `active → fertilite` reste ∝ microbiome** (un sol vivant minéralise plus
  vite — c'est déjà l'esprit de `DECAY_RATE`, on le module par le microbiome).
- Rediriger les **dépôts** : nécromasse / résidus de récolte / exsudats
  arrivent dans `om_fresh` (pas dans `stable`). Adapter les `inject_field`
  ciblant `organic_matter` dans `models.py` → `om_fresh`.
- Calibrer les taux pour que la masse totale de C se conserve raisonnablement
  (pas de création nette de matière).

**Validation 0** : `python3 data/code/main.py` tourne plusieurs siècles sans
crash ; les trois compartiments ont des dynamiques distinctes (fresh
volatil, stable qui monte lentement). Dette **D10 levée côté Python**.

### Étape 1 — Chantier B : racines réellement spatiales

L'uptake **et** les dépôts opèrent sur **toute l'empreinte racinaire**
`plant.root_plots`, plus seulement le plot central.

À coder :
- Dans `engine.py:_apply_uptake` (~l.145) : boucler sur `plant.root_plots`,
  **répartir** la quantité prélevée (eau, fertilité) sur les plots de
  l'empreinte (ex : quantité / nb plots, ou pondérée par densité racinaire).
- Symétriquement, tout **enrichissement** d'une plante (résidus, et bientôt
  les exsudats) se dépose sur `root_plots`.
- La **compétition racinaire** devient alors spatiale et émergente : deux
  empreintes qui se chevauchent puisent le même sol et s'épuisent
  mutuellement — ne rien coder de spécial, ça doit **émerger** du partage.

**Validation 1** : un pivot (pissenlit) et un système fibreux (pâturin)
côte à côte montrent une interaction souterraine plausible ; `main.py`
tourne toujours sur plusieurs siècles.

### Étape 2 — Chantier A : boucle rhizosphère (exsudats ↔ microbiome) ⭐

Le cœur. Chaque plante vivante dépose des **exsudats** proportionnels à sa
photosynthèse, sur ses `root_plots` (étape 1). Ils nourrissent le microbiome
local, qui en retour booste minéralisation + protection + **uptake**.

À coder :
- `exsudat = f(stade, lumière_reçue, santé)` à chaque tick → ajout au
  `microbiome` (principal) et un peu à `om_fresh`, réparti sur `root_plots`.
- **Nouvelle rétroaction** : le `microbiome` ne fait plus que protéger — il
  gagne un **bonus d'uptake / de croissance** (microbiome élevé → plante plus
  vigoureuse → plus d'exsudats). C'est la boucle vertueuse.
- **Universaliser** : supprimer le scripting « Fabaceae = +microbiome/+ferti »
  au profit de la règle **exsudats pour toutes les plantes**. Les Fabaceae
  **gardent uniquement** leur bonus spécifique **fixation N₂**.
- **BORNER la boucle** (piège n°1, voir plus bas) : saturation du microbiome,
  rendement décroissant de l'exsudat, plafond d'uptake. La boucle doit
  **converger**, pas exploser.

**Validation 2** (le test clé du sprint) :
- un **sol nu** se peuple et **s'enrichit** lentement via la succession ;
- une **polyculture dense** photosynthétiquement active **bâtit un sol
  riche** (microbiome + om_active + fertilité montent) ;
- un **sol saccagé** (disturbance forte) **se régénère** par la succession.
- `main.py` sur **plusieurs siècles** sans emballement ni effondrement.

### Étape 3 — Vitalité : grandeur dérivée lisible

Une fonction `vitalite(r, c)` calculée **à la demande** (zéro champ stocké) :

```
vitalite(r,c) = g(microbiome, om_active, fertilite, structure, −disturbance)
```

À coder :
- Fonction dans `fields.py` (méthode d'`EcoFields` ou utilitaire), bornée
  [0,1], pondération à calibrer.
- L'**intégrer aux logs** de `main.py` (carte ou moyenne) pour qu'on puisse
  la **lire dans le terminal** — c'est l'indicateur que le joueur apprendra
  plus tard à percevoir, et la **préfiguration de la Vigueur D11**.
- **Ne pas** créer de `GridField` vitalité (contredirait la décision #2).

**Validation 3** : la vitalité affichée raconte une histoire cohérente
avec les étapes 0-2 (monte sous polyculture, basse sur sol nu/saccagé,
remonte avec la succession).

---

## Pièges connus

- **Emballement de la boucle (étape 2)** : c'est LE risque. exsudats↑ →
  microbiome↑ → uptake↑ → biomasse↑ → exsudats↑… Sans bornes, ça diverge.
  Prévoir saturation/rendements décroissants **dès la première version**,
  et vérifier la convergence sur 500+ ans.
- **Conservation de la matière (étape 0)** : la cascade fresh→active→stable
  + respiration ne doit pas créer de carbone net. Vérifier les bilans.
- **Déterminisme** : tout reste seedé / `_hash_noise`. Aucune source
  d'aléa non reproductible (le jeu est déterministe — philosophie #3).
- **Régression de parité C#** : on aligne Python **sur** le C# pour l'OM,
  donc D10 se referme. Mais les étapes 1-2 ajoutent de la logique **non
  encore portée en C#** — le **noter en dette** pour le Sprint 3 (portage),
  ne pas chercher à porter maintenant.
- **Surface de l'empreinte (étape 1)** : répartir, ne pas dupliquer. Si on
  injecte la quantité pleine sur chaque plot de `root_plots`, on multiplie
  artificiellement l'enrichissement par le nombre de plots.

---

## À produire à la fin

- [ ] `data/code/fields.py` — OM tri-compartiment (`om_fresh/active/stable`),
      cascade + minéralisation ∝ microbiome, `vitalite()`
- [ ] `data/code/engine.py` — `_apply_uptake` spatial sur `root_plots`,
      dépôt d'exsudats sur l'empreinte
- [ ] `data/code/models.py` — `inject_field` redirigés vers `om_fresh` ;
      scripting microbiome par famille remplacé par exsudats universels
      (Fabaceae : ne garder que la fixation N₂)
- [ ] `data/code/main.py` — logs incluant les 3 compartiments OM et la
      vitalité dérivée
- [ ] **`journal.md`** — entrée datée : dette **D10 résolue** (OM v4 Python),
      chantiers B + A + vitalité actés ; **noter la nouvelle dette de portage
      C#** pour Sprint 3 (uptake spatial, exsudats, vitalité non portés)
- [ ] **Memory** — mettre à jour `project_status.md` (D10 levée) et
      éventuellement `project_python_source.md`
- [ ] **Commit** ex : `Sprint sol vivant : OM v4 + racines spatiales + boucle rhizosphère + vitalité`
- [ ] Mettre à jour le **Backlog actif** de `CLAUDE.md` (ce sprint réalisé,
      chantier C mycorhizes listé en extension future)

---

## Critère de fin

`python3 data/code/main.py` simule **plusieurs siècles sans crash** et on
**observe les trois récits** :
1. un sol nu se peuple et s'enrichit (succession + exsudats) ;
2. une polyculture dense bâtit un sol riche (boucle rhizosphère) ;
3. un sol saccagé se régénère.

La **vitalité dérivée** dans les logs suit ces dynamiques de façon
plausible, sans emballement ni effondrement. C'est une validation
**par lecture du terminal** — terrain naturel d'un ingénieur sim.
