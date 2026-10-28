# Sprint FLUIDITÉ PC — PARTAGE (3ᵉ `/conception D116`) — carnet de conception

> Phase : **CONCEPTION FIGÉE le 2026-10-28** (OK Nico) → prêt pour `/sprint-auto`.
> Doc : `docs/perf/fluidite/conception_fluidite_pc_partage.md` (LIRE AVANT TOUT TRONÇON).
> NE JAMAIS lancer `test_epaisseur_500ans`. Golden jamais re-figé dans ce sprint.
> Entrée : run PC du 2026-10-27 → `sprints/perf/fluidite/sprint_fluidite_pc_leviers/00_etat.md`
> (fin du fichier). Golden `fecccded…` (à préserver), pont 0.6.0.
> Cible inchangée : PC Nico (i5-4200H, 2 cœurs / 4 threads), an 2, 1 s/sem demandée →
> **≤ 2 s/sem effectives en A**, aucune image > 100 ms.

## Point de départ (PC, 2026-10-27, s90 ×4) [n=1 run, PC]
- A (normal) **2,78 s/sem** : tick 1 819 ms, pont 726 ms, images 59,6 ms moy.
- B (rendu suspendu) 1,19 s/sem : tick 842 ms → le moteur seul tient la cible.
- C (moteur en pause) 30,9 ms/image, 32 FPS.
- Il faut −0,78 s en A. Le rendu multiplie le tick par ~2,2.
- Zoom ×4 ↔ ×32 : jusqu'à 453 ms (×8→×4), la plus grande part n'est attribuée à aucun poste.

## Mesure d'ouverture (VM, 2026-10-28, `full` graine 1521550718, s85-100, mode delta) [n=1 run, VM, charge 0,3→5]
- Par semaine : tick 881-1 686 ms · `_snapshot` 201-508 ms · `json.dumps` 54-123 ms.
- Ramasse-miettes Python : 25-47 ms par semaine, plus une collecte complète (génération 2)
  toutes les ~7 semaines (s86, s93, s100) qui monte à 151-224 ms. ~190-205 k objets suivis.
- `_snapshot` ≈ 20-30 % du temps Python d'une semaine : c'est le plus gros poste hors tick.

## Leviers recensés (chiffrés, NON tranchés)
1. **Ramasse-miettes** (`gc.freeze` après l'init, seuils relevés) — résultat identique au
   bit près. Gain ~3 % par semaine, supprime les pics de 150-220 ms [estimation VM].
2. **`_snapshot` mémoïsé par plante** (ne recalcule que les plantes changées, comme le delta
   du pont) — vise −40 % du `_snapshot` [hypothèse, non mesurée].
3. **Régulateur de cadence en Saison** : si la semaine est en retard, la vue plafonne ses FPS
   (plancher à trancher) pour rendre CPU **et** budget de puissance au moteur (iGPU Haswell :
   CPU et GPU partagent le TDP et le cache L3 → hypothèse forte pour le « rendu double le
   tick », NON mesurée). Rétabli plein FPS en Planification et quand la caméra bouge.
4. **Banc de partage** : balayage dans UN run PC (plafond FPS 0/20/15 × priorité moteur
   BelowNormal/Normal) → courbe cadence ↔ images.
5. **Enchaînement anticipé du step** (le moteur repart pendant que la vue lit la semaine) —
   gain ~200-300 ms en A [estimation], un geste cliqué attend au pire une semaine de plus.
6. **Hauts paliers** : instrumenter l'envoi au GPU (mémoire vidéo, textures créées par image)
   au changement de palier, puis levier si trouvé — tronçon vue.


## Décisions arrêtées (Nico, 2026-10-28)
- **Pas de carte graphique dédiée** (Intel HD 4600 seule) : pas de levier « autre GPU » ;
  on fait au mieux avec cette machine.
- **Plancher 15 FPS accepté** en Saison quand le moteur est en retard (levier 3).
- **Enchaînement anticipé (levier 5) REJETÉ pour ce sprint** : jusqu'à ~2 s de latence sur un
  geste, jugé trop long → inscrit en dette (note D116), seulement si 1-4 ne suffisent pas.

## Carte des tronçons (FIGÉE 2026-10-28)
| # | Kickoff | Contenu | Golden | État |
|---|---|---|---|---|
| ① | `01_moteur_gc_snapshot.md` | moteur bit-identique : `gc.freeze` + seuils, `_snapshot` mémoïsé par plante ; banc headless n=3 | intact | à faire |
| ② | `02_regulateur_banc_partage.md` | régulateur de cadence (15 FPS si semaine en retard, plein en Planification / caméra qui bouge) + banc de partage (4 sous-phases A : régulateur off/on × priorité BelowNormal/Normal) | intact | à faire |
| ③ | `03_hauts_paliers.md` | hauts paliers : mesurer l'envoi au GPU (mémoire vidéo, textures créées par image) au cran ×4↔×32, levier si trouvé | intact | à faire |
| ④ | `04_bilan_protocole.md` | bilan VM + protocole d'un run PC + clôture | intact | à faire |

## §REPRISE
Conception figée. Prochain : `/sprint-auto sprint_fluidite_pc_partage` → tronçon ①
(`01_moteur_gc_snapshot.md`). Chaque tronçon ajoute ici sa section §N (fait, mesures,
écarts) et met à jour la carte.
