# Sprint Croissance·2 — Profil par espèce + dérivation d'empreinte (tomate, re-figeage)

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> Carte blanche (conception figée) : implémente sans re-valider chaque étape,
> rends compte après. Français + pédagogie (Nico vient du C/Python embarqué,
> expert simulation ; débutant Godot/C# en frontend).
>
> Tronçon **moyen-gros** : il touche plusieurs fichiers **couplés** (profil +
> interface empreinte + croissance + golden). C'est une **synchro cohérente**
> assumée (l'exception « un fichier à la fois » est levée pour ce tronçon).

## Ce que c'est, en une phrase

Deuxième des 6 tronçons. Au tronçon 1 la structure de segments **pousse mais
personne ne la lit** (l'empreinte vient des stades → golden intact). Ici on
**branche le fil** : on donne à chaque espèce un **profil de croissance** (§E,
nouveaux attributs de classe), on **calibre la tomate** (démonstratrice) sur ses
stades actuels, et on fait **dériver l'empreinte** (`height_at`/
`canopy_radius_at`/`root_radius_at`) **de la structure** pour la tomate (§G). Le
`LightField` lit toujours les mêmes méthodes — on change la **source**, pas le
contrat. Conséquence assumée : **le golden bouge** pour la tomate → **re-figeage
légitime** (PAS une fuite, cf. tronçon 1). Les **13 autres espèces gardent
l'ancien chemin** → migration **incrémentale** (§I).

## La bascule mentale vs tronçon 1

| | Tronçon 1 | Tronçon 2 (ici) |
|---|---|---|
| Structure lue ? | non (inerte) | **oui, pour la tomate** |
| Golden | **INTACT** (`6369c30b…`) | **RE-FIGÉ** (re-capture après validation) |
| Leviers de croissance | constantes de module (`growth.py`) | **profil PAR ESPÈCE** (attributs de classe) |
| Critère dur | golden intact | **allure préservée** (empreinte ≈ gabarit stades) **puis** fige |

> ⚠️ **Golden réduit à 10 ans** (2026-06-05) : réf. courante `6369c30b…`
> (engine) / `b005d9ba…` (population). La sénescence du pommier (~70 ans) n'est
> plus exercée — non concerné ici. Tu **re-captureras** l'engine en fin de
> tronçon, **après** validation numérique de l'allure.

## Lis d'abord, dans cet ordre

1. `data/code/CONCEPTION_CROISSANCE.md` — **§E** (le profil par espèce : E.1 le
   schéma d'attributs, E.2 les archétypes de port, **E.3 reliure à l'existant =
   « reproduire l'allure d'abord, enrichir ensuite »**, E.4 le catalogue — seules
   tomate à détailler ici), **§G** (dérivation d'empreinte : ce que produit chaque
   classmethod), **§I** (stratégie de re-figeage maîtrisé, migration espèce par
   espèce). Survole §F/§H (seam/rendu = tronçons 3-5, **hors périmètre**).
2. `sprints/sprint_croissance/00_etat.md` — état + tes points ouverts (forme du
   cache d'empreinte ; ordre de migration).
3. `sprints/sprint_croissance/01_structure_croissance.md` — ce qui a été posé au
   tronçon 1 (modèle `Segment`, `grow_plant`, leviers de module).
4. Code — **les ancrages** :
   - `data/code/plants/base.py:333-359` — les **4 classmethods d'empreinte** sur
     `PlantBase` (`height_at`/`canopy_radius_at`/`root_radius_at`/
     `foliage_density_at`), qui lisent aujourd'hui `inst.stage`. **C'est ici que
     se branche la dérivation.** Attributs de classe existants : `base.py:307-329`.
   - `data/code/plants/perennials.py:55-72` — comment les **pérennes** surchargent
     déjà ces méthodes (via `age_curve`). **Modèle** du polymorphisme à respecter :
     n'ajoute pas un 3ᵉ chemin parallèle, **insère** la voie procédurale dans le
     même contrat.
   - `data/code/plants/species.py:27-60` (`class Tomato`) — ses `growth_stages` :
     `canopy_height` 3→25→40 cm, strate `sol`/`basse`/`basse` (rayon défaut basse =
     30 cm, cf. `STRATE_DEFAULTS` `base.py:72`). **Cibles de calibration.**
   - `data/code/sim/growth.py` — les **constantes de module** (`GROWTH_SPEED`,
     `MAX_REACH_CM`, `AUXIN_*`, `BRANCH_ANGLE`…) : à **promouvoir en profil** (lues
     depuis `plant.plant_class`, avec ces valeurs comme **défauts** sur `PlantBase`).
   - `data/code/tests/test_golden.py` — le golden à **re-capturer** (`--capture`)
     en fin de tronçon, après validation.
   - `data/code/tests/test_croissance.py` — golden de structure du tronçon 1 ; à
     **étendre** (allure d'empreinte de la tomate), pas à casser.

## Périmètre

### A. Le profil de croissance §E — attributs de classe sur `PlantBase`
Ajoute le schéma §E.1 comme **attributs de classe** sur `PlantBase` (`base.py`),
avec des **défauts génériques** = les valeurs de module du tronçon 1 (pour que les
espèces non migrées poussent comme avant) : `growth_speed`, `port_archetype`,
`apical_dominance_base`, `branch_angle`, `phototropism_gain` (inutilisé tant que
le phototropisme est stubé — réserve la place), `wood_persistence`, `max_height_cm`,
`max_extent_cm`, `organ_site`. Puis **`grow_plant` lit ces attributs** depuis
`plant.plant_class` au lieu des constantes de module (les constantes deviennent
les défauts). Pas de RNG, déterminisme inchangé.

### B. Calibrer la tomate (démonstratrice, §E.3)
Override le profil sur `class Tomato` (`species.py`) pour que sa **croissance libre
reproduise l'allure de ses stades** : hauteur qui monte vers **~40 cm**, port
`buissonnant` (rayon de couronne ~25-30 cm à maturité). C'est le **cœur du travail
de calibration** : règle `growth_speed`, `max_height_cm`≈40, `max_extent_cm`≈30,
`apical_dominance_base`, `branch_angle`. **Reproduire d'abord** (allure ≈ gabarit),
enrichir ensuite. Note : le `MAX_REACH_CM=200` du tronçon 1 est un défaut d'arbre —
la tomate veut **bien plus petit** (~40-50 cm).

### C. Dériver l'empreinte de la structure (§G) — voie procédurale
Mécanisme de **bascule par espèce** (défaut sobre, signale ton choix) : un flag de
classe `procedural_growth: bool = False`, mis à `True` **uniquement sur Tomato**.
Dans les 4 classmethods (`base.py:333-359`), `if cls.procedural_growth:` → lire un
**cache d'empreinte** dérivé de la structure ; sinon → l'**ancien chemin** (stades)
inchangé. Dérivations (§G) :
- `height_at` ← `max(z)` des extrémités de segments (`base[2] + dir[2]·length`).
- `canopy_radius_at` ← **extension horizontale max** de la couronne. **Point dur**
  (signale) : une jeune flèche verticale a une extension de branches ≈ 0 alors que
  sa canopée réelle (feuilles, absentes avant le tronçon 5) ne l'est pas. **Défaut
  sobre** : `canopy_radius = max_horizontal_reach + foliage_halfwidth`, où
  `foliage_halfwidth` est un levier de profil (rayon de feuillage autour d'un
  segment) calibré pour reproduire l'allure → rayon **non nul même droit**.
- `root_radius_at` ← **rayon dérivé** (§8 acté) : `k · canopy_radius` ou `k · height`
  (k calibré ; la tomate veut ~30 cm). Pas de structure souterraine.
- `foliage_density_at` ← **garde l'ancien chemin** ce tronçon (défaut sobre, signale) :
  la densité d'ombre dépend des **feuilles**, qui n'existent qu'au **tronçon 5**.
  Dériver un proxy structurel maintenant fausserait fortement le `LightField`
  (l'ombre alimente tout l'écosystème). On migre la **géométrie** (hauteur/rayon)
  d'abord, la **densité de feuillage** suivra avec les organes.

**Cache d'empreinte** (point ouvert §00) — défaut sobre : un dict
`inst.footprint` (height/canopy_r/root_r), **recalculé une fois par tick en fin de
`grow_plant`** (la structure vient d'être mise à jour), lu par les classmethods.
Initialise-le à la naissance (sinon une tomate lue avant son 1ᵉ tick n'a pas de
cache → prévois un repli : recalcul à la volée si `footprint is None`).

### D. Re-figeage du golden (§I) — validation AVANT capture
**Ordre impératif** :
1. Implémente A+B+C. La tomate apparaît dans le scénario golden → le hash **va
   diverger** : **normal**.
2. **Valide numériquement** l'allure (test, cf. E) : sur une tomate en croissance
   libre, la trajectoire `height_at` part de ~3 cm et **plafonne vers ~40 cm**
   (±tolérance), `canopy_radius_at` reste dans ~20-35 cm, monotone non-décroissante
   sur la phase de croissance. **Itère B/C jusqu'à ce que l'allure colle.**
3. **Seulement alors** : `python3 -m tests.test_golden --capture` → nouveau hash.
   Documente l'ancien → nouveau dans `00_etat.md`.
4. Vérifie que `test_genetique`/`test_auxiliaires`/`main.py` passent toujours et
   que le golden **population** (`b005d9ba…`) **n'a pas bougé** (tu n'as pas touché
   à la population — s'il bouge, c'est une fuite à corriger).

### E. Tests
- **Étends `tests/test_croissance.py`** : un bloc « allure d'empreinte tomate » —
  `height_at` croît de ~3 vers ~40 cm et plafonne ; `canopy_radius_at` dans
  l'enveloppe ; `procedural_growth=True` sur Tomato et `False` sur une espèce
  témoin (ex. Basil) qui garde l'ancien chemin (empreinte = stades). Déterminisme.
- **Re-capture `tests/test_golden.py`** (§D.3).

## Hors périmètre (NE PAS faire ici)
Migrer une **2ᵉ espèce** (les 13 autres gardent l'ancien chemin — c'est tout
l'intérêt de l'incrémental). Seam/`tailler` (tronçon 3). Phototropisme réel
(reste stubé neutre). **Organes / `foliage_density` dérivée** (tronçon 5). Rendu
(tronçon 4). Save (tronçon 6). Profil des pérennes/du reste du catalogue (§E.4,
plus tard). Ne casse pas `age_curve` des pérennes.

## Vérification (success criteria)
```
cd data/code
python3 -m tests.test_croissance     # étendu (allure tomate), doit passer
python3 -m tests.test_golden --capture   # APRÈS validation de l'allure (re-figeage)
python3 -m tests.test_golden         # re-vérifie le nouveau hash
python3 -m tests.test_genetique && python3 -m tests.test_auxiliaires
python3 main.py                      # tourne sans crash
```
Le critère dur **de ce tronçon** : l'**allure d'empreinte de la tomate** colle à
son gabarit de stades (validation numérique), puis le golden est **re-figé** sur
ce comportement validé. Mets à jour `00_etat.md` (tronçon 2 ✅ + nouveau hash +
points tranchés : forme du cache, gestion `canopy_radius`/`foliage_density`,
mécanisme de bascule), commit, `/clear`, lance `03_*.md`.

## Points ouverts (défaut sobre + signaler)
- **Forme du cache d'empreinte** : recalcul/tick (défaut) vs invalidation paresseuse.
- **`canopy_radius` sans organes** : `reach + foliage_halfwidth` (défaut) vs autre proxy.
- **`foliage_density`** : ancien chemin conservé (défaut) — à rediscuter au tronçon 5.
- **Mécanisme de bascule** : flag `procedural_growth` (défaut) vs autre.
- **`root_radius`** : `k·canopy_radius` vs `k·height` — choisis et calibre.
