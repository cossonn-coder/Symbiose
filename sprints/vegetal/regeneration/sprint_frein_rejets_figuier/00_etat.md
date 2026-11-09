# sprint_frein_rejets_figuier — état (reliquat D130 : rejets de souche)

**Phase** : conception FIGÉE le 2026-11-09 (OK Nico), prêt pour `/sprint-auto`.
Doc : `docs/vegetal/regeneration/conception_rejets_de_souche.md`.
Golden `a10b7225…` **INCHANGÉ** attendu sur les 5 tronçons.

## Pourquoi (mesuré le 2026-11-09, verger_mur, seed 42, n=1 run, VM)
- Espion 25 ans : 164 rejets de figuier, **164 en hiver** ; lumière au plot ≥ 0,7
  pour 163, couverture 0 pour 164 → les portes du clonal sont ouvertes en
  dormance. Cascade : 4 générations en 25 ans (un rejet est mère à 5 ans).
- Sans l'hiver : 0 rejet en 25 ans (portée 100 cm < couronne ~250 cm ; lumière
  sous la mère 0,25 < 0,30 l'été). Tout ou rien → c'est le modèle, pas un réglage.
- Golden : 36 ramets de trèfle, 0 en hiver [smoke, n=1 run] → ① neutre attendu.

## Décisions (Nico, 2026-11-09)
- Q1 **A** : rejet de souche = réponse à la perte de la partie aérienne ; plus
  d'émission de fond pour le figuier ; au pied, sans gate lumière à la naissance.
- Q2 **comme dans la nature** : déclencheurs = mort ET grosse perte de couronne
  (casse, neige, cladoptose, effondrement, taille joueur) ; souche vivante lue
  sur les mémoires de dommage au pied (ombre, sécheresse, asphyxie, racines
  rongées, pourridié), pas sur une cause.
- Q3 le trou hivernal générique (toutes clonales) est traité dans ce sprint
  (golden re-figé autorisé ; mesuré inutile).
- Q4 trait `rejet_souche` pour tous les ligneux selon leur capacité réelle.
- Q5 gel des rameaux d'un ligneux adulte → dette **D131**.
- Q6 le ⑤ vue de `sprint_releve_ligneuse` est absorbé par le ⑤ d'ici.

## Tronçons
| # | kickoff | état |
|---|---|---|
| ① | `01_dormance_clonale.md` — pas d'émission clonale en hiver (toutes clonales) | à faire |
| ② | `02_souche_a_la_mort.md` — trait `rejet_souche`, souche vivante, rejets à la mort, figuier sans drageon | à faire |
| ③ | `03_perte_de_couronne.md` — mémoire `perte_couronne`, rejets d'un arbre vivant (taille = recépage) | à faire |
| ④ | `04_voix_et_mesure.md` — événement, carnet, encyclopédie, `diag_releve` voie `rejet`, 200 ans | à faire |
| ⑤ | `05_vue_godot.md` — voix `attente` (relève ⑤) + rejets visibles, `dotnet build`, F5, clôture D130 | à faire |

## §REPRISE
Exécution : `/sprint-auto sprint_frein_rejets_figuier`. Prochain tronçon = le
premier « à faire ». Chaque tronçon met à jour sa ligne + un § « Tronçon N — fait ».
