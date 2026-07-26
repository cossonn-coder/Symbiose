# Sprint PÉRIPHÉRIE — état vivant (carnet de bord `/conception`)

> **Phase : CONCEPTION FIGÉE le 2026-07-26.** 7 tronçons prêts pour `/sprint-auto`.
> Ce fichier est le handoff permanent : une reprise à froid lit `CLAUDE.md` + ce
> fichier + le kickoff `0N` du tronçon et continue sans perte.
>
> Sujet : **D73 terraforming** — la périphérie agit sur le jardin, puis le joueur
> agit sur la périphérie. Amorce fournie par Nico le 2026-07-26 (12 questions).
> Rangement retenu : **`champs/peripherie`** (re-tag de `rendu/ambiance`, hérité
> de D58 à tort — le sujet est moteur, pas rendu).
>
> **Conception : `docs/champs/peripherie/conception_peripherie.md`.**
>
> ## Carte des tronçons — golden INCHANGÉ partout (aucun re-figeage autorisé)
>
> | # | Kickoff | Objet |
> |---|---|---|
> | ① | `01_ceinture.md` | état 4 secteurs + génération déterministe, **D92 refermée** — ✅ **FAIT 2026-07-26** |
> | ② | `02_exposition_abri.md` | lisière = obstacle lumière + abri, porosité/turbulence — ✅ **FAIT 2026-07-26** |
> | ③ | `03_graines_eau_corridor.md` | pluie de graines, nappe de berge, `eco.lisiere` — ✅ **FAIT 2026-07-26** |
> | ④ | `04_gestes_forestiers.md` | `abattre`/`receper`/`eteter`, outils, cinétiques, matière — ✅ **FAIT 2026-07-26** |
> | ⑤ | `05_eau_roche_erosion.md` | `endiguer`/`deriver`/`entailler`, mare, érosion — ✅ **FAIT 2026-07-26** |
> | ⑥ | `06_voix_narratives.md` | saule + 5 voix, gestes/techniques/outils, pages, événements — ✅ **FAIT 2026-07-26** |
> | ⑦ | `07_vue_godot.md` | pont 0.5.41, `DecorLayer` consomme, clic secteur, banc F5 |

---

## 1. Repérage factuel — ce que le moteur contient DÉJÀ (vérifié au grep, 2026-07-26)

Six vérifications qui **invalident des prémisses de l'amorce**. Toutes revérifiées
par lecture directe du code, pas par mémoire.

| Constat | Preuve | Conséquence sur l'amorce |
|---|---|---|
| **Hydrologie IMPLÉMENTÉE** (pas seulement conçue) | `fields/ecofields/hydrologie.py:21 tick_hydrology`, `ruissellement.py:33 tick_ruissellement`, `marais.py:29 tick_marais`/`:56 est_marais`, gestes `creuser`/`drainer` (`sim/actions/gestes.py:552,579`), coûts `ELEVE`/`MODERE` + technique/outil `("terrassement","bêche")` (`couts.py:69,115`), tests `test_marais.py`/`test_ruissellement.py`, banc `bancs/hydrologie.py` | **Q6 tranchée : OUI, implémentée.** Le barrage a un support. |
| **Le VENT est implémenté ET branché** — bien au-delà de ce que l'amorce suppose | `sim/wind.py` (masse d'air pure) + **`fields/abri.py` = champ d'abri SPATIAL** (capsule, portée ∝ hauteur, venturi, cache angulaire, mutualise `_point_in_capsule` de `light.py`). Lu par : évaporation, wind chill, thigmomorphogénèse (`wind_memory`→`port_trapu`, `croissance.py:324`), butineurs (`butineurs.py:41`), anémophilie, dégâts de rafale (`boucle.py:346`) | **Le brise-vent n'est PAS à concevoir.** `_obstacles()` (abri.py) liste maison + plantes hautes → la lisière est **une entrée de plus**. H2·brise-vent ≈ 20 lignes, pas un système. |
| **Le patron « obstacle global en coordonnées MONDE » existe** | `eco.tick_light(plants, saison, house=…, tile_origin=…)` et `eco.tick_abri(…, house=…, tile_origin=…)` (`boucle.py:183-197`) ; `light.compute` traite la maison en rectangle balayé + albédo de mur | **Pas de « masque d'horizon » neuf à inventer** (H2). Une lisière = un second obstacle du même type que la maison. |
| **LightField a un CACHE géométrique** | `light.py` `geom_key = (saison, ox, oy, maison…, tuple(obstacles))` → HIT ⇒ `return []` immédiat ; `abri.py` a son `_signature` équivalent | **Le point chaud redouté par l'amorce n'existe pas.** La ceinture est quasi statique ⇒ quelques scalaires de plus dans la clé ⇒ coût ≈ 0 en régime permanent. |
| **Un système d'OUTILS existe** (D82, l'Atelier) | `sim/outils.py` (registre `OUTILS` data-driven, `acquerir_outil`, marqueur `posseder_secateur`) + `sim/actions/deblocage.py:66 GESTE_UNLOCK` (grammaire `("action", verbe)` / `("maitrise", objet, palier)` / `("evenement", marqueur)`) | **Q8 tranchée / D93 PARTIELLEMENT PÉRIMÉE.** Gater `abattre` sur une hache = 1 entrée dans `OUTILS` + 1 dans `GESTE_UNLOCK`. Zéro conception d'inventaire. |
| **Le bois a DÉJÀ son circuit — et ce n'est PAS une jauge** (précision Nico, 2026-07-26) | `NATURES_MULCH` = paille · brf · aiguilles · feuilles → **aucune nature `"bois"`**. Le bois vit en **parcelle de litière typée `bois`** (`eco.deposer_litiere`, `fields/ecofields/matiere_organique.py:47`), manipulée par `empiler_bois` (→ pile, `STRUCTURE_ACCEPTE["pile"] = {"bois"}`, le bac le **refuse**) et `broyer` (squelette → `mulch_stock["brf"]`) | **Q12 : le bois abattu tombe en parcelles `bois` sur les plots du bord**, pas dans un stock. Plus incarné (#5 : on voit le bois par terre) et branché sur tout le circuit décompo/structures (pile = habitat, BRF = faim d'azote D40). |

**D92 quantifiée** (réplication Python du hash `decor|{seed}|{cote}` sur 300 000 seeds) :
**287 929 terrains sur 300 000 (96,0 %) ont les 4 côtés identiques ; 0 falaise.**
Distribution : `PPPP` 120 393 · `FFFF` 95 531 · `RRRR` 72 005 · `FFFR` 12 071.
→ D92 est réel et massif, **mais** il disparaît **par construction** si la vérité
migre côté Python (on écrit un tirage correct au `_hash_noise`). **D73 absorbe D92**,
ce n'est pas un prérequis séparé à traiter avant.

**Géométrie du décor existant** (`visuals/DecorLayer.cs`) : **4 secteurs cardinaux**
(nord/est/sud/ouest), bande de `DepthCm = 900` cm, frontière sinueuse, `Motif ∈
{Prairie, Foret, Riviere, Falaise}` + `PenteFalaise`. La couture `BuildProfile(seed)`
est le point d'entrée unique, explicitement documentée « le pont pourra alimenter la
même struct sans toucher au rendu (dette D73) ».

**Golden** : `tests/test_golden.py build_world` **ne pose AUCUNE maison** (2 tuiles,
8 espèces, pas de `house`). ⇒ une ceinture **opt-in** (absente par défaut, patron
`house=None` / `vent_force=0` → champ nul) laisse le golden **INTACT**.

---

## 2. Décisions ARRÊTÉES

**D-1 — Maille & vérité : 4 secteurs cardinaux, état moteur Python** (Nico, 2026-07-26).
La ceinture vit dans `game_state` côté Python (persistable, déterministe, lisible par
les champs) à la maille qui existe déjà côté vue : 4 secteurs (N/E/S/O), bande de 9 m.
`DecorLayer.BuildProfile` **cesse d'être générateur** et consomme le snapshot — la
couture T4 de D58 était écrite pour ça. *Rationale* : aligné sur l'existant des deux
côtés, un seul niveau de granularité à tenir cohérent (pont + save + rendu), et **D92
disparaît par construction** (le tirage repart d'un `_hash_noise` correct en Python).
Granularité d'un geste = un secteur entier (« j'ouvre une clairière au nord »).

**D-2 — UN seul sprint, ordre interne entrant → sortant** (Nico, 2026-07-26).
L'ordre défendu par l'amorce est conservé (flux entrants d'abord, sinon les gestes sont
creux) mais **n'est pas une frontière de sprint** : tous les points de greffe existent
déjà (abri, lumière, seedbank, hydrologie, outils), donc le couplage entrant fait 2-3
tronçons, pas une fondation. *Rationale* : couper en deux ferait repayer deux fois
l'amorçage de la ceinture et de son pont. ~7 tronçons, le dernier = vue Godot.

**D-3 — « Comptabilisé » = ledger + trace dans le milieu + matière** (Nico, 2026-07-26).
Trois lectures sur les quatre de H4 : consignation au ledger (carnet / encyclopédie /
détection de maîtrise), état écologique persistant (`souche_memory`, clairière,
cicatrice, éboulis), et retour de matière en **parcelles de litière `bois`** posées au
sol (circuit `empiler_bois`/`broyer` existant — surtout PAS une jauge). Le coût
Vigueur est ÉLEVÉ mais **justifié par l'effort physique**, PAS par « action directe sur
le vivant » — l'arbre périphérique est un agrégat, pas une `PlantInstance` ; fonder un
barème sur cette fiction se paierait plus tard. **Aucun indicateur d'impact cumulé**
(#5).

**D-4 — Essence dominante par secteur, pas de forêt d'espèces** (conception, aval de D-1).
Un secteur `foret` porte une **essence dominante** tirée du seed parmi le catalogue
ligneux EXISTANT (hêtre, charme, bouleau, aulne). Elle détermine le comportement au
recépage (rejette / meurt) et la densité d'ombre. *Rationale* : hétérogénéité (#7)
gratuite, réutilise le catalogue, et évite de simuler N arbres (D32). Un secteur `foret`
adjacent à une `riviere` devient **ripisylve** (aulne/saule) — exact écologiquement.

**D-5 — Une seule espèce ajoutée : le SAULE** (règle « le catalogue grandit avec les
idées », signalée). Archétype de la **trogne** (le sprint invente `eteter`, il lui faut
son incarnation), essence normande du bocage, et il **se bouture spontanément** → croise
l'événement rare « bouture » et le canal d'acquisition #2 déjà en place. Reçoit ses
**5 voix** au tronçon narratif. Noisetier et prunellier/ronce sont **écartés** (portés
par le charme et le bouleau côté agrégat) → notés au BACKLOG, pas au sprint.

---

## 3. Questions ouvertes / options en balance

Les 12 questions de l'amorce, révisées après repérage. **8 sont tranchées par les
faits ci-dessus** ; il reste 4 vrais arbitrages, dont 3 remontés à Nico.

| Q | Statut après repérage |
|---|---|
| Q1 vérité de la périphérie + maille | **Proposé** : état moteur Python, maille = **4 secteurs cardinaux** (aligné sur l'existant C#), pas une ceinture 2×2 m. La vue devient consommatrice. → arbitrage Nico. |
| Q2 un sprint ou deux | **Contre-proposition** : UN sprint. Les points de greffe existent tous ⇒ le couplage entrant n'est pas une fondation mais 2-3 tronçons. L'ORDRE interne de l'amorce reste juste (entrant d'abord). → arbitrage Nico. |
| Q3 re-figeage golden | **TRANCHÉE : golden INTACT.** Ceinture opt-in, golden sans maison. Le « re-figeage LARGE » annoncé par l'amorce est évitable. |
| Q4 jusqu'où simuler la ceinture | **TRANCHÉE : champ agrégé pur.** Le cache `geom_key` rend l'agrégat gratuit ; une lisière en vraies `PlantInstance` rouvrirait D32 sans bénéfice. |
| Q5 réutiliser `creuser`/`drainer` | **TRANCHÉE : oui**, les gestes existent avec coûts et outil. Mare périphérique = `creuser` sur secteur. |
| Q6 statut hydrologie | **TRANCHÉE : implémentée.** |
| Q7 D92 d'abord ? | **TRANCHÉE : non**, D73 l'absorbe (le tirage passe en Python). |
| Q8 gating par outil | **TRANCHÉE : oui, trivial** — `sim/outils.py` + `GESTE_UNLOCK` existent (D82). |
| Q9 forme de la comptabilité | **Proposé** : H4-2 (ledger) + H4-3 (trace dans le milieu) + H4-4 (matière), **pas** d'indicateur d'impact cumulé (violerait #5). H4-1 (Vigueur) retenu mais **re-justifié** : effort physique, pas « action sur le vivant » (l'arbre périphérique n'est pas une `PlantInstance`). |
| Q10 cinétique de repousse | À chiffrer en aval (bio). Ordres visés : recépage 7-12 ans, clairière 30-60 ans, falaise jamais. |
| Q11 érosion | **Proposé** : modéliser, mais **minimalement** — c'est le seul retour lisible d'une coupe excessive. |
| Q12 le bois | **TRANCHÉE : parcelles de litière `bois` au sol**, circuit `empiler_bois`/`broyer` existant. **Pas** de nature `"bois"` dans `mulch_stock` (précision Nico). |

**Trous trouvés dans l'amorce** (à intégrer à la conception) :
- **T1 — le brise-vent POREUX est la leçon centrale, pas une note de bas de page.**
  Une haie claire protège **plus loin** qu'un mur plein (qui crée turbulence + venturi).
  ⇒ `densite_ligneuse` module la portée d'abri **non-monotoniquement** ⇒ **abattre
  partiellement peut AMÉLIORER l'abri**. Contre-intuitif, émergent, zéro tutoriel (#6).
  Le moteur a déjà `ABRI_REDUCTION_MAX` + `ABRI_VENTURI_BOOST` pour le porter.
- **T2 — « corridor faune → `habitat_fn` » est un piège #2.** Formuler en **flux
  d'immigration** aux plots de bord (patron pluie de graines), jamais en bonus d'habitat.
- **T3 — la rivière n'a PAS de grille hydraulique hors jardin.** « Même physique
  appliquée hors terrain » est faux : `altitude`/`eau_surface` s'arrêtent au jardin.
  Le barrage doit se traduire en **condition aux limites** (une berge qui pousse ou
  retire de l'eau aux plots du bord concerné), pas en simulation d'un cours d'eau.

---

## 4. Coût perf estimé

- Ceinture = 4 secteurs (O(1)), gestes event-driven hors tick ⇒ nul.
- Lisière comme obstacle de lumière/abri : **absorbée par les caches existants**
  (`geom_key` light, `_signature` abri). Statique ⇒ ≈ 0 en régime permanent.
- Budget visé : **< +2 % de tick**, très en-deçà du plafond projet (+10 %/tronçon).

---

## 5. Décisions de conception prises en aval (sans question à Nico)

- **Brise-vent : la règle des manuels ne s'applique PAS à cette échelle.** Derrière une
  lisière de 15 m, un jardin de 20 m tient entre 0 et 1,3 H — le mur plein y est *le
  plus* protecteur, et la parabole de portée (20-30 H) ne discriminerait rien. Ce qui
  s'exprime à 0-3 H est la **turbulence de décollement** ⇒ porosité module la réduction
  du vent moyen (linéaire) **et la rafale** (quadratique). Leçon : une lisière trop
  dense abrite du vent constant mais fait tomber des rafales.
- **Ombre saisonnière : rien à écrire.** À 49°N, une lisière de 15 m au sud donne 47 m
  d'ombre en hiver, 17 m aux équinoxes, 7 m en été (n'atteint pas le jardin, bande de
  9 m). Ça sort de `solar_slice` + `_point_in_swept_rect` existants.
- **Essences qui rejettent** : charme, aulne, saule → oui ; **hêtre et bouleau → non**
  (recéper une hêtraie, c'est l'abattre). Le catalogue porte déjà les deux camps.
- **Cinétiques** : trogne 5 ans · recépage 10 ans · abattage → pionnières 4 ans, canopée
  30 ans · entaille jamais · barrage non entretenu rompt vers 8 ans.
- **Érosion : retenue, minimale** — greffée sur `structure_sol` (D30), colluvions sur les
  plots de bord, aucun champ neuf. C'est le seul retour qui rend l'irréversible visible.
- **Corridor faune** : le champ de population colonise déjà depuis zéro ⇒ pas de barrière
  à lever. Passe par un **champ du milieu** `eco.lisiere` + poids `lisiere_w` par spec
  (défaut 0.0) — jamais par un bonus d'habitat conditionnel.

## 5bis. Avancement des tronçons

### ① Ceinture moteur — ✅ CLOS le 2026-07-26

- **Créé** `data/code/fields/peripherie.py` (79 LDC pur, 🟢) : `PROFONDEUR_CM = 900`,
  `COTES`, canaux-sentinelles **tranche 91_00x** (`K_TYPE`/`K_ESSENCE`/`K_HAUTEUR`/
  `K_DENSITE`/`K_EAU`/`K_ROCHE`), `voisins(cote)`, `secteur_neutre(cote)`,
  `generer_ceinture(seed) -> list[dict]` (3 passages : type → couplage falaise →
  scalaires+essence). Couche `fields`, n'importe QUE `fields.noise`. **Rien n'est
  branché** : aucun module de la boucle ne l'importe (pas même `fields/__init__.py`,
  volontairement — ② l'y ajoutera au moment du câblage) ⇒ neutralité structurelle.
- **Créé** `data/code/tests/test_peripherie.py` (120 LDC) — **16/16 OK**.
- **Golden INCHANGÉ** : `57c166d8d3626444e0fc9b88b360edc62c047927f7608c45fefae35a6bba08da`.
- **D92 mesurée refermée** sur 300 000 seeds : 4 côtés identiques **2,7 %**
  (avant : 96,0 %) · terrains avec falaise **52,0 %** (avant : 0 %) · présence
  forêt 82,2 % / rivière 68,3 % / prairie 44,4 % / friche 19,5 %.
  Deux correctifs par rapport au C# : décalage par côté sur **deux grands premiers**
  (`7 919` / `104 729`, l'avalanche de `_hash_noise` ne suffisait pas à décorréler
  `cote±1`) **et** adjacence **symétrique** (les deux voisins, plus le seul sens
  horaire) avec condition réalisable (`ni rivière ni forêt`, plus « resté prairie »).
- **⚠️ À valider par Nico (calibrage, pas bug)** : la règle de falaise du kickoff,
  appliquée littéralement, donne **52 % de terrains portant une falaise** — très
  au-dessus du plancher demandé (≥ 5 %). C'est l'arithmétique de la règle
  (P(prairie|friche) 0,40 × P(≥1 voisin rivière) 0,44 ≈ 0,17 par secteur). Si la
  falaise doit rester un accident de terrain rare, il faut **ajouter un tirage de
  conversion** (p. ex. `K_ROCHE < 0,35`) — décision de design, pas absorbée ici.
  Se juge au **F5 du tronçon ⑦** (est-ce que ça se voit trop ?).
- Écarts assumés au modèle §4.1 : pas de champ `pente` ni `seed_secteur` (présents
  côté `DecorLayer` uniquement) — le modèle figé ne les liste pas ; ⑦ les dérivera
  du seed monde + `cote` s'il en a besoin.

### ② Exposition & abri — ✅ CLOS le 2026-07-26

- **`fields/peripherie.py`** (79 → 117 LDC, 🟢) : ajout de la **géométrie MONDE** de
  la ceinture — `MONDE_CM = 2000.0` (miroir exact de `WorldView.WorldCm`, le moteur
  n'avait aucune constante d'emprise globale), `rect_secteur(cote)` (emprise
  `(x0,y0,x1,y1)` de la bande, repère sol x=Est/y=Sud comme `light.py`),
  `occulteurs(ceinture)` → `(x0,y0,x1,y1,hauteur,opacité)` pour `light`, et
  `obstacles_abri(ceinture)` → `(cx,cy,h,rayon,poro)` pour `abri`.
  `TYPES_OCCULTANTS = ("foret","falaise")` — prairie/rivière/friche n'ont pas de
  hauteur, elles n'ombrent ni n'abritent. **Aucun `fields/lisiere_geom.py` créé** :
  la géométrie de la bande EST la responsabilité de `peripherie`, et `light.py`
  reste à 262 LDC (🟢) — pas de scission nécessaire.
- **`fields/light.py`** (262 LDC, 🟢) : `compute(..., ceinture=None)`. Les occulteurs
  sont des **rectangles balayés** (`_point_in_swept_rect`, mêmes helpers que la
  maison) mais à ombre **PARTIELLE** (`att *= 1 − opacité`, là où la maison masque à
  0). Pré-calcul par tranche solaire de `(longueur d'ombre, transmission)` → une
  multiplication par secteur, pas par échantillon. `lisieres` **entre dans
  `geom_key`** → une coupe du ④ invalide le cache ; ceinture statique ⇒ HIT.
  **Zéro `if saison`** : l'asymétrie hiver/été sort de `solar_slice`.
- **`fields/abri.py`** (116 LDC, 🟢) : `_obstacles(..., ceinture=None)` passe en
  **5-uplets** `(cx,cy,h,rayon,poro)` ; `poro=None` pour maison/plantes ⇒ branche
  `ABRI_REDUCTION_MAX * frac` **bit-identique** (porosité des haies du jardin = D94).
  Lisière : `reduction = REDUCTION_LISIERE_MAX·(1−φ)·frac` (linéaire) **et**
  `turbulence *= 1 + TURBULENCE_MUR·(1−φ)²` (quadratique — formule du kickoff prise
  au mot, **sans** dégressivité `frac` sur la turbulence). `poro` ajouté à
  `_signature`. `_build_facteur` renvoie `(facteur, turbulence)` ; le cache
  `eco._abri_cache` passe de 2 à **3 éléments**.
- **Nouveau champ `eco.turbulence`** (`GridField` **LAZY, None au repos**, plafond
  `TURBULENCE_PLAFOND = 2.0`) : multiplicateur de **rafale LOCALE**. Son SEUL lecteur
  est `_wind_damage` (`sim/engine/mortalite.py`), qui lit 1.0 quand le champ est None
  ⇒ casse mécanique **bit-identique** sans ceinture. Pas exposé à `get_field`
  (cohérent avec `eco.vent`, qui n'y est pas non plus).
- **Constantes** (`fields/ecofields/constants.py`) : `REDUCTION_LISIERE_MAX = 0.75`,
  `TURBULENCE_MUR = 0.45`, `TURBULENCE_PLAFOND = 2.0` + le bloc pédagogique §3.2
  (pourquoi PAS la parabole de portée des manuels).
- **Câblage** : `fields/ecofields/ticks.py` (passe-plats `tick_light`/`tick_abri` —
  ils sont **là**, pas dans `container.py` comme l'annonçait le kickoff) et
  `sim/engine/boucle.py` (`ceinture=self.game_state.get("ceinture")` aux deux appels).
  **Pas de ré-export dans `fields/__init__.py`** : `light`/`abri` importent
  `fields.peripherie` directement, personne ne fait `from fields import ...` — le ⑦
  l'ajoutera s'il en a besoin.
- **Tests** `tests/test_peripherie.py` (120 → 228 LDC) : **38/38 OK**. 4 suites
  neuves — E neutralité (champs bit-identiques `None` vs ceinture neutre, aux 4
  saisons, + `turbulence is None`), F saisonnalité (lisière SUD : bord nord **−49 %**
  en hiver, **−0 %** en été ; lisière NORD : lumière-sol **inchangée aux 4 saisons**),
  G porosité (dense abrite plus ET turbule plus, turbulence ×3.24 contre réduction
  ×1.80 ⇒ non-linéarité vérifiée), H caches (HIT/MISS prouvés par sentinelle dans le
  champ, pas par le code de retour — `compute` renvoie `[]` dans les DEUX cas).
- **Golden INCHANGÉ** : `57c166d8d3626444e0fc9b88b360edc62c047927f7608c45fefae35a6bba08da`.
  Suite complète relancée : seuls `test_encyclopedie` (64/68) et `test_sim_server`
  (269/270, pommier sans fruits) échouent — **échecs PRÉ-EXISTANTS**, vérifiés
  identiques sur l'arbre propre (`git stash`).
- **Fumée d'intégration** : monde du golden + `game_state["ceinture"] =
  generer_ceinture(7)` (forêts N 19,8 m / E 15,9 m, rivières S+O) × 60 semaines →
  aucun crash ; `lumiere` moyenne T0 0.235 (hiver, ombrée par l'EST au matin),
  `turbulence` moyenne 1.31.
- **⚠️ À valider par Nico (calibrage, F5 ⑦) — écart assumé à la conception §3.1** :
  l'occulteur est **toute la bande** `[bord, bord+900]`, donc sa face PROCHE est au
  bord du jardin. La table §3.1 (« 7 m en été, n'atteint pas le jardin ») supposait
  implicitement la lisière **en retrait de 9 m**. Conséquence : une forêt au sud
  ombre ~7 m du jardin à midi en été (au lieu de 0). Le kickoff définissait
  explicitement le rectangle comme la bande → suivi au mot, **aucune constante de
  retrait spéculative ajoutée**. Si Nico veut retrouver la table, c'est UNE constante
  (`RETRAIT_LISIERE_CM`) dans `rect_secteur`.
- Autre écart mineur signalé : la turbulence n'est **pas** dégressive le long du
  sillage (le kickoff donne la formule sans `frac`), là où la réduction d'abri l'est.

### ③ Graines, eau, corridor — ✅ CLOS le 2026-07-26

Trois flux entrants, chacun greffé sur un système existant, **aucun système neuf**.

- **`fields/peripherie.py`** (117 → 139 LDC, 🟢) : ajout du helper GÉOMÉTRIQUE partagé
  par les trois flux — `plots_de_bord(cote, rows, cols, tile_origin, portee_cm)`,
  **générateur** de `(r, c, poids)` avec décroissance linéaire de la distance au bord
  (1 au contact, 0 à la portée). Ne parcourt que l'axe perpendiculaire (≤ 40 itérations)
  puis, pour les seules rangées dans la portée, l'axe parallèle ⇒ **O(portée × côté)**,
  jamais O(rows × cols) (réflexe D32). Une tuile loin du bord ne rend RIEN. Aucun
  `fields/lisiere_geom.py` : la géométrie de la bande reste la responsabilité de
  `peripherie`. Nouvel import `constants.PLOT_CM` (couche fondation, OK).
- **A. Pluie de graines** — `fields/seedbank.py` (215 → 254 LDC, 🟢) :
  `tick_apport_peripherie(ceinture, tile_origin)`, patron **exact** de
  `tick_late_succession_enrichment` (même geste : un apport hebdo dans la banque),
  + `apport_secteur(secteur)` (table écologique : friche→`pioneer` 0.0010,
  forêt→`competitor` 0.0008 × `densite_ligneuse`, prairie→`grass` 0.0004,
  rivière/falaise→rien). Portée **4 plots (200 cm)**. Câblé via
  `EcoFields.tick_seed_bank(..., ceinture, tile_origin)` (`fields/ecofields/sol.py`),
  **appelé seulement si `ceinture`** ⇒ sans ceinture la banque n'est même pas touchée.
  C'est le support mécanique qui manquait au **canal d'acquisition #3**.
- **B. Nappe de berge** — nouveau mixin **`fields/ecofields/bordure.py`** (49 LDC, 🟢),
  ajouté aux bases d'`EcoFields` : `tick_berge(ceinture, tile_origin)`. Un secteur
  `riviere` pousse (`ligne_eau > 0`) ou retire (`< 0`) de l'eau dans les pores des
  **3 premiers plots** du bord. **Placé JUSTE AVANT `tick_hydrology`** (étape 2e de
  `boucle.py`) : tout le reste ÉMERGE du circuit existant (capture du surplus en lame
  de surface → `tick_ruissellement` → `marais_memory` → `est_marais`), zéro ligne de
  physique neuve, aucune grille hors jardin. **Piège trouvé et traité** : `humidite.add`
  écrête SILENCIEUSEMENT à `HUM_CAP` — sans routage explicite du surplus vers
  `eau_surface` (miroir de l'étape 5 de `tick_hydrology`), **aucun marécage de berge
  ne pouvait naître**. Calibrage mesuré : `ligne_eau` +40 ⇒ marais au bord en ~80
  semaines · +20 ⇒ marais · +10 ⇒ gorgé sans marais · +4 ⇒ humide · négatif ⇒ bord
  asséché (0.01). Gradient lisible, pas un interrupteur.
- **C. Corridor de lisière** — même mixin : `maj_lisiere(ceinture, tile_origin)` publie
  **`eco.lisiere`** (`GridField` ∈ [0,1], **LAZY, None au repos**, patron
  `eco.turbulence` du ②). Gradient sur **8 plots (400 cm)** ∝ `INTENSITE_LISIERE`
  (forêt 1.00 · friche 0.90 · rivière 0.50 · prairie 0.20 · falaise 0.15), combiné
  entre bords par **MAXIMUM** (un coin n'est pas deux fois une lisière).
  **MÉMOÏSÉ** sur `(types des secteurs, tile_origin)` via `self._lisiere_sig` — la
  ceinture est quasi statique ⇒ calculé une fois ; une coupe du ④ change le type ⇒
  recalcul. Réponse **déclarée par guilde** : `TrophicSpec.lisiere_w` (défaut **0.0**),
  terme additif dans `capacite` (`fields/population/field.py`), lu SEULEMENT si
  `lisiere_w > 0` **et** champ présent ⇒ sinon **non calculé**, bit-identique.
  Poids renseignés (`registry.py`) : hérisson 0.30 · carabe 0.25 · merle 0.25 ·
  chrysope 0.20 · coccinelle 0.20 · syrphe 0.15 (via `PollinatorSpec.lisiere_w`) —
  **14 guildes restent à 0.0**, ravageurs de culture compris. Aucun terme d'habitat
  conditionnel : le milieu porte l'information, la guilde y répond (philo #2).
- **Câblage** `sim/engine/boucle.py` : `maj_lisiere` en **2a-bis** (après `tick_abri`,
  groupé avec les couplages de ceinture, mémoïsé donc ~gratuit, bien avant son unique
  lecteur `tick_populations`), `tick_berge` en **2e** (avant l'hydrologie),
  `tick_seed_bank` reçoit `ceinture` + `tile_origin` (étape 14).
- **Constantes** (`fields/ecofields/constants.py`) : `BERGE_PORTEE_CM = 150`,
  `BERGE_FLUX_PAR_CM = 0.010`, `LISIERE_PORTEE_CM = 400`, `INTENSITE_LISIERE` + deux
  blocs pédagogiques (pourquoi une condition aux limites et pas une rivière ; pourquoi
  un champ du milieu et pas un bonus d'habitat).
- **Tests** `tests/test_peripherie.py` (228 → 415 LDC) : **71/71 OK**. 4 suites neuves —
  ③bis `plots_de_bord` (4 rangées par côté, poids bornés, tuile centrale vide, portée
  nulle), I graines (gradient strict 0.203→0.147→0.090→0.034, **nul au-delà de 4 plots**,
  bord opposé intact, autres archétypes intacts, apport forêt ∝ densité, rivière/falaise
  muettes, neutralité sans ceinture), J berge (bord gorgé ×3.5 / asséché ×0.01, lame de
  surface, **marais émergent au bord et pas à 5 m**, hors-portée bit-identique,
  neutralité), K corridor (gradient, MAX au coin, mémoïsation prouvée par sentinelle,
  retour à None, guilde sensible enrichie au bord et **pas au centre**, guilde à
  `lisiere_w = 0.0` **inchangée au bit près**, audit du registre).
- **Golden INCHANGÉ** : `57c166d8d3626444e0fc9b88b360edc62c047927f7608c45fefae35a6bba08da`.
  Suite complète relancée (71 fichiers hors golden/périphérie/500ans) : `test_sim_server`
  269/270 (pommier sans fruits) et `test_auxiliaires` (0 dégât des deux côtés) —
  **échecs PRÉ-EXISTANTS**, `test_auxiliaires` revérifié IDENTIQUE sur l'arbre propre
  (`git stash`). Tout le reste vert, dont `test_population`, `test_faune_dediee`,
  `test_marais`, `test_ruissellement`, `test_eau`, `test_diversite_fondatrice`.
- **Fumée d'intégration** : monde du golden + `House` + `ceinture = generer_ceinture(7)`
  (forêts N/E en aulne, rivières S+O à `ligne_eau` −77/−76) × 60 semaines → aucun crash ;
  `lisiere` moyenne T0 0.625 / T1 0.083, `turbulence` 1.31, bords asséchés par les deux
  rivières en creux (T0 `humidite` 0.406), carabe/merle/hérisson présents.
- **⚠️ Écart ASSUMÉ et signalé — la prairie n'est pas neutre.** Le kickoff demande
  `prairie → grass` (modérée) et le ③ donne à la prairie une intensité de lisière 0.20.
  Or `secteur_neutre()` est de type `prairie` ⇒ une ceinture « neutre » (4 prairies
  rases) N'EST PLUS neutre pour ces deux flux (elle l'est toujours pour ombre/abri/
  turbulence/graines forestières, qui dépendent d'une hauteur ou d'une densité
  ligneuse). Choix : suivre le kickoff (une prairie SÈME et porte un ourlet — c'est de
  l'écologie) et **corriger la docstring de `secteur_neutre`**, plutôt qu'inventer un
  champ « densité herbacée » hors périmètre. **L'interrupteur opt-in qui protège le
  golden reste l'ABSENCE de ceinture**, ce qui est le cas du golden. À trancher par
  Nico s'il veut un état de ceinture strictement inerte.
- **⚠️ Taille** : `tests/test_peripherie.py` à **415 LDC** (> 400 🔴). Justifié et
  signalé : le kickoff prescrit explicitement d'ÉTENDRE ce fichier, sa responsabilité
  reste unique (tests de la ceinture), et les ④⑤ vont encore l'alimenter → scission à
  confier au **`/refactor`** de fin de sprint (candidat : un fichier par tronçon).
- Écart mineur : `eco.lisiere` **n'est pas exposé à `get_field`** (donc pas d'overlay
  debug F6 ni de pont) — cohérent avec `eco.vent`/`eco.turbulence` du ② ; à décider au ⑦.

### ④ Gestes forestiers — ✅ CLOS le 2026-07-26

Trois gestes, une cinétique, un retour de matière. **Aucun système neuf** : tout se
greffe sur l'existant (`sim/actions`, `cout_action`, `OUTILS`/`GESTE_UNLOCK`,
`deposer_litiere`, canal `log` du ledger).

- **Découpage des responsabilités** (écart ASSUMÉ au kickoff, motivé) : le kickoff ne
  prévoyait qu'un fichier (`sim/actions/paysage.py`). Livré en **deux**, parce que ce
  sont deux responsabilités :
  - **`fields/peripherie.py`** (139 → 196 LDC, 🟢) — la MUTATION de l'état et sa
    CINÉTIQUE : `ESSENCES_QUI_REJETTENT`, table `CINETIQUES`, `DENSITE_PIONNIERE`
    (= `DENSITE_FRICHE[1]`), `SEMAINES_PAR_AN`, `NOMS_COTES`, `couper_secteur(secteur,
    geste)`, `tick_repousse(ceinture, semaines=1.0)`. L'état vit là depuis le ① : ses
    transitions y vivent aussi, sans joueur, sans coût, sans RNG.
  - **`sim/actions/paysage.py`** (NEUF, 68 LDC pur, 🟢) — la couche JOUEUR : gate
    d'outil, coût de Vigueur, bois déposé, trace au ledger — `abattre`/`receper`/
    `eteter`, et rien d'autre (aucun accesseur spéculatif : ⑥/⑦ liront `CINETIQUES`).
  - Bénéfice : `tick_repousse` s'importe depuis `fields` dans `boucle.py` — **aucune
    remontée de `sim.engine` vers le paquet `sim.actions`** (le sens des couches reste
    `fields ← sim ← engine`).
- **3 champs de secteur ajoutés** à `secteur_neutre()` : `geste_coupe` (la cinétique en
  cours, `None` = peuplement reconstitué), `densite_avant`/`hauteur_avant` (le
  peuplement MÛR, cible de repousse, mémorisé par **MAXIMUM** ⇒ recouper avant
  reconstitution n'efface pas la mémoire du terrain).
- **« Recéper une hêtraie, c'est l'abattre » est LITTÉRAL dans le code** :
  `couper_secteur` RENVOIE le geste dont la cinétique s'applique — `receper` sur hêtre/
  bouleau renvoie `"abattre"` (souche morte, 30 ans). Le geste n'est jamais bloqué, rien
  ne l'annonce (philo #6) ; le ledger, lui, le consigne.
- **Cinétiques** (interpolation linéaire déterministe, zéro tirage) : trogne **5 ans**
  (densité CONSERVÉE, hauteur ×0.6) · taillis **10 ans** · abattage **30 ans**. Les DEUX
  lignes de la table §4.4 pour l'abattage sont rendues **sans machinerie** : la densité
  prend le **MAXIMUM** de la courbe de canopée (30 ans) et d'un **plancher pionnier**
  (`DENSITE_PIONNIERE` atteint en 4 ans) ⇒ le vide se remplit vite, la structure est
  lente. Mesuré : charme recépé 0.500 à 5 ans → **0.800 pile à 10 ans** ; abattage 0.250
  à 4 ans, **0.333 seulement à 10 ans**, plein à 30. Départ borné par la cible
  (`min(densite_res, cible)`) ⇒ couper une friche clairsemée ne la densifie jamais.
- **Retour de matière** : `BOIS_COUPE_PAR_CM = 0.002` × densité debout × hauteur retirée,
  déposé en parcelles de litière **`bois`** sur **2 rangées** de plots du bord
  (`BOIS_PORTEE_CM = 100`, via `plots_de_bord`, poids 0.75/0.25). **Aucun stock crédité**,
  aucune nature `"bois"` créée. Vérifié : la **pile** accepte, le **bac REFUSE**. Étêter
  rend moins que d'abattre (la tête, pas le fût). Une tuile loin du bord ne reçoit RIEN.
- **Outils (D93 tombe pour ce périmètre)** : `sim/outils.py` gagne **serpe 50 · hache 70
  · pioche 60** (placeholders F5, ordonnés comme l'effort qu'ils permettent), porte
  Vigueur-SEULE comme le sécateur. `GESTE_UNLOCK` : `abattre ← posseder_hache`,
  `receper ← posseder_serpe`, `eteter ← ("action","receper")` (la trogne s'apprend APRÈS
  le taillis, pas en achetant un outil de plus). `DECLENCHEURS` absorbe `receper` par
  simple dérivation — rien à câbler côté pont.
- **Coûts** : nouveau palier **`TRES_ELEVE = 60.0`** (`couts.py`) — le barème s'arrêtait à
  `ELEVE`, ce qui aurait mis abattre et recéper au même prix alors que leur ASYMÉTRIE est
  toute la leçon. Additif (aucun geste existant ne le référence). `OBJETS_TOUCHES` :
  `("essartage","hache")` · `("taillis","serpe")` · `("trogne","serpe")` — les trois
  techniques reçoivent leurs voix au ⑥.
- **Ledger** : ligne `🪓` dans `game_state["log"]`, patron EXACT de
  `quetes._consigner_accomplissement` (le canal existant ; `journal.consigner` la verse
  au ledger après le tick). **Le parseur de `sim/evenements.py` n'est PAS touché** —
  c'est le périmètre du ⑥ ; une ligne non reconnue est ignorée sans dommage.
- **Câblage** `sim/engine/boucle.py` : `tick_repousse(...)` en **1c**, une fois par monde
  (la ceinture n'appartient à aucune tuile), **AVANT** la boucle des tuiles pour que
  lumière (2) et abri (2a) lisent la hauteur/densité de CE tick. O(4), no-op strict sans
  ceinture ou sans coupe en cours.
- **Caches — le point légué par le ③, vérifié** : `light.geom_key` inclut
  `tuple(lisieres)` (hauteur + opacité=densité) et `abri._signature` inclut
  `(h, poro)` ⇒ **les deux invalident sur hauteur ET sur densité**, prouvé par sentinelle
  dans le champ (suite Q). Une trouée au sud fait passer la lumière-sol du bord de
  **0.150 à 1.000** en hiver.
- **`eco.lisiere` répond désormais à la coupe** (⚖️ **arbitrage Nico, 2026-07-26** — le
  ③ l'avait laissé porté par le SEUL type, ce qui tenait tant que la ceinture était
  figée ; le ④ la fait bouger, et un corridor inerte après un abattage rendrait le geste
  destructeur creux sur ce flux). Modèle : **le type reste l'ARCHÉTYPE, la
  `densite_ligneuse` en module l'INTENSITÉ** — nouveau helper PUR
  `bordure.intensite_lisiere(secteur)` = `INTENSITE_LISIERE[type] × (LISIERE_SOCLE +
  (1 − LISIERE_SOCLE) × densité/DENSITE_FORET[1])`, **affine et monotone croissante**
  (aucune non-linéarité inventée — la non-linéarité reste du côté de l'abri, §3.2).
  - Le **socle** (`LISIERE_SOCLE = 0.25`, `fields/ecofields/constants.py`) est
    ÉCOLOGIQUE, pas un garde-fou numérique : une trouée fraîche n'est pas du béton (il
    reste la litière, le bois mort, l'ourlet). Il garantit en prime que **l'ORDRE des
    archétypes tient** (friche la plus clairsemée 0.261 > prairie 0.20), ce qu'une
    simple multiplication aurait inversé.
  - **Seuls les types à strate ligneuse sont modulés** (`LISIERE_TYPES_LIGNEUX =
    ("foret","friche")`) : prairie/rivière/falaise ont une densité nulle par
    construction, les moduler les annulerait — elles gardent le comportement du ③,
    **intact** (vérifié).
  - Normalisation **dérivée** de `DENSITE_FORET[1]` (import, pas de valeur recopiée) :
    un recalibrage du ① suit automatiquement.
  - **`_lisiere_sig` inclut la densité** ⇒ une éclaircie invalide la mémoïsation, qui
    est CONSERVÉE (règle projet : ne jamais recalculer dans un tick ce qui l'a déjà
    été). L'intensité est calculée une fois par secteur, jamais par plot.
  - **Mesuré** — abattage du bord nord (charme, densité 0.8 → 0.1) : `eco.lisiere` aux
    3 premières rangées **0.826 → 0.308 · 0.716 → 0.267 · 0.606 → 0.226** (−63 %), le
    gradient reste un gradient, **rien ne bouge loin du bord**, et après 30 ans de
    repousse le corridor est **revenu exactement à 0.826** (rien n'est épuisable, #4).
  - **Neutralité intacte** : sans ceinture, `eco.lisiere` reste `None` ⇒ le terme est
    sauté dans `PopulationField.tick` ⇒ capacité de charge **bit-identique**.
  - Conséquence de calibrage : la valeur du ③ « `lisiere` moyenne T0 0.625 » n'est plus
    la référence (une forêt à densité 0.83 rayonne 0.906, non 1.00).
- **Tests** : **nouveau fichier `tests/test_peripherie_gestes.py`** (326 LDC, 🟡 vigilance — responsabilité unique : les tests du ④) —
  **76/76 OK**. Écart au kickoff (« étendre `test_peripherie.py` ») **assumé et motivé** :
  ce fichier était déjà à 415 LDC 🔴 et ④+⑤ l'auraient poussé vers 550 ; « un fichier par
  tronçon » est exactement la scission que le ③ renvoyait au `/refactor` de fin de sprint
  — faite d'emblée plutôt que payée deux fois. Sept suites : L golden neutre (200 ticks
  sur ceinture non coupée = **zéro dérive**), M gating (« refuser sans rien coûter » :
  aucune Vigueur débitée, secteur intact, ledger muet), N rejet de souche, O cinétiques
  (l'asymétrie), P matière, Q bornes + invalidation des caches, **R corridor** (la coupe
  fait baisser `eco.lisiere`, la mémoïsation ne le fige pas, la repousse le ramène).
- **Golden INCHANGÉ** : `57c166d8d3626444e0fc9b88b360edc62c047927f7608c45fefae35a6bba08da`.
  `tests/test_peripherie.py` (①②③) toujours **71/71** — les assertions de la suite K
  sont RELATIVES, la modulation par la densité ne les touche pas. Suite complète relancée
  (63 fichiers hors golden/500ans/périphérie) : **1 seul rouge**, `test_sim_server`
  269/270 (« le pommier pré-âgé a noué des fruits réels » → 0 fruits @ S52) — échec
  **PRÉ-EXISTANT** déjà consigné au ③. Tout le reste vert, dont `test_vent`,
  `test_stress_chronique`, `test_structures`, `test_substrat`, `test_ruissellement`,
  `test_marais`, `test_deblocage`, `test_vigueur`, `test_maitrise*`, `test_carnet`,
  `test_quetes`. **Aucun C# touché** (la vue est le tronçon ⑦) → pas de build à faire.
- **Régression corrigée** : `tests/test_acquisition_outils.py` assertionnait
  `offre_outils == ["secateur"]` (snapshot figé du registre D82). Remplacé par
  l'INVARIANT (« le sécateur y est » + « l'offre = les outils marqués `offre` ») → 16/16.
  Le registre grandira encore.
- **Échec PRÉ-EXISTANT aggravé, attendu** : `test_encyclopedie` était à 64/68 (5 gestes +
  1 technique sans fiche). Il l'est toujours à 64/68 — **les mêmes 4 vérifications**,
  vérifiées identiques sur l'arbre propre (`git stash`) — mais ses listes de « muettes »
  s'allongent de `abattre`/`receper`/`eteter` et `essartage`/`taillis`/`trogne`/`hache`/
  `serpe`. **C'est exactement le périmètre du ⑥** (`geste_corpus`/`technique_corpus`/
  `outil_corpus`), pas un bug de ④.
- **Fumée d'intégration** : monde du golden + `ceinture = generer_ceinture(7)` (forêts N
  19,8 m / E 15,9 m en aulne, rivières S+O) + joueur outillé × 60 semaines → aucun crash ;
  `abattre` nord dépose **26,3** de litière `bois` sur T0, décomposée à **11,7** en 55
  semaines (le circuit décompo la reprend) ; secteur nord à 1,06 an : densité 0.126,
  hauteur 70 cm, souche `morte`, cinétique `abattre` toujours en cours.

**⚠️ À valider par Nico (calibrage/design, pas bugs)** :
1. **`BOIS_COUPE_PAR_CM = 0.002`** — raser une forêt de 20 m de front à densité 0.83 rend
   ~26 unités de `bois` sur une tuile de 6×8. Placeholder ; se juge au F5 (est-ce qu'on
   croule sous le bois, ou est-ce dérisoire ?).
2. **`TRES_ELEVE = 60.0`** — nouveau palier. Sur `MAX_BASE = 100`, abattre est faisable
   une fois par recharge : cher, jamais impossible. À arbitrer si le barème doit rester à
   4 paliers.
3. **`LISIERE_SOCLE = 0.25`** — part de l'effet de lisière qui survit à une coupe rase
   (litière, bois mort, ourlet herbacé qui monte dans la lumière neuve). Placeholder
   écologique ; il fixe aussi de combien le corridor tombe (mesuré : −63 %).
4. **Le ledger n'est encore lu par personne** : la ligne `🪓` traverse `journal.consigner`
   mais aucun `Evenement` typé n'en sort tant que le ⑥ n'a pas ajouté son motif au
   parseur. Attendu, pas oublié.

### ⑤ Eau, roche & érosion — ✅ CLOS le 2026-07-26

Les gestes du **milieu pur** (philo #1 dans sa forme la plus nette : aucun être vivant
touché) et leur conséquence la plus lisible. **Aucun système neuf, aucun champ neuf** :
tout se greffe sur `tick_berge` (③), l'hydrologie (D30/hydrologie), `structure_sol`,
`om_stable`, `OUTILS`/`GESTE_UNLOCK` et le canal `log` du ledger.

- **`fields/peripherie.py`** (196 → **262 LDC**, 🟢) — nouvelle section §EAU & ROCHE, à
  côté de §SYLVICULTURE, même contrat : mutations **PURES** (zéro RNG, zéro coût, zéro
  champ écologique touché). `porte_eau`, `deplacer_ligne_eau(secteur, sens)`,
  `creuser_secteur(secteur)`, `entailler_secteur(secteur)`, `tick_ouvrages(ceinture)`,
  `erosion_secteur(secteur)`. Constantes : `LIGNE_EAU_PAS_CM = 30`,
  `LIGNE_EAU_BORNES = (−150, +120)`, `MARE_LIGNE_EAU_CM = 20`, `ENTAILLE_PAS_CM = 150`,
  `OUVRAGE_RUPTURE_ANS = 8`, `EROSION_DENUDATION_MIN = 0.25`,
  `ENTAILLE_REFERENCE_CM = 2 × ENTAILLE_PAS_CM`, `MARQUEUR_RUPTURE = 🚧`.
- **5 champs de secteur ajoutés** à `secteur_neutre()` : `ouvrage` (`None`/`endiguer`/
  `deriver`), `annees_depuis_ouvrage`, `ligne_eau_naturelle`, `entaille_cm`,
  `erosion_signalee`.
- **La distinction FORME / ARTEFACT est le cœur du tronçon, et elle tient en deux
  lignes de code** : `ligne_eau_naturelle` est mémorisée **au premier ouvrage
  seulement** ; `creuser` relève `ligne_eau` **ET** `ligne_eau_naturelle` (une
  excavation est une forme donnée au terrain, comme le `creuser` de plot qui baisse
  `altitude` définitivement), `endiguer`/`deriver` ne relèvent que `ligne_eau`.
  Conséquence **émergente** : un barrage rompt et rend l'eau à la mare creusée avant
  lui, jamais à zéro. Refaire le geste = **entretien** (horloge à zéro, référence
  naturelle NON réécrite) — mesuré : entretenu tous les 3 ans, un ouvrage tient 12 ans.
- **Mare = le verbe `creuser` EXISTANT sur une autre CIBLE** (kickoff §A respecté à la
  lettre) : `sim/actions/paysage.creuser_peripherie` lit `COUTS["creuser"]`,
  `OBJETS_TOUCHES["creuser"]` et `est_debloque(..., "creuser")`. **Aucune** entrée neuve
  dans `COUTS`/`GESTE_UNLOCK`/l'encyclopédie — pas de `creuser_mare` en doublon.
  Refusé sur une falaise (on ne creuse pas la roche à la bêche).
- **`tick_berge` généralisé** (`fields/ecofields/bordure.py`) : le critère devient la
  **ligne d'eau non nulle**, plus le `type == "riviere"`. Sans ça une mare creusée dans
  une prairie de bordure aurait été **muette**. Le générateur ne pose `ligne_eau` que
  sur les `riviere` ⇒ toute ceinture générée se comporte **bit pour bit** comme au ③
  (les 71 checks du ③ le confirment, dont l'assertion « `ligne_eau` parasite »).
- **`entailler` est le seul geste irréversible du jeu**, et c'est écrit dans les
  données : `entaille_cm` ne décroît jamais, `CINETIQUES` n'a **aucune** entrée de
  falaise, et `tick_repousse` ne boucle que sur `geste_coupe` — qu'`entailler` ne pose
  pas. Vérifié sur **10 000 ticks** (~190 ans) : `altitude_relative` ne remonte pas d'un
  cm. Deux conséquences déjà supportées : l'ombre portée diminue (② relit
  `altitude_relative` via `_hauteur_occultante`, une falaise rasée n'occulte plus rien)
  et la roche mise à nu part en érosion **indéfiniment**.
- **Érosion** (`bordure.tick_erosion`, `fields/ecofields/bordure.py` 57 → **81 LDC**,
  🟢) : intensité fournie par `erosion_secteur` (état du secteur SEUL), deux sources
  combinées par **MAXIMUM** — la **dénudation** d'une coupe (`1 − densité/densite_avant`)
  et la **cicatrice** d'une falaise entaillée. Deux écritures sur des champs existants,
  sur **3 plots** (`EROSION_PORTEE_CM = 150`) avec décroissance : `structure_sol −`
  (grumeaux enfouis sous du minéral) et `om_stable −` (humus dilué). Ce n'est pas un
  malus mais un **flux de matière** : infiltration ↓, asphyxie ↑, uptake ↓ émergent des
  lecteurs existants (philo #2).
  - **Trois émergences gratuites, aucune ligne pour les produire** : l'`eteter`
    **n'érode pas** (densité conservée ⇒ dénudation nulle — la trogne est fréquentable
    jusque dans le sol) ; une **éclaircie légère** non plus (seuil de dénudation 0.25 —
    il faut vraiment ouvrir le couvert) ; et l'érosion **CESSE d'elle-même** quand
    `tick_repousse` ramène la densité, sans qu'aucune ligne ne le dise (philo #6).
    Mesuré : coupe rase du bord nord ⇒ intensité 0.833, `structure_sol` du bord
    0.700 → 0.575 en 60 semaines (gradient 0.575 < 0.625 < 0.675, **plots centraux
    bit-identiques**) ; après 30 ans de repousse, intensité **0.000** et plus rien ne se
    dépose. Une falaise entaillée, elle, érode **toujours** à 50 ans.
  - **Signe diégétique `🪨`** émis **UNE fois par ÉPISODE** (verrou `erosion_signalee`
    sur le secteur, ré-armé quand le sol cesse de partir) = l'événement « 1ᵉʳ éboulis »
    de la conception §7. Sans ce verrou une cicatrice de falaise (permanente) noierait
    le carnet d'une ligne hebdomadaire. Une tuile hors portée ne déclenche **aucun**
    signe (drapeau `touche`).
- **⚠️ Écart ASSUMÉ au kickoff — le signe d'érosion n'est PAS dans `sim/semiologie.py`.**
  Le kickoff écrit « Registre `sim/semiologie.py` ». Or ce module est la **sémiologie
  FOLIAIRE** : signature `(plant, eco, saison) -> float`, et son invariant §2.4 est que
  chaque détecteur **réutilise le seuil même de la mécanique qui blesse le tissu**. Une
  érosion ne blesse aucune feuille, et il n'existe **aucun champ par plot** d'où la
  détecter (le kickoff interdit d'en créer un) : un détecteur foliaire aurait été un
  signe qui **ment sur sa cause**. Le signe est donc rendu par le canal **déjà utilisé
  pour les signes du MILIEU** — un marqueur de log par tuile, patron exact de
  `tick_rosee` (💧/❄) et du transport éolien (🍂), consommé par `journal.consigner`.
  Aucun chiffre en HUD (philo #5), aucun indicateur d'impact cumulé (D-3).
- **Outils / déblocage** : `entailler ← ("action","posseder_pioche")` (la pioche
  attendait depuis le ④ dans `OUTILS`, sans entrée `GESTE_UNLOCK` — elle en a une).
  `endiguer`/`deriver` sont à la **bêche**, qui n'a **pas** de marqueur d'outil (les
  gestes de bêche sont de BASE, cf. `creuser`/`drainer`) → ouverts sur l'**expérience** :
  `("action","creuser")`, idiome exact d'`eteter ← receper`. Effet de bord voulu :
  `creuser` entre dans `DECLENCHEURS` **par simple dérivation** ⇒ `tools/simserver/
  actions.py` le marque déjà, **rien à câbler côté pont**.
- **Coûts** : `endiguer`/`deriver` = `ELEVE`, `entailler` = `TRES_ELEVE` (palier créé au
  ④). `OBJETS_TOUCHES` **REMPLOIE la technique `terrassement`** de `creuser`/`drainer`
  (+ outil bêche / pioche) : inventer deux techniques de plus obligerait le ⑥ à leur
  écrire des voix que la conception §7 ne demande pas.
- **`sim/actions/paysage.py`** (68 → **131 LDC**, 🟢 — pas de 3ᵉ module, consigne du
  §REPRISE respectée) : `endiguer`/`deriver`/`entailler`/`creuser_peripherie`, patron du
  ④ (gate `est_debloque` → **portes métier** → `_payer` tout-ou-rien → mutation →
  `_consigner_terre` ⛏). « Refuser sans rien coûter » vérifié sur **7 portes**.
  Marqueur `⛏` distinct de `🪓` (④), `🚧` (rupture) et `🪨` (éboulis).
- **Câblage `sim/engine/boucle.py`** : `tick_ouvrages` en **1c-bis** (à côté de
  `tick_repousse`, O(4), une fois par monde, AVANT que `tick_berge` ne lise la ligne
  d'eau) ; `tick_erosion` en **2e-bis** (après `tick_berge`, **avant** l'hydrologie qui
  lit `structure_sol` pour l'infiltration ⇒ la conséquence est immédiate). Les deux
  renvoient leurs marqueurs (`log += …`, patron `tick_light`/`tick_rosee`).
  **No-op strict** sans ceinture, sans ouvrage et sans secteur dénudé.
- **Tests** : **nouveau fichier `tests/test_peripherie_eau_roche.py`** (324 LDC, 🟡
  vigilance — responsabilité unique : les tests du ⑤) — **59/59 OK**. Même écart assumé
  qu'au ④ (le kickoff dit « étendre `test_peripherie.py` », déjà à 415 LDC 🔴) : un
  fichier par tronçon. Six suites, une par point du kickoff — S gating (7 portes,
  Vigueur intacte, ledger muet), T déplacement (marécage ÉMERGENT après endiguement,
  bord asséché après dérivation, bornes), U rupture (8 ans, retour à la valeur
  **naturelle**, ledger, entretien, la mare qui survit, no-op 500 ticks), V
  irréversibilité (10 000 ticks, ombre, rasage borné), W érosion (gradient, centre
  intact, étêtage/éclaircie muets, repousse qui arrête, falaise permanente, signe unique,
  tuile hors portée), X neutralité (champs bit-identiques, ceinture neutre inerte,
  lumière identique).
- **Golden INCHANGÉ** : `57c166d8d3626444e0fc9b88b360edc62c047927f7608c45fefae35a6bba08da`.
  `test_peripherie` (①②③) **71/71**, `test_peripherie_gestes` (④) **76/76**. Suite
  complète relancée (**72 fichiers verts** hors golden/500ans) : **2 rouges, tous deux
  PRÉ-EXISTANTS** — `test_encyclopedie` 64/68 (périmètre ⑥) et `test_sim_server` 269/270
  (« le pommier pré-âgé a noué des fruits réels » → 0 fruits @ S52), vérifiés identiques
  sur l'arbre propre (`git stash -u`). **Aucun C# touché** (la vue est le ⑦) → pas de
  build.
  - ⚠️ *Note de flakiness observée* : sous charge machine, `test_sim_server` peut aussi
    faire tomber « snapshot == état du dernier step » (268/270). C'est le bloc `perf`
    (`ms_tick`/`rss_mo`) que `harness._scrub` neutralise pour la comparaison de
    déterminisme **mais pas** pour cette égalité-là. **Sans rapport avec ⑤** (reproduit
    à vide), à verser en dette si ça gêne.
- **Fumée d'intégration** : monde du golden + `House` + `ceinture = generer_ceinture(3)`
  (forêts N/E, **falaise S 827 cm**, rivière O à −71) + joueur outillé (pioche, hache,
  `creuser` réalisé) → les 8 gestes applicables passent, 60 semaines sans crash ; le
  marqueur `🪨` sort au bord nord après l'abattage, `structure_sol` moyenne 0.6986 →
  0.7120 (l'érosion est **locale** aux 3 rangées, la bioturbation domine ailleurs — le
  sol vivant contre-attaque, philo #4), marécage au bord après la mare.

**⚠️ À valider par Nico (calibrage/design, pas bugs)** :
1. **`LIGNE_EAU_PAS_CM = 30` sur des bornes (−150, +120)** — gorger une berge demande
   ~2-3 endiguements, l'assécher autant. Placeholder : se juge au F5 du ⑦ (est-ce qu'un
   barrage se sent en 1 geste ou en 5 ?).
2. **`OUVRAGE_RUPTURE_ANS = 8`** — à 60 s/semaine, 8 ans ≈ 7 h de jeu. Assez long pour
   qu'on oublie l'ouvrage, assez court pour que la leçon arrive dans une partie.
3. **`EROSION_STRUCTURE = 0.003` / `EROSION_HUMUS = 0.0006`** (`fields/ecofields/
   constants.py`) — calés du même ORDRE que la battance de pluie sur sol nu
   (`BATTANCE × STRUCT_INERTIA ≈ 0.0075`). Mesuré : −0.125 de `structure_sol` au bord en
   60 semaines à intensité 0.833. Est-ce que ça se voit assez, ou trop ?
4. **`EROSION_DENUDATION_MIN = 0.25`** — en-dessous, une éclaircie n'érode pas. C'est ce
   seuil qui décide si « couper un peu » est gratuit ou non.
5. **`ENTAILLE_PAS_CM = 150`** ⇒ raser une falaise de 8 m demande 6 coups de pioche à
   60 de Vigueur chacun. Volontairement lourd (irréversible), à arbitrer.
6. **`endiguer`/`deriver` ouverts par `("action","creuser")`** — décision de gating prise
   en aval (la bêche n'a pas de marqueur d'outil). Si Nico préfère un marqueur `bêche` à
   l'Atelier, c'est 1 entrée dans `OUTILS` + 2 conditions à réécrire.

### ⑥ Voix narratives — ✅ CLOS le 2026-07-26

Aucune écologie : de la DONNÉE éditoriale, une table de classification, un PARSEUR.
Le tronçon **referme ce que ④ et ⑤ avaient ouvert** — `test_encyclopedie` repasse de
**64/68 à 68/68** (il était rouge AVANT le sprint : c'était le compteur du ⑥).

- **Le SAULE au catalogue** (décision D-5, règle « le catalogue grandit avec les idées »
  signalée) : `plants/perennials.Willow` (`plants/perennials.py` 324 → **355 LDC**, 🟡
  vigilance — responsabilité unique : les pérennes ligneuses) + `plants/catalogue.py`
  (`"saule"`). *Salix alba*, **Salicaceae** (famille NEUVE déclarée à l'espèce, patron
  `FirTree`/`BirchTree`). Rien d'inventé côté moteur : ses trois signatures étaient
  **déjà** référencées par la chaîne du sprint comme des CHAÎNES sans espèce —
  `ESSENCES_QUI_REJETTENT` (rejet de souche), `ESSENCES_RIPISYLVE` (hélophyte,
  `asphyxie_tolerance_base = 3.0` comme l'aulne), `bouturable` (bouture spontanée →
  croise l'événement rare et le canal d'acquisition #2). Quatrième trait **gratuit** :
  `bloom_forcing_gdd = 4.0` ⇒ il fleurit AVANT de feuiller, en chatons
  **entomophiles** (`pollination_mode="insect"`, ≠ aulne/bouleau anémophiles) = la
  PREMIÈRE table des butineurs de l'année. Port PLEUREUR par `gravitropism_gain = 1.4`
  — le levier que le bouleau avait ouvert « pour préparer le saule ».
- **Ses CINQ voix** (règle « toute plante ajoutée = toutes ses voix ») :
  encyclopédie (`encyclopedie_corpus.FICHES["saule"]`, 3 niveaux ; N1 = la seule
  silhouette, le rejet de souche n'apparaît qu'au N2 et la trogne au N3 — philo #6) ·
  carnet (concept `rejet_de_souche`, vérifié bout-en-bout : une ligne de log de
  recépage produit une note qui NOMME le saule) · pages secrètes (**P42** « La dame
  blanche du saule creux ») · magazine (fiche produit + offre effective, dérivées —
  **zéro ligne** dans `magazine.py`, tout vient du catalogue) · ledger (le fait de
  coupe entre au journal avec `kind`/`cause`/`espece`).
- **Classification corrigée** (`sim/encyclopedie_types.py`) : `TECHNIQUES` gagne
  `terrassement` (⚠️ **PRÉ-EXISTANT** : la technique de `creuser`/`drainer` tombait
  dans `OUTILS` par défaut et se voyait réclamer une fiche d'objet) + `essartage`,
  `taillis`, `trogne`. C'était la cause des 7 « outils muets » du test.
- **Corpus des voix du geste** (D60), tous à 3 niveaux, voix « naturaliste » :
  - `geste_corpus.py` (233 → **321 LDC**, 🟡) : les **6 gestes du sprint** (`abattre`,
    `receper`, `eteter`, `endiguer`, `deriver`, `entailler`) + `creuser`/`drainer`
    (⑤ étend `creuser` à la mare de bordure et son kickoff §A affirmait qu'il avait
    « déjà sa fiche » — il n'en avait AUCUNE) ;
  - `technique_corpus.py` (123 → 155) : `essartage` · `taillis` · `trogne` ·
    `terrassement` ;
  - `outil_corpus.py` (145 → 169) : `hache` · `serpe` · `pioche` (N3 = « quand s'en
    passer », patron du sécateur).
  - **⚠️ Extension de périmètre ASSUMÉE et signalée** : 3 gestes **hors sprint** étaient
    muets depuis leur propre sprint (`pincer`, `arracher`, `glaner`) et bloquaient
    l'invariant « tout objet classé a une source de fiche », qui est TOUT-OU-RIEN. Leurs
    fiches sont écrites pour rendre la suite verte (68/68) — pure donnée éditoriale,
    zéro mécanique. À relire côté éditorial ; annulables sans rien casser d'autre que
    le compteur du test.
- **Le ledger a enfin ses lecteurs** — `sim/evenements.py` (141 → **166 LDC**) reconnaît
  les **quatre marqueurs** que ④ et ⑤ émettaient dans le vide : `🪓` coupe · `⛏`
  eau/roche · `🚧` rupture d'ouvrage · `🪨` éboulis. Trois points de conception :
  1. ils sont testés **AVANT** le filtre `@(r, c)` (patron des marqueurs de tuile
     `🐛`/`💧`/`❄`/`🍃`) — ce sont des faits de **secteur**, sans position ; sans ça la
     ligne était silencieusement ignorée ;
  2. `cause` = le **VERBE** (retraduit du libellé lisible), `espece` = l'**ESSENCE**
     coupée quand le catalogue la connaît (bord sans essence → `None`, gracieux) ;
  3. les deux tables de libellés sont des **MIROIRS** de `paysage.LIBELLE_GESTE` /
     `LIBELLE_TERRE`, **non importées** (le parseur reste pur : `sim.actions` tirerait
     tout le paquet des gestes dans son graphe d'import) — l'exactitude du miroir est
     **vérifiée par test**, pas par la discipline.
  L'API HISTORIQUE `_evenements` (détection de maîtrise D12) reste **aveugle** à ces
  lignes (aucun `@pos`) ⇒ zéro régression, prouvé en test.
- **Carnet** (`sim/carnet.py` 159 → **188 LDC**) : 9 entrées `CONCEPT_DE` + 18 gabarits.
  Les 4 concepts NEUFS du kickoff sont attribués sur ce que le geste **ENSEIGNE** :
  `abattre → brise_vent` (ce qu'on perd d'abord, c'est l'écran ; la rafale décroche),
  `receper → rejet_de_souche` (la souche vit ou meurt), `eteter → lisiere` (la seule
  coupe qui prélève **sans défaire** la lisière — densité conservée), `entailler` +
  éboulis `→ erosion`, eau/rupture `→ eau` (concept existant). Concepts **propres au
  carnet** (hors `encyclopedie_types.CONCEPTS`, comme `carnivorie`/`maladie`) : ils ne
  réclament donc aucune fiche d'encyclopédie, et **restent descriptifs tant qu'aucune
  route ne les crédite** (voir point 3 à valider).
  - **Correctif de lisibilité** : `_lieu((None,))` rendait « **sur None** » — un fait de
    ceinture n'appartient à aucune tuile. Il rend « au jardin ». Les gabarits de
    paysage n'emploient donc pas `{l}` (sauf l'éboulis, tenu par une tuile) et le côté
    du terrain reste lisible dans la ligne de log.
- **Pages secrètes** (`pages_corpus.py` 129 → **144 LDC**) : **P38→P42** — le bocage et
  le remembrement (« Le pays qu'on a rendu lisse »), l'essartage (« On n'ouvre pas un
  bois, on l'emprunte »), la trogne, le meunier et le droit d'eau, la chouette du saule
  creux. Voix C/E, lore PUR (zéro effet), patron du corpus existant.
- **Quêtes (§E) — le kickoff se trompait, et c'est signalé** : « ouvrir une clairière »
  et « rendre la mare aux libellules » ne sont **PAS** des objectifs déjà supportés —
  le mini-catalogue de conditions de `sim/quetes.py` est **FERMÉ** et toutes ses
  familles visent une **classe de plante** (`_classe_cible`), aucune ne lit la ceinture.
  Les écrire aurait demandé de toucher le moteur de quêtes (interdit). Livré à la place :
  **une** lettre (`lettre_saule_tetard`, voix épistolaire d'Odette) sur la famille
  EXISTANTE `nombre_vivant_min` — elle pose un désir, jamais le geste (philo #6).
- **Tests** : **nouveau `tests/test_peripherie_voix.py`** (212 LDC, 🟢) — **91/91 OK**.
  Cinq suites : Y les 5 voix du saule (dont 2 bout-en-bout, log → ledger → carnet),
  Z fiches + onglet de chaque geste/technique/outil du ④/⑤ (+ deux gardes **philo #6** :
  « le hêtre ne rejette pas » n'apparaît qu'au N3, pas de doublon `creuser_mare`),
  AA parseur (4 marqueurs, miroirs des libellés, essence absente gracieuse, API
  historique aveugle), AB carnet (9 concepts, 18 gabarits, notes lisibles sans slot
  vide ni « None », bascule descriptif→interprétatif), AC neutralité (parseur pur,
  carnet sans joueur ⇒ aucune clé, saule **hors** archétypes de succession).
- **Deux tests recalibrés d'un SNAPSHOT vers un INVARIANT** (patron du ④ sur
  `test_acquisition_outils`) : `test_encyclopedie` « corpus = 47 fiches » → **48**
  (l'alignement corpus ⟷ catalogue, lui, était déjà l'invariant) et `test_pages`
  passe de « 37 pages / ids P01..P37 » figés à **plancher + contiguïté** dérivés de
  `len(PAGES)` ⇒ un futur sprint qui ajoute une page ne le rendra plus rouge.
- **Golden INCHANGÉ** : `57c166d8d3626444e0fc9b88b360edc62c047927f7608c45fefae35a6bba08da`.
  Le saule n'est semé nulle part (`build_world` n'en connaît rien, il n'est pas un
  archétype de `WEED_CATALOGUE`) et aucun registre n'est parcouru dans le tick.
  **Aucun C# touché** (la vue est le ⑦) → pas de build.
  Suite complète relancée (**74 fichiers hors golden/500ans**) : **1 seul rouge**,
  `test_sim_server` 269/270 (« le pommier pré-âgé a noué des fruits réels » → 0 fruits
  @ S52) — échec **PRÉ-EXISTANT**, déjà consigné aux ③④⑤, message identique. Tout le
  reste vert, dont `test_encyclopedie` **68/68**, `test_pages` 69/69, `test_carnet`,
  `test_journal`, `test_evenements`, `test_maitrise_detection` (l'API historique du
  parseur est intacte), `test_magazine`, `test_quetes`, `test_palette`,
  `test_progression_geste`, `test_deblocage`, `test_catalogue_lot2/mulch`,
  `test_diversite_fondatrice`, et les trois suites de périphérie (71/71 · 76/76 · 59/59).

**⚠️ À valider par Nico (design/éditorial, pas bugs)** :
1. **Attribution des 4 concepts de carnet** — `eteter → lisiere` est le choix le moins
   évident (il n'y a pas d'événement « corridor » à gater, et la trogne est la seule
   coupe qui laisse la lisière intacte). `abattre → brise_vent` fait porter au geste la
   leçon centrale T1. Si Nico préfère un autre découpage, c'est 3 lignes.
2. **Le saule n'est pas calibré à la sonde** (`growth_speed`, `gravitropism_gain`,
   `age_curve`) : il n'est semé ni au golden ni à un banc, donc rien ne l'exerce. Les
   valeurs sont un décalque de l'aulne poussé d'un cran → **à voir au F5** le jour où
   le joueur en plante un (la lettre d'Odette rend ce cas possible).
3. **Les 4 concepts neufs restent descriptifs pour toujours** tant qu'aucune route ne
   les crédite : `maitrise_detection` ne crédite que les transitions de plante
   (avance/stagne/repro), et rien ne crédite `brise_vent`/`lisiere`/`erosion`/
   `rejet_de_souche`. C'est **cohérent avec le précédent** `carnivorie`/`maladie`
   (même situation depuis leur sprint), mais ça veut dire que la moitié
   interprétative du corpus est **écrite et jamais servie**. Route naturelle : un
   crédit de maîtrise sur le concept à la Nᵉ répétition du geste → hors périmètre ⑥,
   à verser en dette si Nico veut la voir.
4. **`sim/encyclopedie_corpus.py` est à 402 LDC** (🔴 de 2 lignes) après la fiche du
   saule. Sa propre docstring documente déjà la tolérance « corpus de texte, garde-fou
   pas dogme » ; candidat naturel au `/refactor` de fin de sprint (scission par règne
   ou par guilde), **pas** en rognant la prose.

## 6. §REPRISE

**Lire** : `CLAUDE.md` · ce fichier · `docs/champs/peripherie/conception_peripherie.md`
· le kickoff `0N` du tronçon en cours. Au besoin : `DETTE.md` D73/D92/D93/D94 ·
`visuals/DecorLayer.cs` · `fields/abri.py` · `fields/light.py` (`compute`, cache
`geom_key`) · `sim/actions/paysage.py` + `fields/peripherie.py` (§SYLVICULTURE) ·
`sim/outils.py` + `sim/actions/deblocage.py` ·
`fields/ecofields/{hydrologie,ruissellement,marais}.py` · `sim/actions/paillage.py`
(`mulch_stock`, `broyer`) · `sim/actions/compost.py` (`empiler_bois`) ·
`fields/ecofields/matiere_organique.py` (`deposer_litiere`).

**Prochaine étape** : tronçon **⑦** (`07_vue_godot.md`) — **DERNIER du sprint** : pont
0.5.41, `DecorLayer` qui CONSOMME le snapshot (il génère encore), clic secteur, banc F5.
Points d'appui posés par ①→⑥ :
- **côté voix, tout est câblé et n'attend que le pont** (⑥) : les 4 marqueurs de log
  (`🪓 ⛏ 🚧 🪨`) sont parsés en `Evenement` typés (`coupe`/`terrassement`/`rupture`/
  `eboulis`) et le carnet en rend une note ; les 6 gestes + 4 techniques + 3 outils ont
  leurs fiches d'encyclopédie à 3 niveaux ; le **saule** est au catalogue (`Salicaceae`,
  `plants/perennials.Willow`) avec ses 5 voix. ⇒ le ⑦ n'a **aucun corpus à écrire** :
  il expose les 7 gestes au pont et affiche des fiches qui existent déjà ;
- attention **la vue devra nommer les secteurs** : l'`Evenement` ne porte PAS le côté du
  terrain (pas de champ pour ça) — il n'est lisible que dans la ligne de log. Si le
  panneau Carnet doit dire « au bord nord », c'est au ⑦ de le décider (champ neuf dans
  `Evenement`, ou libellé côté vue) ;
- l'état de la ceinture vit dans `game_state["ceinture"]` (4 secteurs, lue par
  `boucle.py` aux étapes **1c** (repousse), **1c-bis** (ouvrages), 2, 2a, 2a-bis, 2e,
  **2e-bis** (érosion) et 14). Champs du secteur (schéma complet dans
  `fields/peripherie.secteur_neutre`) : `type`/`essence`/`hauteur_canopee`/
  `densite_ligneuse`/`souche_memory`/`annees_depuis_coupe`/`geste_coupe`/`densite_avant`/
  `hauteur_avant`/`ligne_eau`/`altitude_relative` + ⑤ `ouvrage`/`annees_depuis_ouvrage`/
  `ligne_eau_naturelle`/`entaille_cm`/`erosion_signalee` ;
- **le patron d'un geste de paysage est posé et exercé 7 fois** : `sim/actions/paysage.py`
  (couche joueur : gate `est_debloque` → portes métier → `spend`/`_payer` tout-ou-rien →
  mutation → matière → `_consigner` 🪓 / `_consigner_terre` ⛏) + `fields/peripherie.py`
  (mutations d'état PURES + cinétiques). Le fichier joueur est à **131 LDC** (🟢, marge) ;
- **le compteur du ⑥ est refermé** : `test_encyclopedie` est passé de **64/68 à
  68/68** (gestes/techniques/outils du sprint + `terrassement` reclassé technique),
  et les quatre marqueurs de log ont leur motif dans `sim/evenements.py`. Le
  **saule** est au catalogue avec ses 5 voix. Les concepts de carnet neufs
  (`brise_vent`/`rejet_de_souche`/`lisiere`/`erosion`) sont tabulés mais **rien ne
  les crédite encore** (cf. ⑥ point 3 à valider) ;
- **saule** (décision D-5, FAIT au ⑥) : `PERENNIAL_CATALOGUE["saule"] = Willow`
  (`Salicaceae`) rend enfin cohérentes les deux tables qui le citaient sans espèce —
  `ESSENCES_RIPISYLVE = ("aulne","saule")` et `ESSENCES_QUI_REJETTENT ⊇ {"saule"}`.
  Sa morphologie n'est PAS calibrée (personne ne le sème) → F5 ;
- **règles d'écriture des flux** (à respecter si le ⑥/⑦ touche un champ) :
  `fields/peripherie.plots_de_bord(...)` est le helper de TOUT effet de bord (graines,
  berge, lisière, bois, érosion — jamais un balayage de grille, réflexe D32), et **les
  CINQ flux répondent à une coupe** : lumière (`light.geom_key`), abri + turbulence
  (`abri._signature`), corridor (`_lisiere_sig` + `intensite_lisiere`) et érosion
  (recalculée à chaque tick, sans cache). Toute écriture neuve doit répondre à : **quel
  cache lit ce champ, et invalide-t-il sur MON écriture ?** ;
- **le pont n'expose AUCUN des 7 gestes de paysage** (ni ④ ni ⑤ n'ont touché
  `tools/simserver/actions.py`, volontairement) → c'est le périmètre du **⑦** avec la
  vue, `DecorLayer` et le clic secteur. À noter pour ⑦ : `eco.lisiere` et
  `eco.turbulence` ne sont pas exposés à `get_field` (pas d'overlay F6), et
  `erosion_signalee`/`entaille_cm` sont les deux champs qui donnent à la vue de quoi
  dessiner une cicatrice ;
- circuit du bois en place et exercé : `eco.deposer_litiere` (parcelle typée `bois`),
  `empiler_bois` (`sim/actions/compost.py`), `broyer` (`sim/actions/paillage.py`).
Aucun tronçon n'est autorisé à re-figer le golden ; si le digest bouge, c'est un bug.
Golden de référence courant : `57c166d8d3626444e0fc9b88b360edc62c047927f7608c45fefae35a6bba08da`.
