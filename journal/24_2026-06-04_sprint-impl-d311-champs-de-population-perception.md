## 2026-06-04 — Sprint impl. D31.1 : champs de population + perception (Python)

**Périmètre** (strictement le visuel, aucun câblage à la santé) : implémenter le
mécanisme `PopulationField` générique conçu en `CONCEPTION_VIE_MACRO.md`, ses 4
instances, et la règle d'échantillonnage sprite — **calculés mais lus par rien**,
golden engine intact.

**Livré :**
- `fields/population.py` (nouveau) — `TrophicSpec` (data-driven : ressource /
  habitat / prédateurs / canal `_hash_noise` dédié), `PopulationField`
  (sous-classe `GridField`, patron `DisturbanceField`), les 4 specs
  (`build_population_specs` : ravageur ← feuillage, monoculture ; auxiliaire ←
  ravageur, nectar+stabilité ; pollinisateur ← fleurs, rondelle ; vers_de_terre
  ← microbiome/OM, sol non perturbé), et `sample_sprites` (fonction PURE
  densité→entités, position `_hash_noise(seed, salt+slot, r, c)` **indépendante
  de la semaine**, cap par plot, scalaire `activite`).
- `fields/ecofields.py` — `EcoFields` détient `populations` (créés en
  `__post_init__`) et les ticke via `tick_populations(tile, plants)` dans l'ordre
  trophique (ravageur d'abord → lit l'auxiliaire de la semaine précédente =
  décalage). **Pas ajouté à `summary()`** (sinon le digest golden bougerait).
- `sim/engine.py` — appel `eco.tick_populations(tile, tile.plants)` en **étape
  13b**, après les autres champs (température/perturbation à jour). Aucun log
  produit.
- `tests/test_population.py` (+ `population_hash.txt`) — golden de champ
  (densités reproductibles, hash `2e6c3075…`) + bornes ∈[0,max] + cap sprites +
  positions indépendantes de la semaine.

**Décision technique (itération en cours de sprint) :** la forme du tick conçue
« cible = naissance − mort » (mort = somme de termes ABSOLUS : froid, perturbation)
**plafonnait toutes les densités à zéro** — à basse population les morts absolues
l'emportent et la cible est clampée à 0, rien ne s'établit. Remplacée par une forme
**multiplicative** : `cible = capacité_de_charge × survie`, où
`capacité = clamp(resource_w·ressource + habitat_w·habitat)` et
`survie = chaleur · (1−préd) · (1−perturbation)`. La cible **ne dépend pas de la
pop courante** → colonisation depuis zéro ; le froid (chaleur→0 l'hiver) et la
famine (pop>capacité) deviennent **implicites**. Trace de validation : montée
estivale, pic automnal ~0.2, déclin hivernal, et **décalage proie→prédateur
visible** (ravageur devance l'auxiliaire qui rattrape puis dépasse). Quantum
sprite calé à 0.06 sur cette plage émergente (2-3 sprites/plot au pic).

**Garde-fous tenus :** golden engine **INTACT** (`ee79dd66…`, vérifié avant *et*
après le changement de modèle — rien ne lit les champs en D31.1) ; canaux
`_hash_noise` dédiés par guilde, décorrélés ; terme `predator` (`effects.py:487`)
laissé en place (retiré seulement en D31.2) ; règle de couches respectée
(`population` n'importe que `grids`+`noise`, `ecofields` l'orchestre) ;
`test_genetique` 20/20, `test_auxiliaires` OK, `main.py` démarre.

**Reste D31 :** D31.2 (câblage écolo : herbivorie←ravageur, prédation←auxiliaire,
`pollinator_reach`←pollinisateur, aération←vers → **re-figeage golden unique**) ;
D31.3 (façades `vigueur_*` + gestes favoriser/écraser/fourche-bêche). Calibrage
(quantum, inerties, amplitude boom-bust) = post-test.

### Hash golden (journal de re-figeage)
`ee79dd66…` → **inchangé** (D31.1 golden-neutre par construction). Nouveau golden
de champ dédié : `population_hash.txt` = `2e6c3075…`.

---
