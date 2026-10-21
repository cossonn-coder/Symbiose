# Sprint INFO-BULLE DU VIVANT — état partagé

> Conception **FIGÉE le 2026-10-22** (`/conception`) →
> [`docs/narration/semiologie/conception_infobulle_vivant.md`](../../../../docs/narration/semiologie/conception_infobulle_vivant.md)
> (LIRE AVANT TOUT TRONÇON). Absorbe **D110 (a)(b)(g)**. **Golden jamais re-figé** :
> référence `22768f33…` (`cd data/code && python3 -m tests.test_golden`). Jamais
> `test_epaisseur_500ans`. Pont de départ : 0.5.46.

## Décisions clés (Nico, 2026-10-22)
1. Nom bête/champignon révélé par **observation en 3 saisons distinctes** (+1 palier par
   saison neuve au survol, plafond `SEUIL_CARNET`) ; champignon = 3 automnes, assumé.
   Règle CLAUDE.md « non identifiable sans maîtrise » conservée.
2. Affichage technique (Maj+F3) : nomme tout dès le 1er survol, avec chiffres.
3. État bête = **abondance** (vue dans le plot) + **nourriture** (`activite`, révélée avec
   le nom). Pas de maladie animale (absente du moteur).
4. Champignon : rôle lu sur place (bois → décompose ; racines → relie ; sinon lie l'humus) ;
   état = densité du réseau.
5. (g) seuil de visibilité **mesuré au rendu** ; voix saine (vert franc / automne / terne).
6. Crédit saisonnier : effet de bord assumé sur `palier_bonus` (Vigueur max ↑ un peu).

## Constats d'entrée (vérifiés au code)
- `SigneDominant` retient l'intensité > 0 ; teinte = intensité × 0,7 puis palette 34.
- Faune : sprite `[r, c, x, y, activite]` ; carpophore `[r, c, x, y, densite]`.
- `ForagerLayer` : aucune ressource reçue (à vérifier/ajouter en ①).
- Dédup vue `_especesMacroObservees` = une fois par session → bloque le crédit saisonnier.

## Carte des tronçons
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| ① | `01_python_corpus_credit.md` | corpus, crédit saisonnier, `appris` champignon, snapshot rôle carpophore, bandes nourriture mesurées, légende, pont bumpé | intact | à faire |
| ② | `02_vue_plante_seuil_voix.md` | seuil mesuré (capture VM) + voix saine + technique | intact | à faire |
| ③ | `03_vue_faune_champignon_bilan.md` | lignes bête/carpophore, dédup (clé, saison), technique, bilan, F5, clôture | intact | à faire |

## Mesures
(à remplir : [machine, n=…] sur chaque chiffre)

## §F5
(procédure écrite par ③)

## §REPRISE
`/sprint-auto sprint_infobulle_vivant` — reprendre au premier tronçon « à faire ».
