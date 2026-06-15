## 2026-06-03 — Sprint conception météo / climat + signes diégétiques

**Conception seule, aucun code.** Livrable = spec dédiée à étudier :
[`docs/conception/CONCEPTION_METEO.md`](docs/conception/CONCEPTION_METEO.md). Couvre **D16**
(forecast) et **Z2** (signes diégétiques). Climat de référence : Normandie
~49°N, océanique tempéré.

### Le pivot

**Décision :** remplacer le tirage météo `random.choice(ALEAS_METEO)`
(`sim/engine.py`) — un **RNG live qui viole la philo #3**, ne tenant que par la
béquille `random.seed(42)` — par une **fonction pure `weather_at(seed, week)`**
à base de `_hash_noise`. Tout le reste du moteur a déjà migré vers le hash
déterministe ; la météo était le dernier îlot non conforme. Une fonction pure du
temps est *évaluable en avance sans avancer la simulation* → débloque
gratuitement le forecast, les signes et la prévisibilité au transcendant.

**Principe-colonne :** la météo est intégralement déterministe. La maîtrise ne
change pas *ce qui arrive*, seulement *combien le joueur sait le lire*.
L'imprévisibilité ressentie est **informationnelle (UX)**, jamais simulatoire.

### Décisions actées

- **Modèle climatique** à 3 échelles : normales saisonnières lisses (sinusoïdes
  température/pluie), dérive interannuelle (réutilise `climate_stress`), et
  événements hebdo tirés par hash (canaux-sentinelles `K_OCC/K_PICK/K_MAG`).
  Catalogue : gel/gelée tardive, canicule, sécheresse (état multi-sem.), tempête,
  grêle (localisée), pluie prolongée (état), redoux. Distinction
  **événement ponctuel** vs **état climatique** (déduit sur fenêtre, sans état
  stocké).
- **Couplage par le milieu uniquement** (philo #1/#2) : chaque événement = des
  deltas de champ + durée, la réponse biologique émerge (`drought_memory`,
  `disease_probability`, gates de croissance, nécromasse).
- **Décision :** ajouter un **champ `temperature` ambiant** (`GridField`, comme
  `lumiere`/`disturbance`) + gate `ok_temp` dans `_avancer_stades` (Option B,
  recommandée). Option A « température implicite » écartée (gel/redoux
  acrobatiques). **Coût assumé : re-figer le golden** au sprint d'implémentation.
- **Décision :** gel/grêle/verse ne sont plus des malus directs (`ReduceHealth`)
  mais `sévérité × (1 − gène_rusticité) × (1 − protection_locale)` → flux ×
  génotype × milieu. Implique un **gène de rusticité au froid** (vecteur
  génétique extensible).
- **Forecast (D16) reformulé/simplifié** : `forecast = [weather_at(seed, week+k)]`,
  cohérent par construction, reproductible. Plus de « tirage décalé à stocker ».
- **Signes (Z2)** : table signe→événement ; le signal est toujours parfait,
  c'est l'**interprétation** qui dépend de la maîtrise. **~20 % sans signe**
  via masque déterministe `_hash_noise(...) > 0.20`, levé au transcendant.
- **Palier météo** (5 niveaux) : découverte (signes non nommés) → investissement
  (co-occurrences) → **maîtrise** (carnet/encyclo interprétatifs, seuil clé) →
  expertise (horizon 2 sem. + intensité/localité) → transcendant (les 20 %
  deviennent lisibles).
- **Vigueur** : préparation (temps figé, modérée — paillage, voiles, brise-vent,
  ombrière, buttes, réserve d'eau) vs réaction (temps réel, élevée — arrosage
  ciblé, sauvetage, tuteurage, récolte d'urgence). Anticiper coûte peu, réagir
  coûte cher (philo #1).

### Reste (sprint d'implémentation ultérieur, découpé en sous-sprints)

`weather_at`/`forecast`/`WeatherEvent` + masque de signe ; champ `temperature` +
`ok_temp` ; gène de rusticité ; réécriture `appliquer_alea` ; retrait de
`random.seed(42)`. **Doit préserver / re-figer `tests/test_golden.py`.**

---
