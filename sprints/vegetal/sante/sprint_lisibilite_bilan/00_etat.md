# Sprint LISIBILITÉ DU BILAN (retours F5 de plante_vivante + D141) — état

> Phase : **CONCEPTION FIGÉE** le 2026-11-19 → `docs/vegetal/sante/conception_lisibilite_bilan.md`. Ouvert le 2026-11-19 sur retours F5
> de Nico après `sprint_plante_vivante` (A). Placé AVANT `sprint_stress_au_bilan` (B),
> choix Nico.

## Retours F5 (Nico, 2026-11-19) et mesures VM (banc `plante_vivante`, seed 42, n=1)
1. **Consoudes identiques à l'œil** — mesuré : broutées partent à 0,35 (pas 0,2),
   reviennent à 0,97 en 5 sem (= 15 s à 3 s/sem) ; 1 segment chacune (port rosette).
2. **Poivrons morts sans matière organique visible** — mesuré : le moteur dépose bien
   la litière (+~1,3 par plot, décroît à 0,75 en 7 sem). Litière `herbace` → `LitterLayer`
   (amas abstraits), pas `LeafLitterLayer` (réservé au tissu `feuille`). Plante retirée
   1 sem après la mort (pas de squelette herbacé).
3. **Info-bulles du bilan non vues** — Nico n'a pas survolé au bon moment. Fenêtres
   courtes : « épuisé » (vitalité < 0,6) ~2 sem chez le poivron ; « refait » ~4 sem.
4. **Noms anglais** (D141) — étiquette `PlanteLue.Tag = Species · stade` (Species =
   `cls.__name__`, `serialize.py:154/643`) ; rapport perf `WorldView.PerfReport.cs:131`.
   Clés françaises sans accents existent déjà (`PLANT_CATALOGUE`, `plants/catalogue.py:20`).
5. Vu en passant : le poivron **rapetisse** en mourant (58 → 47 cm) — `current_height`
   = potentiel × `growth_factor`.

## Décisions arrêtées (Nico, 2026-11-19)
- Q1 **français seul**, pas de réglage Options. Source = `cls.name` (déjà français et
  accentué sur le catalogue) : pas de table neuve ; `species` (classe) reste l'identifiant.
- Q2 **litière visible ET utilisable** : la litière d'herbacée se voit et se ramasse
  par les gestes existants. Vérifié au code : `composter` ramasse déjà toute la litière
  tendre du plot (`sim/actions/compost.py:113`, refuse seulement `bois`/`diffus`) ;
  à confirmer en jeu (geste lisible sur le plot du poivron mort).
- Q3 **le rapetissement se corrige ICI** (moteur, golden re-figé annoncé). Cause vue :
  `height_at` = potentiel × `growth_factor`, et `growth_factor` suit une cible qui
  baisse au déficit (`sim/engine/croissance.py:529`). Intention : la hauteur bâtie est
  ACQUISE ; le stress ralentit la croissance, ne retire pas de taille ; seule une
  destruction (taille, casse, broutage d'apex) en retire.

## Tronçons
| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_hauteur_acquise.md` — hauteur acquise (moteur) | RE-FIGÉ annoncé (départ `8f2dd7ad…`) | à faire |
| ② | Noms français : table Python unique → pont → étiquette, info-bulle, rapport F4, chronique (ferme D141) — `02_noms_francais.md` | intact | à faire |
| ③ | Vue + banc : litière herbacée visible (tiges paille → humus), consoudes broutées à 0,2 + réserves basses, info-bulles vérifiées par capture VM — `03_vue_banc.md` | intact | à faire |

## REPRISE
Lire `CLAUDE.md`, ce fichier, la conception, puis le kickoff du premier tronçon « à faire ».
Lancer : `/sprint-auto sprint_lisibilite_bilan`. Ensuite : `/sprint-auto sprint_stress_au_bilan`.
