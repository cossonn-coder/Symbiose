# Tronçon ② — Pont : signaux phénologiques par-plante pour la vue (PYTHON)

> Kickoff autosuffisant. Lis `CLAUDE.md` (racine) + `00_etat.md` (ce dossier) +
> `docs/vegetal/floraison/conception_desync_phenologie.md` (§1bis, §5 tronçon ②), puis
> exécute. Lancement des tests depuis `data/code/`.
> **Prérequis : tronçon ① CLOS** (désync moteur en place, `w` = semaine
> d'abscission par-plante existe dans `sim/engine/decompo.py`).

## Objectif
Exposer dans le snapshot deux **hints de rendu par-plante** que la vue Godot ③
consommera pour désynchroniser fleurs et teinte automnale, aujourd'hui recalées
sur la **saison globale** (cf. doc §1bis) :
- `floraison` — le **scalaire moteur** `p.floraison ∈ [0,1]` (existe déjà,
  `sim/engine/floraison.py:85`), simplement pas encore exporté.
- `automne` — une **phénophase de coloration ∈ [0,1]** par-plante, rampe montante
  vers la **semaine d'abscission propre** de la plante (même tempo gène que ①).

## Principe (NE PAS dévier)
- **Golden INTACT.** Ces deux clés sont des **hints PUR RENDU** hors
  `_PLANT_ATTRS` — comme `leaf_symptoms`, `organ`, `fruits`, `foliage_density`
  déjà présents (`tools/simserver/serialize.py`, bloc `base[...]` autour des
  lignes 170-182). Le snapshot n'est PAS figé par `test_golden` → aucune dérive
  attendue. Si le golden bouge, tu as touché un état moteur par erreur → corrige.
- **Aucun recalcul, aucune duplication de formule** (règle projet). La semaine
  d'abscission est déjà calculée dans `_abscission` (①) : **factorise-la** en une
  fonction pure réutilisable, appelée par ① ET par le pont (cf. A ci-dessous).
- **NE PAS toucher `foliage_density_at`** (`plants/base/familles.py:297`,
  `plants/perennials.py:109`) : il sert la **sim** (`fields/light.py`), pas que la
  vue. On lit son résultat déjà exporté (`base["foliage_density"]`), on n'y touche
  pas.
- **Déterministe, zéro RNG.** Tout dérive du gène `phenologie_florale` et de
  `week_in_year`.

## A. Factoriser la semaine d'abscission (anti-duplication)
Dans `sim/engine/decompo.py`, extraire la formule par-plante de ① en **fonction
pure module-level** (à côté de `_abscission`), p. ex. :
```python
def semaine_abscission(g: float) -> int:
    """Semaine d'abscission propre à un individu de tempo `g` (gène
    `phenologie_florale`). g>1 = précoce → largue plus tôt. Bornée à la
    fenêtre d'automne. Fonction PURE (déterministe) — partagée par le garde
    d'abscission (moteur) et le pont (hint `automne`), pas de duplication."""
    w = round(ABSCISSION_BASE - ABSCISSION_JITTER * (g - 1.0))
    return max(ABSCISSION_MIN, min(ABSCISSION_MAX, w))
```
- Remplace le calcul **inline** de `w` dans `_abscission` par un appel à cette
  fonction (refactor PUR : mêmes valeurs → **golden inchangé**, ① déjà re-figé).
- Les constantes `ABSCISSION_*` vivent dans `fields/ecofields/constants.py` (①) :
  importe-les dans `decompo.py` si ce n'est pas déjà le cas.

## B. Exporter `floraison` (scalaire moteur)
Dans `tools/simserver/serialize.py`, dans le bloc `base[...]` par-plante (près de
`base["vitalite"]` / `base["organ"]`, ~ligne 170-182) :
```python
base["floraison"] = round(p.floraison, 3)
```
Commente : hint PUR RENDU (③ dessinera les fleurs ∝ ce scalaire, remplaçant le
proxy saisonnier `base["organ"]`). Lecture pure d'un état déjà porté par
l'instance → golden NEUTRE.

## C. Exporter `automne` (phénophase de coloration par-plante)
Toujours dans le même bloc de `serialize.py`. La semaine courante est disponible
localement : `week_in_year` (calculée `serialize.py:82`). Constante de rampe à
poser près des autres hints (ou dans `constants.py` si plus cohérent) :
```python
AUTOMNE_RAMP = 6   # semaines de coloration progressive avant l'abscission
```
Calcul par-plante :
```python
from sim.engine.decompo import semaine_abscission   # (import en tête de module)
...
# `automne` ne concerne QUE les caducs : un persistant ne rougit pas.
if getattr(cls, "deciduous", False):
    g = p.gene("phenologie_florale")
    w = semaine_abscission(g)
    automne = (week_in_year - (w - AUTOMNE_RAMP)) / AUTOMNE_RAMP
    base["automne"] = round(max(0.0, min(1.0, automne)), 3)
else:
    base["automne"] = 0.0
```
- `deciduous` est un attribut de classe d'espèce (`plants/species/*.py`,
  `plants/perennials.py` ; défaut prudent `False` pour les herbacées/persistants).
  `cls` est la classe d'espèce dans ce bloc de sérialisation (même `cls` que
  `cls.foliage_density_at`). Vérifie le nom exact de la liaison locale.
- Sémantique : `automne = 0` tout l'été (vert), monte linéairement sur les
  `AUTOMNE_RAMP` semaines qui précèdent `w`, atteint `1` à `w` (feuillage pleinement
  viré, juste avant largage). Après `w`, `foliage_density` (déjà exporté) chute →
  la feuille disparaît, `automne` reste borné à 1 sans effet.

## Golden — INTACT (garde)
1. `python3 -m tests.test_golden` doit **PASSER SANS re-figeage**. Les trois clés
   ajoutées sont des hints hors `_PLANT_ATTRS` ; le snapshot n'est pas dans le
   digest. **Si le golden échoue, c'est une régression** (tu as modifié un état
   moteur ou la sortie figée) → corrige, ne re-fige PAS.
2. Le refactor A (extraction `semaine_abscission`) doit laisser le golden
   **identique** (même valeurs qu'inline en ①).

## Vérif de sortie
- `python3 main.py` tourne sans crash.
- `python3 -m tests.test_golden` **PASSE inchangé**.
- Inspecter un snapshot (via `tools/export_structure.py` ou le banc habituel) :
  vérifier que `floraison` et `automne` apparaissent par-plante, valeurs plausibles
  (`automne` = 0 en été, > 0 à l'approche de l'automne pour un caduc, 0 pour un
  persistant ; `floraison` ∈ [0,1]).
- Mettre à jour `00_etat.md` (§REPRISE + statut ② CLOSE, confirmer golden intact),
  puis commit.

## Ne PAS faire
- Ne PAS toucher `foliage_density_at` ni la porte photopériode.
- Ne PAS re-figer le golden (② est golden-NEUTRE par construction).
- Ne PAS dupliquer la formule d'abscission (une seule fonction pure partagée).
- Ne PAS introduire de RNG.
- Ne PAS lancer `test_epaisseur_500ans` (interdit : long et inutile).
- Ne PAS toucher au C# (c'est le tronçon ③).
