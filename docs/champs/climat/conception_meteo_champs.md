# Conception — Couplage météo → champs écologiques (dont rosée) (SYMBIOSE)

> **Document de conception. Aucun code écrit.** Spec de référence pour le sprint
> d'implémentation `sprints/champs/climat/sprint_meteo_champs/` (découpé en 5 sous-sprints,
> chacun préserve / re-fige `tests/test_golden.py` de façon ANNONCÉE).
>
> Issu d'un échange de conception (2026-06-29), prolonge `docs/champs/climat/conception_meteo.md`
> (modèle météo déterministe `weather_at`) et `docs/champs/climat/conception_thermique_microclimat.md`
> (T_sol, gel nocturne `t_min_nuit_at`). Climat : Normandie océanique.

---

## 0. Le constat de départ

La météo est **déterminée** proprement (`sim/weather.py::weather_state` → événement
+ T_air + nébulosité, fonction pure). Mais sa **traduction en effets sur les champs
du sol** est encore **provisoire** : dans `sim/engine/aleas.py`, le catalogue
`WEATHER_ALEA` mappe chaque événement vers **un seul delta plat sur un seul champ** —
commenté « PROVISOIRE », « faute de mieux », « mappings approximatifs ». Exemples :

```python
"Canicule":   Alea(..., "humidite", -0.4, "field"),   # delta arbitraire, uniforme
"Pluie prolongée": Alea(..., "humidite", +0.5, "field"),
```

Un delta plat uniforme et instantané est l'**antithèse de la philo #2** (flux →
contrainte écologique → réponse). Pourtant le moteur sait déjà faire mieux **ailleurs** :

- l'**évaporation** dans `tick_hydrology` est ∝ `temperature_sol` (chaud → sol s'assèche) ;
- la **battance** (`tick_structure`) est ∝ `PRECIP_NORM` (intensité de pluie) ;
- la T_sol lit déjà la **nébulosité** de l'événement (`tick_thermique`).

**Pivot de cette conception :** remplacer les deltas plats par des **couplages
médiés** branchés sur cette physique existante, et **compléter les flux manquants**
(rosée, lessivage par la pluie, microbiome climatique) pour que chaque événement
agisse sur **tous** les champs qu'il influence réellement — jamais par un nombre
arbitraire. Périmètre acté avec Nico : **exhaustif** (tous les champs plausibles)
et **refonte propre** (on retire les deltas plats, on ne les empile pas).

> **Principe directeur :** un événement météo ne « pose » jamais une valeur sur un
> champ. Il modifie un **flux** (rayonnement, évaporation, apport/drainage d'eau,
> activité biologique) ; le champ en émerge. Déterminisme philo #3 intact (aucun
> RNG neuf : la météo est déjà tirée par `_hash_noise`).

---

## 1. La matrice cible (événement × champ)

`✅` = déjà câblé (inchangé) · **gras** = construit par ce sprint · `—` = pas d'effet.

| Événement        | T_air | humidité                    | structure | N / K            | microbiome        | autre            |
|------------------|-------|-----------------------------|-----------|------------------|-------------------|------------------|
| **Beau temps**   | normale | **+rosée** (nuit claire)  | —         | —                | actif             | jour : T_sol↑ ✅ |
| **Canicule**     | +7 ✅ | **↓ par évaporation**       | —         | —                | **ralenti** (chaud) | —              |
| **Sécheresse**   | normale | **↓↓ (évap + pluie de fond réduite)** | fissuration | —      | **ralenti** (sec) | —              |
| **Gelée tardive**| −9 ✅ | givre si humide             | —         | —                | **ralenti** (froid) | gel tissulaire ✅ |
| **Redoux**       | +5 ✅ | +fonte                      | —         | —                | réveil            | fonte neige ✅   |
| **Pluie prolongée** | normale | **++ ∝ intensité**       | battance ✅ | **lessivage N** | **léger ↓** (saturation) | —          |
| **Tempête**      | normale | +                           | —         | —                | —                 | vent paillage ✅ |
| **Grêle**        | normale | +                           | battance ✅ | —              | —                 | foliaire médié ✅|
| **Orage**        | normale | ++                          | battance ✅ | lessivage N part.| —              | vent paillage ✅ |
| **Neige**        | −6 ✅ | +fonte différée             | —         | —                | dormant           | manteau ✅       |

Le **pH** reste hors périmètre : sa dérive lente + amendements sont déjà modélisés
(`docs/champs/sol/conception_sol_ph.md`) ; l'acidification par la pluie est marginale → **dette mineure**.

---

## 2. Humidité médiée (sous-sprint ①, fondation)

On **retire** les entrées humidité de `WEATHER_ALEA` (Canicule, Sécheresse, Pluie
prolongée, Orage) et on les remplace par deux flux :

### 2.1 Assèchement émergent (Canicule / Sécheresse)
Aucun terme neuf : la canicule monte T_air → `tick_thermique` monte `temperature_sol`
→ `tick_hydrology` baisse le multiplicateur d'évaporation (`evap = EVAPORATION −
EVAP_TEMP_COEF·max(0, T_sol − EVAP_TEMP_REF)`) → l'humidité **chute par évaporation**.
Le delta plat `−0.4` faisait double-emploi avec ce canal → sa suppression rend
l'assèchement **spatial** (un coin ensoleillé sèche plus qu'un coin ombragé).

### 2.2 Apport de pluie ∝ intensité
Nouvelle table **PURE** côté `fields` (miroir de `PRECIP_NORM`), `PLUIE_APPORT` :

```
PLUIE_APPORT = {"Pluie prolongée": +X, "Orage": +Y, "Tempête": +z, "Grêle": +w,
                "Sécheresse": −s}   # négatif = pluie de fond TARIE (état sec prolongé)
```

L'apport entre dans `tick_hydrology` **infiltré ∝ structure** (comme `BASE_RAIN`,
couplage §2.3 du sol) : `h += (BASE_RAIN + PLUIE_APPORT_event) · structure_sol`.
Un sol grumeleux boit toute la pluie, un sol compacté en laisse ruisseler. La
Sécheresse **réduit la pluie de fond** (apport négatif borné, pas d'humidité
arbitraire enlevée). Calibrage post-test (`X,Y,z,w,s`).

> Conséquence émergente : la même pluie hydrate **moins** un sol battu/compacté —
> la structure du sol gouverne l'efficacité de l'eau (interconnexion structure↔eau).

---

## 3. Rosée & gelée blanche (sous-sprint ②, cœur thermo-hydrique nocturne)

### 3.1 Le continuum « un seul thermomètre nocturne »
`fields/ecofields/thermique.py::t_min_nuit_at(r,c)` calcule déjà la T minimale
nocturne par plot : `T_air − RAYONNEMENT_NOCTURNE·(1−couvert)·(1−nébulosité)`. La
nuit, un sol **découvert** sous un **ciel clair** rayonne sa chaleur et se refroidit.
Le moteur n'en tire aujourd'hui qu'**une** chose (gel tissulaire des semis si < 0 °C).
Physiquement, **avant** de geler, ce sol froid **condense la vapeur de l'air** : la rosée.
Le même refroidissement produit un **continuum** lu sur le même thermomètre :

| Régime         | Condition                                  | Effet                                   |
|----------------|--------------------------------------------|-----------------------------------------|
| **Rosée**      | `t_min_nuit < T_rosée` **et** `t_min_nuit > 0` | dépôt d'eau liquide → `humidite +`   |
| **Gelée blanche** | `t_min_nuit < T_rosée` **et** `t_min_nuit ≤ 0` | dépôt de givre → fonte différée + léger dégât foliaire |
| (gel tissulaire) | `t_min_nuit < TEMP_FROST_DAMAGE` (=0)     | voie EXISTANTE inchangée (semis)        |

### 3.2 Le point de rosée (proxy local)
Pas de champ « humidité de l'air » dédié ; on le dérive de l'humidité du **sol** local
(l'évapotranspiration humidifie l'air au ras du sol) :

```
T_rosée[r,c] = T_air − ÉCART_ROSÉE_SEC + GAIN_HUM_ROSÉE · humidité_norm[r,c]
```

Sol sec → grand écart au point de rosée (peu de rosée) ; sol humide → point de rosée
proche de T_air (rosée facile). `humidité_norm = min(1, humidite/3)` (même échelle que
`tick_thermique`). Constantes calibrées post-test.

### 3.3 La condensation déposée
```
condensation[r,c] = max(0, T_rosée[r,c] − t_min_nuit[r,c]) · ROSÉE_PAR_DEGRÉ
```
- `t_min_nuit > 0` → **rosée liquide** : `humidite.add(r, c, +condensation)`.
- `t_min_nuit ≤ 0` → **givre** : pas d'eau liquide ce matin ; on **mémorise** le dépôt
  (fonte différée §3.4) + dégât foliaire léger §3.5.

### 3.4 Fonte différée du givre
L'eau condensée gelée n'est pas perdue : elle est **restituée à l'humidité quand T
repasse > 0** (réchauffement). Modèle sobre : accumuler le givre dans un petit état
par plot (carte `givre` ou réutilisation d'un champ existant — à trancher au kickoff),
et le reverser dans `humidite` au tick où `t_min_nuit > 0`. Couplage hydrique réaliste
**et sûr** (zéro dégât) — c'est le socle minimal de la gelée blanche.

### 3.5 Dégât foliaire de la gelée blanche (léger, médié)
Le givre brûle le **feuillage exposé établi** (pas les semis — déjà couverts par le
gel tissulaire, **pas de double comptage** : périmètres de plantes disjoints).
Réutilise `_mediated_damage` (`mortalite.py`) : `dégât = sévérité × susceptibilité
(gène rusticite_froid) × (1 − protection paillage)`, cause `"givre"`, sévérité
FAIBLE (`GIVRE_SEVERITY_REF` élevé → dégât plancher). À activer si le calibrage le
permet ; sinon rester sur §3.4 seul (dépôt + fonte), le dégât est l'option « riche ».

### 3.6 La tension écologique recherchée
Le sweet spot émerge des deux formules :
- **sol nu + un peu humide + nuit claire** → fort refroidissement + point de rosée
  correct → **rosée maximale** (le sol nu est le grand capteur du matin) ;
- **sol paillé** → isolé (`couvert` haut) → se refroidit peu → peu de rosée (mais il
  retenait déjà son eau : pas de double peine) ;
- **sol totalement desséché** → point de rosée au plancher → peu de rosée.

Gameplay (poids « significatif » acté) : la rosée ne **ressuscite pas un désert**,
mais **freine la spirale de dessèchement** d'un sol encore vivant et découvert — un
levier de survie en sécheresse, observable, qui récompense la lecture du terrain
(permaculture des climats secs). Calibrer `ROSÉE_PAR_DEGRÉ` pour que ce soit sensible
sans déséquilibrer l'eau.

### 3.7 Signe diégétique (philo #5)
La rosée **est** un signe perceptif direct, rendu le matin (gouttes scintillantes sur
l'herbe, toiles d'araignées perlées ; givre blanc en hiver). On émet au `log` une ligne
marqueur (`💧 rosée` / `❄ gelée blanche`) quand la condensation est notable → le ledger
d'événements (`sim/journal.py`) la capte → carnet/encyclopédie. Le **rendu** (sprites)
est côté Godot via la carte de condensation exposée au snapshot (sous-sprint ⑤).

---

## 4. Lessivage NPK par la pluie (sous-sprint ③)

Le lessivage existe **déjà** (passif, `container.py::tick_decomposition` lignes ~650 :
`leach_factor("N"/"P"/"K", cec)` modulé par la CEC = texture + humus). Ce sprint ne le
recrée pas : il l'**amplifie par le flux d'eau réel** du tick. La pluie qui **draine**
emporte les ions mobiles vers le fond. `tick_hydrology` **retourne déjà** la perte de
drainage par cellule (`pertes = [(r,c, h·(1−drainage))]`, `container.py:392`) — le
crochet existe et est aujourd'hui jeté par la tuile.

Modèle : amplifier le lessivage de N (très mobile) et un peu de K (moyen), P quasi
épargné, **proportionnellement à l'eau drainée ce tick** :
```
facteur_pluie = 1 + LESSIVAGE_PLUIE_K · drainage_norm[r,c]
n *= leach_factor("N", cec) ** facteur_pluie     # ou équivalent borné
```
Un orage sur sol drainant lessive fort l'azote ; un sol grumeleux retient mieux (CEC).
Interconnexion : la **structure** (battance ↓ infiltration) et l'**humus** (CEC ↑)
gouvernent qui garde ses nutriments. Calibrage `LESSIVAGE_PLUIE_K` post-test.

> Décision d'implémentation à trancher au kickoff : lire la perte de drainage
> retournée par `tick_hydrology`, ou recalculer un `drainage_norm` simple. **Ne pas
> dupliquer** la boucle hydrologique (piège connu, cf. sprint pots/bacs).

---

## 5. Microbiome climatique (sous-sprint ④)

Le microbiome évolue aujourd'hui par **famine** (puits si litière épuisée) et un
**lockout pH** (cloche autour du neutre), dans `tick_decomposition`. Il manque le
couplage **climatique** : l'activité microbienne suit une **cloche de température**
et chute au **sec** comme au **gel**. Modèle (terme multiplicatif sur la croissance/
le puits microbien, pas un champ neuf) :

```
f_clim(r,c) = cloche(T_sol, MICROBE_T_OPT, MICROBE_T_TOL) · f_humidité(humidité_norm)
```
- **cloche en température** : optimum ~`MICROBE_T_OPT` (≈ 20 °C), tombe vers 0 au gel
  et à la canicule (activité dormante au froid, stress thermique au chaud) ;
- **facteur humidité** : nul au sec (microbes en dormance), optimal en sol frais,
  légèrement réduit en saturation (anoxie — d'où le « léger ↓ » de la Pluie prolongée).

Conséquence émergente : un sol **chaud et humide** recycle vite (été doux pluvieux),
un sol **gelé** ou **desséché** stocke la matière sans la digérer (litière qui
s'accumule l'hiver / en sécheresse). Couplage direct météo → vitesse du cycle
biogéochimique. Calibrage des constantes post-test.

---

## 6. Interconnexions vivantes + voix + pont (sous-sprint ⑤)

Règle « tout coexiste » (mémoire 2026-06-16) : la rosée et les nouveaux flux doivent
relier les acteurs vivants.

- **Faune abreuvée** : escargots / limaces / détritivores du matin (`fields/population.py`)
  gagnent en activité/survie les semaines à forte rosée (l'eau de surface est leur
  abreuvoir). Terme sobre, pas de nouvelle guilde.
- **Captation foliaire** : une canopée intercepte la rosée → réduction du **stress
  hydrique** de la plante (la rosée hydrate le feuillage). Touche `PlantInstance` /
  l'uptake ; modèle sobre (réduit la mémoire de sécheresse ou complète l'uptake d'eau).
- **Voix narratives** : la rosée et la gelée blanche méritent leurs entrées —
  **encyclopédie** (concept « rosée / micro-cycle de l'eau »), **carnet** (descriptif →
  interprétatif au seuil météo, D12), **pages secrètes** (rosée de la Saint-Jean,
  herbiers anciens). Magazine non concerné. Recopier les corpus dans les modules de
  données existants (`sim/encyclopedie_corpus.py`, `sim/carnet.py::CONCEPT_DE`,
  `sim/pages_corpus.py`).
- **Pont Godot** : exposer la **carte de condensation** (rosée/givre par plot) dans le
  snapshot (`tools/simserver/serialize.py`) pour le rendu des gouttes/givre côté C#.

---

## 7. Découpage en sous-sprints

Le sprint est **gros** (beaucoup de fichiers couplés) → 5 sous-sprints autosuffisants,
chacun une unité testable. Ordre = dépendances (① fonde l'hydrique propre, ② y greffe
la rosée, ③④ ajoutent les autres flux, ⑤ relie le vivant et expose au rendu).

| # | Sujet | Kickoff | Golden |
|---|-------|---------|--------|
| ① | Humidité médiée (retrait deltas plats + `PLUIE_APPORT`) | `01_humidite_mediee.md` | re-figé **LARGE**, annoncé |
| ② | Rosée & gelée blanche (`tick_rosee`, point de rosée, continuum) | `02_rosee_gelee_blanche.md` | re-figé annoncé |
| ③ | Lessivage NPK par la pluie (amplifie le lessivage existant) | `03_lessivage_npk.md` | re-figé annoncé |
| ④ | Microbiome climatique (cloche T + facteur humidité) | `04_microbiome_climatique.md` | re-figé annoncé |
| ⑤ | Interconnexions vivantes + voix + pont snapshot | `05_interconnexions_voix.md` | NEUTRE / léger |

### Invariant golden (tous les tronçons)
Le golden est un **smoke test** (2 tuiles × 4 ans, `tests/test_golden.py` +
`tests/population_hash.txt`). Ce sprint **modifie la physique du tick** → le golden
**va bouger** dès ①. Chaque re-figeage doit être **maîtrisé et annoncé** : vérifier
que la dérive est *localisée et expliquée* (humidité/microbiome qui bougent dans le
sens attendu), JAMAIS un re-figeage aveugle. Re-figer : `python3 -m tests.test_golden
--capture` (depuis `data/code/`) + recapturer la population si besoin. Consigner le
nouveau hash dans `00_etat.md` à chaque cran.

### Calibrage
Toutes les constantes neuves sont des **placeholders post-test**, nommées en tête de
`fields/ecofields/constants.py` : `PLUIE_APPORT`, `ÉCART_ROSÉE_SEC`, `GAIN_HUM_ROSÉE`,
`ROSÉE_PAR_DEGRÉ`, `GIVRE_SEVERITY_REF`, `LESSIVAGE_PLUIE_K`, `MICROBE_T_OPT`,
`MICROBE_T_TOL`. Les valeurs définitives viennent du F5 / des bancs d'essai.

### Couches (rappel)
`plants ← fields ← sim ← engine ← main`. La rosée/microbiome/lessivage vivent dans
`fields/ecofields/` (calcul pur, comme `thermique.py`) ; le câblage d'ordre vit dans
`sim/engine/boucle.py` ; les tables de données météo (`PLUIE_APPORT`) restent PURES
côté `fields` (pas d'import inverse vers `sim`, miroir de `NEBULOSITE`/`PRECIP_NORM`).
