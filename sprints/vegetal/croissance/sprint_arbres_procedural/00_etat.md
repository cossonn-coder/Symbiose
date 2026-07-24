# Sprint — Migration des 9 arbres en croissance procédurale (D91)

**Type/thème :** `vegetal/croissance` · **Statut :** CONCEPTION FIGÉE — prêt `/sprint-auto`
**Doc figé :** `docs/vegetal/croissance/conception_migration_arbres.md`
**Amont :** D90 (taper, CLOS) · D29 (croissance procédurale, doc mère
`docs/vegetal/croissance/conception_croissance.md`) · amorce rev 2 fournie par Nico.
**Golden : INCHANGÉ (`57c166d8…`) sur les 4 tronçons** (les 9 arbres sont hors
scénario golden ; les 2 nouveaux leviers ont un défaut neutre).

## Objectif
Faire passer les 9 arbres restants (Fig, Cherry, Walnut, Oak, Beech, Birch,
Hornbeam, Fir, Alder) de l'empreinte-couronne tabulée (`age_curve`) à la
**croissance procédurale en segments** (`procedural_growth=True`), comme le
pommier — pour qu'ils se dessinent en branches et portent le taper D90.

## FAITS ÉTABLIS PAR LECTURE DU CODE (corrigent l'amorce)

1. **GOLDEN STRICTEMENT NEUTRE pour tout D91.** `tests/test_golden.py` n'instancie
   parmi les ligneux QUE `AppleTree`. Les 9 arbres à migrer ne sont ni plantés ni
   tirés par la succession (`archetype=None` → hors `WEED_CATALOGUE`). → **aucun
   re-figeage sur aucun tronçon.** (L'amorce §3 hedgeait « conditionnel » ; la
   réalité est plus simple.) Reproduit le précédent des sprints ③④⑤ décompo
   (golden NEUTRE).

2. **`port_archetype` n'est JAMAIS lu par la sim** (grep vide dans `sim/`, `fields/`).
   C'est une étiquette descriptive. Le comportement `fleche`↔`etale` ÉMERGE de
   `apical_dominance_base` + `AUXIN_RELEASE_SCALE`. → « ajouter un 8ᵉ archétype
   pleureur » comme string **ne fait rien** : le pleureur exige un **levier
   mécanique neuf** (gravitropisme / poids sur `dir`). C'est le seul vrai trou de
   modèle (confirmé, mais reformulé).

3. **Le vrai risque n'est PAS le golden, c'est la MORT HYDRIQUE au F5.**
   `PROC_ROOT_RATIO=1.0` global : `root_r = canopy_r = max_horiz + foliage_halfwidth`.
   Le commentaire de calibrage du pommier (perennials.py:178-186) est explicite :
   une jeune flèche étroite → canopy_r minuscule → root_r minuscule → uptake
   concentré sur le plot-foyer → **mort par stress hydrique ~an 3**. Le pommier l'a
   résolu par `foliage_halfwidth=50`. **Chaque arbre migré doit régler
   `foliage_halfwidth`** pour survivre — invisible au golden, révélé au F5. Les
   espèces hautes-étroites (sapin, bouleau grêle) sont LES PLUS exposées.

4. **`AUXIN_RELEASE_SCALE=400 semaines` (~7,7 ans) est GLOBAL** et partagé avec le
   pommier (qui EST dans le golden). Un chêne/hêtre centenaire « s'étale »
   entièrement dès ~an 8. Retoucher cette constante toucherait le pommier/golden.
   → ontogénie centenaire = arbitrage (accepter la courbe partagée, OU lever par
   espèce = nouvel attribut, golden-safe car 9 arbres hors golden).

## DÉCISIONS ARRÊTÉES (Nico, lot 1)
- **D1 — Pleureur = nouveau levier gravitropique.** Attribut `gravitropism_gain`
  par espèce (défaut 0.0 = neutre → golden-safe). Greffe dans `_elongate_emit`
  APRÈS `_phototropic_bias` : `_gravitropic_droop(dir, depth, gain)` (helper neuf
  dans `geometrie.py`) biaise le `dir` émis vers le bas, **échelonné par la
  profondeur** (tronc/flèche restent dressés à faible depth ; seuls les rameaux
  distaux retombent) → Betula pendula : leader droit + brindilles pendantes.
  Déterministe (biais géométrique pur, zéro RNG). Bouleau > 0, tous les autres 0.
  Réutilisable saule (D23).
- **D2 — Relâchement d'auxine par espèce.** Nouvel attribut `auxin_release_scale`
  (défaut = 400.0 = la constante globale actuelle → pommier/Tomato/grimpantes
  inchangés, golden bit-identique). `_update_auxin(segs, dominance, release_scale)`
  lit désormais `cls.auxin_release_scale`. Ligneux longévifs (chêne, hêtre) →
  échelle PLUS GRANDE (dressé plus longtemps) ; pionniers (bouleau, aulne) → plus
  petite. Golden-safe (9 arbres hors golden).
- **D3 — Découpage 4 tronçons par famille de calibrage** (voir §DÉCOUPAGE).

## FAISABILITÉ VÉRIFIÉE (code)
- Levier D2 : `_update_auxin` (phases.py:29/35) lit la constante de module → passe
  en param `release_scale`, défaut 400 sur `PlantBase`. Trivial, golden-safe.
- Levier D1 : `_phototropic_bias` renvoie `new_dir` dans `_elongate_emit`
  (phases.py:78) → un blend gravitropique juste après. `depth` déjà calculé par
  `_depths` (dispo via geometrie).
- Multi-tronc figuier : structure initiale = UN `Segment(parent=None)`
  (instance.py:187). Vrai multi-tronc = émettre 2-3 segments basaux à l'init OU
  rejets basaux. `_elaguer` protège DÉJÀ tous les `parent=None`. → **scope T2 :
  figuier `buissonnant` mono-collet d'abord ; multi-tronc = OPTION F5 si le port
  lit mal** (amorce « moindre urgence »). Pas de sur-ingénierie (#2).

## DÉCOUPAGE (D3) — 4 tronçons, golden INTACT partout
- **T1 — feuillus etale + levier release_scale.** Moteur : `auxin_release_scale`
  par espèce (D2). Migre cerisier, charme, hêtre, noyer, chêne (patron pommier
  direct). Calibrage `foliage_halfwidth` (SURVIE hydrique) + gabarit sur `age_curve`.
- **T2 — cas atypiques.** Aulne (etale, rôle hydro D61 intact), figuier
  (`buissonnant` mono-collet), sapin (`fleche`, `deciduous=False` déjà, dominance
  haute + release_scale long). Aiguilles/verticille = notés pour T4 (rendu).
- **T3 — bouleau + levier gravitropique.** Moteur : `gravitropism_gain` (D1).
  Migre bouleau (`fleche` élancé + retombée distale). Prépare saule D23.
- **T4 — vue Godot + banc F5.** Vérifie les 9 ports en branches (`PlantRenderer`
  fait déjà les segments), mode aiguilles pour le sapin (`PlantRenderer.Organs.cs`),
  LOD, banc d'observation des 10 arbres. Golden intact.

## AVANCEMENT
- [x] **T1 — feuillus etale + levier `auxin_release_scale`** (2026-07-24).
  Moteur : attribut `auxin_release_scale` (défaut 400) sur `PlantBase`
  (`familles.py`) ; `_update_auxin` prend le param `release_scale` ; `grow_plant`
  passe `cls.auxin_release_scale` (pommier/Tomate/grimpantes = 400 → **appel
  bit-identique**). Défauts procéduraux d'arbre mutualisés sur `PerennialWoody`
  (emit 50 / max_seg 70 / wood 4000 / angle 70° / fhw 50 / etale / dom 2.0),
  `procedural_growth` NON flippé sur la base. 5 feuillus migrés (`procedural_growth
  =True`), calibrés à la sonde (520 ticks, an 10, monotones, bornés) :
  | espèce | gs | release_scale | foliage_hw | h10/cr10 (cible) |
  |---|---|---|---|---|
  | Cerisier | 1.20 | 600 | 140 | 504/276 (500/280) |
  | Charme | 1.20 | 600 | 100 | 504/236 (500/220) |
  | Hêtre | 0.95 | 500 | 140 | 398/262 (400/260) |
  | Noyer | 1.50 | 650 | 160 | 620/352 (600/350) |
  | Chêne | 0.95 | 500 | 185 | 398/307 (400/300) |
  **Décision imprévue** : le kickoff suggérait `auxin_release_scale` 900-1500 pour
  chêne/hêtre, mais un rs aussi haut → l'apex ne relâche jamais → **poteau nu** (0
  latéral, couronne = foliage_halfwidth) → contredit `etale` + « grand & large ».
  Résolu : rs modéré (500) pour ouvrir la couronne + **largeur portée par
  `foliage_halfwidth`** (double dividende : survie hydrique du jeune arbre à racines
  courtes). Valeurs = placeholders → F5 (T4). **Golden INCHANGÉ `57c166d8…`**.
  test_croissance : 102/102 (dont 2 tests D91 neufs). Suites connexes vertes
  (phototropisme, senescence, grimpe, confinement, lifecycle). C# non touché.
  Reste : T2 (aulne/figuier/sapin), T3 (bouleau+gravitropisme), T4 (vue Godot+banc).
- [x] **T2 — cas atypiques : aulne / figuier / sapin** (2026-07-24). 3 espèces
  migrées (`procedural_growth=True`), calibrées à la sonde (520 ticks, an 10,
  monotones, bornées, déterministes) :
  | espèce | port | gs | rs | dom | fhw | maxseg | h10/cr10 (cible) |
  |---|---|---|---|---|---|---|---|
  | Aulne | etale élancé | 1.65 | 800 | 2.0 | 50 | 70 | 680/233 (700/200) |
  | Figuier | buissonnant | 1.00 | 450 | 1.9 | 95 | **90** | 421/256 (400/250) |
  | Sapin | fleche conique | 0.95 | 700 | 2.8 | 110 | 70 | 398/130 (400/130) |
  **Décisions imprévues** : (1) **Aulne rs=800** (pas « petit » comme suggéré au
  kickoff) : à rs bas le leader s'étalait trop tôt, saturait le cap segments et la
  hauteur stagnait à ~200 (h700 est le PLUS grand jeune arbre → exige un leader tenu ;
  le « pionnier s'étale vite » se lit sur l'ampleur finale, pas à l'an 10). (2) **Figuier
  max_segments relevé 70→90** : un buissonnant ramifie légitimement plus qu'une flèche
  decurrent ; au défaut 70 le cap AMPUTAIT la charpente (couronne non monotone). Reste
  BORNÉ (79<90, run éternel OK). (3) **Sapin = cas le plus simple** : la flèche haute-
  dominance + release long donne cr≈fhw sans réglage laborieux ; fhw=110 tient à la fois
  cr130 étroit ET la survie hydrique (~2,2 plots). **Multi-tronc figuier = option F5
  différée** (mono-collet OK). **Golden INCHANGÉ `57c166d8…`**. test_croissance : 125/125
  (dont 4 tests T2 neufs : migration, déterminisme, sapin-fleche-étroit, aulne-rôle-hydro).
  Suites connexes vertes (marais, evergreen, lifecycle, senescence, phototropisme,
  confinement, mulch). Rôle D61 aulne (fixation N₂ Frankia + asphyxie 3.0) préservé
  (testé). C# non touché. **Note taille** : `perennials.py` = 316 LDC pur → zone vigilance
  (300-400), responsabilité unique (catalogue pérennes ligneuses) → signalé, pas scindé
  en plein sprint. Valeurs = placeholders → F5 (T4). Reste : T3 (bouleau+gravitropisme),
  T4 (vue Godot+banc).

- [x] **T3 — bouleau + levier `gravitropism_gain`** (2026-07-24). Moteur : attribut
  `gravitropism_gain` (défaut 0.0 = neutre) sur `PlantBase` (`familles.py`) ; helper neuf
  `_gravitropic_droop` (`geometrie.py`) ; greffe dans `_elongate_emit` (`phases.py`) APRÈS
  `_phototropic_bias`, passé via `grow_plant` (`cls.gravitropism_gain`). **Décision imprévue
  (trou de modèle révélé à la sonde)** : le kickoff/D1 échelonnaient la retombée par la
  PROFONDEUR topologique `depth`. Or la flèche d'un arbre est une CHAÎNE axiale dont la
  profondeur s'accumule (depth ~16 à 800 cm) → `depth` fait ployer le LEADER autant que les
  rameaux → hauteur s'effondre (783→368 à gain≥0.6). **Correctif** : discriminant =
  **éloignement HORIZONTAL à l'axe du tronc** (`off_axis = min(1, _horiz(tip,collet)/max_extent)`)
  — 0 sur l'axe (flèche dressée, ne ploie pas), →1 au bord (rameau distal pendant).
  Géométrique pur, déterministe, zéro RNG, zéro état neuf (pas de champ Segment, sérialisation
  intacte). L'INTENTION « tronc dressé, twigs pendants » est préservée, le mécanisme corrigé.
  Bouleau migré (`procedural_growth=True`), calibré à la sonde (520 ticks, an 10) :
  | espèce | port | gs | rs | dom | fhw | maxseg | gain | h10/cr10 (cible) |
  |---|---|---|---|---|---|---|---|---|
  | Bouleau | fleche pleureur | 1.9 | 800 | 2.7 | 70 | 70 | **1.0** | 783/270 (800/200) |
  Retombée : 6/36 rameaux distaux dont l'extrémité est SOUS son insertion (worstdz −12,5 cm),
  flèche montante monotone, structure bornée (37≤70), déterministe. **NOTE hydrique (état §3)** :
  bouleau grêle = LE plus exposé (root_r=canopy_r) → fhw=70 généreux (>50 du pommier qui survit)
  → couronne un peu large (270 vs 200) = arbitrage F5. `gravitropism_gain>0` sur le BOULEAU SEUL
  (prépare saule D23). **Golden INCHANGÉ `57c166d8…`** (défaut gain=0 → bit-identique).
  test_croissance : 133/133 (dont 2 tests T3 : `test_bouleau_d91_migre` pleureur+migration,
  `test_gravitropic_droop_helper` contrat du helper ; l'ancien `test_pommier_temoin_non_migre`
  repurposé car plus AUCUNE ligneuse non-migrée après T3). Suites connexes vertes (phototropisme
  11/11, senescence, grimpe, confinement, lifecycle, evergreen, marais). C# NON touché (rendu
  des segments = T4). Tailles : geometrie 138 🟢, phases 140 🟢, perennials 324 🟡 (vigilance,
  responsabilité unique = catalogue, déjà signalé T2). Valeurs = placeholders → F5 (T4).
  Reste : **T4 (vue Godot + banc F5)**.

- [x] **T4 — vue Godot + banc F5** (2026-07-24). PUR-VUE (C#) + banc Python (outil
  de test, niveau `main.py`). **Golden INCHANGÉ `57c166d8…`** (rien touché au moteur
  écolo). `dotnet build Symbiose.csproj` **VERT** (0 erreur / 0 avertissement).
  test_croissance : 133/133 (inchangé, T4 ne touche pas la sim).
  - **Rendu branches** : générique — les 9 arbres sortent du snapshot en SEGMENTS
    comme le pommier, `PlantRenderer` les dessine sans code par espèce (vérifié :
    aucun code d'ossature neuf).
  - **Aiguilles sapin** : **l'archétype `Aciculaire` existait déjà** (`LeafShape`,
    utilisé par thym/lavande). Décision (anti sur-ingénierie #2) : **mapper
    `FirTree → Aciculaire`** dans `LeafProfiles` = mode aiguilles, aucun dispatch
    neuf. `FirTree` reste HORS `LeafOutlines` → au ×16+ il retombe sur l'archétype
    aiguille (pas de limbe à détourer ; verticille = polish différé §7).
  - **Couverture par espèce** (clé = nom de classe Python) : `LeafProfiles` +5
    (Beech/Hornbeam=Elliptique, Birch=Cordee, Alder=Elliptique, Fir=Aciculaire) ;
    `LeafOutlines` +1 (Alder ; Fir volontairement absent) ; `Palettes` +4
    (Beech/Hornbeam/Birch/Fir ; Alder déjà présent, guilde marais). Teintes par espèce.
  - **Banc `foret_ports`** (`bancs/croissance.py` + registre `bancs/__init__.py`,
    `BANC_WEEK_DEPART=20` plein été → 10 couronnes pleines) : les 10 arbres (pommier +
    9) en grille 5×2, ~5 m d'écart, `init config="foret_ports"`. **Décision de
    conception imprévue** : PAS de déroulé Engine (comme `vieux_pommier`) mais
    **morphogénèse PURE** (`grow_plant` direct, l'oracle des sondes T1-T3). Raison :
    l'**aulne** (berge, veut le sol gorgé) et le **figuier** (méditerranéen, pourrit
    dans l'eau) ont des besoins hydriques **inconciliables** → aucune nappe forcée
    unique ne garde les 10 vivants sous le moteur complet (aulne+figuier meurent <an 2,
    constaté). Le banc observe l'ARCHITECTURE, pas l'équilibre écolo → on déroule la
    seule croissance (ni mort hydrique, ni volontaires spontanés). Déterministe
    (graine + positions fixes), sans mécanique neuve, monté 0,6 s (O(segments), pas de
    LightField). Golden NEUTRE (jamais monté pour smoke/full). Heights à l'an 10
    conformes aux gabarits T1-T3 (cerisier 504, noyer 620, bouleau 783…).
  - **Encyclopédie (§6)** : enrichissement descriptif optionnel/non bloquant **NON
    fait** (différé, cf. kickoff « peut être différé »).
  - Tailles : `croissance.py` 54 LDC 🟢 ; `PlantRenderer.Leaf.cs` 217 🟢,
    `.LeafOutline.cs` 167 🟢, `.Organs.cs` **317 🟡** (vigilance, +4 lignes palette
    sur un fichier DÉJÀ en zone, responsabilité unique = organes procéduraux ; pas
    scindé mid-tronçon, signalé). **Reste = F5 Nico** (validation visuelle des 10 ports).

## CARTE DES TRONÇONS (kickoffs autosuffisants présents)
- `01_feuillus_etale.md` — levier `auxin_release_scale` + cerisier/charme/hêtre/noyer/chêne
- `02_cas_atypiques.md` — aulne / figuier buissonnant / sapin flèche
- `03_bouleau_gravitropisme.md` — levier `gravitropism_gain` + bouleau pleureur
- `04_vue_godot_banc.md` — rendu branches + aiguilles sapin + banc F5 `foret_ports`

## §REPRISE
Conception FIGÉE. **T1 + T2 + T3 + T4 CLOS** (golden `57c166d8…` inchangé de bout en bout).
Les **10 arbres sont TOUS migrés** (`procedural_growth=True`) ET rendus (branches génériques +
feuilles/palettes par espèce + aiguilles sapin). **SPRINT PRÊT À CLÔTURER** — il ne reste que la
**validation F5 par Nico** (aucun dev restant côté agent).

**Ce que Nico doit valider au F5** (`init config="foret_ports"`, banc monté ~1 s, plein été) :
1. Chaque port lit-il juste ? flèche du **sapin**, étalé du **chêne/hêtre/noyer**, ovoïde du
   **cerisier/charme**, bas-ramifié du **figuier**, élancé de l'**aulne**, **pleureur** du
   **bouleau** (retombée des rameaux distaux — le port F5 le plus incertain).
2. **Sapin** : nseg=10 à l'an 10 → flèche assez fournie ? aiguilles crédibles (archétype
   Aciculaire) ou trop clairsemé → relever `max_segments`/densité côté moteur (hors T4).
3. **Feuilles** par espèce plausibles (repli/contour) ? teintes des palettes ?
4. Calibrage à l'œil des gabarits placeholders T1-T3 (`foliage_halfwidth`, `auxin_release_scale`,
   `gravitropism_gain`) — tout écart = dette/kickoff moteur séparé, pas T4.

Après F5 OK : cocher le sprint CLOS, passer **D91 → CLOS** dans `DETTE.md`, écrire l'entrée de
clôture `journal.md`, mettre à jour `BACKLOG.md`. Leviers moteur EN PLACE : `auxin_release_scale`
(T1) + `gravitropism_gain` (T3, discriminant = éloignement horizontal à l'axe, PAS depth) par
espèce, défauts procéduraux sur `PerennialWoody`. Encyclopédie §6 = enrichissement optionnel
NON fait (différé). **NE PAS re-figer le golden** (T4 est pur-vue).
