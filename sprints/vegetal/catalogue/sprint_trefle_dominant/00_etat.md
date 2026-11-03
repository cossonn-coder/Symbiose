# Sprint TRÈFLE DOMINANT (D126) — état partagé

**Conception** : `docs/vegetal/catalogue/conception_trefle_dominant.md` (figée le 2026-11-02).
**Où on en est** : conception figée, aucun tronçon lancé. Golden de départ `ac48b170…`.

## Décisions clés (Nico, 2026-11-02)

- Un tapis qui bouge, sans plafond : le cycle azote-graminées fait reculer le trèfle.
- 4 espèces spontanées en plus : dactyle, fétuque rouge, plantain lancéolé (neuves) ; ortie (existante).
- Vue : trèfle et espèces neuves ; le reste attend D118.
- Trèfle à quatre feuilles rare ; le récolter donne un bonus au joueur.

## Carte des tronçons

| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_cycle_azote.md` — fixation freinée, renouvellement des stolons | re-figé annoncé | à faire |
| ② | `02_flore_spontanee.md` — 3 espèces neuves + ortie, 5 voix, mesure de l'effet | re-figé annoncé si des levées du smoke changent | à faire |
| ③ | `03_quatre_feuilles.md` — fonction pure, récolte, bonus, pont | intact | à faire |
| ④ | `04_vue_prairie.md` — tapis, quatre feuilles, formes, protocole F5 | intact | à faire |

## Ce qui reste

Tout. Garde-fous : ne JAMAIS lancer `tests/test_epaisseur_500ans.py` ; mesures ≤ 5 ans de jeu. Déjà rouges avant ce sprint : `test_succession`, `test_edaphique`, `test_parasite` (`IndexError` dans `deposer_litiere`).

## §REPRISE

Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire ». Lancer : `/sprint-auto sprint_trefle_dominant`.
