# sprint_bois_arbres — état (S2 du style homogène)

**Conception FIGÉE le 2026-11-25** (`/conception`, Nico : « oui vas y ») → `docs/rendu/splatting/conception_bois_arbres.md`.
**Prêt pour `/sprint-auto sprint_bois_arbres`.**
Source : `docs/rendu/splatting/backlog_splatting.md` (S2), `conception_reliquats_plantes.md` §2-3
(E3/E4 bois sans joint, rendu seul ; E9 brins/rubans des graminées en S2).
Golden attendu : `bce813af…` INTACT (vue + outillage, `data/code/` jamais modifié).

## Périmètre hérité (backlog)
1. Bois : tube lissé à travers les nœuds, fourches arrondies, aucun angle abrupt.
2. Écorce cuite en splats PAR ESSENCE, plaquée le long du tube.
3. Brins et rubans des graminées : même technique (ruban texturé).
4. Masses ×4 des arbres (gerbes) ; fleurs d'arbre ×4 clairsemées.
5. Portraits d'arbres : sapin (cône), bouleau (écorce blanche), cerisier (fleurs, cerises), figuier.

## Faits vérifiés au code (2026-11-25)
- Bois = `DrawSegments` (`PlantRenderer.cs:543`) → `DrawBranch` → `DrawEcorce`
  (`PlantRenderer.Motifs.cs:177`) : un `DrawLine` par segment, bouts carrés, 3 bandes
  (âme + 2 flancs orientés) + stries au hash. D'où les angles et les joints.
- Couleur d'écorce : `RecettesArbres` (`PlantRenderer.Arbres.cs:29`, 12 essences : pommier,
  cerisier, noyer, chêne, hêtre, bouleau, charme, noisetier, aulne, saule, figuier, sapin) ;
  `AvecEcorce` tire vers l'écorce avec l'épaisseur.
- Topologie : le pont transmet `parent` (`data/code/tools/simserver/segments_pont.py`), mais
  `core/PlantStructure.cs` `Segment` ne le lit pas → à ajouter à la lecture C# (vue seule).
- Sprint (a) ③ : couture mesurée — tronçons cuits bout à bout = joints visibles ; un cylindre
  d'un tenant = propre (`sprint_precuisson_splats/mesures/couture_bois.png`).
- Brins : `PoserBrin` (`PlantRenderer.Graminees.cs:44`) calcule déjà les bords gauche/droit
  point par point (triangles d'une couleur) → il ne manque que des coordonnées de texture.
- Pixels = CODES (palette + ton + orientation, `PaletteIndexee.cs`) ; une pièce reçoit sa
  palette par `ModulatePiece`. L'orientation d'un flanc de tube dépend de l'angle du segment
  à l'écran → une texture d'écorce ne peut pas porter une orientation fixe.

## Constat en image (captures VM 2026-11-25, n=1 par cas, hors dépôt : scratchpad de session)
- Pommier `verger_floraison` ×4/×8/×16 : tronc = pile de rectangles à largeur en MARCHES ; branches =
  bâtons droits ; une branche passe DEVANT le tronc alors qu'elle part derrière (tri par épaisseur
  `PlantRenderer.cs:552`, pas par profondeur) ; ×4 = touffes vertes en grappes, fleurs éparses.
- Sapin (`houppiers`) ×1/×4 : EN JEU aussi un poteau à touffes éparses, aucun cône (pas qu'au portrait).
- Charme ×16 : tronc = 3 bandes plates, bas carré, racines = triangles plats posés au sol.

## Référence PC de Nico (rapport C collé le 2026-11-25, n=1 run, `full` seed 42, an 2 s4, ×32, Turbo)
HD 4600 : FPS 23 [×32, turbo, charge 86-94 %] · frame 54,4 ms [moy. ~1 s] · 87 draw calls · 53 827 primitives ·
précuisson 599/1024 Mo (pages 272, planches 327) · 4 en repli · 11 évincées. Le bois cuit ne coûte
rien par image ; les plantes en REPLI (dessin direct) paient le tube → ① mesure le temps de pinceau
d'un arbre et le nombre de primitives d'un arbre en repli. Le rapport ne dit ni QUELLES plantes sont en
repli ni le temps de cuisson par plante → l'enrichir au ① (règle « rapport C »).

## Décisions arrêtées (par Claude, à confirmer avec le lot de questions)
- D-a Tri du bois par PROFONDEUR (iso), pas par épaisseur.
- D-b Brins/rubans des graminées = même primitive « ruban texturé » que le tube.
- D-c Orientation des flancs = géométrie du tube ; l'écorce cuite n'apporte que les TONS
  (mécanisme — shader de composition dans le pinceau ou variantes cuites par rotation — tranché
  par une maquette au ①).

## Arbitrages de Nico (2026-11-25)
- **B1 Lissage = (B)** : courbe interpolante passant par TOUS les nœuds du moteur ; une géométrie
  unique du bois (« point sur l'axe ») lue par rameaux dérivés, fruits, clic `manger`, sécateur,
  surbrillance, neige sur branche.
- **B2 Écorce cuite pour les 12 essences × 3 âges** (rameau lisse / branche / tronc à rhytidome),
  âge choisi par l'épaisseur du bois.
- **B3 Cône du sapin par la VUE** (étages de rameaux dérivés décroissants vers le haut) pour
  commencer ; moteur intact. Une vraie architecture de conifère au moteur reste une option future
  (non ouverte en dette).

## Décisions de Claude (dans le cadre)
- Primitive « ruban texturé » indépendante de PlantRenderer → resservira au décor de lisière (S3).
- Collet évasé (empattement) remplace les racines-triangles plates ; col de branche aux fourches.
- Fleurs d'arbre ×4 en bouquets cuits (plus une à une) ; masses ×4 : constater d'abord en été
  (les gerbes portent déjà les touffes splat depuis (a) ⑤).

## Carte des tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_axes_tube.md` — parent lu, axes, tube lissé, pied, cols, tri profondeur, géométrie unique, rapport C | à faire |
| ② | `02_ecorces.md` — maquette C3, écorces 12 essences × 3 âges, plaquage | à faire |
| ③ | `03_rubans.md` — brins/rubans des graminées, petit bois en tube | à faire |
| ④ | `04_arbres_x4.md` — bouquets de fleurs cuits ×4, masses constatées l'été | à faire |
| ⑤ | `05_sapin_portraits.md` — cône du sapin en jeu, portraits d'arbres | à faire |
| ⑥ | `06_revue.md` — revue des paliers, F5 consolidé S2, clôture | à faire |

## Règles du sprint
- Golden `bce813af…` INTACT à chaque tronçon ; build vert, 0 avertissement.
- Captures VM `tools/capture_vm.sh` lues au Read avant de conclure ; `uptime` avant toute mesure de temps.
- Poids `assets/splats/` mesuré à chaque tronçon (65 Mo au départ) ; alerte à 200 Mo.
- Interdits : `data/code/` (lecture seule), `test_epaisseur_500ans`, DeepSeek dans les sous-agents, `tools/splat/vendor/`.

## Compte rendu des tronçons
(rempli par chaque tronçon)

## §REPRISE
Lire `CLAUDE.md`, ce fichier, la conception, puis le kickoff du premier tronçon « à faire » (①).
