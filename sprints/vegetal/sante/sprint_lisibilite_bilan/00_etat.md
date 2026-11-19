# Sprint LISIBILITÉ DU BILAN (retours F5 de plante_vivante + D141) — état

> Phase : **CLOS CÔTÉ CODE** le 2026-11-19 (①②③, F5 attendu) — conception figée le 2026-11-19 → `docs/vegetal/sante/conception_lisibilite_bilan.md`. Ouvert le 2026-11-19 sur retours F5
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
| ① | `01_hauteur_acquise.md` — hauteur acquise (moteur) | RE-FIGÉ `8f2dd7ad…` → `e24a23d8…` | FAIT |
| ② | Noms français : table Python unique → pont → étiquette, info-bulle, rapport F4, chronique (ferme D141) — `02_noms_francais.md` | intact `e24a23d8…` | FAIT |
| ③ | Vue + banc : litière herbacée visible (tiges paille → humus), consoudes broutées à 0,2 + réserves basses, info-bulles vérifiées par capture VM — `03_vue_banc.md` | intact `e24a23d8…` | FAIT (non commité) |

## ① Hauteur acquise — fait (2026-11-19)
- `PlantInstance.hauteur_acquise` (cm) + `retenir_hauteur(repli)` (`plants/base/instance.py`) ;
  `height_at` non procédural = `max(potentiel × gf × génétique, hauteur_acquise)`
  (`plants/base/familles.py`, `plants/perennials/base.py`). Getter pur.
- Tenue 1×/tick dans `_update_physiology` (`sim/engine/croissance.py`) **AVANT** la mise à
  jour du `growth_factor` (et non après comme le kickoff le suggérait : sinon le 1ᵉʳ tick
  perdait déjà 2 cm, 60 → 58) ; idem pots (`world/container.py`, sans repli).
- Retombe : `regress()` (stade perdu) ; repli = hiver + vivace dormante non ligneuse.
- Constats au code : taille/écrasement d'une espèce SANS structure ne changent PAS la
  hauteur moteur (la coupe = hint de vue `rabattu`) — inchangé. Aucun repli aérien
  n'existait : le repli ne fait retomber la hauteur qu'au calcul du stade (consoude 50 →
  42 cm), pas à une rosette — un vrai repli à ras = mécanique neuve, non faite.
- Procédurales : 0 baisse de hauteur en 104 sem de smoke [seed 42, n=1] → non touchées.
- Golden re-figé `e24a23d8cb09…` ; neutralisé (`retenir_hauteur` no-op) → `8f2dd7add938…`
  exact. Dérive : tiges qui restent hautes → plus de lumière/moins d'herbivorie basse →
  moins de morts de faim (65 → 50 lignes) et plus de vivantes en an 2 (s104 : 42 → 57)
  [smoke seed 42, n=1].
- Banc OMBRE : poivrons à 60 cm constants jusqu'à la mort (avant 60 → 47).
- Test neuf `tests/test_hauteur_acquise.py` (ombre, dormance consoude, taille tomate,
  régression basilic) vert.

## ② Noms français — fait (2026-11-19)
- Pas de clé neuve : le pont envoyait déjà `name` = `PlantInstance.name` = `cls.name`
  (français) par plante (sol + conteneur) → `name` = nom AFFICHÉ ; `species` reste
  l'identifiant (commentaires posés dans `serialize.py`). Les 52 espèces ont un nom
  français (seul « Dactyle » coïncide avec sa classe, légitime).
- Python : `perf.py` / `perf_annees.py` comptent par `cls.name` (`par_espece`, `top`) ;
  `chronique.py` : texte en noms affichés (`_nom`), `brut` garde les clés catalogue.
  Pont **0.6.22** (aucune clé neuve, valeurs de nom changées), 4 tests de version suivis.
- Inventaire `__name__` restants = IDENTIFIANTS, non touchés : `maitrise_pont`/`vision_cmds`
  (classe → clé catalogue), `REPRO_BY_SEASON`, `graines_espece` (teinte), `server.py`
  (type d'exception).
- C# : `PlanteLue.Tag` = `Name · stade` (repli `Species`) ; `DossierPlantePanel` n'affiche
  plus la classe en italique ; méta neuve `nom` (`WorldView.Snapshot.cs`) lue par l'encart
  Planche et le survol gènes G. Restent en classe : logs `GD.Print` de bancs et le titre
  debug de l'aide du carnet (`_filtreEspece`, clé du carnet — non vérifié).
- Preuves : snapshot pont (init + 60 sem + snapshot, seed 42) byte-identique avant/après ;
  seul `perf_report` change (noms + choix volatil des pires ticks). Section 25
  `tests/simserver/noms.py` (catalogue, `name`, F4, chronique) ; `test_sim_server`
  354/354, `test_chronique` vert ; `dotnet build` vert. Pas de capture VM faite.

## ③ Vue + banc — fait (2026-11-19)
- **A. Tiges paille** : pont **0.6.23**, chaque entrée `litiere` gagne `herbace_masse,
  herbace_age_sem` (index 9-10 ; masse et âge PROPRES de la parcelle `herbace`, même sous
  un autre tissu dominant — l'âge moyen du plot mélange bois et feuilles). Calque neuf
  `visuals/StrawLitterLayer.cs` (125 LDC) : grain sous ×4, tiges couchées dès ×4, paille →
  humus en 12 sem, semis hashé en un lot ; câblé dans `WorldView.Compost.cs` (après
  `LeafLitter`) + liste des couches au sol (`WorldView.Couches.cs`). `LitterLayer` garde
  ses amas. Tissu retenu : `herbace` seul (`fleur` = pétales, rendu `PetalLayer`/amas).
  Snapshot `full` 40 sem seed 42 identique avant/après hors les 2 champs (+ perf volatile).
- `composter` ramasse bien la litière `herbace` d'un poivron mort (section 26
  `tests/simserver/tiges.py`, avec `poser_bac` sur la tuile OMBRE : il FAUT un bac).
- **B. Consoudes** : le 0,35 venait du **warmup d'une semaine** (refeuillaison 0,15/sem) →
  `BANC_WARMUP["plante_vivante"] = 0` (la vue ouvre en s12 à 0,2). **Écart au kickoff** :
  « réserves basses » pour les DEUX broutées tuerait la phrase « refait » (forces < 0,6 →
  « épuisé » prioritaire) et la repousse ne s'étale pas sans mort : sous ~0,45 de feuillage
  le bilan est négatif, à 0,08 de réserves la consoude meurt de faim, à 0,12 elle repousse
  à pleine vitesse [seed 42, n=1]. Décision : 3 consoudes = témoin / broutée riche
  (« refait », 6 sem) / broutée **à bout** (réserves 0,10 : 7 sem de repousse, ternie
  11 sem, « à bout de forces »). Cible ≥ 10 sem tenue par la teinte, pas par la densité.
  Densité à ×4 lisible en port rosette (capture 01) → port inchangé.
- **Poivrons (seed 42)** : morts en s17-s19 (hauteur acquise ne les sauve pas à ce seed ;
  au seed serveur par défaut ils tiennent jusqu'en s33 — le banc F5 est en 42).
  Oracle `tests/test_banc_plante_vivante.py` mis à jour (il exigeait `warmup == 1` →
  0 ; + retard de la broutée à bout en s16 : 0,62 contre 0,76).
- **C. Captures VM** (`captures/`) : 01 s12 « feuillage clairsemé » ; 02 s14 « refait ses
  feuilles » ; 03 s14 « à bout de forces » (consoude à bout) ; 04 s17 « à bout de forces »
  (poivron, `-H`) ; 05 s21 tas de tiges paille au pied du mur. Survol par `-s` (souris
  posée), pas de code de triche. Mesure : `mesures/consoudes.py`.
- Tests : golden `e24a23d8…` intact ; `test_sim_server` (+ section 26) ; oracle banc vert ;
  `dotnet build` vert.

## F5 pour Nico (banc `plante_vivante`)
1. REFEUILLE (sud) : d'ouest en est témoin dense / broutée qui « refait ses feuilles » /
   broutée à bout, terne, plus lente (« à bout de forces »), différence visible ~11 sem.
2. OMBRE (touche H) : poivrons « à bout de forces » vers s17, morts s17-s19, puis tas de
   tiges paille au pied du mur nord qui brunissent vers l'humus.
3. Poser un bac sur la tuile OMBRE puis `composter` sur un tas : les tiges disparaissent.
4. Étiquettes « Consoude · adulte » / « Poivron · adulte » (D141) ; F4 en noms français.

## REPRISE
Sprint CLOS côté code (①②③). Reste : commit de ③, journal, F5 de Nico (recette ci-dessus),
puis fermer D141 dans `DETTE.md` si l'étiquette/F4 sont validés. Suite :
`/sprint-auto sprint_stress_au_bilan`.
