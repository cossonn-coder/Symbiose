# Sprint AUTOMNE VISIBLE (D123 + D118 (A) arbres) — état partagé

**Conception** : `docs/rendu/ambiance/conception_automne_visible.md` (figée le 2026-11-02).
**Où on en est** : conception figée, aucun tronçon lancé.

## Décisions clés (Nico, 2026-11-02)

- **A1** Arbres du jardin dans ce sprint ; golden libre de bouger, à annoncer.
- **A2** Feuilles au sol = vérité moteur.
- **A3** Lisière 4 saisons + signes diégétiques macro (style canicule).
- **A4** De D118, seuls les 11 arbres ; le reste est le sprint suivant.

## Carte des tronçons

| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_fiches_banc.md` — fiches des 11 arbres + banc `bancs/mesure_arbres.py` + `mesures/avant.md` | intact | à faire |
| ② | `02_port_arbres.md` — port par fiche, hauteur qui ne s'effondre plus, arbres âgés et caducs de démo | **re-figé annoncé** | à faire |
| ③ | `03_feuilles_moteur.md` — largage étalé sous la couronne + pont (masse de feuilles, `feuillage`) | **re-figé annoncé** | à faire |
| ④ | `04_vue_arbres.md` — recettes d'arbres, couleur d'automne par espèce, couronne qui s'éclaircit | intact | à faire |
| ⑤ | `05_vue_tapis_chute.md` — tapis lisible dès ×1 + animation de chute | intact | à faire |
| ⑥ | `06_vue_lisiere.md` — lisière 4 saisons + signes macro + protocole F5 | intact | à faire |

## Ce qui reste

Tout. Garde-fous : ne JAMAIS lancer `tests/test_epaisseur_500ans.py` ; mesures ≤ 3 ans de jeu.
`test_succession` et `test_edaphique` sont rouges AVANT ce sprint (vérifié le 2026-10-30).

## §REPRISE

Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire ».
Lancer : `/sprint-auto sprint_automne_visible`.
