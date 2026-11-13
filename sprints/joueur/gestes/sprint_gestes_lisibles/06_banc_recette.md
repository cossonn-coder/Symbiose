# ⑥ Banc d'observation, recette F5, clôture

> Lire d'abord : `CLAUDE.md`, `00_etat.md` (tout ce que ①-⑤ ont posé),
> `docs/joueur/gestes/conception_gestes_lisibles.md`. Golden : **INTACT**.

## Objectif
Un banc unique où Nico regarde, sans jouer à la main, tous les gestes de D136 (a)-(f)
s'animer et laisser leur trace ; puis la recette F5 et la clôture du sprint.

## À faire
1. **Banc `gestes_lisibles`** (registre `data/code/bancs/`) : une tuile préparée pour que
   chaque geste ait une cible valide (litière tendre à glaner, bac avec compost mûr,
   ruche peuplée avec miel, pile, plantes mûres à fruits, une plante à bouturer, un
   nuisible rampant ET un volant, plot humide et plot sec, un pot) + un **plan de test**
   (format du ⑤) qui joue, dans un ordre lisible : arroser, pincer, couper, tailler,
   glaner, drainer, bouturer, arracher, deraciner, retourner, ecraser (rampant, puis
   volant → refus attendu), favoriser_auxiliaire, becher, grelinette, creuser, epandre,
   empiler_bois, pailler, composter, recolter (fruit), recolter_miel, planter (catalogue),
   planter_conteneur, deplacer_pot. Gestes non ouverts par défaut : le banc les ouvre
   (forçage de banc, comme les bancs existants).
2. **Oracle** (`data/code/tests/bancs/`) : le plan joué au pont donne le résultat attendu
   par geste (appliqué / refus attendu), une trace par geste qui en laisse une, aucun
   chiffre dans les messages.
3. **Capture VM** du banc en mode testeur, **regarder les PNG**, planche finale dans
   `planche/` du sprint.
4. **Recette F5** dans `00_etat.md` : lancer le banc, appuyer sur la touche du testeur,
   ce qu'il faut voir pour chaque geste (animation curseur, trace, mot) ; plus les points
   qui ne se voient qu'au F5 (curseur OS, objet en main, catalogue, fenêtre automate
   fermée, récolte au fruit, pluie et sécheresse sur le canvas).
5. **Clôture** : `DETTE.md` — D136 : (a)-(f) traités côté code, F5 attendu ((g), (h)
   restent ouverts) ; `BACKLOG.md` ; entrée `journal/` + pointeur `journal.md` ; mémoire
   de statut si pertinent. Mesure perf du banc (FPS) consignée.

## Ne PAS faire
- Pas de logique nouvelle : ce tronçon observe et recette. Un défaut trouvé se corrige
  s'il est petit et dans le périmètre, sinon il va dans la recette comme limite.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
Sprint CLOS côté code, F5 attendu. `00_etat.md` §REPRISE = recette F5.
