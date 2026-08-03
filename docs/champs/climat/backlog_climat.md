# Backlog — climat

> Fragment de [`BACKLOG.md`](../../../BACKLOG.md) — les entrées de sprint qui
> concernent ce thème, reprises **verbatim**. L'index global des thèmes et
> les kickoffs de dette dormante restent à la racine.

| Sprint | Fichier kickoff |
|---|---|
| Sprint conception météo (conception seule : météo/climat + signes diégétiques, D16+Z2) — ✅ **TERMINÉ 2026-06-03** → spec `docs/champs/climat/conception_meteo.md` | `sprints/sprint_conception_meteo.md` |
| Sprint implémentation météo (porter `docs/champs/climat/conception_meteo.md` en Python : `weather_at`/forecast, `temperature`, gène rusticité, signes) — ✅ **TERMINÉ 2026-06-04** (4 sous-sprints, golden `63bfdac4…`) | `sprints/sprint_meteo_impl/00_etat.md` |
| Sprint VENT & ÉVAPOTRANSPIRATION (D37 complet : vent micro-climatique + évapotranspiration enrichie) — ✅ **TERMINÉ 2026-06-30** (⓪→⑦, perf-first) : masse d'air `sim/wind.py`, évapotranspiration rayonnement+vent (re-résout D39), abri spatial `fields/abri.py` (cache → perf +0 %), thigmomorphogénèse (`port_trapu`), pollinisation/dispersion anémophiles, vent×maladies fongiques, transport éolien de la litière `fields/ecofields/transport.py` + voix `transport_litiere`. Solde **D37**+**D32**+**D39**. Golden re-figé maîtrisé `0d3ca606…`, `test_vent` 54/54, `test_sim_server` 207/207, `test_senescence` PASS. « Arbres en drapeau » → dette future | `sprints/champs/climat/sprint_vent_evapotranspiration/00_etat.md` |
| Sprint EFFONDREMENT MÉTÉO PARTAGÉE (D104 : impact météo hétérogène + préavis dramatique du composé + encart « état du ciel » + couvertures voile/cloche/ombrière) — **✅ CLOS le 2026-08-03** (`/sprint-auto`, ①→④). Golden `9ad035f18…` → `22768f339…` (re-figé au ① comme prévu, ②③④ intacts), `dotnet build` VERT. ① `weather.patch_local` (scope="local" honoré) + averse par le relief · ② `sim/ciel.py` `convergence`/`ciel_semaine` read-only · ③ voile/cloche/ombrière posables par le milieu · ④ pont 0.5.43 + encart `SkyPanel.cs` diégétique + banc `effondrement`. Reste F5 Nico. Voir `journal/147_2026-08-03_sprint-effondrement-meteo-CLOS.md`. | `sprints/champs/climat/sprint_effondrement_meteo/00_etat.md` |
