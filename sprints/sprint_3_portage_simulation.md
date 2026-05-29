# Sprint 3 — Portage de la simulation Python → C#

**Statut** : à faire
**Prérequis** : Sprint 2 terminé (orchestration C# en place et fonctionnelle)
**Estimation** : 3 à 5 sessions (sprint le plus long jusqu'ici)
**Objectif** : porter `effects.py` et `engine.py` en C#, valider la
parité comportementale Python ↔ C# sur 1 an de simulation avec mêmes
seeds, et résoudre la dette D10 (divergence OM tri-compartiment).

---

## Avant de commencer

1. **`CLAUDE.md`** est chargé. Section « Source de vérité » et
   « Architecture courante » à relire attentivement.
2. **`journal.md`** — dettes D5, D6, D10 (effects.py et engine.py non
   portés, divergence OM tri-compartiment).
3. **Memory** — `project_python_source.md` (canon technique),
   `project_status.md` (avancement), `project_game_vision.md` (vision
   actée).
4. **Code Python à lire absolument** (la source de vérité) :
   - `data/code/effects.py` — système d'effets hybride probabiliste
   - `data/code/engine.py` — boucle 52 semaines, succession, transitions
     saisonnières, aléas météo
   - `data/code/models.py:EFFECT_REGISTRY` et le décorateur
     `register_effect` (mécanisme des callbacks complexes)
5. **Code C# à étendre** :
   - `core/EcologySystem.cs` — squelette en place depuis Sprint 2
   - `core/GridField.cs:EcoFields` — déjà en avance sur Python (OM
     tri-compartiment, PathogenPressure) — la dette D10 sera levée par
     ce sprint en remontant ces avances vers Python OU en clarifiant
     qu'on ne les remonte pas
   - `core/TileData.cs`, `core/PlantData.cs`, `core/PlantCatalogue.cs`

---

## Mission

Le moteur C# n'a aujourd'hui aucune logique de simulation active. Tout
est dans les fichiers Python. Ce sprint apporte cette logique en C#,
**en respectant scrupuleusement le comportement Python** (qui est la
source de vérité).

À la fin : lancer `main.py` (Python, 10 ans simulés) et la version C#
avec le même seed produisent des **états finaux comparables** sur les
métriques agrégées (`EcoFields.Summary()`).

---

## Tâches dans l'ordre

### T1. Concevoir l'équivalent C# du registre d'effets
- `EFFECT_REGISTRY` Python est un dict global de callbacks décorés
  (`@register_effect`)
- En C# : `public static class EffectRegistry { public static Dictionary<string, Func<...>> Effects { get; } }`
- Penser à la signature exacte (param : `effect` dict, `plant`,
  `tile`, `gameState`) — la modéliser proprement en C# (probablement un
  record `EffectContext`)

### T2. Porter les classes de mutations (`effects.py:25-73`)
- `AddRondelle`, `RemoveRondelle`, `ReduceHealth`, `AddScore`,
  `InjectField`, `PropagateDisease`, `Notification`
- En C# : records ou classes immutables dans `core/Effects.cs`
- Garder les mêmes noms — facilite la relecture côté Python

### T3. Porter le résolveur (`effects.py:resolve`)
- C'est la fonction centrale du moteur d'effets
- Cas par cas : `inject_field`, `add_rondelle`, `reduce_rondelle`,
  `reduce_health`, `score`, `adjacency_bonus`
- Garder la **même logique probabiliste** (utiliser un `Random`
  déterministe seedé)
- Porter le callback `basil_companion_check` comme premier exemple

### T4. Porter `apply_mutations` et `apply_disturbances`
- L'application des mutations a accès à l'état global
- `herbivory_pressure` et `background_mortality` doivent être déterministes
  avec le seed (via `_hash_noise` déjà portée dans `GridField`)

### T5. Porter `engine.py:Engine.tick_semaine`
La boucle la plus complexe — 17 étapes à respecter dans l'ordre :
1. Aléas début de saison
2. Spring flush (sem 1)
3. Lumière directionnelle
4. Hydrologie
5. Décomposition OM
6. Diffusion spatiale
7. Avancement stades
8. Effets weekly
9. Uptake racinaire
10. Mise à jour physiologie
11. Floraison (mi-saison)
12. Récolte (fin de saison active)
13. Conflits spatiaux
14. Perturbations écologiques
15. Banque de graines
16. Succession
17. Transition hivernale (sem 48-52)
18. Soil memory (fin de saison)

À implémenter dans `EcologySystem.cs:TickWeek()` (signal hooké au
Sprint 2). Brancher le timer `TurnSystem` pour appeler à 60s = 1 sem.

### T6. Porter les saisons et aléas
- Constantes `SAISONS`, `ALEAS_METEO`, `ALEAS_RAVAGEURS`
- Fonctions `saison_de`, `est_debut_saison`, etc.
- En C# : enum `Season` + helper `SeasonHelper`

### T7. Porter la succession (`engine.py:_succession`)
- C'est le mécanisme qui fait apparaître les adventices
- Utilise `SeedBank.niche_index` et `germination_candidates`
- À implémenter dans `core/SeedBankSystem.cs` (stub à remplir, dans
  namespace `Symbiose`)

### T8. Porter les transitions saisonnières
- `_spring_flush` (sem 1)
- `_winter_transition` (sem 48-52)
- Comportements `die` / `dormant` / `evergreen`

### T9. Décider de la dette D10
La version C# de `EcoFields` est plus avancée :
- OM tri-compartiment (`OmFresh`, `OmActive`, `OmStable`) — Python a
  un seul `organic_matter`
- `PathogenPressure` scalaire — Python n'en a pas
- Rain feedback couplé à `VegetationDensity` — Python a un
  `BASE_RAIN` constant

**Décision à proposer à Nico** :
- (a) Remonter ces avances vers Python (le canon évolue, on garde
  Python comme référence à jour) — **recommandé**
- (b) Régresser le C# pour matcher Python — perd des fonctionnalités
- (c) Accepter durablement la divergence et documenter — risqué

Si (a) : porter vers `fields.py` et tester avec `main.py`.

### T10. Test de parité
- Lancer `python3 data/code/main.py` avec un seed connu (ex : 42), durée
  1 an, sortie redirigée vers un fichier texte
- Lancer la version C# avec le même seed, même durée, même tuile, mêmes
  plantes initiales — exporter `EcoFields.Summary()` à chaque fin de
  saison
- Comparer les états :
  - `humidite`, `fertilite`, `microbiome` doivent être **proches à
    quelques décimales près** (tolérance à définir, ex : 5 %)
  - Liste des plantes survivantes doit être **identique**
  - Nombres de germinations spontanées doivent être proches

Si divergence importante : identifier d'où vient le delta. Le plus
souvent : ordre d'application différent, ou floats vs doubles, ou
random seed mal partagé entre Python et C#.

---

## Pièges connus

- **Déterminisme** : Python utilise `random` global + `_hash_noise`.
  En C# : utiliser `System.Random` seedé pour les choix probabilistes,
  mais **garder `_hash_noise` partout où Python l'utilise** pour les
  champs déterministes (disturbance, succession). La parité dépend de
  ça.
- **Ordre des itérations** : `for r in range(rows): for c in range(cols)`
  est strict en Python. Idem en C# — pas de parallélisme caché.
- **Floats vs Doubles** : Python utilise des doubles par défaut, C#
  des floats dans `GridField`. Les écarts d'arrondi peuvent s'accumuler.
  Soit on passe `GridField` en double, soit on tolère des deltas.
- **Logging verbeux** : `engine.py` log beaucoup pour debug. Reproduire
  un log similaire côté C# aide énormément à comparer.

---

## À produire à la fin

- [ ] `core/Effects.cs` (mutations + records)
- [ ] `core/EffectRegistry.cs`
- [ ] `core/EffectResolver.cs` ou méthodes dans `EcologySystem`
- [ ] `core/EcologySystem.cs:TickWeek` complet (17 étapes)
- [ ] `core/SeedBankSystem.cs` (succession + spring flush)
- [ ] Si décision D10.a retenue : `data/code/fields.py` mis à jour pour
      matcher C# (OM tri-compartiment, PathogenPressure, rain feedback)
- [ ] Tests de parité : un script `data/code/parity_test.py` qui
      compare un export C# (JSON) avec une simulation Python identique
- [ ] **`journal.md`** : entrée datée, dettes D5/D6 ✅ levées, D10
      résolue selon décision actée
- [ ] **Commit** ex : `Sprint 3 : portage simulation Python → C#`
- [ ] Proposer Sprint 4 (intégration mécaniques Sprint conception) à Nico

---

## Critère de fin

- En C# : démarrer le jeu, attendre 13 minutes de simulation (1 saison),
  observer dans la console les logs hebdomadaires similaires à ceux de
  `main.py`
- Test de parité automatisé : delta < 5 % sur les métriques agrégées
  d'`EcoFields.Summary()` après 1 an simulé avec même seed
- Aucune divergence sur la liste des plantes survivantes
