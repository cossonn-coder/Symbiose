# Sprint PALETTE & TIROIR — état

> Sprint ② de la refonte de l'accès aux gestes. Conception figée le 2026-11-12 :
> `docs/joueur/gestes/conception_refonte_palette.md` §4 (à lire en entier).
> **Prérequis : `sprint_acces_gestes` CLOS** (le pont expose `gestes_pressentis` et
> `familles` dans le bloc `player` du snapshot). Suite : `sprint_icones_curseur`.

## But
Trouver un geste, savoir qu'il existe, voir ses réglages. Pure vue C#.

## Décisions clés (Nico, 2026-11-12)
- **Barre de favoris** : les 10 cases actuelles (touches 1-9, 0, Tab) restent.
- **Tiroir par familles** : montre tous les gestes ouverts et pressentis.
- **Réglages contextuels** affichés près du geste actif ; fin des touches S, B, N.
- **Ctrl+molette** fait défiler le geste actif dans la barre (molette seule = zoom).
- Pressenti = silhouette + phrase d'ambiance au survol, rien d'autre.
- **Macros débranchées de l'interface** (K, J), code conservé.
- D118 (b) et (c) corrigés ici. Icônes définitives et curseur : sprint ③.

## Golden
`b4a921f8…` (ou celui laissé par le sprint précédent : lire `tests/golden_hash.txt`).
**INTACT** : aucun fichier de `data/code/` hors bancs n'est touché.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_tiroir_familles.md` — panneau tiroir, sélection directe, mise en case | à faire |
| ② | `02_reglages_contextuels.md` — graines, substrats, paillis visibles et cliquables | à faire |
| ③ | `03_pressentis_molette_finitions.md` — silhouettes, Ctrl+molette, D118 (b)(c), macros, banc, clôture | à faire |

## Interdits communs
- Ne JAMAIS lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.
- Ne supprimer aucun code (macros comprises). GDScript interdit.
- Un fichier = une responsabilité ; > 300 LDC (`tools/compte_ldc.py`) → scinder.
- `dotnet build Symbiose.csproj` vert à chaque tronçon ; captures VM
  (`tools/capture_vm.sh`) regardées avant de conclure.

## Constats d'exécution
(à remplir)

## §REPRISE
Lire `CLAUDE.md`, ce fichier, le doc de conception §4, puis le premier kickoff « à faire ».
