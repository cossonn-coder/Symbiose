# Sprint D12·i3 — Seam `cout_action` + table objets-touchés (Python)

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> Carte blanche (conception figée) : implémente sans re-valider chaque étape,
> rends compte après. Français + pédagogie (Nico apprend Godot/C# en frontend,
> vient du C/Python embarqué ; expert Python/simulation).

## Ce que c'est, en une phrase

Troisième des 4 tronçons de l'impl. D12. On pose le **second seam** de la maîtrise
(le premier, `palier_bonus`, est fait en i2) : la **réduction du coût d'action**.
La maîtrise rend les gestes **moins chers en Vigueur** — *contextuellement*, geste
par geste, selon ce que l'action touche. On livre **`cout_action(game_state,
player, action, objets_touches)`** (§4.2) + sa **table data-driven des objets
touchés** (§10.4), et on **branche les gestes existants** de `sim/actions.py`
dessus. **Aucune détection automatique de succès** (zéro hook tick) — ça reste i4.

**Le golden écolo NE bouge PAS** (`c950f06c…` engine / `b005d9ba…` champ) : le
coût d'action vit dans la couche gameplay joueur, au-dessus du tick. **Et le golden
joueur `test_vigueur` reste vert** : sans maîtrise acquise, l'atténuation vaut
**1.0** (neutre) → tous les coûts existants sont identiques. Si un coût change
alors qu'aucune maîtrise n'est en jeu, c'est un **bug**, pas un re-figeage.

## Lis d'abord, dans cet ordre

1. `data/code/CONCEPTION_MAITRISE.md` :
   - **§4.2** `cout_action(player, action, objets_touches)` — le modèle :
     `base × f_globale(player) × f_objets(player, objets_touches)`, atténuation
     ∈ ]0,1]. **Deux termes** : (1) connaissance écologique GLOBALE, (2) maîtrise
     PARTICULIÈRE des objets que CE geste touche. « Maîtrise stockée par objet,
     action = lecteur » : aucune paire action×objet stockée.
   - **§10.4** la **table des objets touchés** par action (le livrable data) —
     terme 2 = union de {technique (toujours), être vivant cible (→ spillover
     famille §3.1), outil si requis, structure si posée/employée}. Les **concepts
     transversaux vivent dans le terme 1 (global), JAMAIS le terme 2**. Items en
     *cursive* = objets **pas encore câblés** côté moteur (outils/structures/
     techniques n'ont pas d'état → ils s'atténuent **neutre 1.0** jusqu'à leur
     sprint, D29/D30/D31).
   - **§10.5** : `observer`/`méditer`/`manger` = **coût NUL**, terme 2 vide.
     Dégradation gracieuse (objet non câblé = 1.0).
   - Survole **§3.2** (les deux mesures globales, déjà codées en i2 :
     `accumulation_globale`, `completude_ratio`) — tu *lis* l'une d'elles pour
     `f_globale`.
2. `sprints/sprint_D12_impl/00_etat.md` — découpage + décisions actées (dont
   i2 : `maitrise.py` reste pur, `actions.py` est la couche d'orchestration qui
   voit Vigueur **et** Maîtrise — c'est **là** que vit `cout_action`).
3. Code — le patron à brancher :
   - `data/code/sim/actions.py` — **les gestes existants** (`recolter`,
     `deraciner`, `ecraser`, `becher`, `grelinette`, `favoriser_auxiliaire`,
     `manger`) et leurs **constantes de coût** (`NUL/FAIBLE/MODERE/ELEVE`,
     `URGENCE_MULT`, `HARVEST_VIGUEUR_COST`). C'est ici que le coût est calculé
     aujourd'hui *en dur* — i3 le fait passer par `cout_action`. Le module importe
     déjà `maitrise as M` (ajouté en i2). **Note le patron `spend(gs, player,
     <coût>)`** : tu remplaces `<coût>` par `cout_action(...)`.
   - `data/code/sim/maitrise.py` — i2 t'a laissé `accumulation_globale`,
     `completude_ratio`, `famille_de`, `palier`. `cout_action` les **lit** (terme
     global + maîtrise par-objet). Ne le retouche pas (sauf besoin d'un petit
     lecteur ; si tu en ajoutes un, garde le module pur).
   - `data/code/tests/test_vigueur.py` — sections A5–A8/D/E testent les coûts
     **en dur** actuels (ex. `courante == 50 - ELEVE`). Ils **doivent rester
     verts** : sans maîtrise, `cout_action == base`. Ajoute une **section G** pour
     le cas AVEC maîtrise (coût qui baisse).

## Périmètre — `sim/actions.py` (+ `tests/test_vigueur.py`)

### A. La table `OBJETS_TOUCHES` (data-driven, §10.4)

Une table de module : `action (str) → {technique, outil, structure}` (les objets
**statiques** du geste). La **cible vivante** n'y est PAS (elle est dynamique :
elle dépend de la plante cliquée) → l'appelant l'ajoute au moment de l'appel.
Reflète la table §10.4 **telle quelle** (ne réinvente rien). Exemples :
`"deraciner" → technique "arrachage", outil "bêche"` ; `"becher" → technique
"bêchage", outil "bêche"` ; `"ecraser" → {}` (geste brut, §10.4) ; `"recolter" →
technique "récolte", outil "sécateur"`. Les clés d'objets (techniques/outils/
structures) sont des **strings** au même titre que les espèces — la maîtrise est
catalogue-agnostique (i1). **Aucun de ces objets n'a d'état moteur** aujourd'hui
→ `palier(...) == 0` → atténuation neutre 1.0 (dégradation gracieuse, §10.5). La
table les **nomme** pour quand leur sprint (D29/D30/D31) les câblera.

### B. `cout_action(game_state, player, action, objets_touches=None) -> float`

Le seam. `base = COUTS[action]` (les constantes existantes, regroupées en table) ;
`return base * f_globale(...) * f_objets(..., objets_touches)`. 

- **`f_globale(player)`** — atténuation par la connaissance écologique générale
  (terme 1, §4.2 : agrégat de **tous** concepts + vivants découverts). Lit un
  agrégat global de i2 (propose **`completude_ratio`** ou `accumulation_globale` —
  choisis-en un, documente). Forme : atténuation **décroissante** vers un plancher
  > 0 (∈ ]0,1]). **PLACEHOLDER NOMMÉ** (ex. `1 - ATT_GLOBALE_MAX * mesure`, borné)
  → vrai calibrage **D12.4**.
- **`f_objets(player, objets_touches)`** — atténuation par la maîtrise des objets
  **concrets** touchés (terme 2). Lit `M.palier(gs, player, objet)` pour chaque
  objet ; objet inconnu (palier 0) → contribution **neutre 1.0**. Combine-les
  sobrement (moyenne des atténuations, ou produit borné — choisis, documente).
  **PLACEHOLDER NOMMÉ** → D12.4. La cible vivante apporte le **spillover famille**
  *gratuitement* (sa maîtrise monte déjà avec §3.1 d'i2).
- **`objets_touches`** = liste de clés (la statique de la table A **+** la cible
  vivante dynamique passée par l'appelant). `None`/`[]` → terme 2 = 1.0.
- **Coût NUL préservé** : si `base == 0` (manger/observer/méditer), renvoie 0
  sans rien lire (§10.5).

### C. Brancher les gestes existants

Dans chaque geste de `actions.py`, **remplace la constante de coût en dur** par un
appel `cout_action`. **Ne change PAS les signatures publiques** (les tests les
fixent). Construis `objets_touches` = `OBJETS_TOUCHES[action]` ∪ {clé d'espèce}
quand il y a une plante cible. Pour récupérer la **clé catalogue d'une
`PlantInstance`**, ajoute un petit helper (reverse `class → clé` depuis
`PLANT_CATALOGUE`/`PERENNIAL_CATALOGUE`, comme i2 a fait `_FAMILLE_DE_ESPECE`) —
**flag** : c'est la seule donnée nouvelle à câbler ; si la résolution échoue,
dégrade en « pas de cible » (terme 2 sans espèce), ne plante pas.

- `ecraser` : `URGENCE_MULT` reste **par-dessus** `cout_action` (l'urgence n'est
  pas de la maîtrise — c'est la phase saison). `cout_action(...) * (URGENCE_MULT
  if urgence else 1.0)`.
- `manger` : `base == 0` → `cout_action` renvoie 0, comportement inchangé.
- `recolter`/`deraciner` : ajoutent la clé d'espèce de `plant` à `objets_touches`.
- `becher`/`grelinette`/`favoriser_auxiliaire` : actions **milieu**, pas de cible
  vivante (philo #2) → `objets_touches` = la statique seule.

### D. Golden joueur — `tests/test_vigueur.py`

- **Non-régression (gratuit) :** A5–A8 / D / E testent déjà des coûts en dur sur
  des joueurs **sans maîtrise** → `cout_action == base` → ils restent **verts**
  sans y toucher. (Si l'un casse, c'est que ton atténuation n'est pas neutre à
  vide → bug.)
- **Section G (nouvelle) :** un joueur **AVEC maîtrise** paie **moins**. Ex. :
  monter `M.crediter_succes`/`enregistrer_preuve` sur la technique (`"arrachage"`)
  et/ou l'espèce, puis vérifier `cout_action("deraciner", …) < ELEVE` strictement,
  et qu'un objet **non maîtrisé** laisse le coût à `base`. Vérifie aussi le
  **plancher** (atténuation jamais ≤ 0) et le **coût NUL** de `manger` inchangé.
- **Le golden de trajectoire (hash `e63b9d7f…`) ne bouge pas** : il n'invoque
  aucune action (régen/refill purs).

## Hors périmètre (gated — NE PAS faire ici)

- **Détection automatique de succès** (lire les signaux du tick §9, fenêtre
  d'imputation, tag féral, gate d'observation) → **i4**. Ici, **zéro hook** dans
  `engine`. La maîtrise progresse toujours par injection (API `observer`/
  `crediter_succes`/`enregistrer_preuve`).
- **Câbler de vrais outils/structures/techniques** (leur donner un état moteur) →
  sprints D29/D30/D31. Ici ils restent des **clés string à palier 0 → neutres 1.0**.
- **Calibrage** (`COUTS` exacts déjà posés en i-Vigueur ; formes/plancher de
  `f_globale`/`f_objets` = placeholders nommés) → **D12.4 post-test**.
- **Portage C#** (D24).

## Garde-fous (non négociables)

- **GOLDEN ÉCOLO INTACT** — avant *et* après : `python3 -m tests.test_golden` →
  **`c950f06c…`** et `python3 -m tests.test_population` → **`b005d9ba…`**. Le coût
  d'action ne touche RIEN d'écolo.
- **`tests/test_vigueur` reste vert** (coûts neutres sans maîtrise) **+** la
  section G passe. `tests/test_maitrise` reste **35/35** (tu ne casses pas i1/i2).
- **`cout_action` vit dans `actions.py`** (la couche d'orchestration qui voit les
  deux couches). `maitrise.py` reste **pur** (importe `plants` seul, jamais
  `vigueur`/`actions`) — sens de dépendance acté en i2.
- **Couche `sim`** : imports absolus, lancement depuis `data/code/`. **Déterminisme**
  total (aucun RNG). **`main.py` doit toujours tourner.**
- **Ne jamais jeter/supprimer de code.** Tronçon additif + branchement ; tu
  *remplaces* des littéraux de coût par un appel, tu ne supprimes pas les
  constantes `COUTS` (elles deviennent la `base`).

## Ampleur

**Moyen.** Un seam + une table data + le branchement de ~6 gestes + une section de
golden. Le couplage est réel (on touche les gestes existants) mais **borné par la
neutralité à vide** : la non-régression est quasi gratuite, l'essentiel du travail
est la table §10.4, le helper `class → clé`, et le cas « avec maîtrise » de G.

## À la fin

- MAJ `sprints/sprint_D12_impl/00_etat.md` (i3 ✅, reste i4, golden vérifiés).
- MAJ `journal.md` (entrée : seam `cout_action`, **golden écolo `c950f06c…`/
  `b005d9ba…` VÉRIFIÉS INCHANGÉS**, golden joueur étendu).
- MAJ `DETTE.md` (D12 → i3 fait) + `BACKLOG.md` (ligne sprint impl. D12·i3).
- Mémoire `project_status` : prochain = D12·i4 (détection de succès branchée).
- Puis commit. Puis `/clear` avant i4.
