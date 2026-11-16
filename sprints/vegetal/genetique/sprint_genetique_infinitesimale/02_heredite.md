# ② Hérédité infinitésimale — brassage, consanguinité, autofécondation

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_genetique_infinitesimale.md` §2, §4, §5, §6
> (dépression de consanguinité) et §8.
> Golden attendu : **RE-FIGÉ LARGE annoncé** — toutes les valeurs de gènes changent
> (brassage au lieu de mutation, σ_A fondateurs, F), donc tout ce qui lit un gène dérive.

## Objectif
Remplacer la mutation fixe par le modèle infinitésimal, porter la consanguinité F par
plante et faire de l'autofécondation un gène.

## À faire
1. **Gène `autofecondation`** ajouté **en queue** du registre : unité `probabilité`, bornes
   [0, 1], σ_A 0.05, neutre par espèce selon `pollination_mode` (`self` 0.95, `insect` 0.15,
   `wind` 0.05). Le neutre se déduit du mode (pas besoin de surcharger 52 classes).
2. **`PlantInstance.F`** (float, défaut 0.0) : consanguinité. Vérifier les sites de
   copie/sérialisation de plante (sauvegarde, `sim/seeds.py` lots ≈ l. 82/96, greffe,
   bouture, clonal) : un clone garde le F de sa mère ; une graine porte son F (champ `Seed`
   avec défaut, rétrocompatible à la lecture).
3. **`child_genes`** (`sim/reproduction.py:162`) suit les formules §4 : moyenne parentale +
   brassage `½σ_A²(1−F̄)` + filet `H_MUT·σ_A²` (`H_MUT = 0.01`), canaux de hash **décorrélés**
   (deux tirages par caractère, garder l'indexation positionnelle). Le choix croisé ou
   autofécondé se fait par hash contre le gène `autofecondation` de la mère. **Lire avant de
   toucher** les lignes ≈ 115-140 (choix du père, repli, `pollination_mode`) et garder le
   repli existant quand aucun père n'est disponible. `SELFING_SIGMA_RATIO` devient inutile :
   le laisser défini (règle « ne jamais supprimer de code », le marquer obsolète en commentaire).
   Introgression : écart du père à son neutre, ajouté au neutre de la mère (§4).
4. **F de l'enfant** : autofécondé `(1+F_m)/2`, croisé 0. Retour de `child_genes` étendu ou
   fonction sœur : au choix, en gardant les appelants lisibles.
5. **Fondateurs** (`founder_genes`, `fields/seedbank.py:118`, et `seed_founder_pool` ≈ l. 436) :
   tirage `neutre + σ_A·z`, F = 0.
6. **Variétés** (graines sans lignée des cultivées de démarrage et de `planter`) : centre par
   espèce `neutre + σ_A·z_variété` (hash espèce + seed du monde), dispersion `σ_A·√(1−F)`,
   F = 0.9 si le neutre d'`autofecondation` ≥ 0.5, sinon 0. Trouver le point d'entrée au code
   (les semis directs passent aujourd'hui par `founder_genes`).
7. **Banque de graines** : `GeneStat` porte la moyenne de F par espèce × parcelle (dans le
   dictionnaire d'espèce, à côté de `genes`) ; `sample_genes` renvoie aussi F. Garder la
   sauvegarde lisible (JSON).
8. **Dépression de consanguinité** (§6) : facteur `1 − DI·F·(1 − s_espèce)`, `DI = 0.3`,
   appliqué au même endroit que `cout_defense` (chercher ses lecteurs, ne pas créer de malus
   de santé). Constantes dans `plants/genetics.py` avec commentaire pédagogique.
9. **Perf** : profiler le smoke avant/après (`cProfile`, même méthode que la mesure du
   2026-11-16 : ≈ 13 s, gènes ≈ 1 %). Consigner. Budget ≤ +2 %.
10. **Re-figeage** : vérifier que la dérive est bien génétique (diff du digest : valeurs
    `GENES[...]` et ce qui en découle), puis `python3 -m tests.test_golden --capture`.
    Consigner l'ancien et le nouveau hash dans `00_etat.md`.

## Tests
- Test ciblé neuf : autofécondation répétée → F tend vers 1 et la variance entre frères
  s'effondre ; croisement → F = 0 ; brassage de σ attendu sur 2000 enfants (tolérance
  statistique) ; déterminisme (deux appels identiques) ; une `Seed` sans F se relit.
- Suites existantes : adapter **uniquement** les assertions qui figeaient l'ancienne loi
  (mutation σ 0.05), en le disant dans le commit. `test_greffe`, `test_plasticite`,
  `test_diversite_fondatrice`, `test_genetique` verts.

## Ne PAS faire
- Toucher aux unités des caractères (c'est le ③). Ajouter d'autres gènes.
- Re-figer sans avoir lu le diff du digest.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`00_etat.md` : ② FAIT, hashes, perf mesurée. Commit.
