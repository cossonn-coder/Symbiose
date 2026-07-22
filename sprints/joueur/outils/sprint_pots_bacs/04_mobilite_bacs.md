# ④ Mobilité + bacs + pont snapshot

> Lire `00_etat.md` + conception §4, §6. Dépend de ③. Golden NEUTRE.

## Objectif
Gestes joueur pour poser/déplacer des conteneurs, bacs N×M immobiles, et exposer
les conteneurs au pont `sim_server` (snapshot + gestes) pour la future vue Godot.

## À faire

### A. Gestes (`sim/actions/`)
- **`poser_pot(monde, substrat, volume, x_cm, y_cm) -> Container`** et
  **`poser_bac(monde, substrat, volume, x_cm, y_cm, rows, cols) -> Container`**
  (phase planification) : créent un conteneur via `make_container`, l'ajoutent à
  la liste monde. Coût Vigueur `MODERE` (entrées dans `sim/actions/couts.py`
  `COUTS`, + `OBJETS_TOUCHES`). Bac : `mobile=False`, `kind="bac"`.
- **`deplacer_pot(container, x_cm, y_cm)`** : refuse si `not container.mobile`
  (un bac ne se déplace pas — refus EN AMONT, aucune Vigueur dépensée, modèle
  `epandre` jauge vide). Sinon met à jour `x_cm, y_cm` → lumière recalculée au
  prochain `tick_chimie` (`tile_origin`). Coût `MODERE`. **Pas de choc plante**
  (la plante et son mini-sol voyagent intacts).
- Concept maîtrise associé (ex. `"contenant"` / `"jardinage_hors_sol"`) sans état
  moteur → atténuation neutre 1.0, comme `"compostage"` (cf. décompo ⑤).

### B. Bacs N×M
- Vérifier que `make_container(kind="bac", rows=2, cols=2, …)` produit un mini-sol
  cohérent ; volume grand → confinement faible/nul (③ s'applique tel quel via
  `volume_norm`). La plante d'un bac peut exploiter plusieurs cellules (root_plots
  bornés à `rows×cols`, levier 2 de ③).
- `fond_ouvert` est porté ici (défaut bac=True, pot=False) mais son EFFET (pont
  vers la tuile) est implémenté en ⑤. En ④ il est juste stocké.

### C. Pont `tools/sim_server.py`
- Snapshot : exposer la liste des conteneurs
  `containers: [{id, kind, substrat, volume, x_cm, y_cm, fond_ouvert,
  plants:[…], eco_summary:{…}}]` (index = `target.container`).
- Routeur : `poser_pot` / `poser_bac` (params substrat/volume/pos/taille),
  `deplacer_pot` (target.container + pos), et **`planter` ciblant un conteneur**
  (target.container au lieu de target.tile). Valider les bornes/cohérence ICI
  (refus de désignation ne coûte rien). Incrémenter la version de protocole
  (0.5.3 → 0.5.4).
- **VUE C# = différée** (tronçon ⑥, Option B) : seul le snapshot/gestes Python.

## Définition de done
- `tests/test_mobilite.py` : poser pot/bac (Vigueur débitée, conteneur dans la
  liste), `deplacer_pot` change la position et la lumière reçue (pot à l'ombre
  maison reçoit moins), bac refuse le déplacement (0 Vigueur), `planter` dans un
  conteneur. Déterminisme.
- `tests/test_sim_server.py` étendu : snapshot conteneurs, gestes routés, index
  invalide/kind mismatch refusés, aller-retour poser→planter→déplacer.
- **Golden PROUVÉ NEUTRE** (smoke + population) — gestes event-driven hors tick,
  liste vide dans le smoke. Suites amont vertes.
- MAJ `00_etat.md` + commit.

## Pièges
- `deplacer_pot` sur un bac = refus propre (pas d'exception, pas de Vigueur).
- Le pont expose mais ne REND pas (Godot en pause) — ne pas toucher au C#.
- Garder le contrat snapshot stable/documenté pour ⑥.
