# CONCEPTION — SOL · Nutriments N / P / K

> Conception figée le 2026-06-19 (Sprint physico-chimie du sol, volet B/3).
> Étude de fond : `sprints/etude_physicochimie_sol.md`. Ordre global du sprint :
> voir `CONCEPTION_SOL_PH.md` §6. Volet frère structure : `CONCEPTION_SOL_STRUCTURE.md`.

## 0. Objectif & intuition

Aujourd'hui `fertilite` est un **proxy unique** de tous les nutriments. On l'éclate
en **trois champs distincts N / P / K** — voie fidèle choisie le 2026-06-19
(`fertilite` **supprimé net**, pas de proxy parallèle). Les trois ont des
comportements **très différents**, et c'est là tout l'intérêt :

- **N (azote)** — croissance végétative ; **très mobile** (lessivé vite) ; fixé par
  les légumineuses ; immobilisé par le bois frais (faim d'azote).
- **P (phosphore)** — racines/floraison ; **quasi immobile** ; **fortement bloqué
  par le pH** (lockout, volet A).
- **K (potasse)** — fruits/résistance ; mobilité intermédiaire ; retenu par
  l'argile/humus (CEC).

Le principe qui fait *payer* cette complexité : la **loi du minimum de Liebig** —
la croissance est plafonnée par le nutriment **le plus rare**, pas par leur somme.
Un sol gorgé d'azote mais carencé en phosphore plafonne sur le phosphore.

Philosophie : **#2** (les nutriments contraignent un flux d'uptake, jamais de
bonus direct) ; **#3** déterministe ; **#5** pas de chiffre HUD (le joueur lit la
carence via la vigueur, le jaunissement, quelles cultures réussissent).

## 1. État de départ

| Brique | Où | Statut |
|---|---|---|
| `fertilite` (proxy N+P+K) | `fields/ecofields/container.py` | **à SUPPRIMER**, éclaté en n/p/k |
| Minéralisation `fresh_miner + active·MINER + stable·MINER → fertilite.add` | `tick_decomposition` | à **splitter** en ratios N/P/K par tissu |
| `UPTAKE["fertilite"]` par stade, boosté microbiome | `plant_uptake` | à passer en **uptake par nutriment + Liebig** |
| `LEACHING_LOSS` (tout mobile) | hydrologie | à **différencier** (N fort, P ~0, K moyen) |
| `SOIL_SIGNATURE` (Fabaceae fert+, Solanaceae −) | signatures familles | à rendre **explicite** sur `n` |
| Entrée nutritive de `soil_memory` | composite | à réalimenter par un **index dérivé** |
| Litière typée 6 tissus, `om_active/om_stable` | système compost ⑤ | OK — porte les ratios de libération |

## 2. Le modèle

### 2.1 Trois champs `n` / `p` / `k` (tronçon ① — socle neutre)

Trois `GridField`, plage ~[0,3] (comme l'ancien `fertilite`), **init par
`soil_type`** (table §3). Posés mais **pas encore lus** par l'uptake (qui lit
toujours `fertilite`) → golden neutre.

### 2.2 Minéralisation splittée

La décompo libère N/P/K en **ratios dépendants du tissu** (feuille riche N, bois
pauvre N, fruit riche K…). Chaque source de minéralisation (`fresh`, `active`,
`stable`) répartit sa libération :

```
for i in (N, P, K):
    champ_i.add( miner_total[r,c] · NPK_RELEASE[tissu][i] )
```

### 2.3 Bascule uptake + loi de Liebig (tronçon ② — LE gros re-figé)

Retrait de `fertilite`. Disponibilité de chaque nutriment = stock × lockout pH
(volet A) × boost microbiome :

```
dispo_i  = champ_i[r,c] · dispo_i(ph) · (1 + micro·MICRO_BOOST)
ratio_i  = dispo_i / BESOIN_i[stade]
limiteur = min(ratio_N, ratio_P, ratio_K)              ⟵ LOI DU MINIMUM
croissance_nutritive ∝ clamp(limiteur, 0, 1)
uptake_i = prélèvement proportionnel à BESOIN_i, borné par dispo_i
```

`dispo_i(ph)` vaut 1.0 tant que le volet A (lockout) n'est pas branché (tronçon 4
global) — le NPK fonctionne seul, le lockout se greffe ensuite.

### 2.4 Lessivage différencié

```
champ_i -= champ_i · LEACHING_i · (1 − cec_norm[r,c])      LEACHING: N≫K>P≈0
```

### 2.5 CEC dérivée (tronçon ② — incluse)

Pas un champ : un **facteur dérivé** texture + humus, modulant lessivage **et**
tampon pH (volet A) :

```
cec[r,c] = CEC_PAR_SOL[soil_type] + CEC_OM_COEF · om_stable_norm[r,c]
```

Argile+humus → CEC élevée (retient, tamponne) ; sable → CEC basse (tout lessive).

### 2.6 `SOIL_SIGNATURE` explicite (tronçon ② — inclus)

L'esquisse devient un vrai flux d'azote :
- **Fabaceae** → `n.add(FIXATION_N)` (fixation symbiotique Rhizobium) ;
- **Solanaceae & gourmandes** → ponction `n` accrue (déjà via uptake élevé).
Rend lisible la **rotation des cultures** (gourmande après légumineuse fixatrice).

### 2.7 Faim d'azote (tronçon ④ volet B = ⑦ global) — RE-FIGÉ MAÎTRISÉ

Quand de la litière **carbonée fraîche** domine un plot — `bois`/BRF **ou substrat
usé de culture de champignons** (déclencheur ajouté par Nico, crochet vers le futur
acteur champignon) — les microbes décomposeurs **immobilisent l'azote** :

```
immobilise = FAIM_N_COEF · masse_C_fraiche_norm[r,c]     (bois + substrat champignons)
n_dispo_local -= immobilise          # azote « emprunté », plante jaunit
# restitution : l'azote emprunté retourne dans n au fur et à mesure que
# la litière C-riche mûrit (passe en om_active/stable)
```

Interconnexion directe avec le compost ⑤ (pile à bois, BRF) et les vers.

### 2.8 Réalimentation de `soil_memory`

L'entrée nutritive de `soil_memory` (ex-`fertilite`) lit désormais un **index
dérivé** = moyenne pondérée des trois normalisés (la mémoire veut une grandeur
lisse, pas le min de Liebig instantané).

## 3. Constantes (placeholders)

```python
NUTRIENT_INIT_PAR_SOL = {  # (N, P, K) hérités
    "terre": (1.0, 0.8, 0.9), "argile": (0.9, 0.9, 1.1),
    "sable": (0.5, 0.4, 0.4), "roche": (0.4, 0.6, 0.5)}

# Ratios de libération à la minéralisation, par tissu de litière (somme libre)
NPK_RELEASE = {  # exemples — feuille riche N, bois pauvre, fruit riche K
    "feuille": {"N": 0.55, "P": 0.20, "K": 0.25},
    "bois":    {"N": 0.15, "P": 0.25, "K": 0.20},
    "fruit":   {"N": 0.30, "P": 0.25, "K": 0.45},
    # … racine, fleur, tige : à compléter sur les 6 tissus existants
}

BESOIN = {  # par stade × nutriment (remplace UPTAKE["fertilite"])
    # germe/jeune/adulte/sénescent : N pour végétatif, P jeune racines, K fructif.
}
LEACHING = {"N": 0.12, "P": 0.005, "K": 0.05}   # N très mobile, P quasi nul
MICRO_BOOST = 0.40                               # conservé de l'uptake actuel
FIXATION_N  = 0.10                               # azote fixé/sem par Fabaceae
CEC_PAR_SOL = {"terre": 0.5, "argile": 0.8, "sable": 0.2, "roche": 0.4}
CEC_OM_COEF = 0.5
FAIM_N_COEF = 0.6                                # immobilisation max par masse C-riche
```

## 4. Tronçons & golden (volet NPK)

- **①** (global 2) Trois champs `n`/`p`/`k` posés/hérités, minéralisation splittée,
  uptake **lit encore `fertilite`**. Golden **NEUTRE**.
- **②** (global 3) **Bascule** : retrait `fertilite`, uptake Liebig, lessivage
  différencié, CEC, `SOIL_SIGNATURE` explicite, `soil_memory` réalimentée.
  **LE gros RE-FIGÉ MAÎTRISÉ du sprint** (isolé ici, une fois).
- **④** (global 7) Faim d'azote (bois/BRF + substrat usé champignons). Re-figé
  maîtrisé.

> Le lockout pH (volet A ④, global 4) se greffe *après* la bascule : `dispo_i(ph)`
> passe de 1.0 à la cloche. Re-figé porté par le doc pH.

## 5. Interconnexions

`n` ← fixation **Fabaceae** · ← décompo (split) · ← **faim d'azote** (litière bois
+ substrat champignons, compost ⑤) · → croissance végétative.
`p` ↔ **pH** (lockout dominant, volet A) · ← futures **mycorhizes** (acteur
champignon à venir).
`k` ↔ **CEC** (argile/humus/cendre).
**CEC** ← `soil_type` + `om_stable` → module **lessivage** + **tampon pH**.
Loi de Liebig → la **rotation des cultures** devient lisible.

## 6. Garde-fous

- **Golden** : la bascule (②) est le re-figé large unique — le **seul** moment où
  l'uptake change de base. Tout poser neutre avant, brancher d'un coup, annoncer.
- **Sur-modélisation** : ne pas multiplier les tissus au-delà des 6 existants ;
  `BESOIN`/`NPK_RELEASE` partent sobres, calibrage jeu-en-main.
- **Couches** : `fields` n'importe jamais `sim` ; les signatures familles passées
  en argument depuis l'engine (comme aujourd'hui).
- **Taille** : si `container.py` (337 ldc, max du dépôt) déborde, isoler le bloc
  nutriments dans `fields/ecofields/nutriments.py` (helper pur).
- **Philo #2/#5** : carence = flux d'uptake bridé → vigueur/jaunissement, jamais de
  malus direct ni de chiffre N/P/K en HUD.
