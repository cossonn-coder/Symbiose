# 00_etat — Sprint GRIMPANTES (mécanique moteur de la grimpe, D49)

> Carnet de bord VIVANT (skill /conception §0bis). Phase A en cours = challenge,
> RIEN n'est figé. Reprise à froid : lire `CLAUDE.md` + ce fichier.

## Sujet
Volet A SEUL de D49 : une plante grimpante cherche un SUPPORT, s'y accroche,
grimpe pour de vrai → hauteur → accès lumière (LightField). L'avantage doit
ÉMERGER d'une géométrie (philo #2), jamais d'un bonus direct. Couche A Python
(vérité) AVANT tout rendu C#. Rendu de vrille (CONCEPTION_RENDU_FEUILLAGE §7/E6)
HORS périmètre. Rampantes/traçantes + violettes = HORS (reporté D62).

## Vérifications CODE faites en phase A (ancrage)
1. **Bean (Haricot) est `procedural_growth = True`** (Fabaceae, `species/cultivees.py:42`,
   Bean l.136). Sa hauteur = `footprint_value("height")` = **max(z) des extrémités
   de segments** (`base/instance.py:176-204`). Sa canopée = extension horizontale
   max. → la hauteur est DÉJÀ émergente de la géométrie des segments, PAS un
   scalaire. Les `canopy_height=150/200` des stades grimpante sont des potentiels,
   pas la hauteur lue.
2. **Bean EST dans le golden** (`tests/test_golden.py:76 add_plant(Bean,4,2)`).
   → toute modif de sa croissance RE-FIGE le golden (smoke test).
3. **L'apex a déjà un plancher de verticalité** `MIN_APEX_Z` dans
   `_phototropic_bias` (`growth/geometrie.py:88-115`) : si la composante z tombe
   sous le plancher, l'apex est redressé « jamais à plat ». C'est LE hook naturel
   du port grimpant : moduler ce plancher selon l'état de support.
4. **`current_height` est lu par PLUSIEURS consommateurs** hors lumière :
   `container.py:209` (occupation pot), `engine/decompo.py:85` (nécromasse
   abscission), `effects/perturbations.py:34,382` (nécromasse + establishment),
   `fields/abri.py:64` (abri faune), sérialisation pont. → si « hauteur effective »
   DIVERGE de la biomasse réelle, ces consommateurs sous-comptent (une grimpante
   affalée a une grande biomasse mais une faible hauteur debout).
5. **StakeSlot ≠ tuteur de grimpe** (`world/tile.py:18-56`). C'est le porte-
   **rondelles** du système MTG (0-9 tiges × max 3 rondelles homogènes, `is_bonus`).
   AUCUNE position, AUCUNE hauteur. → la prémisse du brief et de D49 (« 10 tuteurs/
   tuile réutilisables ») est FAUSSE. Un tuteur/treillis/pergola de grimpe est une
   STRUCTURE NEUVE (position + hauteur), proche des bac/pile posables (⑤ décompo).
6. **Mur maison** existe avec hauteur + albédo espalier (`world/building.py:31-32`,
   height 600, wall_albedo 0.35). Support « mur » réel et gratuit.

## Décisions ARRÊTÉES (Nico, batch 1)
- **A1 = GÉOMÉTRIQUE.** La hauteur émerge de la géométrie des segments : au-delà
  de `hauteur_autoportante` sans support, l'apex retombe (plancher de verticalité
  effondré → `max_z` bas + étalement horizontal = affalement). Accroché → biais
  d'apex vers l'axe du support → grimpe. `height_at`/`current_height` restent la
  vraie `max_z`, JAMAIS de clamp/divergence → consommateurs (nécromasse, abri,
  pot) justes. Réutilise `_phototropic_bias` + `MIN_APEX_Z` (growth/geometrie).
- **A2 = PANOPLIE COMPLÈTE.** Supports posables NEUFS : tuteur + treillis +
  pergola + geste `palisser`, PLUS le mur maison (existe) et la plante-hôte
  vivante (émergent). StakeSlot NON réutilisé (c'est le porte-rondelles MTG).
- **A3 = DÉMO RÉDUITE.** 2-3 plantes pour prouver la mécanique ; le reste du
  catalogue → D26.

## Micro-choix Claude (tranchés)
- **mode_grimpe** = 3 valeurs `crampon` / `vrille_volubile` / `sarmenteux`
  (gouverne QUELS supports sont valides).
- **Plantes démo** = HARICOT (déjà là, `vrille_volubile`, coût 0) + LIERRE
  (`crampon`, monte au mur nu) + JASMIN (`sarmenteux`, démontre `palisser`).
  → couvre les 3 modes avec 2 espèces neuves. GLYCINE écartée (redondante avec
  haricot : Fabaceae + vrille_volubile déjà couverts) → part en D26 avec
  courge/kiwi/vigne/akébia.
- **Étranglement** par ombre du LightField : émergent, pas de règle dédiée, assumé.
- **Verse/vent** : attaché → résistance ; tuteur ne casse PAS (écarté).
- **Vue Godot** = INCLUSE (tronçon ⑥, décision Nico 2026-07-03) : rattache le
  **rendu de vrille** différé (`CONCEPTION_RENDU_FEUILLAGE §7/E6`) + rendu des
  supports. Bonus décision A : la vue suit la géométrie GRATUITEMENT (les
  segments montent/s'affalent déjà dans le snapshot → PlantRenderer les dessine).

## RÈGLE PERMANENTE (Nico 2026-07-03)
La **vue Godot est TOUJOURS le dernier tronçon** de chaque sprint (ici et pour
tous les prochains). Gravée en mémoire + skill `/conception` (phase B). Un sprint
moteur sans son tronçon vue est incomplet.

## Découpage FIGÉ (6 tronçons, perf-first)
- ① **CLOS** (2026-07-03) traits (`hauteur_autoportante`, `mode_grimpe`, état
  `support`) + affalement géométrique SANS support. Golden **RESTÉ NEUTRE**
  (`a6c2f651…` inchangé) — cf. §REPRISE : la dérive prévue ne se matérialise pas
  dans le digest (le droop est réel sur la géométrie du haricot mais n'atteint pas
  les `_PLANT_ATTRS` trackés). Aucun re-figeage effectué (illégitime sans dérive).
- ② **CLOS** (2026-07-03) structures-support posables (`world/support.py` :
  `Support` + table `support_compatible` + sentinelle `MUR`, champ `Tile.supports`)
  + mur maison + recherche d'accroche bornée (`sim/grimpe.py:chercher_support`,
  rayon 1.5 plot, câblée dans `boucle.py` juste avant `grow_plant`) + biais de
  grimpe (`GRIMPE_Z` + branche accroché de `_apex_z_floor`). Golden **NEUTRE**
  (`a6c2f651…` inchangé) — haricot=vrille_volubile, mur nu refusé, aucun support
  posé dans le smoke.
- ③ **CLOS** (2026-07-03) plante-hôte vivante comme support (`world/support.py` :
  sentinelle `HOTE` + compat crampon/vrille_volubile ; `sim/grimpe.py` :
  `_hote_candidats` scan des voisines vivantes plus hautes + `_maj_ou_detache_hote`
  entretien avant filtre perf = relit `current_height` chaque tick / détache à la
  mort ou disparition de l'hôte) + étranglement ÉMERGENT (LightField, aucune règle
  dédiée). Golden **NEUTRE** (`a6c2f651…` inchangé). Suite `tests/test_grimpe.py`
  NEUVE (7 tests : accroche/suivi/détachement×2/rayon/seuil/étranglement).
- ④ gestes joueur (`poser_tuteur/treillis/pergola`, `palisser`) + maîtrise
  (outil `tuteur`, technique `palissage`) + résistance verse → event-driven,
  golden INTACT.
- ⑤ catalogue lierre + jasmin + 5 voix chacune + SOIL_SIGNATURE → golden NEUTRE.
- ⑥ **vue Godot** : rendu supports + accroche + vrilles (§7 feuillage) + pont
  (supports au snapshot, bump ENGINE_VERSION) + **banc d'essai `grimpantes`**
  (Nico 2026-07-03 : haricot À CÔTÉ du tournesol pour la grimpe sur hôte, champ
  tomates/basilic/poivrons au sud, départ début printemps=automatique wiy1) →
  golden INTACT (vue pure + banc jamais monté pour smoke/full).

## §REPRISE
CONCEPTION FIGÉE 2026-07-03. Doc = `docs/conception/CONCEPTION_GRIMPANTES.md`.
6 kickoffs `01→06` écrits.

**① CLOS 2026-07-03.** Fait : 2 traits inertes sur `PlantBase`
(`hauteur_autoportante`/`mode_grimpe`), état `support=None` sur `PlantInstance`,
Bean réglé (35 cm / `vrille_volubile`), constante `DROOP_Z=-0.10`, plancher d'apex
CONTEXTUEL `_apex_z_floor(plant, max_z)` + `_clamp_apex_z` dans `growth/geometrie.py`,
câblés dans `_elongate_emit` (`growth/phases.py`) via un `z_floor` calculé une fois
par passe. Non-grimpantes strictement inchangées (défauts `None`).

**GOLDEN NON RE-FIGÉ — resté NEUTRE `a6c2f651…`.** Le kickoff ① prévoyait une
dérive maîtrisée (haricot affalé → `growth_factor`/`shade_memory`). Vérifié
empiriquement : le droop S'ACTIVE bien (Bean T1 dépasse 35 cm, plancher effondré
167×, 45 apex émis sous MIN_APEX_Z), la géométrie DIFFÈRE (max_horiz +0,6 cm sous
gradient fort) MAIS l'écart ne remonte pas jusqu'aux `_PLANT_ATTRS` trackés (canopée
quantifiée au plot + haricot annuel qui meurt/reset). Un re-figeage aurait été
illégitime (pas de dérive réelle). Mécanique correcte, juste plus douce que prévu au
digest. À revoir en ⑥ (F5) : si l'affalement doit se VOIR davantage, calibrer
`DROOP_Z` / la tolérance de tilt — décision Nico à la maquette.

Suites vertes (golden, croissance 67/67, phototropisme 11/11, senescence, vigueur
136/136, population, maitrise, plasticite + suite complète). `test_sim_server`
ROUGE mais PRÉ-EXISTANT (KeyError 'plants' dû au WIP hydrologie non commité sur
`serialize.py`, reproduit sans mes changements) — hors périmètre ①.

**② CLOS 2026-07-03.** Fait : `world/support.py` NEUF (dataclass `Support`
type/x_cm/y_cm/height_cm/finesse + helper pur `support_compatible` : crampon→tout,
vrille_volubile→tout sauf mur nu, sarmenteux→rien auto ; sentinelle `MUR`),
champ `Tile.supports=[]`, ré-export `world/__init__.py`. `sim/grimpe.py` NEUF :
`chercher_support(plant, tile, house)` — no-op sauf grimpante LIBRE au-dessus de
`hauteur_autoportante` ; scan borné (rayon 1.5 plot) des `Tile.supports` + point
d'appui du mur maison (repère monde via `tile_origin`) ; retient le compatible le
plus proche, départage déterministe (distance puis clé stable, zéro RNG) ; pose
`plant.support=(ref, height_appui)`. Câblé dans `boucle.py` (étape 9c-bis, juste
avant `grow_plant`, house depuis `game_state`). Loi d'apex complétée : constante
`GRIMPE_Z=0.85`, branche accroché de `_apex_z_floor` → plancher renforcé tant que
`max_z < height_appui`, MIN_APEX_Z au sommet atteint.

**GOLDEN NEUTRE — `a6c2f651…` inchangé** (haricot=vrille_volubile, mur nu refusé,
aucun `Support` posé dans le smoke → aucune accroche ne se déclenche). `test_golden`
PASS hash identique. `test_sim_server` **VERT 244/244** (était rouge au ① à cause
du WIP hydrologie non commité ; désormais vert). Suites vertes : croissance 67/67,
phototropisme 11/11, senescence, signes 8/8, structures 80/80, plasticité,
conteneur. C# **non concerné** (② Python pur). LDC : support.py 19, grimpe.py 43
(≤300 🟢).

Sanity manuel hors golden (accroche RÉELLE prouvée) : haricot forcé >35 cm sans
support reste libre ; avec un tuteur à 10 cm → accroche (persistante, non
re-scannée) ; un crampon fictif près du bord du mur maison → accroche mur
(hauteur d'appui 600).

**③ CLOS 2026-07-03.** Fait : sentinelle `HOTE` dans `world/support.py`
(compat crampon + vrille_volubile, PAS sarmenteux — une tige vivante offre une
prise) + ré-export `world/__init__.py`. `sim/grimpe.py` étendu :
`_hote_candidats(plant, tile, mode)` scanne les voisines VIVANTES plus hautes que
`hauteur_autoportante` dans le rayon (clé de départage = `id(other)`, déterministe
intra-tick) ; `_maj_ou_detache_hote(plant, tile)` appelé AVANT le filtre perf =
relit `hote.current_height` chaque tick (suivi) ou détache (`support=None`) si
l'hôte est mort/parti (`_est_hote` = duck-typing sur `is_alive`/`current_height`).
Étranglement NON codé : ÉMERGE du `LightField` (tri hauteur-décroissante, aucune
exclusion entre plantes distinctes proches — VÉRIFIÉ : `light.py:253` ne saute que
l'auto-ombrage via `qh <= ph: break`).

**GOLDEN NEUTRE — `a6c2f651…` inchangé** (Bean(4,2) sans voisine haute à portée ;
Sunflower en (0,1) hors rayon). `test_golden` PASS hash identique. `test_sim_server`
**VERT 244/244**. Suite NEUVE `tests/test_grimpe.py` (7 tests VERTS) : accroche hôte
vivant, suivi de croissance, détachement à la mort, détachement si l'hôte disparaît,
hors-rayon refusé, hôte trop court ignoré, étranglement émergent (hôte 180 cm sous
grimpante 200 cm → lumière 0.80 vs 1.0 isolé). Suites vertes : croissance,
phototropisme 11/11, sénescence, signes, structures, conteneur. C# **non concerné**
(③ Python pur, vue en ⑥). LDC : grimpe.py 73, support.py 20 (≤300 🟢).

**PROCHAINE ÉTAPE → ④ `04_gestes_maitrise.md`** : gestes joueur
(`poser_tuteur/treillis/pergola`, `palisser`) + maîtrise (outil `tuteur`, technique
`palissage`) + résistance verse → event-driven, golden attendu INTACT.
Golden : ①②③ resté NEUTRE, NEUTRE/INTACT ④→⑥.
