# CONCEPTION — Luxuriance par stratification (D65, absorbe D62)

> **Statut : conception FIGÉE (2026-07-04, `/conception`).** Prête pour
> `/sprint-auto`. Extrait de D64 (« le vrai objectif derrière la mort du
> tournesol ») et **absorbe D62** (rampantes clonales). Fait suite à
> `CONCEPTION_USURE_LETALITE.md §6`.
>
> **Intention Nico** : un plot n'est PAS limité à une plante. Plusieurs strates
> coexistent (couvre-sol trèfle + potagère + grimpante + traçante) et la
> **luxuriance** naît de la **densification** — la compétition émerge de la
> densité partagée, jamais d'un conflit discret (cf. D64① qui a rendu le conflit
> non-létal). Le jardin doit se **remplir** et se **superposer**, visiblement.

## 1. Ce qui EXISTE déjà (vérifié dans le code — ne pas réinventer)

Le socle de stratification est là à ~70 % :

- **Strates par stade** — `plants/base/empreintes.py::STRATE_DEFAULTS`
  (`sol/basse/moyenne/haute/grimpante` → `height/canopy_r/root_r/density`) +
  `STRATE_SHADE_TOLERANCE`. Une espèce hérite gratuitement, override au besoin.
- **Co-occupation permise** — `world/tile.py::add_plant` crée une `PlantInstance`
  sans tester l'occupation (`is_valid_plot` seul).
- **Ombrage vertical asymétrique ÉMERGENT** — `fields/light.py` : une plante
  n'est ombrée que par ses voisines **plus hautes** (tri hauteur décroissante).
  La stratification verticale fonctionne déjà.
- **Empreinte au sol dérivée de la structure** — `instance.update_footprint()` →
  `footprint{height, canopy_r, root_r}`. `_plots_in_radius` mappe rayon → plots.
- **Conflit NON-LÉTAL** (D64①) — la co-occupation est viable, l'éclaircissage
  émerge de la rareté partagée (lumière/eau/nutriments), pas d'un verdict.
- **Évaporation modélisée** — `fields` : `EVAPORATION`, `SOIL_RETENTION` → hook
  gratuit pour « sol couvert = eau conservée ».
- **AUCUN clonal** — `sim/reproduction.py` = 100 % par graine. La « bouture » est
  un marqueur d'événement rare (`sim/pages.py`), pas une mécanique.

**Le manque** : rien ne *densifie* activement le tapis (semis seul = clairsemé),
aucun *champ de couverture* lisible, aucun *empilement visible*, aucune
*silhouette d'espèce*. Ce sprint comble ces 4 briques.

## 2. Les 4 briques (arbitrées avec Nico)

### 2.1 — Champ de couverture au sol (brique 2) — le SOCLE
Un **champ scalaire** `couverture_sol` (0..1 par plot) : fraction du sol couverte
par les strates basses (**sol + basse**). Alimenté par **scatter** : chaque plante
*stampe* son empreinte au sol (`_plots_in_radius` sur `canopy_r`) pondérée par la
densité de strate, dans le champ. **Un seul balayage de plantes/tick** (jamais un
sweep de grille), réutilise l'infra empreinte existante.

Trois consommateurs (interconnexion « tout coexiste ») :
- **(a) Évaporation** — sol couvert → `EVAPORATION` réduite localement (l'eau est
  conservée sous le tapis). **Flux → contrainte** (philo #2), jamais un bonus
  plante.
- **(b) Germination d'adventices** — forte couverture → la levée de graines
  d'adventices du `seedbank` est **supprimée** (le couvre-sol étouffe la concurrence
  — bénéfice permaculturel réel). Modif du gate de germination.
- **(c) Gate du clonal** (interne, §2.2) — un plot **déjà saturé** en couverture
  refuse un nouveau ramet → **auto-limitation** de la colonie + **cap perf**.

### 2.2 — Densification clonale (brique 1, absorbe D62)
Une plante clonale mature **émet des ramets** (clones) dans le voisinage : nouveau
point d'enracinement, `PlantInstance` **génétiquement identique** (vecteur de
gènes copié — clone, *pas* de brassage sexué). Émergence du tapissage et des
**colonies envahissantes**.

**UNE mécanique paramétrée** (pas 3 chemins de code) — trait d'espèce
`clonal_mode ∈ {none, stolon, rhizome, drageon}` module 3 axes :

| mode      | portée (radius) | gate d'établissement            | agressivité | exemples          |
|-----------|-----------------|---------------------------------|-------------|-------------------|
| stolon    | courte          | **besoin de lumière au sol**    | modérée     | trèfle, fraisier, violette |
| rhizome   | longue          | **tolère l'ombre** (réserve)    | forte       | menthe, bambou traçant |
| drageon   | très courte     | près de la mère                 | modérée     | framboisier       |

Invariants :
- **Déterministe** — offset (direction/distance) et cadence via `_hash_noise` /
  `hash_gauss` (comme `reproduction.py`). **Zéro RNG live** (philo #3).
- **Coût Vigueur sur la mère** — cloner puise l'énergie propre de la plante →
  arbitrage émergent graines ↔ ramets (une plante qui tapisse investit moins
  dans la reproduction sexuée).
- **Établissement conditionné** (§2.1c) — le ramet ne prend QUE si le plot cible
  n'est pas saturé (couverture < seuil pour sa strate) ET si le gate de mode est
  satisfait (lumière au sol pour stolon, quelconque pour rhizome). Le caractère
  **envahissant** du bambou/menthe émerge de `rhizome` (portée + tolérance ombre),
  pas d'un flag « envahissant ».
- **Cap perf** — le gate de couverture borne mécaniquement le nombre de ramets →
  protège le `LightField` (déjà 53 % CPU) d'une explosion de plantes.

### 2.3 — Empilement multi-strates VISIBLE (brique 3)
Rendu Godot : ordre de dessin **par strate, arrière→avant**
(`sol → basse → moyenne → haute → grimpante`), y-sort **à l'intérieur** de chaque
strate. Résultat : le couvre-sol se dessine SOUS la potagère, SOUS la grimpante →
la superposition est lisible, la luxuriance se **voit**. Le champ de couverture
(§2.1) est rendu en teinte/densité au sol.

### 2.4 — Empreinte propre à l'espèce (brique 4)
`canopy_r` pilote **déjà** ombre + uptake (écologie). On **n'ajoute pas** de champ
écologique concurrent. On ajoute :
- **(a) Silhouette** — descripteur data par espèce (`silhouette ∈ {touffe,
  rosette, étalée, dressée, tapis, …}`) lu par le renderer pour dessiner la bonne
  forme (trèfle ras ↔ courge étalée ↔ tournesol dressé).
- **(b) Override d'empreinte CIBLÉ** — seulement là où le défaut de strate ment :
  la **courge** est strate `basse` mais s'**étale** au sol → `canopy_r` élargi par
  override espèce. Overrides limités aux espèces **hors golden** → dérive neutre.

## 3. Philo de design — conformité

- **#1/#2 (flux, pas de malus direct)** — la couverture agit par évaporation et
  germination d'adventices (flux → contrainte), jamais en touchant la santé d'une
  plante. Le clonal est une *reproduction*, pas un bonus.
- **#3 (déterminisme)** — clonal 100 % hash, zéro RNG vivant.
- **#4 (run éternel)** — les colonies clonales enrichissent la persistance du sol.
- **#5 (indices visuels)** — luxuriance = empilement + tapis visibles, pas un
  chiffre. Le taux de couverture se *voit* (densité), ne s'affiche pas.
- **#6 (sagesse écologique)** — semer dense / laisser tapisser = hypothèses ;
  l'écosystème répond (auto-limitation, ombre, envahissement). Méthode
  scientifique préservée.
- **#7 (hétérogénéité)** — offsets clonaux hashés → colonies propres à chaque terrain.

## 4. Coût perf

- Champ couverture : **1 scatter** de plantes/tick (stamp d'empreinte), coût ~
  identique au stamp de canopée. Pas de sweep de grille. Budget ≤ +10 %/tronçon.
- Clonal : émission cadencée (pas chaque tick), gate couverture borne la
  population → pas d'inflation du `LightField`.

## 5. Découpage (perf-first, golden discipliné)

| # | Tronçon | Golden |
|---|---------|--------|
| 1 | Champ `couverture_sol` + hooks évaporation & adventices | **RE-FIGÉ** (humidité dérive sur plot couvert ; golden porte Clover) |
| 2 | Mécanique clonale (ramets déterministes, gate couverture, coût Vigueur) | **RE-FIGÉ** (trèfle stolonifère → ramets dans le golden) |
| 3 | Empreinte/silhouette par espèce (descripteur + override ciblé) | NEUTRE (overrides hors golden) |
| 4 | Catalogue clonal ① : fraisier + menthe + trèfle stolonifère + 5 voix | NEUTRE (hors scénario) |
| 5 | Catalogue clonal ② : framboisier + bambou traçant + violettes + 5 voix | NEUTRE |
| 6 | Vue Godot : empilement visible + couverture rendue + silhouettes + colonies + pont + banc F5 `luxuriance` | INTACT |

Chaque re-figeage (T1, T2) est **localisé, expliqué, prévu** par son kickoff —
`/sprint-auto` refuse tout re-figeage non annoncé.

## 6. Hors périmètre (notés, pas dans ce sprint)

- Habitat faune dans le tapis clonal (couplage MacroLife) — extension future.
- Interaction rhizome bambou ↔ mycélium/mycorhize — hors scope.
- Éclaircissage de co-occupants de **même hauteur** — remède déjà conçu
  (`CONCEPTION_COMPETITION_INTRAPLOT §2.3 Q4`), non déclenché ici.
