# Tronçon ⑦ — Couplage planter + pailler par MAÎTRISE (auto-paillage)

**Prérequis** : `CLAUDE.md`, `00_etat.md`, `CONCEPTION_EQUILIBRE_INVASION.md` §6.
Patrons : `sim/actions/gestes.py::planter`, `sim/maitrise.py` /
`sim/maitrise_detection.py` (paliers découverte→…→transcendant, par famille/
concept), le stock de mulch (④), `pailler` (③).

## Objectif
« On paille systématiquement quand on plante, une fois qu'on maîtrise. »
Au-dessus d'un **palier de maîtrise** (de la plante/famille concernée), `planter`
**auto-paille** le plot ; la **nature du mulch dépend de la plante ET de la
maîtrise** (arbre → BRF ; potagère → paille ; palier plus haut → mulch mieux
adapté/plus efficace).

## Fichiers à toucher
- `sim/actions/gestes.py::planter` — après le dépôt du grain, SI le palier de
  maîtrise de la famille de l'espèce ≥ `SEUIL_AUTOPAILLAGE` ET stock dispo :
  appeler `pailler` sur le plot avec la **nature choisie** (mapping
  espèce/famille → nature, modulé par le palier). Sinon plante sans mulch (pas de
  friction si pas de stock / pas de maîtrise).
- Mapping `espece/famille → nature de mulch` (dict data-driven, à côté de
  `NATURES_MULCH`). Palier ↑ → depth/efficacité ↑ (nature « idéale » débloquée).
- Vérifier le coût : l'auto-paillage consomme Vigueur + stock comme un `pailler`
  normal (pas gratuit) — ou un tarif réduit « geste combiné » (à trancher dans le
  kickoff par le sous-agent, documenter le choix).

## Golden
**INTACT**. Le smoke n'a pas la maîtrise requise (paliers de départ bas) → aucune
auto-paillage → `planter` inchangé. Vérifier `test_golden`/`test_population`.
Vérifier aussi `tests/test_vigueur` / tests de `planter` existants.

## NE PAS
- Pas d'effet direct sur la plante (le mulch amende le CHAMP, #2). Pas de RNG.
- Ne pas auto-pailler si aucun stock (pas de mulch « magique » — respecter ④).

## Vérif / F5
Test : planter à basse maîtrise = pas de mulch ; à maîtrise ≥ seuil = plot paillé
de la bonne nature. F5 (⑧) : planter une tomate maîtrisée → paille apparaît.
