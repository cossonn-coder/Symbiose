# ③ Fruits par cohorte, limites relevées, noix du noyer — golden INTACT attendu

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §6, `plants/base/stades.py` (`Fruit`, `MAX_ORGANS`, `organ_sites`), `sim/engine/decompo.py` (`_tick_fruits`, `frac_nouaison`), `sim/engine/anemophilie.py`, `sim/actions/gestes.py` (manger ciblé), `tools/simserver/serialize.py`, `tools/simserver/plante_route.py`, `tools/jardinier_auto/operateurs.py`, `fields/ecofields/constants.py` (`FRUIT_MASSE`, `FEUILLE_PAR_PLOT`), `tests/test_fruits.py`.

## Objectif

Un arbre adulte porte autant de fruits qu'un vrai : des centaines, voire des milliers. Le noyer porte ses noix.

## À faire

1. **`Fruit` = cohorte** sur un site, avec un champ `nombre` (défaut 1). Lecteurs à trouver au `grep` (`\.fruits`, `Fruit(`, `MAX_ORGANS`, `organ_sites`) : nouaison, maturation, chute, manger, pont, automate, faune attirée par les fruits (rechercher `fruit` dans `fields/population` et `sim/engine`).
2. **Leviers d'espèce** : nombre de fruits par site à la nouaison complète, et masse unitaire. Ordres de grandeur à **sourcer** et déclarer `[odg]` : cerisier, pommier, figuier, noyer adultes. Sur les arbres, tous les apex sont des sites, sans le plafond de 10. Les autres espèces gardent leur comportement (1 fruit par cohorte, `MAX_ORGANS`).
3. **Manger** retire un fruit de la cohorte, le gain restant ∝ maturité. **Chute** : nombre × masse unitaire en litière `fruit`. **Garde-fou de masse** : comparer la litière fruit annuelle d'un arbre à sa litière de feuilles, et mesurer fertilité, humus et faune attirée avant/après [`full`, seed 42, 3 ans]. Si la masse fait dériver le sol, ramener la masse unitaire à l'échelle de la litière et le dire.
4. **Pont** : exporter `nombre` par fruit (`serialize.py`), incrémenter la version du protocole comme le font les tronçons précédents (`grep` sur la version actuelle), garder `fruit_index` pour viser une cohorte.
5. **Noyer** : après ②, mesurer `pollen_recu` des deux noyers du banc. Cible `[choix]` : une paire voisine noue au moins à moitié, un isolé autour de 0,2 à 0,35 (le noyer est dichogame). Recalibrer de préférence au niveau de l'espèce ; si c'est `ANEMO_DOSE_COEF` global, mesurer les autres anémophiles (noisetier, chêne…).
6. **Effet** : fruits par arbre et par an sur `verger_mur` et `full`, poids du snapshot JSON avant/après, tick médian.
7. Golden, `tests/test_fruits`, `tests/simserver`, `test_verger_mur`, suites pollinisation, puis bilan et commit.

## Golden

**INTACT attendu** : les arbres du smoke ne sont pas mûrs ; les herbacées gardent 1 fruit par cohorte. S'il bouge : anomalie, pas de re-figeage.

## NE PAS

Changer `frac_nouaison` ni `POLLEN_DEMI`. Dessiner (④). Lancer `tests/test_epaisseur_500ans.py`.
