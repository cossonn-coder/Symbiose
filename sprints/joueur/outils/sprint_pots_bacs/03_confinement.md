# ③ Plante en pot + confinement racinaire (effet nain)

> Lire `00_etat.md` + conception §3. Dépend de ②. Le tronçon le plus délicat :
> l'effet nain HYBRIDE (philo #2 — jamais de malus direct). Golden NEUTRE (aucun
> pot dans le smoke).

## Objectif
Une plante peut vivre DANS un conteneur : elle puise dans le mini-sol, grandit,
et reste **naine** si le volume est petit, via trois leviers cumulés.

## À faire

### A. Plante dans le conteneur
- `make_container` / un helper `planter_dans(container, plant_class)` ajoute une
  `PlantInstance` à `container.plants`, positionnée au centre de la cellule
  (`x_cm, y_cm` du conteneur — la position continue existe déjà, cf.
  `PlantInstance.x_cm/y_cm`).
- `Container.tick_chimie` → enrichi en `Container.tick(...)` qui, après la chimie,
  fait l'**uptake + croissance** des plantes du conteneur, en réutilisant le code
  de la boucle tuile (uptake `eco.plant_uptake`, morphogénèse `sim/growth.py`),
  mais **borné à la géométrie du mini-sol**.

### B. Levier 1 — réservoir réduit (émergent)
- `VOLUME_REF = 75` (L) ; `volume_norm = volume_litres / VOLUME_REF`.
- `eco.plant_uptake(...)` gagne un `volume_factor: float = 1.0` (défaut →
  **tuiles bit-identiques**). Le conteneur passe `volume_factor = 1/volume_norm`
  (clampé, ex. `min(VOLUME_CONF_MAX, …)`) : un petit pot voit ses retraits
  d'uptake amplifiés relativement au stock → concentration chute vite →
  sécheresse/carence via les mécanismes EXISTANTS. NE PAS toucher la plante
  directement.

### C. Levier 2 — plafond racinaire (émergent)
- L'uptake du conteneur n'itère QUE sur les cellules du mini-sol (1 pour un pot)
  → `root_plots` naturellement bornés. Vérifier que `root_plots` (qui dérive d'un
  rayon continu, `plants/base/instance.py:256`) est bien **intersecté** avec les
  cellules valides du conteneur (sinon le rayon « déborde » dans le vide). Si la
  plante en pot étend son rayon au-delà du pot, clamper l'ensemble de cellules
  exploitées à `eco.rows × eco.cols`.

### D. Levier 3 — signal root-bound léger (explicite, garantit le bonsaï)
- `occupation = plant.biomass / volume_litres` (proxy de saturation racinaire ;
  `biomass` existe sur `PlantInstance`).
- Au-delà de `ROOTBOUND_SEUIL` (knob, ex. 0.3), facteur
  `confinement = clamp(CONF_MIN, 1.0, 1 - k*(occupation - SEUIL))` qui **multiplie
  le gain de croissance segmentaire** dans `sim/growth.py`. Passer ce facteur via
  le contexte de croissance (paramètre optionnel défaut 1.0 → tuiles intactes).
- Knobs de départ : `ROOTBOUND_SEUIL`, `CONF_MIN` (ex. 0.25), `k` — calibrage
  post-test, à exposer en constantes lisibles.

## Définition de done
- `tests/test_confinement.py` : à substrat/lumière/eau ÉGAUX, une même espèce
  croît MOINS en petit pot (5 L) qu'en grand (75 L) qu'en pleine terre — gradient
  monotone (effet nain). Le petit pot s'assèche/se carence plus vite (levier 1).
  root_plots jamais hors du mini-sol (levier 2). Root-bound s'active au-delà du
  seuil et bride la croissance (levier 3) ; `volume_factor=1.0` ⇒ uptake
  bit-identique à l'actuel (test de non-régression). Déterminisme h1==h2.
- **Golden PROUVÉ NEUTRE** (smoke + population). `volume_factor` défaut 1.0 et le
  facteur croissance défaut 1.0 garantissent l'invariance. Suites amont vertes
  (croissance, vigueur, eau, golden, population, sim_server).
- MAJ `00_etat.md` + commit.

## Pièges
- Philo #2 : aucun des 3 leviers ne pose un malus direct « parce que c'est un pot ».
  Levier 1/2 = flux/géométrie ; levier 3 = signal de saturation → croissance, pas
  un retrait de santé. Le bonsaï doit ÉMERGER, pas être imposé.
- Bien défaut-er tous les nouveaux paramètres (1.0) pour l'invariance golden.
- Le proxy `biomass` pour l'occupation est volontairement grossier (calibrage).
