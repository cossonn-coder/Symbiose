# Tronçon ② — Porte thermique NEUTRE sur la niche de germination

> Kickoff **autosuffisant** (lis CLAUDE.md + 00_etat.md + ce fichier).
> Conception : `CONCEPTION_GERMINATION_THERMIQUE.md` §1. Lancement depuis
> `data/code/`. Golden : **INTACT** (la porte démarre plate).

## Objectif
Brancher la porte thermique `bell(T_sol, t_opt_eff, t_germ_tol)` sur la niche aux
**3 points** de germination, mais avec un défaut **PLAT** (`t_germ_tol` large →
cloche ≈ 1.0 partout) → la germination ne change pas → **golden inchangé**. On
pose la plomberie ; le typage qui la rend mordante vient au ③.

## Patron à copier (porte pH déjà en place)
- `bell(val, opt, tol)` = `fields/ecofields/nutriments.py:38`, pure, vaut 1.0 au
  centre, plate si `tol` large.
- Lecture T_sol spatialisée : `eco.temperature_sol.at_plot(r, c)` (patron exact de
  `mycelium.py:58`, `matiere_organique.py:144`).

## À faire
1. **`plants/base/familles.py`** — sur `PlantBase`, **EXACTEMENT** le patron des
   attributs pH (l.82-93), en **littéraux** (la couche `plants` n'importe JAMAIS
   `fields`) :
   ```python
   t_germ_opt: float = 18.0   # T_sol optimale de levée (°C)
   t_germ_tol: float = 30.0   # demi-largeur LARGE → cloche plate → neutre au départ
   ```
   `t_germ_tol` doit être assez large pour que `bell` ≈ 1.0 sur toute la plage de
   T_sol rencontrée au golden (sinon dérive). Vérifier au golden.
2. **`sim/succession.py` — point 1, `_lever_grains_en_attente` (l.40)** : juste
   après la porte pH (l.104 `niche *= bell(eco.ph.at_plot(r,c), plant_class.ph_opt,
   plant_class.ph_tol)`), ajouter :
   ```python
   niche *= bell(eco.temperature_sol.at_plot(r, c),
                 plant_class.t_germ_opt, plant_class.t_germ_tol)
   ```
   (pas encore de gène ni de plancher — ②, on garde simple.)
3. **`fields/seedbank.py:287` `germination_candidates`** : ajouter un paramètre
   `arch_temp=None` (même patron que `arch_ph`), et dans le corps, après le bloc
   `if arch_ph:` (l.321-322) :
   ```python
   if arch_temp:
       niche_eff *= arch_temp.get(archetype, 1.0)
   ```
4. **`sim/succession.py` — point 2, `succession` (l.133)** : construire un dict
   `arch_temp` symétrique à `arch_ph` (l.199), p.ex. :
   ```python
   arch_temp = {a: bell(eco.temperature_sol.at_plot(r, c), cls.t_germ_opt,
                        cls.t_germ_tol) for a, cls in WEED_CATALOGUE.items()}
   ```
   et le passer à `germination_candidates(..., arch_temp=arch_temp)`.
5. **`spring_flush` (l.236)** : **NE PAS y toucher** ici (suppression au ⑤).

## Golden
**INTACT.** Vérifier `python3 -m tests.test_golden` → hash **inchangé**. Si dérive,
c'est que `t_germ_tol` n'est pas assez large : l'élargir jusqu'à neutralité.
NE PAS re-figer à ce tronçon — un golden qui bouge ici est un **bug**, pas une
dérive maîtrisée.

## Ce qu'il NE faut PAS faire
- Pas de plancher froid, pas de gène, pas de typage d'espèce (③④).
- Ne pas supprimer `spring_flush` (⑤).
- Ne pas câbler le 3ᵉ point dans `spring_flush` (il disparaît au ⑤).
