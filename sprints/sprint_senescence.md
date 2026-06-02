# Sprint mortalité réaliste — sénescence, maladies fongiques, ravageurs,
# renouvellement

**Statut** : à faire — conception close le 2026-06-02
**Prérequis** : Sprint éclairement terminé (Python) — `age_years` en place sur
`PlantInstance`, interface lumière polymorphe, pérennes (`perennials.py`).
**Estimation** : 1 mini-sprint Python (puis portage C# = dette D27).
**Objectif** : faire **mourir les plantes comme dans la nature**. Aujourd'hui
seules les annuelles (hiver) et les perdantes de conflit meurent ; les vivaces
et arbres sont quasi immortels et stagnent à santé 1/3 (« zombies »). On donne
une **santé dynamique** (qui chute ET se rétablit), une **sénescence par âge**,
les **causes de mort naturelles manquantes** (fonte des semis, maladies
fongiques, dégâts de ravageurs) et un **renouvellement** des populations
(ressemis vivaces + semis d'arbres).

> Le moteur Python `data/code/` est la **source de vérité** — on conçoit et code
> ici d'abord, le portage C# est la dette D27. `genetic_factor` reste neutre 1.0
> (l'héritage est le Sprint génétique D17+D22).

---

## Avant de commencer

1. **`CLAUDE.md`** chargé. Lire l'entrée `journal.md` du 2026-06-02
   « Sprint éclairement » (contexte `age_years`, santé, pérennes) et celle de
   conception de ce sprint (décisions actées ci-dessous).
2. **Code à lire avant** :
   - `data/code/effects.py` — `herbivory_pressure`, `background_mortality`
     (⚠️ `max(1, …)` : ne tue jamais → cause des zombies), `resolve_plant_turn`,
     `ReduceHealth`, `disease_probability` côté `fields.py` (logistique microbiome).
   - `data/code/engine.py` — ordre du `tick_semaine` (lumière → stades → effets
     → uptake → physiologie → floraison → récolte → conflits → perturbations →
     banque → succession → hiver), `_winter_transition`, `_update_physiology`,
     `_succession`/`_spring_flush`, `add_necromass`.
   - `data/code/models.py` — `PlantInstance` (`age_years`, `health`,
     `current_height`, `growth_factor`), `life_cycle`/`winter_strategy`,
     `STRATE_DEFAULTS`, `PlantBase`.
   - `data/code/perennials.py` — `PerennialWoody`, `age_curve`, `reproduction_rate`
     (=0 aujourd'hui → arbres sans descendance).
   - `data/code/fields.py` — `SeedBank` (par archétype), `niche_index`,
     `tick_plant_production` (seuls les archétypes alimentent la banque).

---

## Décisions d'architecture (actées le 2026-06-02)

1. **Santé = vitalité dynamique** (couplage choisi). `health` cesse d'être un
   cliquet : il **descend** sous stress (maladie, ravageurs, sénescence) et
   **remonte** en convalescence si le milieu est bon. Supprime le plancher
   `max(1, …)` de `background_mortality` qui interdit la mort.
2. **Sénescence couplée à la santé** (pas de seuil dur, pas de proba directe).
   Au-delà de 70 % de la longévité, une pression de sénescence fait décliner la
   santé ; mort à `health = 0`. Vulnérabilité émergente : un vieux sujet meurt
   aussi plus vite d'une maladie ou d'un conflit.
3. **Causes de mort naturelles ajoutées** : fonte des semis (damping-off,
   stade semis), maladies fongiques (au-delà du mildiou Solanaceae), dégâts de
   ravageurs **létaux** sur plante affaiblie. Toutes passent par `health`.
4. **Renouvellement « comme dans la nature »** : toute plante arrivée à maturité
   disperse des propagules **avant** de mourir. Archétypes → banque existante ;
   vivaces sans archétype (trèfle…) et arbres → **ressemis/semis local**
   (provisoire, sera unifié par la SeedBank-espèce du Sprint génétique D17).
5. **Mort → nécromasse ∝ taille** (`current_height`/canopée), pas au stade. Un
   chêne centenaire mort = gros apport d'OM + **grande trouée** → relance la
   succession locale (dynamique de mosaïque).
6. **Déterminisme** : toutes les morts/germinations par `_hash_noise`, aucun RNG.

---

## Mécaniques détaillées

### M1 — Santé dynamique (récupération + plancher levé)
- Récupération (par tick, après la lumière) : si `health < 3` et `sen < 0.5`,
  `Q = lumière_reçue × min(1, humidité) × (1 − perturbation)` ;
  `p_guérison = Q × HEAL_RATE` ; `hash < p → health += 1`.
- `background_mortality` : retirer `max(1, …)` → peut atteindre 0 sur une plante
  déjà affaiblie/perturbée (reste rare, modulé par `stress_memory`).

### M2 — Sénescence par âge
- `longevity_years` par espèce (défauts par `life_cycle`). `sen = clamp((age_years
  − ONSET·L)/((1−ONSET)·L), 0, 1)`, `ONSET = 0.7`.
- `p_déclin = sen × SEN_RATE` ; `hash < p → health −= 1`. La guérison se coupe à
  `sen ≥ 0.5` (irréversible en fin de vie). `L = ∞` (annuel) → sauté.

### M3 — Bisannuelles (monocarpie)
- `life_cycle == "biennial"` : floraison/graines l'an 2 puis mort (`age_years ≥ 2`
  après floraison). Règle implémentée ; molène à coder à l'extension catalogue.

### M4 — Fonte des semis (damping-off)
- Cible : stade **semis** (`current_stage == 0`). Drivers réalistes :
  `p_fonte = DAMPOFF_BASE × max(0, humidité − seuil) × (1 − protection_microbiome)
  × densité_locale × facteur_saison_fraîche`. `hash < p → health = 0`.
- Leçon permaculture : ne pas semer trop **humide / dense / froid** ; un sol
  vivant (microbiome) protège. Réutiliser la logistique de `disease_probability`.

### M5 — Maladies fongiques (généralisées)
- Plantes adultes : `p_fongique = FUNGAL_BASE × humidité × densité_locale
  × (1 − protection_microbiome) × susceptibilité_famille`. `ReduceHealth`.
- Le mildiou Solanaceae existant devient un cas particulier (susceptibilité
  élevée). Aromatiques/diversité réduisent la pression (déjà partiellement là).

### M6 — Ravageurs létaux
- Étendre `herbivory_pressure` + aléas ravageurs : sur une plante **déjà
  affaiblie** (`health ≤ 1`) ou forte infestation (monoculture × peu
  d'auxiliaires), les dégâts peuvent **tuer** (lever le non-létal implicite).
- Leçon : biodiversité + auxiliaires = régulation ; monoculture = vulnérabilité.

### M7 — Renouvellement
- Vivaces sans archétype + arbres mûrs (`age_years > maturity_years`) : à la
  saison des graines, `p = reproduction_rate` (hash) → **semis** même espèce
  (`age_years = 0`) sur un plot **libre** à portée de dispersion, gated par la
  niche (lumière/espace). Provisoire → remplacé par D17 (SeedBank-espèce) + D22.

---

## Données à calibrer (au run 500 ans)

**`longevity_years`** (proposition à valider) :

| Espèce | Type | L (ans) |
|---|---|---|
| annuelles (tomate, poivron, haricot, tournesol, basilic, bourse) | annuel | ∞ (hiver) |
| Molène | bisannuel | 2 |
| Minette, Pâturin | vivace courte | 3 |
| Trèfle | vivace | 5 |
| Pissenlit | vivace longue | 8 |
| Cerisier | arbre | 60 |
| Pommier | arbre | 70 |
| Figuier | arbre | 80 |
| Noyer | arbre | 200 |
| Chêne | arbre | 500 |

Défauts par `life_cycle` : annual → ∞, biennial → 2, perennial herbacé → 5,
`PerennialWoody` → dernier point de `age_curve` × 1,5 (repli).

**`maturity_years`** (âge de première fructification) : fruitiers ~5, noyer ~15,
chêne ~25 ; herbacées : dès le stade mature.

**Constantes** : `SENESCENCE_ONSET = 0.7`, `SEN_RATE`, `HEAL_RATE`,
`HEAL_SEN_CUTOFF = 0.5`, `DAMPOFF_BASE`, `FUNGAL_BASE`, rayon de dispersion.

---

## Sous-objectifs (ordre suggéré)

1. **`models.py`** — `longevity_years` + `maturity_years` (+ défauts par
   `life_cycle`) ; `PerennialWoody.longevity_years` dérivé de `age_curve`.
2. **`fields.py`** — constantes (sénescence, guérison, damping-off, fongique).
3. **`effects.py`** — lever le plancher de `background_mortality` ; damping-off ;
   maladies fongiques généralisées ; ravageurs létaux.
4. **`engine.py`** — `_tick_senescence_health` (sénescence + guérison) ; mort
   bisannuelle ; nécromasse ∝ `current_height` ; renouvellement (M7).
5. **Calibration** — longévités + constantes au run 500 ans.
6. **Test** — un arbre meurt vers `L`, la santé remonte sous bonnes conditions,
   le verger se renouvelle, 500 ans stables.

---

## Critères de validation

1. Un arbre planté vit ~`longevity_years` puis **meurt** (fini les 500 ans à 1/3).
2. La santé **remonte** sous bonnes conditions → plus de zombies bloqués à 1/3.
3. Des semis meurent de **fonte** en conditions humides/denses, protégés par un
   sol vivant.
4. Une **monoculture** appauvrie subit maladies/ravageurs (mortalité visible) ;
   une polyculture diverse résiste.
5. **Renouvellement** : populations (vivaces + arbres) persistent par ressemis,
   pas par individus immortels.
6. **500 ans stables**, pas d'extinction généralisée. Déterminisme préservé.

---

## À produire à la fin

- [ ] `models.py`, `fields.py`, `effects.py`, `engine.py` modifiés
- [ ] Longévités + constantes calibrées au run 500 ans
- [ ] Test : mort par âge + guérison + fonte + renouvellement vérifiés
- [ ] `journal.md` : entrée datée de calibration ; `CLAUDE.md` à jour
- [ ] Mémoire (`project_status.md`, `project_python_source.md`)
- [ ] Dette **D27** : portage C# de la mortalité réaliste
- [ ] Commit HEREDOC

---

## Dépendances / fenêtres

- **D17 (SeedBank-espèce)** + **D22 (héritage)** : le renouvellement M7 est
  **provisoire** (semis local direct). À unifier dans une vraie banque d'espèces
  génétique au Sprint génétique — ne pas doubler le système ici.
- **Catalogue** : molène (bisannuelle) et les 3 autres espèces non-Python à
  coder à l'extension catalogue (D26) ; la **règle** bisannuelle est posée ici.
