# ② Flore spontanée : dactyle, fétuque, plantain, ortie — golden RE-FIGÉ annoncé si le smoke change

**Lire d'abord** : `CLAUDE.md` (règles « Le catalogue grandit » et « Toute plante ajoutée = toutes ses voix »), `00_etat.md` (bilan ①), conception §3 et §5,
`docs/narration/voix/conception_voix_narratives.md`.

## Objectif

Des espèces nouvelles lèvent seules, et les graminées nourries par l'azote font de l'ombre au trèfle.

## À faire

1. **Espèces neuves** dans `plants/species/` : `Dactyle` (*Dactylis glomerata*, touffe haute et dense, nitrophile), `Fétuque rouge` (*Festuca rubra*, fine, sols moyens et pauvres),
   `Plantain lancéolé` (*Plantago lanceolata*, rosette à épi). `plants/species/adventices.py` est à 254 LDC : vérifier avec `tools/compte_ldc.py`, module neuf si besoin. Patron : `PoaAnnua`. Ortie = `Nettle` existante.
2. **Levée** : dans `sim/succession.py`, après `choisir_archetype`, une sous-sélection pure d'espèce dans l'archétype, selon l'azote du plot puis hash : `grass` → pâturin, fétuque, dactyle (riche) ;
   `competitor` → pissenlit, plantain, ortie (riche). `WEED_CATALOGUE`, `SEED_ARCHETYPES` et la banque ne changent pas de forme : vérifier qui les lit, car `arch_ph`, `arch_temp` et `arch_allelo` passent par la tête d'archétype.
   Vérifier `sample_genes` pour une espèce hors tête, et que `CLOVER` n'est pas ajouté à la levée spontanée.
3. **Ombre** : vérifier par la mesure que le dactyle baisse `eco.lumiere.at_plot` sous `CLONAL_LIGHT_SEUIL` (0,30) sur un plot réel. La lumière passe par `canopy_radius_at` et `foliage_density_at` (`fields/light.py`) ; un pied seul peut ne pas suffire.
   Réglage par l'espèce (rayon, densité, hauteur), pas par un bonus. Si l'ombre ne peut pas arrêter un stolon, le dire et décrire ce qui manque.
4. **5 voix** pour les 3 neuves : encyclopédie (3 niveaux, `sim/encyclopedie_corpus/`), carnet (`CONCEPT_DE`), magazine, événements, page secrète si une porte un lore. Ajouter l'azote et le cycle au concept concerné. Repérer les autres points d'ajout avec le pissenlit (`grep -rl Taraxacum data/code visuals`, hors `perf_dumps`).
5. **Tests** `tests/test_flore_spontanee.py` : sous-sélection déterministe ; dactyle et ortie seulement sur sol riche ; chaque neuve a ses voix ; déterminisme.
6. **Mesure** `mesures/apres_flore.md`, même protocole qu'au ①, 5 ans : critères de la conception §5 (trèfle sous 40 %, déplacement d'au moins un tiers des plots entre an 3 et an 5, 18 espèces, les 4 présentes, N sain), tick an 2 ≤ +10 %. Un critère raté se dit, avec la cause. Un sprint inerte n'est pas un succès.

## Golden

**RE-FIGÉ annoncé** seulement si des levées du smoke changent d'espèce (raison à consigner, puis `--capture`). Sinon intact.

## NE PAS

Ajouter un archétype. Baisser les frais de germination pour forcer la diversité sans le signaler. Plafonner le trèfle. Toucher au C#. Lancer `tests/test_epaisseur_500ans.py`.
