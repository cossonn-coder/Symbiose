# CONCEPTION — Voix narratives & dispositifs informationnels (D13 · D14 · D18 · D43 + D12.2)

> **Conception SEULE.** Aucun code touché. Bloc « dette » conçu d'un coup le
> 2026-06-29 (conversation à trancher avec Nico). Source unique pour : magazine de
> botanique (D13), carnet auto (D14), pages secrètes (D18), carnet interprétatif de
> l'acclimatation (D43), **encyclopédie** (4ᵉ voix, sans code de dette jusqu'ici) et
> la **table palier → déblocage D12.2** (débloquée parce que tous ses consommateurs
> sont désormais conçus).
>
> Les trois kickoffs isolés (`sprints/dette_kickoffs/D13_*.md`, `D14_*.md`,
> `D18_*.md`) restent valables ; ce doc les **fond** autour d'un substrat commun et
> ajoute ce qu'aucun kickoff seul ne pouvait voir.

---

## 0. Décisions de cadrage (tranchées par Nico, 2026-06-29)

| # | Question | Décision |
|---|---|---|
| ① | Substrat : ledger partagé ou 4 modules ? | **Ledger partagé** — un journal d'événements unique, les voix sont des lecteurs |
| ② | Inclure l'encyclopédie (4ᵉ voix) ? | **Oui** — interface + couplage conçus ici, corpus complet inclus |
| ③ | Remplir D12.2 maintenant ? | **Oui** — la table palier→déblocage est dans ce doc (§3) |
| A | Encyclopédie : paliers des 3 niveaux | **1 / 2 / 3** (basique / bio / écosystémique) |
| B | Carnet : seuil de bascule interprétative | **Palier 3** du concept de l'entrée (réglage « anticipé » → palier 1) |
| C | Magazine : seuil d'ouverture des sœurs | **Palier 3** d'un membre de la famille |
| Docs | Structure | **Doc unifié** (celui-ci) + table D12.2 intégrée |
| Édit. | Périmètre rédactionnel | **Mécanique + corpus complet** (carnet, encyclopédie 28 fiches, pages) |

Micro-choix par dette **adoptés des kickoffs sans re-débat** : D13 = maîtrise condition /
Vigueur coût, espèces des familles maîtrisées, numéros saisonniers ; D14 = journal
append-only borné, bascule par entrée recalculée à la consultation (révélation
rétroactive), gabarits paramétrés `(type, cause)` ; D18 = corpus pré-écrit fini,
déclenchement déterministe-mais-imprévisible (3 robinets), pur lore zéro effet
mécanique.

---

## 1. Le substrat partagé — le **ledger d'événements**

### 1.1 Principe
Toutes les voix consomment **le même flux** d'événements que le tick émet déjà dans
son `log` (marqueurs `🌱 ⏸ 🌑 ❄ 🌊 🌸 🍎 🍂 🪵 🪦 ✗ 🌰 🐛 🌡 …`). Aujourd'hui
`sim/maitrise_detection.py::_evenements()` parse déjà une **partie** de ce flux
(`avance` / `stagne` / `repro`) pour créditer la maîtrise. On en fait une **fondation
commune**.

### 1.2 Module commun à extraire — `sim/evenements.py`
Extraire `_evenements()` (+ les regex `_POS`, `_RE_TILE`, `_RE_AVANCE`, etc. + le
`_raison_stagnation`) de `maitrise_detection.py` vers un nouveau module **pur**
`sim/evenements.py`. Les deux consommateurs l'importent :

```
sim/evenements.py     ← parse pure du log → flux d'Événements typés
   ↑                ↑
maitrise_detection  journal   (lecteurs ; aucun n'est importé par engine)
```

Couche : `evenements` est au niveau `sim`, au-dessus du tick comme la détection.
`engine` ne l'importe **jamais** (sens de couche préservé, golden intact).

**Élargissement du parseur** : la détection n'avait besoin que de 3 types. Le carnet
en veut plus. On étend `evenements()` pour produire aussi : `floraison`, `nouaison`,
`mort` (cause `sénescence`/`asphyxie`/`gel`/`conflit`), `ravageur`, `abscission`,
`reproduction` (déjà là). Type unifié :

```python
Evenement = namedtuple("Evenement", "kind tile_id pos espece cause")
# kind   ∈ {germination, levée, stagnation, floraison, nouaison, reproduction,
#           mort, ravageur, abscission, …}
# cause  ∈ {sec, noyé, ombre, froid, sénescence, asphyxie, gel, conflit,
#           pollinisé, None}
# espèce = clé catalogue (ou None pour un événement sans plante : aléa météo…)
```

La détection de maîtrise continue de ne lire que les `kind` qui l'intéressent → son
comportement (et le golden joueur `test_maitrise_detection`) est **inchangé** par
l'extraction (refactor pur).

### 1.3 L'état du ledger — `game_state["journal"][player]`
```python
game_state["journal"][player] = {
    "entries": [ {semaine, zone, kind, cause, espece}, … ],   # append-only borné
    "resume":  { (kind, cause): count, … },                   # agrégat des anciens
}
```
- **Append-only borné** (run éternel → pas de journal infini). On garde les
  `JOURNAL_MAX` dernières entrées détaillées ; au-delà, l'entrée la plus ancienne est
  **repliée dans `resume`** (incrément du compteur `(kind, cause)`), exactement comme
  la structure de croissance borne ses segments. `JOURNAL_MAX` = placeholder D12.4
  (proposé : 200).
- **Zone** = `(tile_id, r, c)` (identité stable, déjà utilisée par la détection).
- **Par avatar**, **sérialisé au save** (JSON lisible). Le `resume` survit ; les
  entrées détaillées anciennes non — choix assumé (« je me souviens *qu'il a souvent
  fait sec ici*, plus du détail de chaque semaine »).

### 1.4 Le point d'entrée — au-dessus du tick
```python
# Appelé par le DRIVER après chaque eng.tick_semaine(), à côté de detecter() :
journal.consigner(game_state, player, log, semaine)
```
Symétrique de `maitrise_detection.detecter()` et de `tick_player_vigueur()`. **Jamais
importé par `engine`.** Le golden écolo est **intact par construction** (aucune clé
`journal` n'existe dans une succession spontanée sans joueur).

---

## 2. Les quatre voix (lecteurs read-only du substrat)

> Toutes les voix vivent dans la **maison normande** (hub). Toutes sont
> **event-driven hors tick**, **pures lectures** (sauf l'achat magazine qui `spend` la
> Vigueur et dépose un lot — event-driven aussi), **par avatar**, **golden intact**.

### 2.1 Carnet auto — voix « je », par **événement**
- **Rôle** : enregistrement automatique, indexé, consultable. Descriptif tant que le
  concept n'est pas maîtrisé, **interprétatif** au palier 3 du concept (révélation
  rétroactive : une vieille note « se comprend » quand on maîtrise enfin sa cause).
- **Interface** :
  ```python
  carnet_lire(game_state, player, filtre=None) -> list[EntréeFormatée]
  ```
  Pour chaque entrée du ledger : `concept = CONCEPT_DE[(kind, cause)]` ; `registre =
  "interprétatif" si palier(concept) ≥ SEUIL_CARNET or reglage_anticipé else
  "descriptif"` ; le texte est tiré du **gabarit** `(kind, cause, registre)` (§5) avec
  ses *slots* remplis (espèce, lieu, saison). `filtre` = par concept / par zone / par
  saison (indexation).
- `SEUIL_CARNET = 3` (décision B). Réglage d'aide « interprétatif anticipé »
  (Options, défaut NON) → `SEUIL_CARNET = 1` pour ce joueur.
- **Concept par événement** : table `CONCEPT_DE` (§5.0).
- **D43 (acclimatation)** = un cas de cette règle : l'entrée `acclimatation` (signe
  diégétique déjà émis par le moteur, sprint plasticité ⑤) a pour concept
  **`adaptation`** ; au palier 3 d'`adaptation`, son gabarit interprétatif révèle
  « cette lignée s'est armée — ses descendants naîtront pré-acclimatés ». Aucun
  câblage neuf : c'est une ligne de plus dans `CONCEPT_DE` et un gabarit de plus.

### 2.2 Encyclopédie — voix « naturaliste qui observe », par **espèce**
- **Rôle** : wiki ingame qui se complète aux découvertes. **3 niveaux** révélés selon
  le palier de maîtrise de l'espèce (décision A) :
  - **palier 1** (découverte) → **niveau basique** : nom, silhouette, « observée le… ».
  - **palier 2** (investissement) → **+ description biologique** : cycle, besoins,
    strate, famille.
  - **palier ≥ 3** (maîtrise) → **+ effets écosystémiques** : compagnonnage, rôle dans
    la succession, indications de sol, interactions faune/sol.
- **Pas d'état neuf** : une espèce a une fiche ssi `palier(espèce) ≥ 1` (la maîtrise
  porte déjà la découverte). La détection crédite déjà repro (→ p2) et succès répétés
  (→ p3) : le palier **EST** la progression d'observation décrite par CLAUDE.md.
- **Interface** :
  ```python
  encyclopedie_index(game_state, player) -> list[espèce]          # découvertes
  encyclopedie_lire(game_state, player, espèce) -> Fiche tronquée  # au niveau = min(palier,3)
  ```
- Couplage **magazine** : la fiche de niveau ≥ 2 est ce que le magazine affiche pour
  une espèce sœur offerte (le joueur « lit avant d'acheter »).

### 2.3 Pages secrètes — voix multiples, lore pur
- **Rôle** : savoirs épars, ésotériques, poétiques. **Corpus fini pré-écrit** (§7),
  révélé par fragments. **Zéro effet mécanique** (décision adoptée). Consultation au
  **coffret du grenier**.
- **3 robinets déterministes-mais-imprévisibles** :
  - **hasard** ↔ adossé aux événements rares déjà déterministes (bouture / oiseau /
    vent — quand ils existeront comme marqueurs ; en attendant, ancrage sur
    `_hash_noise(seed, semaine, "page")` au passage de saison).
  - **récompense** ↔ adossé aux **succès de maîtrise marquants** (`credits` renvoyés
    par `detecter()` : franchissement de palier, naturalisation férale §9.4). Une belle
    réalisation → une belle page.
  - **fouille** ↔ action joueur au grenier (`fouiller_grenier`) qui **révèle une page
    déjà “due”** (déterministe, pas de RNG live).
- **État trivial** : `game_state["pages"][player] = set(ids révélés)`. Sérialisé.
- **Interface** :
  ```python
  pages_trouvees(game_state, player) -> set[id]
  reveler_page(game_state, player, robinet, contexte) -> id | None   # driver, hors tick
  ```
- **Ordre de révélation** : les pages ont un `palier_thème` indicatif ; un robinet
  révèle la **prochaine page due** compatible avec le contexte (concept du succès pour
  « récompense », n'importe laquelle pour « hasard »). Corpus épuisable → quand tout
  est trouvé, les robinets sont muets (pas de game-feel de manque : c'est du bonus).

### 2.4 Magazine de botanique — 4ᵉ canal d'acquisition
- **Rôle** : introduire **volontairement** une espèce (vs les 3 canaux subis). **Pas
  une monnaie** : maîtrise = condition d'apparition, Vigueur = coût d'obtention.
- **Offres** : famille `F` ouvre ses **espèces sœurs** (présentes au catalogue maître,
  pas encore dans la `PlayerSeedBank`) dès qu'**un membre de `F` atteint palier 3**
  (décision C). Présentation en **numéros saisonniers** : chaque passage de saison, le
  numéro propose un sous-ensemble des espèces débloquées **de saison** (filtre par
  fenêtre de semis de l'espèce).
- **Interface** :
  ```python
  magazine_offres(game_state, player, saison) -> list[espèce]
  acheter_au_magazine(game_state, player, espèce) -> bool
      # gate (offre valide) → vigueur.spend(COUT_MAGAZINE) → PlayerSeedBank.add(lot)
  ```
- `COUT_MAGAZINE` = placeholder D12.4 (proposé : coût Vigueur élevé, ponctuel — c'est
  un acte rare et décisif).

---

## 3. Table D12.2 — palier → déblocage (le cœur enfin remplissable)

Les **5 paliers** : `0` inconnu · `1` découverte · `2` investissement · `3` maîtrise ·
`4` expertise · `5` transcendant. La table mappe **qualitativement** chaque palier vers
ce qu'il ouvre. (Les **seuils numériques** — `completude_ratio` exact, `K`, `BASE`,
`R`, `COUT_MAGAZINE`, `JOURNAL_MAX` — restent du **calibrage D12.4 post-test**.)

| Palier | Nom | Encyclopédie (espèce) | Carnet (concept) | Magazine (famille) | Terrain D15 (famille) | Pages secrètes |
|---|---|---|---|---|---|---|
| 0 | inconnu | — | — | — | — | — |
| 1 | découverte | **fiche basique** (nom, silhouette) | descriptif | — | — | robinet *hasard* actif |
| 2 | investissement | **+ description biologique** | descriptif | — | — | — |
| 3 | **maîtrise** | **+ effets écosystémiques** | **bascule interprétatif** | **sœurs offertes** (numéro saisonnier) | **tuile thématique apparaît** | robinet *récompense* (palier franchi) |
| 4 | expertise | (nuances — corpus enrichi futur) | interprétatif fin | numéro plus riche | tuile mûre | — |
| 5 | transcendant | (page dédiée + non-action) | interprétatif total | — | écosystème auto-suffisant | **page rare dédiée** au concept |

**Lectures de la table**
- L'**encyclopédie** lit le palier **de l'espèce**.
- Le **carnet** lit le palier **du concept** de chaque entrée (pas de l'espèce) — une
  note sur une tomate ayant soif bascule quand tu maîtrises **l'eau**, pas la tomate.
- Le **magazine** et le **terrain** lisent le palier **d'un membre de la famille**
  (réutilise le spillover famille déjà codé) ; le magazine lit aussi
  `completude_ratio` pour un éventuel gate global (seuil = D12.4).
- Les **pages** lisent les `credits` (franchissements) renvoyés par `detecter()`.

> **Terrain D15** est dans la table par cohérence de coordination (D12.2 *coordonne*
> magazine + carnet + terrain + encyclopédie), mais sa **mécanique** reste à concevoir
> dans D15 (hors de ce bloc). On fixe ici seulement *son palier déclencheur = 3*.

---

## 4. Frontières & golden

- **Tout est hors tick** (driver) → **golden écolo INTACT, jamais re-figé** (comme
  Vigueur et détection de maîtrise). Le refactor `evenements.py` est **pur** (golden
  joueur `test_maitrise_detection` inchangé).
- **Hors périmètre** (renvoyé) : UI Godot (coffret/grenier, kiosque magazine, pages du
  carnet) ; portage C# (D24) ; D15 mécanique d'extension de terrain ; calibrage
  numérique (D12.4) ; les événements rares bouture/oiseau/vent comme *marqueurs* moteur
  (le robinet « hasard » s'ancre provisoirement sur `_hash_noise` au passage de saison
  jusqu'à leur existence).
- **Tests d'implémentation visés** : une entrée consignée par marqueur ; bascule de
  registre quand le palier du concept franchit le seuil ; bornage (journal ne croît pas
  sans fin) ; magazine gated par palier 3 + Vigueur débitée + lot déposé ; page révélée
  sur le bon robinet ; aucune page ne donne d'effet mécanique ; encyclopédie tronquée
  au bon niveau.

---

## 5. Corpus — Carnet (gabarits `(type, cause)` → 2 registres)

> Voix **interne, première personne**. *Slots* : `{e}` = nom de l'espèce, `{l}` =
> lieu (« le coin nord-est », dérivé de la zone), `{s}` = saison. Le **registre**
> s'affiche selon `palier(concept)` au moment de la **consultation** (révélation
> rétroactive). Livrable éditorial — à relire/affiner par Nico, pas du code.

### 5.0 `CONCEPT_DE[(kind, cause)]` — quel concept gate l'entrée
| kind | cause | concept |
|---|---|---|
| germination | — | succession |
| levée (reprise) | = cause levée | (la cause : eau / lumière / météo) |
| stagnation | sec | eau |
| stagnation | noyé | eau |
| stagnation | ombre | lumière |
| stagnation | froid | météo |
| floraison | — | pollinisation |
| nouaison | — | pollinisation |
| reproduction | auto / biparental / introgr. | reproduction |
| mort | sénescence | sénescence |
| mort | asphyxie | eau |
| mort | gel | météo |
| mort | conflit | compétition |
| ravageur | — | ravageurs |
| abscission | — | décomposition |
| acclimatation | — | adaptation |

### 5.1 Gabarits
| (type, cause) | Descriptif (palier < 3) | Interprétatif (palier ≥ 3) |
|---|---|---|
| germination | « Une pousse de {e} a levé {l}. » | « {e} a germé {l} : chaleur et humidité réunies, le sol y était prêt. » |
| stagnation sec | « Le plant de {e} {l} fait grise mine, feuilles molles. » | « Encore la soif {l} — ce sol draine trop vite pour {e}, je le sais maintenant. » |
| stagnation noyé | « {e} {l} a le pied dans l'eau, plus rien ne bouge. » | « Trop d'eau {l} : les racines de {e} étouffent, le sol ne ressuie pas. » |
| stagnation ombre | « {e} {l} s'étire, pâle, tiges filantes. » | « L'ombre {l} bride {e} — elle file chercher la lumière qu'on lui vole. » |
| stagnation froid | « {e} {l} est figée depuis le coup de froid. » | « Le froid {l} a mis {e} en pause : sous son seuil, rien ne pousse. » |
| levée (reprise) | « {e} {l}, longtemps à l'arrêt, est repartie. » | « {e} {l} repart — j'ai levé ce qui la bloquait, et ça a payé. » |
| floraison | « {e} {l} s'est couverte de fleurs. » | « {e} fleurit {l} : la table est mise pour les butineurs, la nouaison se joue là. » |
| nouaison | « Des fruits se forment sur {e} {l}. » | « Nouaison {l} — le pollen reçu a porté, le fruit grossira. » |
| reproduction | « {e} a essaimé alentour {l}. » | « {e} se ressème {l} : la lignée se perpétue, le brassage a eu lieu. » |
| mort sénescence | « Le vieux pied de {e} {l} s'est éteint. » | « {e} {l} a bouclé son cycle — la sénescence, pas un accident ; sa nécromasse nourrit déjà le sol. » |
| mort asphyxie | « {e} {l} a dépéri puis succombé. » | « Noyée {l} : l'excès d'eau prolongé a fini par tuer {e}. » |
| mort gel | « {e} {l} a été emportée par le gel. » | « Le gel {l} a eu {e} — au-delà de sa rusticité, rien à faire. » |
| mort conflit | « {e} {l} a cédé la place à plus vigoureux. » | « Éclaircissage naturel {l} : {e} a perdu la course à la lumière et aux ressources. » |
| ravageur | « Des bestioles s'affairent sur {e} {l}. » | « Pression de ravageurs {l} — si les auxiliaires sont là, l'équilibre se rétablit seul. » |
| abscission | « {e} {l} laisse tomber ses feuilles. » | « Abscission {l} : {e} se déleste avant l'hiver, sa litière amorce l'humus de l'an prochain. » |
| acclimatation | « Le feuillage de {e} {l} a pris un éclat cireux, glauque. » | « {e} {l} s'est acclimatée — et ses descendants naîtront pré-armés contre ce stress. » |

---

## 6. Corpus — Encyclopédie (28 fiches × 3 niveaux)

> Voix **naturaliste qui observe** (3ᵉ personne, descriptive et factuelle, ≠ le « je »
> du carnet). **N1** = palier 1 (ce qu'on voit). **N2** = palier 2 (biologie). **N3** =
> palier 3 (rôle écosystémique). Contenu **à étudier** (sujet hors expertise de Nico) —
> botanique réelle, à relire/corriger.

### Annuelles & potagères cultivées
**Tomate** (Solanaceae · strate basse)
- N1 : Plante herbacée dressée, feuilles découpées odorantes, fruits charnus rouges.
- N2 : Annuelle gélive, thermophile — ne démarre qu'au-dessus de ~12 °C, fructifie tout
  l'été. Gourmande en eau et en azote. Sensible au mildiou (familial Solanaceae).
- N3 : S'associe au basilic et aux Astéracées qui attirent ses auxiliaires ; à éloigner
  des autres Solanaceae (partage les mêmes maladies). Gros consommateur → épuise le sol,
  à faire suivre d'une légumineuse.

**Poivron** (Solanaceae · basse)
- N1 : Buisson compact, feuilles lisses, fruits creux verts puis colorés.
- N2 : Annuelle très thermophile, encore plus frileuse que la tomate ; cycle long, a
  besoin d'une saison chaude pleine pour mûrir. Même fragilité fongique familiale.
- N3 : Même clan que tomate/aubergine — rotation et distance de rigueur. Profite des
  fleurs compagnes qui soutiennent prédateurs de pucerons.

**Haricot** (Fabaceae · sol→grimpante)
- N1 : Tige volubile ou naine, feuilles trifoliées, gousses pendantes.
- N2 : Annuelle fixatrice d'azote — ses racines hébergent des rhizobiums en nodules qui
  captent l'azote de l'air. Autofertile en azote, peu exigeante.
- N3 : Pilier des « trois sœurs » (maïs-tuteur, courge-couvre-sol) ; laisse le sol plus
  riche en azote qu'elle ne l'a trouvé. Grimpante, elle cherche un support (cf. tuteurs).

**Trèfle** (Fabaceae · sol)
- N1 : Tapis bas de feuilles à trois folioles, fleurs en pompons.
- N2 : Légumineuse fixatrice d'azote, vivace ou annuelle ; couvre-sol dense, fleurs très
  mellifères.
- N3 : Engrais vert et **paillis vivant** par excellence : enrichit en azote, protège le
  sol nu, nourrit abeilles et bourdons. Base d'une prairie fertile.

**Tournesol** (Asteraceae · basse)
- N1 : Grande tige unique, large capitule jaune tourné vers le soleil.
- N2 : Annuelle héliotrope géante, croissance très rapide ; racine pivotante profonde.
  Graines riches recherchées des oiseaux.
- N3 : Brise-vent éphémère et perchoir ; capitule = garde-manger pollinisateurs puis
  oiseaux. Légèrement allélopathique — espace ses voisines sensibles.

### Aromatiques & compagnes
**Basilic** (Lamiaceae · basse)
- N1 : Petit buisson de feuilles tendres très parfumées.
- N2 : Annuelle gélive thermophile ; floraison en épis à supprimer pour prolonger le
  feuillage. Aime chaleur et arrosages réguliers.
- N3 : Compagnon classique de la tomate (brouille les ravageurs par son parfum, partage
  le même microclimat chaud) ; ses fleurs nourrissent les petits pollinisateurs.

**Achillée millefeuille** (Asteraceae · sol)
- N1 : Feuillage finement découpé en plumes, corymbes blancs plats.
- N2 : Vivace rustique, racine traçante, très résistante à la sécheresse ; floraison
  estivale longue.
- N3 : Aimant à auxiliaires (syrphes, coccinelles, micro-guêpes) grâce à ses ombelles
  accessibles ; accumulatrice dynamique, **activatrice de compost**. Médicinale.

**Phacélie** (Boraginaceae · sol)
- N1 : Tiges souples, feuilles crénelées, fleurs bleu-mauve enroulées en crosse.
- N2 : Annuelle à croissance ultra-rapide, non apparentée aux cultures courantes (idéale
  en rotation). Floraison mellifère exceptionnelle.
- N3 : Un des meilleurs **engrais verts** : couvre vite le sol nu, étouffe les adventices,
  nourrit massivement abeilles et syrphes, puis se fauche avant graine.

**Thym** (Lamiaceae · sol)
- N1 : Sous-arbrisseau rampant ligneux, minuscules feuilles aromatiques.
- N2 : Vivace méditerranéenne, xérophile, aime le sec, le drainant et le calcaire ;
  floraison estivale.
- N3 : Couvre-sol pérenne anti-érosion ; ses essences déroutent certains ravageurs et son
  tapis fleuri nourrit les pollinisateurs en pleine chaleur.

**Lavande** (Lamiaceae · sol)
- N1 : Touffe gris-vert ligneuse, épis floraux mauves dressés très parfumés.
- N2 : Vivace méditerranéenne, xérophile et calcicole ; déteste l'excès d'eau et l'ombre.
- N3 : Bordure mellifère majeure (abeilles, papillons) ; réputée éloigner mites et
  pucerons des voisines. Structure pérenne du jardin sec.

**Bourrache** (Boraginaceae · sol)
- N1 : Plante velue rude, fleurs bleues en étoile retombantes.
- N2 : Annuelle vigoureuse qui se ressème seule ; accumulatrice de potassium ; fleurs et
  jeunes feuilles comestibles (goût de concombre).
- N3 : Aimant à abeilles parmi les plus puissants ; excellente compagne tomate/fraisier ;
  sa biomasse tendre fait un paillis riche. Pionnière auto-entretenue.

**Consoude** (Boraginaceae · sol)
- N1 : Grosse touffe de feuilles rêches, clochettes mauve-rosé.
- N2 : Vivace robuste à **racine pivot profonde** qui puise les minéraux du sous-sol ;
  repousse vite après coupe.
- N3 : Accumulatrice dynamique reine (potassium) → **purin et paillis fertilisants** ;
  barrière vivace ; fleurs très mellifères. Outil de fertilité du permaculteur.

**Moutarde** (Brassicaceae · sol)
- N1 : Tige dressée, feuilles lobées, grappes de fleurs jaunes vives.
- N2 : Annuelle à cycle éclair, piquante (glucosinolates) ; monte vite à fleur.
- N3 : Engrais vert **biofumigant** (assainit le sol en se décomposant) ; couvre-sol
  rapide et nectarifère. À ne pas enchaîner avec d'autres Brassicaceae (mêmes parasites).

### Potagères & sauvages
**Carotte** (Apiaceae · sol)
- N1 : Rosette de feuilles plumeuses finement divisées, racine pivot orange.
- N2 : Bisannuelle cultivée en annuelle ; la 2ᵉ année monte en ombelle blanche. Aime un
  sol meuble et frais.
- N3 : En fleur, son ombelle nourrit syrphes et micro-guêpes ; associée à l'oignon/poireau
  qui déroutent mutuellement leurs mouches respectives.

**Courgette** (Cucurbitaceae · sol)
- N1 : Grosses feuilles larges sur tige étalée, grandes fleurs jaunes, fruits allongés.
- N2 : Annuelle thermophile, monoïque (fleurs mâles et femelles séparées) → **dépend des
  pollinisateurs** pour nouer. Très gourmande en eau et matière organique.
- N3 : Son feuillage couvre et ombre le sol (couvre-sol des « trois sœurs ») ; pas de
  butineurs = pas de courgettes — indicateur vivant de la santé pollinisatrice.

**Mâche** (Caprifoliaceae · sol)
- N1 : Petites rosettes tendres au ras du sol.
- N2 : Annuelle très rustique au froid, cycle d'hiver ; se ressème spontanément.
- N3 : Couvre-sol hivernal qui occupe le terrain quand tout dort, limite le sol nu et le
  lessivage ; salade de soudure entre deux saisons.

**Ortie** (Urticaceae · sol)
- N1 : Tige carrée, feuilles dentées urticantes, fleurs verdâtres en grappes.
- N2 : Vivace traçante, **indicatrice de sol riche en azote** et en vie ; accumulatrice de
  fer et d'azote.
- N3 : Plante-hôte de nombreux papillons ; **purin** fertilisant et stimulant ;
  réservoir d'auxiliaires en lisière. Sa présence raconte la fertilité du lieu.

**Ail** (Amaryllidaceae · sol)
- N1 : Touffe de feuilles linéaires dressées, bulbe en gousses.
- N2 : Vivace cultivée en annuelle, riche en composés soufrés ; plantation d'automne,
  récolte d'été.
- N3 : Compagnon répulsif (pucerons, certains champignons) près des rosiers et fruitiers ;
  à éloigner des légumineuses. Assainit son voisinage.

**Myrtille** (Ericaceae · sol)
- N1 : Petit arbrisseau buissonnant, feuilles ovales, baies bleu sombre pruineuses.
- N2 : Vivace **acidophile stricte** (n'aime que les sols acides, pH bas) ; symbiose avec
  des mycorhizes éricoïdes spécifiques.
- N3 : Indicatrice/exigeante de terre de bruyère ; ses baies nourrissent les oiseaux
  (dispersion). Hors de son pH, elle dépérit — révèle l'acidité du sol.

### Adventices pionnières & indicatrices
**Bourse-à-pasteur** (Brassicaceae · sol)
- N1 : Petite rosette, hampe fine à fruits triangulaires en cœur.
- N2 : Annuelle pionnière à cycle ultra-court, plusieurs générations par an ; comestible.
- N3 : **Indicatrice de sol remué/cultivé** ; couvre fugace le sol nu. Tête de pont de la
  succession après une perturbation.

**Minette** (Fabaceae · sol)
- N1 : Petit trèfle rampant à fleurs jaunes en têtes serrées.
- N2 : Légumineuse annuelle fixatrice d'azote, frugale ; **indicatrice de sol pauvre et
  sec**.
- N3 : Colonise et **réamorce** les sols maigres en y fixant de l'azote ; fourrage et
  nectar discrets. Premier maillon vers une prairie plus riche.

**Dactyle, Fétuque rouge, Plantain lancéolé** (sprint trèfle dominant ②) : fiches dans
`sim/encyclopedie_corpus/adventices.py`, page P48 pour le plantain.

**Pâturin annuel** (Poaceae · sol)
- N1 : Petite graminée touffue, épillets verts clairs.
- N2 : Graminée annuelle ultra-pionnière, germe et grenaille en continu ; colonise tout
  sol nu.
- N3 : Premier tapis qui fixe la surface après mise à nu ; transition vers un gazon
  pérenne. Omniprésent, indicateur de sol travaillé/piétiné.

**Pissenlit** (Asteraceae · sol)
- N1 : Rosette de feuilles dentées, capitule jaune unique, aigrette ronde.
- N2 : Vivace à **racine pivot profonde**, accumulatrice dynamique ; floraison très
  précoce.
- N3 : Sa racine **décompacte** le sol et remonte les minéraux ; une des premières
  ressources de nectar pour les abeilles au sortir de l'hiver. Indicatrice de sol tassé.

### Arbres pérennes
**Figuier** (Moraceae · haute)
- N1 : Petit arbre à grandes feuilles lobées, écorce grise lisse, figues vertes/violettes.
- N2 : Pérenne caduc méditerranéen, résistant à la sécheresse une fois établi ; aime la
  chaleur réverbérée d'un mur.
- N3 : Idéal en espalier sud (microclimat chaud, albédo du mur) ; figues = manne pour
  oiseaux et insectes en fin d'été. Ombre dense estivale.

**Pommier** (Rosaceae · haute)
- N1 : Arbre à houppier arrondi, floraison blanche-rosée au printemps, pommes.
- N2 : Pérenne caduc nécessitant du **froid hivernal** (vernalisation) et une **pollinisation
  croisée** (deux variétés). Longévité de plusieurs décennies.
- N3 : Cœur du verger : fleurs = ressource pollinisatrice majeure du printemps ; sensible
  au carpocapse (guetter les auxiliaires/mésanges). Porte tout un cortège d'espèces.

**Cerisier** (Rosaceae · haute)
- N1 : Arbre élancé, écorce annelée brillante, floraison blanche abondante, cerises.
- N2 : Pérenne caduc à floraison **très précoce**, sensible aux gelées tardives ; croissance
  rapide.
- N3 : Sa floraison hâtive est une des premières grandes tables des pollinisateurs ;
  cerises = aimant à oiseaux (dispersion des noyaux).

**Noyer** (Juglandaceae · haute)
- N1 : Grand arbre à large couronne, feuilles composées aromatiques, noix en brou.
- N2 : Pérenne caduc de grande taille, croissance lente, longévité séculaire ; **émet de la
  juglone**.
- N3 : **Allélopathique** : la juglone inhibe nombre de plantes sous sa couronne — crée une
  niche particulière. Ombre profonde ; noix nourrissent la faune.

**Chêne** (Fagaceae · haute)
- N1 : Arbre massif à couronne étalée, feuilles lobées, glands.
- N2 : Pérenne caduc de très longue vie, croissance lente ; symbiose ectomycorhizienne
  étendue.
- N3 : **Espèce clé de voûte** : héberge une biodiversité immense (insectes, oiseaux,
  champignons) ; glands = ressource majeure ; pivot du wood-wide-web de la lisière.

---

## 7. Corpus — Pages secrètes (lore pur, voix multiples)

> **Zéro effet mécanique** (décision adoptée) : ces pages ne débloquent rien, ne donnent
> aucun bonus. Elles **résonnent** avec ce que le joueur vit (un thème qu'il commence à
> maîtriser) et récompensent l'exploration. **Pastiche en STYLE** — aucune citation
> réelle longue (risque copyright) : ce sont des textes *originaux* écrits *à la manière
> de*. Cinq voix. Chaque page : `id`, voix, `concept` (résonance thématique, sert au
> robinet *récompense*), `palier_thème` indicatif (ordre de révélation, pas un gate dur),
> `robinet` pressenti. Corpus **fini & épuisable** (20 entrées ici ; extensible plus tard).
>
> Rappel robinets (§2.3) : *hasard* (aléa déterministe au passage de saison / événements
> rares) · *récompense* (franchissement de palier marquant sur le concept) · *fouille*
> (action au coffret du grenier).

### Voix A — le maraîcher de la non-action *(pastiche Fukuoka)*

**P01 · « Ne rien faire est le travail le plus difficile »** — concept `non-action` ·
palier_thème ~4 · robinet *récompense*
> On me demande quoi ajouter au sol. Je réponds : enlevez d'abord vos mains. La terre
> savait faire avant nous et fera après nous. Chaque geste qu'on s'épargne, c'est un
> geste que la nature reprend — et elle le fait mieux. Le jardinier accompli se reconnaît
> à ce qu'il a cessé de faire.

**P02 · « La graine et la boue »** — concept `succession` · palier_thème ~2 ·
robinet *fouille*
> Je n'ouvre plus la terre. J'enrobe mes graines d'argile et je les laisse au sol nu ;
> celles qui doivent lever lèvent, à leur heure, sans que je choisisse pour elles. Le sol
> couvert se ressème seul. Le sol retourné n'engendre que des herbes qu'on appelle
> mauvaises parce qu'elles arrivent avant qu'on les ait invitées.

**P03 · « L'ombre du fruitier »** — concept `paillage` · palier_thème ~2 ·
robinet *hasard*
> La paille n'est pas un déchet : c'est la peau du sol. Sous elle, l'humidité reste, les
> vers travaillent, les graines d'herbe étouffent. J'ai rendu à la terre ce que la
> moisson lui avait pris, et la terre, l'année suivante, m'a rendu davantage.

**P04 · « Le verger qui se passe de moi »** — concept `transcendance` · palier_thème ~5 ·
robinet *récompense*
> La dernière année, je n'ai presque rien fait. Les arbres se taillaient par leurs
> propres branches mortes, les bêtes mangeaient les bêtes, le trèfle nourrissait les
> racines. J'ai compris que mon rôle n'était pas de commander le jardin, mais d'apprendre
> à m'en retirer sans qu'il s'effondre.

### Voix B — la jardinière des allées *(pastiche Sackville-West)*

**P05 · « Un jardin de lune »** — concept `floraison` · palier_thème ~3 ·
robinet *fouille*
> Plantez le blanc pour le soir : les fleurs pâles s'allument quand le reste s'éteint, et
> le jardin vous offre une seconde journée après le coucher du soleil. Le tabac, la
> bourrache au crépuscule, l'achillée qui retient la dernière lueur — c'est un luxe qui
> ne coûte que de l'attention.

**P06 · « De l'art de marier les voisines »** — concept `compagnonnage` · palier_thème ~3 ·
robinet *récompense*
> On ne plante pas une espèce, on compose une conversation. Le basilic chuchote à la
> tomate, la capucine attire les pucerons loin des choux comme une hôtesse détourne un
> fâcheux. Le mauvais jardin est un monologue ; le beau jardin, un dîner où chacun tient
> sa place.

**P07 · « Éloge des bordures »** — concept `pollinisation` · palier_thème ~2 ·
robinet *hasard*
> Laissez une lisière folle au bout de l'allée. C'est là, dans ce désordre toléré, que
> vivent les alliés discrets : la guêpe minuscule, le syrphe déguisé en abeille, le
> crapaud sous la pierre. Un jardin trop propre est un jardin sans défenseurs.

**P08 · « La patience des vivaces »** — concept `non-action` · palier_thème ~4 ·
robinet *fouille*
> La première année, elles dorment ; la deuxième, elles rampent ; la troisième, elles
> bondissent. Qui plante une vivace plante pour la jardinière qu'il sera dans trois ans.
> J'ai appris à aimer cette lenteur — elle me survivra, et c'est très bien ainsi.

### Voix C — les savoirs paysans *(dictons, lune, météo)*

**P09 · « Le calendrier des anciens »** — concept `météo` · palier_thème ~2 ·
robinet *hasard*
> Quand l'hirondelle rase le sol, garde ton foin ; quand l'araignée tisse au matin, le
> beau temps tient. Le ciel rouge du soir réjouit le berger, le ciel rouge du matin
> l'inquiète. Nos grands-parents lisaient le temps sur le dos des bêtes avant qu'on ne
> l'imprime sur du papier.

**P10 · « La lune montante »** — concept `lune` · palier_thème ~3 ·
robinet *fouille*
> Sème les feuilles en lune montante, les racines en lune descendante, dit-on depuis
> toujours. Que la sève écoute vraiment l'astre ou non, le dicton oblige à observer le
> ciel chaque nuit — et c'est l'observation, peut-être, le vrai secret.

**P11 · « Là où pousse l'ortie »** — concept `sol` · palier_thème ~2 ·
robinet *récompense*
> Ne maudis pas l'ortie : elle te dit que ta terre est grasse et vivante. Le chardon
> parle d'un sol compact, le pissenlit d'un sol tassé qu'il viendra percer. Les herbes
> que tu n'as pas semées sont les premières à te renseigner — encore faut-il savoir lire.

**P12 · « Ce que la fève rend à la terre »** — concept `azote` · palier_thème ~3 ·
robinet *fouille*
> Après les pois et les fèves, plante les gourmandes — choux, courges — car la
> légumineuse laisse derrière elle une richesse invisible. Nos aïeux ne connaissaient pas
> le mot azote ; ils savaient seulement qu'après la fève, tout pousse mieux.

**P13 · « L'année du gland »** — concept `succession` · palier_thème ~4 ·
robinet *hasard*
> Une bonne glandée annonce un hiver rude, prétend-on. Vrai ou faux, l'arbre qui charge
> ses fruits prépare la forêt de dans cent ans. Le paysan plante des noix qu'il ne verra
> jamais mûres : c'est sa façon de croire en l'avenir.

### Voix D — les herbiers anciens *(théorie des signatures, vertus)*

**P14 · « De la signature des plantes »** — concept `indicatrices` · palier_thème ~2 ·
robinet *fouille*
> Les anciens enseignaient que Dieu avait marqué chaque herbe du signe de son usage : la
> feuille en forme de foie pour soigner le foie, la fleur jaune contre la jaunisse.
> Naïveté, sans doute — mais derrière la fable, l'idée juste que la forme d'une plante
> raconte sa vie et son lieu.

**P15 · « La consoude, dite herbe à recoller »** — concept `accumulation` · palier_thème ~3 ·
robinet *récompense*
> On la nommait *consolida* car on lui prêtait le pouvoir de ressouder les chairs et les
> os. Ses racines plongent où nulle autre ne descend et remontent les trésors du sous-sol
> dans ses feuilles. Coupe-la, couche-la au pied de tes plants : ce qu'elle a volé à la
> profondeur, elle le donne à la surface.

**P16 · « Vertu du sureau et de l'aulne »** — concept `mycélium` · palier_thème ~4 ·
robinet *fouille*
> Sous l'écorce et sous la terre court un fil que l'œil ne voit pas. Les anciens
> parlaient d'un réseau d'âmes reliant les arbres d'une même forêt ; nous dirions
> aujourd'hui filaments. L'arbre malade est nourri par le bien portant, par des routes
> souterraines plus vieilles que nos chemins.

**P17 · « Du noyer et de son ombre maudite »** — concept `allélopathie` · palier_thème ~3 ·
robinet *hasard*
> Garde-toi de planter sous le noyer : rien n'y prospère, et l'on disait jadis que son
> ombre rendait fou qui s'y endormait. Vérité paysanne sous la superstition — l'arbre
> empoisonne le sol autour de lui pour régner seul. Toute puissance se paie d'une
> solitude.

### Voix E — les cahiers de sorcières *(préparations, décoctions)*

**P18 · « Le purin qui réveille la terre »** — concept `compost` · palier_thème ~3 ·
robinet *récompense*
> Emplis un seau d'orties fraîches, noie-les d'eau de pluie, oublie-les jusqu'à ce que
> ça pue le diable. Cette eau noire et puante, étendue au pied des plants, les fait
> bondir. Ce que la civilisation appelle engrais, la grand-mère l'appelait sa potion —
> c'était la même chose.

**P19 · « Décoction de prêle contre les fièvres du feuillage »** — concept `non-action` ·
palier_thème ~4 · robinet *fouille*
> Fais bouillir la prêle, ce végétal d'avant les fleurs, et asperge-en tes rosiers au
> petit matin. On dit qu'elle arme la plante contre les moisissures. Mais la vraie
> sorcière sait que la meilleure potion est celle qu'on n'a pas eu besoin de faire :
> soigne le sol, et la plante ne tombera pas malade.

**P20 · « Le pacte du jardin »** — concept `transcendance` · palier_thème ~5 ·
robinet *récompense*
> Au bout de bien des saisons, j'ai cessé de commander à mon jardin et j'ai commencé à
> l'écouter. Il m'a appris que je n'étais pas sa maîtresse mais sa voisine. Le dernier
> sortilège n'est pas de plier la nature à ta volonté — c'est de désirer ce qu'elle fait
> déjà. Alors le jardin se garde tout seul, et tu es libre.

---

## 8. Roadmap d'implémentation (quand Nico dira « go »)

> **Conception figée — PAS de code tant que Nico ne lance pas le sprint.** Cette section
> fixe seulement l'**ordre** et les **garde-fous**, pour qu'un sprint découpé soit lançable
> à froid. Principe invariant : **tout vit hors tick** (driver/maison), donc le **golden
> écologique reste INTACT** à chaque tronçon (aucun re-figeage). Un sous-agent qui voit le
> golden bouger doit STOP : c'est une fuite, pas un re-figeage.

### 8.1 Ordre des tronçons (≈ 6 sous-sprints autosuffisants)

| # | Tronçon | Nature | Golden | Teste |
|---|---|---|---|---|
| ① | **Extraire `sim/evenements.py`** | refactor pur | inchangé | `_evenements()` déplacé de `maitrise_detection.py` → module commun ; `Evenement` namedtuple unifié ; `maitrise_detection` ré-importe (API appelante intacte) |
| ② | **Ledger `sim/journal.py`** | ajout hors tick | inchangé (no-op sans joueur) | `journal.consigner(gs, player, log, semaine)` appelé par le DRIVER après le tick ; `gs["journal"][player] = {"entries", "resume"}` ; opt-in (pas de joueur → pas de clé) |
| ③ | **Carnet** (D14 + D43) | lecteur read-only | inchangé | `carnet_lire()` ; `CONCEPT_DE` (§5.0) ; gabarits 2 registres (§5) ; bascule au palier 3 du concept ; réglage « interprétatif anticipé » ; D43 = ligne `adaptation` |
| ④ | **Encyclopédie** | lecteur read-only | inchangé | `encyclopedie_index()` / `encyclopedie_lire()` ; fiche tronquée à `min(palier,3)` (§6) ; pas d'état neuf (palier ≥ 1 ⇒ fiche) |
| ⑤ | **Pages secrètes** (D18) | event-driven hors tick | inchangé | `pages_trouvees()` / `reveler_page()` ; `gs["pages"][player] = set` ; 3 robinets (§2.3) ; corpus §7 ; ordre par `palier_thème` ; épuisable |
| ⑥ | **Magazine** (D13) | event-driven hors tick | inchangé | `magazine_offres()` / `acheter_au_magazine()` ; sœurs au palier 3 famille (décision C) ; numéro saisonnier ; `vigueur.spend(COUT_MAGAZINE)` → `PlayerSeedBank.add` |

Dépendances : ① avant tout (socle) ; ② dépend de ① ; ③④⑤⑥ dépendent de ② mais sont
**indépendants entre eux** (parallélisables si besoin). Suggéré quand même en série pour
garder un `00_etat.md` simple et un golden vérifié à chaque cran.

### 8.2 Tests visés (par tronçon, tous golden-neutres)

- **`tests/test_evenements.py`** (①) : un log jouet → la bonne liste d'`Evenement` ;
  parité avec l'ancien `_evenements` (mêmes tuples qu'avant extraction).
- **`tests/test_journal.py`** (②) : `consigner` n'écrit rien sans joueur (golden) ;
  avec joueur, accumule les entrées ; `JOURNAL_MAX` borne l'historique.
- **`tests/test_carnet.py`** (③) : même événement, palier < 3 → texte descriptif,
  palier ≥ 3 → texte interprétatif ; réglage anticipé force interprétatif au palier 1 ;
  `acclimatation` rattaché à `adaptation` (D43).
- **`tests/test_encyclopedie.py`** (④) : palier 1/2/3 → fiche tronquée au bon niveau ;
  espèce non découverte → absente de l'index.
- **`tests/test_pages.py`** (⑤) : robinet *récompense* sur concept `X` → page de concept
  `X` due ; corpus épuisé → `None` ; déterminisme (même seed → même page).
- **`tests/test_magazine.py`** (⑥) : palier 3 sur un membre de famille → sœurs offertes ;
  achat → Vigueur dépensée + lot en banque ; offre filtrée par saison.
- **`tests/test_golden.py`** : **doit rester identique** après chaque tronçon (preuve que
  tout est hors tick).

### 8.3 Ce qui reste HORS de ce bloc (pointeurs)

- **UI Godot** des 4 voix (carnet, encyclopédie, coffret grenier, kiosque magazine dans
  la maison-hub) → vue C#, **dette D24** (portage non prioritaire, cf. mémoire priorités).
- **Calibrage D12.4** : `COUT_MAGAZINE`, `JOURNAL_MAX`, seuil `completude_ratio` éventuel,
  `PREUVES_BASE`/`R`, `PALIER_BONUS_K` — placeholders nommés, à régler post-test.
- **Terrain D15** (tuile thématique au palier 3) : mécanique propre à concevoir ; D12.2
  fixe seulement *son palier déclencheur*.
- **Marqueurs `bouture` / `oiseau` / `vent`** (événements rares) : le robinet *hasard* des
  pages s'y adossera quand ils existeront comme marqueurs de log ; **fallback** en
  attendant = ancrage sur `_hash_noise(seed, semaine, "page")` au passage de saison.
- **Corpus paliers 4-5** : l'encyclopédie n'a que 3 niveaux (décision A) ; les nuances
  expertise/transcendant (table §3, colonnes 4-5) sont un **enrichissement futur** du
  corpus, pas un blocage.

---
