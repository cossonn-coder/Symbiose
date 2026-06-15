## 2026-06-07 — Sprint Maison & ombre déterministe : conception + tronçons 1-4 (Python) — CLOS

La **maison normande** entre dans la simulation : elle projette une **ombre
déterministe** dans le `LightField` et les plantes **se penchent vers la lumière**
(phototropisme). Conception figée le matin (`docs/conception/CONCEPTION_MAISON_OMBRE.md`,
commit `57ff88f`, Q1-Q6 toutes tranchées), 4 tronçons implémentés dans la journée.

**Décision : monde agrandi 20×20 m = 1600 plots, maison centrale 8×8×6 m.**
Calcaire de Montmartin, **albédo espalier borné** (réflexion des murs ensoleillés,
≈2,5 m, falloff linéaire), maison **paramétrable** (config terrain). **Chemins en
pierre de 50 cm** entre tuiles, NON simulés — c'est l'option B : les champs lumière
**par tuile sont conservés** (pas de `LightField` global, coût ×30 évité) ; seule
la maison ombrage globalement, via un offset monde par tuile (`origin_*_cm`).

**Décision : le golden devient un smoke test** (2 tuiles 6×8 × 4 ans, ~5,6 s).
`main.py` cesse d'être le golden → **démo/banc d'essai** ; la sénescence ~60 ans
sort en `tests/test_senescence.py` séparé. Maison + phototropisme couverts par
tests ciblés (`test_ombre_maison` 4, `test_phototropisme` 11), pas par un hash
global gonflé.

**Tronçons.** **t1** monde + maison INERTE (`world/building.py`, golden re-capturé
`8ef7729f…`) → **t2** ombre analytique (rectangle balayé `_point_in_swept_rect`,
opaque → plancher `LIGHT_FLOOR`, albédo inclus, sans `house` chemin bit-identique ;
coût ≈ +2,6 %/tick ; golden enrichi d'une maison `0aa2892c…`) → **t3** phototropisme
branché dans `growth.py` (gradient de lumière-sol **local** par différences finies,
borné ≤12°/émission + plancher de verticalité `MIN_APEX_Z`=0.30, zéro RNG ;
re-figeage maîtrisé → golden **`16a1b937…`**) → **t4** maquette saisonnière
3 secteurs (S/NE/NO) × 4 saisons, 2 fichiers subtil (0.10) vs marqué (0.30).

**Constats de la maquette** (à retenir) : (a) gradient net **S≈1.00 > NE≈0.74 >
NO≈0.41** ; (b) la pente vient du gradient **local = ombre maison + AUTO-OMBRAGE
de la canopée** → même en plein soleil une plante vigoureuse se penche un peu
(réaliste, pas un bug) ; (c) modèle solaire **symétrique E-O** → NE/NO diffèrent
surtout par la phase d'ombre.

**Décision (provisoire) : phototropisme marqué = 0.30** (défaut actuel). Nico ne
peut pas trancher définitivement **sans les organes rendus** → à reconfirmer
avec feuilles/fleurs/fruits (Godot). ⚠ `phototropism_gain` (réservé) renommé
`phototropism_strength` — `CONCEPTION_CROISSANCE.md` §E dit encore l'ancien nom.

**Statut.** Sprint **CLOS côté Python** (t1-t4). Reste hors sprint : rendu Godot
maison + ombre (t5), portage C# (D24).

---
