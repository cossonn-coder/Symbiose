# CONCEPTION — Équilibre de l'invasion d'adventices & levier PAILLAGE

> Conçu le 2026-07-06 (`/conception`, dette **D69**). Sprint
> `sprints/faune/trophique/sprint_equilibre_invasion/` (kickoffs 01-08). Source de vérité
> Python `data/code/`. Golden re-figé **une seule fois** (tronçon ②, localisé,
> annoncé). Ce doc reflète la conception ARBITRÉE, pas la version challengée.

## 0. Pourquoi (le fil, depuis la perf)

Le tick coûte **∝ N** (nombre de plantes vivantes). L'investigation perf du
2026-07-06 a montré qu'à 8 tuiles **N ne se borne pas** (enveloppe d'été 603 an1
→ 1043 an5) : l'invasion férale est donc **un problème de perf** (philo #4 : coût
borné à horizon infini) autant que de gameplay. Le monde `config="full"` démarre
53 cultivées plantées, **balayées en < 1 saison** (dès s26 il ne reste que 8
haricots ; tout le reste = pionnières levées de la seedbank).

**Objectif** : rendre l'invasion **infléchissable par le joueur via le MILIEU**
(philo #1), pas la supprimer — un jardin non tendu **doit** retourner à la friche
(philo #6). On **ajoute des leviers** + on **donne le temps** de réagir.

> ⚠️ **Après ce sprint, revenir à la perf pure** : D67 (LOD des émetteurs
> d'ombre) + LightField, redevenu poste #1 depuis la mémoïsation `761bbe9`.

## 1. Cadre philo (garde-fous)

- **#1** : le joueur agit sur le milieu (pailler, broyer, récolter, planter) ;
  l'action directe (déraciner une adventice) reste possible mais coûteuse.
- **#2** : **aucun bonus/malus direct sur les plantes**. Le mulch amende des
  CHAMPS (germination, humidité, pH, OM, habitat) ; la réponse biologique émerge
  au tick. Les cultivées ne sont **jamais** rendues invincibles — leur survie
  émerge du milieu tendu (mulch, couvert, densité).
- **#3** : déterministe, zéro RNG vivant (mulch = champ scalaire, gestes
  event-driven).
- **#5** : indices visuels (texture de mulch au sol, faune qui s'abrite), pas de
  chiffres en HUD.
- **Interconnexion** : le paillage touche germination + banque de graines +
  évapotranspiration + OM + pH/NPK (selon nature) + champignons (hook) + faune
  (abri). Aucun acteur isolé.

## 2. Le levier PAILLAGE (moteur)

### 2.1 Champ `paillage`
Nouveau `GridField` par plot (profondeur de mulch ∈ [0,1]), patron de
`couverture_sol`. Détenu par `EcoFields`, tické après les autres champs.
- **Au repos `paillage=0` partout** → tous les facteurs valent ×1 → **golden
  INTACT** (le smoke n'a aucun geste `pailler`).

### 2.2 Effets par plot (tronçon ③)
- **Germination férale ↓** : dans `succession.py`, `niche *= (1 - paillage)`
  (au-dessus d'un seuil, cutoff dur — miroir de la vis A couverture). Un plot
  paillé ne laisse plus lever d'adventice.
- **Vieillissement des graines ↑** : sous mulch, `SEED_VIABILITY_LOSS` local est
  accéléré (les graines enfouies s'épuisent) → effet DURABLE (mulcher longtemps
  vide la banque locale, `fields/seedbank.py`).
- **Évapotranspiration ↓ / humidité ↑** (D8) : le mulch réduit l'évaporation du
  plot (patron `couverture_sol`→évaporation déjà en place), tempère le sol.
- **Décomposition → `om_stable`** : le mulch se décompose lentement (décroissance
  du champ) en matière organique stable → nourrit le sol, et **décroît** (à
  ré-appliquer). C'est le canal d'interconnexion qui « ferme la boucle ».

### 2.3 Geste `pailler` (tronçon ③)
`sim/actions/gestes.py` : pose du mulch sur une **zone** (coût Vigueur modéré,
phase de planification). Consomme un **stock de matière** (tronçon ④). Binaire :
appliqué seulement si coût payé ET stock disponible (patron `epandre`/`planter`).

## 3. Matériau & nature du mulch (tronçon ④)

Le mulch n'est plus abstrait : il **vient de quelque part** (interconnexion).

### 3.1 Deux voies d'approvisionnement
- **BRF par broyage** : geste `broyer` sur le **bois** (`bois_restant` des
  squelettes, pile de bois) → **Bois Raméal Fragmenté**.
- **Récolte de plantes à paille** : récolter blé/chanvre/sapin (tronçon ⑤) →
  paille / aiguilles dans le stock.

Le stock de mulch est une jauge (par avatar ou par tuile — patron
`compost_mur`/`player_seed_bank`, tranché au tronçon ④).

### 3.2 Trois natures — chaque propriété = un couplage EXISTANT
| Nature | Décompo | Effet distinctif | Couplage |
|---|---|---|---|
| **BRF** (bois broyé) | lente | **faim d'azote** transitoire ; nourrit champignons saprophytes | NPK (`n`), hook mycélium |
| **Paille** (blé, chanvre) | moyenne | forte rétention d'humidité ; chanvre tient + longtemps (fibres) | humidité/ET |
| **Aiguilles** (sapin) | lente | **acidifiant** (pH↓ local) ; léger frein allélopathique à la germination | pH, germination |

Tous partagent : germination↓ + humidité↑ + abri faune + décompo→OM. Ils
**diffèrent** sur vitesse / faim d'azote / pH / affinité fongique. Valeurs
calibrées au tronçon ④ (data-driven, un dict de propriétés par nature).

> **Hook mycélium** : le BRF est le substrat des saprophytes
> (`design_mycelium_interconnexions`, figé mais non implémenté). On pose un
> simple hook (le BRF marque un plot comme riche en bois), pas de dépendance.

## 4. Catalogue paille/BRF (tronçon ⑤)

Ajout de **3 espèces** (règle « l'espèce sert l'idée » + « toutes ses voix ») :
- **Blé** (*Triticum*) — graminée annuelle, paille de référence.
- **Chanvre** (*Cannabis sativa*) — fibre, paille durable, plante-service.
- **Sapin** (*Abies*) — conifère, aiguilles acidifiantes + rameaux → BRF.

Chacune reçoit ses **5 voix** (encyclopédie 3 niveaux, carnet/concepts, pages
secrètes si lore, magazine/famille, événements de cycle de vie) — cf.
`docs/narration/voix/conception_voix_narratives.md`.

## 5. Paillage ↔ vie macro : ABRI (tronçon ⑥)

Les `PopulationField` (faune) lisent `paillage` comme **habitat/abri** : les
guildes **ombrophiles** n'aiment pas le plein soleil sans couvert → un plot
paillé devient un refuge (terme d'habitat += f(paillage)). Émergence recherchée :
la faune auxiliaire colonise les zones paillées, visible au F5 (philo #5).
Golden INTACT (paillage=0 au repos → habitat inchangé).

## 6. Couplage planter + pailler par MAÎTRISE (tronçon ⑦)

Au-dessus d'un **palier de maîtrise** (de la plante concernée), le geste
`planter` **auto-paille** le plot : « on paille systématiquement quand on
plante, une fois qu'on maîtrise ». La **nature du mulch dépend de la plante ET de
la maîtrise** (arbre → BRF ; potagère → paille ; plus la maîtrise est haute, plus
le mulch est adapté/efficace). Consomme le stock si dispo, sinon plante sans
mulch. Golden INTACT (le smoke n'a pas la maîtrise requise).

## 7. Recalibrage des freins férals (tronçon ②)

**Seul re-figeage du sprint** (localisé, annoncé, mesuré ① avant/après).
- **Cible** : friche en **~2-3 saisons** (pas < 1) ; plateau N **~600-700 à 8
  tuiles** (vs 1043+).
- **Knobs** (pas le cutoff dur) : `COUVERTURE_GERM_EXP`, enrichissement de la
  seedbank (`tick_disturbance_enrichment`/`tick_late_succession_enrichment`),
  base de la vague de printemps. La vis A avait été calibrée sur **2 tuiles**
  (« ~190 »), d'où la dérive à 8.
- **Méthode** : sweeps mesurés par `tools/diag_population.py` (tronçon ①), on
  ajuste jusqu'à la cible, on fige le nouveau golden + `population_hash`.

## 8. Banc « monde propre » + démo (tronçons ① et ⑧)

- **① Preset `config="propre"`** dans `cmd_init` : mêmes tuiles + maison, mais
  **seedbank férale vidée + succession férale coupée**. Sert au F5 (observer les
  cultivées seules), aux tests, et à isoler la perf à N maîtrisé (croise le bras
  fidélité de D67). `tools/diag_population.py` promu depuis `/tmp` dans `tools/`.
- **⑧ Démo zone paillée sud** : `build_world_full` gagne une **planche plein sud
  paillée** avec **tomate/basilic/poivron/tournesol** (les cultures qui
  mouraient) → démonstrateur vivant du levier au F5. Hors golden smoke → INTACT.

## 9. Découpage (perf-first, vue Godot en dernier)

| # | Tronçon | Golden |
|---|---|---|
| ① | Banc « monde propre » (`config="propre"`) + diag `tools/diag_population.py` | INTACT |
| ② | Recalibrage freins férals (onset ~2-3 saisons, N~650/8 tuiles) | **RE-FIGÉ** localisé annoncé |
| ③ | Paillage moteur : champ + geste `pailler` + effets (germ↓/ET↓/graines↑/→OM) | INTACT |
| ④ | Matériau : `broyer`→BRF + récolte paille → stock ; 3 natures data-driven | INTACT |
| ⑤ | Catalogue blé/chanvre/sapin + 5 voix chacun | INTACT |
| ⑥ | Paillage ↔ vie macro (abri) | INTACT |
| ⑦ | Couplage planter+pailler par maîtrise (auto-paillage) | INTACT |
| ⑧ | Vue Godot (pailler/broyer cliquables, rendu mulch+BRF, abri faune) + démo sud | INTACT |

## 10. Coût perf

- Champ `paillage` : scalaire/plot, tick de décroissance = ~gratuit (patron
  `couverture_sol`). Lecture par germination/seedbank/ET/population = accès
  `at_plot` déjà comptés.
- Recalibrage ② : constantes → coût neutre, mais **borne N plus bas** → **gain
  perf net** (tick ∝ N).
- Bilan : le sprint est **perf-positif** (l'objet même est de borner N).
