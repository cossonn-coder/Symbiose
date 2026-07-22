# Tronçon ③ — Bascule uptake **Liebig** (retrait `fertilite`, le gros re-figé)

> Sprint physico-chimie du sol. Conception : `docs/champs/sol/conception_sol_nutriments_npk.md`
> (§2.2 → §2.8, §3, §5). Kickoff **autosuffisant** (relançable à froid).
> Tronçons ① (pH) et ② (champs `n`/`p`/`k` posés, hérités, INERTES) déjà CLOS.
> ⚠️ **C'EST LE RE-FIGÉ LARGE UNIQUE DU SPRINT** — prévenir Nico, vérifier que
> la dérive golden est localisée et EXPLIQUÉE avant de re-figer.

## Objectif

**Supprimer `fertilite` net** (voie fidèle, décision 2026-06-19) et faire vivre les
trois champs `n`/`p`/`k` posés au ② : minéralisation splittée par tissu, uptake
plafonné par la **loi du minimum de Liebig**, lessivage différencié, CEC dérivée,
`SOIL_SIGNATURE` rendue explicite (fixation d'azote Fabaceae), `soil_memory`
réalimentée par un index dérivé. Le pH lockout (`dispo_i(ph)`) reste à **1.0** ici
(il se greffe au tronçon ④).

## Périmètre — LE point dur : `fertilite` a beaucoup de consommateurs

`fertilite` n'est pas qu'un champ d'uptake. Inventaire (grep `fertilite` hors tests,
2026-06-20) — **chacun doit être redirigé** sous peine de `AttributeError` :

**Écrivains de `fertilite` (→ doivent écrire `n`/`p`/`k`) :**
- `container.tick_decomposition` — `self.fertilite.add(r,c, released)` → **splitter**
  par `NPK_RELEASE[tissu]` (§2.2). C'est le cœur du re-figé.
- `sim/actions/compost.py` (`epandre`) — `EPANDRE_WEIGHTS[...]["fertilite"]` + 
  `eco.fertilite.add(...)`. Mapper le poids `fertilite` vers `n` (ou répartir n/p/k).
- `sim/engine/aleas.py` — `Alea("Pucerons", …, "fertilite", -0.3, "field")` :
  `apply_weather` cible le champ par nom → choisir une cible (proposé : `n`).
- Effets de plantes `inject_field` `"variable":"fertilite"` :
  `plants/base/familles.py` (228, 293), `plants/species/adventices.py` (93,109,188),
  `compagnes.py` (203), `cultivees.py` (205). Ce sont les signatures/legs (ex.
  trèfle qui enrichit). Mapper chaque `"fertilite"` → `"n"` (azote = enrichissement
  générique) sauf cas explicite. **Le `get_field("fertilite")` doit alors renvoyer
  None proprement** ou ces variables doivent être réécrites en `"n"`.
- `world/tile.py` — `RONDELLE_TYPES` contient `"fertilite"` (rondelle posable).
  Décider : renommer la rondelle ou la rediriger vers `n`. ⚠️ **le golden pose une
  rondelle `fertilite`** (`tests/test_golden.py:47,68`) → impact direct.

**Lecteurs de `fertilite` (→ doivent lire un INDEX dérivé n/p/k) :**
- `sim/vigueur_plante.py:64` — `eco.fertilite.at_plot(r,c)/FIELD_NORM`.
- `sim/succession.py` (176, 254 + `choisir_archetype` seuil `fertilite < 0.3`).
- `container.tick_soil_memory` — `fert = min(1, fertilite/3)` (§2.8 : index dérivé).
- `container.vitalite` — `fert = min(1, fertilite/3)`.
- `container.summary` / `boucle.py:356` repr — affichage.

**Décision de cadrage proposée** (carte blanche, conception figée — à confirmer
dans le rapport de clôture, pas à bloquer dessus) :
1. **Index nutritif dérivé** `fertilite_index(r,c)` = moyenne pondérée des trois
   normalisés (`(n+p+k)/3 / 3.0` borné [0,1], ou pondération §2.8). TOUS les
   lecteurs lisent cet index → grandeur lisse, jamais le min de Liebig instantané.
2. **Canal d'écriture `fertilite`** (rondelle, aléa, `inject_field`, `epandre`) →
   **`n`** par défaut (azote = enrichissement générique). Réécrire les `"variable":
   "fertilite"` en `"variable": "n"` dans les effets de plantes.
3. `get_field("fertilite")` : **retirer** l'entrée (plus de champ). Garder
   `fertilite_index` comme méthode, pas comme champ.

## Le modèle (CONCEPTION §2.2 → §2.8)

### Minéralisation splittée (§2.2)
Dans `tick_decomposition`, `released` (= `fresh_miner + d_active·MINER + d_stable·
MINER`) ne va plus dans `fertilite` mais se répartit. **Subtilité** : `released`
agrège trois sources de tissus différents. Le `fresh_miner` est déjà accumulé par
parcelle (`p.tissu` connu) ; `active`/`stable` n'ont plus de tissu (mélangés). 
→ Proposé : splitter `fresh_miner` PAR tissu via `NPK_RELEASE[p.tissu]` dans la
boucle des parcelles ; pour `active`/`stable` (humus mélangé) utiliser un ratio
NPK « humus » moyen (`NPK_RELEASE["humus"]` à ajouter, ou la moyenne). Bilan de
masse conservé (somme des ratios = la part minéralisée, le reste respiré déjà ôté).

### Uptake + loi de Liebig (§2.3)
Remplacer `UPTAKE["fertilite"]` par `BESOIN[stade]` par nutriment. Dans
`plant_uptake` :
```
dispo_i  = champ_i[r,c] · 1.0(ph, neutre au ③) · (1 + micro·MICRO_BOOST)
ratio_i  = dispo_i / BESOIN_i[stade]      (si BESOIN_i=0 → ratio neutre, exclu du min)
limiteur = min(ratio_N, ratio_P, ratio_K) ∈ contrainte de croissance
uptake_i = prélèvement ∝ BESOIN_i, borné par champ_i[r,c]
```
⚠️ **Question d'intégration** : qui CONSOMME le `limiteur` ? Aujourd'hui l'uptake
ne renvoie qu'un dict `consumed`. La croissance nutritive (limiteur de Liebig) doit
remonter au gate de croissance / vigueur. Vérifier `sim/growth.py` + `sim/vigueur_*`
pour brancher le limiteur (l'eau a déjà sa logique ; le nutritif suivait `fertilite`
via vigueur_plante). **Tracer ce fil avant de coder** — c'est là que se joue la
dérive golden réelle.

### Lessivage différencié (§2.4) + CEC dérivée (§2.5)
```
cec[r,c] = CEC_PAR_SOL[soil_type] + CEC_OM_COEF · min(1, om_stable/…)   (borné)
champ_i  -= champ_i · LEACHING[i] · (1 − cec_norm[r,c])
```
Remplace le `LEACHING_LOSS` unique en fin de `tick_decomposition`. CEC = facteur
dérivé (pas un champ). N très mobile, P quasi nul, K moyen.

### `SOIL_SIGNATURE` explicite (§2.6)
Fabaceae → `n.add(FIXATION_N)` (fixation Rhizobium). Aujourd'hui la signature passe
par `tick_soil_memory` (sig microbiome) + les effets `inject_field`. Rendre la
fixation d'azote explicite et lisible (rotation des cultures). Solanaceae/gourmandes
= ponction `n` déjà portée par l'uptake élevé.

### `soil_memory` réalimentée (§2.8)
`tick_soil_memory` lit `fertilite_index` (moyenne pondérée normalisée) au lieu de
`fertilite/3`. Idem `vitalite`.

## Constantes à ajouter (`constants.py`, §3) — placeholders, calibrage post-test
```python
NPK_RELEASE = {  # ratios de libération à la minéralisation, par tissu (somme ≤ 1)
    "diffus":{...}, "feuille":{"N":.55,"P":.20,"K":.25}, "fleur":{...},
    "herbace":{...}, "fruit":{"N":.30,"P":.25,"K":.45}, "bois":{"N":.15,"P":.25,"K":.20},
    "humus":{...}}  # « humus » pour active/stable (sans tissu) — à définir
BESOIN = {  # par stade × nutriment, REMPLACE UPTAKE["fertilite"]
    # germe/jeune/adulte/sénescent : N végétatif, P jeune racines, K fructif
}
LEACHING    = {"N":0.12, "P":0.005, "K":0.05}
MICRO_BOOST = 0.40            # = UPTAKE_MICRO_BONUS actuel (le conserver/renommer)
FIXATION_N  = 0.10
CEC_PAR_SOL = {"terre":0.5, "argile":0.8, "sable":0.2, "roche":0.4}
CEC_OM_COEF = 0.5
```
NB : `NUTRIENT_INIT_PAR_SOL` existe déjà (②). `UPTAKE` perd sa clé `"fertilite"`
(garde `humidite`/`microbiome`).

## Taille (garde-fou)
`container.py` est déjà à **398 ldc** (> seuil ~350). Ce tronçon AJOUTE de la
logique (split minéralisation, Liebig, CEC, lessivage diff., fixation). **Isoler le
bloc nutriments dans un helper pur `fields/ecofields/nutriments.py`** (modèle =
`ph.py`/`thermique.py` : calcul pur, le container délègue). Conception §6 le prévoit
explicitement. NE PAS laisser gonfler `container.py`.

## Golden — RE-FIGÉ LARGE (annoncer, isoler, expliquer)
- C'est **le seul** re-figeage assumé du sprint. La dérive vient de : minéralisation
  qui ne nourrit plus un champ unique mais trois, uptake Liebig (≠ ancien uptake
  fertilité), lessivage différencié, fixation N, soil_memory/vitalite via index.
- **Tactique** : tout brancher d'un coup, lancer le golden, INSPECTER la dérive
  (`tools/diag_fields_span.py` aide ; comparer summaries), vérifier qu'elle est
  cohérente (azote qui lessive vite, P stable, K moyen ; cultures gourmandes qui
  carencent), PUIS re-figer le hash. Documenter la dérive dans `00_etat.md`.
- Mettre à jour les tests qui posent une rondelle/eco `fertilite` (golden +
  `test_planter`, `test_structures`, `test_evergreen`, etc. : ~15 `init_eco(fertilite=)`
  → remplacer par `n=`/`p=`/`k=` ou un param de compat dans `init_eco`).

## Validation
- `python3 -m tests.test_golden` PASS après re-figeage maîtrisé (hash NOUVEAU,
  noté dans `00_etat.md` + journal).
- Suites ciblées qui touchent fertilité/uptake/compost/succession/vigueur : faire
  tourner et corriger les références `fertilite` (toutes redirigées).
- `python3 main.py` tourne 500+ sans crash.
- Script de contrôle : un sol gorgé de N mais carencé en P plafonne sur P (Liebig) ;
  Fabaceae enrichit `n` ; N lessive plus vite que P.

## À faire en fin de tronçon
- MàJ `00_etat.md` : statut ③ ✅, **nouveau hash golden**, dérive expliquée, note
  taille (helper `nutriments.py`), liste des consommateurs `fertilite` redirigés.
- Signaler à Nico le re-figeage + les décisions de cadrage (canal d'écriture → `n`,
  index dérivé pour les lecteurs, sort de la rondelle `fertilite`).
- Commit : `feat(sol) : tronçon ③ bascule Liebig — fertilite supprimé net, NPK splitté + uptake minimum + CEC + lessivage diff. — golden RE-FIGÉ LARGE (dérive expliquée)`.
- Écrire `04_ph_lockout.md` avant le `/clear` (volet pH §2.2 : cloches `dispo_i(ph)`
  + chlorose alcaline ; greffe `dispo_i(ph)` qui passe de 1.0 à la cloche).
