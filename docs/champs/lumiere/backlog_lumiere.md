# Backlog — lumière

> Fragment de [`BACKLOG.md`](../../../BACKLOG.md) — les entrées de sprint qui
> concernent ce thème, reprises **verbatim**. L'index global des thèmes et
> les kickoffs de dette dormante restent à la racine.

| Sprint | Fichier kickoff |
|---|---|
| Sprint éclairement (Z7, D20-D21 : ombres pixel + pérennes + réalignement OM) — ✅ **TERMINÉ 2026-06-02 (Python)** | `sprints/sprint_eclairement.md` |
| Sprint conception Maison & ombre déterministe (conception seule) — ✅ **TERMINÉ 2026-06-07** → spec `docs/champs/lumiere/conception_maison_ombre.md`. Maison centrale **8×8×6 m** (calcaire Montmartin, albédo espalier borné, **paramétrable**) projette une **ombre déterministe** dans le `LightField` ; monde agrandi **20×20 m = 1600 plots** ; **chemins en pierre** entre tuiles (option B : champs lumière par tuile conservés, pas d'ombrage inter-tuiles → coût ×30 évité) ; **phototropisme** branché (apex se penche) ; **golden réduit en smoke test**. 6 décisions tranchées (Q1-Q6) | `sprints/sprint_maison/00_etat.md` |
| **Sprint impl. Maison & ombre (Python)** — ✅ **CLOS côté Python 2026-06-07** (tronçons 1-4). **1** monde 20×20 m + maison inerte + golden smoke test (`world/building.py`) ✅ ; **2** ombre maison (rectangle balayé) + albédo espalier dans `LightField` ✅ ; **3** phototropisme branché dans `growth.py` (`phototropism_strength` défaut **marqué 0.30**, borné) ✅ ; **4** maquette saisonnière 3 secteurs × 4 saisons (`render_maquette`, 2 fichiers subtil/marqué) ✅. Golden smoke test `16a1b937…`. Verdict phototropisme provisoire = **marqué**, à reconfirmer avec organes/Godot. **Plus tard** (tronçon 5, hors sprint) : rendu Godot maison + ombre, portage C# (D24) | `sprints/sprint_maison/00_etat.md` |
