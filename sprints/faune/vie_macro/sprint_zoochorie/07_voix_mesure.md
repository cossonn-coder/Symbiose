# ⑦ Voix de la dispersion + mesure longue (D42)

Lire d'abord : `CLAUDE.md`, `00_etat.md`, doc
`docs/faune/vie_macro/conception_zoochorie.md` (tout). Faits : ①-⑥ (grain sauvage,
chute unifiée + glandée, noisetier, merle + perchoir, geai + écureuil + ceinture,
mulot ; golden re-figé au ⑥ — hash courant dans `00_etat.md`).

## Objectif
Faire parler la dispersion, puis mesurer sur 200 ans qu'elle tient le critère D130
**avec** les bêtes, et que la nucléation se voit.

## Voix
Le ledger (`sim/evenements.py`) transforme des lignes de log en événements : lire
comment il reconnaît `🌱 Levée`, `🍎 Nouaison`, `🍂 Chute fruit` et y brancher :
- **levée d'un grain sauvage** par origine (`🌱 Levée (semé par merle|geai|ecureuil|
  mulot|chute|ceinture)`, format posé au ①) ;
- **glandée** : une ligne de log à la nouaison d'une année forte (à ajouter dans
  `_tick_fruits`, une fois par espèce et par an, pas par pied) ;
- prises du merle/geai/écureuil et prédation du mulot (lignes du ④-⑥) — événement
  agrégé, pas un par semaine si le carnet en serait noyé (regarder comment la
  chute de fruits est dédoublonnée).
- **Carnet** (`sim/carnet.py`, `CONCEPT_DE`) : concept neuf `dispersion`, gabarits
  descriptif (« un jeune cerisier a levé sous le vieux poirier mort — je n'en ai pas
  semé ») et interprétatif (« le merle mange les cerises et sème sous ses
  perchoirs ») ; concept `glandee` ou rattachement à `dispersion` (choisir, justifier).
  Le crédit de maîtrise : vérifier dans `sim/maitrise_detection.py` si une levée de
  plante crédite déjà un concept (transition « reproduit ») ; si le concept ne peut
  jamais passer interprétatif, le noter au titre de **D95**, ne pas inventer une
  route de crédit.
- **Encyclopédie** : niveau 3 (effets) du merle, geai, écureuil, mulot, cerisier,
  chêne, hêtre, noyer, noisetier mentionne qui sème qui (déjà amorcé aux ③-⑥ :
  compléter, pas dupliquer).
- **Signes** (`sim/signes_corpus.py`) : entrées geai, écureuil, mulot (comme le merle
  l.~198/224 : silhouette + ce qu'il fait).
- **Pages secrètes** (optionnel) : le geai « planteur de chênes » (savoir forestier).

## Mesure
Outil existant `data/code/tools/diag_releve.py` (voie graine/ramet/rejet) : y ajouter
la voie par **origine** du grain (lue au log de levée) et la **distance à la mère**.
1. `verger_mur`, seed 42, 200 ans : taux de remplacement ≥ 1 pour pommier, cerisier,
   noyer ; fourré ≤ 10 ; part des recrues de cerisier nées à > 5 m de la mère [n=1
   run]. Le banc coupe l'herbivorie (`sans_herbivorie`) : vérifier que cela ne coupe
   pas la lecture des guildes `disperseur` (catégorie différente).
2. Banc neuf `bancs/nucleation.py` (pure composition, golden neutre) : prairie
   ouverte, un cerisier mûr au sud, un **perchoir** et un **mort debout** à 8 m, une
   ceinture `foret` (hêtre) au nord ; 50 ans. Attendu : semis de cerisier sous le
   perchoir et le mort debout, chênes/hêtres en terrain découvert côté nord.
   Test `tests/bancs/test_nucleation.py` court (≤ 10 ans, assertions qualitatives).
3. Calibrage borné : leviers `P_GRAIN_CHUTE`, `P_TRANSIT`, `P_OUBLI_*`, `TAUX_PRISE`,
   `APPETIT`, `PRED_MAX`, `GRAINS_SAUVAGES_MAX_PLOT`. Critère raté hors bornes →
   STOP et décision Nico (comme le fourré de figuiers de la relève ④).
4. Perf `full` 5 ans, tick médian an 3-5, avant (début de sprint) / après, ≤ +10 %
   cumulé ; charge VM (`uptime`) notée.
Runs longs en arrière-plan, en parallèle si la charge le permet. Chiffres avec leur
limite entre crochets.

## Ne PAS faire
- Pas de nouveau mécanisme moteur (seulement voix, outil, banc, calibrage).
- Golden : **inchangé depuis le ⑥** attendu (voix = lecture du log ; la ligne de
  glandée est un AJOUT au log → elle change le hash si une glandée survient au
  smoke : aucun chêne/hêtre/noisetier au smoke, donc non). Si le hash bouge, chercher.
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Tests
`test_evenements`, `test_carnet`, `test_encyclopedie`, `test_signes`,
`test_signes_legende`, `bancs.test_verger_mur`, `bancs.test_nucleation`.
