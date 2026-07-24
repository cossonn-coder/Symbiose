# Tronçon ② — Conditions d'état (snapshot)

> Sprint QUÊTES (D79). Lire d'abord : `CLAUDE.md`, `00_etat.md`,
> `docs/joueur/automate/conception_quetes.md`, le tronçon ① (déjà fait).
> Golden : **INCHANGÉ**.

## Objectif
Ajouter la famille de conditions **d'état instantané**, lue sur le **snapshot du
monde vivant hors tick** (la vraie brique neuve de D79) :
- `hauteur_min(cible, metres)` — « un pommier ≥ 5 m » ;
- `floraison_min(cible, n)` — « ≥ n trèfles en floraison » ;
- `nombre_vivant_min(cible, n)` — « ≥ n plants vivants de l'espèce ».

## Contexte de vérité
- **F2** : ces conditions se lisent sur le SNAPSHOT (itération `game_state["tiles"]`
  → `tile.plants`), PAS via le ledger.
- Hauteur d'une plante : `plants/base/familles.py::height_at(inst)` (annuelles) /
  `plants/perennials.py::height_at(inst)` (pérennes). Utiliser l'accès existant,
  ne pas recalculer une hauteur.
- Floraison : marqueur de stade `🌸` / champ de stade de la plante — repérer le
  prédicat de floraison RÉEL utilisé ailleurs (grep `floraison`, `bloom`, stade)
  et le réutiliser, NE PAS en inventer un.
- Espèce d'une plante : `plant.plant_class` comparé à `classe_cible(cible)`
  (même résolution catalogue qu'au ①).

## À implémenter
1. Dans `sim/quetes.py`, ajouter les 3 types au **mini-catalogue déclaratif** :
   chaque type = fonction pure `(params, game_state) → (accomplie: bool,
   avancement_diegetique: str)`. L'aiguillage par tag (posé au ①) route vers le
   bon évaluateur.
2. Ces conditions **n'ont pas de hook** : elles sont **évaluées à la demande**
   (au passage de saison et/ou à la lecture du panneau) par un balayage borné du
   snapshot. Aucune évaluation dans le tick moteur → golden intact.
3. **Progression diégétique (V2)** : chaque évaluateur renvoie une phrase
   approximative (« à hauteur d'homme », « ça y est presque », « il en manque
   encore »), PAS un ratio chiffré (le chiffre exact = debug seulement, exposé
   à part au ⑤). Prévoir des seuils diégétiques simples (ex. <33 % / <66 % /
   <100 % / accompli).

## Tests
- Étendre `tests/test_quetes.py` : une plante fabriquée à hauteur ≥ seuil
  satisfait `hauteur_min` ; n trèfles fleuris satisfont `floraison_min` ; en
  deçà → non, avec la bonne phrase diégétique.
- `python3 -m tests.test_golden` → **hash INCHANGÉ** (évaluation hors tick,
  opt-in).

## Ne PAS faire
- Pas de déclenchement auto ni de table de quêtes (③). Pas de vue (⑤).
- Ne pas recalculer hauteur/floraison — réutiliser les prédicats existants
  (feedback « pas de recalcul dans un tick »).
- Ne pas créer d'espèce (kiwi = D26 ; démo sur pommier/tournesol/trèfle).

## Fin de tronçon
Golden inchangé → maj `00_etat.md` → commit.
