# CONCEPTION — Plante assemblée (silhouettes, perf ×4 + accéléré, légende des signes)

> Conception **FIGÉE le 2026-10-19** (`/conception`, à partir de
> [`entree_plante_assemblee.md`](entree_plante_assemblee.md)). Sprint :
> `sprints/rendu/pixelart/sprint_plante_assemblee/`. Absorbe **D109 (d)(e)(f)**.
> Bilan d'entrée chiffré : `sprints/perf/lod/sprint_perf_vue/00_etat.md`.
> **Golden jamais re-figé** (référence `22768f33…`) : tout est vue ou pont, rien dans le tick.

## 1. Le problème (F5 de Nico, 2026-10-19)

1. **Paliers bas « horribles »** : ×0,5, ×1, ×2 = « gros blobs verts ». ×4 est le zoom où l'on veut rester.
2. **Perf** : ×4 = 32,5 FPS sur le PC (critère 60 raté, ~12 ms à trouver, tout en rendu CPU) ;
   **accéléré** (Continu 3 s/semaine, ×8) = 5 FPS, 199 ms/image [PC, n=1 chacun].
3. **« Ce que je vois, je ne sais pas l'identifier »** : liseré brun, taches noires, bêtes.
4. Bug : légende F1 coupée en bas d'écran (`world/WorldView.Hud.cs`, ligne « F3 étiquettes… I vie macro… »).

## 2. Diagnostic vérifié

### 2.1 Pourquoi des blobs
`visuals/PlantRenderer.Paliers.cs` : sous ×4, une plante = **une ellipse 2 tons** (tache à ×0,5,
ellipse du port à ×1 parmi 8 ports, + teinte santé à ×2). La structure réelle est abandonnée alors
qu'elle tient à l'écran : une tomate de 60 cm fait ~47 px internes de haut à ×2, ~23 à ×1, ~12 à ×0,5
(0,39 px/cm × palier). En jardin dense (s45 : 272 plantes) les ellipses se chevauchent → blobs.

### 2.2 Où vont les draw calls à ×4
Banc E s45, VM, couches masquées une à une (`tools/perf_vm.sh -E 5 -z 4 -x …`). Le nombre de draw
calls est la métrique portable VM ↔ PC.

| couche | draw calls [VM, n=1] |
|---|---|
| total | 2 013 |
| **Decor** (ceinture : forêt, rivière, falaise, prairie) | **1 099** |
| couvre-sol (Couverture, Allelopathie, Mulch, Puddle, Litter, LeafLitter) | 449 |
| Objects (plantes + maison) | 380 |
| vie macro + ciel + météo + Vignette | 34 |
| Ground (masquage sans effet mesurable — à comprendre au ①) | 0 |

`DecorLayer` est un nœud **statique** (redessiné seulement aux bascules de LOD) dont le `_Draw`
émet des centaines de `DrawColoredPolygon`/`DrawCircle` : chaque primitive = un envoi GPU. Même
défaut, en plus petit, pour les couvre-sol. Les plantes : une texture cuite **par plante**
(`PlantBaker`, atlas de poses propre à chaque plante) → pas de lot possible entre plantes.
**Estimation (hypothèse)** : à ~14 µs par draw call [PC, n=1], 2 000 → ~300 ≈ −24 ms par image.

### 2.3 Accéléré
Pas un problème de draw calls (936 à ×8). Tick serveur 2 354 ms contre ≤ 1 495 au nominal [PC, n=1
chacun] → **hypothèse** : contention Python ↔ Godot sur 2 cœurs. Suspects vérifiés au code :
`ForagerLayer` appelle `QueueRedraw()` **à chaque image** dès que son palier est atteint (70 butineurs) ;
la priorité réduite du serveur (`SimBridge.BaisserPriorite`, `BelowNormal`) n'a jamais été constatée
sous Windows. Le rapport F4 n'a pas les postes en accéléré → **instrumenter**.

## 3. Décisions (Nico, 2026-10-19)

1. **Un seul sprint** A + B + C + bug F1, un seul F5 final. Ordre : perf → silhouettes → légende.
2. **Silhouettes = plante assemblée** aux paliers bas (×0,5 · ×1 · ×2) : les **vraies tiges** (1 px) +
   des **éléments de pixel-art** (touffes de feuillage, fleurons) posés sur les **vrais segments**.
   Les touffes sont **générées une fois** (atlas du kit) depuis la table **`LeafShape` par espèce**
   déjà existante (`PlantRenderer.Leaf.cs` : composée, elliptique, cordée, lobée, lancéolée,
   aciculaire) et la palette d'espèce → continuité visuelle avec ×4. **×4 et au-delà inchangés.**
3. **« Pixels plus fins » = éléments plus petits et détaillés**, pas la pleine résolution : le monde
   reste 960×540 ×2 (décision 8 de PERF VUE close sans suite).
4. **Info-bulle au survol à deux niveaux** (plantes ET bêtes) :
   - **par défaut, descriptive** : ce qu'on VOIT (« liseré brun-noir au bord des feuilles »,
     « petit coléoptère rouge à points ») ; la **cause** d'un signe / le **nom** d'une bête n'apparaît
     qu'une fois **appris** ;
   - **affichage technique** (touche dédiée, étiquetée comme F6, « déconseillé en première
     découverte ») : nomme tout — cause + intensité, espèce.
5. **Accéléré : mesure en fin de sprint** — instrument + correctifs des suspects évidents pendant le
   sprint ; UN banc lancé par Nico à la fin tranche. Raté → dette chiffrée, pas de boucle.

## 4. Modèle

### 4.1 Perf ×4 — tout en lot (cible ≲ 300 draw calls à ×4 [VM])
- **Decor** et **couvre-sol** : leurs primitives sont accumulées dans un `ArrayMesh` (couleurs par
  sommet) dessiné par **un** `DrawMesh` — recette déjà en place : `visuals/PlantShadow.cs` (ombres en
  lot, PERF VUE ③), `world/SolMaillage.cs` (sol par tuile, D106). Reconstruit seulement quand le
  contenu change (bascule de LOD, rotation, snapshot pour les couvre-sol). Image identique au pixel
  (capture VM avant/après).
- **Plantes** (D109 d) : les cuissons partagent des **pages d'atlas communes** au lieu d'une texture
  par plante, pour que Godot regroupe les plantes consécutives de même texture. Image identique.

### 4.2 Accéléré
- **Banc accéléré** au F5 (touche à côté de E) ≡ `tools/perf_vm.sh -A …` : ×8, Continu 3 s/semaine,
  rapport complet **avec postes**, dont : `ForagerLayer`, application de semaine (étalement), parse
  du snapshot, GC, **priorité effective du serveur** lue par l'OS.
- `ForagerLayer` : redessin borné (cadence bornée ou lot à la manière du peintre vie macro ②) —
  forme exacte au tronçon, mesurée.
- Critère inchangé : **aucune image > 100 ms** en accéléré.

### 4.3 Plante assemblée (paliers bas)
- **Kit** : pour chaque `LeafShape`, quelques **touffes** de 3×3 à 9×9 px internes (2-3 variantes
  au hash, zéro `Random`), en **rampe de palette** (ombre / base / lumière) ; **fleurons** 1-2 px.
  Généré une fois au démarrage dans un atlas de kit (comme la palette SNES : petites rampes partagées).
- **Montage** : tiges/fût = les segments en lignes de 1 px (épaisseur réelle si plus large) ; aux
  extrémités feuillées, une touffe dont la **taille dépend du palier** (petite à ×0,5) ; densité ∝
  `foliage_density`. **Teinte** = langage des paliers actuels conservé (espèce + saison dès ×0,5,
  santé dès ×2, givre, neige, fleurs) — on change la FORME, pas l'information (tableau D4).
- Inchangé : **tapis par plot** (D5) pour les plantes sous `TapisSeuilPx`, bois nu l'hiver,
  squelettes, pré-cuisson (aucun coût par image), picking.
- La « couronne » (`Couronne()`) reste le **contour** utilisé par le picking et la boîte de cuisson.

### 4.4 Légende des signes
- **Observer un signe** = étendre l'observation par survol existante (`world/WorldView.Observation.cs`
  → commande pont `observer`, `tools/simserver/maitrise_pont.observer_espece`). Survoler une plante
  qui porte un signe **visible au palier courant** (signes foliaires fins dès ×16 — cf.
  `PlantRenderer.PaliersHauts.cs` ; teinte de santé dès ×2) consigne **une note au carnet** :
  « j'ai vu <description> sur <plante>, semaine N ». Dédup : une note par (espèce, signe, saison).
- **JAMAIS dans le tick** : le pont écrit le journal comme un geste du joueur. Si le moteur consignait
  les symptômes au snapshot, le journal dépendrait de la fréquence d'appel → non-déterminisme.
- **Appris** = palier du **concept** du signe ≥ seuil du carnet interprétatif (`SEUIL_CARNET`, avec
  l'option « interprétatif anticipé ») — la même bascule que le carnet : la note se comprend, la
  fiche « signe » de l'encyclopédie s'ouvre, l'info-bulle nomme la cause, **au même moment**.
  Bêtes : nom révélé au même seuil sur la clé de maîtrise de l'espèce (posture « visible dès le
  début, non identifiable sans maîtrise »).
- **Corpus** (donnée éditoriale Python, source de vérité) : description visible + fiche 3 niveaux
  pour chacun des **11 signes** (`sim/semiologie.py` : chlorose, secheresse, asphyxie, ravageurs,
  rongeur_racinaire, ombre, senescence, acclimatation + maladie, gel, grele) ; description visible
  pour chaque espèce de la vie macro.
- La vue reçoit du pont ce que le joueur a appris (signes, bêtes) : elle **lit**, ne décide pas.

## 5. Philosophie de design
- #1/#2 : rien n'agit sur la simulation. #3 : golden intact, zéro RNG (variantes au hash), observation
  par geste du joueur hors tick. #5 : la forme est l'information ; chiffres seulement en affichage
  technique. #6 : la cause se mérite (observer → formuler → maîtriser), le technique reste un choix
  d'accessibilité assumé comme F6.

## 6. Tronçons (golden intact partout)
| # | Contenu |
|---|---|
| ① | Decor + couvre-sol en maillage (−~1 500 draw calls) |
| ② | Plantes en pages d'atlas communes (D109 d) + bilan ×4 VM |
| ③ | Accéléré : banc + postes + priorité + `ForagerLayer` ; bug légende F1 |
| ④ | Kit d'éléments (atlas généré depuis `LeafShape` + palettes) + planche |
| ⑤ | Montage de la plante assemblée aux paliers bas |
| ⑥ | Signes côté Python : corpus, `observer` étendu, carnet, encyclopédie, « appris » au pont |
| ⑦ | Vue : info-bulle 2 niveaux + touche technique + bilan + procédure PC + F5 |

## 7. Liens
`docs/perf/lod/conception_perf_vue.md` · `docs/perf/lod/conception_rendu_visible.md` (tableau D4,
tapis D5) · `docs/narration/semiologie/conception_semiologie_foliaire.md` ·
`docs/narration/voix/conception_voix_narratives.md` · `DETTE.md` D109.
