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

## CARTE DES TRONÇONS (kickoffs autosuffisants présents)
- `01_feuillus_etale.md` — levier `auxin_release_scale` + cerisier/charme/hêtre/noyer/chêne
- `02_cas_atypiques.md` — aulne / figuier buissonnant / sapin flèche
- `03_bouleau_gravitropisme.md` — levier `gravitropism_gain` + bouleau pleureur
- `04_vue_godot_banc.md` — rendu branches + aiguilles sapin + banc F5 `foret_ports`

## §REPRISE
Conception FIGÉE. **T1 CLOS** (golden `57c166d8…` inchangé). Prochaine étape :
**T2 = `02_cas_atypiques.md`** (aulne / figuier buissonnant / sapin flèche). Lire :
`CLAUDE.md` + ce fichier + le doc figé
`docs/vegetal/croissance/conception_migration_arbres.md` + `02_cas_atypiques.md`.
Le levier `auxin_release_scale` (T1) est en place et disponible pour le sapin
(flèche → rs long). Chaque tronçon met à jour ce fichier (cocher + valeurs de
calibrage + hash golden confirmé).
