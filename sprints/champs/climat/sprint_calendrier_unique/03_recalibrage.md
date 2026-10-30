# ③ Recalibrage sur mesure — golden RE-FIGÉ (annoncé)

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (tableau avant/après de ②),
`docs/champs/climat/conception_calendrier_unique.md` (§4 table mois → semaine, §5
fenêtres proposées, §6 critère), `mesures/avant.md`, `mesures/apres_decalage.md`.

## Objectif

Remettre au **mois réel** tout ce qui est calé sur une semaine précise, puis ne
recalibrer un seuil que sur un **écart mesuré** (décision C3). Le climat est désormais
juste (②) ; ici on réaligne ce qui s'y rapporte.

## À faire

0. **Réveil THERMIQUE des ravageurs (décision Nico C5, 2026-10-30 — option 1, philo #2)**.
   Cause des 7 suites rouges de ② (cf. `00_etat.md` « Entrées de ③ » §1) : la porte
   photopériodique ouvre les ravageurs dès wiy 1 (jours ≥ 12 h à l'équinoxe) → pression
   0,02-0,04 > seuil létal 0,015 de `sim/effects/perturbations.herbivory_pressure` →
   semis morts en 3-4 semaines.
   - **Vérifié au code** : il existe DÉJÀ une rampe thermique instantanée `warmth`
     (`T_COLD_ZERO` 3 °C → `T_WARM_FULL` 15 °C, `fields/population/constants.py`),
     GLOBALE à toutes les guildes, multipliée à `phenology` dans
     `fields/population/field.py` `tick()`. Elle ne suffit pas à retenir les ravageurs
     au printemps frais.
   - **Intention** (le moyen est à trancher par mesure, l'hypothèse est réfutable) : les
     guildes `category="ravageur"` (puceron, limace, doryphore — `registry.py`) se
     réveillent sur un signal **thermique propre** (dans la réalité, l'éclosion des
     pucerons suit une somme de degrés-jours, pas la longueur du jour). Piste la plus
     simple d'abord : une rampe thermique PAR GUILDE dans `TrophicSpec` (même schéma que
     `daylen_min/full`, défaut = valeurs globales actuelles → autres guildes
     bit-identiques). Si la rampe instantanée ne suffit pas, passer à une somme de
     degrés-jours (état déterministe, remis à zéro en wiy 1).
   - **Interdit** (option 2 écartée par Nico) : relever le seuil 0,015 ou toucher la
     formule de `herbivory_pressure` — on agit sur le FLUX (la population), pas sur
     l'effet sur la plante.
   - **Critère** (mesuré, `[n=… ans, VM]`) : pression ravageur < 0,015 sur les plots
     semés en wiy 1-6 ; ravageurs bien présents fin printemps → été (la boucle
     ravageur → auxiliaire doit rester observable) ; les 7 suites rouges redeviennent
     vertes SANS les isoler ni les contourner. Si une suite reste rouge pour une AUTRE
     cause, la consigner, ne pas forcer.
   - **Précision Nico (C5bis)** : une mortalité PARTIELLE des semis est acceptable
     (génétique, météo, emplacement, ravageurs) ; seule l'hécatombe systématique est
     refusée. Et surtout : « les ravageurs viennent quand il y a déjà des plantes pour
     les nourrir » → la population suit la ressource hôte avec un délai de
     colonisation (vérifier le plancher `habitat_w·habitat` et l'inertie), en plus de
     la porte thermique ou à sa place.
   - Faire ce point **en premier** (il conditionne toutes les mesures suivantes).

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
