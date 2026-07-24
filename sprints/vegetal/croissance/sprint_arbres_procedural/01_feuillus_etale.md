# T1 — Feuillus etale + levier `auxin_release_scale`

**Sprint :** migration des 9 arbres en croissance procédurale (D91).
**Doc de conception :** `docs/vegetal/croissance/conception_migration_arbres.md` (§2, §4, §7).
**Doc mère :** `docs/vegetal/croissance/conception_croissance.md` (§D.1, §E, §G).
**Golden attendu : INCHANGÉ** (`57c166d8…`). Ne PAS re-figer.

## Objectif
1. Ajouter le levier d'ontogénie **par espèce** `auxin_release_scale` (moteur).
2. Migrer 5 feuillus etale en croissance procédurale : **cerisier, charme, hêtre,
   noyer, chêne**, calibrés pour survivre et reproduire leur allure `age_curve`.

## Contexte technique (établi par lecture du code)
- Seul le **pommier** (`AppleTree`, perennials.py:146) est `procedural_growth=True`
  aujourd'hui. Son bloc de profil (lignes 159-209) est le **patron à répliquer**.
- `_update_auxin(segs, dominance)` (sim/growth/phases.py:29) lit la **constante de
  module** `AUXIN_RELEASE_SCALE = 400.0` (sim/growth/constantes.py:22) :
  `f_age = max(AUXIN_PROD_FLOOR, 1.0 - plant_age / AUXIN_RELEASE_SCALE)`.
- Les défauts de profil sont sur `PlantBase`/`familles.py` (lignes 234-249).
- **Piège de survie n°1** : `update_footprint` (instance.py:259) pose
  `root_r = canopy_r = max_horiz + foliage_halfwidth`, `PROC_ROOT_RATIO=1.0`. Une
  jeune flèche étroite → racines sur 1 plot → assèchement → mort ~an 3. Le pommier
  s'en sort avec `foliage_halfwidth=50` (voir son commentaire perennials.py:178-186).

## Fichiers à toucher
- `data/code/sim/growth/phases.py` — signature de `_update_auxin`.
- `data/code/plants/base/familles.py` — nouvel attribut `auxin_release_scale`.
- `data/code/plants/perennials.py` — défauts procéduraux d'arbre sur
  `PerennialWoody` + profils des 5 espèces.
- `data/code/tests/` — un test de croissance libre (voir §Tests).

## Étape 1 — levier `auxin_release_scale` (moteur, golden-safe)
1. Sur `PlantBase` (familles.py, à côté de `apical_dominance_base`) ajouter :
   ```python
   auxin_release_scale: float = 400.0  # semaines : échelle de relâchement d'auxine
   # avec l'âge (§D.1). Défaut = ancienne constante globale AUXIN_RELEASE_SCALE →
   # espèce non réglée = comportement historique. Ligneux longévif → PLUS GRAND
   # (dressé plus longtemps) ; pionnier → plus petit.
   ```
2. Dans `_update_auxin`, ajouter un paramètre `release_scale: float` et remplacer
   la constante par lui :
   ```python
   def _update_auxin(segs: list, dominance: float, release_scale: float) -> None:
       ...
       f_age = max(AUXIN_PROD_FLOOR, 1.0 - plant_age / release_scale)
   ```
   Garder l'import de `AUXIN_RELEASE_SCALE` (il reste la valeur-défaut miroir).
3. Dans `grow_plant` (phases.py:241), passer `cls.auxin_release_scale` :
   ```python
   _update_auxin(segs, cls.apical_dominance_base, cls.auxin_release_scale)
   ```
   Le pommier / Tomate / grimpantes héritent 400.0 → **appel bit-identique**.

## Étape 2 — défauts procéduraux d'arbre sur `PerennialWoody`
Sur la classe `PerennialWoody` (perennials.py:22), poser des défauts de profil
**d'échelle arbre** (mutualisation, §4 du doc), SANS flipper `procedural_growth`
(reste False sur la base → migration incrémentale) :
```python
# Défauts procéduraux communs aux ligneux migrés (chaque espèce surcharge son
# gabarit / release_scale / dominance). procedural_growth reste flippé PAR ESPÈCE.
emit_length_cm    = 50.0    # flèche en peu de segments (comme le pommier)
max_segments      = 70
wood_persistence  = 4000    # ~la vie de l'arbre (sinon charpentières meurent en 1 an)
branch_angle      = 70.0    # insertion assez horizontale → étalement
foliage_halfwidth = 50.0    # SURVIE hydrique (racines multi-plots) — départ, à ajuster
port_archetype    = "etale"
apical_dominance_base = 2.0
```
> Ces défauts reproduisent le profil pommier. Chaque espèce migrée ne surcharge
> ensuite que ses **deltas** (gabarit `max_height_cm`/`max_extent_cm`, `growth_speed`,
> `auxin_release_scale`, `girth_max_cm` déjà posé).

## Étape 3 — migrer les 5 feuillus etale
Pour **cerisier (`CherryTree`), charme (`HornbeamTree`), hêtre (`BeechTree`),
noyer (`WalnutTree`), chêne (`OakTree`)**, ajouter à chaque classe :
```python
procedural_growth = True
growth_speed      = <calibré>     # cm/tick pour atteindre l'allure age_curve
max_height_cm     = <dernier point d'age_curve en hauteur, ou plafond visé>
max_extent_cm     = <dernier point d'age_curve en rayon>
auxin_release_scale = <400 par défaut ; chêne & hêtre PLUS GRAND, ex. 900-1500>
# foliage_halfwidth hérité (50) — AJUSTER si l'espèce meurt de soif jeune (F5/sonde)
```
**Méthode de calibrage (comme le pommier, §E.3)** : régler `growth_speed` /
`max_height_cm` / `max_extent_cm` pour que l'empreinte dérivée **reproduise
l'allure de l'`age_curve`** dans la fenêtre d'observation (viser le point ~10 ans
de chaque `age_curve`). Utiliser une **sonde de croissance libre** (voir §C du doc
mère : `growth_factor=1.0`, cycle saisonnier réel, ~520 ticks) pour vérifier :
montée monotone, bornée, pas d'effondrement de couronne, **pas de mort hydrique
précoce** (si la sonde tourne avec eau simulée). Ce sont des **placeholders → F5** :
viser le bon ordre de grandeur, Nico affine à l'œil au T4.

Gabarits qualitatifs à respecter (relatifs) : chêne = très grand & large ; hêtre =
grand ample ombre profonde ; noyer = grand ouvert ; cerisier = moyen ; charme =
moyen ovoïde.

## Ce qu'il NE faut PAS faire
- Ne PAS flipper `procedural_growth` sur `PerennialWoody` (base) — par espèce only.
- Ne PAS toucher le pommier (`AppleTree`) — son profil reste tel quel.
- Ne PAS re-figer le golden. Si le golden bouge, c'est un bug (les 5 espèces sont
  hors scénario, le défaut release_scale=400 laisse le pommier identique) → chercher
  la régression, ne pas re-figer.
- Ne PAS toucher aulne / figuier / sapin / bouleau (tronçons suivants).
- Ne PAS ajouter le gravitropisme (c'est T3).

## Tests / vérification
- **Golden** : `cd data/code && python3 -m tests.test_golden` → **INCHANGÉ**.
- **Suites ciblées croissance** existantes : relancer celles qui exercent la
  croissance procédurale (chercher `tests/test_croissance*` / structure) → vertes.
- Ajouter un petit test de croissance libre par espèce migrée (au moins chêne +
  cerisier) : instancier, faire tourner ~520 ticks, asserter hauteur finale > semis,
  structure bornée (`len(segments) <= max_segments`), déterminisme (deux runs =
  mêmes segments).
- **Ne PAS** lancer `test_epaisseur_500ans` (interdit — long, inutile).

## Mise à jour en fin de tronçon
- `00_etat.md` : cocher T1, noter les valeurs de calibrage retenues + hash golden
  confirmé inchangé + reste (T2).
- Commit : `feat(arbres ①) : levier auxin_release_scale + 5 feuillus etale migrés (D91)`.
