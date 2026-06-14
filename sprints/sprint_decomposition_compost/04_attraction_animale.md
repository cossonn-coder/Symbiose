# Sous-sprint ④ — Attraction animale : le fruit tombé appelle la faune (frais → `auxiliaire`, pourri → `ravageur` + frac.)

> **Kickoff autosuffisant (démarrage à froid).** Lire d'abord `00_etat.md`
> (§Acquis ①②③) et `data/code/CONCEPTION_DECOMPOSITION_COMPOST.md` (**§4**
> surtout, + §1.2 ligne `fruit`, + §7 ligne ④, + `CONCEPTION_VIE_MACRO.md` §2
> pour le modèle des 4 guildes). ③ a donné aux fruits un **état moteur** qui
> **tombe en litière `fruit`** (`deposer_litiere(r,c,"fruit",masse)` quand un
> fruit non cueilli sur-mûrit). ④ branche la **réponse animale** à cette litière :
> un tas de `fruit` frais nourrit les **auxiliaires** (frugivores, oiseaux) ; un
> tas **avancé/pourri** appelle les **ravageurs** (charognards, mouches) en
> dominant + une petite fraction d'auxiliaires de décomposition. ④ ne crée
> **aucune 5ᵉ guilde** (conception : trop lourd), **aucune structure posable**
> (⑤ : bac/pile), **aucun rendu Godot** (⑥, intégration en pause).

## Ampleur & risque (à lire avant de coder)
Sous-sprint **PETIT à MOYEN**. Le mécanisme neuf est **une ou deux grilles de
signal** dérivées de `eco.litiere` (parcelle `fruit`, lue par `age_sem`) qui
viennent **gonfler la capacité de charge** des guildes `auxiliaire`/`ravageur`.
Tout le reste réutilise l'architecture **data-driven** existante de
`fields/population.py` (les `TrophicSpec`, le `PopulationField.tick` générique) :
- la litière `fruit` + son `age_sem` **existent déjà** (parcelle, fusionnée par
  tissu → **au plus une parcelle `fruit` par plot** → lecture triviale et
  déterministe) ;
- les fonctions de ressource/habitat sont déjà des **grilles `[rows][cols] ∈
  [0,1]` pures** (`_foliage_grid`, `_ravageur_grid`, `_stability_grid`…) — on en
  ajoute/compose une ;
- le tick population est **déjà appelé** (étape 13b, `eco.tick_populations`).

> **Risque #1 = re-figeage golden — mais ④ sera très probablement NEUTRE.**
> Comme ③ (et ②A), le scénario du golden ne produit **aucune litière `fruit`** :
> la seule espèce `fruitier` du smoke test est l'**AppleTree** (`maturity_years
> = 5 > fenêtre 2 ans`) → **jamais de nouaison → jamais de chute → jamais de
> parcelle `fruit`**. Donc le **terme de signal fruit vaut exactement 0 partout**
> → `capacite` inchangée → champs de population **bit-identiques à ③**. **À
> VÉRIFIER, pas à supposer** : si le hash dérive, c'est un **bug** (le terme
> fruit n'est pas exactement nul à zéro fruit, ou il touche une grille hors
> `fruit`). Cibles à retrouver **inchangées** :
> `smoke 908f591b…`, `population 435e6f72…` (h1==h2 et identiques à ③).
>
> **Risque #2 = déterminisme.** Le signal est **strictement** fonction de
> (masse, `age_sem`) de la parcelle `fruit` du plot. **Aucun `random`**, aucune
> dépendance à un ordre non trié (la fusion par tissu garantit une parcelle
> `fruit` unique/plot → pas d'ambiguïté d'ordre). Le tick population **lit la
> litière au début de l'étape 13b**, donc **l'état d'avant** la chute de la
> semaine (`_tick_fruits` = 15c) et **après** le vieillissement
> (`tick_decomposition`, avant 13b) → décalage d'une semaine **assumé** (cohérent
> avec le décalage proie↔prédateur du modèle). Le noter, ne pas le « corriger ».

---

## Acquis ①②③ réutilisés
- `eco.litiere[r][c]` : `list[Parcelle{tissu, masse, age_sem}]`, fusion par tissu
  → **au plus une parcelle `fruit`/plot**. `age_sem` est **incrémenté chaque
  semaine** par `tick_decomposition` (acquis ①). Une parcelle `fruit` apparaît
  uniquement par `_tick_fruits` (③, chute des sur-mûrs) → `fruit` frais = `age_sem`
  bas, `fruit` pourri = `age_sem` élevé. **C'est le seul vecteur du signal §4.**
- `fields/population.py` (D31) — architecture **data-driven** intacte :
  - `TrophicSpec{name, salt, resource_fn, habitat_fn, predators, *_w, inertia}` ;
  - `PopulationField.tick` : `capacite = clamp(resource_w·res + habitat_w·hab)` ;
    `cible = capacite · survie` ; relaxation avec inertie. **On gonfle la
    `capacite`** des bonnes guildes via la ressource/habitat — **pas de nouvelle
    machinerie dans le tick générique** si possible.
  - 4 instances (`build_population_specs`) : `ravageur` (res=`_foliage_grid`,
    hab=`_monoculture_grid`, prédateur=`auxiliaire`) ; `auxiliaire`
    (res=`_ravageur_grid`, hab=`_stability_grid`) ; `pollinisateur` ; `vers`.
  - **Ordre de tick** : `ravageur` puis `auxiliaire` (l'auxiliaire lit le
    ravageur fraîchement mis à jour) — **conservé**.
- `tick_populations(tile, plants)` (`ecofields.py:391`) appelé étape **13b**
  (`engine.py:880`). Les grilles de ressource reçoivent `(eco, tile, plants)` →
  **`eco` donne accès à `eco.litiere`** : tout le matériau du signal est là.
- Référence habitat persistant : `favoriser_auxiliaire` (`actions.py:540`) pose
  une rondelle `auxiliaire` lue par `_stability_grid` → **patron** du « terme-
  source d'habitat » pour la pile à bois (§4.1, mais voir décision #0).

---

## Le modèle (conception §4, FIGÉE)

Une parcelle `fruit` émet un **signal selon son `age_sem`** (succession sur le
fruit) couplé aux guildes existantes (**aucune 5ᵉ guilde**) :

- **Fruit frais tombé** (`age_sem` bas) → gonfle **`auxiliaire`** (frugivores,
  oiseaux : le verger nourrit la faune utile).
- **Fruit avancé / pourri** (`age_sem` élevé) → gonfle **`ravageur`** (charognards,
  mouches) **en dominant** (pénalité de fermentation → incite à cueillir, philo
  #6) **+ une petite fraction `auxiliaire`** (auxiliaires de décomposition :
  cloportes, coléoptères — la décompo n'est jamais pur déchet). **Pas de sous-
  guilde dédiée** (tranché Nico) : juste cette fraction en plus du `ravageur`.

> **Lien pédagogique (philo #6)** : laisser pourrir → nuisibles ; cueillir &
> composter → faune utile. La conséquence enseigne, sans sermon. ④ pose la
> moitié « laisser pourrir → nuisibles » ; ⑤ posera « composter → sol vivant ».

### Comment se compose le signal (à partir de la parcelle `fruit`)
Par plot, lire la parcelle `fruit` (s'il y en a une) → `(masse, age_sem)`. En
dériver **deux poids ∈ [0,1]** via `age_sem` :
- `frais(age)` : **décroît** avec l'âge (1 quand fraîchement tombé → 0 quand vieux),
- `pourri(age)` : **croît** avec l'âge (0 frais → 1 quand bien avancé),

modulés par `masse` (un gros tas appelle plus, borné/normalisé conservativement,
cf. décision #3). Puis :
- **auxiliaire** reçoit `frais·signal + pourri·signal·FRAC_AUX_POURRI`,
- **ravageur** reçoit `pourri·signal`.

> Forme **additive bornée** à plugger dans la `capacite` (clamp [0,1] déjà fait
> par le tick). À zéro fruit → les deux termes = **0** → `capacite` inchangée →
> **golden neutre** (invariant à garder absolument, cf. risque #1).

---

## Décisions à figer en tout début de ④ (≤ 3, puis carte blanche)
> Conception FIGÉE ; 3 points d'implémentation à trancher AVANT de coder (les
> écrire dans `00_etat.md` §Acquis ④).

0. **(frontière, trancher d'abord) Pile à bois → habitat `auxiliaire` (§4.1) :
   DIFFÉRER à ⑤.** La pile à bois est une **structure posable** qui **n'existe
   pas avant ⑤**. ④ n'a rien à quoi accrocher l'habitat. → ④ traite **uniquement
   le couplage fruit→guildes** ; le « pile à bois → habitat » se fera en ⑤ quand
   la structure sera posable (réutilisera le patron `_stability_grid`/rondelle).
   *(Recommandé. À confirmer : si Nico veut un hook générique d'habitat dès ④,
   l'ajouter, mais sans structure à câbler il resterait mort.)*

1. **Où vit le signal & comment le brancher sans casser le tick générique.**
   Recommandé : **deux nouvelles grilles pures** dans `population.py`
   (`_fresh_fruit_grid`, `_rotten_fruit_grid`, lisant `eco.litiere`) **composées**
   dans la ressource des guildes concernées — soit en **enveloppant** les
   `resource_fn` existantes (`auxiliaire.resource_fn = base + frac·pourri +
   frais` ; `ravageur.resource_fn = _foliage_grid + pourri`), soit en ajoutant un
   **3ᵉ terme additif optionnel** `signal_fn` au `TrophicSpec` + au `tick`
   (machinerie minime, plus lisible que des closures composées). **Trancher** et
   noter. Contrainte : **0 fruit ⇒ terme 0 ⇒ capacite identique** (golden neutre).

2. **Loi `age_sem` → (frais, pourri).** Seuils/ rampes (placeholders, calibrage
   post-test) : p.ex. `frais = clamp(1 − age/FRUIT_FRAIS_SEM)`,
   `pourri = clamp((age − FRUIT_FRAIS_SEM)/FRUIT_POURRI_SEM)`, avec
   `FRUIT_FRAIS_SEM ≈ 2-3`, transition vers `pourri` ensuite. Knobs dans
   `population.py` (à côté des `*_REF`) ou `ecofields.py` (à côté des knobs ③).
   **Conservatif** : la magnitude doit rester petite (la dérive golden FUTURE,
   quand un fruitier précoce existera, doit être lisible, pas explosive).

3. **Normalisation masse→signal & fraction auxiliaire du pourri.**
   `signal = min(1, masse / FRUIT_SIGNAL_REF)` (réutiliser l'échelle `FRUIT_MASSE
   = 0.15` de ③ : un fruit ≈ 0.15 → `FRUIT_SIGNAL_REF` de l'ordre de 0.3-0.6 pour
   qu'un petit tas soit déjà visible mais pas saturant). `FRAC_AUX_POURRI ≈
   0.2-0.3` (la « petite fraction » §4). Knobs, calibrage post-test.

---

## Plan d'implémentation (un fichier à la fois ; ordre = dépendances)

1. **`fields/population.py`** — knobs (`FRUIT_FRAIS_SEM`, `FRUIT_POURRI_SEM`,
   `FRUIT_SIGNAL_REF`, `FRAC_AUX_POURRI`) + helpers purs `_fruit_litter(eco,r,c)
   → (masse, age_sem)` (lit la parcelle `fruit` du plot, `(0,0)` si absente),
   `_fresh_fruit_grid` / `_rotten_fruit_grid` (grilles `[0,1]`). Brancher selon
   décision #1 (envelopper les `resource_fn` de `auxiliaire`/`ravageur`, **ou**
   ajouter `signal_fn` au `TrophicSpec` + une ligne dans `PopulationField.tick`).
   → *verify :* `python3 -c "import fields.population"` OK ; à **zéro fruit** les
   grilles sont nulles (test rapide) → golden **doit** rester neutre.
   > **Couches** (CLAUDE.md `plants ← fields ← sim ← engine`) : tout reste dans
   > `fields` (population lit `eco.litiere`, déjà dans `fields/ecofields`). **Aucun
   > import de `sim`/`engine`/`tools`.** Pas de cycle.

2. **`fields/ecofields.py`** *(si besoin)* — un seul point de contact possible :
   exposer un accès propre à la parcelle `fruit` d'un plot si on ne veut pas que
   `population.py` itère `eco.litiere[r][c]` (sinon, l'itération inline ≤ 3
   lignes suffit). **Probablement aucune modif** ici. Ne PAS toucher
   `tick_populations` (l'ordre 13b est correct).

3. **`tools/sim_server.py`** — **probablement aucun bump nécessaire** : les champs
   de population sont déjà exposés au snapshot (vie macro D31, sprites
   échantillonnés). Vérifier que les densités `auxiliaire`/`ravageur` remontent
   bien (elles le font déjà). Bump cosmétique **0.3.4 → 0.3.5** seulement si on
   ajoute un champ au protocole (a priori non). → *verify :* poignée de main OK,
   un snapshot après chute de fruit montre l'`auxiliaire`/`ravageur` bouger près
   du plot.

4. **Test dédié `tests/test_attraction.py`** (modèle : `test_fruits.py`,
   `test_population.py`) — **forcer** des parcelles `fruit` via
   `eco.deposer_litiere(r,c,"fruit",m)` à `age_sem` contrôlé (incrémenter
   `age_sem` à la main ou ticker), ticker les populations, asserter :
   - fruit **frais** (age bas) → `auxiliaire[r][c]` **monte** vs témoin sans fruit ;
   - fruit **avancé** (age élevé) → `ravageur[r][c]` **monte** (dominant) **et**
     `auxiliaire[r][c]` monte **un peu** (frac.) ;
   - **monotonie** : ravageur(pourri) > ravageur(frais) ;
   - **déterminisme** : deux runs → mêmes densités (h1==h2) ;
   - **neutralité** : zéro parcelle `fruit` → densités **identiques** au tick sans
     le code ④ (invariant golden, peut se vérifier en comparant à un eco témoin).
   → *verify :* `python3 -m tests.test_attraction` vert.

5. **Re-figeage golden + suites + doc** — voir §Golden. **Attendu : NEUTRE.**

---

## §Golden — protocole (attendu NEUTRE, à PROUVER)
Comme ②/③ : `git stash` du diff, lancer l'ancien et le nouveau golden + le test
population, **comparer les hash**.
- **Attendu** : `smoke 908f591b…` et `population 435e6f72…` **inchangés**
  (bit-identiques à ③) — le golden ne crée aucune litière `fruit`.
- **Si dérive** → **NE PAS figer aveuglément** : c'est un **bug** (terme fruit
  non nul à zéro fruit, ou grille touchée à tort). Diagnostiquer, corriger,
  re-vérifier la neutralité. Ne re-figer que si une cause **légitime et
  expliquée** apparaît (peu probable en ④).
- Noter le résultat (neutre confirmé, ou dérive + cause) dans `00_etat.md`.

## Définition de terminé (DoD)
- [ ] Signal fruit branché : `frais → auxiliaire`, `pourri → ravageur` (dominant)
      `+ FRAC_AUX_POURRI → auxiliaire`. **Aucune 5ᵉ guilde.**
- [ ] **Déterministe** (h1==h2 sur le test dédié) ; **zéro fruit ⇒ capacite
      inchangée** (invariant prouvé par le test de neutralité).
- [ ] `tests/test_attraction.py` vert (frais↑aux, pourri↑rav+un peu d'aux,
      monotonie, déterminisme, neutralité).
- [ ] **Golden NEUTRE confirmé** (smoke `908f591b…`, population `435e6f72…`
      inchangés, h1==h2) — OU dérive corrigée jusqu'à neutralité.
- [ ] **11 suites ciblées vertes** (génétique, croissance, maîtrise, vigueur,
      population, ombre, phototropisme, sénescence, signes, auxiliaires, fruits…).
- [ ] `main.py 5` tourne `exit=0`, scores sains.
- [ ] Pile à bois → habitat **explicitement différé à ⑤** (noté), OU implémenté
      si Nico le demande (décision #0).
- [ ] `00_etat.md` §Acquis ④ + `journal.md` à jour ; commit `feat(décompo·
      compost) : sous-sprint ④ — attraction animale (fruit→guildes)`.

## Pièges (vécus aux sous-sprints précédents)
1. **Croire la dérive obligatoire.** ④ est **neutre** sur le golden actuel
   (aucun fruit). Si ça dérive, c'est un bug, pas « la dérive annoncée ».
2. **Déterminisme.** Aucun `random`. La parcelle `fruit` est **unique/plot**
   (fusion par tissu) → pas d'ordre à trier, mais **ne jamais** dépendre de
   l'ordre d'itération d'un `set`/`dict`.
3. **Frontière de couches.** `population.py` reste dans `fields` — n'importe que
   `fields.grids`/`fields.noise` (+ lecture `eco`). **Pas** de `sim`/`tools`.
4. **Casser le tick générique.** Si on ajoute `signal_fn` au `TrophicSpec`, le
   défaut doit être « pas de signal » (None → terme 0) pour que pollinisateur/
   vers restent **bit-identiques**. Ne toucher que `auxiliaire`/`ravageur`.
5. **Magnitude trop forte.** Signal conservatif (knobs #2/#3) : un tas de fruits
   ne doit pas saturer la guilde à 1.0 instantanément (boom irréaliste).
6. **Inertie & décalage.** Le signal monte **progressivement** (inertie 0.85 du
   champ) — c'est voulu (la faune arrive « semaines plus tard », comme
   `favoriser_auxiliaire`). Le test doit ticker **plusieurs semaines** pour voir
   l'effet, pas un seul tick.

## Ce que ④ NE fait PAS (frontières)
- **Pas de structures posables** (bac à compost / pile à bois) ni gestes
  `composter`/`empiler`/`retourner`/`epandre` = **⑤**. La pile à bois → habitat
  (§4.1) en dépend → **différé à ⑤** (décision #0).
- **Pas de nouvelle guilde** : on réutilise `auxiliaire`/`ravageur` (tranché).
- **Pas de rétroaction fruit→santé de la plante** (philo #2 : le fruit modifie un
  **champ de population**, la plante n'est jamais touchée directement).
- **Pas de rendu Godot** (sprites de faune sur les fruits) = **⑥** (pause).
- **Pas de modif de `_tick_fruits` (③)** ni de la litière (①) : ④ **lit** la
  parcelle `fruit`, ne la **produit** ni ne la **consomme** (la décompo ① la
  vide déjà).
