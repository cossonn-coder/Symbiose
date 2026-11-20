# 2026-11-20 — Étude 3D + gaussian splats, conception PRÉCUISSON EN SPLATS FIGÉE

**Contexte.** F5 de `sprint_depart_jardin` : une plante repiquée à la main meurt →
**D143** ouverte, non diagnostiquée (Nico : « laisse ça en dette »). Puis Nico ouvre
l'étude « passer le jeu en 3D, tous les graphismes en gaussian splats » à partir de deux
dépôts : ink-studio (siliconjungle, JS, MIT, créé 2026-11-16) et SyntaxSplat (iamvillain).
Aucun ne tourne dans Godot ; seul addon Godot maintenu : gdgs (ReconWorldLab, GDScript,
compute = Forward+).

**Prototype** (`docs/rendu/splatting/prototype/`, commit `3959d96`) : tomate mûre, tige du
moteur + feuilles et grappes procédurales, rendue en splats par le CPU d'ink-studio sur la
VM — 106 000 splats, cuisson 17 s [n=1 plant, VM]. Nico : « c'est incroyable c'est
magnifique et c'est ça que je veux pour Symbiose ».

**Matériel.** Nico achète un PC ; budget ~1 000 € → carte 8 Go et 16 Go de RAM jugés
suffisants pour nos splats (couleur unique cuite ≈ 50-60 o/splat [estimation], rendu
pixel-art en basse résolution). Banc de vérité 3D temps réel reporté au nouveau PC.

**Conception figée** `docs/rendu/splatting/conception_precuisson_splats.md` : précuire hors
ligne (VM) et afficher dans la vue iso actuelle. D1 fidélité maximale au moteur dans le
jardin ; D2 images versionnées (git = seul canal VM→Windows), alerte ~200 Mo ; D3 kit
d'organes splats assemblé sur les vrais segments + portraits entiers hors jeu ; D4 tous les
zooms ×0,5→×32 ; D5 trous précuits, couleurs à la palette ; D6 3 portraits par espèce
dévoilés avec les niveaux de l'encyclopédie ; D7 programme par familles (plantes → lisière →
faune/champignons → structures/maison → sol/météo → icônes) ; D8 icônes en objets splats.
Clé technique : une pièce splat parle la langue de la palette indexée (ton = volume,
orientation = normale quantifiée) → une géométrie sert toutes les teintes, la lumière reste
celle du vrai soleil.

**Sprint (a)** `sprints/rendu/splatting/sprint_precuisson_splats/` : 7 tronçons, golden
intact partout, ① = porte de décision (lisibilité à 3 px, extraction ton/orientation).
