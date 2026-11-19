# Sprint STRESS AU BILAN (D140 G, sprint B) — état

> Conception FIGÉE le 2026-11-18 : `docs/vegetal/sante/conception_plante_vivante.md`
> (§4-§5). **Prérequis : `sprints/vegetal/sante/sprint_plante_vivante/` (A) CLOS** —
> ce sprint suppose le bilan carbone, `feuillage`, `reserves`, `vitalite` dérivée et
> l'adaptateur `erode` = perte de tissus en place. Lire l'`00_etat.md` du sprint A
> (acquis, noms réels des fonctions et constantes) AVANT tout tronçon.

## But
Remplacer l'adaptateur universel du sprint A par le **vrai mécanisme de chaque
stress** : ce qu'il retire (feuilles, sucres, eau, racines, vaisseaux, bourgeons).

## Décisions clés (Nico, 2026-11-18)
- Tout le vivant végétal passe au bilan ; plus de mort au sort.
- Causes de mort : famine, destruction, défaillance hydraulique, racines perdues,
  fin de cycle, vieillesse. Code supplanté commenté et conservé, jamais supprimé.

## Golden
Départ = `e24a23d8cb09…` (fin de `sprint_lisibilite_bilan`). ① **INTACT** (vérifié, voir Acquis) · ②③④ **RE-FIGÉ annoncé** chacun (dérive
prouvée localisée par neutralisation du seul mécanisme du tronçon) · ⑤ **INTACT**.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_secheresse_embolie.md` — stomates + défaillance hydraulique | **FAIT** (golden INTACT `e24a23d8…`, non commité) |
| ② | `02_froid_gel_brulure.md` — feuilles détruites vs bourgeons/sève gelés | à faire |
| ③ | `03_maladies_racines.md` — mildiou, oïdium, fonte, asphyxie, pourriture, campagnol | à faire |
| ④ | `04_vieillesse_cycle_mycorhize.md` — vieillesse, fin de cycle, paiement fongique | à faire |
| ⑤ | `05_vue.md` — signes, info-bulle, banc, clôture D140 G | à faire |

## Contrôle commun à chaque tronçon
Critères d'ouverture du sprint A toujours tenus (`tests/test_ouverture_vivante.py`) ;
perf tick `full` ≤ +10 % ; suites `tests/` vertes ; jamais `test_epaisseur_500ans`.

## Acquis du ① (2026-11-19)
- Départ réel = golden de `sprint_lisibilite_bilan` (`e24a23d8cb09…`, hauteur acquise),
  pas celui du sprint A.
- `sim/embolie.py` (neuf, pur) : `seuil_extreme(plant)` = `PART_EXTREME` 0,5 ×
  `SEUIL_SEC` 0,15 / gène `tolerance_secheresse` EXPRIMÉ ; `maj_embolie(plant,
  hum_percue, presence, surplus) -> bool` (accumule `TAUX_EMBOLIE` 0,20 × sévérité ×
  présence ; dilue `× (1 − RENOUV_BOIS 0,05 × min(1, surplus))` ; True à
  `SEUIL_EMBOLIE` 0,9) ; `conduction(plant)` = 1 − embolie.
- `PlantInstance.embolie` (hors `_PLANT_ATTRS`). `sim/bilan.f_eau` : rampe sèche sur
  `hum_percue × conduction` (la plante « voit » un sol plus sec ; sur sol arrosé une
  embolie partielle ne coûte rien). **Écart au kickoff (mesuré)** : un rabot direct
  `f_eau × conduction` mettait un chêne à 50 % d'embolie en déficit l'été sur sol humide
  → jamais de bois neuf → spirale de famine.
- `_update_physiology` : `presence` calculée une fois, puis après la famine
  `elif maj_embolie(…)` → `MortaliteMixin._mort_dessechee` (setter `vitalite = 0` =
  destruction, la souche garde ses réserves ; log « 🪦 X@pos meurt de dessèchement
  (embolie …) » + nécromasse). `sim/evenements._raison_mort` : « meurt de dessèchement »
  → cause **`secheresse`** (voix carnet/aide/concept `eau` EXISTANTES, pas de clé neuve
  `dessechement` — écart assumé au kickoff).
- `drought_stress_damage` SUPPLANTÉ (appel commenté dans `perturbations.py`, fonction
  conservée ; `DROUGHT_DAMAGE_THRESHOLD` reste lu par `souche_vivante`, `semiologie`,
  bancs). `drought_memory` NON détournée (5 lecteurs : plasticité, voix soif, signe,
  souche, pont) : l'embolie lit `eau_percue` du tick, l'accumulation fait l'intégration.
- Gène de tolérance sécheresse : aucune espèce ne le surcharge (neutre 1,0 partout) —
  pas de « tolérance d'espèce » comme le kickoff le supposait ; le seuil suit le gène
  individuel × plasticité seulement.
- Golden **INTACT** `e24a23d8…` (re-figeage annoncé inutile) : smoke ne descend jamais
  sous 2× le seuil sec (eau perçue / seuil ≥ 2 sur 5005 plante-semaines), `drought_memory`
  max 0,035 → ni l'ancien dégât ni l'embolie ne s'y exercent [seed 42, n=1].
- Effet en jeu (`full` seed 42 s10→s62, n=1) : `drought_memory` max 0,39 → l'ancien
  dégât ne tirait JAMAIS non plus ; embolie sur 51 plante-semaines, toutes des trèfles
  (max 0,63), aucune mort desséchée — le monde normand n'a pas de sécheresse extrême ;
  le mécanisme est prouvé par banc (`tests/test_embolie.py`).
- Banc `tests/test_embolie.py` : modérée (10 sem stomates fermés, réserves 0,79,
  embolie 0, pluie → remonte) ; extrême (chêne mort hydraulique en 5 sem, réserves 0,90) ;
  tolérante (sol 0,03 : neutre 8 sem, gène 1,5 → 12 sem) ; bois neuf (0,50 → 0,41 en
  4 sem, figé en dormance) ; tick réel → ligne 🪦 lue `secheresse`.

- `tests/test_ouverture_vivante` : 3 critères TENUS (arbres 0/13 ; herbacées 18/123 =
  14,6 % ; 0 rejet). Suites : vertes sauf `test_peripherie`, `test_population` et 6
  `tests/bancs/*` (climatique, biotique, edaphique, bancs_grimpe, liane_relais,
  verger_mur) — tous **rouges aussi sur HEAD** (worktree, vérifié), sans lien.
- Perf tick `full` s10→s30 [3 paires alternées, charge 5-8, bruitée] : HEAD 13,2 s →
  13,3 s (+0,8 %, dans le bruit).
- LDC : `croissance.py` 273, `mortalite.py` 250, `perturbations.py` 309, `instance.py`
  296, `embolie.py` 19, `bilan.py` 78.
- Pour ②③ : `_mort_dessechee` est le patron d'une mort par destruction consignée au
  log 🪦 (ajouter la phrase à `_raison_mort`) ; l'embolie de GEL-DÉGEL des ligneux
  (conception §5) n'est PAS faite — ② peut réutiliser `plant.embolie` (accumuler depuis
  le gel) et la même mort.

## REPRISE
① fait (non commité). Lire `CLAUDE.md`, ce fichier, l'`00_etat.md` du sprint A et de
`sprint_lisibilite_bilan` (hauteur acquise), la conception, puis le kickoff du premier
tronçon « à faire » (②). Golden courant `e24a23d8cb09…`. Lancer : `/sprint-auto sprint_stress_au_bilan`.
