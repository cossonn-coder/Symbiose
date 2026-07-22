# Backlog — transverse projet & portage C#

> Fragment de [`BACKLOG.md`](../../BACKLOG.md) — les entrées de sprint qui
> concernent ce thème, reprises **verbatim**. L'index global des thèmes et
> les kickoffs de dette dormante restent à la racine.

| Sprint | Fichier kickoff |
|---|---|
| Sprint 2 (orchestration C#) | `sprints/meta/sprint_2_orchestration.md` |
| Sprint refactor structurel (réorg `data/code/` en paquets + archive journal + dette/backlog source unique + golden output) — ✅ **TERMINÉ 2026-06-03** | `sprints/sprint_refactor_structurel.md` |
| **Sprint Intégration Godot ↔ Python (PROCHAIN)** — 🟢 **kickoff prêt 2026-06-07**. Architecture **ACTÉE = Option B** (Python moteur / Godot vue, pont sous-process JSON ; moteur pur-stdlib → binaire gelé ; source de vérité unique). Découpé en ~6 tranches verticales (pont minimal → monde statique rendu + fix D2/D3/D8 → saison animée → actions joueur → organes/overlays/vie macro → packaging PyInstaller). Lève D24 (« portage » → « pont ») + D2/D3/D4/D8. ⚠️ Pas de `dotnet` ici → Nico build/lance dans Godot, Claude code | `sprints/meta/sprint_integration_godot/00_etat.md` |
| Sprint 3 (portage simulation — peut absorber le sprint éclairement) | `sprints/meta/sprint_3_portage_simulation.md` |
| Sprint 4 (mécaniques conception) | `sprints/meta/sprint_4_mecaniques_conception.md` |
