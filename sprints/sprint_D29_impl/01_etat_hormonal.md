# Sprint D29·i1 — État hormonal : 2 scalaires + trait `reponse_taille` (Python)

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> Carte blanche (conception figée) : implémente sans re-valider chaque étape,
> rends compte après. Français + pédagogie (Nico vient du C/Python embarqué,
> expert simulation ; débutant Godot/C# en frontend).

## Ce que c'est, en une phrase

Premier des 3 tronçons de l'implémentation D29. On pose la **fondation** : les
**2 scalaires hormonaux** sur `PlantInstance` et le **trait `reponse_taille`** sur
`PlantBase`, **rien d'autre**. Aucune cinétique, aucune lecture nouvelle dans le
tick, aucune action `tailler` (c'est i2/i3). Ici on ne fait qu'**ajouter de l'état
inerte avec des défauts neutres**, exactement comme on ajoute un champ à une
dataclass sans encore le brancher.

**Le golden écolo NE bouge PAS** (`c950f06c…` engine / `b005d9ba…` champ). À ce
stade c'est **trivial à garantir** : on ajoute des champs que **personne ne lit
encore**. Si un hash bouge ici, c'est qu'un défaut a fui dans un chemin de
sérialisation/égalité lu par le golden → bug.

## Lis d'abord, dans cet ordre

1. `data/code/CONCEPTION_HORMONES.md` — **§C.1** (l'état nouveau : les 2 champs,
   défauts `1.0`/`0.0`), **§C.2** (pourquoi 2 et pas 1), **§C.3** (repos neutre =
   critère golden #1), **§F** (trait `reponse_taille`, archétype string, défaut
   `"insensible"`). Survole §C.4/§D (mapping/action = i2/i3, **hors périmètre ici**).
2. `sprints/sprint_D29_impl/00_etat.md` — le découpage des 3 tronçons.
3. Code — **le patron à copier** :
   - `data/code/plants/base.py:115` — `@dataclass class PlantInstance` (où ajouter
     les 2 scalaires, à côté de `growth_factor: float = 1.0`).
   - `data/code/plants/base.py:254` — `class PlantBase(ABC)` et ses traits-archétypes
     existants `life_cycle`/`winter_strategy`/`archetype` (lignes 274-277) : c'est
     **exactement** le motif à reproduire pour `reponse_taille`.

## Périmètre — `plants/base.py` (+ test neuf)

### A. `PlantInstance` (dataclass, base.py:115)
Deux champs, **après** les champs d'état existants, defaults = repos NEUTRE (§C.1) :
```python
dominance_apicale: float = 1.0   # signal hormonal TRANSITOIRE (apex intact = 1.0)
ramification:      float = 0.0   # état architectural CUMULATIF persistant
```
Si `PlantInstance` a un `clone()`/copie ou une (dé)sérialisation
(`to_dict`/`from_dict`), **propage les 2 champs** (round-trip identité). Vérifie
sinon que la dataclass les copie déjà (champs simples → `replace`/`asdict` ok).

### B. `PlantBase` (base.py:254)
Un trait de classe, sur le modèle de `life_cycle`/`archetype` :
```python
reponse_taille: str = "insensible"   # défaut : aucune réponse hormonale (golden-safe)
```
**Ne touche encore aucune espèce** (Tomato/AppleTree = i3). Tout le catalogue hérite
du défaut `"insensible"` → comportement strictement inchangé.

### C. Test de neutralité — `tests/test_hormones.py` (NEUF)
Patron golden joueur (cf. `tests/test_vigueur.py` section A : `check(name, cond,
detail)`, contrats déterministes sans RNG). Vérifie **seulement la fondation** :
1. Une `PlantInstance` fraîche a `dominance_apicale == 1.0`, `ramification == 0.0`.
2. Toute classe du catalogue a `reponse_taille == "insensible"` (aucune migrée).
3. Si clone/sérialisation existe : round-trip préserve les 2 scalaires.
4. **No-op golden** : importer et instancier ne change rien — réutilise le test de
   neutralité golden existant si présent, sinon documente que le golden est lancé
   à part (étape de vérif ci-dessous).

## Hors périmètre (NE PAS faire ici)
Cinétique/mapping dans le tick (i2). Action `tailler` (i3). Migration Tomato/
AppleTree (i3). Marqueur `🌿` (plus tard). Aucun `_hash_noise`, aucun coefficient.

## Vérification (success criteria)
```
cd data/code
python3 -m tests.test_hormones      # nouveau, doit passer
python3 -m tests.test_golden        # DOIT rester c950f06c… / b005d9ba…  (INTACT)
python3 -m tests.test_genetique && python3 -m tests.test_auxiliaires   # non-régression
python3 main.py                     # tourne sans crash
```
Le golden intact est le critère dur. Mets à jour `00_etat.md` (i1 ✅ + ce qui a été
fait/tranché), puis commit, puis `/clear`, puis lance `02_cinetique.md`.
