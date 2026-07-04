# Sprint « Luxuriance par stratification » (D65) — état vivant

> Carnet de bord de la `/conception` (skill `conception`, §0bis). Reconstructible
> à froid : lire `CLAUDE.md` + ce fichier suffit à reprendre. PHASE A (challenge)
> en cours — RIEN n'est figé tant que Nico n'a pas dit « OK ».

## Sujet
D65 « luxuriance par stratification / densification » — extrait de D64. Un plot
n'est pas limité à une plante : plusieurs strates coexistent (couvre-sol +
potagère + grimpante + traçante), la **compétition émerge de la densification**,
pas d'un conflit discret. Détail source : `CONCEPTION_USURE_LETALITE.md §6`.

## 4 briques D65 (toutes prioritaires Nico)
1. Densification clonale des couvre-sols/traçantes (stolons trèfle/fraisier/menthe).
2. Champ de couverture au sol par strate (« sol couvert à X % »), lu par écologie + rendu.
3. Empilement multi-strates VISIBLE (superposition / ordre de dessin).
4. Empreinte graphique propre à l'espèce — taille au sol ET silhouette.

## Fondations VÉRIFIÉES dans le code (ne pas réinventer)
- Strates par stade : `plants/base/empreintes.py::STRATE_DEFAULTS` (canopy_r/root_r/height/density)
  + `STRATE_SHADE_TOLERANCE`. Strates : sol/basse/moyenne/haute/grimpante.
- Co-occupation DÉJÀ permise : `world/tile.py::add_plant` ne teste pas l'occupation.
- Ombrage vertical asymétrique émergent : `fields/light.py` (seuls les voisins PLUS HAUTS ombrent).
- Empreinte au sol dérivée de la structure : `instance.update_footprint()` → `footprint{height,canopy_r,root_r}`.
- Conflit rendu NON-LÉTAL par D64① (co-occupation viable = blocage amont levé).
- Reproduction 100 % par graine (`sim/reproduction.py`) — AUCUN clonal existant.
- Évaporation modélisée (`fields` : `EVAPORATION`, `SOIL_RETENTION`) → hook couverture→humidité dispo.
- Catalogue : Trèfle (Clover) OUI ; Courgette OUI ; fraisier/menthe NON (prévus D62).

## COUPLAGE MAJEUR — D62
Brique 1 (clonal stolons/rhizomes) = frontalement **D62** (rampantes clonales,
🟡 non conçue : fraisier/menthe/framboisier/bambou + violettes, chacune 5 voix,
touche `reproduction.py`/`seedbank.py`). À trancher avec Nico : D65 absorbe D62 /
D65 sans clonal (renvoyé à D62) / clonal MINIMAL ici + espèces à D62. → Q1.

## Décisions ARRÊTÉES (Nico, lot 1 — 2026-07-04)
- **D1 — D65 ABSORBE D62.** Mécanique clonale complète + espèces (fraisier,
  menthe, framboisier, bambou traçant, violettes odorantes), chacune ses 5 voix.
  D62 sera fermée/fusionnée à la clôture. Sprint gros → 6 tronçons.
- **D2 — champ de couverture = 1 SCALAIRE par plot** (fraction couverte, strates
  sol+basse), scatter depuis les empreintes. Lu par 2 flux écolo (philo #2) :
  évaporation réduite + germination d'adventices supprimée. + 3ᵉ rôle interne :
  **gate d'établissement du clonal** (couverture saturée = pas de nouveau ramet)
  → auto-limitation émergente ET **cap perf** du nombre de plantes.
- **D3 — empreinte espèce = silhouette de rendu + override CIBLÉ.** Pas de
  nouveau champ écologique (canopy_r pilote déjà ombre+uptake). On ajoute un
  descripteur `silhouette` (data) + un override d'empreinte au sol seulement là
  où le défaut de strate ment (courge basse-mais-étalée). Overrides limités aux
  espèces HORS golden → neutre.
- **D4 — clonal = UNE mécanique paramétrée** (pas 3 chemins de code). `clonal_mode`
  ∈ {none, stolon, rhizome, drageon} module 3 axes : portée (radius), gate
  (stolon = besoin lumière sol / rhizome = tolère l'ombre, réserve / drageon =
  courte portée près de la mère), agressivité (intervalle). Ramet = COPIE
  génétique (pas de brassage), déterministe (hash), coût Vigueur sur la mère.

## Golden — re-figeages prévus
- **T1** (couverture→évaporation) : RE-FIGÉ maîtrisé (humidité dérive sur tout
  plot couvert). Le golden porte Clover sur tuile 2.
- **T2** (clonal sur trèfle du golden) : RE-FIGÉ maîtrisé (ramets de trèfle).
- T3/T4/T5 : NEUTRE (overrides + espèces hors scénario golden). T6 : INTACT.

## Coût perf (à surveiller)
LightField = déjà 53 % du CPU. Champ de couverture = 1 scatter (stamp empreinte,
réutilise `_plots_in_radius`), jamais un balayage. Le gate de couverture BORNE le
nombre de ramets → protège le LightField d'une explosion de plantes. Budget ≤ +10 %.

## Carte des tronçons (perf-first, golden discipliné)
1. Champ de couverture `couverture_sol` + hooks évaporation & adventices — RE-FIGÉ.
2. Mécanique clonale (ramets déterministes, gate couverture, coût Vigueur) — RE-FIGÉ.
3. Empreinte/silhouette par espèce (descripteur `silhouette` + override ciblé) — NEUTRE.
4. Catalogue clonal ①  : fraisier + menthe (+ trèfle stolonifère) + 5 voix — NEUTRE.
5. Catalogue clonal ② : framboisier + bambou traçant + violettes + 5 voix — NEUTRE.
6. Vue Godot : empilement multi-strates visible + couverture rendue + silhouettes
   + colonies clonales + pont + banc F5 `luxuriance` — INTACT.

## Avancement
- **T1 ✅ FAIT (2026-07-04)** — Champ `couverture_sol` + 2 hooks écologiques.
  - Champ scalaire `couverture_sol` ∈ [0,1] par plot (nouveau `GridField` dans
    `container.py`, exposé `get_field` → overlay F6), recalculé chaque tick par
    SCATTER dans le mixin neuf `fields/ecofields/couverture.py::CouvertureMixin.
    tick_couverture(plants, saison)` (stamp des empreintes des plantes de strate
    sol+basse, densité×canopée, écrêté [0,1] par le champ). Câblé dans
    `sim/engine/boucle.py` étape **2d**, AVANT hydrologie (3) et succession (13).
  - Hook (a) évaporation : `hydrologie.py` rapproche `evap` de 1.0 (rétention)
    ∝ couverture (`COUVERTURE_EVAP_FRAC=0.4`). Vérifié : per-tick, plot couvert
    RETIENT plus d'eau (1.4972 > 1.4954 sur banc isolé) — sens correct.
  - Hook (b) germination : `sim/succession.py` gate la germination FÉRALE (pas
    les grains plantés) si `couverture_sol ≥ COUVERTURE_ADVENTICE_SEUIL=0.6`.
  - Constantes dans `fields/ecofields/constants.py`.
  - **Golden RE-FIGÉ** (annoncé) : `15073be1…` → **`d26432d3c236543234b1176c0290ffbd7df3f2740488b8e7caea1704a6e95143`**.
    Raison : Clover (strate basse) sur tuiles paires du golden → couverture > 0 →
    évaporation modifiée + germination férale gatée → cascade humidité/population.
    Dérive LOCALISÉE et bornée (cov ∈ [0,1], cov_max ~0.8 ; humidité plausible
    0.01–1.0, aucune explosion ni effondrement). Suites ciblées vertes (golden +
    éco/hydro/succession du bloc rapide).
  - LDC (code pur) : couverture 20 / hydrologie 41 / succession 145 / container 244 — tous 🟢.
  - **Suite `test_population` RE-FIGÉE** (hash externe `population_hash.txt`) :
    `e7f1cf19…` → `5a1873db…`. Même cascade humidité→population que le golden
    (toutes les assertions COMPORTEMENTALES passent inchangées, seul le hash de
    déterminisme du champ densité glisse). `test_epaisseur_500ans` (test manuel
    long anti-emballement) NON relancé — jugé inutile par Nico pour ce tronçon.

- **T2 ✅ FAIT (2026-07-04)** — Mécanique clonale (ramets déterministes).
  - Traits sur `PlantBase` (`plants/base/familles.py`) : `clonal_mode ∈ {none,
    stolon, rhizome, drageon}` (défaut `none` = neutre) + `clonal_radius_cm` (60)
    + `clonal_interval` (4). UNE mécanique paramétrée (D4), pas 3 chemins.
  - Nouveau `sim/clonal.py::emettre_ramets(tile, eco, seed, week)` : pour chaque
    plante VIVANTE, MATURE, `clonal_mode != none`, dans sa fenêtre de cadence
    (porte hashée `week*41`) ET assez vigoureuse (`vigueur_plante ≥ SEUIL`) —
    tire un offset hashé (angle `week*31`, distance `sqrt(u)` `week*37`, ≤ radius),
    teste le GATE d'établissement (`_peut_etablir` : plot valide + `couverture_sol
    < COUVERTURE_SATURATION=0.85` + lumière au sol `≥ 0.30` pour stolon/drageon,
    rhizome exempté → envahissant émergent), et pose un ramet = clone (gènes +
    expression COPIÉS). Coût sur la MÈRE = bouffée `stress_memory += 0.06`
    (arbitrage émergent graines ↔ ramets). 1 ramet max/mère/tick. Zéro RNG live.
  - Câblé `sim/engine/boucle.py` étape **9e** (après croissance/vigueur/sénescence
    /floraison, `seed` déjà en scope). Clover → `clonal_mode="stolon"`.
  - **CALIBRAGE** : `CLONAL_VIGUEUR_SEUIL` posé à **0.02** (pas 0.08). La façade
    `vigueur_plante ≈ qi_local` sur un couvre-sol sain, et le qi_local d'un plot
    réel plafonne ~0.05 (le trèfle du golden ombragé par la maison culmine à
    ~0.048) → un seuil trop haut n'émettait JAMAIS (golden inchangé = bug de gate).
    0.02 laisse cloner une mère mature bien portante, coupe net une mère mourante
    (santé→0 annule la façade). **Point à valider F5 : la densité/vitesse de
    tapissage du trèfle.**
  - **Golden RE-FIGÉ** (annoncé) : `d26432d3…` → **`061934db09ad646a01f19b8f4d0b677f13438e87bce2f8531527be425e7c22a8`**.
    Raison : Clover (stolon, tuile 0) émet des ramets de trèfle → +2 plantes trèfle
    + `stress_memory` de la mère (∈ `_PLANT_ATTRS`) → cascade. Dérive BORNÉE et
    cohérente : colonie trèfle 1→3 sur le smoke (2 ans), aucune explosion (bound
    12 ans : trèfle culmine à 8 puis reflue à 0 par succession, total plantes
    stabilisé ~100-130, PAS de runaway — le gate couverture EST le cap). Suite
    complète **47/47 tests verts** (dont test_competition 14/14, test_senescence).
  - **`test_population` INCHANGÉ** (hash `5a1873db…` identique) : son scénario ne
    contient pas de clonale → non impacté. Pas de re-figeage.
  - LDC (code pur) : clonal 59 / familles 213 / boucle 244 = 🟢 ; cultivees 323
    🟡 (pré-existant, catalogue = une responsabilité, +5 lignes seulement).
  - C# NON concerné (T2 Python pur, aucun `dotnet build`).

- **T3 ✅ FAIT (2026-07-04)** — Empreinte/silhouette par espèce (NEUTRE).
  - **Descripteur `silhouette`** (pur data, AUCUN effet moteur) : nouveau champ de
    classe `silhouette: str | None = None` sur `PlantBase` (`plants/base/familles.py`)
    + classmethod `silhouette_base()` (patron `shade_tolerance_base`) : override
    explicite sinon dérivé de la strate du stade MATURE via la table neuve
    `STRATE_SILHOUETTE` (`plants/base/empreintes.py` : sol→tapis, basse→touffe,
    moyenne→touffe, haute→dressée, grimpante→dressée). Palette : touffe · rosette ·
    étalée · dressée · tapis · buisson. Lu par le renderer C# au **T6** (via pont),
    pas ici.
  - **Overrides silhouette CIBLÉS, tous HORS golden** (défaut de strate qui ment) :
    Courgette `"étalée"` (basse-mais-rampante), Carotte + Mâche + Pissenlit
    `"rosette"` (rosettes plaquées, défaut `touffe`), Myrtille `"buisson"`
    (sous-arbrisseau ligneux). Aucune espèce du golden touchée → défauts de strate
    (Clover→tapis, Sunflower→dressée, Tomato→touffe) inchangés.
  - **Override d'empreinte au sol (b)** : la courge portait DÉJÀ son empreinte
    élargie via ses stades (`canopy_radius=60` ≫ défaut basse=30) — l'override ciblé
    (b) est donc déjà en place ; T3 ne fait qu'y adjoindre la `silhouette="étalée"`
    documentée. Pas de nouveau champ écologique (D3 respecté : `canopy_r` pilote seul).
  - **Golden INCHANGÉ** (`061934db09ad646a01f19b8f4d0b677f13438e87bce2f8531527be425e7c22a8`)
    — tronçon NEUTRE confirmé. **`test_population` INCHANGÉ** (`5a1873db…`).
  - LDC (code pur) : familles 220 / empreintes 41 / potageres 146 / adventices 185
    / sauvages 70 — tous 🟢.
  - C# NON concerné (T3 Python pur ; le RENDU de la silhouette est T6).

- **T4 ✅ FAIT (2026-07-04)** — Catalogue clonal ① : fraisier + menthe + 5 voix (NEUTRE).
  - **2 espèces neuves** (le trèfle porte DÉJÀ `clonal_mode="stolon"` depuis T2 →
    « réglage stolonifère du trèfle » sans objet, rien à changer) :
    - **Fraisier** (`Strawberry`, Rosaceae) dans `plants/species/potageres.py` :
      vivace couvre-sol `clonal_mode="stolon"`, `clonal_radius_cm=45` (stolon court),
      `silhouette="rosette"`, `fruitier=True`, strate sol→basse, clé catalogue `fraisier`.
    - **Menthe** (`Mint`, Lamiaceae) dans `plants/species/aromatiques.py` : vivace
      `clonal_mode="rhizome"`, `clonal_radius_cm=90` + `clonal_interval=3` (porte loin,
      cadence rapide → envahissement ÉMERGENT via le gate rhizome qui ignore l'ombre),
      `silhouette="touffe"`, mellifère, clé catalogue `menthe`. Réutilise la mécanique
      clonale figée au T2 (`sim/clonal.py`) — AUCUNE modif du moteur clonal.
  - **Les 5 voix, chacune** :
    1. Encyclopédie ✅ — 2 fiches × 3 niveaux (`sim/encyclopedie_corpus.py`) ; count
       corpus 30→32 (test + docstrings mis à jour).
    2. Carnet ✅ — nouvel événement `ramet` mappé au concept `reproduction`
       (`CONCEPT_DE`) + 3 paires de gabarits PAR MODE (stolon doux / rhizome « à
       surveiller » / drageon) dans `sim/carnet.py`.
    3. Pages secrètes ✅ (optionnel, mais porté) — P25 « Le fraisier qui marche »
       (concept succession) + P26 « La menthe qu'on garde en cage » (compagnonnage)
       dans `sim/pages_corpus.py` ; count 24→26 (test + docstring).
    4. Magazine ✅ — automatique : l'offre dérive de `cls.family` + fiche produit lit
       `FICHES` → présence encyclo + famille suffit (Rosaceae/Lamiaceae déjà connues).
    5. Événements ✅ — marqueur `🌿 Ramet (mode) : nom @pos` (émis par `sim/clonal.py`
       depuis T2) désormais PARSÉ en `Evenement("ramet", …, cause=mode)` dans
       `sim/evenements.py` (regex `_RE_RAMET`). Test dédié `test_ramet_clonal`.
  - **Golden INCHANGÉ** (`061934db…`) — NEUTRE confirmé (ni fraisier ni menthe semés
    dans le scénario). **`test_population` INCHANGÉ** (`5a1873db…`).
  - Suites voix vertes+adaptées : encyclopedie 68/68, pages 53/53, evenements 20/20,
    carnet 19/19, magazine 23/23, catalogue_lot2 16/16. LDC 🟢 (potageres 196,
    aromatiques 114, carnet 148, evenements 134).
  - C# NON concerné (T4 Python pur ; rendu des silhouettes/colonies = T6).

- **T5 ✅ FAIT (2026-07-04)** — Catalogue clonal ② : framboisier + bambou traçant +
  violette odorante + 5 voix (NEUTRE).
  - **3 espèces neuves** dans `plants/species/sauvages.py` (spontanées non-archétypes,
    `archetype=None` → hors WEED_CATALOGUE) ; réutilisent la mécanique clonale figée
    au T2 (`sim/clonal.py`) — AUCUNE modif du moteur :
    - **Framboisier** (`Raspberry`, Rosaceae) — `clonal_mode="drageon"`, portée TRÈS
      courte (`clonal_radius_cm=40` → fourré resserré près de la mère), strate
      moyenne→haute, `silhouette="buisson"`, `fruitier=True`. Clé `framboisier`.
      Démonstrateur du DRAGEON.
    - **Bambou traçant** (`RunningBamboo`, Poaceae) — `clonal_mode="rhizome"`, portée
      LONGUE (`clonal_radius_cm=120`) + `clonal_interval=3` (rapide) + gate lumière
      IGNORÉ (rhizome) → envahissement EXTRÊME émergent, BORNÉ par le gate couverture
      (T1). Strate haute, `silhouette="dressée"`, evergreen, anémophile (hérite compét.
      hydrique Poaceae). Clé `bambou`. Démonstrateur extrême de l'envahissement.
    - **Violette odorante** (`SweetViolet`, **Violaceae — FAMILLE NEUVE**) — couvre-sol
      d'ombre `clonal_mode="stolon"` (portée 45), `shade_tolerance=1.6` (SCIAPHILE),
      strate sol, `silhouette="tapis"`, mellifère précoce. Clé `violette`. Nouvelle
      classe `Violaceae` (INERTE, `family_effects=[]`) dans `plants/base/familles.py`,
      exportée par `plants/base/__init__.py` + `plants/__init__.py`.
  - **Les 5 voix, chacune** :
    1. Encyclopédie ✅ — 3 fiches × 3 niveaux (`encyclopedie_corpus.py`) ; count corpus
       32→**35** (test + docstrings MAJ).
    2. Carnet ✅ — AUCUNE modif nécessaire : `CONCEPT_DE` + gabarits sont déjà
       mode-génériques (stolon/rhizome/drageon → concept `reproduction`) depuis T4.
    3. Pages secrètes ✅ — P27 « Le fourré qui avance » (succession, framboisier),
       P28 « La prison du bambou » (compagnonnage — PAS non-action, sinon casse
       l'invariant du test), P29 « La première table de l'année » (floraison,
       violette) ; count 26→**29** (test + docstring MAJ).
    4. Magazine ✅ — automatique (offre dérive de `cls.family` + `FICHES`) :
       Rosaceae/Poaceae déjà connues, Violaceae neuve suffit. AUCUNE modif.
    5. Événements ✅ — le marqueur `🌿 Ramet (mode)` est déjà parsé data-driven
       (`_CLE_DE_NOM` dérive du catalogue) → les 3 espèces sont reconnues sans modif.
  - **Golden INCHANGÉ** (`061934db09ad646a01f19b8f4d0b677f13438e87bce2f8531527be425e7c22a8`)
    — NEUTRE confirmé (aucune des 3 semée au golden). **`test_population` INCHANGÉ**
    (`5a1873db…`).
  - Suites vertes : golden, population, encyclopedie 68/68, pages **56/56**,
    evenements 20/20, carnet 19/19, magazine 23/23, catalogue_lot2 16/16 + **suite
    complète (tous les test_*.py hors test_epaisseur_500ans) verte** (`fail=0`).
  - LDC (code pur) : sauvages 191 / familles 225 / encyclopedie_corpus 298 (corpus
    data) / pages_corpus 105 — tous 🟢.
  - C# NON concerné (T5 Python pur ; rendu silhouettes/colonies = T6).

## §REPRISE
**T5 CLOS.** Prochain : **T6 = vue Godot** (INTACT — consommera `silhouette` +
colonies clonales + couverture via le pont ; empilement multi-strates visible + banc
F5 `luxuriance`). Conception FIGÉE
`docs/conception/CONCEPTION_LUXURIANCE_STRATIFICATION.md`. À la clôture du sprint :
fermer D62 (absorbée), MAJ DETTE/BACKLOG/journal/mémoire.
