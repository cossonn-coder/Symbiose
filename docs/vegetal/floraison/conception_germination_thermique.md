# CONCEPTION — GERMINATION THERMIQUE (lit T_sol)

> Doc de conception **FIGÉ** (arbitré et validé par Nico, 2026-06-30). On en tire
> les kickoffs `0N_*.md` de `sprints/vegetal/floraison/sprint_germination_thermique/`.
>
> Filiation : s'appuie sur `docs/champs/climat/conception_thermique_microclimat.md` (le champ
> `temperature_sol` existe et est spatialisé), `docs/champs/sol/conception_sol_ph.md` (patron de
> **porte multiplicative** `bell(val, opt, tol)` sur la niche de germination) et
> `docs/vegetal/genetique/conception_plasticite_expression.md` / la génétique (vecteur de gènes hérité).
> Résout le trou : **la germination ignore la température du sol**.

---

## 0. Déclencheur & décision

La **levée ignore la chaleur du sol**. Le code de germination
(`sim/succession.py`) module la niche par des portes multiplicatives — tolérance
à l'ombre, perturbation, `bell(pH)` — mais **jamais** par `T_sol`. Le seul proxy
de saisonnalité est un artefact **calendaire** : `spring_flush` (`succession.py:236`)
multiplie la germination par **×2,5** quand `week` tombe dans une fenêtre de
printemps codée en dur.

C'est un **`if semaine==1` déguisé** : la vague de levée printanière est posée à
la main, pas issue de la physique. Elle viole la philo du projet (#2 : pas de
bonus direct, toujours flux → contrainte → réponse émergente ; #3 : déterminisme
sans magie).

**Décision Nico (2026-06-30)** : on branche la levée sur la **température du sol**
avec une philo **téléonomie + sélection darwinienne + émergence**. La vague de
printemps doit **ÉMERGER** : chaque graine germe quand SA température locale
franchit SON seuil propre. On **supprime** `spring_flush`. Le périmètre validé en
conversation inclut tous les effets ci-dessous, **7 tronçons**.

---

## 1. Modèle — porte thermique sur la niche de germination

### 1.1 Principe

La germination reste un **produit de portes multiplicatives** sur l'indice de
niche. On ajoute une **porte thermique** strictement sur le même patron que la
porte pH déjà en place (`succession.py:104`) :

```
niche *= bell(T_sol_local, t_opt_eff, t_germ_tol)
```

- `bell(val, opt, tol)` = cloche gaussienne pure (`fields/ecofields/nutriments.py:38`),
  déjà réutilisée pour pH, le facteur climatique microbien et la fenêtre thermique
  du mycélium. Vaut **1.0** au centre (`val == opt`), décroît symétriquement, plate
  si `tol` est large.
- `T_sol_local` = `eco.temperature_sol.at_plot(r, c)` — **déjà spatialisé** (ombre
  maison, évaporation, rosée, inertie). Patron de lecture identique à
  `mycelium.py:58` et `matiere_organique.py:144`.

**Aucun bonus, aucun seuil binaire** : une graine bien au chaud dans sa fenêtre
voit sa niche ×~1.0 ; une graine au froid voit sa niche s'effondrer vers ~0. La
**vague de printemps émerge** mécaniquement du réchauffement progressif du sol,
plot par plot, espèce par espèce — pas d'un calendrier.

### 1.2 Deux paramètres d'espèce + un plancher global

Sur `PlantBase` (`plants/base/familles.py`), patron **exact** des attributs pH
(l.82-93), **littéraux** (la couche `plants` n'importe JAMAIS `fields`) :

| Attribut | Rôle | Défaut |
|---|---|---|
| `t_germ_opt` | température de sol optimale de levée (°C) | `18.0` (tempéré moyen) |
| `t_germ_tol` | demi-largeur de la cloche (°C) | **LARGE** au démarrage → cloche plate → ×~1.0 → golden neutre au tronçon ② |

Plus une **constante globale** (couche `fields`/`sim`, pas `plants`) :

| Constante | Rôle | Valeur de départ |
|---|---|---|
| `T_GERM_FLOOR` | plancher froid : sous ce seuil, **aucune** germination, quelle que soit l'espèce | `~5.0 °C` (cohérence de nommage avec `temp_min_growth=5.0`, `familles.py:82`) |

Le plancher modélise le **zéro de végétation** : sous ~5 °C, l'eau ne circule pas,
les enzymes dorment, aucune graine ne lève. Il évite aussi qu'une espèce à `tol`
large germe l'hiver.

### 1.3 Les trois points de germination (tous portés)

`sim/succession.py` contient **trois** chemins de levée — les trois reçoivent la
porte thermique pour rester cohérents :

1. **`_lever_grains_en_attente` (l.40)** — grains **plantés** par le joueur. Porte
   pH à l.104. On y multiplie la niche par `bell(T_sol, t_opt_eff, t_germ_tol)`.
   Le **gène propre** du grain se lit sur `grain.genes` (cf. l.97 pour
   `tolerance_ombre`).
2. **`succession` (l.133)** — levée **férale** (banque de graines du sol). La porte
   pH passe par un dict `arch_ph` (l.199) transmis à `germination_candidates`. On
   ajoute un dict **`arch_temp`** symétrique.
3. **`spring_flush` (l.236)** — **SUPPRIMÉ** au tronçon ⑤ (c'est l'artefact
   calendaire qu'on remplace par l'émergence).

`germination_candidates` (`fields/seedbank.py:287`) accepte déjà `arch_tolerance`
et `arch_ph` (multiplicateurs de niche) ; on ajoute le paramètre **`arch_temp`**
sur le même patron (l.321-322 `if arch_ph: niche_eff *= arch_ph.get(archetype, 1.0)`).

---

## 2. Gène `germination_thermique` — variabilité + sélection darwinienne

### 2.1 Le gène

On ajoute `germination_thermique` **EN QUEUE** de `GENE_NAMES`
(`plants/genetics.py:43`). L'ajout en queue **préserve les canaux de hash**
existants (commentaire l.36/42) → golden des autres gènes intact. Patron
**`rusticite_froid`** : `>1.0` = lève **plus au froid** (décale l'optimum vers le
bas) ; `<1.0` = exige plus de chaleur.

Héritage **automatique** : `child_genes` (`reproduction.py:121`, boucle
`for i, g in enumerate(GENE_NAMES)`) calcule le nouveau gène seul. `clamp_gene`
(l.103) le borne à `[0.40, 1.60]`. `neutral_genes` (l.109) le démarre à 1.0.

### 2.2 Décalage de la cloche par le gène (formule de départ, calibrage post-test)

```
t_opt_eff = t_germ_opt − GERM_GENE_SHIFT · (gene − 1.0)
```

`GERM_GENE_SHIFT` = amplitude (°C) du décalage d'optimum par unité de gène
(départ ~3-4 °C, à calibrer au banc). Gène `1.30` avec shift `4.0` → optimum
abaissé de `1.2 °C` → la graine lève dans un sol plus froid → **avance** sur ses
sœurs au printemps précoce.

- **Grain propre** (`_lever_grains_en_attente`) : `gene = grain.genes.get("germination_thermique", 1.0)`.
- **Pool féral** (`succession`) : `gene = eco.seed_bank.species[r][c][cls]["genes"]["germination_thermique"].mean`
  (`GeneStat.mean`, `seedbank.py:57`, défaut 1.0 si absent). La cloche férale est
  donc décalée par la **moyenne du pool-sol local**.

### 2.3 Sélection darwinienne imprimée dans le sol (philo #4)

C'est le cœur téléonomique. Sur un terrain à printemps précoce/froid, les graines
à `germination_thermique` élevé lèvent **en avance**, occupent la niche, fleurissent,
**réensemencent** le pool-sol local → la moyenne `GeneStat.mean` du plot **dérive
vers le haut** au fil des saisons. Le sol porte la **mémoire de la sélection** :
au bout de quelques années, les plots froids ont un pool « lève-tôt », les plots
chauds un pool « lève-tard ». **Aucun code de sélection explicite** — ça tombe de
la reproduction + héritage + réensemencement déjà en place. Émergence pure (#4,
#7 hétérogénéité persistante).

---

## 3. Correctif amont — la pluie ne refroidit pas l'air (③ du diagnostic)

### 3.1 Le trou, vérifié

| Pluie → | État actuel | Chemin |
|---|---|---|
| humidité | ✅ câblé | `PLUIE_APPORT` (`constants.py:589`) → `hydrologie.py` |
| T_sol | ✅ câblé (indirect, lag 1 tick) | humidité → `−REFROID_EVAP·hum_norm` (`thermique.py`) ; thermique tourne AVANT hydrologie → pluie de N refroidit en N+1 |
| **T_air** | ❌ **AUCUN** | `weather.py:197` `t_air = temp_norm + temperature_delta(event)` ; `temperature_delta` ne rend ≠0 que pour `TEMP_DELTA_BASE` = {Gelée tardive, Canicule, Redoux, Neige}. Pluie/Orage/Grêle **absents** → delta 0.0 |

Une averse d'été laisse donc l'air **aussi chaud qu'avant**, ce qui est faux
physiquement (refroidissement par évaporation + masse d'air froide). Comme `T_air`
nourrit `T_sol` (via `T_PLANTE_ALPHA` et le bilan thermique), ce trou **fausse en
amont** la germination qu'on est en train de brancher.

### 3.2 Le correctif

**Décision Nico : « corriger aussi ».** On ajoute `Pluie prolongée` et `Orage` à
`TEMP_DELTA_BASE` (`weather.py:65`, couche `sim`) avec un petit **delta froid**
(placeholder **~−2 à −3 °C**, calibrage post-test). Effet : une averse rafraîchit
l'air, donc le sol, donc retarde un peu les levées chaudes — cohérent, émergent.

**Conséquence golden** : `t_air` du smoke test bouge → **re-figeage maîtrisé et
annoncé au tronçon ①**.

---

## 4. Typage du catalogue (tronçon ③)

On ne se contente pas de démonstrateurs : on **type TOUT le catalogue** (27
plantes) avec sa fenêtre thermique de levée (`t_germ_opt`, `t_germ_tol`) **et**
son environnement préférentiel, fichiers `plants/species/{cultivees,potageres,
aromatiques,compagnes,sauvages,adventices}.py` + `plants/perennials.py`.

- **Frileuses** (optimum haut ~20-24 °C, tol étroite) : Tomato, Basilic, Poivron,
  Courgette, Haricot, Tournesol — lèvent tard, redoutent le sol froid.
- **Rustiques** (optimum bas ~10-14 °C, tol large) : Mâche, Carotte, Moutarde,
  adventices pionnières — lèvent tôt, colonisent le sol frais de sortie d'hiver.

C'est ce **gradient inter-espèces** qui, croisé au réchauffement progressif du
sol, fait émerger une **succession temporelle** de levées (les pionnières d'abord,
les frileuses ensuite) — sans aucun calendrier.

---

## 5. Banc multifacteur de germination (tronçon ⑥)

Le banc existant `semis_tempere` (`bancs/biotique.py:113`) **isole** seulement la
germination (neutralise mildiou + froid) ; il ne **balaye aucun facteur**. On crée
un banc NEUF `germination_multifacteur` (+ oracle dans `tests/bancs/`) qui balaye
**toutes choses égales par ailleurs** : `temperature_sol`, `humidite`, `pH`,
`lumiere`. Forçage uniforme via `build_banc_tile(..., temperature_sol=…, humidite=…,
**champs)` (`bancs/base.py`). Le banc n'est **jamais monté** au smoke/full →
**golden NEUTRE**. Il sert à calibrer `t_germ_opt/tol`, `T_GERM_FLOOR`,
`GERM_GENE_SHIFT` et le delta froid pluie.

---

## 6. Voix narratives (tronçon ⑦, OBLIGATOIRE)

Hors tick (ledger + corpus read-only) — golden NEUTRE. Cf.
`docs/narration/voix/conception_voix_narratives.md`.

- **Encyclopédie** (`sim/encyclopedie_corpus.py`, §6 fiche 3 niveaux) : la fenêtre
  thermique de levée + l'environnement préférentiel par espèce (niveau 2 « bio »,
  niveau 3 « effets écosystémiques » = la succession temporelle émergente).
- **Carnet** (`sim/carnet.py`, `CONCEPT_DE` §5) : concept « germination / chaleur du
  sol ». Descriptif au début (« les semis tardent », « rien ne lève encore »),
  **interprétatif au palier de maîtrise** (« le sol n'a pas atteint la chaleur de
  réveil de cette espèce » ; « tes lignées lèvent plus tôt chaque année »).
- Pas d'espèce neuve → la règle « 5 voix par plante neuve » n'est PAS déclenchée,
  mais ⑦ enrichit quand même les voix des espèces typées.

---

## 7. Découpage en 7 tronçons (golden annoncé par tronçon)

| # | Tronçon | Golden |
|---|---|---|
| ① | Diagnostic + oracle pluie + **correctif T_air** (banc `pluie_thermique` + ajout Pluie/Orage à `TEMP_DELTA_BASE`) | **RE-FIGÉ maîtrisé** (T_air bouge) |
| ② | Porte thermique **NEUTRE** (`t_germ_opt/tol` PLAT sur `PlantBase` + `bell(T_sol,…)` aux 3 points) | **INTACT** (tol large → ×~1.0) |
| ③ | Plancher `T_GERM_FLOOR` + **typage de TOUT le catalogue** (T° + environnement) | **RE-FIGÉ maîtrisé** |
| ④ | Gène `germination_thermique` (queue de `GENE_NAMES`, grain propre + pool féral) | **RE-FIGÉ maîtrisé** |
| ⑤ | **Flush émergent** : SUPPRIMER `spring_flush` + son appel `boucle.py:175` | **RE-FIGÉ maîtrisé** |
| ⑥ | Banc multifacteur `germination_multifacteur` + oracles | **NEUTRE** |
| ⑦ | Voix narratives (encyclopédie + carnet), OBLIGATOIRE | **NEUTRE** (hors tick) |

---

## 8. Garde-fous de conception (à ne pas dériver)

- **Émergence stricte** : aucune magie calendaire ne survit (⑤ supprime
  `spring_flush`). La vague de printemps = somme de levées locales.
- **Pas de bonus direct sur les plantes** (#1/#2) : porte multiplicative sur la
  niche, jamais de `+X` sur une plante.
- **Déterminisme zéro RNG** (#3) : `bell` pure, `T_sol` déterministe, gène hérité
  déterministe.
- **Couche `plants` n'importe jamais `fields`** : `t_germ_opt/tol` sont des
  littéraux sur `PlantBase` ; les constantes globales (`T_GERM_FLOOR`,
  `GERM_GENE_SHIFT`) vivent dans `fields`/`sim`.
- **Sélection darwinienne émergente** (#4/#7) : aucun code de sélection, elle tombe
  de reproduction + héritage + réensemencement.
- **Re-figeages golden ANNONCÉS** tronçon par tronçon (①③④⑤).
