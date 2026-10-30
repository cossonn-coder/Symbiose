# Sprint CALENDRIER UNIQUE (D122) — état partagé

**Conception** : `docs/champs/climat/conception_calendrier_unique.md` (figée le 2026-10-30).
**Où on en est** : conception figée, aucun tronçon lancé.

## Décisions clés (Nico, 2026-10-30)

- **C1** L'année commence à l'**équinoxe de printemps** (wiy 1 ≈ 20 mars) : on décale le
  CLIMAT de 11 semaines (T min/HR max/vent wiy 4 → 45, solstice 25 → 14), on garde
  les étiquettes de saison (printemps 1-13 … hiver 40-52).
- **C2** Un seul calendrier en couche basse : `data/code/calendrier.py` (racine, zéro
  dépendance) ; `sim/engine/calendrier.py` le ré-exporte ; les copies locales le lisent.
- **C3** **Mesurer d'abord, recalibrer après** : banc de mesure figé avant, rejoué après.
- **C4** Soleil (déclinaison par saison) hors périmètre.

## Carte des tronçons

| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_banc_mesure.md` — banc `bancs/mesure_calendrier.py` + `mesures/avant.md` | intact | à faire |
| ② | `02_calendrier_unique.md` — `calendrier.py` + décalage des 4 courbes + `mesures/apres_decalage.md` | **re-figé LARGE annoncé** | à faire |
| ③ | `03_recalibrage.md` — fenêtres au mois réel (aléas, champignons, abscission) + seuils sur écarts mesurés + bancs F5 + `mesures/apres_recalibrage.md` | **re-figé annoncé** | à faire |
| ④ | `04_vue.md` — audit C# saisonnier, `dotnet build`, protocole F5 « une année » | intact | à faire |

## Ce qui reste

Tout. Garde-fous : ne JAMAIS lancer `tests/test_epaisseur_500ans.py` ; mesures ≤ 3 ans.

## §REPRISE

Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire ».
Lancer : `/sprint-auto sprint_calendrier_unique`.
