# SS③ — Python cœur sim 1 : engine, ecofields, effects

> Lire `00_etat.md`. Tronçon **à RISQUE ÉLEVÉ** : on découpe des modules
> centraux du moteur. Le golden est le filet — vérifier le hash **après
> chaque module éclaté**, pas seulement à la fin.

## Cibles

| Fichier | Lignes | Couche |
|---------|--------|--------|
| `sim/engine.py` | 967 | sim/engine |
| `fields/ecofields.py` | 863 | fields |
| `sim/effects.py` | 703 | sim |

## Méthode (la même pour les trois)

Transformer le module surdimensionné en **paquet** dont l'`__init__.py`
**ré-exporte l'API publique** — ainsi tous les imports existants
(`from sim.engine import X`, `import fields.ecofields as …`) continuent de
marcher **sans toucher un seul appelant**. C'est la clé d'un refactor à
comportement identique.

Exemple pour `sim/engine.py` → paquet `sim/engine/` :

```
sim/engine/
  __init__.py        # re-exporte : from .boucle import Engine ; from .xxx import ...
  boucle.py          # la boucle de tick principale
  <responsabilité_2>.py
  <responsabilité_3>.py
```

Étapes par module :
1. **Lire le module**, repérer les groupes de responsabilité (classes,
   familles de fonctions qui vont ensemble). Tracer le plan de découpe
   AVANT de couper.
2. `git mv sim/engine.py sim/engine/__init__.py` (préserve l'historique),
   puis extraire chaque groupe vers `sim/engine/<nom>.py`.
3. Dans `__init__.py`, ne garder que les **ré-exports** (`from .x import …`)
   + éventuellement une courte docstring pédagogique d'orientation.
4. **Imports internes** : entre sous-fichiers d'un même paquet, imports
   relatifs (`from .boucle import …`). Respecter la règle de couches
   `plants ← fields ← sim ← engine` : un sous-fichier ne doit pas créer
   d'import remontant.
5. Chaque nouveau fichier **< 500 l de code** (vérifier `compte_ldc.py`),
   commentaires pédagogiques conservés/renforcés.

## Vérification (CRITIQUE, après CHAQUE module)

```
cd data/code
python3 -m tests.test_golden      # vert + hash INCHANGÉ
python3 main.py                    # tourne sans crash (réf comportementale)
```

Si le hash bouge → un comportement a changé (ordre d'exécution, effet de
bord d'import, état partagé). **Revenir** et comprendre avant de continuer.
Lancer aussi les suites ciblées impactées (`tests.test_vigueur`,
`tests.test_population`, etc.) selon les modules touchés.

## Définition de fait

- [ ] `sim/engine/`, `fields/ecofields/` (ou découpe équivalente),
      `sim/effects/` : chaque fichier < 500 l code.
- [ ] API publique inchangée (aucun appelant modifié, ou modif triviale
      d'import justifiée).
- [ ] Golden vert + **hash identique** ; `main.py` tourne.
- [ ] `compte_ldc.py` confirme : plus aucun de ces 3 ensembles > 500 l.
- [ ] `00_etat.md` mis à jour → commit → `/clear`.

## Commit suggéré

`refactor(sprint·global) : SS③ — engine/ecofields/effects éclatés en paquets (API ré-exportée), golden inchangé`
