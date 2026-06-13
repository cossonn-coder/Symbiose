# CONCEPTION — compétition intra-plot (cohabitation, stratification & éclaircissage)

> **Statut : conception FIGÉE (2026-06-13, Q1–Q11 tranchées par Nico).** Prête
> pour l'implémentation. Fait suite au kickoff
> `sprints/sprint_competition_intraplot_conception.md` et **réalise pleinement
> Q4 du sprint planter/arroser** (« EMPILEMENT AUTORISÉ », dont la réalisation
> avait été renvoyée ici). La compétition est **déjà largement émergente** dans
> le moteur (lumière asymétrique + uptake partagé) ; ce sprint **lève le verrou**
> de germination, **ajoute la stratification** (tolérance à l'ombre + étiolement)
> et laisse l'**éclaircissage émerger** de la rareté partagée.
>
> **Re-figeage golden ANNONCÉ et MAÎTRISÉ** : la germination tourne DANS le tick
> → lever le verrou fera germer des plots auparavant exclus → la population
> dérive. S'ajoutent un **nouveau gène** (`tolerance_ombre` → vecteur de gènes +
> reproduction) et l'**étiolement** (morphogénèse). Dérive **localisée et
> expliquée**, comptée avant/après (cf. §5).

## 1. L'intention (source de vérité du « quoi »)

- **Backlog** (`BACKLOG.md`) : « plusieurs plantes peuvent ESSAYER de pousser par
  plot, la compétition (lumière/eau/nutriments) fait l'**éclaircissage naturel** ».
- **Philo #2** (CLAUDE.md) : jamais de malus direct sur les plantes — **flux →
  contrainte écologique → réponse biologique émergente**. L'éclaircissage n'est
  **pas** un « tirage du perdant » : il **émerge** de la rareté partagée (ombre,
  eau, nutriments) que les co-occupants se disputent.
- **Méthode scientifique** (philo #6) : semer dense est une **hypothèse** du
  joueur ; le milieu répond (certains lèvent, d'autres fondent) → observation →
  ajustement. Aucune densité n'est interdite ; c'est l'écosystème qui tranche.
- **Cadrage Nico (2026-06-13)** : il n'y a **pas de plot binairement « occupé »**.
  Tant que les **conditions réelles** (lumière disponible au sol, eau, nutriments)
  le permettent, une graine peut **essayer** — même si le plot porte déjà une
  plante. Hautes, grimpantes, couvre-sol **cohabitent par stratification
  verticale** : c'est la base de la **guilde** permaculturelle.

→ Le « quoi » est posé. Ce sprint tranche le « comment » exact (Q ci-dessous).

## 2. Modèle proposé (mappé sur le code vérifié, 2026-06-13)

### 2.0 Ce qui EXISTE déjà (ne pas réinventer)

La compétition est **largement en place** — le risque du sprint est de la
**ré-empiler**. Ancrages vérifiés :

- **Empilement déjà permis au niveau bas.** `world/tile.py:add_plant` crée une
  `PlantInstance` **sans vérifier l'occupation** (seulement `is_valid_plot`). Le
  verrou est **uniquement** dans la couche germination, pas dans le modèle de
  données : plusieurs plantes peuvent coexister à la même position.
- **Compétition LUMIÈRE asymétrique — émergente.** `fields/light.py:light_received`
  ne filtre une plante que par ses **voisins PLUS HAUTS** (auto-ombrage exclu, tri
  hauteur décroissante). Sur un plot partagé, **la plus haute ombre la plus
  basse** → `shade_memory` de la dominée monte (`engine.py:309`).
- **Compétition EAU/NUTRIMENTS — émergente.** `engine.py:_apply_uptake` fait
  puiser chaque plante sur **toute son empreinte racinaire** ; deux empreintes
  qui se chevauchent **épuisent le même sol** (uptake séquentiel → le second
  trouve moins). `_apply_exudates` partage de même.
- **Détection de conflit — câblée mais informative.** `world/tile.py:detect_conflicts`
  signale 2+ plantes partageant un plot via `ConflictNotification`, mais
  `resolved` n'est jamais positionné → **aucune mortalité n'en découle** (et ce
  sprint n'en ajoute pas : l'éclaircissage émerge, §2.3).
- **Phototropisme directionnel — codé.** `sim/growth.py:_phototropic_bias` biaise
  l'apex vers le gradient de lumière local (`phototropism_strength` par espèce).

### 2.1 Lever le verrou — la germination redevient affaire de conditions (Q1, Q2)

Le verrou est dans `sim/succession.py` : trois portes **sautent les plots
occupés AVANT même** de calculer la niche.

- `succession()` : `if (r,c) in occupied_roots: continue` (+ garde position).
- `spring_flush()` : même skip `occupied_roots`.
- `_lever_grains_en_attente()` : grain sur plot occupé → **patiente**.

**On supprime ces skips.** On n'injecte **AUCUN** terme « occupation » artificiel
(ce serait un malus déguisé, contraire à philo #2 et au cadrage Nico). Le frein
vient des **champs réels déjà calculés** :

- **Lumière au sol** : une plante haute sur le plot **ombrage déjà** le sol de ce
  plot (LightField, empreinte canopée) → `light` bas dans `niche_index`
  (`seedbank.py:niche_index = light × (1-root_density) × disturbance × …`). Un
  **héliophile** voit donc une niche basse sous canopée (il ne lève pas) ; un
  **sciaphile** lève quand même (§2.2).
- **Sol établi** : `soil_memory_deep` élevé → niche abaissée (déjà dans la
  formule). Un massif installé décourage la germination **sans l'interdire**.

> **Conséquence directe** : la cohabitation devient **légitime par stratification**
> (le couvre-sol sciaphile lève sous la haute) **et** la sur-densité reste **rare
> et coûteuse** (l'héliophile ne lève pas à l'ombre). Émergent de bout en bout.

**Pas de cap dur** (Q2). L'écologie borne seule. Le frein lumière + la mortalité
émergente (§2.3) suffisent ; on n'ajoute pas de plafond `N plantes/plot`.
**Vigilance perf (D32, non bloquante)** : `LightField.compute` = 53 % du CPU,
coût ∝ surface de canopée → on **surveille** la densité au calibrage (§4). Si le
test montrait un emballement, on reverrait — mais **pas de cap design** a priori.

### 2.2 Stratification — tolérance à l'ombre & étiolement (Q3, Q6, Q7)

Le moteur a déjà la **géométrie** des strates (`base.py` : champ `strate` ∈
{haute, moyenne, basse, sol, grimpante} + `STRATE_PROFILES`), **mais pas
l'écologie** : aujourd'hui l'ombre pénalise **tout le monde pareil**
(`shade_memory` uniforme, `growth_factor = 0.6 + 0.4×light`), et `niche_index`
ignore toute préférence d'ombre. Sans ajout, « couvre-sol vivant sous une haute »
**ne survit pas**. On ajoute donc le maillon manquant.

**(a) Nouveau gène `tolerance_ombre`** (Q6) — dans `GENE_NAMES`
(`plants/genetics.py`), parallèle à `tolerance_secheresse` :

```python
# plants/genetics.py
GENE_NAMES = ("hauteur", "rusticite_froid", "vigueur",
              "resistance_pathogene", "tolerance_secheresse",
              "tolerance_ombre")          # >1 = sciaphile (prospère à l'ombre)
```

- Hérité **automatiquement** via `child_genes` (canal de hash = index dans le
  tuple — l'ajout suffit, rien d'autre à câbler côté reproduction).
- **Défaut par strate** au niveau espèce : les espèces de strate `sol`/`basse`
  démarrent avec `tolerance_ombre > 1` (sciaphiles), les `haute` ≈ ou < 1
  (héliophiles). Le **gène** module ensuite individuellement (variation +
  sélection naturelle de la tolérance, cohérent avec D17/D22).

**Effets du gène** (deux points de lecture, médiés par les champs — philo #2) :

1. **Germination** (`niche_index` / tirage par espèce) : la lumière requise est
   **escomptée par `tolerance_ombre`**. Un sciaphile lève à `light` faible là où
   un héliophile échoue. C'est ce qui réalise la stratification au semis.
2. **Croissance** (`engine.py:_update_physiology`) : le `growth_factor` cesse de
   suivre la lumière brute → il suit la lumière **corrigée par `tolerance_ombre`**.
   Un sciaphile ombragé **garde une bonne croissance** (prospère) ; un héliophile
   ombragé **décroît** (et s'étiole, ci-dessous).

**(b) Étiolement** (Q7) — « filer vers la lumière ». Le phototropisme
**directionnel** existe déjà (l'apex penche). On ajoute l'**élongation accrue à
l'ombre** pour l'héliophile contrarié : sous canopée, sa croissance en **longueur
augmente** (tige grêle, entre-nœuds longs) au prix de la **robustesse** (santé /
résistance moindre). Issue :

- s'il **atteint la lumière** (trouée, gradient remonté via phototropisme) → il
  est **sauvé**, croissance normale reprise ;
- s'il **n'atteint pas** → il **dépérit** → mort par le système existant
  (`_tick_senescence_health`) → **nécromasse** (`necromass_biomass`). Aucune mort
  « verdict » : c'est le déclin émergent (Q3).

> **Garantie d'intégration à vérifier à l'impl** : le `LightField` du tick doit
> bien être passé à `grow_plant(plant, …, light_field=…)` pour **tous** les
> co-occupants ombragés (sinon `light_field=None` → apex droit, pas de
> phototropisme). C'est le « on vérifie bien qu'elles filent vers la lumière ».

### 2.3 Éclaircissage — convergence de stress existants, sans verdict (Q3, Q4, Q5)

**On lève le verrou et on MESURE d'abord** (Q3) : l'émergent (ombre + uptake
partagé) suffit-il à emporter le perdant, ou stagne-t-il ? La mort doit passer
par `_tick_senescence_health` (déclin de santé), **jamais** par une mortalité de
surpeuplement ad hoc. Si la mesure montre un **embouteillage** (des dominés
ombrés mais vivants indéfiniment), l'éclaircissage se complète par la
**convergence des stress déjà modélisés**, rendus sensibles aux co-occupants :

- **Fonte des semis** (Q4) — `_local_density` (`effects.py:349`) compte
  aujourd'hui les voisins via `plots_within_radius(r,c,1)`, **qui exclut le plot
  central** (`tile.py:131 discard((row,col))`). **Deux plantes même-position ne
  se comptent donc pas.** On **inclut les co-occupants du plot central** dans la
  densité → `damping_off` (fonte des semis) éclaircit le **semis serré** (leçon
  permaculture directe). Poids co-occupant vs voisin = §4.
- **Place racinaire & nutriments** — `root_plots` qui se chevauchent puisent le
  même sol (`_apply_uptake`) ; co-occupés, ils s'épuisent mutuellement → le
  dominé boit/mange moins → déclin. Déjà émergent ; renforcé par la densité.
- **Asphyxie** — un sol gorgé pénalise via `asphyxie_memory` (modèle eau du
  sprint précédent) ; un semis serré en sol humide cumule fonte + asphyxie.
- **Lumière (dominance)** (Q5) — **le plus haut gagne** (déjà codé) ; le plus bas
  **n'ombrage pas** au-dessus (auto-ombrage/voisins plus bas exclus de
  `light_received`) — réaliste **et** gain perf. L'antériorité joue
  **indirectement** (le premier levé est plus grand quand le second émerge).

> **Émergent, pas écrit à la main** (philo #2) : on ne fait que **rendre les
> stress existants sensibles à la co-occupation** (densité qui compte enfin le
> centre) ; aucune nouvelle règle « la plante X perd, on la tue ». La mort tombe
> de `_tick_senescence_health` comme pour la sénescence ou la sécheresse.

### 2.4 Graines plantées & polyculture (planter, espèces)

- **Graine plantée sur plot occupé : elle LÈVE** (réalise Q4 du sprint planter).
  Le skip de `_lever_grains_en_attente` est supprimé (§2.1) → le grain lève
  **sous le même frein de niche** que la succession (lumière/sol/tolérance ombre).
  Semer dans un massif établi reste **possible mais peu probable** = réaliste.
- **Aucune restriction d'espèce/famille par plot.** La cohabitation
  multi-familles est le cœur de la permaculture ; la complémentarité (fixatrice
  d'azote sous une haute, ombrage mutuel) **émerge déjà** des champs (fertilité,
  lumière). Pas de règle « une espèce par plot ».

## 3. Décisions FIGÉES (Nico, 2026-06-13)

- **Q1 → LEVER LE VERROU sans malus artificiel.** Supprimer le skip
  `occupied_roots` dans les **3 portes** (`succession`, `spring_flush`,
  `_lever_grains_en_attente`). La niche est freinée par les **champs réels**
  (lumière-sol ombragée + sol établi), **pas** par un terme « occupation ».
- **Q2 → PAS DE CAP dur.** L'écologie borne seule (vigilance perf D32, non
  bloquante — surveiller au calibrage).
- **Q3 → LEVER ET MESURER.** La mort du perdant **émerge** du déclin de santé
  (`_tick_senescence_health`) → nécromasse. Compléter par §2.3 **seulement si**
  la mesure montre un embouteillage. Jamais de mortalité « verdict ».
- **Q4 → ÉCLAIRCISSAGE par CONVERGENCE de stress existants** : fonte des semis
  (inclure les **co-occupants** dans `_local_density`, lever l'exclusion du
  centre) + place racinaire / uptake partagé + asphyxie + manque de nutriments.
- **Q5 → LE PLUS HAUT GAGNE** la lumière ; le plus bas n'ombrage pas au-dessus
  (déjà codé + gain perf).
- **Q6 (trait) → NOUVEAU GÈNE `tolerance_ombre`** dans `GENE_NAMES`, parallèle à
  `tolerance_secheresse`, hérité via `child_genes`. Défaut **par strate**
  (sol/basse = sciaphile), modulé par le gène. Entre dans **germination** (niche
  escomptée) **et** dans **croissance** (`growth_factor` corrigé).
- **Q7 (filer) → AJOUTER L'ÉTIOLEMENT.** Héliophile ombragé **élonge plus** (tige
  grêle) au prix de la robustesse → sauvé s'il atteint la lumière, sinon dépérit.
  S'appuie sur le phototropisme directionnel existant (garantir le `LightField`).
- **planter → GRAINE PLANTÉE SUR PLOT OCCUPÉ LÈVE** (sous le même frein de niche).
- **espèces → AUCUNE RESTRICTION** : multi-familles/multi-strates = guilde émergente.

## 4. Calibrage chiffré PROPOSÉ (à valider — valeurs de départ, mesurées sur la simu)

Comme les `K`/`BASE` ailleurs : **valeurs de départ**, affinées post-test.

| Constante | Valeur proposée | Justification (ancrage) |
|---|---|---|
| `tolerance_ombre` défaut sol/basse | **~1.25** | sciaphile : lève et croît à ~½ lumière sans pénalité forte |
| `tolerance_ombre` défaut haute | **~0.90** | héliophile : pénalisé dès l'ombrage modéré |
| `tolerance_ombre` (bornes) | hérite `GENE_MIN/MAX` 0.70–1.30, dur 0.40–1.60 | mêmes garde-fous que les autres gènes (`genetics.py`) |
| Lumière effective germination | `light_eff = light × tolerance_ombre` (cap 1.0) | escompte la lumière requise par la tolérance — un sciaphile « voit » plus de lumière qu'il n'y en a |
| Lumière effective croissance | `growth_factor = 0.6 + 0.4 × min(1, light × tolerance_ombre)` | même correction que la germination — symétrie |
| Poids co-occupant dans `_local_density` | **1.0** (= un voisin), normalisé `/6` | un co-occupant pèse autant qu'un voisin proche ; à affiner si la fonte est trop/pas assez vive |
| Gain d'élongation à l'ombre (étiolement) | **+30 %** de vitesse axiale quand `light_eff < 0.4`, pour `tolerance_ombre < 1` | « file vers la lumière » ; n'affecte pas les sciaphiles |
| Coût robustesse de l'étiolement | santé / résistance **−10 %** tant que la plante est étiolée | la tige grêle est fragile → dépérit si elle n'atteint pas la lumière |

**Cible d'éclaircissage** : densité intra-plot qui **augmente modérément** sur le
golden (stratification visible : 1 haute + 1 couvre-sol viables ; semis serrés
héliophiles qui fondent), **sans** explosion perf (D32). Le **rendu Godot** d'une
pile (offsets visuels, profondeur, lisibilité) = **volet vue ultérieur**, hors
scope conception.

## 5. Garanties (par construction)

- **Re-figeage golden MAÎTRISÉ et ANNONCÉ — obligatoire.** La germination est
  **dans le tick** → ce sprint **re-fige le golden** (`tests/test_golden.py`,
  smoke 2 tuiles × 4 ans). Trois sources de dérive, toutes **attendues et à
  expliquer dans le commit** :
  1. **Plus de germinations** sur des plots auparavant exclus (le verrou levé) →
     population plus dense. **Compter germinations avant/après**, vérifier que la
     dérive s'explique **seulement** par l'empilement.
  2. **Nouveau gène `tolerance_ombre`** → le vecteur de gènes change de taille →
     `child_genes` / échantillonnages décalent les canaux de hash. Dérive
     **structurelle attendue** (un gène de plus), pas comportementale.
  3. **Étiolement** → morphogénèse modifiée à l'ombre → hauteurs/segments dérivent
     là où il y a ombrage. Localisé aux plantes ombragées.
  → **Aucune autre mécanique de tick ne doit bouger.** Garde-fou de revue : une
  dérive hors de ces trois causes = couplage involontaire à corriger.
- **Déterminisme** : on **réutilise les canaux de hash existants**
  (`_hash_noise`, `succession.py`) — **aucun RNG neuf**. L'itération des plots est
  déjà ordonnée ; lever le verrou n'introduit pas d'ordre non déterministe. Le
  nouveau gène hérite sur un canal = son index dans `GENE_NAMES` (mécanisme
  existant de `child_genes`).
- **Philo #2** : l'éclaircissage **émerge** (ombre corrigée par tolérance + uptake
  partagé + densité co-occupants + asphyxie) — **aucune mortalité « verdict »**.
  La mort passe par `_tick_senescence_health`. Les deux points de lecture du gène
  (germination, croissance) **médient par le champ lumière**, jamais d'écriture
  directe arbitraire sur la plante.
- **Philo #1/#6/#7** : semer dense devient une **vraie décision** (parfois payante,
  parfois fonte) apprise par l'observation ; la stratification est une **leçon de
  guilde** ; deux terrains (sols/lumières différents) produisent des cohabitations
  différentes.
- **Perf (D32)** : pas de cap, mais le **frein lumière** (héliophiles qui ne lèvent
  pas à l'ombre) borne naturellement la canopée totale → pas d'emballement
  systématique. **Surveillé** au calibrage ; cap réintroduit **seulement** si le
  test l'impose.

## 6. Découpage d'implémentation (conception figée → kickoff d'impl séparé)

Ampleur **moyen** (peu de fichiers mais cœur écolo + vecteur de gènes + golden).
Tronçons autosuffisants, chacun préserve/re-fige **explicitement** le golden :

1. **Lever le verrou** — supprimer le skip `occupied_roots` dans les 3 portes de
   `succession.py` (`succession`, `spring_flush`, `_lever_grains_en_attente`).
   **Tronçon le plus sensible, isolé.** **Golden RE-FIGÉ maîtrisé** : compter les
   germinations avant/après, vérifier que la seule dérive est l'empilement
   (avant le gène/étiolement, pour isoler la cause). Mesurer ici si l'émergent
   tue (Q3).
2. **Gène `tolerance_ombre`** — l'ajouter à `GENE_NAMES` (`genetics.py`) ; défaut
   par strate au niveau espèce ; brancher la **lumière effective** en germination
   (`seedbank`/tirage succession) **et** en croissance (`engine._update_physiology`,
   `growth_factor`). **Golden re-figé maîtrisé** (dérive structurelle gène +
   sciaphiles qui lèvent/prospèrent à l'ombre).
3. **Étiolement** — élongation axiale accrue à l'ombre pour héliophiles
   (`growth.py` / `_elongate_emit`) + coût de robustesse ; garantir le
   `light_field` passé aux co-occupants. **Golden re-figé maîtrisé** (morphogénèse
   ombragée).
4. **Densité intra-plot** — *si Q3/mesure le justifie* : inclure les co-occupants
   du plot central dans `_local_density` (`effects.py`) → fonte des semis éclaircit
   le serré. **Golden re-figé maîtrisé.** (Sauté si l'émergent suffit.)
5. **Tests** : co-germination effective (héliophile **ne** lève **pas** sous
   canopée, sciaphile **oui**) ; stratification viable (1 haute + 1 couvre-sol
   survivent ensemble) ; étiolement (héliophile ombragé file puis sauvé/dépérit) ;
   éclaircissage observé sur N saisons (semis serré fond) ; déterminisme
   byte-identique ; **golden re-figé, dérive expliquée**.

Le **rendu Godot** de la pile (offsets, profondeur, lisibilité) = **volet vue
ultérieur**. Le **pont** `sim_server.py` n'a **rien à router de neuf** (pas de
geste ajouté) ; au plus, exposer la strate/tolérance au snapshot si la vue veut
décaler les sprites — volet vue.

---
*Réfs : `sprints/sprint_competition_intraplot_conception.md` (kickoff),
`CONCEPTION_PLANTER_ARROSER.md` (gabarit + Q4 renvoyée ici), `sim/succession.py`
(les 3 portes + `_lever_grains_en_attente`), `fields/seedbank.py:niche_index`,
`fields/light.py:light_received` (asymétrie hauteur), `sim/engine.py:_apply_uptake`
/`_update_physiology` (`growth_factor`, `shade_memory`)/`_tick_senescence_health`,
`sim/effects.py:_local_density`/`damping_off`/`necromass_biomass`,
`world/tile.py:plots_within_radius` (exclusion du centre)/`add_plant`/`detect_conflicts`,
`plants/genetics.py` (`GENE_NAMES`, `child_genes`, `tolerance_secheresse`),
`plants/base.py` (`strate`, `STRATE_PROFILES`, `phototropism_strength`),
`sim/growth.py` (`_phototropic_bias`, `_elongate_emit`), `tests/test_golden.py`.*
