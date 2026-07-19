# 2026-07-19 — Sprint ACQUISITION DES MOYENS D'AGIR (sécateur + mulch) — CLOS

Sprint figé par `/conception` (spec `docs/conception/CONCEPTION_ACQUISITION_OUTILS.md`),
exécuté en 4 tronçons via `/sprint-auto`. Lève deux dettes de la **même classe** —
un geste bloqué faute d'un moyen jamais provisionné : **D82** (chaîne de taille
morte, `couper` gated sur `posseder_secateur` que rien ne posait) + l'impasse
`RAVITAILLEMENT_MANQUANT` du jardinier automate (pailler sans mulch amorçable).
**Golden `57c166d8…` INTACT sur les 4 tronçons + le refactor — zéro re-figeage**
(tout est opt-in joueur, hors du tick golden qui tourne sans joueur).

## ① Gestes manuels `pincer` + `arracher` — FAIT (`8733f6a`)

Bas du **gradient de gestes** (main nue avant l'outil). Façades `sim/actions/gestes.py` :
`pincer` DOUX (`PINCER_INTENSITE=0.5 < COUPE_NETTE`, auxine ↓, aucun retrait, coût
FAIBLE, débourrement émergent) ; `arracher` NET à la main (écime + litière `bois`
MÊME calcul que `tailler`, PLUS `plant.erode(VITALITE_STEP)` — le différenciateur
main/outil est la BLESSURE, pas la coupe : l'outil débloque la coupe SANS érosion,
philo #1/#6). `couts.py`, `palette.py`, `__init__.py`, dispatch serveur câblés, pont
**0.5.31**. Tests `test_gestes_manuels` 22/22. Golden inchangé.

## ② Acquisition Atelier + registre `OUTILS` — FAIT (`23a46ce`)

**Cœur D82.** Module NEUF `sim/outils.py` (jumeau de `sim/magazine.py`) : registre
data-driven `OUTILS` (`secateur`→`{marqueur:"posseder_secateur", cout_vigueur:40.0
placeholder F5, offre:True}`), `offre_outils` (Vigueur seule, aucune maîtrise → tôt
dans la partie), `acquerir_outil` (gate offre → idempotence → `vigueur.spend` →
`marquer_action`+`evaluer_deblocages`, bool jamais d'exception). Verbe pont
`acheter_outil` (patron `acheter_magazine`), pont **0.5.32**. La chaîne réelle :
l'acquisition ouvre `couper` (`posseder_secateur`), `tailler` ne s'ouvre qu'après
une coupe PRATIQUÉE. Tests `test_acquisition_outils` 15/15. Golden inchangé.

## ③ Ravitaillement mulch (3 canaux) — FAIT (`0b8fee5`)

Impasse `RAVITAILLEMENT_MANQUANT` levée **à la racine**.
- **Canal 1 `glaner`** (geste BASE sur le MILIEU, philo #1) : nature NEUVE `feuilles`
  dans `NATURES_MULCH`, façade `sim/actions/paillage.py::glaner` (retire la litière
  de surface tendre — le bois RESTE — → `mulch_stock["feuilles"]`, refus sans dépense
  si sol propre). Amorçable dès qu'il y a des feuilles au sol, sans outil ni culture.
- **Canal 2** : graines paille au départ — `BANQUE_DEPART` inclut `ble`/`chanvre`.
- **Canal 3** : import Atelier — registre `MATERIAUX` (`sim/outils.py`, jumeau
  `OUTILS`, `botte_paille`→`3×PAILLAGE_DOSE`, CONSOMMABLE non idempotent), verbe pont
  `acheter_materiau`. Jardinier automate câblé (`Perception.litiere_tendre`,
  `_prep_ravitaillement` propose `glaner` en canal 1). Pont **0.5.33**. Tests
  `test_ravitaillement_mulch` 13/13, `test_automate_troncon2` 10/10. Golden inchangé.

## ④ Vue Godot : Atelier + menu gestes — FAIT (`2e62c93`)

Rend jouables les moyens d'agir des tronçons 01-03. **Commande pont READ-ONLY
`atelier`** (0.5.34) → `{outils:[{cle,cout_vigueur,possede}], materiaux:[…]}`, miroir
lecture-seule des verbes d'achat (possession dérivée d'`est_debloque(couper)`, aucun
état neuf). Vitrine C# `AtelierPanel.cs` (jumeau du Magazine, ouverte au clic maison
via `WorldView.Hub.cs`) ; menu gestes `pincer`/`arracher`/`glaner`
(`GesteIcon.cs`+`WorldView.Actions.cs`) ; `SimBridge.cs` relaie les 5 verbes déjà en
place. **Fix moteur no-op** (`sim/actions/deblocage.py`) : les 3 gestes manuels/glanage
ajoutés à `GESTES_BASE` — ils en étaient absents, ce qui les GRISAIT à jamais dans la
palette Godot ; set jamais matérialisé hors joueur → golden intact confirme le no-op.
`dotnet build` VERT, golden inchangé.

## Refactor auto-léger — `actions.py` 462 → 292 LDC (`b388ed5`)

Les 3 verbes ajoutés en 01-03 avaient poussé `tools/simserver/actions.py` à **462 LDC
pur** (🔴 > 400). Découpage PUR sur le patron existant (`conteneurs_route`/
`multiplication_route`) : deux gros blocs de dispatch de `_do_action` extraits en
modules route — `plante_route.py` (`manger`/`recolter`/`deraciner`/`couper`/`pincer`/
`arracher`/`tailler`, 96 LDC) + `structures_route.py` (`poser_bac`…`recolter_miel`,
93 LDC). `actions.py` retombe à **292 LDC** (🟢), tous < 300. **Attention notée** :
le golden n'exerce PAS `cmd_action` (opt-in joueur) → invariance PROUVÉE par les
suites ciblées (gestes 22/22, acquisition 15/15, ravitaillement 13/13, troncon2 10/10)
+ `test_sim_server` aux **mêmes 4 échecs pré-existants** (assertions `engine_version`
périmées ×3 + timing floraison), aucun sur le routage refactoré. Golden inchangé.

## État final

D82 ✅ LEVÉE + impasse `RAVITAILLEMENT_MANQUANT` ✅ LEVÉE. Golden final `57c166d8…`
(0 re-figeage), pont **0.5.34**, `dotnet build` vert. **Reste F5 Nico** : ouvrir
l'Atelier → acquérir le sécateur (Vigueur débitée) → `couper`/`tailler` apparaissent
sur une plante ; `pincer`/`arracher` disponibles d'emblée ; `glaner` sur litière
crédite du mulch puis `pailler` marche ; botte de paille achetée → `pailler` sans rien
avoir cultivé. Voix : messages diégétiques + ledger (pas de 5-voix, aucune espèce
neuve) ; carnet interprétatif « déchiré vs net » → dette D54. Constante placeholder
`cout_vigueur=40.0` du sécateur à calibrer au F5.
