# Sprint ACQUISITION DES MOYENS D'AGIR (sécateur + mulch) — état

> **CONCEPTION FIGÉE 2026-07-19.** Spec : `docs/conception/CONCEPTION_ACQUISITION_OUTILS.md`.
> Prêt pour `/sprint-auto`. Deux dettes levées : **D82** (chaîne taille morte,
> `couper` gated sur `posseder_secateur` que rien ne pose) + impasse
> `RAVITAILLEMENT_MANQUANT` de `tools/jardinier_auto/` (pailler sans mulch
> amorçable). Même classe de bug : geste bloqué faute d'un moyen non provisionné.

## Phase courante
**TRONÇON 01 FAIT** (moteur, gestes manuels `pincer`+`arracher`). Reste 02→04.

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
- **01** — Gestes manuels `pincer` + `arracher` (moteur + tests). Golden inchangé.
- **02** — Acquisition Atelier + registre `OUTILS` → déblocage sécateur (moteur).
  CŒUR D82. Golden inchangé.
- **03** — Ravitaillement mulch : `glaner` + graine paille + import Atelier (moteur).
  Lève `RAVITAILLEMENT_MANQUANT`. Golden inchangé (NEUTRE).
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
Tronçon **01 FAIT** (golden `57c166d8…` inchangé, pont 0.5.31). **Prochain = 02**
(acquisition Atelier + registre `OUTILS` → déblocage sécateur, CŒUR D82).
Lire pour exécuter : `CLAUDE.md` + ce fichier + le kickoff `02_*.md` +
`docs/conception/CONCEPTION_ACQUISITION_OUTILS.md` §B. Chaque tronçon met à jour cette
section (fait/à faire) en fin de course.
DETTE ouverte à traiter en fin de sprint : `/refactor tools/simserver/actions.py`
(418 LDC > 400 depuis 01).
