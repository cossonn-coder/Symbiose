# Sprint Maison & ombre déterministe — état partagé

> État léger partagé entre tronçons (≤ ~25 lignes utiles). Mis à jour en fin de
> chaque sous-sprint. **Conception figée** : `data/code/CONCEPTION_MAISON_OMBRE.md`
> (commit `57ff88f`). Toujours la lire avant un tronçon.

## Ce qu'on construit
La **maison centrale** projette une **ombre déterministe** dans le `LightField`,
les apex **se penchent vers la lumière** (phototropisme branché), et une maquette
montre des secteurs contrastés (S plein soleil / NE semi-ombre / NO ombre) sur un
**cycle annuel**. Maison **8×8×6 m**, calcaire de Montmartin (**albédo borné** =
effet espalier), monde **20×20 m = 40×40 = 1600 plots**, **chemins en pierre**
entre tuiles (→ pas d'ombrage inter-tuiles ; seule la maison ombrage globalement).
Maison **paramétrable** (config terrain : position/empreinte/hauteur/matériau/
climat ; défauts posés ici). `PLOT_CM` inchangé (50 cm).

## Stratégie golden (décision Q4 — SMOKE TEST)
Le golden devient un **smoke test petit & rapide** (petit monde, peu d'années).
Le scénario `main.py` (9 tuiles, 30 ans, pommier sénescent) **cesse d'être le
golden** → devient une **démo/banc d'essai** ; la sénescence ~70 ans passe en
**test long séparé**. Maison + phototropisme couverts par **tests ciblés**
(`test_ombre_maison`, `test_phototropisme`), pas par un hash global gonflé.

## Architecture clé (option B, validée)
Champs lumière **par tuile CONSERVÉS** (pas de `LightField` global — coût ×30
évité). On ajoute un **offset monde par tuile** (`origin_*_cm`) + l'injection de
la **seule maison** comme obstacle dans `compute`. Cf. §1 du doc.

## Découpage (4 tronçons + 1 plus tard ; cf. §9)
- **1 — Monde agrandi + maison INERTE + golden smoke test.** ⬜ Nouveau layout
  3×3 (centre = maison, 8 tuiles jardin + chemins), offset monde par tuile, objet
  config `House` (data seule, **ne projette pas encore d'ombre**), nouveau
  `main.py` démo, **golden minimal reconstruit**. → `01_*.md`
- **2 — Ombre de la maison dans `LightField`.** ⬜ Rectangle balayé (sol + reçu),
  par position monde de la tuile, + **albédo espalier borné** (désactivable, 2b si
  lourd). `test_ombre_maison`. → re-figeage localisé. → `02_*.md`
- **3 — Phototropisme branché dans `growth.py`.** ⬜ Apex se penche, déterministe,
  borné, **intensité paramétrable** ; maquette rend **subtil ET marqué** (Nico
  tranche). `test_phototropisme`. → re-figeage maîtrisé. **(risqué)** → `03_*.md`
- **4 — Maquette saisonnière 3 secteurs.** ⬜ `render_structure.py` +
  `export_structure.py` : grille `secteurs × 4 saisons × plantes`, vrai
  `LightField` + maison + albédo. → outil seul, golden intact. → `04_*.md`
- **5 — (plus tard, hors ce sprint)** rendu Godot maison + ombre, portage C# (D24).

## Boucle de travail (rappel CLAUDE.md)
Lancer `0N` → travailler → vérifier le golden/tests → mettre à jour ce fichier →
commit → **`/clear`** → lancer `0N+1`.

## Décisions actées (cf. §8 du doc — Q1-Q6 toutes tranchées)
Chemins en pierre (Q1) · tuiles hétérogènes (Q2) · phototropisme **marqué** défaut,
Nico tranche sur exemples (Q3) · golden smoke test (Q4) · calcaire + albédo +
maison paramétrable (Q5) · maquette annuelle 4 images/saison (Q6).

## Points ouverts (à trancher dans le tronçon concerné, défaut sobre + signaler)
- **1** : largeur des chemins (défaut 50 cm = 1 plot) ; plot-arithmétique exact du
  layout 20×20 avec chemins ; forme du golden smoke test minimal (combien de
  tuiles/années).
- **2** : forme exacte du test point-dans-rectangle-balayé ; rayon/falloff albédo.
- **3** : valeur finale `phototropism_strength` (Nico tranche à l'œil).
