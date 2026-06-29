# Tronçon ⓪ — Référence perf + scatter LightField (D32)

> Kickoff autonome. Design : `CONCEPTION_VENT_EVAPOTRANSPIRATION.md` **§7B**.
> **Aucun effet de vent ici** — on prépare le terrain perf. Golden **INTACT**
> (bit-identique exigé).

## But
1. **Référence perf** : profiler `ms/tick` sur le monde complet (1600 plots / ~81
   plantes) + un run long, isoler les postes (LightField ≈ 59 %, dont
   `_point_in_capsule` seul ≈ 35 %). Fixer le **budget +X %/tronçon** (§7B).
2. **Optim scatter (D32)** : remplacer le **gather** de la boucle lumière-sol
   (`fields/light.py` `compute`, L266-291 : chaque plot × chaque plante, aucun
   élagage) par un **scatter** (chaque ombre ne visite que les plots de sa
   bounding-box de capsule). **Mesuré ×5.6-7.1, plancher** (`tools/diag_light_coverage.py`).

## Pourquoi c'est golden-safe
Un plot hors de la bbox d'une capsule renvoie **forcément** `False` dans
`_point_in_capsule` → l'élaguer ne change **aucun** résultat. C'est purement éviter
des tests voués à `False`. **Mais** : la bbox doit être un **vrai sur-ensemble** de
la capsule (centre `(qx,qy)`, extrémité `+ (sdx,sdy)·length`, marge `±qr` sur x ET
y, conversion plot via `int(coord // PLOT_CM)` avec clamp `[0,rows/cols-1]`). Un
off-by-one qui exclut un plot couvert dérive le golden **en silence**.

## Démarche
1. **Profil de référence** : écrire/relancer un profil `cProfile` sur le monde
   complet + run long ; consigner les chiffres dans `00_etat.md` (ms/tick par poste)
   et fixer X (% max ajouté par tronçon).
2. **Scatter** : dans `compute`, pour la boucle **lumière-sol** uniquement, inverser
   l'ordre : pour chaque tranche × chaque plante (`infos`), calculer la bbox de la
   capsule, n'itérer que les plots de cette bbox, y appliquer `att *= (1-qd)`.
   Attention : l'accumulation par plot reste **multiplicative sur toutes les
   plantes** + ajout albédo + ombre maison + plancher → restructurer en accumulant
   l'atténuation par plot (init 1.0, multiplier au passage), puis appliquer maison/
   albédo/plancher dans une passe finale par plot. **La boucle par-plante (lumière
   reçue, L240-263) reste inchangée** (déjà élaguée par tri-hauteur + break).
3. **Test d'équivalence** (garde-fou obligatoire) : un test qui compare, sur le
   monde smoke (et idéalement le monde complet quelques ticks), la grille
   lumière-sol scatter vs l'ancienne gather → **égalité bit-à-bit** (`==` sur les
   floats, pas tolérance). Sans ce vert, D32 n'est pas soldée.

## Pièges
- La maison (`_point_in_swept_rect`) et l'albédo (`_wall_albedo_bonus`) sont des
  termes **par-plot indépendants des plantes** → les garder dans la passe par-plot,
  pas dans le scatter par-plante.
- L'ombre maison met `att=0` (ombre pleine) AVANT le produit des plantes : respecter
  cet ordre (un plot sous la maison ignore les capsules plantes).
- `infos` inclut les **squelettes secs debout** (densité `SILHOUETTE_SECHE`) — les
  traiter comme les vivants dans le scatter.

## Critères de succès
- `python3 -m tests.test_golden` **inchangé** (hash identique, zéro re-figeage).
- Nouveau **test d'équivalence scatter==gather** au vert.
- `ms/tick` mesuré **en baisse** sur le monde complet (viser le ×6 plancher sur la
  boucle sol) ; consigner avant/après dans `00_etat.md`.
- Suites de non-régression : `test_phototropisme`, `test_ombre_maison` (ou
  équivalent lumière/maison), `test_sim_server`.

## Clôture du tronçon
MAJ `00_etat.md` (statut ⓪ ✅ + chiffres perf + budget X). Solder **D32** dans
`DETTE.md`. Commit. `/clear`. Lancer `t1_vent_masse_air.md`.
