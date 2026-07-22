# Sprint 1 — Recalibrage visuel : dimensions, nomenclature, maison

**Statut** : à faire
**Prérequis** : Sprint conception terminé (`509ff4c`). Sprint conception
bis recommandé mais pas bloquant — le visuel ne dépend pas des décisions
sauvegarde/lore.
**Estimation** : 1 à 3 sessions, dont la première peut être courte
(décisions sur le format des sprites)
**Objectif** : aligner ce qui est codé dans `world/TileGrid.cs` avec ce
qui est sur disque dans `assets/sprites/`, générer le sprite maison
manquant, et obtenir un premier rendu Godot cohérent à l'écran d'une
grille 3×3 tuiles avec maison centrale.

---

## Avant de commencer

1. **`CLAUDE.md`** est déjà chargé. Lis-le.
2. **`journal.md`** — lis surtout :
   - Section « Dette technique consolidée », dettes **D2, D3, D4**
     (mismatch dimensions, mismatch noms, sprite maison absent)
   - Sprint conception : décision 12 (extension par maîtrise) — pour
     comprendre que 9 tuiles est le départ, pas une limite
3. **Memory** — `reference_assets.md` contient les dimensions mesurées
4. **Code à lire** :
   - `world/TileGrid.cs` (~140 lignes) — code actuel à refondre
   - `world/TileGrid.tscn` — scène attachée
   - `core/SpriteLoader.cs` — autoload, charge les sprites de
     `assets/sprites/`
   - `core/TileData.cs` — méthode `HexToScreen` à aligner sur la grille
   - `project.godot` — vérifier `run/main_scene` (uid pointant vers
     TileGrid.tscn)

---

## État disque vs état code

Mesures réelles au 2026-05-29 :

| Sprite | Disque | Codé | Conformité |
|---|---|---|---|
| `tile_terre.png` | 78×57 RGBA | 96×48 (TileGrid.cs) | ❌ |
| `tiles.png`, `rondelles.png` | 1408×768 sheets | non parsés | ❌ |
| `basilic_1_semis.png` | 308×189 **RGB sans alpha** | `basil_1_semis` attendu | ❌ |
| Stades autres plantes | sheets sans découpe | noms anglais individuels attendus | ❌ |
| `maison.png` | **absent** | absent | manquant |

Catalogue C# (`core/PlantCatalogue.cs`) référence `tomato_1_semis`,
`basil_1_semis`, `bean_1_semis`, `clover_1_semis`, `sunflower_1_semis`,
`bursa_1_semis`, etc. Aucun n'existe sur disque.

---

## Tâches dans l'ordre

### T1. Décision : format final des tuiles
**Avant tout code**, faire trancher Nico (par AskUserQuestion si besoin) :
- Garder le sprite 78×57 actuel et adapter `HexToScreen` ?
- Ou re-générer toutes les tuiles en 96×48 pour matcher le code ?

Conseil : **78×57 conservé**. Re-générer 4 sprites prend du temps,
adapter le code en prend peu. Mais c'est Nico qui décide.

### T2. Décision : nomenclature sprites
- Renommer les fichiers sur disque (`basilic_1_semis` → `basil_1_semis`) ?
- Ou modifier le catalogue C# pour pointer vers les noms français ?

Conseil : **modifier le catalogue C#**. Le français est la langue projet
(CLAUDE.md). Conserve la cohérence linguistique.

### T3. Décision : sprite maison
- Style annoncé : normande, calcaire gris, toit ardoise, volets bois,
  Montmartin-sur-Mer
- Source : Nico génère (Aseprite / outil IA), ou Claude propose un
  prompt génératif à un outil externe
- Dimensions cohérentes avec la grille de tuiles (probablement
  3×3 plots = 234×171 si tuile 78×57, à ajuster pour donner une
  emprise visuelle de maison)
- Le sprite doit avoir un canal alpha (chromakey ou alpha natif)

### T4. Mesurer toutes les tuiles
```bash
file /home/nico/Nextcloud/projects/symbiose/assets/sprites/tiles/*.png
```
Confirmer que `tile_argile`, `tile_sable`, `tile_roche` sont aussi en
78×57. Sinon, les uniformiser.

### T5. Refondre `world/TileGrid.cs`
- Constantes `TileW` et `TileH` selon décision T1
- Logique de **grille 3×3 tuiles** (pas 3×3 plots) avec **tuile centrale =
  maison** (pas cultivable)
- Pour chaque tuile cultivable (8 sur 9), instancier la grille de
  **6×8 plots** en quinconce dans la tuile
- ZIndex correct (les plantes du sud occulent celles du nord, la maison
  porte une ombre dynamique au sprint 4)
- Pas de placeholder magique — supprimer le code de debug
  `_Input` qui imprime « Survol plot » dans la console
- Synchroniser `TileData.HexToScreen` (statique dans `TileData.cs`) avec
  la nouvelle géométrie

### T6. Aligner `PlantCatalogue.cs` ↔ noms de fichiers
Selon décision T2 :
- Soit renommer 50+ fichiers sur disque
- Soit modifier chaque `SpriteName = "tomato_1_semis"` en
  `SpriteName = "tomate_1_semis"` (et créer les fichiers s'ils manquent)

Attention : les sheets 1408×768 (`tomates.png`, `haricot.png`, etc.)
**ne contiennent pas les stades individuels**. Un découpage est nécessaire,
soit dans Godot via `AtlasTexture`, soit via export PNG individuels.

### T7. Vérification visuelle
- Ouvrir Godot 4.6 .NET en SSH ? Pas possible. Demander à Nico de
  vérifier à l'écran sur sa machine, ou utiliser un outil headless de
  rendu si disponible.
- Critère : la scène `TileGrid.tscn` s'ouvre, la grille 3×3 tuiles est
  centrée, la maison est dans la tuile centrale, les 8 tuiles
  cultivables affichent correctement leur sol.

---

## Pièges connus

- **`SpriteLoader` est récursif** — il charge tout `assets/sprites/`
  sous-dossiers compris, avec la clé = nom de fichier sans extension.
  Donc renommer un fichier change la clé.
- **Sprites basilic en RGB sans alpha** → la chromakey magenta
  `#FF00FF` annoncée dans l'ancienne doc n'est pas en place. À
  appliquer en post-process (Aseprite ou ImageMagick) avant intégration.
- **`Main.tscn` est obsolète** (D8) mais pas dans le scope de ce sprint.
  Ne pas y toucher — c'est Sprint 2.

---

## À produire à la fin

- [ ] `world/TileGrid.cs` refondu (grille 3×3 + maison)
- [ ] `core/PlantCatalogue.cs` mis à jour selon décision T2
- [ ] `assets/sprites/tiles/maison.png` créé (ou prompt génératif livré
      à Nico s'il préfère générer lui-même)
- [ ] `core/TileData.cs:HexToScreen` cohérent
- [ ] **`journal.md`** : nouvelle entrée datée, dettes D2/D3/D4 marquées
      ✅ levées, décisions T1/T2/T3 actées
- [ ] **Commit** dédié avec message HEREDOC, ex :
      `Sprint 1 : recalibrage visuel et grille 3×3 + maison`
- [ ] Proposer Sprint 2 (orchestration) à Nico

---

## Critère de fin

Au lancement de `TileGrid.tscn` dans Godot 4.6 :
1. Une grille 3×3 tuiles s'affiche, centrée à l'écran
2. La tuile centrale montre la maison (avec son canal alpha respecté)
3. Les 8 tuiles cultivables affichent leur sol (terre par défaut)
4. Aucune erreur dans la console Godot
5. Pas de sprite manquant signalé par `SpriteLoader`
