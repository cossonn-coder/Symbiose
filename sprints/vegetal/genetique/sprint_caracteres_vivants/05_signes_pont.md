# ⑤ Signes visibles et pont

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_caracteres_vivants.md` §4.
> Golden attendu : **INTACT** (export et voix).

## Objectif
Que le pont donne à la vue tout ce qu'il faut pour dessiner les caractères, et que les voix
en parlent sans chiffre.

## À faire
1. **Export** (`tools/simserver/serialize.py`) : par plante, les paramètres visuels **dérivés**
   (pas les gènes bruts) : teinte de la fleur (depuis l'axe d'espèce et `couleur_fleur`),
   échelle de la fleur, contraste des guides, échelle et nombre des fruits, matité de la
   feuille, port (dominance), présence de rejets. Une fonction pure par signe, couche `sim`
   ou pont. Incrémenter `ENGINE_VERSION`. Comparer le snapshot JSON avant/après.
2. **Survol de debug G** (`world/WorldView.Genes.cs`) : tous les caractères dans leur unité,
   groupés (fleurs, fruits, feuille, gestes, sol, chaleur et froid, lignée).
3. **Voix** : concepts « pollinisation guidée » (guides à nectar, ce que voit l'abeille —
   révélé au palier de maîtrise de la pollinisation), « goût et défense » (amertume =
   défense), « lignée » (complété) dans l'encyclopédie et le carnet (`CONCEPT_DE`). Le carnet
   note la première fois qu'un organe est amer ou toxique.

## Tests
- Test ciblé : chaque signe dérivé varie avec son gène et reste borné ; aucune clé de signe
  n'entre dans le digest du golden.
- Golden identique.

## Ne PAS faire
- Toucher au tick. Exporter des gènes bruts hors du survol de debug.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`00_etat.md` : ⑤ FAIT. Commit.
