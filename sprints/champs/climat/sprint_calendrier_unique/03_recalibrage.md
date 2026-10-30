# ③ Recalibrage sur mesure — golden RE-FIGÉ (annoncé)

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (tableau avant/après de ②),
`docs/champs/climat/conception_calendrier_unique.md` (§4 table mois → semaine, §5
fenêtres proposées, §6 critère), `mesures/avant.md`, `mesures/apres_decalage.md`.

## Objectif

Remettre au **mois réel** tout ce qui est calé sur une semaine précise, puis ne
recalibrer un seuil que sur un **écart mesuré** (décision C3). Le climat est désormais
juste (②) ; ici on réaligne ce qui s'y rapporte.

## À faire

1. **Fenêtres au mois réel** (conception §5 — les propositions y sont chiffrées) :
   - aléas `sim/weather._CATALOGUE` (gelée tardive 2-9, canicule 12-24, sécheresse
     12-28, grêle 7-22, orage 8-24, neige 38-49, autres inchangés) + son commentaire
     d'en-tête ;
   - fenêtres de `fields/fongique.REGISTRE_FONGIQUE` (table §5) + le commentaire
     « Calendrier moteur… sem. 43 = fin novembre » ;
   - `fields/ecofields/constants.ABSCISSION_MIN/MAX` 34-39 → 30-36 ;
   - `bois_chute_semaine` des espèces (`plants/species/sauvages.py`, `aromatiques.py`) :
     relire chacune avec la table §4 et le commentaire qui la motive ; ne changer que
     si l'intention écrite contredit le mois obtenu.
   Les nombres du §5 sont une proposition écologique arbitrée ; un écart se justifie en
   une ligne dans le commit, sinon on les applique tels quels.
2. **Re-mesurer** → `mesures/apres_recalibrage.md`.
3. **Seuils, uniquement si un indicateur reste rouge** (critère §6 : contredit la réalité
   — gel en été, pommier fleuri hors printemps, recouvrement pollinisateurs ≈ 0, tomate
   morte de froid au printemps, carpophore hors de sa saison) :
   - floraison : `bloom_forcing_gdd` par espèce / `T_BASE_FLORAISON`
     (`sim/engine/floraison.py`), remise à zéro des degrés-jours en wiy 1 ;
   - porte photopériodique des pollinisateurs (`DEF_DAYLEN_MIN/FULL`,
     `fields/population/constants.py`).
   Une modification par cause, chacune justifiée par la ligne de mesure qui l'exige.
   Si un rouge ne se résout pas par un réglage simple, **ne pas forcer** : le consigner
   dans `00_etat.md` comme point F5 / candidat dette.
4. **Bancs F5** (`bancs/__init__.BANC_WEEK_DEPART`) : leurs semaines de départ ont été
   choisies sous l'ancien climat (s9 « ~6 °C » devient mi-mai, `effondrement` 1309 dépend
   des fenêtres d'aléas). Relire chaque commentaire, recalculer la semaine qui remplit
   l'intention écrite ; pour `effondrement`, retrouver une semaine où le ciel composé est
   déjà au plomb et une grêle locale suit (outil : `sim/ciel.py` + `weather_at`), sinon
   point F5.
5. **Golden** : re-figé (attendu), hash consigné. Autres suites vertes (SAUF
   `test_epaisseur_500ans.py`) ; mêmes règles qu'en ② pour les tests figeant une semaine.
6. `00_etat.md` : tableau final avant → après décalage → après recalibrage (≤ 12 lignes,
   chiffres marqués `[n=… ans, VM]`).

## Golden

**RE-FIGÉ, annoncé** : fenêtres d'aléas, de fructification, d'abscission et seuils
éventuels déplacés au calendrier réel.

## NE PAS

- Retoucher le décalage climatique de ② (W_T_MIN, W_SOLSTICE_ETE).
- Recalibrer sans ligne de mesure qui le demande.
- Toucher la déclinaison solaire, le C#.
- Lancer `tests/test_epaisseur_500ans.py`.
