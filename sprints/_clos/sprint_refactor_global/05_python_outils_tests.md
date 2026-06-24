# SS⑤ — Python outils & tests

> Lire `00_etat.md`. Risque **moyen** : outils et tests ne participent pas
> au hash golden, mais `sim_server.py` est le **pont vers Godot** — toute
> régression casse l'intégration. Vérifier le protocole après découpe.

## Cibles

| Fichier | Lignes | Rôle |
|---------|--------|------|
| `tools/sim_server.py` | 779 | pont sous-process JSON stdin/stdout (protocole 0.3.5) ← critique |
| `tools/render_structure.py` | 592 | maquettes SVG |
| `tests/test_vigueur.py` | 899 | suite Vigueur |
| `tests/test_sim_server.py` | 825 | suite du pont |

## Méthode

- **`tools/sim_server.py`** → paquet `tools/sim_server/` (ou modules
  voisins importés par un mince point d'entrée). Séparer : boucle
  stdin/stdout + dispatch protocole d'un côté ; handlers par commande de
  l'autre (snapshot, actions, heatmaps…). **Le point d'entrée exécuté par
  Godot doit garder son chemin/nom** (`tools/sim_server.py` invoqué par
  `SimBridge.cs`) — si on passe en paquet, garder un `sim_server.py` ou
  ajuster le chemin dans `SimBridge.cs` ET le `.spec` PyInstaller. **Choix
  conservateur : garder `tools/sim_server.py` comme mince entrée** qui
  importe le reste, zéro changement côté Godot/packaging.
- **`render_structure.py`** : séparer logique de rendu / dessin des
  primitives / CLI.
- **Tests** (`test_vigueur`, `test_sim_server`) : découper par thème en
  plusieurs fichiers `test_*.py` (le runner les ramasse). Aucune contrainte
  de hash ; juste rester < 500 l et garder tous les cas (ne RIEN retirer).

## Vérification

```
cd data/code
python3 -m tests.test_golden                 # toujours vert + hash inchangé
python3 -m tests.test_sim_server             # pont OK
python3 -m tests.test_vigueur                # suite Vigueur OK
# pont vivant : un aller-retour réel
python3 tools/sim_server.py  < un_message_test  # ou via le harnais de test
```

Si le `.spec` PyInstaller (`tools/sim_server.spec`) liste des modules
explicitement, le mettre à jour pour la nouvelle arbo (sinon le packaging
t7 casserait plus tard).

## Définition de fait

- [ ] `sim_server` éclaté, **point d'entrée Godot inchangé** (`SimBridge.cs`
      et `.spec` non cassés).
- [ ] `render_structure`, `test_vigueur`, `test_sim_server` < 500 l chacun.
- [ ] Aucun cas de test retiré (conservation totale).
- [ ] Golden vert + hash identique ; suites pont + Vigueur vertes.
- [ ] `00_etat.md` mis à jour → commit → `/clear`.

## Commit suggéré

`refactor(sprint·global) : SS⑤ — sim_server/render/tests éclatés, entrée pont préservée, golden inchangé`
