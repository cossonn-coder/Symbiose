# Tronçon ⑦ — Catalogue météo : Neige + Orage + manteau neigeux

> Sprint thermique-microclimat. Conception : `docs/conception/CONCEPTION_THERMIQUE_MICROCLIMAT.md`.
> Kickoff **autosuffisant** (relançable à froid).
> Pré-requis : ⑥ CLOS (gel nocturne localisé ; helper `t_min_nuit_at` dans
> `fields/ecofields/thermique.py` ; knob `RAYONNEMENT_NOCTURNE=5.0` ; golden
> NEUTRE car le smoke ne gèle jamais — hash inchangé `b1173a78…`).

## Objectif

Le catalogue météo (`sim/weather.py::_CATALOGUE`) n'a pas de **Neige** ni
d'**Orage**. Ce tronçon les ajoute comme vrais événements **et** branche le
**manteau neigeux** — le point laissé en attente au ⑥ (commentaire « + neige ⑦ »
dans `t_min_nuit_at`). Premier émergent recherché : **la neige ISOLE le sol**
(effet igloo — un manteau de neige protège du gel nocturne, contre-intuitif mais
réel), en s'ajoutant au couvert de litière dans `T_min_nuit`. L'Orage, lui, est
un événement composite violent (pluie battante + vent) de fin de printemps/été.

## ⚠️ Dérive golden attendue : re-figeage MAÎTRISÉ **LARGE**

Contrairement à ⑥ (neutre), ⑦ **modifie le tirage météo** : ajouter des entrées
à `_CATALOGUE` change la liste `cands` (candidats de la saison) dans `weather_at`
→ l'index `int(pick * len(cands))` se décale → **tous** les événements des
fenêtres saisonnières chevauchant Neige/Orage changent (pas seulement les
nouvelles semaines Neige/Orage). C'est la dérive « météo (tirages) » annoncée au
`00_etat.md`. **Re-figeage attendu et large** — tracer la cause (nouveau
catalogue), pas un bug. Garder le déterminisme (aucun RNG live).

## Modèle

### A. Catalogue (`sim/weather.py`)

Ajouter 2 entrées à `_CATALOGUE` (kind, scope, durée, fenêtre week_in_year ;
calendrier moteur : printemps 1-13, été 14-26, automne 27-39, hiver 40-52) :

```python
("Neige",  "global", 2, (44, 52)),   # cœur de l'hiver (état multi-semaines)
("Orage",  "local",  1, (16, 30)),   # été (orages convectifs)
```

- **Neige** : delta de température FROID. Ajouter à `TEMP_DELTA_BASE` :
  `"Neige": -6.0` (la neige tombe sous 0 → entre dans `TEMP_DRIVEN`, donc PAS
  d'effet `WEATHER_ALEA` en plus, comme Gelée/Canicule/Redoux). Elle déclenchera
  le gel nocturne via `temp_now < TEMP_FROST_DAMAGE` ET dépose le manteau (§B).
- **Orage** : NON thermique (delta 0) → garde une voie `WEATHER_ALEA`. C'est un
  composite : pluie battante (humidité ↑) **et** vent (paillage dispersé). Le
  modèle `Alea` actuel ne porte qu'UN effet ; le plus surgical = router l'Orage
  comme la **Tempête** (paillage −1) MAIS avec en plus l'humidité. Deux options :
  - **(a)** réutiliser tel quel l'`Alea` Tempête (paillage −1) — simple, mais
    perd la pluie. **À éviter** (Orage ≡ Tempête serait redondant).
  - **(b) préférée** : dans `boucle.py`, traiter `Orage` comme un cas qui
    applique DEUX aléas (humidité +0.5 puis paillage −1) — ou ajouter un champ
    `extra` à `Alea`. **Le plus simple et lisible : 2 entrées appliquées en
    séquence.** Décrire en commentaire que l'Orage = pluie + vent.
  Ajouter dans `WEATHER_ALEA` (aleas.py) au moins l'effet pluie de l'Orage ;
  câbler le vent dans `boucle.py` à côté (cf. branche `elif event.kind not in
  TEMP_DRIVEN` qui lit `WEATHER_ALEA[event.kind]`). **Choisir l'option la plus
  surgicale et l'annoncer à Nico.**

### B. Manteau neigeux (la pièce neuve = un état persistant)

La neige doit **persister entre les ticks** (elle s'accumule puis fond) → c'est
un nouvel **état** sur `eco`. Modèle proposé (le plus simple, à valider) :
**scalaire `eco.snow ∈ [0,1]` par tuile** (manteau uniforme — la neige tombe sur
toute la tuile). Pas un `GridField` (over-engineering pour l'instant ; la
modulation par couvert/canopée = raffinage futur, le noter).

- **Accumulation** : si l'événement du tick est `Neige`, `snow = min(1, snow +
  SNOW_ACCUM)` (knob `SNOW_ACCUM ≈ 0.5`).
- **Fonte** : sinon, `snow = max(0, snow − SNOW_MELT_BASE − SNOW_MELT_WARM ·
  max(0, temp_now − 0))` — fond lentement au froid, vite au redoux/dégel
  (couplage température, knobs `SNOW_MELT_BASE ≈ 0.05`, `SNOW_MELT_WARM ≈ 0.03`).
- **Où** : un nouveau pas `tick_snow(temp_now, is_neige)` sur le conteneur eco,
  appelé dans `boucle.py` **AVANT** le bloc gel (le gel lit le manteau du tick)
  — ou juste après le calcul de `temp_now`/`event`. PUR, déterministe.
- **Init** : `snow = 0.0` au démarrage ; persister dans le snapshot/save si un
  pont l'expose (sinon no-op).

### C. Branchement dans le gel nocturne (le rendez-vous du ⑥)

Dans `t_min_nuit_at` (thermique.py), le couvert intègre ENFIN le manteau :

```python
couvert = min(1.0, eco.om_fresh_at(r, c) / LITIERE_REF + eco.snow)
```

→ sous un bon manteau neigeux (`snow` proche de 1), `couvert → 1`, le sol ne
rayonne plus, `T_min_nuit → T_air` : la neige PROTÈGE du gel (effet igloo). Le
helper reste PUR (lit `eco.snow`, ne l'écrit pas). Retirer le commentaire
« + manteau neigeux ⑦ » posé au ⑥.

### D. Signes + nébulosité (déjà partiellement prêts)

- `NEBULOSITE` (constants.py) a **déjà** `Orage: 0.85` et `Neige: 0.70` (posés
  au ④) → la thermique diurne les gère sans toucher. Rien à faire côté nébul.
- Ajouter Neige + Orage à `SIGN_TABLE` (weather.py §4, voix naturaliste). Sans
  entrée, `weather_signs` lèvera un KeyError dès qu'ils sont tirés. Proposition :
  - `"Neige"`: ("ciel bas et ouaté", "silence feutré, sons étouffés", "air qui
    pique et sèche").
  - `"Orage"`: ("chaleur lourde et moite", "cumulus qui bourgeonnent en tours",
    "premiers grondements lointains").

## Étapes

1. **`sim/weather.py`** — 2 entrées `_CATALOGUE` ; `TEMP_DELTA_BASE["Neige"] =
   -6.0` (entre dans `TEMP_DRIVEN` automatiquement) ; 2 entrées `SIGN_TABLE`.
2. **`fields/ecofields/constants.py`** — knobs `SNOW_ACCUM`, `SNOW_MELT_BASE`,
   `SNOW_MELT_WARM` (bloc « Gel nocturne », commentés).
3. **conteneur eco** (`fields/ecofields/container.py` ou le bon module — `snow`
   est un attribut d'état : l'initialiser à 0.0 et exposer `tick_snow`). ⚠️
   `container.py` est à ~359 ldc — si l'ajout dépasse le seuil, **sortir
   `tick_snow` en helper pur dans `thermique.py`** (comme la T_sol au ①) et ne
   laisser qu'une fine délégation dans le conteneur. Signaler le choix.
4. **`fields/ecofields/thermique.py`** — `couvert += eco.snow` (cf. §C), retirer
   le TODO neige.
5. **`aleas.py`** — entrée(s) `WEATHER_ALEA` pour l'Orage (pluie ; vent câblé en
   `boucle.py`).
6. **`sim/engine/boucle.py`** — appeler `eco.tick_snow(...)` (avant le gel) ;
   gérer l'Orage composite (pluie + vent) dans la branche météo non-thermique.
7. **Golden** — `python3 -m tests.test_golden`. **Échec LARGE attendu** (tirages
   météo décalés). Tracer (logs Neige/Orage, manteau qui s'accumule/fond) puis
   re-figer (`--capture`).
8. **Suites ciblées** : `test_croissance`, `test_eau`, `test_genetique`,
   `test_population` doivent rester PASS (le nouveau catalogue ne touche ni la
   génétique ni l'eau directement). S'il existe un test météo qui code en dur la
   liste des kinds, le recalibrer (raconter, ne pas neutraliser).

## Invariant golden

- **Dérive attendue LARGE** : nouveau catalogue → tirages météo décalés sur les
  fenêtres été/hiver → cascade complète (traçable au changement de `cands`).
- **Doit rester** : déterminisme (météo PURE, manteau déterministe), `weather_at`
  toujours pure, snapshot inchangé hors `snow`. La thermique diurne (④) gère déjà
  Neige/Orage via NEBULOSITE → pas de surprise diurne.

## Validation

- `python3 -m tests.test_golden` re-figé (hash noté dans `00_etat.md`).
- `python3 main.py 3` exit 0, scores affichés.
- Vérif mécanisme (print jetable, réutiliser `tests.test_golden.build_world` +
  `Engine`) : (a) après une semaine `Neige`, `eco.snow > 0` ; (b) à manteau haut,
  `t_min_nuit_at` d'un plot remonte vers `t_air` même sans litière (igloo) ;
  (c) sans Neige, `snow` décroît, plus vite si `temp_now` élevé (dégel).

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (⑦ ✅ + nouveau hash + ampleur de la dérive +
  recalibrage éventuel d'un test météo).
- Commit : `feat(thermique) : tronçon ⑦ catalogue Neige + Orage + manteau neigeux (effet igloo) — golden RE-FIGÉ MAÎTRISÉ`.
- Écrire le kickoff `08_snapshot_meteo.md` avant le `/clear` (snapshot météo +
  carte température exposés au pont Python→Godot ; dérive NEUTRE = vue).
```
