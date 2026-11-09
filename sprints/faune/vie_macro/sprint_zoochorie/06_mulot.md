# ⑥ Le mulot mange les graines, et en cache — golden RE-FIGÉ annoncé (D42)

Lire d'abord : `CLAUDE.md`, `00_etat.md`, doc
`docs/faune/vie_macro/conception_zoochorie.md` §4.6. Faits : ① grain sauvage, ②
chute unifiée + glandée, ③ noisetier, ④ merle + `sim/zoochorie.py`, ⑤ geai,
écureuil, catégorie `disperseur`.

## Objectif
Le mulot (*Apodemus sylvaticus*) est le **prédateur** des graines tombées et un petit
disperseur. Il ferme deux boucles : la **satiation** (années de glandée) et la chaîne
**graine → mulot → rapace/couleuvre**.

## Guilde (`fields/population/registry.py`)
`TrophicSpec` **mulot**, catégorie `disperseur` (⑤), sel neuf. Placé **avant** les
super-prédateurs (ils lisent leurs proies fraîches, cf. commentaire du registre).
- Habitat = couvert : paillage (`_avec_abri_paillage`), structures `pile`, lisière
  (`lisiere_w` ≈ 0,25), plots sous couronne ligneuse.
- Ressource = grains sauvages au sol (compte par plot normalisé) + fruit tombé
  (`_fruit_litter`, frais ou non) + densité de la banque-sol
  (`eco.seed_bank.total_density`, **lue, pas consommée** — dette).
- Nocturne, actif toute l'année (fenêtre large).
- Proie : ajouter `"mulot"` aux proies du **rapace** (`_proies_grid(("campagnol",
  "merle", "mulot"), …)`) et de la **couleuvre** ; `predators=("rapace",
  "couleuvre")` sur le mulot.
- Encyclopédie faune (`fields/faune_encyclo.py`) : entrée `mulot` + liens
  symétriques (rapace, couleuvre, chêne, hêtre, noisetier, noyer, cerisier).

## Prédation et caches (`sim/zoochorie.py`)
Chaque semaine, par tuile, après les dépôts du jour (ordre à justifier en commentaire) :
- Offre `O` = nombre de grains sauvages de la tuile ; satiation `s = A / (A + O)`
  (Holling II, `A` placeholder).
- Pour chaque grain sauvage (ordre déterministe : plots triés, puis ordre de liste),
  `p = PRED_MAX × mulot(r,c) × s` ; tirage `_hash_noise` (canal libre, vérifié par
  grep). Pris → avec `P_CACHE_MULOT` (≈ 0,15) il est **déplacé** (≤ 3 m, plot tiré
  par hash pondéré par le couvert, `origine="mulot"`, sa dormance et sa péremption
  conservées) ; sinon **mangé** (retiré).
- Les grains plantés par le joueur (`origine == "joueur"`) ne sont **jamais** touchés
  (dette notée).
- Log : une ligne courte par tuile et par semaine où il y a eu prédation
  (`🐭 Mulot : <n> graines mangées, <k> cachées`) — pas une ligne par grain.

## Golden — RE-FIGEAGE ANNONCÉ
Le mulot vit de la **banque-sol dès le smoke** → champ non nul → il nourrit rapace et
couleuvre → leur densité change → la prédation sur le **campagnol** (et le merle,
la limace) change → dégâts racinaires du campagnol → plantes. Dérive **attendue et
localisée** à la chaîne rapace/couleuvre/campagnol/limace et à ses conséquences sur
les plantes. Aucun grain sauvage au smoke → la prédation de graines n'y joue pas.
Procédure : (1) avant re-figeage, montrer la dérive : densités moyennes rapace,
couleuvre, campagnol, limace par an (smoke, 4 ans) avant/après, et lister les
plantes dont `vitalite`/stade diffère au digest final ; (2) si une dérive apparaît
hors de cette chaîne (lumière, sol, succession sans lien), STOP, chercher ; (3) sinon
re-figer avec `python3 -m tests.test_golden --capture`, reporter l'ancien et le
nouveau hash dans `00_etat.md` et le message de commit.

## Ne PAS faire
- Ne pas consommer `SeedBank.species` / archétypes (granivorie banque-sol = dette).
- Ne pas mettre le mulot en `herbivore_vertebre`.
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Tests
`tests/test_mulot.py` : (a) grains sauvages + mulot imposé : une part mangée, une part
déplacée sous couvert ; (b) satiation : 10× plus de grains → part mangée plus faible ;
(c) grains joueur intacts ; (d) rapace nourri par le mulot (champ rapace > 0 avec
mulot seul comme proie). Lancer `test_population`, `test_faune_dediee`,
`test_stress_chronique`, `test_evenements`, `bancs.test_verger_mur`.

## Perf
`full` 5 ans, tick médian an 3-5, ≤ +10 %.

## F5
Aucun (vue au ⑧).
