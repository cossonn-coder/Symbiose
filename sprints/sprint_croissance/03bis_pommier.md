# Sprint Croissance·3bis — Migration procédurale du **pommier** (`etale`)

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis les sources citées, puis exécute.
> Carte blanche (conception figée) : implémente sans re-valider chaque étape,
> rends compte après. Français + pédagogie (Nico vient du C/Python embarqué,
> expert simulation ; débutant Godot/C# en frontend).
>
> Tronçon **moyen** : 3 fichiers de prod couplés (`plants/base.py`,
> `plants/perennials.py` — `AppleTree` y vit —, `sim/growth.py`) + 1 fichier de test +
> **re-capture du golden**. Synchro cohérente multi-fichiers assumée (l'exception « un
> fichier à la fois » est levée). **Le golden engine SERA re-figé** (≠ tronçons 1-3) —
> re-figeage MAÎTRISÉ, pas une fuite : on valide AVANT de capturer.

## Ce que c'est, en une phrase

Première espèce **ligneuse** sur la voie procédurale : on migre le **pommier**
(`AppleTree`) de l'empreinte par **`age_curve`** (interpolation âge→hauteur/rayon) vers
l'empreinte **dérivée de la structure** de segments — comme la tomate au tronçon 2,
mais avec trois obstacles propres aux arbres que la tomate n'avait pas : (1) l'override
de `PerennialWoody` qui court-circuite la voie procédurale, (2) l'échelle (un arbre de
plusieurs mètres dépasse les plafonds de structure calibrés pour une annuelle), (3) une
allure qui se joue sur des **décennies**, pas des semaines.

## Décisions déjà tranchées (avec Nico) — NE PAS re-débattre

1. **Périmètre = le pommier SEUL.** Les autres ligneuses (`Fig`, `CherryTree`,
   `WalnutTree`, `OakTree`) restent sur `age_curve` (`procedural_growth=False`) →
   inchangées. Le reste du catalogue annuel/herbacé = §E.4, plus tard.
2. **Cible de calibration = l'allure dans la fenêtre du golden (10 ans).** L'`age_curve`
   du pommier vise **(10 ans → 350 cm de haut, 200 cm de couronne)**. Le point 50 ans
   (700/350) et la sénescence (~70 ans) **ne sont PAS exercés** par le golden réduit à
   10 ans (cf. en-tête `test_golden.py`) → ils sont « nice to have » (moteur permanent
   continue à pousser lentement), **pas un critère dur**. Reproduire l'allure **d'abord**
   (§E.3), enrichir ensuite.
3. **`port_archetype="etale"`** (decurrent, §E.2) : dominance qui se relâche avec l'âge
   → couronne large. C'est l'archétype, pas une mécanique neuve : l'étalement ÉMERGE du
   relâchement d'auxine avec l'âge (`_update_auxin`, `f_age`) déjà codé.

## Les trois obstacles (chiffrés) — le cœur du tronçon

**Obstacle 1 — l'override `PerennialWoody`.** `perennials.py:55-67` surcharge
`height_at`/`canopy_radius_at`/`root_radius_at` pour lire l'`age_curve` SANS tester
`procedural_growth`. Tant qu'on ne le résout pas, activer le flag sur `AppleTree` ne
change RIEN (l'override gagne). Résolution propre (déterministe, pas de calibration) :
faire déléguer chaque override à la voie procédurale de `PlantBase` quand le flag est
levé —

```python
@classmethod
def height_at(cls, inst) -> float:
    if cls.procedural_growth:
        return super().height_at(inst)      # voie procédurale §G (footprint × gène)
    h, _ = cls._interp(inst.age_years)       # voie age_curve (arbres non migrés)
    return h * inst.growth_factor * inst.gene("hauteur")
```

Idem `canopy_radius_at`/`root_radius_at`. `PlantBase.height_at` (`base.py:400-425`) teste
DÉJÀ `procedural_growth` et lit `inst.footprint_value(...)` → `super()` retombe pile
dessus. `foliage_density_at` reste tel quel (feuilles = tronçon 5). Les arbres non migrés
(flag False) gardent l'`age_curve` au mot près → **eux n'entrent jamais dans la branche
procédurale**.

**Obstacle 2 — l'échelle (plafonds de structure par espèce).** Sonde mesurée :
un `AppleTree` `procedural_growth=True` avec les **défauts hérités** (depuis `PlantBase`,
calés sur l'annuelle) plafonne après 10 ans à **38 cm / 32 segments** au lieu de 350/200.
Pire, c'est **physiquement impossible** : `EMIT_LENGTH=8 cm` (module) + `MAX_SEGMENTS=40`
(module) → un tronc de 350 cm exigerait **44 segments rien que pour la flèche**. Il faut
des **segments plus longs** et un **plafond plus haut**, *par espèce*. Promotion à faire
(le §L de la conception sanctionne déjà « `MAX_SEGMENTS` (par espèce) » comme levier ;
`EMIT_LENGTH` est son compagnon naturel — la granularité de segment) :

- Ajoute sur `PlantBase` (`base.py`, bloc profil §E vers `base.py:383-395`) deux attributs :
  `emit_length_cm: float = 8.0` (≡ défaut module `EMIT_LENGTH`) et
  `max_segments: int = 40` (≡ défaut module `MAX_SEGMENTS`). **Défauts = constantes de
  module actuelles** → toute espèce non migrée pousse à l'identique (golden de
  STRUCTURE `test_croissance` Tomato/Basil **intact**).
- Dans `sim/growth.py`, `grow_plant` (`growth.py:329-360`) **passe** `cls.emit_length_cm`
  à `_elongate_emit` et `cls.max_segments` à `_elaguer`, qui lisent aujourd'hui les
  constantes de module en dur (`_elongate_emit` `growth.py:~244` `if s.length_cm >=
  EMIT_LENGTH` ; `_elaguer` `growth.py:287/297` `if alive > MAX_SEGMENTS`). Mêmes
  signatures-paramètres que le passage déjà fait pour `max_height`/`wood_persistence` au
  tronçon 2 — calque exact. Les constantes de module **restent** comme valeurs-miroir des
  défauts (cf. le commentaire `growth.py:34-39` ; `test_croissance` continue de référencer
  `G.MAX_SEGMENTS`/`G.EMIT_LENGTH` = ce que la tomate hérite).
- Sur `AppleTree` : `emit_length_cm ≈ 50` (350 cm / 50 = 7 segments de flèche →
  dominance facile à tenir) et `max_segments ≈ 70` (flèche + charpentières dans le
  plafond). **Valeurs de départ, à calibrer.**

> ⚠️ Attention au **bois qui tombe trop tôt** : `wood_persistence` défaut = **60
> semaines** → les charpentières d'un arbre sans apex actif mourraient au bout d'~1 an
> (`_elaguer`, sénescence du bois). Un arbre vit des décennies : règle `wood_persistence`
> **haut** sur `AppleTree` (p.ex. `≈ 4000`, ordre de grandeur « la vie de l'arbre en
> semaines »). C'est probablement le levier le plus sensible pour que la couronne
> persiste.

**Obstacle 3 — l'allure décennale.** L'`age_curve` est **concave** (vite puis plateau) ;
le moteur pousse à `growth_speed × growth_factor × saison` jusqu'au gabarit. On ne
reproduit PAS la courbe point par point — on vise : **flèche qui atteint ~350 cm vers
l'an 10**, montée monotone, couronne qui s'élargit vers ~200 cm, **déterministe**, **bornée**
(`len ≤ max_segments`, jamais 0). Le relâchement d'auxine avec l'âge (`AUXIN_RELEASE_SCALE
= 400` semaines ≈ 7,7 ans, module) fait que la dominance se relâche vers l'an 8 →
transition flèche→étalement = l'archétype `etale` ÉMERGE tout seul. **Si** l'allure 10 ans
reste inatteignable avec les leviers par-espèce existants, tu peux promouvoir
`AUXIN_RELEASE_SCALE` en attribut de profil (même patron que l'obstacle 2) — mais
**essaie d'abord sans**, scope minimal.

Valeurs de départ `AppleTree` (toutes **à calibrer** via la boucle-sonde §C) :
`growth_speed ≈ 1.5`, `apical_dominance_base ≈ 2.0`, `branch_angle ≈ 60`,
`max_height_cm ≈ 700`, `max_extent_cm ≈ 350`, `foliage_halfwidth ≈ 30`,
`organ_site = "lateral"` (fructification latérale, lu au tronçon 5).

## Lis d'abord, dans cet ordre

1. `data/code/CONCEPTION_CROISSANCE.md` — **§E** (profil par espèce ; **E.2** archétypes,
   **E.3** « reliure à l'existant : reproduire l'allure d'abord », **E.4** catalogue),
   **§G** (dérivation d'empreinte), **§I** (migration espèce par espèce, golden re-figé
   localisé), **§L** (leviers de calibrage, dont `MAX_SEGMENTS` par espèce).
2. `sprints/sprint_croissance/00_etat.md` — état + tronçons 1/2/3 faits, la ligne du
   tronçon 2 décrit **comment la tomate a été migrée** (le modèle à calquer) et l'⚠️ sur
   `apical_dominance_base` qui a dû passer >1.
3. Code — **les ancrages** :
   - `data/code/plants/perennials.py:22-80` — `PerennialWoody` (l'override à résoudre,
     obstacle 1) ; `:100-111` — `AppleTree` (`age_curve` = cible de calibration, ajoute-lui
     le profil procédural).
   - `data/code/plants/base.py:383-395` — bloc profil §E (où ajouter `emit_length_cm`/
     `max_segments`) ; `:400-425` — `PlantBase.height_at`/`canopy_radius_at`/`root_radius_at`
     (la voie procédurale que `super()` cible) ; `:198-232` — `update_footprint`/
     `footprint_value` (la dérivation, pure géométrie, ne pas toucher).
   - `data/code/plants/species.py:214-244` — `Tomato`, **le profil migré modèle** (calque
     la structure des attributs, pas les valeurs).
   - `data/code/sim/growth.py:329-360` — `grow_plant` (passe les nouveaux leviers) ;
     `:224` `_elongate_emit` (lit `EMIT_LENGTH`) ; `:267-298` `_elaguer` (lit `MAX_SEGMENTS`).
   - `data/code/tests/test_croissance.py:158-216` — le **test d'allure tomate** (le gabarit
     du test d'allure pommier à écrire).
   - `data/code/tests/test_golden.py` — `AppleTree` est dans le scénario (`:79`, tuile 0,
     pos (0,7)), horizon **10 ans**. C'est CE golden qui sera re-figé.

## Périmètre

### A. `plants/base.py` — promotion des plafonds de structure par espèce
Ajoute `emit_length_cm: float = 8.0` et `max_segments: int = 40` au bloc profil §E
(défauts = constantes de module). Rien d'autre.

### B. `sim/growth.py` — lecture des leviers par espèce
`grow_plant` passe `cls.emit_length_cm`/`cls.max_segments` à `_elongate_emit`/`_elaguer`
(nouveaux paramètres), qui remplacent l'usage en dur des constantes de module. Les
constantes de module **restent** (valeurs-miroir). **Aucun changement de la dynamique
pour les espèces qui héritent les défauts** (Tomato/Basil) → `test_croissance` doit
rester **43/43** sans y toucher.

### C. `plants/perennials.py` — override résolu + profil `AppleTree`
1. `PerennialWoody.height_at`/`canopy_radius_at`/`root_radius_at` : délèguent à
   `super()` quand `cls.procedural_growth` (obstacle 1).
2. `AppleTree` : `procedural_growth=True` + le profil (obstacle 2/3, valeurs de départ
   ci-dessus). **Calibration** : écris une petite boucle-sonde (jetable ou commentée) qui
   fait tourner `grow_plant` sur ~520 ticks (`growth_factor=1.0`, été fixe puis cycle
   réel) et imprime hauteur/couronne/`len` ; ajuste `growth_speed`/`apical_dominance_base`/
   `emit_length_cm`/`max_segments`/`wood_persistence` jusqu'à approcher **~350/~200 à l'an
   10**, monotone et borné. Documente les valeurs retenues en commentaire (comme Tomato).

### D. Tests — `tests/test_croissance.py`
Ajoute un **test d'allure pommier** calqué sur `test_allure_tomate` :
- **montée** : la hauteur part bas (~30 cm) et monte **monotoniquement** vers ~350 cm sur
  la fenêtre 10 ans (tolérance large, c'est une allure : p.ex. `300 ≤ h(an 10) ≤ 420`) ;
- **couronne** : s'élargit vers ~200 cm (tolérance), non nulle au départ ;
- **bornage** : `len(segments) ≤ AppleTree.max_segments` à tout instant, jamais 0 ;
- **déterminisme** : deux instances, même seed/pos/séquence → empreintes identiques ;
- **témoin non migré** : `Fig` (ou `CherryTree`) garde l'`age_curve` — son `height_at`
  reste piloté par `age_years` (pousse une structure mais ne la lit pas, `footprint is
  None`). Garantit que l'override résolu n'a pas « fuité » sur les arbres non migrés.

### E. Golden — re-figeage MAÎTRISÉ (≠ tronçons 1-3)
`AppleTree` est **vivant 10 ans** dans `test_golden`, avec une grande couronne :
l'empreinte procédurale ≠ l'empreinte `age_curve` → le **`LightField` change** →
`growth_factor` du pommier ET de ses voisins (tuile 0) changent → **le hash engine
bouge**. C'est **attendu**. Procédure (ordre impératif) :
1. **D'ABORD valider** : `test_croissance` (allure + bornage + déterminisme pommier)
   passe, et la sonde montre une allure saine (montée monotone, bornée).
2. Lancer `python3 -m tests.test_golden` → il **FAIL** (normal). **Inspecter** que la
   dérive est **localisée et plausible** (le pommier + ses voisins de tuile 0 ; le reste
   du monde devrait peu bouger). Si une plante lointaine explose, c'est une **fuite** à
   corriger, pas à capturer.
3. **Re-capturer** : `python3 -m tests.test_golden --capture` (nouveau `golden_hash.txt`).
4. **Vérifier que les AUTRES goldens NE bougent PAS** (pas d'`AppleTree` chez eux) :
   `test_population` (60 sem., pas d'arbre → `b005d9ba…` **inchangé**) et `test_vigueur`
   (`_minimal_state` = Tomato/Basil/Bean → `vigueur_hash` **inchangé**). S'ils bougent,
   **fuite** → corriger, pas re-capturer.

## Hors périmètre (NE PAS faire ici)
Migration des **autres ligneuses** (Fig/Cherry/Walnut/Oak restent `age_curve`). Profil du
**reste du catalogue annuel/herbacé** (§E.4). **Organes** (fleurs/fruits latéraux,
`organ_site`, `foliage_density`) = tronçon 5. **Rendu Godot** = tronçon 4. Sénescence du
pommier sur 70 ans (golden réduit à 10 ans, hors fenêtre). Phototropisme réel
(`phototropism_gain` reste stubé neutre). Ne **rétablis pas** le golden à 100 ans.

## Vérification (success criteria)
```
cd data/code
python3 -m tests.test_croissance     # 43 existants + allure pommier — doit passer
python3 -m tests.test_golden         # re-figé : capturer APRÈS validation (étape E)
python3 -m tests.test_population     # INCHANGÉ (b005d9ba…) — pas de fuite
python3 -m tests.test_vigueur        # INCHANGÉ (vigueur_hash) — pas de fuite
python3 -m tests.test_genetique && python3 -m tests.test_maitrise && python3 -m tests.test_signes
python3 main.py                      # tourne sans crash (pommier tuile centrale)
```
Critère dur : `AppleTree` est `procedural_growth=True`, son empreinte vient de la
structure (override résolu), l'allure 10 ans approche l'`age_curve` (350/200, tolérance),
la structure est **bornée** (run éternel), `population`/`vigueur` **intacts**, et le
golden engine est **re-figé proprement** (validé avant capture, dérive localisée). Mets à
jour `00_etat.md` (tronçon 3bis ✅ : pommier migré, override `PerennialWoody` résolu,
plafonds `emit_length_cm`/`max_segments` par espèce, golden re-figé `<nouveau hash>`,
valeurs de profil retenues), commit, `/clear`, lance `04_*.md` (rendu Godot — **différé**
selon préférence Nico : à confirmer avec lui avant de l'attaquer).

## Points ouverts (défaut sobre + signaler)
- **`emit_length_cm` / `max_segments` pommier** : 50 / 70 (départ) — calibrés sur l'allure.
- **`growth_speed` / `apical_dominance_base`** : 1.5 / 2.0 (départ) — flèche qui tient ~7
  segments puis se relâche avec l'âge (`etale`).
- **`wood_persistence` pommier** : haut (~4000 sem.) — sinon la couronne s'effondre. Levier
  le plus sensible.
- **`AUXIN_RELEASE_SCALE` par espèce** : NON promu par défaut (essayer sans) ; à promouvoir
  seulement si l'allure 10 ans est inatteignable autrement.
- **Tolérance de l'allure** : large (c'est une allure, pas la courbe) — `±20 %` sur les
  points 10 ans est raisonnable. Resserrable au calibrage.
