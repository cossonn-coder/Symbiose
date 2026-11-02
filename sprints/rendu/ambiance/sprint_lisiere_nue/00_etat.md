# Sprint LISIÈRE NUE (D124) — état partagé

**Conception** : `docs/rendu/ambiance/conception_lisiere_nue.md` (figée le 2026-11-02).
**Où on en est** : conception figée, aucun tronçon lancé.

## Décisions clés (Nico, 2026-11-02)

- Branches derrière la couronne, révélées par le dégarnissement ; neige et givre dessus.
- Fleurs en colonies réalistes, vérité moteur ; les pollinisateurs y mangent et s'y voient.
- Couronne d'hiver réaliste : feuilles sèches sur hêtre, charme, chêne ; bouleau nu.
- Damier de l'assise cassé.
- Cadence ok mais vigilance : tick an 2 ≤ +10 %, draw calls constants, rien de reconstruit par semaine.

## Carte des tronçons

| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_colonies_moteur.md` — colonies, nourriture, pont 0.6.4, mesure sur 3 ans | intact attendu (smoke sans ceinture) | à faire |
| ② | `02_vue_fleurs_damier.md` — fleurs en colonies, butineurs de bord, damier | intact | à faire |
| ③ | `03_vue_branches.md` — branches, couronne d'hiver, protocole F5 | intact | à faire |

## Ce qui reste

Tout. D119 (c) (butineurs dès l'an 1) se ferme si la mesure du ① le confirme.
Garde-fous : ne JAMAIS lancer `tests/test_epaisseur_500ans.py` ; mesures ≤ 3 ans de jeu.
`test_succession` et `test_edaphique` étaient rouges avant le sprint AUTOMNE VISIBLE.

## §REPRISE

Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire ».
Lancer : `/sprint-auto sprint_lisiere_nue`.
