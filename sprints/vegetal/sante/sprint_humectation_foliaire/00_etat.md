# Sprint HUMECTATION FOLIAIRE — état vivant (`/conception`)

**Origine** : amorce D38 « rosée nocturne & hygrométrie de l'air » (2026-07-26).
**Phase courante** : B **FIGÉE** — doc de conception + 4 kickoffs autosuffisants
(01→04). **SPRINT TERMINÉ : tronçons ①②③④ TOUS EXÉCUTÉS (golden INCHANGÉ `57c166d8…`
dans les QUATRE).**
**Rangement** : `vegetal/sante` (et non `champs/climat` — cf. décision D3 ci-dessous).

---

## Q1 (BLOQUANTE) — RÉSOLUE par lecture du code, 2026-07-26

Verdict : **l'amorce se trompe de sujet.** Le reliquat de D38 n'est pas « poser une
hygrométrie de première classe » mais **corriger un proxy faux déjà en production**.

### (a) rosée — **CLOSE DE FAIT**, confirmé au code
`fields/ecofields/rosee.py` fait tout ce que la dette demandait :
- point de rosée calculé : `t_rosee = t_air − ECART_ROSEE_SEC(6.0) + GAIN_HUM_ROSEE(5.0)·hum_norm` ;
- **écrit bien dans `humidite`** (`rosee.py:84` — `eco.humidite.add(r, c, cond + gel)`) ;
- continuum liquide/givre + fonte différée (`eco.givre`) ;
- `rosee_last` consommé par **3** endroits : faune (`fields/population/resources.py:413`),
  captation foliaire (`sim/engine/croissance.py:284`), pont (`tools/simserver/serialize.py:441`).

Reliquats réels : rendu C# gouttes/givre (**D24**) + dégât foliaire du givre différé
(`GIVRE_SEVERITY_REF` réservée, `rosee.py:105-115`, bloqué par `_mediated_damage`
qui ne cible que le stade « semis »).

### (b) évaporation — **NE PAS TOUCHER** (voir décision D1)
`tick_hydrology` (`hydrologie.py:85-125`) porte déjà **trois** pilotes d'évaporation :
température (`EVAP_TEMP_COEF`), rayonnement (`EVAP_RAD_COEF·(1−nébulosité)`), vent
(`EVAP_WIND_COEF·vent[r,c]`), + rétention couverture/paillage.

### (c) maladie — **LE VRAI TROU, et il est déjà en production**
`sim/effects/perturbations.py:216` (fonction `fungal_disease`, pas `fungal_pressure`) :

```python
hum_norm = min(1.0, eco.humidite.at_plot(r, c) / 3.0)   # ← humidité du SOL
p = eco.disease_probability(r, c, base_rate=FUNGAL_BASE, family=plant.plant_class.family)
p *= hum_norm * (0.4 + density) * susc
p *= max(0.0, 1.0 - FUNGAL_VENT_DRY * min(1.0, vent_local))   # assèchement (VENT ⑥)
spore = _spore_load(...)                                       # dispersion (VENT ⑥)
```

`disease_probability` (`fields/ecofields/sol.py:118-144`) ne porte **que** microbiome +
inoculum familial — **aucun terme de vent** (l'amorce le supposait à tort ; le vent
agit dans `fungal_disease`, en aval).

**Le défaut** : l'humidité du **SOL** sert de proxy à l'humectation du **FEUILLAGE**.

---

## Décisions arrêtées

- **D1 — Le volet évaporation (H2 de l'amorce) est ABANDONNÉ.** Un terme VPD dérivé de
  (nébulosité, T_sol) serait un **double comptage** : `EVAP_RAD_COEF·(1−nébulosité)` et
  `EVAP_TEMP_COEF·(T−11°C)` sont déjà là, et le VPD n'est que leur produit croisé. On
  paierait un re-figeage golden **LARGE** sur la formule qui a déjà tué un pommier par
  asphyxie (D39) pour un terme d'interaction quasi nul. *Réduire le périmètre plutôt que
  casser* — `tick_hydrology` n'est PAS touché par ce sprint.
- **D2 — Pas de grandeur « hygrométrie » (H1 tranché hors des options A/B/C).** L'HR de
  l'air est un intermédiaire de calcul, pas un objet de jeu. L'objet de jeu est
  l'**humectation du feuillage**. Aucun `GridField` persistant neuf.
- **D3 — Rangement `vegetal/sante`** (Q9) : le sujet est une correction de la pression
  fongique, pas un champ climatique. Nom : `sprint_humectation_foliaire`.
- **D4 — H5 (brise-vent ambivalent) n'est PAS une question ouverte : c'est un fait
  accompli.** `fields/abri.py` écrit `eco.vent[r,c]` bas sous un brise-vent →
  `1 − FUNGAL_VENT_DRY·vent_local` remonte → maladie ↑. L'abri est **déjà** à double
  tranchant depuis le sprint VENT ⑥, sans que ce soit décidé. Q7 devient : assumer et
  **rendre lisible**, ou brider.

## Questions QA/QB/QC — RÉSOLUES (figées dans les kickoffs)

- **QA — OUI, c'est le cœur.** L'incohérence pédagogique `arroser` (ci-dessous) est
  corrigée par le tronçon ③.
- **QB — MAINTENANT.** La guilde oïdium est traitée dans ce sprint (tronçon ④).
- **QC — Moteur seul, AUCUNE espèce ajoutée** (prêle et vigne écartées, D26 du doc ;
  le porteur d'oïdium — la courgette — existe déjà au catalogue).

## Carte des tronçons (golden attendu)

- **① `wetness_memory`** — pose + alimente la mémoire d'humectation, lue par personne. **NEUTRE.**
  ✅ **FAIT** (golden INCHANGÉ `57c166d8…`). Champ sur `PlantInstance`, alimenté dans
  `_update_physiology` (rosée `capte` remontée hors garde, pluie/nébulosité passées par
  `boucle.py`, séchage vent+soleil, aération par `foliage_density_at`). Test
  `tests/test_humectation.py` (4 cas) vert. `croissance.py` = 204 LDC pur (🟢).
  **Écart kickoff assumé** : `foliage_density_at(plant)` au lieu de `plant_class.foliage_density`
  (None sur les herbacées → crash évité, valeur de repli par strate).
- **② bascule du proxy** — `fungal_disease` lit l'humectation foliaire au lieu de l'humidité-sol.
  ✅ **FAIT — golden INCHANGÉ `57c166d8…` (re-figeage PRÉVU mais NON survenu, expliqué ci-dessous).**
  Deux sites basculés `min(1,hum/3)` → `plant.wetness_memory` : `fungal_disease`
  (`perturbations.py:216`) et `infection_memory` (`croissance.py`). Bloc `wetness_memory`
  DÉPLACÉ avant `infection_memory` dans `_update_physiology` (mise à jour du tick courant
  avant lecture — pas de décalage d'un tick). `FUNGAL_VENT_DRY`/`_spore_load` intacts
  (double comptage vent assumé, D1 kickoff). `disease_probability` NON touché.
  Tests `test_humectation.py` étendus (a/b/c ②) — dont la non-régression du bug pédagogique
  (arroser au pied ne change plus la maladie). 11 suites ciblées vertes (dont `inoculum`,
  `senescence`, `plasticite`, `stress_chronique`). LDC : croissance 204, perturbations 249 (🟢).

  **POURQUOI le golden n'a PAS bougé** (vérifié empiriquement, pas une supposition) :
  1. `fungal_disease` ne déclenche **JAMAIS** dans le smoke 2 tuiles × 4 ans (0 ligne
     `maladie fongique` — p reste sous le bruit AVANT comme APRÈS). Donc aucun `vitalite`
     ni rondelle `maladie` ne change.
  2. `infection_memory` **change bien** (mesuré : p.ex. Minette `resistance_pathogene`
     exprimé 1.03 avant → 1.001 après ; toggle env comparant `hum/3` vs `wetness` = hash
     **byte-identique**). Son SEUL aval est `cout_defense()` → timing de stade + `heal`.
     L'écart de sur-expression (~0.03 → ~0.001) déplace `needed` de <0,5 % : sous la
     résolution qui ferait franchir une frontière de stade entière ou bouger un flottant
     digéré (`growth_factor`/`vitalite` restent bit-identiques pour TOUTES les plantes).
  → Correction **live et câblée** (wetness max 0.295, 2684 plant-semaines >0 dans le smoke),
    mais **neutre au digest** de ce smoke. Dérive LOCALISÉE à santé/plasticité, conforme au
    kickoff (rien sur hydro/nutriments/épaisseur). **Aucun re-figeage nécessaire.**
- **③ `arroser` pied/feuillage** — le geste rend le dilemme jouable. **NEUTRE.**
  ✅ **FAIT (golden INCHANGÉ `57c166d8…`).** Carte transiente `eco.aspersion_last`
  (patron `rosee_last`) posée par `arroser(feuillage=True)` (`gestes.py`), lue par le
  terme `ASPERSION_WET_GAIN` de l'humectation (`croissance.py::_update_physiology`) puis
  remise à plat par `tick_semaine` (`boucle.py`, étape **9b**). Défaut `feuillage=False`
  = au pied, comportement bit-identique (appelants inchangés). Coût IDENTIQUE dans les
  deux modes (§2.5). Pont : `params.feuillage` sur `arroser`, `ENGINE_VERSION` → **0.5.42**.
  Tests `test_humectation.py` étendus (③ a/b/c/d) — 11 suites vertes. LDC : croissance 212,
  gestes 235, boucle 269 🟢.
  **⚠️ Écart au kickoff (2 points, assumés) :**
  1. **Reset placé APRÈS `_update_physiology` (étape 9b), pas AVANT.** Le kickoff disait
     « avant `_update_physiology` ». Faux pour une transiente PRODUITE HORS TICK : le geste
     s'applique ENTRE deux ticks (cmd_action / automate après `tick_semaine`, invariant H2),
     donc l'aspersion est déjà écrite quand le tick démarre ; un reset EN TÊTE l'effacerait
     avant que l'humectation la lise → le geste n'aurait JAMAIS d'effet. Reset côté
     CONSOMMATEUR (après lecture) → l'aspersion vit exactement le tick qui suit le geste.
  2. **`DOSE_ARROSAGE` DÉPLACÉ** de `sim/actions/gestes.py` vers `fields/ecofields/constants.py`
     (ré-importé par gestes.py, API `sim.actions.DOSE_ARROSAGE` inchangée). Cause : l'import
     de `sim.actions.gestes` par `sim.engine.croissance` (voulu par le kickoff pour la
     normalisation `aspersion / DOSE_ARROSAGE`) crée un CYCLE engine→actions→world→sim.
     Constante logée bas-couche = une seule source de vérité, pas de cycle, pas de drift.
- **④ guilde oïdium** — la courgette, exception qui interdit la solution unique.
  ✅ **FAIT — golden INCHANGÉ `57c166d8…` (neutralité PROUVÉE empiriquement, pas supposée).**
  Attribut ADDITIF `oidium_susceptibility` sur `PlantBase` (défaut 0.0, à côté de
  `fungal_susceptibility`) ; porteurs : **courgette 0.9** (Cucurbitaceae, cas d'école,
  hors smoke) + **pommier 0.3** (`AppleTree`, Rosaceae — tavelure ET oïdium). Constantes
  `OIDIUM_BASE/T_REF/T_SPAN` (`ecofields/constants.py`, exportées `fields/__init__`).
  Fonction `oidium_disease` (miroir de `fungal_disease`, signal **INVERSE**
  `(1−wetness_memory)×chaleur`, canal `week·47`, PAS de FUNGAL_VENT_DRY — le vent
  n'assèche pas l'oïdium, c'est le dilemme). Branchée en **chronique** dans
  `apply_disturbances` (capée comme le mildiou), export `effects/__init__`. `resistance_pathogene`
  médie les deux guildes (aucun gène neuf). Tests `test_humectation.py` étendus (④ a/b/c/d —
  dont **le test du dilemme** : à chaleur égale, mouillé→mildiou 27/oïdium 2, sec→mildiou 2/oïdium 22,
  les guildes s'inversent). LDC perturbations : **273 pur 🟢** (< 300, aucun refactor).
  **⚠️ Point critique du kickoff RÉSOLU — le pommier EST dans le smoke golden.** Le kickoff
  offrait deux options (pommier→0.0 OU re-figeage sur autorisation). J'ai testé
  **empiriquement** pommier=0.3 → **golden byte-identique `57c166d8…`** : `oidium_disease`
  ne franchit jamais le seuil sur le pommier du smoke (gate T>18 °C × feuillage sec × densité
  familiale). Donc la 3ᵉ voie s'ouvre : **guilde à 2 porteurs ET golden neutre**, sans
  re-figeage. Valeur 0.3 = placeholder → **calibrage F5** possible. 11+4 tests
  `test_humectation` verts ; suites `inoculum`/`stress_chronique`/`plasticite` vertes.
- *Pas de tronçon vue Godot : sprint moteur pur ; le visible (gouttes/givre) = D24, déjà tracé.*

## L'incohérence pédagogique (argument central, à valider par Nico)

`sim/actions/gestes.py:162-189` — `arroser` n'écrit **que** `eco.humidite` (un seul
mode, pas de choix pied/feuillage). Enchaînement actuel :

> `arroser` → `humidite` ↑ → `hum_norm` ↑ → `fungal_disease` ↑

Le joueur qui sauve une plante de la sécheresse **la rend malade**, par un chemin
biologiquement **faux** : en vrai, arroser *au pied* ne mouille pas le feuillage et
n'ouvre pas la porte au mildiou. Le modèle enseigne aujourd'hui l'inverse de la bonne
pratique permacole (« arrose au pied, jamais sur les feuilles ») → **violation dormante
de philo #6**. C'est le vrai reliquat de D38, et il justifie le sprint à lui seul.

## Coût perf estimé

Négligeable et **borné O(N plantes)** : l'humectation est une float par plante
(patron `drought_memory`/`wind_memory`), lue/écrite dans la boucle physiologie déjà
existante. Aucune passe de champ neuve, aucun O(N²).
**Interdit d'emblée** (Q8 de l'amorce) : humectation par segment/organe (D29).

## Canaux `_hash_noise` — inventaire vérifié au grep

Utilisés : `week·`{0, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 53, 59}.
`week·43` réservé D41 (non consommé). **Libres : 47, 61, 67.**
Note : `fungal_disease` tire sur `week·13`.

## §REPRISE

À lire : `CLAUDE.md` + ce fichier. Puis, si besoin de re-vérifier :
`sim/effects/perturbations.py:179-224` (`fungal_disease`), `fields/ecofields/sol.py:118`
(`disease_probability`), `fields/ecofields/rosee.py`, `sim/actions/gestes.py:162`.

**Prochaine étape** : **SPRINT TERMINÉ.** ①②③④ CLOS (golden inchangé `57c166d8…` dans les
quatre). ④ a livré la guilde oïdium (attribut `oidium_susceptibility`, `oidium_disease`
signal inverse, 2 porteurs courgette 0.9 / pommier 0.3, canal `week·47`) — aucune espèce
ajoutée, aucun gène neuf, aucun re-figeage. NON COMMITÉ par le sous-agent ④ (commit =
orchestrateur/Nico).
**F5 Nico restant** :
- ③ : TOGGLE pied/feuillage sur `arroser` côté vue Godot (`params.feuillage`, pont 0.5.42).
- ④ : **calibrer `oidium_susceptibility` du pommier** (0.3 = placeholder ; libre de le
  monter APRÈS F5, mais alors vérifier le golden — au-delà d'un certain seuil × chaleur il
  pourrait franchir sur le pommier du smoke et demander un re-figeage annoncé). La courgette
  (0.9, hors smoke) est le vrai porteur pédagogique.
- Rendu C# des signes `oïdium` (feutrage blanc) : hors périmètre moteur, à tracer si absent
  du mapping `PlantRenderer` (cf. reliquat D24 gouttes/givre du ①).
