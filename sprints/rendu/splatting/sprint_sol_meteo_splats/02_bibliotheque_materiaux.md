# ② Bibliothèque des matériaux du sol — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md` (compte rendu ① : cellule, mesures), conception §3.1 et E5,
`tools/splat/cuire_tapis.js`, `recettes/tapis_terre_motteuse.js`, `visuals/MulchMotifs.cs`,
`visuals/TracesSolMotifs.cs` (ce que chaque matière doit évoquer aujourd'hui).
Golden attendu : **`bce813af…` INTACT**. Aucun fichier C# touché.

## Objectif
Cuire toutes les géométries du tapis aux 7 paliers (×0,5 → ×32), variantes comprises.

## Géométries (liste de départ ; fusionner si deux se ressemblent à l'œil)
terre fine · terre motteuse (①) · sable/gravier · herbe rase (réutiliser `feuille_ruban`/`limbe_graminee`) ·
paille (brins couchés en tous sens) · BRF (copeaux clairs d'aubier, reconnaissables au 1er regard —
demande Nico) · aiguilles (réutiliser `feuille_aiguille`) · feuilles mortes en tapis dense (réutiliser les
feuilles du jardin) · neige (grains + croûte, bosses douces) · craquelé (plaques séparées par des fentes
= creux) · **flanc** (coupe de terre, pavée horizontalement seulement).
Humus, tourbe, vase, argile, sable fin = **palettes** sur les géométries de terre (E5), rien à cuire.

## À faire
1. Une recette `recettes/tapis_<geometrie>.js` par géométrie ; ton = volume (creux/bosses nets, E6).
2. Cuisson parallèle (`--liste | xargs -P`), planches + manifeste `tapis.json`.
3. Planche de contrôle par géométrie et par palier (pavage 3×3) → `mesures/02_*`.

## Mesures
Temps total [VM, charge notée], Mo git ajoutés (alerte 200 Mo), couture = 0 partout.

## Ne PAS faire
×64 (réservé au ⑧, scène seule). La vue. `data/code/`, `test_epaisseur_500ans`, DeepSeek, `vendor/`.

## Fin
`00_etat.md`, commit `feat(tapis②) : …`.
