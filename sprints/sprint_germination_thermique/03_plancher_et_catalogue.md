# Tronçon ③ — Plancher froid `T_GERM_FLOOR` + typage de TOUT le catalogue

> Kickoff **autosuffisant** (lis CLAUDE.md + 00_etat.md + ce fichier).
> Conception : `CONCEPTION_GERMINATION_THERMIQUE.md` §1.2 + §4. Lancement depuis
> `data/code/`. Golden : **RE-FIGÉ maîtrisé** (annoncé).

## Objectif
Rendre la porte thermique **mordante** : (a) un plancher froid global sous lequel
RIEN ne germe ; (b) typer les 27 espèces avec leur vraie fenêtre de levée → la
succession temprelle des levées émerge (pionnières froides d'abord, frileuses
ensuite).

## À faire
1. **Constante globale `T_GERM_FLOOR`** (~5.0 °C) — couche `fields` ou `sim`, PAS
   `plants`. Choisir l'emplacement par cohérence avec les autres constantes
   thermiques (p.ex. `fields/ecofields/constants.py` à côté des constantes
   thermiques, ou un module `sim` si la lecture s'y prête mieux). Nommage cohérent
   avec `temp_min_growth=5.0` (`familles.py:82`).
2. **Appliquer le plancher** aux 3 points de germination (dans `succession.py`,
   ET via `germination_candidates` pour le féral) : si
   `eco.temperature_sol.at_plot(r,c) < T_GERM_FLOOR` → niche = 0 (court-circuit,
   aucune levée). Le plus simple : porte binaire multiplicative avant la cloche.
3. **Typer TOUT le catalogue** — `t_germ_opt` + `t_germ_tol` réalistes par espèce,
   fichiers `plants/species/{cultivees,potageres,aromatiques,compagnes,sauvages,
   adventices}.py` + `plants/perennials.py`. Repères (calibrage fin au banc ⑥) :
   - **Frileuses** (opt ~20-24 °C, tol étroite ~6-8) : Tomato, Basilic, Poivron,
     Courgette, Haricot, Tournesol.
   - **Rustiques/pionnières** (opt ~10-14 °C, tol large ~10-14) : Mâche, Carotte,
     Moutarde, adventices, vivaces rustiques.
   - Le reste : interpoler selon la biologie de l'espèce (climat d'origine).
   Documenter brièvement (commentaire pédagogique) le « pourquoi » d'une fenêtre
   atypique.
4. **Environnement préférentiel** : si la conception/§4 implique aussi un attribut
   d'environnement déjà existant (ombre/humidité), s'aligner dessus sans en créer
   un doublon — la fenêtre thermique est le cœur du tronçon.

## Golden
**RE-FIGÉ maîtrisé.** Le typage rend la cloche mordante → certaines levées du smoke
test se décalent/disparaissent selon T_sol. C'est l'effet recherché. Procédure :
lancer le golden, constater la dérive, **re-figer** le hash dans
`tests/test_golden.py`, **annoncer** au commit + cocher ③. Vérifier que la dérive
est **cohérente** (pas d'effondrement total des levées : si plus rien ne germe,
les fenêtres sont trop étroites ou le floor trop haut → réajuster).

## Ce qu'il NE faut PAS faire
- Pas de gène (④), pas de suppression `spring_flush` (⑤).
- Ne PAS importer `fields` depuis `plants` : `t_germ_opt/tol` restent littéraux.
- Ne pas sur-étroitir les fenêtres au point de tuer toute germination — garder un
  jardin vivant.
