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
| ① | `01_axes_tube.md` — parent lu, axes, tube lissé, pied, cols, tri profondeur, géométrie unique, rapport C | **FAIT côté code 2026-11-26** (F5 attendu) |
| ② | `02_ecorces.md` — maquette C3, écorces 12 essences × 3 âges, plaquage | **FAIT côté code 2026-11-26** (F5 attendu) |
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

### ① Axes et tube lissé — FAIT côté code (2026-11-26), golden `bce813af…` intact, build 0 avert.
- **Parent lu** : `PontDelta.Pas` 10 → 11, `parent` rangé EN FIN (col. 10, `ColParent`) pour ne
  décaler aucun lecteur ; l'âge reste col. 9 (`ColAge`, la soustraction des semaines le vise
  nommément). `null` Python (collet) → −1 (Nil.AsDouble aurait donné 0). `Segment.Parent` (défaut −1)
  lu aussi par `ParseSegment`. `data/code/tests/simserver/delta.py` garde déjà `parent` : rien à faire.
- **Neufs** : `visuals/BoisAxes.cs` (axes, Catmull-Rom centripète, largeur continue, pied, cols,
  mémo `ConditionalWeakTable` par référence de structure, partagé avec le pinceau) ;
  `visuals/RubanTexture.cs` (primitive : normales en onglet borné, bandes [u0,u1] avec u/v, un
  `CanvasItemAddTriangleArray` par morceau) ; `visuals/PlantRenderer.Tube.cs` (tube vivant +
  squelette, tri par profondeur, tons de l'ancien `DrawEcorce`, stries, neige, clic, surbrillance).
- **Lecteurs migrés** sur `PointDuBois` / la courbe : rameaux dérivés (donc fruits et feuilles
  d'arbre), feuilles génériques (`PlaceFeuille`), bout tendre, `FindSegmentNear`, `BoisSous`,
  surbrillance, banc `MilieuSegmentCanvas`. Les nœuds étant SUR la courbe, les lecteurs de bouts
  (`FruitPoint`, vrilles, emprise) n'avaient pas à bouger.
- **Non migrés (hors périmètre, signalés)** : paliers bas ×0,5-×2 (`DrawTigesAssemblees`,
  `PlacerTouffes`, `Paliers.cs` : tiges de 1 px, droites) ; lianes ; ports à fiche ; petit bois
  dérivé (③). Racines-triangles coupées quand le tube est actif (halo gardé) ; ellipse au sol sous
  le tronc (sinon bas coupé à l'horizontale, vu en capture).
- **Interrupteur** : Maj+F11 / `SYMBIOSE_SPLATS=0` → ancien bois ET lecteurs droits (clés de mémo
  des rameaux/fruits incluent l'état de l'interrupteur).
- **Rapport C / F4** : `BudgetCuisson.Ligne()` liste les espèces en repli et la pire cuisson
  (« pinceau max X ms (espèce) », depuis le lancement).
- **Mesures** [VM llvmpipe, charge 9-11, n=1 cuisson par cas] : bois seul du charme (70 segments)
  3,3 / 5,1 / 6,7 / 10,3 ms à ×4/×8/×16/×32 (ancien : 0,5 / 0,8 / 1,2 / 3,0 ms) ; ≈ 2 850 triangles
  [×16-×32] ; cuisson complète du charme ×32 ≈ 1 014 ms [après] contre 992 ms [avant] → le bois
  pèse ≈ 1 % d'une cuisson. Première version 45 ms à ×16 (stries en `DrawPolyline` + `Ton` par quad)
  corrigée. Frame `full` ×8 avant/après NON mesurée (VM trop chargée pour un temps significatif).
- **Banc de taille** `-Y AppleTree` ×8 et ×16 : OK (70 → 69 segments, 0 feuillage déplacé).
- Captures : `mesures/01_*` (verger ×4/×8 avant/après, charme ×16 avant/après : plus de marches,
  pied ×8 évasé). Constat : tronc continu effilé, pied évasé arrondi, branches derrière le tronc
  passent derrière. Squelette : pas de banc prêt, à voir au F5.
- **Écarts au kickoff** : aucun bloquant. `PontDelta.Pas` = 11 avec `parent` en fin (et non en
  tête) ; `tests/simserver/delta.py` est sous `data/code/` (lecture seule, déjà correct).
- **F5 Nico** : tronc et charpentières sans marche ni coude (×4→×32) ; pied évasé (force 0,8 [choix])
  et cols ; branche arrière derrière le tronc ; squelette d'arbre mort ; taille : surbrillance qui
  suit la courbe, coupe là où l'on vise ; Maj+F11 avant/après ; rapport C : espèces en repli.

### ② Écorces cuites — FAIT côté code (2026-11-26), golden `bce813af…` intact, build 0 avert.
- **Choix C3 = (c) « bande de TONS posée par-dessus le modelé »** (ni (a) ni (b) tels quels) :
  (a) shader de composition RÉFUTÉ au code — un matériau est porté par le CanvasItem entier, pas
  par un appel de dessin ; le bois devrait quitter la liste de commandes de la plante (ordre de
  pose avec halo/organes cassé) et le repli littéral exigerait un 2ᵉ shader. (b) copies cuites
  par orientation ÉCARTÉE sur le poids : 9 copies (8 orientations + plat) × 2 moitiés (codes +
  littéral) ≈ 8 Mo par bande tronc ×32 [calcul, 376×400 texels], ≈ 100 Mo de VRAM pour 12
  essences à ×32 [calcul]. Retenu : la bande ne porte que des tons en orientation PLATE, le ton
  de base (2) est transparent → seules les marques (creux 0, ombre 1, pigment clair 3) se posent
  sur l'âme + flancs orientés de ① (le flanc soleil reste éclairé par la géométrie). 2 moitiés
  (codes / gris littéral × teinte d'éclat, comme `Motifs.cs`) → pinceau et repli par le même appel.
  Limite assumée : une marque ton 1 se fond dans un flanc à l'ombre (ton 1) ; les creux restent.
- **Outil** : `tools/splat/recettes/ecorce.js` (13 essences = 12 arbres + `Generique`, × 3 âges :
  rameau d 1,5 cm P 8 cm · branche d 6 P 16 · tronc d 20 P 32 ; 8 motifs : fissures, réseau de
  losanges, écailles en briques, lenticelles en pigment, rides, cannelures, poches de résine,
  taches) ; `tools/splat/cuire_ecorces.js` (photo de face, 1 texel = 1 px interne au palier ×4/
  ×8/×16/×32, largeur × 1,5 = WoodWidthFactor, cache + parallèle). `cuire.js` exporte sa palette.
- **Périodicité** : motifs posés en y0 − P, y0, y0 + P ; fût en 3 tronçons de longueur P ; pas
  du sculpteur = P/m, m pair. Couture MESURÉE (débord d'un quart comparé à l'octet) : 0,52 % de
  texels différents [7 848 / 1 521 000, 39 bandes × 4 paliers ; pire bande 8,3 %, une petite
  bande ×4] — non nulle (départage de splats à profondeur égale, supposé) ; invisible sur la
  planche (bandes répétées 2 fois).
- **Vue** : `visuals/Ecorces.cs` (chargeur : manifeste, planche du palier courant seule, texture
  codes/littéral) ; `visuals/PlantRenderer.Ecorce.cs` (âge par épaisseur : rameau < 3,5 cm <
  branche < 10 cm < tronc, fondus ±1 / ±2,5 cm par SUPERPOSITION des deux motifs, poids ≥ 0,25 ;
  phase au hash par axe × individu ; générique si lig ≥ 0,5 ; bois < 4 px internes : stries de
  ① gardées) ; `RubanTexture.PoserBandePeriodique` (quads COUPÉS aux frontières de période).
  `GrisTon` (Motifs.cs) passé `internal`. Neige, surbrillance : dessinées après (inchangées).
  Squelette : bois mort uni (inchangé).
- **Bug trouvé et corrigé en cours** : `planche.ranger` regroupe par palier → manifeste mal
  apparié (tronc lisait le rect d'une branche) ; tri par palier avant rangement.
- **Mesures** [VM llvmpipe, charge 10-16] : poids des 4 planches 0,30 Mo [somme 6+24+71+201 Ko] ;
  `assets/splats/` reste 65 Mo ; cuisson 39 bandes ≈ 8 min en 8 processus [tronc 11-88 s de
  sculpture, 310-390 k splats ; une bande tronc photo ×32 ≈ 20-30 s] ; déterminisme : 2 cuissons
  `CherryTree_branche` identiques à l'octet, assemblage identique (sha256). Coût par image :
  nul pour une plante cuite ; en repli, +1 appel de triangles par morceau (non chronométré).
- Captures : `mesures/controle_ecorces.png` (13 colonnes, 3 âges, ×16, 2 périodes), 
  `mesures/02_verger_x{8,16,32}_apres.png` (pommier : plaques lisibles sur le tronc, continues).
  Avant = `01_verger_x8_apres.png` (tube uni + stries). Écart : `houppiers` non capturé (pieds
  cachés par la maison/lisière aux points essayés ; la plupart des troncs y sont minces, D91) →
  les 11 autres essences ne sont vues qu'en planche.
- **Non vérifié séparément** : pinceau (codes) vs repli (littéral) — les captures montrent le
  repli (journal : `idx=False` sur le pommier) ; même chemin de code, seuls rect et modulate changent.
- **F5 Nico** : marques d'écorce sur pommier/charme ×8→×32 ; fondu rameau/branche/tronc sans
  marche ; bouleau (blanc, lenticelles noires, base noire) ; lecture côté soleil vs ombre ;
  neige/surbrillance par-dessus ; pinceau ET repli identiques ; Maj+F11.

## §REPRISE
② non commité au moment de l'écriture (l'orchestrateur commit). Lire `CLAUDE.md`, ce fichier, la
conception, puis le kickoff du premier tronçon « à faire ». ① et ② faits côté code. Prochain : ③ (`03_rubans.md`) — `RubanTexture.PoserBandePeriodique`
(bande périodique texturée, quads coupés aux frontières) est réutilisable pour les brins ; les
écorces se recuisent par `node tools/splat/cuire_ecorces.js` (cf. tools/splat/README.md).
