# Sprint CALENDRIER UNIQUE (D122) — état partagé

**Conception** : `docs/champs/climat/conception_calendrier_unique.md` (figée le 2026-10-30).
**Où on en est** : ① FAIT (banc + `mesures/avant.md`, golden intact) ; ② à lancer.

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
| ① | `01_banc_mesure.md` — banc `bancs/mesure_calendrier.py` + `mesures/avant.md` | intact | **fait** |
| ② | `02_calendrier_unique.md` — `calendrier.py` + décalage des 4 courbes + `mesures/apres_decalage.md` | **re-figé LARGE annoncé** | à faire |
| ③ | `03_recalibrage.md` — fenêtres au mois réel (aléas, champignons, abscission) + seuils sur écarts mesurés + bancs F5 + `mesures/apres_recalibrage.md` | **re-figé annoncé** | à faire |
| ④ | `04_vue.md` — audit C# saisonnier, `dotnet build`, protocole F5 « une année » | intact | à faire |

## Chiffres AVANT (①, `mesures/avant.md`)

- Glace de la mare (tourbière) : 10 / 11 / 1 sem. au **printemps** [n=3 ans, VM], 0-1 en hiver.
- T_air hebdo jamais < 0 : 0 sem. de gel en 3 ans [n=3 ans, VM] ; T min annuelle en
  hiver (an 1, s51) ou printemps (an 2 s9, an 3 s1) [n=3 ans, VM].
- Pommier (`floraison_saisons`) : bloom s14-s15 = **été** [n=3 ans, VM] ; recouvrement
  0/2 puis 2/2 sem. ; 0-2 fruits. Jour le plus long s25 (été, `daylength`).
- Tomates du smoke : disparues s23 (été) an 1 ; abscission 1ʳᵉ s35 chaque année ;
  carpophores (coprin seul) été/automne/hiver, jamais au printemps [n=3 ans, VM].
- Pommier du smoke : jamais fleuri en 3 ans → indicateur 4 lu sur `floraison_saisons`.

## Ce qui reste

②, ③, ④. Rejouer `python3 -m bancs.mesure_calendrier 3` en fin de ② et ③. Garde-fous : ne JAMAIS lancer `tests/test_epaisseur_500ans.py` ; mesures ≤ 3 ans.

## §REPRISE

Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire » (②).
Lancer : `/sprint-auto sprint_calendrier_unique`.
