# Sprint Maison·1 — **Monde agrandi + maison INERTE + golden smoke test**

> **Kickoff autosuffisant.** Démarrage à froid : tu reprends sans contexte
> préalable. Lis ce fichier en entier, puis `data/code/CONCEPTION_MAISON_OMBRE.md`
> (surtout §1, §2, §5, §7), puis les sources citées, puis exécute. Carte blanche
> (conception figée) : implémente sans re-valider chaque étape, rends compte
> après. **Français.** Nico est expert Python/simulation → pas besoin de
> sur-expliquer Python ; sois rigoureux sur le **déterminisme** et le **golden**.
>
> Tronçon **moyen** : touche la géométrie du monde (`world/`, `fields/ecofields.py`),
> crée un objet config maison, **réécrit `main.py`** (démo) et **reconstruit le
> golden en smoke test**. Synchro multi-fichiers **assumée** (l'exception « un
> fichier à la fois » est levée). Lancement depuis `data/code/`.

## Ce que c'est, en une phrase
On **agrandit le monde** à 20×20 m (40×40 = 1600 plots) selon le layout 3×3 du
§2 (centre = **maison 8×8×6 m**, 8 tuiles jardin séparées par des **chemins en
pierre**), on pose un **objet config `House`** (data seule — **il ne projette
encore AUCUNE ombre**), et on **reconstruit le golden** en **smoke test rapide**
(décision Q4). À la fin de ce tronçon, la maison **existe** dans le monde mais le
`LightField` l'ignore encore (l'ombre arrive au tronçon 2).

## Principe directeur (à NE PAS contourner)
- **Maison INERTE ce tronçon.** Aucune modification de `fields/light.py`. La maison
  est un objet de données posé dans le monde, point. Garder les tronçons étanches.
- **Maison paramétrable (Q5, §3)** : crée une **dataclass de config** (p. ex.
  `world/building.py` → `House` : `center_x_cm, center_y_cm, width_cm, depth_cm,
  height_cm, wall_albedo, …`) avec les **défauts** : centrée, 800×800 cm, 600 cm,
  albédo 0.35 (calcaire Montmartin). Ne câble RIEN d'autre que le stockage.
- **Offset monde par tuile (§1)** : ajoute `origin_x_cm, origin_y_cm` à `Tile`
  (ou à `EcoFields`) pour situer chaque tuile dans le repère monde. C'est le
  plumbing qui permettra au tronçon 2 de savoir où chaque tuile est vs la maison.
  **Inerte aussi** ce tronçon (juste stocké).
- **Chemins en pierre (Q1, §2)** : plots non-cultivables entre tuiles. Modélise-les
  de la façon la plus sobre (p. ex. les tuiles sont simplement *espacées* via leurs
  offsets ; les allées sont l'espace monde entre tuiles, pas forcément des plots
  simulés). Défaut largeur **50 cm (1 plot)**. Choix tranché ici, signalé.
- **Déterminisme** : zéro RNG nouveau. Le golden doit redevenir reproductible.

## Sources à lire (dans l'ordre)
1. `data/code/CONCEPTION_MAISON_OMBRE.md` §1 (option B), §2 (layout + chemins), §5
   (coûts), §7 (golden smoke test).
2. `world/tile.py` — `Tile`, `add_plant(cls, row, col)`, `RONDELLE_TYPES`.
3. `fields/ecofields.py` — `init_eco(tile_id, rows, cols)`, structure par tuile.
4. `main.py` — scénario 9 tuiles ACTUEL (= golden actuel, à transformer en démo).
5. `tests/test_golden.py` — le test golden actuel (à reconstruire en smoke test).
6. `constants.py` — `PLOT_CM = 50`.

## Plan suggéré (révisable)
1. `world/building.py` : dataclass `House` (config paramétrable, défauts posés).
2. `Tile`/`EcoFields` : champs `origin_x_cm, origin_y_cm` (offset monde), défaut 0.
3. Constructeur de monde : fonction qui pose le **layout 3×3** (8 tuiles + maison
   centrale + chemins) avec offsets monde corrects. Tuiles hétérogènes OK (Q2).
4. **`main.py`** : devient une **démo** sur le nouveau monde (la maison est posée,
   inerte). Garder l'esprit (sols contrastés, plantes compagnes) adapté au layout.
5. **Golden smoke test** : reconstruire `tests/test_golden.py` sur un **petit
   monde court** (déterministe, rapide). Décider la forme minimale (combien de
   tuiles/années) — viser « quelques secondes ». La **sénescence longue** (~70 ans)
   → **test séparé** lancé à la demande (ne pas la mettre dans le smoke test).
6. **Re-figer** le(s) golden hash sur le nouveau scénario smoke test.

## Critères de succès (vérifier AVANT de clore)
- [ ] `python3 main.py` tourne sur le nouveau monde (maison posée, inerte).
- [ ] La maison **ne change PAS** la lumière (aucune touche à `fields/light.py`) —
      vérifiable : retirer la maison du monde laisse le golden identique.
- [ ] Golden smoke test **rapide** (quelques secondes) et **déterministe**
      (relancer 2× = même hash). Hash re-figé documenté.
- [ ] `python3 -m tests.test_golden` vert ; suite existante (`test_genetique`,
      `test_croissance`, `test_vigueur`, `test_maitrise…`, `test_population`,
      `test_auxiliaires`) **toujours verte** (adapter les imports si le monde
      bouge, sans changer la dynamique).
- [ ] `00_etat.md` mis à jour (tronçon 1 ✅, hash, largeur chemins tranchée).

## Pièges connus
- Ne pas créer un `LightField` global (ce serait l'option A, ×30 — interdit).
- Tuiles hétérogènes : `init_eco` prend déjà `rows, cols` → pas de régression, mais
  vérifier que rien ne suppose 6×8 en dur ailleurs.
- Le golden actuel est branché sur `main.py` 9 tuiles ; en le reconstruisant,
  s'assurer qu'aucun autre test n'en dépend silencieusement.
