## 2026-06-13 — Sprint planter/arroser · Session C : pont `sim_server.py` (protocole 0.3.3) — sprint CLOS

Dernier tronçon : les deux gestes traversent le pont JSON, la vue Godot pourra
les déclencher. **Aucune logique moteur touchée** → golden INCHANGÉ (toujours
`7ee907d3…`, le re-figeage de la Session B reste le dernier).

**Routing (`tools/sim_server.py`, `_do_action`)** : nouveau bloc `verb in
("planter", "arroser")`. Ces gestes visent le MILIEU par **position continue**
(`target.x_cm/y_cm`, locale tuile) — le serveur la **résout en plot-foyer** via
`_plot_at` (helper miroir de `PlantInstance.plot_foyer` : `(int(y//PLOT_CM),
int(x//PLOT_CM))`) car les façades écrivent au plot (banque-sol / champ
humidité). Un point hors tuile est un **refus de désignation** → ne coûte rien
(façade jamais appelée), comme un segment invalide pour `tailler`.
- `planter` : `params.species` (clé catalogue, validée contre `PLANT_CATALOGUE`),
  refus **« lot vide » EN AMONT** (message distinct de la Vigueur insuffisante,
  symétrie avec la façade) → `A.planter(...)`. Coût `FAIBLE`.
- `arroser` : `params.urgence` (bool) **ou** `params.phase == "saison"` →
  `× URGENCE_MULT`. Message lit l'humidité avant/après (effet visible en un
  aller-retour).

**Banque-joueur** : attachée à `game_state["player_seed_bank"]` dès `cmd_init`
(vide) — le tick de récolte (`engine.py`, gardé) la remplit au fil des automnes.
Exposée au snapshot : `player.seeds = {clé: nombre}` (lots non vides), la vue
propose les graines plantables. Pur compteur, la génétique reste moteur (D17/D22).

**Protocole** : `ENGINE_VERSION` 0.3.2 → **0.3.3** + ligne d'historique + cible
`point` documentée dans la docstring.

**Garanties :** `test_sim_server` **113/113** (section 12 neuve : refus planter
espèce inconnue/lot vide/hors tuile/tuile introuvable SANS coût ; `player.seeds`
vide à l'init puis remplie à la récolte ; dépôt réussi → lot −1 + coût FAIBLE ;
arroser monte le champ de DOSE, urgence ×1.5, cumul plafonné à 3.0 ; **2 runs
byte-identiques**). Toute la suite verte : golden `7ee907d3…`, `test_vigueur`
135/135, `test_croissance` 67/67, `test_planter` 18/18, `test_eau` 20/20.
`main.py` tourne propre.

**Sprint planter/arroser CLOS** (3 sessions). Le rendu Godot des gestes (choisir
une graine, viser, voir le sol s'humidifier, indices d'asphyxie) = volet vue
ultérieur — le pont est prêt. Suivant cadré : **compétition intra-plot** (Q4,
cohabitation/éclaircissage quand plusieurs plantes partagent un plot).
