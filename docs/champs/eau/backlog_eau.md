# Backlog — eau

> Fragment de [`BACKLOG.md`](../../../BACKLOG.md) — les entrées de sprint qui
> concernent ce thème, reprises **verbatim**. L'index global des thèmes et
> les kickoffs de dette dormante restent à la racine.

| Sprint | Fichier kickoff |
|---|---|
| **Sprint HYDROLOGIE DE RELIEF & MARÉCAGES (MOTEUR + vue)** — ✅ **CONCEPTION FIGÉE 2026-07-03** (`/conception`, s'appuie sur D57 relief) → spec `docs/conception/CONCEPTION_HYDROLOGIE_MARECAGE.md`. Ajoute la dimension hydraulique LATÉRALE : champ `altitude` micro-relief déterministe NEUF (≠ épaisseur d'humus D57) ; `eau_surface` (lame de surface) + `tick_ruissellement` (double-buffer déterministe, l'eau va des plots hauts aux bas) → **FLAQUE** ; flaque durable → **MARÉCAGE** (`marais_memory` + hystérèse → décompo anaérobie=tourbe, pH acide, niche). Guilde interconnectée : **sphaigne** (ingénieur : acidifie+retient+tourbe), **aulne** (Betulaceae NEUVE, fixe l'azote arboré), **plante carnivore** (Drosera = 1er végétal-PRÉDATEUR, puits sur la **faune de mare** moustique/libellule NEUVE → échappe à la faim d'azote D41) — chacune ses 5 voix. Gestes joueur **`creuser`** (cuvette) / **`drainer`**. **8 tronçons** (①altitude→②eau_surface+ruissellement [golden RE-FIGÉ LARGE annoncé]→③marécage→④faune de mare→⑤aulne+sphaigne→⑥carnivore+puits→⑦gestes→⑧vue). Croise D57/D40/D39/D31/D41/D55. **Prêt pour `/sprint-auto`** | `docs/conception/CONCEPTION_HYDROLOGIE_MARECAGE.md` + `sprints/sprint_hydrologie_marecage/` (00_etat + 01→08) |
