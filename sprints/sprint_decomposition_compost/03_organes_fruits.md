# Sous-sprint ③ — Organes-fruits traçables : maturité par fruit, `manger` ciblé, chute des non-cueillis *(absorbe D19)*

> **Kickoff autosuffisant (démarrage à froid).** Lire d'abord `00_etat.md`
> (§Acquis ① et ②) et `data/code/CONCEPTION_DECOMPOSITION_COMPOST.md` (**§3**
> surtout, + §2.4 chute, + §7 ligne ③). ① a posé l'infrastructure parcelles +
> `deposer_litiere`. ② a branché les **vrais dépôts** du vivant et du mort
> (`tailler`→bois, squelette persistant, abscission, écraser-squelette). ③
> donne aux **fruits un état réel** sur la plante (ils cessent d'être un proxy
> de rendu saisonnier) : ils mûrissent, se mangent **un par un**, et tombent
> s'ils ne sont pas cueillis. ③ ne crée **aucune attraction animale** (④ :
> fruit→`auxiliaire`/`ravageur`), **aucune structure posable** (⑤ : bac/pile),
> **aucun rendu Godot** (⑥, intégration en pause).

## Ampleur & risque (à lire avant de coder)
Sous-sprint **MOYEN**. Le mécanisme neuf est **un état `fruits` sur la plante +
un pas d'engine** qui le fait naître/mûrir/tomber. Tout le reste réutilise des
seams existants :
- naissance/sites = `_organ_sites()` + `organ_site` (profil d'espèce, déjà lus
  par le rendu) ;
- saison/floraison/récolte = helpers `engine.py` (`saison_de`,
  `est_phase_floraison`, `PHASES_ACTIVES`) — **déterministes, aucun RNG** ;
- chute → litière = `deposer_litiere(r, c, "fruit", masse)` (acquis ①) ;
- `manger` ciblé = même logique de **désignation d'un sous-élément** que
  `tailler` au segment (tranche 5) ;
- vigueur/maturité = `sim/vigueur_plante.py` (`maturite`, `vigueur_plante`).

> **Risque #1 = le re-figeage golden.** Aujourd'hui les fruits sont un **pur
> proxy de rendu** (`REPRO_BY_SEASON`, `tools/render_structure.py`) → ils
> **n'existent pas dans le moteur** et ne pèsent pas sur le hash. Dès que les
> fruits deviennent un état moteur **qui tombe en litière `fruit`**, ils
> alimentent la cascade fertilité → **le golden dérive** (le pommier de la
> tuile 0 fructifie dans la fenêtre 2 ans, et sans geste joueur le smoke test
> **ne cueille jamais** → tous les fruits sur-mûrissent et tombent). Cette
> dérive est **localisée et déterministe** : dépôts `fruit` aux semaines de
> sur-maturité du pommier. À caractériser et re-figer comme en ② (h1==h2,
> diff de log expliqué).
>
> **Risque #2 = le déterminisme.** Apparition et maturation **strictement**
> fonction de (saison, sites d'organes dérivés des segments, âge). **Aucun
> `random`**, aucune dépendance à l'ordre d'itération non trié. Les sites
> viennent de `_organ_sites()` (déjà déterministe, sous-échantillonné régulier).

---

## Acquis ①/② réutilisés
- `eco.deposer_litiere(r, c, tissu, masse)` — **unique** point de dépôt, fusion
  par tissu. Le tissu `"fruit"` (table `TISSU`, `fields/ecofields.py`) existe
  déjà mais **n'est alimenté par personne** avant ③.
- État post-mortem sur `PlantInstance` (`morte`, `stade_mort`, `bois_restant`,
  `semaines_mort`) ajouté en ② : **modèle à copier** pour ajouter `fruits`.
- Pas d'engine ② `_tick_skeletons` / `_abscission` : **modèle de pas weekly à
  copier** pour `_tick_fruits` (placement, garde `is_alive`, ordre).
- Helpers saison `engine.py` : `saison_de(week)`, `est_debut_saison`,
  `est_fin_saison`, `est_phase_floraison(week, saison)`, `est_phase_recolte`,
  `PHASES_ACTIVES = {"printemps","ete","automne"}`, `SAISONS` (ranges).
- `_organ_sites(plant, organ_site)` (`tools/render_structure.py:386`) → liste de
  points 3D (bouts d'apex `terminal`, ou rameaux latéraux `lateral`), plafonnée
  `MAX_FRUITS=10`, déterministe. **Source des sites** (à réutiliser ou recopier
  côté `sim/` pour ne pas faire dépendre `sim` de `tools` — cf. piège #3).

## Espèces concernées (état actuel)
- **Tomato** : `organ_site = "terminal"` (`plants/species.py:254`),
  fructifie été/automne (`REPRO_BY_SEASON`). *Mais* la tomate **meurt à w2-3**
  dans les tests (froid de démarrage + mildiou familial) → **n'exerce pas** la
  fructification dans le golden (cf. mémoire `tomate_mort_precoce`).
- **AppleTree** : `organ_site = "lateral"` (`plants/perennials.py:172`),
  fleur (printemps) → fruit (été/automne). **C'est le pommier de la tuile 0 du
  golden** → **principal porteur de la dérive ③**.
- Les autres espèces n'ont pas de profil fruitier explicite (`REPRO_BY_SEASON`
  ne liste que Tomato/AppleTree). ③ **conserve ce périmètre** : seules les
  espèces avec un profil reproducteur fruitier portent des `fruits`. Critère
  d'éligibilité à figer en début de ③ (cf. §3.0).

---

## Le modèle (conception §3, FIGÉE)

### Structure
```
fruit = { segment_id: int, maturite: float (0→1, puis >1 = sur-mûr), masse: float }
```
- Liste `fruits: list` portée par `PlantInstance` (comme les champs post-mortem
  de ②). `segment_id` = identité d'un apex/rameau porteur (un site).
- **Apparaît** aux sites `_organ_sites()` en **saison de fructification**,
  **mûrit** chaque semaine (`maturite += d_mat`), puis **sur-mûrit** (>1).
- **Exposé au snapshot** → la vue affichera la maturité (couleur/taille, §6,
  rendu plus tard). Remplace/complète le hint `organ` du protocole 0.2.2.

### `manger` ciblé (§3.2) — c'est exactement D19
`sim/actions.py:manger` cesse de lire la maturité **globale** de la plante :
- **cible UN fruit précis** (désigné à la souris côté Godot, comme `tailler` au
  segment — ici on passe un identifiant de fruit au moteur) ;
- **gain Vigueur ∝ `maturite` DU FRUIT** (vert = peu, mûr = beaucoup, blet =
  décline) ;
- **le fruit DISPARAÎT** de `plant.fruits` (déplétion réelle = D19).

### Chute des non-cueillis (§2.4 + §3.3)
Un fruit dont `maturite` dépasse 1 (seuil de sur-maturité) **tombe** :
`deposer_litiere(r, c, "fruit", fruit.masse)` puis retrait de la liste. **La
cueillette est récompensée, la fermentation pénalisée** (philo : « laisser tout
au sol » s'use). La fermentation animale (`fruit`→`ravageur`) est **④, pas ③**.

---

## Décisions à figer en tout début de ③ (≤ 3, puis carte blanche)
> Conception FIGÉE mais 3 paramètres d'implémentation à trancher AVANT de coder
> (les écrire dans `00_etat.md` §Acquis ③) :

1. **Où vit `fruits`** : champ `list` sur `PlantInstance` (recommandé, miroir
   des champs post-mortem ② — propre, sérialisable, indépendant du rendu) plutôt
   que `Segment.organs` (régénéré à la volée par le rendu, non stocké). Le
   `fruit.segment_id` relie au site.
2. **Combien de fruits par plante & masse unitaire** : plafond = `MAX_FRUITS`
   (10, déjà l'anti-fouillis du rendu) ; masse par fruit = placeholder calibré
   (p.ex. ∝ taille de plante / nb sites), **conservatif** (la dérive golden doit
   rester petite). Pose de la masse → table/constante dans `fields/ecofields.py`
   à côté des knobs ② (`FRAC_BOIS_MORT`, `ABSCISSION_FRAC`…).
3. **Vitesse de maturation & seuil de chute** : `d_mat`/semaine (placeholder,
   p.ex. atteindre 1 en ~la moitié de la saison) et seuil de sur-maturité
   (p.ex. `maturite > MATURITE_CHUTE`, ~1.3) → knobs `ecofields.py`.

---

## Plan d'implémentation (un fichier à la fois ; ordre = dépendances)

1. **`plants/base.py`** — ajouter `fruits: list = field(default_factory=list)`
   à `PlantInstance` (+ éventuellement un petit dataclass `Fruit{segment_id,
   maturite, masse}` à côté de `Segment`). → *verify :* `python3 -c "import
   plants.base"` OK, golden **inchangé** (champ vide, jamais alimenté encore).

2. **`fields/ecofields.py`** — knobs `FRUIT_MASSE`, `FRUIT_DMAT`,
   `MATURITE_CHUTE`, critère d'éligibilité fruitière. → *verify :* import OK,
   golden inchangé.

3. **`sim/` (nouveau pas `_tick_fruits`)** — placé près des pas ②
   (`_tick_skeletons`/`_abscission`), gardé `if not plant.is_alive: continue`,
   itération **triée déterministe**. Logique :
   - en saison de fructification (helpers `engine.py`) et espèce éligible :
     **garantir** un fruit par site `_organ_sites()` qui n'en a pas encore
     (création idempotente, comme `deposer_mort` est idempotent sur `morte`) ;
   - **mûrir** chaque fruit (`maturite += FRUIT_DMAT`) ;
   - **chute** : `maturite > MATURITE_CHUTE` → `deposer_litiere(r,c,"fruit",
     masse)` + retrait.
   - hors saison : laisser tomber/retirer les fruits restants (déterministe).
   → *verify :* golden **dérive** (dépôts `fruit` du pommier) — caractériser.
   > **Frontière de couches** (CLAUDE.md : `plants ← fields ← sim ← engine`) :
   > `_organ_sites` vit dans `tools/render_structure.py`. Ne PAS faire importer
   > `tools` par `sim`. Soit déplacer la pure géométrie de sites dans une couche
   > basse (p.ex. `plants/base.py` ou `sim/growth.py`) et la **réutiliser** des
   > deux côtés, soit recopier la dérivation (≤ 15 lignes) dans `sim/`. Trancher
   > au point 3 et le noter dans `00_etat.md`.

4. **`sim/actions.py:manger`** — signature ciblée `manger(..., *, fruit_id=...)`
   (ou index dans `plant.fruits`). Gain `HARVEST_GAIN_FULL * fruit.maturite *
   (santé/Qi via `vigueur_plante` comme **modulateur**, cohérent §1 actuel) ;
   **retirer le fruit**. Sans fruit ciblé / plante sans fruit → no-op à gain ~0
   (qu'on LISE, comme aujourd'hui le « hors-passe »). **Conserver** l'ancien
   chemin whole-plant ? Non : ③ = D19, `manger` devient per-fruit. Garder le
   code mort en commentaire si utile (mémoire : ne rien jeter). → *verify :*
   `test_planter`/suites existantes vertes ; nouveau mini-test `manger` ciblé.

5. **`tools/sim_server.py`** — bump protocole **0.3.4** :
   - snapshot : exposer par plante la **liste des fruits** `{segment_id,
     maturite, masse}` (remplace/complète le hint `organ` proxy ;
     `organ_site` conservé) ;
   - routage `manger` : lire `target.fruit` (identifiant de fruit) et le passer
     à `A.manger`. Message « gain ∝ maturité **du fruit** cueilli ».
   → *verify :* `python3 -m tools.sim_server` poignée de main + un `manger`
   ciblé renvoie un gain cohérent.

6. **`tools/render_structure.py`** — faire lire les **vrais fruits** du
   snapshot au lieu de `REPRO_BY_SEASON` (couleur/taille ∝ `maturite`).
   **Rendu = vue** : si touché, rester minimal (la vue Godot complète est ⑥).
   *Optionnel ③* ; `REPRO_BY_SEASON` peut rester comme repli pour les SVG outils
   tant que ⑥ n'a pas repris. À trancher selon budget — **ne pas bloquer ③**.

7. **Re-figeage golden + suites + doc** (comme ②) — voir §Golden.

---

## Définition de terminé (DoD)
- [ ] `PlantInstance.fruits` existe ; un dataclass `Fruit` clair si retenu.
- [ ] `_tick_fruits` fait **naître/mûrir/tomber** les fruits, **déterministe**
      (h1==h2 sur 2 runs), gardé `is_alive`, itération triée.
- [ ] Chute → `deposer_litiere(..., "fruit", ...)` (et **rien d'autre** : pas
      d'effet direct sur la plante — philo #2).
- [ ] `manger` cible **un** fruit : gain ∝ sa `maturite`, fruit **retiré**.
- [ ] Snapshot expose la liste des fruits + maturité ; protocole **0.3.4**
      documenté dans l'en-tête `sim_server.py` (historique des versions).
- [ ] **Golden re-figé localisé** : dérive = dépôts `fruit` du pommier (tuile 0),
      caractérisée (semaines, masses) et expliquée ; `population_hash` re-figé
      **seulement si** les vers/guildes lisent le `fruit` (a priori `om_fresh`
      dérivé bouge → re-figer aussi, à vérifier). h1==h2 sur les deux.
- [ ] **11 suites ciblées vertes** (génétique, croissance, maîtrise, vigueur,
      population, ombre, phototropisme, sénescence, signes, auxiliaires…).
- [ ] `main.py` (5 ans suffit — **PAS 30 ans**, c'est trop long, perf D32)
      tourne `exit=0`, scores sains.
- [ ] `00_etat.md` §Acquis ③ + `journal.md` à jour ; commit `feat(décompo·
      compost) : sous-sprint ③ …`.

## Pièges (vécus aux sous-sprints précédents)
1. **Re-figeage non maîtrisé.** Comme ②, faire un `git stash` du diff, lancer
   l'ancien et le nouveau golden, **diff de log**, attribuer chaque ligne qui
   bouge à un événement fruit. Annoncer la dérive avant de figer.
2. **Déterminisme.** Aucun `random`. Trier toute itération sur les sites/plantes
   (l'ordre d'un `set`/`dict` non trié casse le hash).
3. **Frontière de couches.** `sim` ne doit pas importer `tools` (cf. point 3).
4. **Sur-création de fruits.** Idempotence stricte : un site = au plus un fruit ;
   ne pas re-créer un fruit déjà mangé/tombé dans la même saison sans règle
   claire (sinon source infinie de litière → dérive explosive).
5. **Coût de `manger`.** Le geste reste **bon marché** (récolte/cueillette =
   canal vertueux, philo #1). Ne pas y ajouter de coût Vigueur punitif.
6. **`MAX_FRUITS`/masse trop gros** → dérive golden énorme. Calibrer conservatif.

## Ce que ③ NE fait PAS (frontières)
- **Pas d'attraction animale** : `fruit`→`auxiliaire` (frais) / `ravageur`
  (avancé) = **④**. ③ ne touche **pas** `fields/population.py`.
- **Pas de structures** (bac/pile) ni gestes `composter`/`empiler`/`retourner`/
  `epandre` = **⑤**.
- **Pas de rendu Godot** (maturité-fruit à l'écran, sprites) = **⑥** (pause).
- **Pas de fleurs traçables** : §3 ne modélise un état réel que pour les
  **fruits**. La fleur fanée → parcelle `fleur` reste le proxy actuel (et la
  chute fleur détaillée est hors périmètre ③ sauf si triviale).
