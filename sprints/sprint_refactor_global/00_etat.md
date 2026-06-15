# Sprint REFACTOR GLOBAL — état partagé

> État léger, mis à jour en **fin de chaque tronçon**. Lire ce fichier +
> le `0N_*.md` du tronçon courant suffit à reprendre à froid.

## But du sprint

Refactor de tout le dépôt (Python + C# + docs) pour s'y retrouver :
regrouper les fichiers par nature, supprimer les fossiles, et faire passer
**chaque fichier sous ~500 lignes de CODE PUR** (commentaires pédagogiques
exclus du décompte et **conservés au cœur des fichiers**).

## Invariants ABSOLUS (toute la durée du sprint)

1. **Golden jamais re-figé.** `cd data/code && python3 -m tests.test_golden`
   reste vert et le hash golden **ne bouge pas** : un refactor ne change
   AUCUN comportement. Si le hash bouge → on s'est trompé, on revient.
2. **Build Godot OK** après tout tronçon C# (compile sans erreur).
3. **~500 lignes de code pur max par fichier.** Convention de comptage =
   `tools/compte_ldc.py` (livré au SS①). Exception tolérée seulement si
   signalée + justifiée à Nico.
4. **Commentaires pédagogiques préservés et centraux** — jamais sacrifiés
   pour gagner des lignes.
5. **Granularité pragmatique** : un fichier = une classe / un concept
   cohérent (PAS une-fonction-par-fichier). Python éclaté → paquet avec
   `__init__.py` qui ré-exporte l'API publique (imports existants intacts).
6. **Avant chaque tronçon : git à jour.** Un commit par tronçon, puis
   `/clear`. Pas de suppression de code utile (cf décision ci-dessous).

## Décisions actées (2026-06-15, conversation kickoff)

- **Suppression** : seulement les fossiles (non modifiés depuis avril ET
  inutiles). Tout ce qui date de mai/juin = rangé/archivé, jamais supprimé.
- **Racine conservatrice** : Python reste dans `data/code/`, Godot à la
  racine (chemins `res://`, `.csproj`, pont `SimBridge` inchangés).
- **`docs/desktop/`** : gardé tel quel (usage propre : export app desktop).
- **Journal** : éclaté par sprint + `journal.md` = index de pointeurs.
- **Seuil 500** : recalibré en clôture (SS⑦) sur le max empirique mesuré.

## Tronçons

| SS | Titre | Risque | Statut |
|----|-------|--------|--------|
| ① | Déchets & docs/conception + helper comptage | nul | ⬜ à faire |
| ② | Journal éclaté (index + par sprint) | faible | ⬜ |
| ③ | Python cœur sim 1 (engine, ecofields, effects) | élevé | ⬜ |
| ④ | Python cœur sim 2 (actions, base, species, growth) | élevé | ⬜ |
| ⑤ | Python outils & tests (sim_server, render, 2 tests) | moyen | ⬜ |
| ⑥ | C# WorldView (1759 l) | moyen | ⬜ |
| ⑦ | C# reste & finition + grave règles dans CLAUDE.md | moyen | ⬜ |

## Reprise

Tronçon courant : **SS①**. Lire `01_dechets_docs.md`.

## Journal de bord (rempli en fin de tronçon)

- (rien encore)
