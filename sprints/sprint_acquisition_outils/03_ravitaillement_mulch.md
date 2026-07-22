# Tronçon 03 — Ravitaillement en mulch (3 canaux)

> Tu démarres À FROID. Lis `CLAUDE.md`, `00_etat.md`, puis
> `docs/joueur/outils/conception_acquisition_outils.md` §C. Lève l'impasse
> `RAVITAILLEMENT_MANQUANT` de `tools/jardinier_auto/`.

## Objectif
`pailler` refuse quand `mulch_stock` est vide ET qu'aucun canal n'est amorçable tôt
(pas de squelette bois à `broyer`, pas de plante à paille cultivée à
`recolter_paille`) → l'automate consigne `RAVITAILLEMENT_MANQUANT`. On ajoute
**trois canaux** d'approvisionnement (gradient parallèle à l'acquisition d'espèce),
sans trahir le principe de `paillage.py` (« le mulch VIENT de quelque part »).

## Canal 1 — `glaner` (geste BASE, cycle INTERNE) — lève l'impasse à la racine
Ramasse la `litiere` de surface tendre d'un plot → crédite `mulch_stock` d'une
**nouvelle nature « feuilles »**.
- `fields/ecofields/constants.py:1050` (`NATURES_MULCH`) : ajoute l'entrée
  **`"feuilles"`** avec un profil d'effet cohérent avec les natures existantes
  (calque le plus proche — mulch tendre/rapide, distinct de `brf`/`aiguilles` plus
  ligneux). Renseigne les mêmes tables que les autres natures (rendement/effet).
- Façade `glaner` dans `sim/actions/paillage.py` (là où vit le stock) : réutilise
  le patron `_ramasser_vers_structure` (`sim/actions/compost.py:44`) mais crédite
  `mulch_stock(game_state)["feuilles"] += <matière ramassée>` au lieu d'une
  structure. Refus EN AMONT si rien à glaner (plot sans litière tendre → aucune
  Vigueur dépensée, patron `broyer`). Coût FAIBLE.
- `sim/actions/couts.py` : `COUTS["glaner"]=FAIBLE`, `OBJETS_TOUCHES["glaner"]=()`
  (geste brut sur le milieu, sans outil). `palette.py` : `"glaner":"plot"`.
- `sim/actions/__init__.py` : exporte `glaner`.
- `tools/simserver/actions.py` : dispatch `glaner` (cible plot, patron `becher`/
  `pailler`), message diégétique. **Bump protocole** + `version.py`.

## Canal 2 — graine de paille au départ (cycle INTERNE cultivé) — DONNÉES seules
`"ble"`/`"chanvre"` (`plants/catalogue.py:60`, `mulch_source` déjà posé) doivent
être accessibles tôt → cultiver → `recolter_paille` alimente le stock `paille`.
- `tools/simserver/commands.py:37` : ajoute `"ble"` et `"chanvre"` à
  `BANQUE_DEPART`. **ATTENTION** : `_banque_initiale` ne peuple `BANQUE_DEPART`
  qu'en config `full` (`commands.py:53`). Vérifie la config de démarrage réelle des
  bancs/jardinier_auto : si la config par défaut n'est pas `full`, verse plutôt
  blé/chanvre à l'offre magazine amorce (là où l'offre de départ est définie) pour
  qu'ils soient réellement accessibles tôt. Pas de code moteur neuf.

## Canal 3 — import Atelier (cycle EXTERNE, Vigueur) — réutilise l'infra du tronçon 02
Cadré comme import externe parallèle au magazine de graines (PAS « mulch abstrait »).
- `sim/outils.py` (créé au tronçon 02) : ajoute un registre **`MATERIAUX`**
  data-driven : `MATERIAUX = {"botte_paille": {"nature": "paille",
  "dose": <placeholder, ex. 3×PAILLAGE_DOSE>, "cout_vigueur": <placeholder>}}`.
  `acquerir_materiau(game_state, player, materiau) -> bool` : gate offre + `spend`
  Vigueur ; effet = `mulch_stock(gs)[nature] += dose` (importe `mulch_stock` de
  `sim.actions.paillage`). Bool, jamais d'exception.
- `tools/simserver/actions.py` : verbe **`acheter_materiau`** (patron
  `acheter_outil`). Bump protocole (peut partager le même bump que `glaner` si tu
  fais les deux dans le même incrément — une seule entrée `version.py` claire).

## Golden
**INCHANGÉ (NEUTRE).** Le smoke ne paille/glane jamais → nature `feuilles` jamais
lue au tick, stock jamais touché. `python3 -m tests.test_golden` : hash figé. Si
l'ajout de `feuilles` à `NATURES_MULCH` fait bouger le hash, c'est qu'un lecteur de
tick l'itère au repos → isole et rends l'ajout inerte hors paillage effectif.

## Vérif de l'impasse (le vrai critère de succès)
Fais tourner `tools/jardinier_auto/` sur un scénario où l'impasse
`RAVITAILLEMENT_MANQUANT` apparaissait : elle ne doit plus se produire (le canal
`glaner` fournit une réponse jouable au facteur `hydrique`/`sol_nu`). Consigne le
avant/après dans le rapport de fin de tronçon.

## Tests ciblés
- `glaner` sur un plot avec litière : `mulch_stock["feuilles"]` crédité, litière de
  surface réduite, Vigueur débitée. Plot sans litière → refus sans dépense.
- `acquerir_materiau("botte_paille")` : `mulch_stock["paille"] += dose`, Vigueur
  débitée ; refus si fonds insuffisants.
- `pailler` fonctionne après `glaner` (stock `feuilles` couvre `PAILLAGE_DOSE`).

## NE FAIS PAS
- Pas de « mulch qui apparaît de rien » : le canal 3 est un import Vigueur explicite.
- Ne lance JAMAIS `test_epaisseur_500ans` (long, inutile).
- Pas de re-figeage golden.

## Fin de tronçon
Mets à jour `00_etat.md` §REPRISE (03 fait, impasse levée, prochain = 04 vue) et
commit (`feat(moyens) ③ : ravitaillement mulch 3 canaux — lève RAVITAILLEMENT_MANQUANT`).
