# Sprint VUE — rattrapage Godot des sprints moteur + packaging — état partagé

> **Kickoff autosuffisant** (démarrage à froid). Lire CE fichier puis le
> `0N_*.md` du sous-sprint courant suffit à reprendre. Suite directe du
> **sprint Intégration Godot** (tranches 1-6 closes) : on **rattrape la VUE**
> sur tout ce que le moteur a gagné depuis la tranche 6, puis on **clôt par le
> packaging** (tranche 7). **GDScript INTERDIT, tout en C#, namespace `Symbiose`.**

## En une phrase
Le moteur (Python, source de vérité) a beaucoup avancé depuis le dernier rendu
Godot : **écraser une plante, planter/arroser, compétition/étiolement,
décomposition & compost ①–⑤** (litière typée, squelettes, fruits traçables,
structures bac/pile). Le **pont JSON expose déjà presque tout (0.3.5)** ; ce
sprint fait **voir et déclencher** ces features dans Godot, **sans toucher la
logique du moteur** (golden intact), puis **gèle/exporte** le jeu pour les
amis/famille de Nico.

## Invariants ABSOLUS (toute la durée du sprint)
1. **Golden jamais re-figé.** `cd data/code && python3 -m tests.test_golden`
   reste vert, hash **`908f591bee…`** inchangé (population `435e6f72…`). Le
   moteur n'est PAS modifié : si la vue a besoin d'une donnée, on l'**expose en
   LECTURE** dans le snapshot (`tools/simserver/serialize.py`) — la sérialisation
   ne touche jamais le tick → golden neutre. Toute exposition nouvelle = +checks
   `tests/test_sim_server.py` + bump `ENGINE_VERSION`.
2. **Build C# vert** après chaque sous-sprint touchant le C#. **NOUVEAU
   depuis le refactor global** : `dotnet` SDK 8.0 est installé sur la VM →
   `export PATH="$HOME/.dotnet:$PATH" && dotnet build Symbiose.csproj` est le
   **filet de compilation**. Le **F5 visuel reste à Nico** (Godot pas sur la VM).
3. **~350 lignes de code pur max par fichier** (recalibré au refactor global ;
   `tools/compte_ldc.py`). Les fichiers `WorldView.*.cs` sont déjà des partials
   par concept — y ajouter du code en restant sous le seuil, ou créer un partial.
4. **Avant chaque sous-sprint : git à jour.** Un commit par sous-sprint, puis
   `/clear`. Rien jeté (Option B : Godot = vue, le moteur ne bouge pas).

## Conception actée (rappels du sprint Intégration — Option B)
- Python tourne en **sous-process** (`tools/sim_server.py`), émet le **snapshot
  JSON**, Godot **rend** et **renvoie les intentions joueur** (`SimBridge.Action`).
- **Python possède les règles** (validité, coût Vigueur) ; **Godot est bête** :
  il résout la désignation (plante/plot/tuile/fruit/structure) et transmet.
- Scène principale = `world/WorldView.tscn` (classe `WorldView`, partials par
  concept). Rendu plante = `visuals/PlantRenderer.cs` (+ `.Organs.cs`,
  `PlantShadow.cs`). Vie macro = `visuals/MacroLife.cs`. Heatmaps debug F6 =
  `visuals/FieldOverlay.cs`.

## Ce que le pont expose DÉJÀ (0.3.5) — vérifié dans `serialize.py`
- `plants[]` : `tile, species, name, x_cm, y_cm, stage, stage_name, height_cm,
  foliage_density, organ` (**proxy saisonnier** `REPRO_BY_SEASON`), `organ_site`,
  `segments` (structure), **`fruits[] {segment, maturite, masse}`** (vrai état ③).
- `sprites{}` : vie macro échantillonnée par guilde (déjà rendue par `MacroLife`).
- **`structures{}` par tuile** : `[{kind, plot, compost_mur}]` (⑤) — **exposé
  mais PAS encore rendu**.
- `player` : `vigueur, vigueur_max, seeds {clé: nombre}` (lots plantables).

## Les DEUX manques du snapshot (à exposer en lecture, golden neutre) — RÉSOLUS
- ✅ **Plantes mortes persistantes (squelettes)** : exposées en 02 (snapshot
  0.3.6, `dead` + `{stade_mort, bois_restant, semaines_mort}`).
- ✅ **Litière par plot** : exposée en 03·A (snapshot 0.3.7, `litiere[tile] =
  [[r, c, tissu_dominant, masse], …]`, liste creuse, `diffus` écarté).

## Ce que la VUE C# gère DÉJÀ (à étendre)
- Palette de **8 gestes** (touches 1..8, `WorldView.Actions.cs` tableau `Gestes`) :
  `recolter, deraciner, ecraser(plot/guilde), favoriser_auxiliaire, becher,
  grelinette, tailler, manger(plante entière)`.
- Picking plante (`FindPlant`/`FindSegmentGlobal`), plot (`FindPlot`), file
  d'UNE intention, flash de feedback, HUD Vigueur, étiquettes survol (F3).
- **Manquent** : `planter` (avec choix de graine depuis `player.seeds`),
  `arroser`, **`manger` ciblé sur un fruit** (`target.fruit`), **`ecraser` une
  PLANTE** (≠ le geste plot/guilde actuel), et les **6 gestes compost**
  (`poser_bac, poser_pile, composter, empiler_bois, retourner, epandre`).

## Carte des sous-sprints (4 — vertical slices, révisable)
| # | Sujet | Kickoff | Moteur ? | Golden | État |
|---|-------|---------|----------|--------|------|
| 01 | **Gestes joueur manquants** : planter (choix graine), arroser, écraser-plante — pur câblage C# (pont prêt) | `01_gestes_manquants.md` | non | neutre | ✅ |
| 02 | **Cycle de vie visible** : fruits réels (maturité vert→mûr→sur-mûr) + squelettes post-mortem + abscission. Snapshot expose les morts (lecture) | `02_fruits_squelettes.md` | snapshot RO | neutre | ✅ |
| 03 | **Sol vivant & compost** : litière au sol + structures bac/pile + jauge `compost_mur` + 6 gestes compost. Snapshot expose la litière (lecture) | `03_litiere_structures.md` | snapshot RO | neutre | ✅ (+ correctif F5 : composter le sol → bac proche, remplissage visible) |
| 04 | **Packaging (tranche 7)** : gel PyInstaller + export Godot — clôture avec Nico (poste Windows) | `04_packaging.md` | non | neutre | ⬜ (VM faite) |

> **Ordre** : 01→02→03 rattrapent la vue, **04 ferme** (le build distribué
> reflète alors la vue complète). 04 est en grande partie déjà fait sur la VM
> (cf. `sprints/sprint_integration_godot/07_packaging.md`) — reste le gel
> Windows + build + F5 final par Nico.

## Boucle de travail (rappel CLAUDE.md)
`0N` → coder → `dotnet build` vert (si C#) + golden inchangé → MAJ ce fichier →
commit → `/clear` → `0N+1`. Le F5 visuel de chaque sous-sprint = Nico ; sur son
retour, triage (correctif ou dette/sous-sprint indépendant, pas de dev immédiat).

## Pièges & rappels
- **Moteur intaillable** : toute nouvelle donnée pour la vue = champ de snapshot
  en lecture (jamais une branche dans le tick). Re-vérifier `908f591bee…` après
  CHAQUE ajout serialize.
- **Témoin de build** à incrémenter à chaque tronçon (piège sync Nextcloud déjà
  vécu : un build resté en arrière donne « rien ne s'affiche »).
- **Palette de gestes** : on passe de 8 à ~14 verbes → prévoir une sélection qui
  tient (catégories, ou liste HUD cliquable). HUD riche/encyclopédie = hors
  scope (sprints dédiés) ; viser le **minimal jouable** (cf. 01).
- **Attraction ④ + habitat pile = déjà visibles** via `MacroLife` (les sprites
  de guildes suivent les densités) — rien à rendre, juste à constater au F5.

## REPRISE (démarrage à froid)
**03 COMPLET + correctif F5 appliqué (build vert, 2026-06-16)** — la vue rend le
canal décompo·compost ET le correctif F5 (composter le sol → bac proche +
remplissage visible). **Reste un 2e F5 de confirmation** (cf. ci-dessous) puis
**04 packaging** = dernière tranche du sprint. Lire `04_packaging.md`.
État moteur de référence INCHANGÉ : golden `908f591bee…` / population `435e6f72…`,
pont **`ENGINE_VERSION 0.3.8`** (snapshot expose `contenu` des structures, RO),
`tests/test_sim_server.py` **158 checks** (+6 : section 13b remplissage du bac).
Le C# reste **pur rendu/câblage** (aucune touche moteur).

**À VÉRIFIER au 2e F5 (correctif F5 du 03)** :
- **composter / empiler = clic sur la LITIÈRE au sol** (comme tailler/cueillir),
  plus sur le bac. La vue route vers le **bac/pile le plus proche de la MÊME
  tuile**. Pas de bac dans la tuile → message « posez-en un ». retourner/épandre
  restent un clic sur la STRUCTURE.
- **Remplissage VISIBLE** : le bac/pile se remplit dès le compostage (`contenu`
  brut, avant maturation) et se vide à l'épandage (`compost_mur`). Saturation à
  `MasseRef = 6` (mesuré : un plot bien fourni ≈ 1-6 de litière) — si « toujours
  plein / toujours vide » au F5, ajuster CETTE seule constante (`CompostStructure.cs`).
- **Levier déterministe** : init full → litière déjà présente sur les plots ;
  poser un bac, sélectionner « composter » (Tab), cliquer un plot avec litière →
  la litière file dans le bac, qui se remplit. Épandre (clic bac) le vide.

**À VÉRIFIER au F5 de 03 (points soulevés en codant B/C/D)** :
- **LOD litière** : la litière n'apparaît qu'à partir du zoom ×2 (palier sous la
  vie macro ×4) — en vue d'ensemble on ne la voit pas (voulu, sobre). Réglable
  (`LitterLayer.MinZoom`). Lever déterministe : `deraciner` un pommier (config
  full) → litière `feuille` ocre sur son plot, visible en zoomant.
- **Calibrages à l'œil** : densité de litière (`LitterLayer.MasseRef = 2.5`) et
  remplissage des structures (`CompostStructure.MurRef = 6`) sont des références
  posées sans mesure (la masse d'une litière/jauge dépend du scénario) — à ajuster
  au F5 si « toujours plein » ou « toujours vide ».
- **Garde-fou phase NON posé** : poser/composter/empiler/épandre sont jouables en
  TOUTE phase (le serveur applique quelle que soit la phase). Le kickoff prévoyait
  un garde-fou « planification » mais « à confirmer au F5 » → laissé permissif
  pour ne pas frustrer. À trancher avec Nico.
- **Structure ↔ litière au MÊME plot** : `composter`/`empiler` ramassent la litière
  du plot OÙ est posée la structure (clic sur la structure). Composter une litière
  d'un plot voisin n'est pas câblé (design minimal du kickoff). À juger à l'usage.

**03·A (rappel, FAIT Python pur)** — snapshot expose la **litière** par tuile
(`litiere[tile] = [[r, c, tissu_dominant, masse], …]`, liste creuse, `diffus`
écarté). Pont **0.3.7**, module `tests/simserver/litiere.py` (section 15).
Détail des features moteur rendues : `sprints/sprint_decomposition_compost/00_etat.md`
(§Acquis ①–⑤) + `docs/conception/CONCEPTION_DECOMPOSITION_COMPOST.md`.

**02 (rappel) : CODÉ, build vert, EN ATTENTE F5 Nico** — fruits réels + squelettes
post-mortem + `manger` ciblé. Snapshot 0.3.6 (les morts). Points à vérifier au F5
ci-dessous.

**À VÉRIFIER au F5 (points soulevés en codant 02)** :
- **Annuelles sans squelette** : le récit du kickoff (« une annuelle qui meurt
  laisse une silhouette sèche ») ne correspond PAS au moteur — seules les vivaces
  LIGNEUSES (`age_curve`, p.ex. AppleTree) laissent un squelette persistant ; les
  herbacées (bois=0) sont retirées au tick même de leur mort, jamais vues. Pour
  voir un squelette au F5 : **déraciner un pommier** (mort immédiate + bois) ou
  attendre une sénescence ligneuse (test long). Pas un bug, design moteur ②B.
- **Fruits proxy perdus pour les non-fruitiers** : les fruits basculent sur
  l'état moteur réel (kickoff Partie B) → une espèce SANS nouaison moteur (tomate,
  herbacées) ne montre plus de fruit décoratif d'été/automne. Les FLEURS restent
  sur le proxy. Voir des fruits = espèce `fruitier` (pommier) à `maturity_years`.
- **« couchée » = aplatissement d'affichage** (z×0.18) : le moteur ne ré-oriente
  pas les segments d'un squelette (flag seul) — première lecture « à terre », à
  juger au F5 (peut demander un meilleur rendu en dette si peu lisible).

## Journal de bord (rempli en fin de sous-sprint)
- **03 correctif F5 (2026-06-16, retour F5 Nico)** — deux réserves levées, moteur
  intact (golden `908f591bee…`). **(1) Composter le sol** : le moteur acceptait
  DÉJÀ `composter(eco, r, c, struct)` avec `(r,c)` = plot de litière indépendant du
  plot du bac ; seul le câblage C# forçait le plot du bac. Le `case 's'`
  (`WorldView.Actions.cs`) route maintenant composter/empiler comme un **clic sur la
  litière** → `FindNearestStructure(kind, tile, r, c)` (nouvelle méthode,
  `WorldView.Compost.cs`, distance Manhattan en plots) achemine vers le bac/pile le
  plus proche de la tuile ; retourner/épandre restent un clic sur la structure.
  **(2) Remplissage visible** : le rendu ne lisait que `compost_mur` (mûr, lent) →
  bac vide juste après compostage. Snapshot **0.3.7 → 0.3.8** : `serialize.py`
  expose `contenu` (Σ masse brute des parcelles, RO, golden NEUTRE) ;
  `CompostStructure.cs` remplit ∝ **`contenu + compost_mur`** (`MurRef`→`MasseRef=6`,
  calibré sur la mesure : un plot fourni ≈ 1-6). Tests : section **13b**
  (`structures.py`, +6 checks) composte une litière d'un AUTRE plot → bac `contenu>0`,
  `compost_mur==0` (pas de maturation sans step), litière source ramassée.
  **152 → 158 checks**. Build vert (0 warning), LDC max 326 (Actions.cs) < 350.
  Témoin « vue·rattrapage 03 correctif F5 ». **2e F5 Nico** : cf. §REPRISE.
- **03·B/C/D (2026-06-16)** — sol vivant & compost RENDU (C# pur, moteur intact,
  golden `908f591bee…` inchangé). **B litière** : nouveau layer batché
  `visuals/LitterLayer.cs` (patron MacroLife — UN CanvasItem, re-projeté au _Draw,
  LOD ×2, culling) ; amas semi-transparents jitterés par hash (philo #3) au plot,
  couleur par tissu dominant (feuille ocre, fleur rosé, herbacé paille, fruit
  rouille, bois brun), densité/alpha ∝ masse. **C structures** : nouveau nœud
  `visuals/CompostStructure.cs` (un par structure, dans la couche YSort `_objects`
  → occlusion correcte avec les plantes) ; bac = caisse iso ouverte remplie de
  compost ∝ jauge, pile = tas de rondins sur assise d'humus ∝ jauge ; empreinte
  tourne avec la vue (WorldToScreenOffset), hauteur en vertical écran. Diff = pleine
  reconstruction par snapshot (peu nombreuses, jauge change, pas de fondu). **D
  gestes** : palette 9 → **15** (les 6 compost via Tab) ; 2 kinds neufs dans
  TryAction — `q` (poser_bac/poser_pile → plot {tile,r,c}, planification) et `s`
  (composter/empiler_bois/retourner/épandre → structure du plot cliqué via
  `target.structure` index-dans-la-tuile + {r,c} sauf retourner ; épandre omet
  params.q ⇒ tout le dispo). Câblage `world/WorldView.Compost.cs` (ApplyLitiere/
  ApplyStructures/FindStructureIndex) ; `_structs.Clear()` ajouté à RebuildWorld.
  Build vert (0 warning), LDC max 308 (Actions.cs) < 350, sim_server **152/152**.
  Témoin bumpé « vue·rattrapage 03 ». **F5 Nico** + réserves : cf. §REPRISE.
- **03·A (2026-06-16)** — litière exposée au snapshot (Python pur, lecture seule,
  golden NEUTRE). `serialize.py` ajoute `litiere[tile] = [[r, c, tissu_dominant,
  masse], …]` dans la boucle des tuiles (à côté de `sprites`/`structures`) : par
  plot, on filtre les parcelles de SURFACE (`tissu != "diffus" && masse > 0`),
  `tissu_dominant` = parcelle de plus grande masse, `masse` = Σ de surface arrondie
  (4 déc., déterministe) ; plots vides OMIS (liste creuse). La parcelle `diffus`
  (exsudats/humus permanent) est écartée car non rendue. Pont **0.3.6 → 0.3.7**
  (`version.py` + historique). Nouveau module `tests/simserver/litiere.py`
  (section 15, **12 checks**) : levier déterministe = `deraciner` un pommier (config
  full) → `deposer_mort` dépose une litière `feuille` sur son plot-foyer ; on vérifie
  litière vide au départ, apparition ciblée au bon plot, format compact, omission des
  plots vides, déterminisme byte-à-byte. Un check adapté : `structures.py`
  (engine_version 0.3.6 → 0.3.7). **140 → 152 checks** (+12). Golden `908f591bee…`
  inchangé. **Reste 03·B/C/D (C#)** : rendu litière + structures + 6 gestes (cf.
  REPRISE). Partie A seule = pas de build C# / témoin de vue à toucher.
- **02 (2026-06-16)** — cycle de vie visible. **Partie A (Python, lecture seule,
  golden NEUTRE)** : `serialize.py` n'ignore plus les morts — chaque plante porte
  `dead` (false/true) ; un squelette expose `{stade_mort, bois_restant,
  semaines_mort}` + sa structure. Pont **0.3.6** (`version.py`). Nouveau module de
  test `tests/simserver/morts.py` (section 14) : levier déterministe = `deraciner`
  un pommier (ligneux) → squelette `seche`, bois>0, byte-identique en rejeu. Deux
  tests adaptés au changement : `actions.py` (un déraciné ne « disparaît » plus, il
  passe squelette — l'ancien snapshot le MASQUAIT) et `structures.py` (engine_version
  0.3.6). **123 → 136 checks** (+11 morts, +2 adaptés). Golden `908f591bee…` inchangé.
  **Partie B (C#)** : `PlantStructure.Fruits` (miroir `FruitData`), rendu fruits
  depuis l'état moteur réel (`PlantRenderer.Organs.cs` : `DrawFruits`, couleur
  vert→mûr→brun via `FruitColor`/`MaturiteChute=1.3`, taille ∝ masse) ; les fleurs
  restent sur le proxy saisonnier. **Partie C** : `manger` (kind `p`) ajoute
  `target.fruit = FindFruitNear(clic)` si la plante porte des fruits. **Partie D** :
  `PlantRenderer` mode squelette (`SetSkeleton`/`DrawSkeleton`, bois mort gris-brun,
  aplati si couchée), câblé dans `WorldView.Snapshot.cs` (lecture `dead`). Build C#
  vert (0 warning), tous fichiers < 350 LDC (max 272, Actions.cs), témoin bumpé
  « vue·rattrapage 02 ». **F5 Nico** : (a) déraciner un pommier → silhouette sèche
  grise ; (b) un fruitier mûr (pommier à `maturity_years`, scénario long/saisons)
  montre des fruits qui verdissent→mûrissent→brunissent ; (c) `manger` un fruit →
  il disparaît, gain ∝ maturité. Réserves notées en §REPRISE.
- **02b (2026-06-16, retour F5 Nico : A+B validés, C trop long)** — levier démo :
  le handler `init` config **"full"** pré-vieillit le(s) fruitier(s) à
  `maturity_years` (`commands.py`) → le pommier NOUE des fruits dès l'**été de
  l'an 1** (semaine 14) au lieu de l'an 6, **plus besoin de Turbo 5 ans pour le
  Bloc C**. main.py (démo 500 ans) et golden smoke intacts (lever en config full
  seulement). Monde toujours 53 plantes (on vieillit, on n'ajoute pas), pont
  inchangé (réglage d'init, pas de champ neuf → pas de bump). Test
  `morts.test_pommier_fruite` (section 14b) garde le levier + le chemin nouaison→
  `plant.fruits`→snapshot. **140/140**, golden `908f591bee…` inchangé. NB : la
  structure procédurale reste petite au 1er été (≈13 sem de croissance) → peu de
  fruits d'abord, davantage les étés suivants quand le branchage s'étoffe.
- **01 (2026-06-16)** — planter / arroser / écraser-plante câblés (pur C#, moteur
  intact). Palette portée de 8 à **11 gestes** ; touches 1..8 directes + **[ ]**
  cyclent toute la palette (scale pour les 6 gestes compost de 03), **S** cycle
  l'espèce à planter (depuis `player.seeds`). **Correction protocole** : le
  kickoff annonçait `target = {tile, r, c}` pour planter/arroser, mais le serveur
  réel (0.3.3, `actions.py:137`) attend un **point continu `{tile, x_cm, y_cm}`
  local** qu'il résout en plot via `_plot_at` → nouveau kind `'m'` (point milieu)
  côté vue. Écraser-plante = nouvelle entrée kind `'p'` (picking plante existant,
  sans `guilde` → routé sur la plante) avec urgence préparation/réaction. Garde-
  fou taille : tous fichiers `WorldView.*.cs` restent sous ~350 LDC. Build vert,
  golden `908f591bee…` inchangé, témoin de build bumpé. **F5 Nico** : (a) cycler
  une graine (S) et planter sur un plot ; (b) arroser en Pause vs Saison (coût
  ×1.5) ; (c) écraser une plante (déformée/écimée/meurt selon l'espèce).
- **01b (2026-06-16, retour F5)** — planter/arroser étaient inatteignables (gestes
  9-10, seulement via `[ ]` en position US sur AZERTY). Refonte ergonomie :
  **Tab cycle toute la palette** (une touche, remplace `[ ]`), chiffres **1..9**
  en direct. Palette **fusionnée à 9 gestes** : « écraser » = plante si sous le
  curseur sinon nuisible (le serveur route déjà par forme de cible) ; « ameublir »
  = bêcher (clic, plot) / **Maj+clic = grelinette** (global). Légende : ligne
  toggles triée par position AZERTY (F3·F4·H·F6·I·O·M), énumération des gestes
  retirée (débordait) + **AutowrapMode** de sécurité, le HUD montre le geste
  courant. Build vert, golden `908f591bee…` inchangé.
- **01c (2026-06-16, retour F5)** — kit de démarrage banque-joueur (1 tournesol +
  1 tomate + 1 basilic) pour tester `planter` sans attendre un automne. Réservé à
  la config **`full`** (monde du F5) ; `smoke` reste à banque vide → le flux
  empty→récolte de `tests/simserver/planter.py` est intact. Golden inchangé,
  sim_server **123/123**, pas de bump `ENGINE_VERSION` (aucun champ nouveau).
