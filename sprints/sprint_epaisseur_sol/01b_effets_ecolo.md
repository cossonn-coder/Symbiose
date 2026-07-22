# ①b — Effets écologiques : rétention d'eau + accès NPK

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Prérequis :
> **①a fait** (le champ `epaisseur_sol` stocké + `tick_epaisseur` existent).
> Conception complète : `docs/champs/sol/conception_epaisseur_sol.md` §3.

## Objectif

Faire **agir** l'épaisseur sur l'écologie via **deux flux du sol** (jamais un
bonus direct sur la plante — philo #2). La plante répond émergemment.

## Canal 1 — Rétention d'eau (greffe hydro)

Dans `fields/ecofields/hydrologie.py`, méthode `tick_hydrology`, il y a
**exactement** (autour de la ligne 109) :

```python
h += apport * self.structure_sol.at_plot(r, c)      # 2. pluie infiltrée
h += self.soil_memory.at_plot(r, c) * SOIL_RETENTION  # 3. rétention
perte = h * (1.0 - drainage)                          # ... drainage ensuite
```

Ajoute un **terme miroir de rétention**, juste après la ligne 3, **avant** le
calcul de `perte`/drainage :

```python
h += epaisseur_norm(r, c) * EPAISSEUR_RETENTION * f_composition(soil_type, om_n)
```

- `epaisseur_norm` = épaisseur du plot normalisée (borne haute plausible → [0,1]).
  L'épaisseur est lue depuis `self.epaisseur_sol` — c'est celle du **tick
  précédent** (l'hydro tourne avant `tick_epaisseur`), décalage 1 tick uniforme
  déterministe (voulu, cf. ①a).
- `f_composition` = **module par la composition** : réutilise le patron
  `cec_norm_at(soil_type, om_stable_norm)` de `fields/ecofields/nutriments.py:78`.
  Effet MO **plus fort sur sable** (pauvre, drainant) que sur **argile** (déjà
  rétentrice). `om_n = min(1.0, om_stable/5.0)` (même normalisation que le reste
  du module, cf. `matiere_organique.py:212`).
- `EPAISSEUR_RETENTION` = constante placeholder (`constants.py`, commentée),
  calibrée F5. Doit rester **modérée** : un sol épais tamponne, il ne rend pas la
  sécheresse impossible.

Le revers **asphyxie** (D39, sol gorgé) n'est **pas bridé** — conséquence
émergente assumée.

## Canal 2 — Accès NPK

Le **volume de stock de nutriments accessible à l'uptake** croît avec l'épaisseur.
Trouve la fonction d'uptake racinaire (`plant_uptake` / uptake par nutriment avec
loi de Liebig — cf. `docs/champs/sol/conception_sol_nutriments_npk.md`, module nutriments/uptake).
Module la **fraction du stock disponible** par `epaisseur_norm` : un sol épais met
une plus grande part du stock à disposition.

⚠️ **CROISE D41** (sol déjà affamé : uptake > minéralisation, famine édaphique
VOULUE). **Borne cet effet** :
- effet **plafonné** (ne jamais rendre le NPK infini),
- calibré pour **ne pas masquer ni annuler** la famine D41 — l'épaisseur
  **atténue** la carence sur sol riche/humifère, elle ne la **supprime** pas,
- si le calibrage F5 s'avère impossible sans casser D41, **réduis l'effet à
  symbolique** et note-le en dette plutôt que de fausser la famine.

## Golden

**RE-FIGÉ, ANNONCÉ.** Deux flux neufs (rétention + uptake) changent le
comportement. Dérive attendue : sols épais un peu plus humides et un peu moins
carencés. Lance `python3 -m tests.test_golden`, **comprends** la dérive (localisée
aux plots épais), re-fige. Si la dérive est massive/globale ou emballée → bug,
annule.

## Test 500 ans (anti-emballement) — OBLIGATOIRE

La boucle **litière → épaisseur → rétention d'eau → croissance → plus de litière**
est un **feedback positif** : borne-la. Écris/lance une simulation longue (500
ans, cf. `main.py` qui a tourné 500+ ans) et vérifie :
- l'épaisseur **converge** (ne diverge pas vers l'infini) sur un jardin prospère,
- la famine D41 **reste possible** sur un jardin épuisé,
- pas de tuile qui s'asphyxie systématiquement par emballement rétention.

Conserve le script de test (règle projet : ne jamais jeter de code de test).

## Ce qu'il NE faut PAS faire

- Pas de bonus/malus direct sur la plante — tout passe par les flux du sol (#2).
- Ne pas toucher au rendu ni au snapshot (c'est ②).
- Ne pas re-calculer l'hydrologie ailleurs (piège connu : lire les flux déjà
  calculés, cf. commentaires `hydrologie.py`).
- Ne pas laisser l'accès NPK annuler D41.

## Perf

Deux lectures `at_plot` par plot dans des boucles déjà existantes → négligeable.
Aucun nouveau balayage.
