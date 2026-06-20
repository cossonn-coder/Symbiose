# Tronçon ⑦ — Faim d'azote (bois/BRF + substrat usé de champignons)

> Sprint physico-chimie du sol. Conception : `docs/conception/CONCEPTION_SOL_NUTRIMENTS_NPK.md`
> §2.7 (faim d'azote, modèle d'immobilisation/restitution). Kickoff **autosuffisant**
> (relançable à froid). Python depuis `data/code/`.
> Tronçons ① (champ `ph`), ② (n/p/k posés), ③ (Liebig + lessivage diff. + CEC),
> ④ (lockout cloches dispo), ⑤ (fenêtres pH espèce + chlorose), ⑥ (amendements
> chaux/soufre) **déjà CLOS**. Golden figé `d8856261bbe49787…`.

## Objectif

Quand de la litière **carbonée fraîche** domine un plot — `bois`/BRF **ou substrat
usé de culture de champignons** (déclencheur ajouté par Nico, crochet vers le futur
acteur champignon) — les microbes décomposeurs **immobilisent temporairement
l'azote** du sol pour digérer ce carbone. La plante au-dessus jaunit (faim d'azote),
puis l'azote est **restitué** quand la litière C-riche mûrit. C'est l'effet permacole
classique « j'ai épandu du BRF frais, mes salades ont jauni un an ».

## Le modèle (CONCEPTION NPK §2.7)

```
immobilise = FAIM_N_COEF · masse_C_fraiche_norm[r,c]   (bois + substrat champignons)
n_dispo_local -= immobilise          # azote « emprunté » → plante jaunit
# restitution : l'azote emprunté retourne dans n au fur et à mesure que la
# litière C-riche mûrit (passe en om_active/stable)
```

- **C-riche fraîche** = parcelles de tissu `bois` (déjà tracées par plot dans la
  litière typée du sprint décompo) **+** un nouveau type/marqueur `substrat`
  (substrat usé de champignons — peut être un crochet INERTE au début, jamais
  produit dans le smoke). La masse normalisée pilote l'intensité.
- **Immobilisation = un FLUX sur le champ `n`** (philo #2 : on baisse la dispo
  d'azote local, jamais la plante directement) — la plante ressent via l'uptake
  Liebig (③) qui plafonne sur `n` réduit, donc croît moins → jaunit.
- **Restitution** : pas de création nette d'azote. L'azote emprunté est rendu
  quand le `bois` se fragmente/mûrit (la décompo le fait déjà avancer en
  `om_active`). Modèle simple possible : l'immobilisation est un PRÉLÈVEMENT
  RÉVERSIBLE recalculé chaque tick (tant que le bois est là, n reste bridé ; quand
  il a mûri, le bridage disparaît tout seul) — pas besoin de stock séparé si on
  recalcule depuis la masse de bois fraîche présente. **Trancher avec soin** :
  un prélèvement recalculé chaque tick est plus simple et auto-réversible qu'un
  compte d'azote emprunté à restituer (éviter le sur-design).

## Constante (CONCEPTION §3 — à ajouter dans `fields/ecofields/constants.py`)

```python
FAIM_N_COEF = 0.20   # azote immobilisé/tick par unité de C frais normalisé (placeholder)
```

## Greffes (repères, à re-vérifier au grep)

1. **Litière typée** — `fields/ecofields/litiere.py` : vérifier comment les
   parcelles de tissu `bois` sont stockées par plot et comment lire leur masse
   fraîche (`om_fresh_at` est un agrégat tous tissus ; il faut la part `bois`
   spécifiquement). Ajouter au besoin un accesseur `bois_fresh_at(r,c)` (helper,
   pas de calcul lourd dans `container`).
2. **`tick_decomposition`** (ou un nouveau pas dédié) dans `container.py` :
   appliquer l'immobilisation sur `n` AVANT l'uptake (l'uptake ③ lit `n`). Calcul
   pur isolable dans `nutriments.py` (comme `split_miner`/`dispo`) pour ne pas
   gonfler le conteneur (déjà ~423 ldc).
3. **Substrat champignons** : type de tissu / marqueur neuf. S'il n'existe aucun
   producteur (acteur champignon non implémenté), le poser INERTE (jamais créé au
   smoke) — pur crochet. NE PAS implémenter l'acteur champignon ici.

## Golden attendu

**MAÎTRISÉ** : le smoke contient-il du `bois` frais sur un plot habité ? Si OUI, la
faim d'azote va bel et bien baisser `n` localement → **dérive attendue** (re-figé
maîtrisé, inspecter que seules les lignes ECO/plantes concernées bougent, expliquer).
Si le `bois` du smoke est sur des plots sans plante ou en quantité négligeable →
dérive faible/nulle. **Inspecter au `git stash` diff** avant de re-figer ; si la
dérive dépasse l'attendu, c'est un bug (coef trop fort, mauvais tissu lu).

## À faire en fin de tronçon
- Ajouter `FAIM_N_COEF` + l'immobilisation `n` depuis le `bois`/substrat frais.
- Crochet `substrat` champignons INERTE (pas d'acteur).
- Vérifier golden (NEUTRE si pas de bois habité ; sinon re-figé MAÎTRISÉ inspecté)
  + suites (structures, vigueur, planter, eau, population…). `test_senescence`
  reste rouge = D39 pré-existante (pas ⑦).
- Tester À LA MAIN : déposer du `bois` frais sur un plot, vérifier que `n` chute
  puis remonte quand le bois mûrit (réversibilité).
- MàJ `00_etat.md` (⑦ ✅, hash, note taille) ; `main.py` 50+ ans OK.
- Commit : `feat(sol) : tronçon ⑦ faim d'azote (bois/BRF + substrat champignons)`.
- Écrire `08_structure_sol.md` avant le `/clear` (volet structure §2 : champ
  `structure_sol` Option B — infiltration/asphyxie/uptake, dette D30 absorbée).
