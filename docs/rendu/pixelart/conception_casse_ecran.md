# Conception — CE QUI EST CASSÉ À L'ÉCRAN (D112) + grammaire 16 bits

> Figée le 2026-10-29 (`/conception D112`, accord Nico). Sprint :
> `sprints/rendu/pixelart/sprint_casse_ecran/`. **Référence visuelle** :
> [`etude_brief_da_16bits.md`](etude_brief_da_16bits.md) (brief de Nico, gravé tel quel).
> Pure vue + pont en lecture/debug → **golden jamais re-figé** (`fecccded…`).

## 1. Périmètre (Nico : « tout D112 »)

| Point D112 | Constat au code (2026-10-29) | Tronçon |
|---|---|---|
| (a) faune | Dessinée en **rectangles** taille réelle par espèce (`visuals/MacroLife.cs:61`) ; les « grands traits noirs » ≈ merle (25×8 cm, `1e1e22`) | ⑤ |
| (b) maison en verre | `PlantZIndex` = 10 + rang de strate (`WorldView.Luxuriance.cs:55`) : le ZIndex **prime** sur le YSort de `Objects` ; la maison est en z 0 relatif → toute plante passe devant | ② |
| (d) vent F6 | La heatmap existe quand `eco.vent` est calculé (champ paresseux, apparaît alors dans le registre `cmd_fields`, `tools/simserver/commands.py:367`). Le « bug » vu en longue partie zoom/dézoom = **HORS périmètre** (Nico). Reste : vent **en tête** du cycle F6, toujours présent, bornes fixes + `lisiere`/`turbulence` (D99) | ② |
| (e) Maj+F3 | Chiffres bruts (`WorldView.InfoBulle.cs:170`) → jauges | ② |
| (f) F11 « spray » | Post-process plein écran 34 couleurs + Bayer 4×4 (`visuals/palette_snes.gdshader:93-97`) | ③ |
| (h) psilocybe | N'apparaît qu'au banc vivant (`WorldView.BancVivant.cs:74`) ; `cmd_debug` (`tools/simserver/maitrise_cmds.py:115`) n'a pas d'op pour le faire pousser | ② |
| (i) ×2 plus beau que ×4 | **Deux moteurs** : ×0,5→×2 = touffes estampillées (`PlantRenderer.Kit.cs`) ; ×4→×32 = segments + organes (`PlantRenderer.PaliersHauts.cs`) | ④ |
| (k) décor animé | Décor = atlas statique 1 draw call (+ `DecorDevant`) | ⑥ |
| (l) soleil invisible | `Eclairement()` (`Kit.cs:286`) éclaire le BAS de la touffe, ignore le soleil | ③ |
| (m) cohérence inter-paliers | voir (i) ; le contour du ×1 (`MaitreSombre 2e3038`) est **interdit** par le brief sur les masses | ③④ |
| (n) H + DecorDevant | `ApplyHouseGhost` ne module que la maison (`WorldView.Controls.cs:279`) | ② |
| résidus lisière | vert uni au-delà de 9 m ; falaise en grands blocs à ×2 ; pic de redessin décor à ×4 (165 ms [n=1 run, VM chargée]) | ⑥ |

**Hors périmètre** : bug de vent en longue partie (Nico) ; **nuit** (rampe bleu/or) → dette
D117 ; texture du sol (règle 6 du brief — Nico trouve beau le dégradé actuel des plots, D34
inchangée).

## 2. Adaptation du brief à Symbiose (arbitrages)

1. **Une espèce = une recette** : rampe (3-5 tons, teinte qui dérive ombres → bleu-vert,
   éclats → jaune), motif (forme, taille, orientations), squelette (= la plante procédurale
   du moteur, segments `structure`), accent (fleur, liseré), ancrage (halo dithéré). **La
   même recette à tous les paliers** : un palier plus fin estampille plus de motifs, plus
   petits relativement à la plante — jamais une autre méthode (méthode 2 de Nico : partir du
   complet, retirer des détails en dézoomant). Ferme (i)(m).
2. **Contour sélectif** : masses (canopée, touffe, buisson, couvert) **sans contour** ;
   petits objets (fleurs, bêtes, pierres, bacs/pots, carpophores) = trait 1 px de la teinte
   la plus sombre de **leur propre** rampe. Jamais `#000`, jamais noir semi-transparent.
3. **Lumière = soleil RÉEL** (Nico) : l'éclat se pose sur la face tournée vers le soleil,
   à l'opposé de l'ombre portée (`WorldView.SunShadowDir`, `WorldView.Soleil.cs:24`). Les
   ombres portées sont gardées (Nico les aime) mais **teintées** (vert-noir type `#071010`
   à alpha, au lieu du noir alpha 0,18 de `PlantShadow.cs:38`).
4. **Palette INDEXÉE** (analogue CGRAM SNES / LUT d'un microcontrôleur) : la précuisson
   écrit par pixel un **indice de ton** (creux / moyen / clair / éclat…) et un **code
   d'orientation de face** ; un shader de lecture choisit la couleur dans la **LUT de la
   matière** selon la direction du soleil. Conséquences : 0 recuisson quand le soleil tourne
   (pas d'à-coup), mémoire d'atlas inchangée (au lieu de ×4 orientations), F11 post-process
   **retiré**, nuit future = échange de LUT. La météo par plante (teintes canicule, givre…,
   `PlantRenderer.Meteo.cs`) et le fondu doivent survivre — via la LUT ou un modulate.
5. **Dialectes** (validés) : 3 Secret of Mana = toute plante seule (icône vive 3-4 tons) ;
   2 Chrono Trigger forêt = couverts denses (tapis par plot, prairies, lisière : grain
   olive en chevrons) ; 1 = nuit (dette D117).
6. **Iso 2:1 conservée** ; la « grille 16 px » du brief = la grille du plot (78×39 px/plot).
7. **Déterminisme** : tout « bruit » / « tuiles retirées » / orientation de motif = **hash**
   (position, espèce, individu) — jamais `Random`. Deux voisins diffèrent par le hash, jamais
   par la rampe.
8. **Discipline** : ≤ 5 tons par matière (6 avec éclat isolé), Nearest, zoom entier, pas de
   rotation de sprite.

## 3. Instrument de validation (feedback 2026-10-14 : je valide par mesure)

La checklist du brief devient un **banc de mesure automatique** sur les PNG de
`tools/capture_vm.sh` : tons distincts par matière (via un masque d'espèce/matière), pixels
`#000` / quasi-noirs neutres, contour noir sur masse, dérive de teinte (teinte(ombre) −
teinte(éclat) dans le bon sens), deux individus voisins non identiques, éclat du côté du
soleil. Chaque tronçon visuel rend son rapport de mesure ; le F5 de Nico = **ressenti seul**.

## 4. Coût perf

- ③ palette indexée : 1 lecture de texture LUT par fragment (négligeable) ; précuisson
  inchangée en nombre ; suppression du post-process plein écran (gain). **Mesure avant/après
  obligatoire** (banc E, `tools/perf_vm.sh`) — budget ≤ +10 % de frame.
- ④ paliers hauts estampillés : risque principal (nombre de motifs à ×16/×32). Perf-first :
  cuire par palier dans les pages d'atlas existantes (`AtlasPages.cs`, plantes « prêtes par
  palier » du sprint LEVIERS) ; estampiller une seule fois par cuisson, pas par frame.
- ⑤ faune : portraits précuits par espèce et par palier, dessinés en lot (comme
  `CarpophoreLayer`) — draw calls inchangés.
- ⑥ décor animé : déformation au vent dans un shader sur l'atlas décor (aucun redessin
  CPU), éclairage via la même LUT. Le pic de redessin à ×4 se mesure à l'outil Z.

## 5. Découpage (7 tronçons, golden intact partout)

① charte + banc de mesure · ② défauts (b)(n)(e)(d)(h) · ③ palette indexée + soleil
(paliers bas) + F11 retiré + ombres teintées · ④ paliers hauts dans la même grammaire ·
⑤ faune en icônes · ⑥ lisière et décor (dialecte 2, animé, résidus) · ⑦ bilan à l'écran.
