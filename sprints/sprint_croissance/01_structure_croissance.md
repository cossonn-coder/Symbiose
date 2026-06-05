# Sprint Croissance·1 — Structure de segments + croissance Python (cœur, INERTE)

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> Carte blanche (conception figée) : implémente sans re-valider chaque étape,
> rends compte après. Français + pédagogie (Nico vient du C/Python embarqué,
> expert simulation ; débutant Godot/C# en frontend).

## Ce que c'est, en une phrase

Premier des 6 tronçons. On pose le **cœur** : chaque plante reçoit une **structure
de segments** (un arbre de branches) qui **pousse à chaque tick**, pilotée par
l'**auxine le long de la structure** + un **bornage** (le vieux bois tombe). **Mais
on ne câble RIEN à l'empreinte ni au rendu** : la structure grandit **à côté**, sans
encore être lue par `height_at`/le `LightField`. C'est l'équivalent du tronçon i1 de
la Vigueur/Maîtrise : on construit l'**état + la dynamique inerte** d'abord, on
**branche** ensuite (tronçon 2).

**Le golden écolo NE bouge PAS** (`6369c30b…` engine / `b005d9ba…` champ ; golden
réduit à **10 ans** le 2026-06-05, cf. `00_etat.md` — ancien hash 100 ans `c950f06c…`)
**à ce tronçon** : tant que personne ne **lit** la structure (l'empreinte vient encore des
stades), le tick produit le même résultat. Si un hash bouge ici, c'est une **fuite**
(quelque chose lit déjà la structure) → bug, pas un re-figeage. *(Le re-figeage
viendra au tronçon 2, quand on câblera l'empreinte.)*

## Lis d'abord, dans cet ordre

1. `data/code/CONCEPTION_CROISSANCE.md` — **§C** (modèle de données : le `Segment`,
   ses champs, accumulation **bornée**, déterminisme §C.2), **§D** (l'algorithme :
   §D.1 auxine le long de la structure — production apex / transport descendant /
   inhibition latérale / relâchement avec l'âge ; §D.2 allongement & émission ; §D.3
   débourrement ; §D.6 **bornage**). Survole §D.4 phototropisme (peut être **stubé
   neutre** ici si le `LightField` n'est pas encore branché — cf. périmètre), §E/§F/
   §G/§H (profil/seam/empreinte/rendu = tronçons 2-5, **hors périmètre ici**).
2. `sprints/sprint_croissance/00_etat.md` — découpage des 6 tronçons + points ouverts
   (dont les tiens : représentation du `Segment`, où loger la boucle).
3. Code — **le patron et les ancrages** :
   - `data/code/plants/base.py:114` `@dataclass PlantInstance` — y ajouter le champ
     `segments` (+ `__post_init__` : une plante naît avec **1 segment** = le collet/
     apex initial). Modèle de croissance actuel = `growth_stages` (annuelles) /
     `age_curve` (perennials.py) : **tu n'y touches pas** (c'est le tronçon 2 qui
     migrera l'empreinte).
   - `data/code/fields/noise.py` — **`_hash_noise`** (fondation déterministe) : **toute**
     décision pseudo-aléatoire (direction d'un segment, jitter d'angle, quel latéral
     débourre) passe par lui, alimenté par `(seed, x_cm, y_cm, age, segment_id)`. **Zéro
     RNG** (philo #3).
   - `data/code/sim/engine.py:306` — la maj de `growth_factor` dans la boucle de tick :
     c'est **à côté** que s'insère la croissance de structure (ou dans un module dédié
     `sim/growth.py` que le tick appelle — **point ouvert, défaut sobre = module dédié
     appelé par l'engine**, signale ton choix).
   - `data/code/tests/test_golden.py` — le garde-fou à NE PAS faire bouger.
   - `data/code/tests/test_vigueur.py` (section A, `check(name, cond, detail)`) — patron
     du golden joueur à cloner pour `tests/test_croissance.py`.

## Périmètre

### A. Le modèle `Segment` + `PlantInstance.segments`
Dataclass `Segment` (champs §C.1 : `parent`, `base`, `dir`, `length_cm`,
`thickness_cm`, `age_weeks`, `auxin`, `is_apex`, `organs=[]` — `organs` reste vide
ici, c'est le tronçon 5). `PlantInstance.segments: list[Segment]` ; à la naissance,
**un seul segment apex** au collet (`x_cm,y_cm,z=0`, `dir` vertical, `auxin=AUXIN_SOURCE`).
Champ `default_factory` pour ne pas casser les instances existantes.

### B. La dynamique de croissance (module `sim/growth.py` proposé)
Une passe par plante par tick (appelée par l'engine), **sans RNG**, dans l'ordre §D :
1. **Auxine** (§D.1) : production aux apex, transport descendant décroissant
   (`AUXIN_DECAY`), inhibition latérale sous `AUXIN_INHIB_THRESHOLD`, relâchement de
   la production avec l'âge (`× f(age/maturité)`) → moteur **permanent**.
2. **Allongement & émission** (§D.2) : l'apex allonge (`growth_speed · growth_factor ·
   saison`), émet un nouveau segment au-delà d'un seuil, épaissit le bois porteur.
3. **Débourrement** (§D.3) : un latéral dont l'auxine passe sous le seuil naît
   (direction = porteur tournée de `branch_angle` + jitter déterministe), devient apex.
4. **Bornage** (§D.6, **vital**) : segment trop vieux et sans apex actif **meurt**, le
   sous-arbre détaché **tombe** ; plafond `MAX_SEGMENTS` (élague les plus vieux
   improductifs). La structure reste **bornée par la taille de la plante**.
- **Constantes / leviers** (placeholders nommés, valeurs **plausibles** mais à
  calibrer, §L) : `AUXIN_SOURCE`, `AUXIN_DECAY`, `AUXIN_INHIB_THRESHOLD`,
  `growth_speed`, `branch_angle`, `wood_persistence`, `MAX_SEGMENTS`. Pour ce tronçon,
  ils peuvent être des **constantes de module** (le profil **par espèce** = tronçon 2).
- **Phototropisme** (§D.4) : **stub neutre** ici (croissance droite + jitter
  déterministe) — le biais `LightField` se branche quand l'empreinte est câblée
  (tronçon 2). Signale ce report.

### C. Test — `tests/test_croissance.py` (NEUF)
Patron golden joueur (déterministe, `check(...)`). Vérifie la **dynamique inerte** :
1. Une plante neuve a **1 segment apex** au collet.
2. Après N ticks de croissance libre (une espèce, constantes du module) : la structure
   **grandit** (nombre de segments ↑, hauteur de structure ↑), l'apex **domine** (peu
   de latéraux tant que l'auxine est haute).
3. **Débourrement** : si on force la chute d'auxine de l'apex (appel direct, pas encore
   `tailler`), des latéraux **naissent** ; la dominance se **rétablit** ensuite.
4. **Bornage** : sur un horizon long, le nombre de segments **sature** (≤ `MAX_SEGMENTS`),
   du vieux bois **tombe** — pas de croissance illimitée (run éternel).
5. **Déterminisme** : 2 runs même seed + même position → **structures identiques**.

## Hors périmètre (NE PAS faire ici)
Câblage à l'empreinte (`height_at`… → tronçon 2, c'est lui qui re-fige le golden).
Profil **par espèce** (tronçon 2). Phototropisme réel (tronçon 2). Seam/`tailler`
(tronçon 3). Rendu/organes (tronçons 4-5). Save (tronçon 6). Ne touche **pas** les
`growth_stages`/`age_curve` existants.

## Vérification (success criteria)
```
cd data/code
python3 -m tests.test_croissance     # nouveau, doit passer
python3 -m tests.test_golden         # DOIT rester 6369c30b… / b005d9ba…  (INTACT — structure non lue ; golden 10 ans)
python3 -m tests.test_genetique && python3 -m tests.test_auxiliaires
python3 main.py                      # tourne sans crash
```
Le golden intact est le critère dur **de ce tronçon** (la structure est inerte). Si
un hash bouge → fuite (quelque chose lit déjà la structure), corrige-la. Mets à jour
`00_etat.md` (tronçon 1 ✅ + points tranchés : forme du `Segment`, emplacement de la
boucle), commit, `/clear`, lance `02_*.md`.
