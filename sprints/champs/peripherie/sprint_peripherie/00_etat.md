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
> | ② | `02_exposition_abri.md` | lisière = obstacle lumière + abri, porosité/turbulence |
> | ③ | `03_graines_eau_corridor.md` | pluie de graines, nappe de berge, `eco.lisiere` |
> | ④ | `04_gestes_forestiers.md` | `abattre`/`receper`/`eteter`, outils, cinétiques, matière |
> | ⑤ | `05_eau_roche_erosion.md` | `endiguer`/`deriver`/`entailler`, mare, érosion |
> | ⑥ | `06_voix_narratives.md` | saule + 5 voix, gestes/techniques/outils, pages, événements |
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

## 6. §REPRISE

**Lire** : `CLAUDE.md` · ce fichier · `docs/champs/peripherie/conception_peripherie.md`
· le kickoff `0N` du tronçon en cours. Au besoin : `DETTE.md` D73/D92/D93/D94 ·
`visuals/DecorLayer.cs` · `fields/abri.py` · `fields/light.py` (`compute`, cache
`geom_key`) · `sim/outils.py` + `sim/actions/deblocage.py` ·
`fields/ecofields/{hydrologie,ruissellement,marais}.py` · `sim/actions/paillage.py`
(`mulch_stock`, `broyer`) · `sim/actions/compost.py` (`empiler_bois`) ·
`fields/ecofields/matiere_organique.py` (`deposer_litiere`).

**Prochaine étape** : tronçon **②** (`02_exposition_abri.md`) — la lisière devient un
obstacle de lumière + une entrée de `abri._obstacles()`. Il consommera
`fields/peripherie.py` (créé au ①) : lire `generer_ceinture`, `secteur_neutre`,
`PROFONDEUR_CM`, `voisins`. C'est ② qui décidera d'ajouter le ré-export dans
`fields/__init__.py`.
Aucun tronçon n'est autorisé à re-figer le golden ; si le digest bouge, c'est un bug.
Golden de référence courant : `57c166d8d3626444e0fc9b88b360edc62c047927f7608c45fefae35a6bba08da`.
