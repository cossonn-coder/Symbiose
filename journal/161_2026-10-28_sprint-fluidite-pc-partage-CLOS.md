## 2026-10-28 — Sprint FLUIDITÉ PC PARTAGE (3ᵉ temps D116) — CLOS

`/sprint-auto`, tronçons ①→④, golden `fecccded…` **jamais re-figé**, pont 0.6.0.
Détail et mesures : `sprints/perf/fluidite/sprint_fluidite_pc_partage/00_etat.md` §1-§4.

- ① `80ea965` — moteur bit-identique : `gc.freeze` + seuil gen0 50 000 après `cmd_init`
  (gc 39 → 2 ms/sem, pire 217 → 73 ms [n=3 runs, VM chargée]) ; `_snapshot` mémoïsé
  par segment (−15 % [n=3 runs, charge variable], cible −40 % non tenue : le reste se
  recalcule dans `sim/`). Pont octet-identique (outil `tools/verif_pont_identique.py`).
- ② `1a7eeeb` — régulateur de cadence (15 FPS en Saison si la semaine due attend le
  moteur ; plein FPS en Planification et 1 s après un mouvement caméra) + priorité moteur
  basculable + banc de partage A1..A4. VM : régulé ~0 % [n=1 run, charge 8-10].
- ③ `9828dee` — ligne « GPU » du rapport Z : à ×8+ le va-et-vient vient des pages
  d'atlas DÉDIÉES détruites en rafale (×16→×32 : 10, −272 Mo [n=3 allers-retours, VM]).
  Levier « réserve de pages partagées » essayé, inerte, retiré.
- ④ `72c8169` — bilan VM : A 2,10 → 2,01 s/sem, 1,82 avec régulateur [n=1 run chacun,
  VM charge 0,9→4,5] ; protocole d'un run PC + règles de lecture.

**Décision :** levier 5 (enchaînement anticipé du step) rejeté (latence geste ~2 s), en
dette D116 seulement si 1-4 ne suffisent pas. Plancher 15 FPS accepté.

**Question :** au run PC — le régulateur s'engage-t-il (sinon « semaine due » à l'horloge
murale) ? priorité Normal par défaut ? les pages dédiées portent-elles le pic ×8→×4 ?
