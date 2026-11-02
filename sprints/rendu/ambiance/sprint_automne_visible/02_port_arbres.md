# ② Port des arbres + arbres de démo — golden RE-FIGÉ (annoncé)

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (cause de l'effondrement, ①),
`docs/vegetal/croissance/fiches_arbres.md`, `mesures/avant.md`, conception §3.1 et §5.

## Objectif

Chaque arbre pousse selon sa fiche : une couronne dès le jeune âge, une hauteur qui ne baisse
jamais toute seule, des ports distincts.

## À faire

1. **Corriger l'effondrement de hauteur** selon la cause établie au ①. Critère au banc : la hauteur
   ne baisse pas de 5, 10, 15 à 25 ans pour aucun arbre [hors taille, seed 42].
2. **Ports par espèce** : régler les paramètres de classe (`port_archetype`, `apical_dominance_base`,
   `branch_angle`, `growth_speed`, `max_height_cm`, `max_extent_cm`, `emit_length_cm`,
   `max_segments`, `foliage_halfwidth`) d'après les cibles des fiches. Vérifier ce que `port_archetype`
   accepte réellement avant d'ajouter une valeur. Un vrai pommier de 5 ans a des branches : viser des
   latéraux dès ~3-5 ans. Attention au commentaire de `AppleTree` : le rayon commande aussi les
   racines, donc la survie à la sécheresse. Vérifier que l'arbre survit [banc, 3 ans max].
3. **Monde de démo** (`main.build_world_full`, `tools/simserver/commands._pre_vieillir_fruitiers`) :
   pré-vieillir tous les ligneux fondateurs de `full`/`propre` (y compris les aulnes de la mare) à
   ~10-12 ans (renommer la fonction en conséquence). Ajouter 2-3 caducs aux couleurs d'automne
   distinctes (bouleau, cerisier, charme) qui n'ombrent pas le potager de la tuile S. Vérifier les
   tests qui montent `full` (`test_sim_server`, `test_bois_mort`, `test_automate_*`,
   `test_peripherie_pont`).
4. **Mesurer le coût** : tick an 2 de `full` avant/après (`tools/profile_monde.py` ou `banc_cadence.py`),
   chiffre marqué `[n=…, VM]`. Budget ≤ +10 %. Au-delà : réduire `max_segments` ou le nombre d'arbres.
5. `mesures/apres_port.md` : banc rejoué, comparaison avec `avant.md`.

## Golden

**RE-FIGÉ, annoncé** : le pommier du smoke change de structure. Dérive limitée aux ligneux, à
expliquer (ancien → nouveau hash). Suites vertes sauf `test_succession` et `test_edaphique`, rouges
avant le sprint.

## NE PAS

Toucher au C#, à `foliage_density_at`, à `_abscission` (③). Ajouter une espèce. Lancer
`tests/test_epaisseur_500ans.py`.
