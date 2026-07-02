# ③ — Marécage (`marais_memory` + hystérèse + effets)

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/conception/CONCEPTION_HYDROLOGIE_MARECAGE.md` §3. **Golden NEUTRE hors banc.**
> Prérequis : ② fait (`eau_surface` existe).

## Objectif
Une flaque qui DURE fait basculer le plot en **marécage** : état persistant,
anaérobie (décompo ↓ → tourbe), acide (pH ↓), niche ouverte pour les espèces
marécageuses (⑤⑥). Émergent, pas scripté (philo #2/#6).

## Fichiers
- `fields/ecofields/container.py` : champ `marais_memory: GridField(max_val=1.0)`
  (initial 0) + registre.
- `fields/ecofields/` (module hydrologie/ruissellement ou neuf) : `tick_marais()`
  — intégration + hystérèse (helper `est_marais(r,c)` lisant l'hystérèse).
- `fields/ecofields/matiere_organique.py` (`tick_decomposition`/`speed`) : moduler
  `speed *= (1 − MARAIS_DECOMP_MALUS * marais_memory[r][c])` (anaérobie). Couple D40.
- `fields/ecofields/ph.py` (`tick_ph`) : pousser le pH vers `PH_TOURBE` ∝
  `marais_memory` (terme additif borné).
- `sim/engine/boucle.py` : appeler `tick_marais()` après `tick_ruissellement` et
  AVANT `tick_decomposition`/`tick_ph` (ils lisent le marais du tick — ou décalage
  1 tick uniforme, au choix documenté).
- `fields/ecofields/constants.py` : `MARAIS_LERP`, `MARAIS_ON`, `MARAIS_OFF`,
  `MARAIS_DECOMP_MALUS`, `PH_TOURBE`, `PH_MARAIS_LERP` (placeholders).
- `data/code/bancs/` : banc `tourbiere` (cuvette gorgée forcée : altitude basse +
  humidité/eau_surface hautes) + `data/code/tests/bancs/` oracle (le plot bascule
  marais, décompo chute, pH baisse). Brancher dans `cmd_init` (hors smoke/full).
- `tools/simserver/serialize.py` : bloc `marais` par tuile (liste creuse) + bump.
- `tests/test_marais.py` : entrée/sortie hystérèse, effets décompo/pH.

## Modèle
```
cible = 1.0 if eau_surface[r][c] > SEUIL_FLAQUE else 0.0
marais_memory[r][c] += (cible − marais_memory[r][c]) * MARAIS_LERP     # LENT (semaines)
est_marais = marais_memory > MARAIS_ON  (entrée) / < MARAIS_OFF (sortie)   # hystérèse
```
Tourbe = **émergent** : décompo ↓ → `om_fresh/active` s'accumule → `_cible_epaisseur`
monte → épaisseur monte. **Aucun code neuf pour la tourbe** (juste le malus décompo).

## Golden
**NEUTRE** : le smoke reste SANS cuvette profonde → `eau_surface` ~0 → `marais_memory`
~0 → décompo/pH inchangés → `test_golden` **inchangé** (hash ②). ⚠️ Vérifier que
l'ajout des ticks/lectures ne bouge pas le digest sur le smoke (marais=0 ⇒ facteurs
neutres ×1.0). Si le smoke bascule, re-figeage MAÎTRISÉ annoncé (préférer calibrer).
Le banc `tourbiere` (hors golden) prouve le mécanisme via son oracle.

## Ce qu'il NE faut PAS faire
- Ne pas coder un « type de sol marais » scripté — c'est un état ÉMU (mémoire+seuil).
- Ne pas dupliquer l'accumulation de tourbe (elle sort du malus décompo, pas d'un
  ajout direct à l'épaisseur).
- Pas encore d'espèces (⑤⑥) ni de faune (④).

## F5
- Une cuvette gorgée finit-elle par « noircir » en marais (§7) ? Durée de bascule
  crédible (`MARAIS_LERP`) ? Assèchement fait-il ressortir (hystérèse) ?
