# Sprint ACCÈS AUX GESTES — état

> Sprint ① de la refonte de l'accès aux gestes (3 sprints). Conception figée le
> 2026-11-12 : `docs/joueur/gestes/conception_refonte_palette.md` (à lire en entier).
> Suite : `sprint_palette_tiroir` puis `sprint_icones_curseur`.

## But
Rendre **tous** les gestes du moteur atteignables en jeu normal et jouables dans la
vue. Aujourd'hui 20 gestes gatés sur 32 ne s'ouvrent jamais (poule-œuf : la
technique n'est découverte qu'en utilisant le geste qu'elle verrouille) et 10 gestes
n'existent pas dans la vue. Ferme D133.

## Décisions clés (Nico, 2026-11-12)
- On **garde** `GESTE_UNLOCK` ; on **ajoute** `PORTES_TECHNIQUE` : franchir une porte
  DÉCOUVRE la technique (palier 1), ce qui rend vraies les conditions existantes.
- Quatre portes : Atelier, geste de base voisin, observation, courrier.
- Posséder une structure offerte vaut l'avoir posée.
- Trois états : inconnu / pressenti (calculé) / ouvert. Pressenti = silhouette +
  phrase d'ambiance, jamais la piste.
- `FAMILLE_GESTE` (8 familles) vit en Python, exposée au pont.
- Test d'atteignabilité permanent.

## Golden
`b4a921f8…` (`tests/golden_hash.txt`). **INTACT sur les 4 tronçons** : état joueur
opt-in, hooks au-dessus du tick. S'il bouge : fuite dans le tick → annuler, ne
jamais re-figer.

## Tronçons
| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_portes_atteignabilite.md` — table des portes, conditions `stock`/`compte`, test du point fixe | intact | à faire |
| ② | `02_atelier_courrier_observations.md` — outils neufs, récompense `technique`, lettres, marqueurs d'observation | intact | à faire |
| ③ | `03_pressentis_familles_pont.md` — pressentis + phrases, familles, routes supports/couvertures, snapshot, bump pont | intact | à faire |
| ④ | `04_vue_minimale_banc.md` — gestes manquants dans `Gestes[]`, banc F5 | intact | à faire |

## Interdits communs à tous les tronçons
- Ne JAMAIS lancer `tests/test_epaisseur_500ans`.
- Pas de `ps aux` / `pgrep -f` ; `uptime` pour la charge.
- Ne supprimer aucun code existant (macros, anciens tests).
- Aucun appel DeepSeek de routine ; un besoin de fouille = kickoff incomplet → le
  consigner ici.

## Constats d'exécution
(à remplir par les tronçons)

## §REPRISE
Lire `CLAUDE.md`, ce fichier, le doc de conception, puis le premier kickoff « à faire ».
