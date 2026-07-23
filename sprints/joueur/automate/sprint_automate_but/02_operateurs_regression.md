# Tronçon ② — Opérateurs créatifs + moteur de régression

> Sprint **Automate dirigé par le but** (D87). Conception :
> `docs/joueur/automate/conception_automate_but.md` (§2, §4). Lis `CLAUDE.md` +
> `00_etat.md` + ce fichier. Le tronçon ① (log) est fait — ses constructeurs
> `entree_plan`/`entree_diagnostic` sont disponibles dans `trace.py`.

## Objectif

Doter l'automate d'un **planificateur moyens-fins** : à partir d'un objectif actif
`Objectif(geste, quantite, cible)`, produire (par chaînage arrière borné sur un
**petit catalogue d'opérateurs**) le **prochain geste créatif faisable** pour faire
ADVENIR la cible. **Ce tronçon PRODUIT les plans créatifs et les trace ; il ne les
BRANCHE PAS encore dans la boucle** (c'est ③). Il est testable en isolation.

## Rappel d'architecture (déjà en place — LIS le code)

- `objectifs.py` : `Objectif` (frozen `geste/quantite/cible/id`), `objectifs_actifs`,
  `incrementer`, `est_atteignable`, `classe_cible`, `progression`. La cible est une
  **clé d'espèce** du catalogue.
- `proposition.py` : renvoie un `Plan(verbe, cible, cible_obj, nature, facteur,
  priorite)` ou une `Impasse`. **Réutilise ce dataclass `Plan`** pour les gestes
  créatifs (mêmes champs ; `facteur` pourra valoir p.ex. `"advenir"`).
- `planter` (`sim/actions/gestes.py:100`) : source = `PlayerSeedBank` (`take`),
  dépose un `GrainEnAttente`, `cultive=True`. Signature `planter(gs, player, tile,
  eco, species, r, c, x_cm=None, y_cm=None)`.
- `acheter_au_magazine(gs, player, espece)` (`sim/magazine.py`) : écrit Vigueur +
  banque ; `magazine_offres(gs, player)` liste les espèces offertes (palier 3
  famille). `SEUIL_MAGAZINE=3`, `COUT_MAGAZINE=120`.
- `favoriser_auxiliaire` (`sim/actions/`) : pose une rondelle `auxiliaire` sur la
  zone. Vérifie sa signature exacte au `grep`.
- `plant.plant_class.fruitier` (bool, `plants/base/familles.py:79`) : espèce à
  fruit vs végétatif. `plant.fruits` (liste, `plants/base/instance.py:135`) : fruits
  noués. `plant.floraison` (float). `maturite(plant)` (utilisé par `recolter`).
- `tile.plants_at(row, col, layer="both")` + `tile.grains_en_attente` (dict `(r,c)`).

## Fichiers à créer

- `tools/jardinier_auto/operateurs.py` — **NEUF** : le catalogue des 3 opérateurs.
- `tools/jardinier_auto/planification.py` — **NEUF** : régression arrière + état
  persistant `automate_plans`.
- `tests/test_automate_planif.py` — **NEUF**.
- `tools/jardinier_auto/__init__.py` — ré-exports si besoin.

## Modèle — `operateurs.py`

Trois opérateurs, chacun = fonctions PURES sondant l'état vivant (aucune écriture) :

1. **`acheter_magazine(sp)`** — `pre(gs, player)` : `sp in magazine_offres(gs,
   player)` ∧ Vigueur courante ≥ `COUT_MAGAZINE`. `post` : graine `sp` en banque.
2. **`planter(sp)`** — `pre(gs)` : `PlayerSeedBank.count(sp) > 0` ∧ un **plot libre**
   déterministe existe. `post` : cultivée de `sp` (à terme). Fournit le **placement**
   (§2.3) : `plot_libre(engine) -> (tile, r, c)` = premier `(tile, r, c)` en
   balayant `engine.tiles` (ordre liste) puis `(r,c)` croissant, où libre =
   `tile.plants_at(r,c)` sans vivant ET `(r,c) not in tile.grains_en_attente`.
3. **`favoriser_auxiliaire(sp)`** — `pre` : ∃ cultivée `fruitier` de `sp` dont la
   **zone n'a pas** de rondelle `auxiliaire` (vérifie l'état des `stakes`/rondelles
   de la tuile — voir `compost.py` §4.1 qui pose déjà une rondelle `auxiliaire`).
   `post` : habitat posé (one-shot).

**« Récoltable » typé organe** (helper partagé, §2.1) :
`but_satisfait(plant, sp)` = si `fruitier` → un `plant.fruits` **mûr** présent ;
sinon → `maturite(plant) >= MATURITE_MUR` (importe le seuil de `diagnostic.py`).

## Modèle — `planification.py`

État persistant opt-in sous `game_state["automate_plans"]` :
`{obj_id: {tentatives_semaille:int, essai_precedent:(saison,plot)|None,
en_veille:bool, chainon:str|None}}` (créé à la volée ; l'ordre n'importe pas, on
itère les objectifs triés par id).

`avancer_plans(engine, actifs, profil) -> (plans_creatifs, veilles)` :
pour chaque objectif actif (déjà trié par id), dont `geste == "recolter"` :
- compter les cultivées vivantes de `cible` → `n_vivantes` ; `nb_cible = min(quantite,
  3)` (surchargeable — voir ⑤ pour le param banc ; ici lire un défaut).
- **si** une cultivée `fruitier` sans habitat auxiliaire existe → émettre un
  `Plan(favoriser_auxiliaire)` (priorité créative basse, cf. ③). Trace `plan`
  `{sous_but:"favoriser_auxiliaire", raison:"cultivee_fruitiere_sans_habitat"}`.
- **si** `progression < quantite` ET `n_vivantes < nb_cible` → chaînage arrière pour
  OBTENIR une nouvelle cultivée :
  - `planter.pre` vraie → `Plan(planter)` sur le plot choisi. Trace `plan`
    `{sous_but:"semer", raison:"n_vivantes<nb_cible & graine_en_banque"}`.
  - sinon `acheter_magazine.pre` vraie → `Plan(acheter_magazine)`. Trace `plan`
    `{sous_but:"acheter", raison:"pas_de_graine & offre_magazine"}`.
  - sinon → **veille** `chainon_manquant` (retour dans `veilles`, détail
    `{chainon:"graine", source:"aucune"}`). NE PAS émettre de geste.
- sinon (assez de cultivées, ou progression atteinte) → aucun geste créatif.

Récursion **bornée** `PROFONDEUR_MAX = 4` (garde-fou ; la chaîne réelle est ≤ 3).
**Aucune** simulation temporelle en avant. **Ordre total stable** : objectifs triés
par id ; placement déterministe ; cible florale = plus petit `(tile_id, y_cm, x_cm)`.

Le geste `Plan` créatif porte une **priorité MODÉRÉE basse** (constante nommée,
p.ex. `PRIO_CREATIF = 5`) — bien SOUS les facteurs de survie (10-20 dans `regles.py`)
→ préemption survie (③). `recolter` **reste réactif**, on ne l'émet jamais ici.

## Golden

**INTACT**. Ce tronçon n'est pas branché dans `jouer_tick` → aucun effet sur un run.
Le golden tourne sans joueur/objectif → no-op de toute façon. Vérifie
`python3 -m tests.test_golden`.

## Tests

`tests/test_automate_planif.py` (déterministes, opt-in) :
- monter un monde AVEC un joueur, une `PlayerSeedBank` contenant une graine tomate,
  un objectif `recolter tomate` → `avancer_plans` émet un `Plan(planter)` au bon
  plot ; sonde le déterminisme (2 runs → mêmes plans).
- banque vide + offre magazine (palier 3 simulé) → `Plan(acheter_magazine)`.
- banque vide + pas d'offre → **veille** `chainon_manquant`, aucun geste.
- espèce `fruitier` → sous-chaîne `favoriser_auxiliaire` proposée ; espèce
  `fruitier=False` → PAS de sous-chaîne pollinisation.
- `but_satisfait` : distingue fruit mûr vs maturité végétative.

## Ne PAS faire

- NE PAS câbler dans `boucle.jouer_tick` (③).
- NE PAS écrire dans le moteur ni exécuter les gestes (fonctions de DÉCISION).
- NE PAS ajouter d'attribut aux espèces (on LIT `fruitier`).
- NE PAS inclure la voie « récolter des semences d'une plante-mère » (écartée, #2).
- NE PAS créer de geste nouveau.

## Fin de tronçon

Golden intact + tests verts → `00_etat.md` (§REPRISE : ② fait, `avancer_plans` prêt
à brancher) + commit (`feat(automate ②) : opérateurs créatifs + régression arrière`).
