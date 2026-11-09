# ④ Le merle sème sous les perchoirs (D42)

Lire d'abord : `CLAUDE.md`, `00_etat.md`, doc
`docs/faune/vie_macro/conception_zoochorie.md` §4.5 et §4.7. Faits : ① grain sauvage
(`grain_sauvage`, `deposer_grain_sauvage`, plafond par plot), ② chute unifiée
(`recrue_par_fruits`), ③ noisetier.

## Objectif
Le merle **prend** les fruits mûrs sur la plante (cerisier, framboisier, fraisier),
les graines qui survivent au transit tombent **sous les perchoirs**. Le joueur peut
poser un **perchoir**.

## Modèle
Module neuf `sim/zoochorie.py` (couche `sim`, il lit `fields` et `plants`, jamais
`engine`). Fonction appelée une fois par semaine **par tuile**, juste
après `_tick_fruits` (étape 15c de `sim/engine/boucle.py`, vérifié le 2026-11-09 :
populations 13b → succession 15 → fruits 15c). Les fruits de la semaine sont alors
à jour ; les grains déposés lèvent au plus tôt la semaine suivante (et de toute
façon au printemps, dormance ①). Le dire dans le commentaire.
1. **Prise** : pour chaque plante vivante, `recrue_par_fruits` et mangée par le
   merle (trait d'espèce `mange_par = ("merle",)` posé sur cerisier, framboisier,
   fraisier ; défaut `()`), pour chaque cohorte `maturite >= 1.0` :
   `prise = nombre × TAUX_PRISE × d̄`, `d̄` = densité moyenne du champ `merle`
   (`eco.populations["merle"]`) sur les plots foliaires (herbacée : plot du pied).
   Somme des prises de la tuile bornée par l'appétit `APPETIT × Σ densité merle de la
   tuile` (si dépassé, toutes les prises sont réduites au prorata — Holling II).
   Arrondi entier déterministe (`_hash_noise` pour la partie fractionnaire).
   `cohorte.nombre -= prise` ; cohorte vide retirée. Placeholders : `TAUX_PRISE`
   ≈ 0,15/sem, `APPETIT` à fixer pour qu'une année ordinaire laisse tomber une part
   des cerises [calibrage ⑦].
2. **Graines** : `n = prise × P_TRANSIT` (≈ 0,05 placeholder ; une cerise = un
   noyau), gènes `child_genes(mère, find_father(...))`, `child_expression(mère)`.
3. **Dépôt** : chaque graine tombe sur un plot tiré par hash, pondéré par la grille
   **perchoir** du monde. Poids d'un plot : sous la couronne d'un ligneux vivant de
   hauteur ≥ 150 cm (`foliar_plots`), sous un mort debout (`stade_mort == "seche"`,
   plots de son ancienne couronne ou à défaut son pied), plot d'un `Support`
   (`tile.supports`, tout type), + `eco.lisiere` si présent. Grille calculée
   **seulement** les semaines où une prise a eu lieu (mémoïsée pour la semaine).
   Le monde = toutes les tuiles (repère monde via `origin_x_cm/origin_y_cm`) : un
   dépôt sur une autre tuile va dans un **tampon** `game_state` vidé APRÈS la boucle
   des tuiles (fin de `tick_semaine`), pour que l'ordre des tuiles ne décide rien.
   Dépôt via `deposer_grain_sauvage` (`origine="merle"`). Sans perchoir nulle part :
   la graine est perdue (le merle ne se pose pas au milieu du gazon).
4. Log court et stable (lu au ⑦) : une ligne par plante et par semaine de prise,
   ex. `🐦 Merle : <n> fruits pris sur <espèce>@<pos>` ; pas une ligne par graine.

**Effet induit voulu** : moins de cerises tombent → moins de litière `fruit` →
`_merle_food_grid` (fruit frais au sol) et `_rav_fruit_signal` baissent : c'est la
boucle réelle, ne pas la compenser.

## Le perchoir (geste)
`sim/actions/supports.py` : `poser_perchoir` sur le patron de `poser_tuteur`
(gabarit ≈ 200 cm, finesse `"fin"`), coût dans `sim/actions/couts.py`
(`OBJETS_TOUCHES`), technique de maîtrise `perchoir` déclarée comme
`palissage` (non câblée au tick). Vérifier au code ce que `support_compatible`
(`world/support.py`) fait d'un type inconnu : une grimpante peut s'y accrocher comme
à un tuteur (acceptable), mais aucun chemin ne doit planter. Pont : exposer le geste
dans `tools/simserver/actions.py` comme `poser_tuteur` (incrément de version du
protocole selon l'usage du fichier).

## Ne PAS faire
- Ne pas modifier la dynamique du champ `merle` (sa ressource reste
  `_merle_food_grid`).
- Pas de geai/écureuil/mulot (⑤-⑥).
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Tests
`tests/test_merle_seme.py` : (a) cerisier mûr + champ merle imposé : des cerises sont
prises, la chute diminue d'autant ; (b) les grains `merle` tombent sous un perchoir
(arbre, mort debout, support) et nulle part ailleurs ; (c) sans perchoir : aucun
grain ; (d) un perchoir posé loin du cerisier reçoit des grains ; (e) dépôt sur une
autre tuile via le tampon (deux tuiles) ; (f) appétit : doubler les fruits ne double
pas la prise.

## Golden
`a10b7225…` **INCHANGÉ** attendu (aucun fruit mûr au smoke).

## Perf
`full` 5 ans, tick médian an 3-5, ≤ +10 %.

## F5
Aucun (vue au ⑧).
