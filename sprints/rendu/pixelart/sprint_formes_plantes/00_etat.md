# Sprint FORMES DES PLANTES (reste de D118 (A)) — état

**Conception figée le 2026-11-04** : `docs/rendu/pixelart/conception_formes_plantes.md`. 5 tronçons, à exécuter par `/sprint-auto sprint_formes_plantes`.

## Décisions clés

1. 33 espèces : port dessiné par la vue (7 ports + fiche), sans dessiner leurs segments. Tomate, lierre, jasmin gardent leurs segments.
2. Taille : clic sur la plante, coupe visible par hints du pont (`rabattu`, `pince`). Arbres, tomate, lierre, jasmin gardent le segment.
3. Formes seules ; le reste demeure dans D118 réduite.

Golden attendu : **inchangé partout**, `a10b7225…` à l'ouverture. Vérifié par patch mémoire pour les segments [smoke], à revérifier au ② pour les hints. Tout écart est une anomalie à remonter, pas un re-figeage.

## Carte des tronçons

| # | Kickoff | Contenu | État |
|---|---|---|---|
| ① | `01_banc_fiches.md` | Banc, mesure des silhouettes, « avant », 36 fiches | à faire |
| ② | `02_socle_rosettes.md` | Socle des ports, taille, rosettes (7) | à faire |
| ③ | `03_tiges.md` | Tiges à feuilles étagées (12) | à faire |
| ④ | `04_chaumes_tapis_buissons.md` | Chaumes, couvre-sols, buissons, courgette (13) | à faire |
| ⑤ | `05_grimpantes_grammaire_bilan.md` | Haricot, tomate, lierre, jasmin, fleurs et feuilles SNES, bilan | à faire |

## Garde-fous

- Ne JAMAIS lancer `tests/test_epaisseur_500ans.py`. Mesures ≤ 3 ans de jeu.
- Déjà rouges avant ce sprint : `test_succession`, `test_edaphique`, `test_parasite`.
- Vérifier la charge VM (`uptime`) avant toute mesure de temps. Chaque chiffre porte sa limite entre crochets.
- `PlantRenderer.Prairie.cs` (301 LDC) et `PlantRenderer.Organs.cs` (292) ne doivent pas grossir : code neuf dans des partials neufs.

## Bilans

(rempli par chaque tronçon : ce qui est fait, mesures, écarts, ce que le suivant doit savoir)

## §REPRISE

Lire `CLAUDE.md`, ce fichier, la conception, puis le prochain kickoff « à faire ».
