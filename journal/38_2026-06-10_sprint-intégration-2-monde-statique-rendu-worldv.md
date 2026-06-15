## 2026-06-10 — Sprint Intégration·2 : monde statique rendu (`WorldView`)

### Contexte

Tranche 2 du sprint Intégration (kickoff `02_monde_statique.md`) : Godot
dessine le **monde complet** reçu par le pont — 8 tuiles hétérogènes, maison,
plantes posées en position monde — et plus la démo statique. Pas d'animation
ni d'interaction (tranches 3-4).

### Constat assets (mesuré, point ouvert du kickoff tranché)

Les PNG tuiles sont **inutilisables pour une grille jointive** : le damier de
transparence a été **cuit en gris** dans l'image (alpha=255 partout — c'était
la cause des « tuiles opaques » vues en t1), et les tailles sont
**incohérentes** (`tile_terre` 78×57, `tile_argile`/`tile_sable` 32×23 ;
rapport ×2,44 non entier). Losange utile mesuré sur `tile_terre` : **78×39 px**
(iso 2:1 exact) + socle ~15 px.

**Décision (Nico) : placeholders procéduraux** (losanges `Polygon2D`, teintes
dominantes mesurées des PNG : terre `#967a64`, argile `#cd7434`, sable
`#f1e9bb` ; damier ±5 % ; fond fenêtre gris pierre = chemins) **+ cahier des
charges/prompt pour régénérer les sprites via un LLM d'images** →
`assets/sprites/tiles/GENERATION_TUILES.md`, nouvelle dette **D34**. Les PNG
actuels restent en place.

### Fait — Python

- `main.py` : **fabrique extraite** (`build_world_full()` — 8 tuiles SECTORS
  plantées + maison) et scénario démo passé sous `if __name__ == "__main__"`.
  Sortie vérifiée **byte-identique** (diff vide sur `main.py 1` avant/après).
- `tools/sim_server.py` : `init(config="full")` → monde complet (import de la
  fabrique, zéro copie ; `smoke` reste le défaut).
- `tests/test_sim_server.py` : **30/30** (nouvelle section monde full : 8
  orientations, 3 sols, origins distincts, maison [600,600]→[1400,1400], 53
  plantes posées, config inconnue refusée + serveur survivant).
- **Golden intact** (`16a1b937…`).

### Fait — C# (la VUE)

- **`world/WorldView.cs` + `WorldView.tscn`** : nouvelle scène principale
  (`run/main_scene` basculé ; `Main.tscn`/`TileGrid.tscn` conservés, plus
  référencés). `_Ready` : `Start → Init(42,"full") → StepWeek×12 → rendu` ;
  process Python laissé ouvert (tranches 3-4), `Quit()` sur `_ExitTree`.
- **Projection UNIQUE** `WorldToScreen(x_cm,y_cm)` calibrée sur le losange
  réel (78×39 px / 50 cm → 0,78/0,39 px/cm ; `PxPerCmZ`=0,78) — **D2 levée**.
  `PlantRenderer.Iso` **délègue** à cette projection (l'ancien couple
  cos30×PxPerCm=0,42 de la maquette SVG supprimé) → échelle plante = échelle
  monde (pommier 350 cm ≈ 273 px), démo TileGrid plus grande qu'avant, assumé.
- **Ordre de dessin** : sol (ZIndex 0) / objets (ZIndex 10 + **YSortEnabled**,
  ancrage = point de contact au sol le plus proche caméra — collet plante,
  coin SE maison).
- Maison **placeholder procédural** (empreinte iso + façades est/sud extrudées
  de `height_cm` + toit, gris calcaire) — D4 mitigée, sprite normand à venir.
- `StructureLoader.FromSnapshot()` dans `PlantStructure.cs` (collet = base du
  segment 0, comme `export_structure.py` ; parsing segments factorisé).
  Plantes sans segments : pas de nœud, comptées en console.
- Caméra de cadrage zoom 0,5 (paliers entiers = hors tranche).

### Mesures

Snapshot full : ~17 Ko sem 2 (54 plantes) → **~83 Ko sem 13** (152 plantes,
germinations seedbank comprises) — négligeable à 1 snapshot/60 s. Tick full
≈ **150 ms** ; warmup 12 semaines ≈ 1,8 s au lancement.

### Dette

**D2 ✅ levée**, **D8 ✅ levée**, **D3 statuée** (obsolescence partielle : rendu
procédural), **D4 mitigée** (placeholder), **D34 ouverte** (ré-export assets
tuiles). `DETTE.md` à jour.

**Statut.** Tranche 2 **CLOSE** — confirmée par Nico dans Godot le jour même :
monde complet (1188 plots, maison, **152 plantes affichées / 0 ignorées**,
warmup 12 semaines = 3451 ms sur son poste). Plantes « toutes petites » =
attendu (échelle monde × zoom cadrage 0,5), résolu par les futurs paliers de
zoom. **Demande post-F5 → D35** : contrôles caméra (déplacement aux flèches,
zoom par paliers ×4-×32, rotation de la vue par quarts de tour — re-projection
d'orientation dans `WorldToScreen`, pas une rotation canvas). Signalé au
passage : un dossier `symbiose/` parasite (projet Godot vide auto-créé) traîne
à la racine, non suivi par git. **Prochaine : tranche 3 (saison animée),
kickoff `03_*.md` à écrire.**

---
