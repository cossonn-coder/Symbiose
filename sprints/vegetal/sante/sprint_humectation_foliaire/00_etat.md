# Sprint HUMECTATION FOLIAIRE — état vivant (`/conception`)

**Origine** : amorce D38 « rosée nocturne & hygrométrie de l'air » (2026-07-26).
**Phase courante** : B **FIGÉE** — doc de conception + 4 kickoffs autosuffisants
(01→04). **Tronçons ①② EXÉCUTÉS (golden INCHANGÉ dans les DEUX). Reste ③④.**
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
- **④ guilde oïdium** — la courgette, exception qui interdit la solution unique.
  **NEUTRE — à prouver.**
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

**Prochaine étape** : tronçons ①② CLOS (golden inchangé `57c166d8…` dans les deux ;
pour ②, le re-figeage était prévu mais NON survenu — smoke n'exerce pas le déclenchement
fongique, et l'aval de `infection_memory` est sous-résolution ; explication vérifiée
ci-dessus). Reprendre au **③** (`03_*.md`) : `arroser` pied/feuillage — rend le dilemme
jouable, golden attendu NEUTRE. `wetness_memory` est désormais **lue** par les deux sites
de pression fongique ; le ③ ajoutera un mode feuillage à `arroser` (écrira l'humectation
via un `aspersion_last`, cf. `ASPERSION_WET_GAIN` réservé au ①).
