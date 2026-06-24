# SS④ — Python cœur sim 2 : actions, base, species, growth

> Lire `00_etat.md` + la **méthode du SS③** (paquet + `__init__.py` qui
> ré-exporte l'API) : identique ici, ne pas la redétailler. Tronçon **à
> RISQUE ÉLEVÉ**, golden vérifié après chaque module.

## Cibles

| Fichier | Lignes | Couche | Note |
|---------|--------|--------|------|
| `sim/actions.py` | 775 | sim | gestes joueur + `cout_action` |
| `plants/base.py` | 738 | plants | `GrowthStage`/`PlantInstance`/`ConflictNotification`/`PlantBase` + 5 familles + empreintes + registre d'effets |
| `plants/species.py` | 654 | plants | catalogue d'espèces (données) |
| `sim/growth.py` | 503 | sim | morphogénèse segments + auxine + phototropisme (tout juste au-dessus) |

## Découpes pressenties (à confirmer en lisant)

- **`plants/base.py`** : candidat naturel à `plants/base/` avec
  séparation `stages.py` (GrowthStage), `instance.py` (PlantInstance,
  ConflictNotification), `familles.py` (les 5 familles + PlantBase),
  `empreintes.py`, `effets.py` (registre). C'est le module le plus
  structurant — soigner le plan AVANT de couper, c'est le socle de
  `plants ← fields ← sim`.
- **`sim/actions.py`** : séparer par famille de gestes (planter/arroser,
  tailler, écraser/déraciner, manger…) + `cout_action` à part.
- **`plants/species.py`** : données → découper par groupe d'espèces
  (annuelles / vivaces / indicatrices…) ré-exportées par `__init__.py`.
- **`sim/growth.py`** (503, marge faible) : si la séparation
  morphogénèse / auxine-phototropisme tient naturellement, la faire ;
  sinon dépassement léger → **signaler + justifier** (cf règle exceptions).

## Vérification (après CHAQUE module)

```
cd data/code
python3 -m tests.test_golden      # vert + hash INCHANGÉ
python3 main.py
```

`base.py` et `species.py` touchent la couche `plants` : lancer aussi
`tests.test_genetique`, `tests.test_croissance`, `tests.test_senescence`.
`actions.py` : `tests.test_planter`, `tests.test_eau`, `tests.test_structures`.

Hash qui bouge → revenir (cf SS③).

## Définition de fait

- [ ] Les 4 ensembles : chaque fichier < 500 l code (ou exception
      growth.py signalée+justifiée à Nico).
- [ ] API publique inchangée (imports appelants intacts).
- [ ] Golden vert + **hash identique** ; `main.py` tourne ; suites ciblées
      vertes.
- [ ] `00_etat.md` mis à jour → commit → `/clear`.

## Commit suggéré

`refactor(sprint·global) : SS④ — actions/base/species/growth éclatés, golden inchangé`
