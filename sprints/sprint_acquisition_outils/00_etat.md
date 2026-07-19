# Sprint ACQUISITION DES MOYENS D'AGIR (sécateur + mulch) — état

> **CONCEPTION FIGÉE 2026-07-19.** Spec : `docs/conception/CONCEPTION_ACQUISITION_OUTILS.md`.
> Prêt pour `/sprint-auto`. Deux dettes levées : **D82** (chaîne taille morte,
> `couper` gated sur `posseder_secateur` que rien ne pose) + impasse
> `RAVITAILLEMENT_MANQUANT` de `tools/jardinier_auto/` (pailler sans mulch
> amorçable). Même classe de bug : geste bloqué faute d'un moyen non provisionné.

## Phase courante
**TRONÇONS 01+02+03 FAITS** (moteur). D82 LEVÉE + impasse `RAVITAILLEMENT_MANQUANT`
LEVÉE côté moteur. Reste 04 (vue Godot, F5 Nico).

## Avancement
- **01 — Gestes manuels `pincer` + `arracher` : FAIT** (2026-07-19).
  Façades `sim/actions/gestes.py` (`PINCER_INTENSITE=0.5 < COUPE_NETTE`) : `pincer`
  DOUX (auxine ↓, aucun retrait, coût FAIBLE) ; `arracher` NET (écime + litière
  `bois` MÊME calcul que `tailler` + `plant.erode(VITALITE_STEP)`, coût ELEVE, AUCUN
  gain). `couts.py` (`COUTS`/`OBJETS_TOUCHES`, famille `taille` SANS outil),
  `palette.py` (famille `plante`), `__init__.py` (export), dispatch serveur
  `tools/simserver/actions.py` (branche plante, désignation comme `tailler`), pont
  **0.5.31** (noté `version.py`). Tests : `tests/test_gestes_manuels.py` 22/22.
  **Golden INCHANGÉ** (`57c166d8…`). test_vigueur 136/136.
  ⚠️ DETTE TAILLE : `tools/simserver/actions.py` passe de 391 (vigilance) à **418
  LDC pur → > 400** avec les 2 branches de dispatch neuves. Router qui gonfle à
  chaque verbe → candidat `/refactor` (scinder la branche plante), HORS périmètre
  tronçon 01 (moteur pur, un fichier à la fois). À traiter en fin de sprint.
  NB : test_sim_server a 4 échecs PRÉ-EXISTANTS (assertions `engine_version==0.5.28`
  périmées + timing floraison) — indépendants de ce tronçon.
- **02 — Acquisition Atelier + registre `OUTILS` → déblocage sécateur : FAIT**
  (2026-07-19). **CŒUR D82 levé côté moteur.** Module NEUF `sim/outils.py` (30 LDC
  pur, jumeau de `sim/magazine.py`) : registre `OUTILS` data-driven
  (`secateur`→`{marqueur:"posseder_secateur", cout_vigueur:40.0 (placeholder F5),
  offre:True}`), `offre_outils` (Vigueur seule, aucune maîtrise → toujours
  `["secateur"]`), `acquerir_outil` (gate offre → idempotence → `vigueur.spend` →
  `marquer_action` + `evaluer_deblocages` ; bool, jamais d'exception). Verbe pont
  `acheter_outil` (`tools/simserver/actions.py`, patron `acheter_magazine` :
  `params.outil`, chemin Vigueur unique, `result.achete`), pont **0.5.32** (noté
  `version.py`). Tests : `tests/test_acquisition_outils.py` 15/15. **Golden
  INCHANGÉ** (`57c166d8…`).
  CHAÎNE RÉELLE (fait code, ≠ « cascade auto » du kickoff) : l'acquisition ouvre
  `couper` (`("action","posseder_secateur")`) ; `tailler` ne s'ouvre qu'après une
  coupe PRATIQUÉE (`("action","couper")` dans `GESTE_UNLOCK`) — le pont marque
  `couper` réussi. Test aligné sur ce fait. Kickoff/couper-tailler intacts.
  ⚠️ DETTE TAILLE : `tools/simserver/actions.py` passe de 418 à **431 LDC pur**
  (+13, le verbe `acheter_outil`) — toujours > 400. Router qui gonfle à chaque
  verbe → `/refactor tools/simserver/actions.py` en fin de sprint (HORS périmètre,
  un fichier à la fois). `sim/outils.py` = 30 LDC (🟢).
- **03 — Ravitaillement mulch (3 canaux) : FAIT** (2026-07-19). **Impasse
  `RAVITAILLEMENT_MANQUANT` LEVÉE À LA RACINE.**
  - Canal 1 `glaner` : nature NEUVE `"feuilles"` dans `NATURES_MULCH`
    (`fields/ecofields/constants.py`, tendre decay 1.0, `vers_bois=0`, `abri 0.5`) ;
    façade `sim/actions/paillage.py::glaner` (retire la litière de surface tendre
    `TISSUS_GLANABLES = STRUCTURE_ACCEPTE["bac"]` — bois RESTE — → `mulch_stock["feuilles"]`,
    coût FAIBLE, refus SANS dépense si sol propre). `couts.py`/`palette.py`/`__init__.py`
    câblés. Geste BASE sur le MILIEU (philo #1) — amorçable dès qu'il y a des feuilles
    au sol, aucun squelette ni culture requis.
  - Canal 2 : graines paille au départ — `BANQUE_DEPART` (`commands.py`) passe à
    `("tournesol","tomate","basilic","ble","chanvre")` (données seules).
  - Canal 3 : import Atelier — registre `MATERIAUX` (`sim/outils.py`, jumeau `OUTILS` :
    `botte_paille`→`{nature:"paille", dose:3×PAILLAGE_DOSE, cout_vigueur:20.0, offre:True}`),
    `offre_materiaux` + `acquerir_materiau` (gate offre → `vigueur.spend` →
    `mulch_stock[nature] += dose` ; CONSOMMABLE, non idempotent). Verbe pont
    `acheter_materiau` (`params.materiau`, chemin Vigueur unique).
  - jardinier_auto : `Perception.litiere_tendre` neuf (`perception.py`,
    `_litiere_tendre_at`, mêmes `TISSUS_GLANABLES`) ; `_prep_ravitaillement`
    (`proposition.py`) propose `glaner` en CANAL 1 (kind "milieu") avant broyer/
    recolter_paille ; `execution.py` branche `glaner`.
  - Pont **0.5.33** (`version.py`, changelog glaner+acheter_materiau+canal 2).
  - Tests : `tests/test_ravitaillement_mulch.py` NEUF 13/13, `test_automate_troncon2`
    10/10 (nouveau `test_glaner_leve_impasse`). **Golden INCHANGÉ** (`57c166d8…`).
  ⚠️ DETTE TAILLE : `tools/simserver/actions.py` passe de 431 à **462 LDC pur**
  (+31, verbes `acheter_materiau`+`glaner`) — toujours > 400. `/refactor` en fin de
  sprint (HORS périmètre). `sim/outils.py`=50, `paillage.py`=49 LDC (🟢).

## Décisions clés (détail dans le doc de conception)
- **Gradient de gestes** : `pincer` (DOUX, main, BASE) < `arracher` (NET déchiré,
  main, `erode()` vitalité, BASE) < `couper`/`tailler` (NET propre, sécateur, pas
  d'erode). L'outil débloque la coupe SANS blessure, pas « couper » (philo #1/#6).
- **`couper`/`tailler` déjà implémentés** → non touchés. Différenciateur main/outil
  = `arracher` appelle `erode`, l'outil non. Pas de champ « propreté » neuf.
- **`bouturer` non touché** (déjà en aval du sécateur dans la chaîne taille≥2).
- **Acquisition sécateur** : Atelier (hub-maison), Vigueur seule tôt, miroir
  `acheter_au_magazine` → pose `posseder_secateur`. Registre `OUTILS` data-driven.
- **Ravitaillement mulch = 3 canaux** : `glaner` (litière→stock nature « feuilles »,
  BASE, interne) + graine paille au départ (blé/chanvre, interne cultivé) + import
  Atelier (Vigueur, externe parallèle au magazine). Principe `paillage.py` préservé.
- **Golden INTACT sur les 4 tronçons** (opt-in joueur hors tick, smoke sans joueur).
  Zéro re-figeage. **Voix** : messages diégétiques + ledger, pas de 5-voix (aucune
  espèce neuve) ; carnet interprétatif « déchiré vs net » → dette D54.

## Carte des tronçons
- **01** — Gestes manuels `pincer` + `arracher` (moteur + tests). Golden inchangé. ✅
- **02** — Acquisition Atelier + registre `OUTILS` → déblocage sécateur (moteur).
  CŒUR D82. Golden inchangé. ✅ FAIT (pont 0.5.32).
- **03** — Ravitaillement mulch : `glaner` + graine paille + import Atelier (moteur).
  Lève `RAVITAILLEMENT_MANQUANT`. Golden inchangé (NEUTRE). ✅ FAIT (pont 0.5.33).
- **04** — Vue Godot : Atelier cliquable (outils + matériaux) + menu gestes + pont.
  F5 Nico. Tronçon vue obligatoire.

## Faits code de vérité (confirmés 2026-07-19)
- `sim/actions/deblocage.py:55` chaîne `couper→tailler→bouturer` ; `marquer_action`/
  `evaluer_deblocages`. `couper` dispatch `actions.py:176` (appelle `A.tailler`),
  `tailler` `gestes.py:260` (`atteindre_segment intensite=1.0` + litière bois).
- `plant.erode(step)` : `gestes.py:396` (`ecraser_plante`). Seam DOUX/NET seuil
  `COUPE_NETTE` (`sim/growth/seam.py`).
- `sim/magazine.py::acheter_au_magazine` (patron acquisition Vigueur, importé
  `tools/simserver/actions.py:21`). `BANQUE_DEPART` `commands.py:37`
  (`tournesol/tomate/basilic`, peuplée si config `full`).
- Mulch : stock `game_state["mulch_stock"]` (`sim/actions/paillage.py`), sources
  `broyer`/`recolter_paille`, `NATURES_MULCH` `fields/ecofields/constants.py:1050`,
  `PAILLAGE_DOSE=0.6`. `_ramasser_vers_structure` `compost.py:44`. Espèces mulch :
  `"ble"`/`"chanvre"`/`"seigle"` `catalogue.py:60`.
- Impasse : `tools/jardinier_auto/impasses.py` (`RAVITAILLEMENT_MANQUANT`),
  règles `regles.py` (`pailler` prio 12 hydrique / 8 sol_nu).
- Protocole pont courant : **0.5.30** (`tools/simserver/version.py`). Chaque
  tronçon moteur qui ajoute un verbe bump au numéro libre suivant + note version.py.

## §REPRISE
Tronçons **01+02+03 FAITS** (golden `57c166d8…` inchangé, pont **0.5.33**). **D82
levée** (`sim/outils.py` pose `posseder_secateur`) ET **impasse
`RAVITAILLEMENT_MANQUANT` levée à la racine** (canal 1 `glaner` = geste BASE sur le
milieu, amorçable dès qu'il y a de la litière tendre au sol). Les 3 canaux moteur
sont câblés + testés (13/13 `test_ravitaillement_mulch`, 10/10 `troncon2`).
**Prochain = 04** (VUE GODOT, F5 Nico) : Atelier cliquable (outils + matériaux) +
menu gestes (`pincer`/`arracher`/`glaner`) + branchement pont (`acheter_outil`/
`acheter_materiau`/`glaner`, protocole 0.5.33). Tronçon vue obligatoire, dernier du
sprint. Lire pour exécuter : `CLAUDE.md` + ce fichier + kickoff `04_*.md` +
`docs/conception/CONCEPTION_ACQUISITION_OUTILS.md` §D.
DETTE ouverte à traiter en fin de sprint : `/refactor tools/simserver/actions.py`
(**462 LDC > 400** depuis 01+02+03).
