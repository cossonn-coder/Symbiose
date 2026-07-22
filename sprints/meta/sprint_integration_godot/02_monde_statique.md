# Tranche 2 — Monde statique rendu (le snapshot devient visible)

> **Kickoff autosuffisant.** Lire d'abord `00_etat.md` (Option B actée ; tranche 1
> CLOSE : le pont `sim_server.py` ↔ `SimBridge.cs` fonctionne, confirmé F5 chez
> Nico). But de la tranche : **Godot dessine le MONDE reçu par le pont** — tuiles
> hétérogènes, maison, plantes à leur position monde — et plus la démo statique.
> Pas d'animation ni d'interaction (tranches 3-4). Ampleur : **moyen/gros**
> (1 fichier Python étendu, 2-3 fichiers C#, 1 scène). Lève **D2, D8**, et statue
> sur **D3/D4** (voir « Dette » en bas).

## 📖 Pédagogie — ce qu'on construit et pourquoi

**Du snapshot à l'écran, c'est un pipeline de projection.** Le moteur vit en
coordonnées **monde top-down** (cm, x = est-ouest, y = nord-sud, 20×20 m). L'écran
veut de l'**isométrique pixel art**. Toute la tranche est UNE transformation :
`(x_cm, y_cm) monde → (px, py) écran iso`, appliquée aux 3 familles d'objets
(plots de tuile, empreinte maison, collets des plantes). Une seule fonction,
écrite une fois, utilisée partout — si elle est juste, TOUT est aligné ; si on la
duplique avec des variantes, plus rien ne coïncide (c'est exactement le bug D2
actuel : `TileGrid.cs` projette en 96×48 des sprites qui font 78×57).

**Godot reste « bête ».** Il ne calcule rien d'écologique : il lit `init.world`
(statique : layout des tuiles, maison) et le snapshot (plantes + segments), et
les dessine. Toute donnée manquante s'ajoute **au snapshot côté Python** (lecture
seule), jamais en logique C#.

## État de départ (acquis tranche 1)

- `core/SimBridge.cs` : `Init(seed, config)` → `world` (tuiles : `id`, `soil`,
  `rows`, `cols`, `origin_x_cm`, `origin_y_cm` ; maison : `footprint_cm`
  [x0,y0,x1,y1], `height_cm`) ; `StepWeek()`/`GetSnapshot()` → snapshot (plantes :
  `tile`, `species`, `name`, `x_cm`/`y_cm` **locaux tuile**, `stage`, `stage_name`,
  `height_cm`, `segments` au format Croissance·6).
- `visuals/PlantRenderer.cs` : dessine déjà une `PlantStructure` (segments) en
  `_Draw()`, projection `Iso()` portée de Python, LOD silhouette ≤×4 —
  **réutiliser, brancher sur le snapshot** au lieu de `structure.json`.
- `core/PlantStructure.cs` : DTO + parsing des segments — le snapshot a le même
  schéma de segments, il faut juste un point d'entrée depuis un
  `Godot.Collections.Dictionary` (pas un fichier).
- Position monde d'une plante : `origin_*_cm` de sa tuile + `x_cm`/`y_cm` locaux.
- 1 plot = 50 cm (`PLOT_CM`). Monde 20×20 m. Chemins de 50 cm entre tuiles
  (non simulés). Maison : empreinte [600,600]→[1400,1400], 6 m de haut.

## Livrables

1. **Python — monde complet dans `sim_server.py`** : accepter
   `init(config="full")` → le layout 3×3 réel (8 tuiles `SECTORS` + maison,
   **réutiliser la fabrique de `main.py`** comme la tranche 1 a réutilisé
   `build_world` du golden — import, pas de copie ; si `main.py` mélange
   fabrique et scénario, extraire la liste `SECTORS`/`build_tile` est OK, c'est
   de la réutilisation, pas un changement de logique). `config="smoke"` reste le
   défaut des tests. Étendre `tests/test_sim_server.py` (forme du monde full :
   8 tuiles, sols variés, origins distincts). **Golden intact** obligatoire.
2. **C# — `world/WorldView.cs` + scène `WorldView.tscn`** (nouvelle scène
   principale, propre, dans le namespace `Symbiose`) :
   - au `_Ready` : `SimBridge.Start → Init(seed, "full") → GetSnapshot`, puis
     construit le visuel. (Le process reste ouvert — les tranches 3-4 s'en
     serviront ; `Quit()` sur `_ExitTree`.)
   - **une seule fonction de projection** `WorldToScreen(x_cm, y_cm)` (iso 2:1
     sur la **diagonale du plot**), utilisée pour les tuiles, la maison et les
     plantes. Mesurer le **losange utile** dans `tile_terre.png` (78×57 fichier ;
     déterminer hauteur losange vs épaisseur de socle) → constantes calibrées
     sur le sprite réel (**lève D2**).
   - tuiles : un `Sprite2D` par plot, texture par `soil` (`tile_terre`,
     `tile_argile`, `tile_sable` — noms français du `SpriteLoader`, déjà
     chargés) ; ZIndex par profondeur (y croissant devant).
   - maison : **placeholder procédural** (Polygon2D : empreinte iso + 2 façades
     extrudées de `height_cm`, gris calcaire) — pas de sprite (D4 reste ouverte,
     le sprite normand viendra ; le placeholder donne l'occupation et l'échelle).
   - plantes : un `PlantRenderer` par plante du snapshot, posé à
     `WorldToScreen(origin + x/y locaux)`, structure issue des `segments` du
     snapshot. Les espèces non procédurales n'ont que 1-2 segments génériques →
     elles apparaissent comme des pousses minimales, **assumé** en t2.
3. **Conservation** : `TileGrid.cs`/`TileGrid.tscn` et l'ancien `Main.tscn`
   restent dans le dépôt (rien n'est jeté — règle projet) ; seul
   `run/main_scene` bascule sur `WorldView.tscn`. Le toggle smoke test du pont
   (t1) reste accessible via TileGrid.

## Critères de succès (vérifiables)

- [ ] `python3 -m tests.test_sim_server` vert (smoke + forme du monde full).
- [ ] `python3 -m tests.test_golden` **inchangé** (`16a1b937…`).
- [ ] Nico, F5 : le monde 3×3 complet s'affiche — 8 tuiles aux **bons sols**
      placées selon leurs `origin_*_cm`, maison centrale visible, plantes du
      snapshot posées à leur position monde (tomate/pommier avec branches).
- [ ] Les tuiles se touchent proprement (plus le « grid cassé » du 96×48) ;
      mesurer la taille du snapshot full (8 tuiles) et la noter dans `00_etat.md`.

## Points ouverts (défaut sobre + signaler)

- **Transparence des tuiles** : Nico voit des tuiles **opaques** — vérifier si
  c'est le PNG (fond non transparent) ou l'import Godot. Si les PNG tuiles sont
  RGB sans alpha (comme les plantes, cf. mémoire assets), choisir : ré-export
  des assets OU chromakey à l'import — à trancher avec Nico, défaut = constater
  d'abord.
- **Chemins en pierre** (bandes de 50 cm entre tuiles) : pas dessinés en t2
  (fond uni) — viendront avec l'habillage.
- **Ombre de la maison** : PAS en t2 (le snapshot ne l'expose pas encore) —
  reportée à la tranche 5 (overlays lumière), sauf demande de Nico.
- **Caméra/zoom** : un `Camera2D` simple pour cadrer le monde suffit ; les
  paliers ×4/×8/×16/×32 = hors tranche.

## Dette

**D2 levée** (constantes calibrées sur le sprite réel). **D8 levée** (nouvelle
scène principale propre ; l'ancien `Main.tscn` conservé mais plus référencé).
**D3 statuée par obsolescence partielle** : le rendu plante est **procédural**
(segments, pas de PNG par stade) → le mismatch `basil_*`/`basilic_*` ne bloque
plus le rendu ; D3 reste ouverte pour ce qui consommera encore des sprites
nommés (rondelles, indicateurs). **D4 reste ouverte** (placeholder maison en
attendant le sprite normand). Mettre `DETTE.md` à jour en fin de tranche.

## Boucle de travail (rappel)

Travailler → tests + golden verts → F5 Nico → mettre à jour `00_etat.md`
(tranche 2 ✅ + décisions + mesure snapshot full) → entrée `journal.md` →
mettre à jour `DETTE.md` (D2/D3/D8) → commit → `/clear` → tranche 3.
