# Sprint Croissance procédurale (D29 réorienté) — état partagé

> État léger partagé entre tronçons (≤ ~25 lignes utiles). Mis à jour en fin de
> chaque sous-sprint. Conception figée : `data/code/CONCEPTION_CROISSANCE.md`.

## Ce qu'on construit
Remplacer l'affichage par sprites figés par une **vraie morphogénèse** : chaque
plante possède une **structure de segments** (branches), en **Python** (source de
vérité, déterministe), dont la croissance est pilotée par l'**auxine le long de la
structure** + la **lumière** (`LightField`). L'empreinte (`height_at`/`canopy_radius_at`
…) sera **dérivée de la structure** (contrat inchangé, seule la source change). Rendu
**tout procédural** (branches + organes en pixels) côté Godot. **Profil de croissance
PAR ESPÈCE** (vitesse + `port_archetype`) à décrire pour les 14 espèces. Absorbe D29
hormones (le modèle « 2 scalaires » est mort ; `tailler` devient un appelant du seam).

## Stratégie golden (re-figeage MAÎTRISÉ, pas « intact »)
Le moteur permanent change le comportement de **toutes** les plantes → le golden
**sera re-figé**, mais **localisé et incrémental** : la structure est **construite
inerte d'abord** (tronçon 1, golden INTACT car non lue), **puis câblée à l'empreinte**
(tronçon 2, **re-figeage**), **espèce par espèce** (démonstratrice d'abord). On valide
(visuel + numérique vs gabarit `growth_stages`/`age_curve`) **avant** de figer.

## Découpage (sprint GROS → 6 tronçons ; révisable par Nico)
- **1 — Structure + croissance Python (cœur), INERTE.** ✅ `Segment` (base+dir+length
  +`has_bud`) sur `PlantInstance` (1 apex au collet) ; `sim/growth.py` (auxine le long
  de la structure, allongement/émission, débourrement, **bornage** : retrait d'apex à
  `MAX_REACH`, senescence du bois sans apex, plafond `MAX_SEGMENTS` dur, **rejet de
  souche** → run éternel), appelé par l'engine après la physiologie. Déterministe
  (`_hash_noise`, zéro RNG). `tests/test_croissance.py` **19/19**. **Golden INTACT**
  (structure non lue). Phototropisme **stubé neutre** (apex droit, jitter latéral) →
  tronçon 2. ⚠️ Golden **réduit à 10 ans** (2026-06-05, la croissance alourdit le tick ;
  sénescence pommier ~70 ans **non exercée pour l'instant**) → re-capturé **`6369c30b…`**
  (≠ ancien `c950f06c…`). Le hash `c950f06c…` cité dans `01_*.md` est donc périmé.
- **2 — Profil par espèce + dérivation d'empreinte.** ✅ Schéma §E posé sur
  `PlantBase` (attributs de classe, défauts = ex-constantes de module → espèces non
  migrées inchangées) ; `grow_plant` lit le profil depuis `plant.plant_class`.
  **Tomate migrée** (`procedural_growth=True`) : `height_at`/`canopy_radius_at`/
  `root_radius_at` lisent un **cache `inst.footprint`** recalculé en fin de
  `grow_plant` (repli à la volée si None). `foliage_density_at` garde l'ancien chemin
  (feuilles = tronçon 5). Racines = `PROC_ROOT_RATIO·canopy` (k=1.0). `test_croissance`
  **33/33** (5 structure tronçon 1 intacts + allure tomate + témoin Basil).
  **Golden NON re-figé** : il reste **`6369c30b…`** (engine) / **`b005d9ba…`** (pop),
  inchangés — LÉGITIME, pas une fuite (cf. ⚠️ ci-dessous). Suite complète verte
  (genetique 20, maitrise 35+20, signes 8, vigueur 103, main.py OK).
  > ⚠️ **2 imprécisions du kickoff `02_*.md` corrigées** : (a) il citait les stades
  > de Bourse-à-pasteur (~40 cm) comme ceux de la tomate → recalibré sur la VRAIE
  > tomate **~150 cm** (choix Nico, §E.3). (b) Il prédisait un **re-figeage** ; en
  > fait la tomate **meurt à w2-3 dans le scénario golden** (froid de démarrage
  > t≈4.4 °C < seuil 5 °C + mildiou familial Solanaceae -1 santé/sem → morte avant
  > de pousser ; **comportement préexistant**, identique au tronçon 1). À ses tailles
  > (≤35 cm → 1 seul plot) l'empreinte procédurale ne perturbe **rien** → golden
  > intact. La vraie couverture du procédural = le **test d'allure** (montée monotone
  > 3→150, couronne 18→49), pas le golden. (c) `apical_dominance_base` dut passer à
  > **2.2** (>1) car `AUXIN_DECAY`/seuil (modules, fixes) ne permettent pas de tenir
  > une flèche de ~19 segments sous 1.0 → attribut redéfini en « force » (1.0=nominal).
- **3 — Seam `atteindre_segment` + `tailler`.** ✅ Seam continu (§F) posé dans
  `sim/growth.py` (doux = baisse d'auxine ; net ≥ `COUPE_NETTE` = écimage du sous-arbre,
  collet protégé ; pur structurel, zéro RNG/Vigueur). `tailler` branchée dans
  `sim/actions.py` (binaire calqué sur `deraciner` : coût `MODERE` via `cout_action`,
  gain ∝ maturité × `GAIN_TAILLE_RATIO`, appelle le seam → débourrement ÉMERGENT au
  tick suivant). **Golden INTACT** (`6369c30b…` engine, pop & vigueur_hash inchangés —
  `tailler` jamais appelée par le scénario). `test_croissance` **43/43** (+4 seam :
  écimage→débourrement, doux, collet protégé, déterminisme), `test_vigueur` **110/110**
  (+7 : contrat coût/binaire/gain/objets de `tailler`). **Absorbe D29 hormones**
  (modèle scalaire `dominance_apicale`/`reponse_taille` définitivement jeté).
  Points tranchés : `COUPE_NETTE=0.8`, `GAIN_TAILLE_RATIO=0.3`, `_segment_cible`
  (apex = cime z max ; branche = apex latéral le plus profond, repli meneur ; collet→None).
  > **Périmètre réduit vs kickoff initial** : la démonstratrice **pommier** (`etale`,
  > fructification latérale) est sortie → **tronçon 3bis** dédié (re-figerait le golden,
  > exige l'override `PerennialWoody` + calibrage `age_curve`). Ici on démontre sur la
  > **tomate** (déjà procédurale), golden intact.
- **3bis — Migration procédurale du pommier.** ⬜ Port `etale`, fructification
  latérale, override `PerennialWoody`, calibrage `age_curve` décennal → re-figeage
  golden localisé.
- **4 — Rendu pixel structure (Godot).** ⬜ Projection iso + rastérisation segments
  aux zooms ×4…×32, LOD (§H.1/§H.3). Premier rendu visible des branches.
- **5 — Organes procéduraux (Godot) — RISQUE N°1.** ⬜ Générateur feuilles/fleurs/
  fruits, stades d'organe, palette/saison (§H.2). Itératif.
- **6 — Save de la structure.** ⬜ Sérialisation JSON bornée (§J), option d'allègement.

## Plus tard (hors chantier, ligne BACKLOG)
Déclencheurs naturels du seam (grêle/chenille/vent → `atteindre_segment`) ; marqueur
`🌿` (succès maîtrise §9.5) ; profil de croissance du **reste du catalogue** (§E.4) ;
portage C# (D24) ; structure racinaire réelle (gated, §8 = rayon dérivé).

## Décisions déjà actées (conception — `CONCEPTION_CROISSANCE.md` §B)
Segments / Python source de vérité / accumulation **bornée** / auxine le long des
segments / phototropisme `LightField` / empreinte **dérivée** (contrat inchangé) /
organes **tout procéduraux** / racines **rayon dérivé**. Intensité **continue**,
moteur **permanent**, déclencheurs naturels **plus tard**.

## Points ouverts (à trancher dans le tronçon concerné, défaut sobre + signaler)
- **1** ✅ tranché : `Segment` = **base+dir+length** (extrémité dérivée) + `has_bud`
  (bourgeon axillaire, §D.3) ; boucle = **module dédié `sim/growth.py`** appelé par
  l'engine (§9c, après `_update_physiology`). Bornage : portée `MAX_REACH_CM` +
  senescence + plafond dur + rejet de souche (leviers de module, calibrage = tronçon 2).
- **2** ✅ tranché : cache d'empreinte = **dict `inst.footprint` recalculé 1×/tick**
  en fin de `grow_plant` (défaut sobre ; repli à la volée si None), **pas**
  d'invalidation paresseuse. Bascule par espèce = **flag `procedural_growth`**.
  `canopy_radius` sans organes = `max_horiz + foliage_halfwidth` (couronne non nulle
  même droit). `root_radius` = **k·canopy** (k=`PROC_ROOT_RATIO`=1.0). `foliage_density`
  = ancien chemin (→ tronçon 5). Ordre de migration = **tomate seule** ce tronçon.
- **3** ✅ défaut tranché : `cible="branche"` = retrait de l'**apex latéral le plus
  profond** (non-meneur) → la flèche n'est pas touchée, donc la dominance reste
  ~inchangée (elle émerge du choix de cible, pas d'une mécanique dédiée). Repli sur le
  meneur s'il n'y a aucun latéral. Heuristique alternative encore possible (calibrage).
