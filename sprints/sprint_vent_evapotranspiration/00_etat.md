# Sprint VENT & ÉVAPOTRANSPIRATION (D37) — état partagé

> **État léger** (mis à jour en fin de chaque tronçon). Le **design figé** vit dans
> [`docs/conception/CONCEPTION_VENT_EVAPOTRANSPIRATION.md`](../../docs/conception/CONCEPTION_VENT_EVAPOTRANSPIRATION.md)
> — chaque kickoff `tN_*.md` y renvoie pour le détail. Repars à froid : lis ce
> fichier + le `tN_*.md` du tronçon courant + la/les §§ de conception citées.

## En une phrase
Introduire le **vent** comme facteur micro-climatique complet et **enrichir
l'évaporation** (rayonnement + vent) pour rééquilibrer la rosée → résout **D37**
(vent continu) et **D39** (`test_senescence` rouge : pommier asphyxié à 19,5 ans).
**Contrainte #1 = perf** (Nico : « peur que le moteur soit trop lent »).

## Décisions figées (Nico, 2026-06-29)
- Périmètre = **D37 complet** + tous les effets (thigmo, dégât étiolées, semis
  intérieur/extérieur, régimes nul/risées/venturi, vent↔nébulosité, pollinisation/
  dispersion, maladies fongiques, wind chill, transport litière/neige).
- Découpage **perf-first 8 tronçons** (⓪→⑦, §8 conception). ⓪→② débloquent D39 à
  coût ~nul ; ③ (abri spatial) = seul morceau cher, isolé/caché/mutualisé/reportable.
- **D32 intégré au tronçon ⓪** : optim scatter de la boucle lumière-sol, **mesurée
  ×6 plancher, golden-safe** (`tools/diag_light_coverage.py`). Verrou = test
  d'équivalence bit-à-bit.
- **Re-figeage golden LARGE assumé** dès ② (nébulosité dynamique + évaporation).
- « Arbres en drapeau » = hors périmètre (dette).

## Carte des tronçons
| # | Fichier | Coût | Golden | Statut |
|---|---------|------|--------|--------|
| ⓪ | [`t0_reference_perf_scatter.md`](t0_reference_perf_scatter.md) | mesure+gain | **INTACT** | ⏳ à faire |
| ① | [`t1_vent_masse_air.md`](t1_vent_masse_air.md) | O(1) | neutre | ⏳ |
| ② | [`t2_evapotranspiration.md`](t2_evapotranspiration.md) | marginal | **re-fige LARGE** → D39 vert | ⏳ |
| ③ | [`t3_abri_spatial.md`](t3_abri_spatial.md) | **À BUDGÉTER** | re-fige | ⏳ |
| ④ | [`t4_thigmomorphogenese.md`](t4_thigmomorphogenese.md) | négligeable | re-fige | ⏳ |
| ⑤ | [`t5_pollinisation_dispersion.md`](t5_pollinisation_dispersion.md) | négligeable | re-fige | ⏳ |
| ⑥ | [`t6_maladies_fongiques.md`](t6_maladies_fongiques.md) | négligeable | re-fige | ⏳ |
| ⑦ | [`t7_transport_voix.md`](t7_transport_voix.md) | amorti | re-fige | ⏳ |

## Boucle de travail (rappel CLAUDE.md)
Lancer `tN` → coder → **mesurer ms/tick avant/après** (budget §7B) → golden (intact
ou re-figeage annoncé) → MAJ ce fichier → commit → `/clear` → lancer `tN+1`.

## Clôture du sprint
- Rouvrir/MAJ **D39** dans `DETTE.md` (récidive via rosée, re-résolu par le fond).
- Solder **D37** + **D32** (scatter). MAJ `journal.md` (index) + entrée `journal/NN_…`.
- Supprimer `HANDOFF.md` (devenu obsolète).

## REPRISE (démarrage à froid)
« lis `sprints/sprint_vent_evapotranspiration/00_etat.md` puis le `tN_*.md` du
tronçon ⏳ le plus haut » → exécuter ce tronçon, garder/re-figer le golden comme
indiqué, respecter le budget perf.
