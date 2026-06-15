# Sprint génétique / reproduction — banques de graines par espèce et
# héritage biparental

**Statut** : à faire — conception close le 2026-05-29
**Prérequis** : Sprint éclairement terminé (`current_height` utilise déjà un
`genetic_factor`, neutre 1.0 jusqu'ici). Voir `sprints/sprint_eclairement.md`.
**Objectif** : implémenter la séparation des banques de graines (D17) et le
moteur de génétique des populations (D22) — vecteur de gènes, héritage
biparental, pollinisation par espèce, hybridation par introgression.

> Ce sprint a été **détaché** du Sprint éclairement parce que l'empilement
> conçu (banque-sol génétique + pollinisation par espèce + introgression +
> gènes vectoriels) est un moteur de génétique des populations dont le coût
> dépasse celui des ombres. Le découpage permet de valider chaque sprint
> séparément.

---

## ⚠️ Mise à jour 2026-06-03 — synchronisation avant démarrage

Ce kickoff a été écrit le 2026-05-29, **avant** les sprints sol vivant,
succession, éclairement et mortalité réaliste. État réel du code aujourd'hui :

**Ce qui a changé et impacte le travail :**
- `reproduction_rate` est désormais **actif**. Le renouvellement provisoire
  **M7** (`engine._renewal`, mini-sprint sénescence) l'utilise pour ressemer les
  vivaces sans archétype (trèfle, achillée) et les arbres mûrs. **CE SPRINT DOIT
  REMPLACER `_renewal`** par la vraie SeedBank-espèce génétique — c'est le pont
  principal du sprint. Ne pas doubler le système.
- `maturity_years` existe sur les arbres (âge de 1re fructification) → condition
  de production de graines. `longevity_years` et `fungal_susceptibility` aussi
  sur `PlantBase` (cf. sprint sénescence).
- `SeedBank` a gagné `tick_late_succession_enrichment` (amorçage propagules
  vivaces ∝ maturité du sol) en plus de `tick_plant_production` (graines par
  archétype au stade ≥2) et `tick_disturbance_enrichment`. La couche
  espèce+génétique s'ajoute **par-dessus** ces trois.
- Rondelles **`pollinisateur` ET `auxiliaire`** existent (posées par les
  mellifères + achillée/phacélie). La pollinisation par insectes doit lire ces
  rondelles — le levier « favoriser les auxiliaires = meilleures graines » est
  déjà alimenté côté terrain.
- **Positions continues** `x_cm/y_cm` en place → calculer `pollination_radius`
  en distance euclidienne réelle (cohérent avec la lumière), pas en plots.
- Espèces ajoutées depuis la conception : achillée (vivace), phacélie
  (annuelle) + catalogue d'arbres (`perennials.py`). Tous candidats repro.

**Inchangé / confirmé :**
- `genetic_factor` toujours neutre 1.0 dans `height_at`/`PerennialWoody` → ce
  sprint le branche pour de bon.
- Le modèle d'archétypes (pioneer/…/competitor) pilote toujours `niche_index` et
  la succession : la génétique par espèce s'ajoute **sans le casser**.

**Workflow actif :** bypassPermissions + carte blanche (implémenter sans
valider chaque étape une fois la conception figée) ; aucun code n'est jeté.

---

## Avant de commencer

1. **`CLAUDE.md`** chargé. Relire D17 et D22.
2. **`journal.md`** — entrée `2026-05-29 — Sprint conception éclairement &
   reproduction`, section « Génétique & reproduction (D17 + D22) ».
3. **Code à lire** :
   - `data/code/fields.py` — `SeedBank` actuelle (densités d'archétypes par
     plot, **sans espèces ni génétique**). C'est ce modèle qu'on étend.
   - `data/code/engine.py` — `tick_seed_bank`, succession (`niche_index`,
     `germination_candidates`), reproduction.
   - `data/code/models.py` — `PlantInstance`, familles/espèces, position
     continue (issue du Sprint éclairement).

---

## Décisions actées (rappel)

### Deux banques distinctes (D17)

| | **SeedBank-sol** | **SeedBank-joueur** |
|---|---|---|
| Nature | champ écologique latent | inventaire discret |
| Indexé par | espèce × plot | espèce, en lots |
| Génétique | **vectorielle** (moyenne + variance par gène par espèce) | héritée, sélectionnée |
| Au déménagement | reste au terrain | suit l'avatar |
| Rôle | succession spontanée + brassage féral | sélection du joueur |

**Ponts** :
1. Récolte d'une plante mûre → graines dans la **banque-joueur** (génétique
   héritée préservée).
2. Graines non récoltées (chute, mort) → **banque-sol** (génétique conservée
   au pool féral local).
3. Semis depuis la banque-joueur → plante portant la génétique de la graine.
4. Succession spontanée → naît de la banque-sol.

> Conserver la compatibilité avec le modèle d'archétypes existant
> (`pioneer`/`nitrogen_fixer`/`grass`/`competitor`) qui pilote `niche_index`
> et la succession — la génétique par espèce s'ajoute **par-dessus**, sans
> casser la dynamique de niche.

### Gènes vectoriels extensibles (D22)
- `genes = {hauteur: float, …}` — seul `hauteur` est rempli au départ.
  Prévoir l'extension (vigueur, résistance pathogène, tolérance sécheresse…)
  sans refactor.
- Plage normale [0.7, 1.3], gaussienne centrée 1.0 σ=0.1. L'introgression
  peut pousser **hors** de cette plage (vigueur hybride).

### Héritage biparental
- À la production de graines sur une plante mère fécondée :
  - chercher un **père compatible à portée de pollinisation** ;
  - `gène_enfant = moyenne(mère, père) + mutation gaussienne`, par gène ;
  - **pas de partenaire à portée → autofécondation** (mère + mutation,
    consanguinité = diversité faible).
- **Déterministe** : appariement et mutation via le hash `_hash_noise` (seed,
  semaine, position) — aucun RNG live (règle de design #3).

### Pollinisation par espèce
- Champ `pollination_mode` (`wind` / `insect` / `self`) + `pollination_radius`
  (cm) par espèce.
- **Pollinisateurs auxiliaires** présents → augmentent rayon/probabilité de
  croisement. Mécanique permaculture : favoriser les auxiliaires = meilleures
  graines.

### Hybridation par introgression sur espèce fixe
- Croisement autorisé entre espèces **proches** (même genre/famille — définir
  les groupes de compatibilité).
- L'enfant **garde l'espèce de la mère** ; les gènes du père **décalent** ses
  facteurs vectoriels. **Aucune** nouvelle `PlantData` générée.

---

## Sous-objectifs

### 1. `data/code/fields.py` — `SeedBank` par espèce + génétique
- Étendre la banque-sol : par plot, par espèce → densité + distribution
  vectorielle de gènes (moyenne + variance), en plus des archétypes.
- Vieillissement, enrichissement par perturbation, production : conserver.

### 2. `data/code/seeds.py` (ou models.py) — objets graine & banque-joueur
- `Seed` (espèce + vecteur de gènes) ; `PlayerSeedBank` (lots par espèce,
  transportable).
- Sérialisation JSON (cohérent avec le save par profil, cf Z1).

### 3. `data/code/reproduction.py` — héritage biparental
- Appariement déterministe mère↔père à portée (mode + rayon + auxiliaires).
- Calcul du vecteur enfant (moyenne + mutation, introgression inter-espèces).

### 4. Intégration `engine.py`
- Brancher la production de graines (récolte → joueur ; chute → sol).
- Brancher la succession sur la banque-sol génétique.
- `current_height = potential × genetic_factor(réel) × growth_factor`.

### 5. Portage C#
- `core/SeedBankSystem.cs` (stub existant) : deux banques.
- `core/Seed.cs` + `core/Reproduction.cs`.

### 6. Tests
- Sélection émergente : récolter les plus hauts sur N saisons → la moyenne
  `hauteur` de la lignée monte (Python).
- Brassage : présence d'auxiliaires → diversité génétique accrue.
- Parité Python ↔ C# sur 1 saison.

---

## À produire à la fin de la session

- [ ] `fields.py` : banque-sol par espèce + distribution génétique
- [ ] banque-joueur (lots, transportable, JSON)
- [ ] héritage biparental + pollinisation par espèce + introgression
- [ ] intégration `engine.py` (ponts récolte/chute/semis/succession)
- [ ] `genetic_factor` réel branché dans `current_height`
- [ ] portage C# (`SeedBankSystem.cs`, `Seed.cs`, `Reproduction.cs`)
- [ ] tests sélection émergente + brassage + parité
- [ ] `journal.md`, `CLAUDE.md`, memory mis à jour
- [ ] Commit dédié

---

## Critère de fin

Les deux banques coexistent (sol génétique lié au terrain, joueur
transportable), la production de graines applique l'héritage biparental
(pollinisation par espèce modulée par les auxiliaires, autofécondation à
défaut), l'introgression inter-espèces décale les gènes sans créer d'espèce,
la sélection artificielle est démontrée (récolte ciblée → lignée qui dérive),
parité Python ↔ C# vérifiée.

## Zones blanches à trancher en début de session
- Granularité de la distribution génétique en banque-sol (par plot ? par
  tuile ? moyenne+variance ou échantillons ?).
- Groupes de compatibilité d'hybridation (par genre ? par famille ?).
- Coût en Vigueur de la récolte sélective (lien avec D11 Vigueur).
