# Backlog — voix narratives

> Fragment de [`BACKLOG.md`](../../../BACKLOG.md) — les entrées de sprint qui
> concernent ce thème, reprises **verbatim**. L'index global des thèmes et
> les kickoffs de dette dormante restent à la racine.

| Sprint | Fichier kickoff |
|---|---|
| **Bloc voix narratives (D13 magazine + D14 carnet + D18 pages secrètes + D43 acclimatation + encyclopédie + D12.2)** — ✅ **CONCEPTION FIGÉE 2026-06-29** → spec unifiée `docs/narration/voix/conception_voix_narratives.md` (§0→§8). Décisions Nico : **substrat = ledger partagé** (`sim/journal.py`, extrait de `_evenements()` → `sim/evenements.py`, consigné par le DRIVER hors tick → golden INTACT) ; **4 voix lecteurs read-only** (carnet « je » par événement, encyclopédie « naturaliste » par espèce, pages secrètes lore pur, magazine 4ᵉ canal) ; **encyclopédie 3 niveaux** sur paliers 1/2/3 (A) ; **carnet bascule interprétatif au palier 3** du concept (B, D43 = cas `adaptation`) ; **magazine sœurs au palier 3** famille (C) ; **table D12.2** remplie (§3, seuils → D12.4). **Corpus complet** : carnet (gabarits 2 registres §5), **encyclopédie 28 fiches × 3 niveaux** (§6), **pages secrètes 20 entrées 5 voix** (§7). Roadmap impl. **6 tronçons** (①evenements→②journal→③carnet→④encyclopédie→⑤pages→⑥magazine, tous golden-neutres, §8). **CONCEPTION SEULE — pas d'impl. tant que Nico ne lance pas** (portage non prioritaire). Mémoire `design_voix_narratives.md`. Reste : impl. Python (6 tronçons) + UI Godot (D24) + marqueurs bouture/oiseau/vent + calibrage D12.4 | `docs/narration/voix/conception_voix_narratives.md` + journal |
