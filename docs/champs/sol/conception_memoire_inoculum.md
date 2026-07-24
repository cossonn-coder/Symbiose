# Conception — Mémoire d'inoculum du sol (« terre malade » / rotation)

> Origine : `/conception D10` (2026-07-24). D10 (« réconcilier `PathogenPressure`
> C#→Python ») est **caduque dans sa lettre** — Option B : le `EcoFields` C# est
> du code MORT (rien de vivant ne l'appelle), Godot est une vue nourrie par le
> pont Python. D10 se scinde en un **ménage** (supprimer le scalaire C# mort) et
> une **idée écologique** retenue par Nico : porter dans Python, source de vérité,
> une **mémoire d'inoculum de tuile** persistante que le modèle actuel n'a pas.
>
> Sprint associé : `sprints/champs/sol/sprint_memoire_inoculum/`. Lignée D10,
> croise D27 (santé), D22b (`resistance_pathogene`), D38 (hygrométrie→maladie),
> D40 (vitesse décompo), le sol vivant (microbiome), la succession/seedbank.

## 0. Le trou que ça comble

Python a déjà un modèle de maladie **riche PAR PLANTE** : `fungal_disease`
(humidité × densité de même famille × `fungal_susceptibility` familiale × gène
`resistance_pathogene` individuel × vent séchant/dispersant), `infection_memory`
par plante (charge vécue = SAR/priming), `damping_off` (fonte des semis),
`disease_probability(r,c)` (protection microbiome logistique).

**Ce qui manque** : `infection_memory` meurt AVEC la plante. Une tuile qui a
porté une monoculture malade repart **vierge** à la plantation suivante. C'est
écologiquement faux pour les pathogènes du sol et des résidus (mildiou hivernant
sur débris, verticillium, agents de fonte) et ça prive le jeu de toute
**pédagogie de rotation** — pourtant la leçon permaculture n°1 (philo #2/#6).

**La mécanique** : un champ édaphique qui se souvient des maladies passées,
indexé par famille (pédagogie de rotation), nourri par les infections réalisées,
rabattu par le sol vivant et le temps.

## 1. Le champ `InoculumField`

Un champ détenu par `EcoFields` (paquet `fields/ecofields/`, classe assemblée
dans `container.py`). Contrairement aux `GridField` denses (humidité, microbiome…),
il est **sparse et indexé par famille** :

```
load : dict[(r, c)] -> dict[famille -> float]      # charge ∈ [0, INOC_MAX]
```

- **Par famille** (décision D3) : l'inoculum est hôte-spécifique. Replanter la
  MÊME famille sur un plot chargé = maladie amplifiée ; **tourner vers une autre
  famille échappe à la charge, ÉMERGENT** (aucune règle « rotation » spéciale :
  le bucket d'une famille absente décroît simplement jusqu'à zéro).
- **Sparse** : seuls les plots ayant hébergé une maladie ont une entrée ; un
  bucket retombé sous `INOC_EPSILON` est supprimé (borne le coût, cf. §7).
- API : `at(r, c, famille) -> float`, `total(r, c) -> float` (somme des familles,
  pour la niche molène et le rendu), `deposit(r, c, famille, q)`, `tick_decay(eco)`.

## 2. Alimentation — CONSÉQUENCE (décision D2)

Deux canaux déterministes (zéro RNG). **Jamais** de re-dérivation humidité×mono
(ce serait un second compteur de monoculture, cf. §5).

**Canal 1 — dépôt continu de la plante infectée.** Chaque tick, toute plante
vivante dont `infection_memory > INOC_DEPOT_SEUIL` dépose dans le bucket
`(son plot, sa famille)` :

```
q1 = INOC_FROM_MEMORY × (infection_memory − INOC_DEPOT_SEUIL)
```

Piggyback sur la passe maladie déjà existante (la boucle par-plante de
`apply_disturbances`/effets) → **aucune nouvelle boucle spatiale**.

**Canal 2 — pulse de résidu à la mort.** Quand une plante infectée meurt (voie
`deposer_mort`/nécromasse, `sim/effects/perturbations.py`), un dépôt ponctuel :

```
q2 = INOC_FROM_DEATH × infection_memory
```

Les débris infectés hébergent l'inoculum hivernant → leçon **nettoyage /
sanitation** (ne pas composter du matériel malade). C'est ce canal qui fait que
la terre reste malade APRÈS la disparition de la plante.

## 3. Suppression — décroissance + microbiome (décision D6)

Une passe `tick_decay` par tick sur les buckets **non vides** :

```
load ← load × INOC_DECAY − INOC_MICRO_SUPPRESS × microbiome_norm(r,c)
load ← max(0, load)        # bucket < INOC_EPSILON → supprimé (sparse)
```

- `INOC_DECAY` calé pour une **demi-vie ~2 saisons** : l'inoculum HIVERNE (la
  rotation doit durer 2-3 ans pour payer) mais finit par s'effacer.
- **microbiome** = sols suppressifs : un sol vivant DIGÈRE l'inoculum (antagonistes,
  compétition). Réutilise le levier existant (`microbiome.at_plot / MICROBE_EFFECT_REF`).
- **PAS** de perturbation/bêchage comme réducteur : ce serait un « biner pour
  guérir » anti-permaculture (le bêchage tue déjà le microbiome). Le seul remède
  actif est **restaurer la vie du sol + laisser reposer/tourner** (philo #1/#6).

## 4. Couplage à la maladie — greffe UNIQUE (décision D5)

`disease_probability` (`fields/ecofields/sol.py:108`) est le **point d'entrée
commun** de `damping_off`, `fungal_disease`, du mildiou-rondelle
(`sim/effects/resolution.py:138`) ET du signal SAR (`sim/engine/croissance.py:316`).
On l'enrichit d'un paramètre **`family` optionnel** :

```python
def disease_probability(self, r, c, base_rate=0.3, family=None):
    micro_norm = min(1.0, self.microbiome.at_plot(r, c) / MICROBE_EFFECT_REF)
    protection = 1.0 / (1.0 + exp(-6.0 * (micro_norm - 0.5)))
    charge = 0.0 if family is None else self.inoculum.at(r, c, family)
    amplif = 1.0 + INOC_GAIN * charge
    return base_rate * amplif * max(0.02, 1.0 - protection)
```

- **family passée** (`fungal_disease`, `damping_off`, mildiou) → la terre à
  Solanacées vicie les Solanacées. Structure `(1+charge) × (1−protection)` =
  offense × défense, séparation propre (miroir exact de l'ancien C#).
- **family=None** (signal SAR de `croissance.py`) → formule INCHANGÉE, sans
  inoculum → **casse la boucle de rétroaction** inoculum → signal SAR →
  `infection_memory` → inoculum. Le priming immunitaire de la plante reste piloté
  par le risque ambiant, pas par la mémoire de terre (anti-runaway, borné de fait).

## 5. Anti double-comptage (invariant de design)

`fungal_disease` lit déjà `_local_density(same_family=True)` = la **propagation
instantanée** entre voisins vivants de même famille. L'inoculum est une chose
DIFFÉRENTE : la **mémoire** du passé réalisé (dépôts §2), qui SURVIT à la mort
des plantes. Les deux sont complémentaires, pas redondants — parce que l'inoculum
n'est **jamais** re-dérivé de la densité courante (raison du rejet de la source
« style C# »). Vérification : à densité courante forte mais historique vierge,
l'inoculum est nul ; à plot fraîchement veuf d'une monoculture malade, la densité
est nulle mais l'inoculum est haut.

## 6. Molène — l'indicatrice signature (décision D4)

*Verbascum thapsus* (**bouillon-blanc**), Scrophulariaceae, bisannuelle pionnière
indicatrice. Elle **apparaît sur terre malade persistante** — l'indicatrice C#
(`PathogenPressure > 0.6`) enfin incarnée côté Python.

**Apparition** via un facteur de niche `arch_inoculum` passé à
`seedbank.germinate_candidates` (patron strict de `arch_ph`/`arch_temp`/`arch_allelo`) :

- porte de **RELÂCHE** (≠ les autres portes qui referment) : molène gatée à ~0
  sur sol sain, ~1 quand `inoculum.total(r,c) > INOC_MOLENE_SEUIL` (smoothstep) ;
- tous les autres archétypes = **1.0 neutre** → **golden INTACT quand
  l'inoculum est nul** (molène ne lève pas sur le sol sain du smoke).

**Les 5 voix** (règle « toute plante = ses 5 voix ») :
1. **Encyclopédie** (3 niveaux) — vu : rosette laineuse ; cycle : hampe florale
   bisannuelle, sol vicié/remué ; répété : indicatrice de pression pathogène,
   médicinale.
2. **Carnet** — `CONCEPT_DE` : concept *maladie / sol vicié* (interprétatif au
   palier maladie).
3. **Pages secrètes** — lore médicinal du bouillon-blanc (feuilles pectorales,
   « herbe aux mille vertus ») : voix herbier ancien / savoir paysan.
4. **Magazine** — offre famille Scrophulariaceae.
5. **Événements** — marqueurs de cycle bisannuel (rosette → hampe) au ledger.

## 7. Perf & déterminisme

- +1 champ **sparse** ; canal 1 piggyback la passe par-plante (0 boucle neuve) ;
  canal 2 sur l'événement mort ; `tick_decay` itère les buckets NON vides (borné
  par le nombre de plots ayant hébergé une maladie). Budget << +10 %/tronçon.
- **Zéro RNG** : accumulateur/décroissance purs, déterministes. Le tirage de
  germination molène réutilise le `_hash_noise` existant de `germinate_candidates`.

## 8. Ménage C# (clôt la lettre de D10)

Supprimer le code **mort** de `core/EcoFields.cs` : champ `PathogenPressure`,
`TickPathogen`, l'entrée `"pathogen"` de `Summary()`, et la lambda
`eco.PathogenPressure > 0.6f` de l'indicatrice molène (`PlantCatalogue.Indicatrices.cs`).
Chirurgie minimale, `dotnet build` doit rester vert (le registre d'indicatrices
C# est lui-même du legacy non branché ; on retire juste la référence morte).

## 9. Tronçonnage (perf-first, vue en dernier)

| # | Contenu | Golden |
|---|---|---|
| ① | `InoculumField` + 2 canaux d'alimentation + `tick_decay`, **DORMANT** (rien ne le lit dans la math du tick) | **INTACT** + verrou |
| ② | `disease_probability(family)` → fungal/damping/mildiou ; SAR reste `family=None` | **RE-FIGÉ MAÎTRISÉ** (annoncé) |
| ③ | Molène : espèce + `arch_inoculum` (porte de relâche) + 5 voix | NEUTRE visé (localisé si tirage smoke déplacé) |
| ④ | Ménage C# + vue Godot (snapshot `inoculum`, heatmap F6, banc F5 `rotation_inoculum`) | **INTACT** |

## 10. Placeholders de calibrage (post-test F5)

`INOC_DEPOT_SEUIL`, `INOC_FROM_MEMORY`, `INOC_FROM_DEATH`, `INOC_DECAY`
(demi-vie ~2 saisons), `INOC_MICRO_SUPPRESS`, `INOC_MAX`, `INOC_EPSILON`,
`INOC_GAIN` (amplif douce au ②), `INOC_MOLENE_SEUIL`. Tous à caler au banc `rotation_inoculum`.

## 11. Points F5

- Monoculture de Solanacées répétée sur le même plot → maladie qui S'AGGRAVE
  saison après saison (inoculum monte, heatmap F6 rouge).
- **Rotation** vers une autre famille → la maladie reflue (bucket Solanacées
  décroît, l'autre famille part saine).
- **Molène** qui colonise les plots durablement viciés.
- Sol vivant (microbiome haut) qui digère l'inoculum plus vite.
