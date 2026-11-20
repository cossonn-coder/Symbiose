# sprint_precuisson_splats — état du sprint

**Conception FIGÉE le 2026-11-20** (`/conception`, Nico : « vas-y ») →
`docs/rendu/splatting/conception_precuisson_splats.md`. Sprint (a) « plantes » du
programme « tout en splats » (D7). **Prêt pour `/sprint-auto sprint_precuisson_splats`.**
Golden : **INTACT à tous les tronçons** (vue + outillage, `data/code/` jamais touché).

## Carte des tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_atelier_cuisson.md` — outil `tools/splat/` + feuille composée, format palette indexée, tous paliers, mesures — **PORTE DE DÉCISION** | **fait 2026-11-20 — porte PASSÉE avec réserves** (cf. compte rendu) |
| ② | `02_feuilles.md` — bibliothèque des feuilles (formes, variantes, vues, trous D5) | **fait 2026-11-20** (non commité) |
| ③ | `03_tetes_fruits_bois.md` — têtes, fleurs, fruits, bourgeons, bois (couture mesurée) | à faire |
| ④ | `04_vue_paliers_hauts.md` — vue ×4 → ×32 | à faire |
| ⑤ | `05_vue_paliers_bas.md` — vue ×0,5 → ×2 (kit) | à faire |
| ⑥ | `06_portraits.md` — 162 portraits | à faire |
| ⑦ | `07_vue_encyclopedie.md` — encyclopédie + magazine, clôture | à faire |

## Règles du sprint
- Si la porte du ① échoue (pièce illisible à 3-9 px, ou ton/orientation non
  extractibles) : **arrêt**, retour en `/conception`.
- Poids (D2) mesuré à chaque tronçon ; alerte et arrêt si les pièces dépassent ~200 Mo.
- Capture VM sans écran pour voir avant le F5 : `tools/capture_vm.sh` (Godot + Xvfb
  sous `~/opt`, cf. `tools/lib_vm_godot.sh`).
- Interdits : `test_epaisseur_500ans` ; DeepSeek dans les sous-agents (protocole) ;
  modifier les sources copiées d'ink-studio.

## Compte rendu des tronçons
(rempli par chaque tronçon : fait, mesures, chemins des planches et captures)

### ① Atelier de cuisson (2026-11-20) — PORTE PASSÉE avec réserves
**Fait.** ink-studio copié dans `tools/splat/vendor/ink/` (commit `fb94031…`, MIT,
11 Mo, 1 004 fichiers ; provenance dans `tools/splat/README.md`) ; `tools/splat/.gdignore`
(Godot n'importe pas le dossier). Outil JS : `cuire.js` (orchestration),
`lib/iso.js` (caméra), `lib/codes.js` (passes → codes), `lib/planche.js`,
`lib/controle.js`, `mesurer_vues.js`, recette `recettes/feuille_composee.js`
(fonction `feuille` du prototype). Sorties : `assets/splats/feuille_composee_x{0_5,1,2,4,8,16,32}.png`
+ `feuille_composee.json` ; contrôle `mesures/controle_feuille_composee.png`
(rampe 5 tons + soleil fixe haut-gauche, règle exacte du shader ; en bas, la rangée
« Composee » du kit actuel capturée par `capture_vm.sh -k`, agrandie ×10).
**Format = atlas du kit existant** : R = niveau (littéral F11 OFF), G = `128|ton<<4|orient`,
A = posé. Manifeste : palier, inclinaison, variante, lacet, planche, rect, attache.

**Mesures [VM, n=1 cuisson complète, charge ~1].**
- Sculpture+bake d'une forme : ~0,18 s. Photo d'une pièce : 84 ms (×0,5) · 130 (×1) ·
  305 (×2) · 277 (×4) · 267 (×8) · 853 (×16) · 3 140 (×32). Recette entière
  (504 pièces = 7 paliers × 8 lacets × 3 inclinaisons × 3 variantes) : **6 min 08 s**.
- Poids : planches 0,84 Mo (dont ×32 469 Ko, ×16 178 Ko) + manifeste 100 Ko ;
  contrôle 227 Ko ; vendor 11 Mo. Extrapolation ~15 feuilles + ③ ≈ 30-60 Mo [estimation, pas mesurée].
- Déterminisme : 2 cuissons complètes → sha256 IDENTIQUES sur les 8 fichiers + le contrôle.
- **V retenu = 8 lacets × 3 inclinaisons (−30°, 0°, +30°)**. Mesure (`mesurer_vues.js`,
  1 − IoU des silhouettes recalées sur l'attache, 96 photos/tour) : AUCUN coude —
  le saut entre vues voisines décroît linéairement (×4 : V=4 0,97 · V=8 0,81 · V=12 0,66
  · V=16 0,58 · V=24 0,49 ; mêmes valeurs ×0,5 → ×16). Inclinaison ±15° ≈ 0,6,
  ±30° ≈ 0,83 (≈ le pas de 45° en lacet). Donc « aucun saut visible quand l'organe
  tourne » n'est atteignable par AUCUN V aux paliers ≥ ×4 (une feuille fine qui
  tourne de 15° change de silhouette à 50 %). V=8 choisi parce que : multiple de 4
  (rotation D35 = vues exactes), même pas que la quantification des orientations
  (45°), poids ÷2 vs 16. **Conséquence pour ④** : choisir la vue sur l'azimut AU
  REPOS de l'organe (pas sur la pose de vent), sinon une feuille proche d'une
  frontière clignotera entre deux vues.
- **Lisibilité (regardée au Read, contrôle + comparaison au kit)** :
  ×0,5 (2-5 px) = une MARQUE orientée (tiret clair/sombre), pas une forme — ni
  plus ni moins lisible que la touffe 3 px du kit actuel ; ×1 (~8×4 px) = rameau
  de folioles orienté, lisible comme feuillage ; ×2 (~15×8) = feuille composée
  reconnaissable ; ×4 → ×32 = nettement plus riche que le kit (folioles,
  rachis, revers sombres). Réserves : pièces plus CLAIRES que le kit (une feuille
  couchée regarde « en haut » → +1/+2 ton dès que le soleil est haut ; le kit
  dôme répartit ses normales sur 8 directions) et sans contour sombre → contraste
  moindre sur sol ; à juger au F5 (⑤), réglable par `TON_DE` dans `cuire.js`.

**Écarts au kickoff (hypothèses réfutées / corrigées).**
1. Échelle : CLAUDE.md dit 78×39 px/plot ; le code dit **39×19,5 px INTERNES**
   (SubViewport ×2) → 0,39 px/cm × palier. Pièces calées sur les px internes.
2. La vue est une projection OBLIQUE (verticales à l'échelle du sol), une caméra
   ortho ne la reproduit pas : tangage 30° + lacet 45° = sol exact, verticales
   **+22 %**. Accepté (< 1 px jusqu'à ×4 sur une feuille) ; l'ORIENTATION, elle,
   est projetée par la vraie projection oblique (comme `PaletteIndexee.MajSoleil`).
3. Lire le splat propriétaire pixel par pixel = bruit poivre-et-sel illisible aux
   paliers bas : ajout d'un **suréchantillonnage** (×4 jusqu'à ×2, ×2 à ×4, ×1 dès
   ×8) puis moyenne normale/ton par pixel. C'est la « réduction » de D4, pas un
   contournement.
4. Ton : cuisson sans soleil (`sunK=0`, ambiant 0,75 + ciel 0,25 → revers ×0,75),
   10 crans de gris → tons 0/1/2 (seuils 0,2 / 0,5). Tons 3-4 jamais cuits (shader).
   Seuil « plat » = 0,3 (FacePlate du kit, ~17,5° face caméra).
5. Les pièces vont dans `assets/splats/` (une planche PAR PALIER : chargement ×16/×32
   à la demande possible au ④).

### ② Bibliothèque des feuilles (2026-11-20) — FAIT
**Fait.** 18 recettes de feuille + 6 touffes, toutes cuites dans `assets/splats/`
(une planche par palier, `<recette>_kit.png` pour les touffes, un manifeste par recette).
Briques nouvelles : `tools/splat/lib/limbe.js` (limbe en volume depuis un contour 2D
de la vue : 2 moitiés en coussin `S.puff` relevées en V autour de la nervure, pétiole,
gaufrage), `lib/feuille.js` (fabrique fiche → recette), `lib/trous.js` (trous D5 =
solides négatifs `{ neg: true }`), `recettes/touffe.js` (+ 6 `touffe_<forme>.js`),
`controle_feuilles.js` (planche de toute la bibliothèque, relue sur disque).
`cuire.js` : axes `trous`, `tailles` (+ `empriseCm`), lacets/inclinaisons propres à
la recette, défaut d'inclinaisons = −30,0,30 ; `planche.js` groupe par nom de planche.
Non-régression : `feuille_composee` recuite → pièces saines IDENTIQUES à l'octet
(×0,5-×8 inchangées, entrées saines du manifeste égales ; ×16/×32 : pièces trouées
ajoutées APRÈS les saines).

**Table « nom vue → recette »** (aussi dans le champ `vue` de chaque manifeste) :
Ovale + `LeafShape.Elliptique` → `feuille_ovale` · Lanceolee + `LeafShape.Lanceolee`
→ `feuille_lanceolee` · Coeur + `LeafShape.Cordee` → `feuille_coeur` · Composee +
`LeafShape.Composee` → `feuille_composee` · Paume + `LeafShape.Lobee` (palmilobée :
courge, figuier, vigne) → `feuille_paume` · `FormeFeuille.Lobee` (lobes PENNÉS :
chêne, moutarde) → `feuille_lobee` — **même mot, deux formes** : `LeafShape.Lobee`
couvre aussi chêne et moutarde (Leaf.cs) ; au ④ de choisir par espèce · Dentee →
`feuille_dentee` · Spatule → `feuille_spatule` · Scie → `feuille_scie` · Lierre →
`feuille_lierre` · Ruban → `feuille_ruban` · Cuillere → `feuille_cuillere` · Plume →
`feuille_plume` · Palmee → `feuille_palmee` · Triade → `feuille_triade` ·
`LeafShape.Aciculaire` → `feuille_aiguille` (absente de `FormeFeuille`) ·
Scie/Lanceolee + `Gaufre` → `feuille_scie_gaufree` / `feuille_lanceolee_gaufree` ·
kit `KitTouffe(LeafShape, 3|5|7|9, v)` → `touffe_<forme>` (planche `kit`, `taille_px`).
Contours RECOPIÉS de la vue (ContourDente, Spatule, Lobe, Ovale, Coeur, Scie, Lierre,
Paume, ProfilLanceole) ; dispositions de PoserPlume/Palmee/Triade/Cuillere.

**Marques.** Cuites (relief) : `Pli` (gouttière en V de 0,5 rad, dans TOUS les rubans),
`Gaufre` (sillons négatifs le long des nervures secondaires, 2 recettes `_gaufree` ;
tomate : la composée garde sa forme du prototype, pas de version gaufrée). Laissées à
la vue (couleur / brillance) : `Duvet`, `Gouttes`, `Eclat`, `Revers` (dessous argenté =
palette ; le revers en volume, lui, est déjà cuit via les inclinaisons), `Nervures`
(lierre : nervures PÂLES, couleur, à plat).

**Trous (D5).** Morsure (bord, degrés 1 = 1 bouchée, 2 = 3) et grêle (criblage,
1 = 3 trous, 2 = 7, grêlon ≤ 1 cm) ; aux seuls ×16 et ×32 (PaliersHauts.cs), les
encoches de grêle de Froid.cs sont servies par les morsures. **Décision : trous sur
la variante 0 seulement** (`TROUS_VARIANTES` = 1 dans cuire.js) — ×3 sur les
variantes = +~20 min CPU et ~×3 de poids troué par recette ; réversible. Pas de trous
sur aiguille ni plume (rien à cribler, la vue n'en dessine pas). Manifeste : `trou`,
`degre`.

**Mesures [VM, n=1 cuisson complète, 12 processus parallèles, charge ~13].**
- 24 recettes, **11 520 pièces** (dont 2 880 trouées, 72 touffes ; 223 vides : aiguille
  et cuillère aux paliers bas, quelques vues de profil à ×0,5).
- Temps : **48 min 44 s** mur, 288 min CPU ; une recette va de 39 s (aiguille) à 49 min
  (paume, rayon 29 cm : ×32 ≈ 10 s/photo en charge).
- **Poids** : `assets/splats/` = **14,8 Mo** (planches 12,3 + manifestes 2,5), soit
  +13,9 Mo au ② ; contrôles `mesures/` +1,8 Mo. Loin de l'alerte 200 Mo.
- Déterminisme : composée recuite = octets identiques au ① (pièces saines).

**Contrôles** (lus au Read) : `mesures/controle_feuilles.png` (toute la bibliothèque :
×1 + 8 lacets ×8, puis ×16 saine + 4 degrés de trous ; touffes en bas) et
`mesures/controle_<recette>.png` (toutes vues). Lecture : toutes les formes se
distinguent dès ×8, le pli en V donne deux faces (ombre/lumière) très lisibles, les
trous se lisent à ×16. Les touffes donnent des taches orientées variées (leurs feuilles
montent de 0 à ~50°) ; mêmes réserves qu'au ① (plus claires que le kit, sans contour).

**Points pour la suite.**
- **TAILLE** (④ ⑤) : une feuille est cuite à UNE longueur nominale par forme
  (ovale 9 cm, dentée 15, ruban 30, paume 20 + 6 de pétiole…, cf. `longCm` des
  recettes) ; la vue a des feuilles de 2 à 30 cm selon espèce et stade. Pas de mise à
  l'échelle (zooms entiers) → le ④ devra choisir : accepter la taille nominale, ou
  demander une classe de taille de plus (×2 pièces/poids) — décision à remonter.
- Largeurs (`large`) fixées par forme (médiane des fiches) : une seule géométrie sert
  des espèces plus ou moins larges.
- Le kit des touffes a la largeur de la taille demandée (±1 px) mais une hauteur
  ~moitié (vue iso), là où le kit actuel est carré : à juger au ⑤.

## F5 (recette pour Nico — complétée par ④⑤⑦)
(à écrire)

# Carnet de conception (historique)

## Contexte
- Prototype tomate validé par Nico (« c'est ça que je veux pour Symbiose ») :
  `docs/rendu/splatting/prototype/` (ink-studio CPU sur la VM, 106 000 splats,
  cuisson 17 s [n=1 plant, VM]).
- Refonte 3D temps réel = horizon (mémoire `project_refonte_splatting`) ; PC de Nico
  en cours d'achat, budget serré : carte 8 Go probable, 16 Go de RAM.
- Ce sprint = amener le rendu splat DANS la vue actuelle (iso 2D) par PRÉCUISSON
  hors ligne (images produites sur la VM, affichées par Godot).

## Faits vérifiés (code)
- Vue : cuisson EN JEU par plante (`visuals/PlantBaker.cs`, atlas de poses de vent
  ≤ 8, pages communes `AtlasPages`) depuis un dessin vectoriel ; paliers bas
  ×0,5-×2 = « plante assemblée » : vrais segments + TOUFFES du kit
  (`PlantRenderer.Kit.cs`, 3-9 px, codes de palette indexée ton + orientation de
  face lus par shader, lumière côté soleil réel).
- Moteur : la tomate n'est qu'une tige droite (port inventé côté vue).
- Catalogue : 54 espèces [classes distinctes des 5 tables de `plants/catalogue.py`].
- ink-studio : export `atlas --directions N --maps depth,normal,...` (cartes de
  normales → codes d'orientation de face possibles).

## Décisions arrêtées
- **D1 (Nico 2026-11-20) fidélité MAX au moteur dans le jardin** : la plante en jeu
  suit ses vrais segments (taille au segment, phototropisme, vent, santé, rotation
  D35). → plantes entières précuites (A) EXCLUES en jeu ; reste B (kit d'organes
  précuits assemblé sur les segments) ou C (B + portraits entiers hors jeu).
- **D2 (Nico 2026-11-20) images versionnées dans git** (git = seul canal
  VM→Windows) avec les recettes. Place disque côté Nico non limitante (30 Go libres
  sur le PC actuel). Garde-fou retenu : poids du dépôt mesuré à chaque tronçon,
  alerte si le kit dépasse ~200 Mo (croissance de l'historique à chaque
  régénération, pas le disque) ; régénérer seulement ce qui a changé.

- **D3 (Nico 2026-11-20) option C** : kit d'organes précuits en splats assemblé
  sur les vrais segments DANS le jardin + PORTRAITS entiers (façon prototype
  tomate) pour encyclopédie / magazine / carnet (hors jeu, sans contrainte de
  fidélité segment par segment).

- **D4 (Nico 2026-11-20) TOUS les zooms en splats** (×0,5 → ×32) : le kit pixel
  des paliers bas (touffes 3-9 px, fleurons) est lui aussi généré depuis les
  recettes splat (réduction + quantification), plus de pièce dessinée à la règle.
  « Tous les graphismes » : périmètre au-delà des plantes → lot 3.
- **D5 (Nico) symptômes ×16** : TROUS (morsures, criblage de grêle) = variantes
  précuites de chaque feuille, 2-3 degrés ; COULEURS (nécrose, taches, givre) =
  palette / peint par-dessus, comme aujourd'hui.
- **D6 (Nico) portraits** : 3 par espèce (jeune · mûre en pleine saison · fin de
  cycle / hiver), dévoilés avec les 3 niveaux de fiche de l'encyclopédie ; le
  magazine montre le portrait mûr.

- **D7 (Nico 2026-11-20) programme « tout en splats »**, un sprint par famille,
  F5 entre chaque : (a) plantes [CE sprint] → (b) décor de lisière → (c) faune +
  champignons → (d) structures + maison → (e) sol, litière, eau, neige, météo →
  (f) icônes. Les sprints (b)-(f) sont à concevoir après le F5 de (a).
- **D8 (Nico) icônes de gestes = petits objets en splats** (trois quarts), sous
  réserve d'un F5 de lisibilité avant de remplacer les icônes actuelles (sprint f).

## Faits vérifiés (lot 2)
- Grammaire de la vue (`PlantRenderer.PortsFiches.cs`) : 7 ports (Rosette, Tige,
  Chaume, Tapis, Buisson, Rampante, Volubile) + arbres (Houppier/Arbres), 15 formes
  de feuille, 14 formes de tête (inflorescences), 8 marques. → bibliothèque de
  recettes = ce vocabulaire, PAS 54 recettes d'espèce.
- Paliers hauts (`PaliersHauts.cs`) : ×4 masses de feuillage + points ; ×8 organes
  (forme de feuille, fleur par famille, fruit globe) ; ×16 symptômes (morsures,
  grêle, nécrose, taches, givre) ; ×32 intime (nervures 2ᵉ, étamines, poils).
- Palette indexée (`visuals/PaletteIndexee.cs:14`) : pixel = n° de palette (R,G) +
  B = 128 | ton(0-4) << 4 | orientation(0-7 écran, 8 plat). Une pièce splat peut
  s'y couler : ton = volume (creux/ombre/base/clair), orientation = normale
  quantifiée (carte de normales ink-studio), palette posée à l'assemblage → UNE
  géométrie de feuille sert toutes les teintes (espèce, saison, santé, maturité).
- Panneaux existants : `world/EncyclopediePanel.cs`, `MagazinePanel.cs`,
  `CarnetPanel.cs`.

## §REPRISE
Lire `CLAUDE.md`, ce fichier, la conception, puis le kickoff du premier tronçon
« à faire » de la carte. ① et ② faits (non commités par les sous-agents). Prochain :
③ (`03_tetes_fruits_bois.md`) — réutiliser `cuire.js` + `lib/feuille.js` (fabrique
`recette`) ; les têtes/fruits n'ont PAS de trous (ne pas poser `trous`). Cuire toute
une famille en parallèle : commande dans `tools/splat/README.md`. Golden `bce813af…`
intact.
