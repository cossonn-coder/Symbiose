# Sprint MARE VIVANTE (D121) — état partagé

**Conception FIGÉE le 2026-10-30** en conversation (F5 de Nico sur SOL NOURRICIER ;
Nico : « oui pour tes recommandations et en hiver la mare est couverte de glace »).
Dette : `DETTE.md` D121. Golden de départ **`4c696821…`** (`cd data/code && python3 -m
tests.test_golden`) : **INCHANGÉ sur les 3 tronçons** (aucun re-figeage prévu). Filet
C# : `dotnet build Symbiose.csproj`. Pont de départ **0.6.1**.

## Constats de départ (vérifiés au code / mesurés le 2026-10-30)
- La mare (sprint SOL NOURRICIER ④) : `sim/mare_initiale.py`, fond 3×3 `MARE_FOND`
  (lignes 7..9, colonnes 4..6 de la tuile NE), alimentée par `fields/ecofields/source.py`.
  Centre en eau 104/104 sem. [seeds 42/1/2, n=3] ; bords du fond oscillent autour de
  `SEUIL_FLAQUE` = 0,10 (`fields/ecofields/constants.py`).
- Vue : `visuals/PuddleLayer.cs` + `PuddleLayer.Mare.cs` — aplats `_lot` (LotTriangles),
  un plot marais SANS lame exportée → dessiné en vase brune (bascule d'un coup = « la
  mare se remplit de terre » vu par Nico). Reflets = 2 traits de 1 px fixes → invisibles.
- Export pont (`data/code/tools/simserver/serialize.py` l. ~545-560) : `eau_surface`
  creux `[[r,c,lame]]` SEULEMENT si lame > SEUIL_FLAQUE ; `marais` creux `[[r,c,marais,etat]]`.
- Faune : `fields/population/perception.peindre_presence` ne peint une espèce qu'au-dessus
  de `SEUIL_PRESENCE` = 0,06. Mesuré [seed 42, n=1, 78 sem.] : été s18-36 → 6 moustiques
  + 1 libellule envoyés ; automne-hiver → densité ≈ 0, rien envoyé. Or voix/info-bulle
  continuent d'en parler (ex. moustique : « J'ai senti La libellule… » — coquille
  majuscule, `sim/voix_etres_corpus.py:59`). Moustique dessiné à taille réelle 0,6 cm
  (`visuals/MacroLife.cs` table `Especes`) → visible seulement à ×8.
- DA : palette indexée (`visuals/PaletteIndexee.cs`, rampes `RampesDa`), shader animé au
  vent de la lisière (`visuals/decor_indexe.gdshader` : uniforms `vent_*`, `onde_*`,
  `TIME`) = patron à suivre pour l'eau. Banc de capture VM : `tools/capture_vm.sh`
  (options `--capture-*` documentées en tête de `world/WorldView.Capture.cs`), mesure
  d'image `tools/da_image.py`.
- Gel/neige existants : `eco.snow`, `eco.givre`, `thermique.t_min_nuit_at` ; aucun état
  de glace sur l'eau.

## Décisions (Nico, 2026-10-30)
1. **Marnage réaliste** : le cœur reste toujours en eau ; les bords se découvrent l'été en
   vase LUISANTE, transition PROGRESSIVE (jamais de bascule eau → terre d'un coup).
2. **Eau en DA 16 bits** : palette indexée + tramage ; au repos **scintillement lent** des
   reflets (2-3 tons) ; en **SIGNAL** : rides au vent, ronds de pluie, ronds de gobage quand
   les insectes de mare sont là (DA : « animation = signal d'état »).
3. **Ce qui est DIT = ce qui est PEINT** : faune de mare absente (automne/hiver) → n'est
   plus nommée (voix, info-bulle) ; moustiques en **nuée lisible dès ×4**.
4. **Glace en hiver** : état Python (vérité), rendu C#.

## Tronçons
| # | Kickoff | Golden | État |
|---|---|---|---|
| ① | `01_moteur_pont.md` | inchangé ✅ | **fait** (non commité) |
| ② | `02_eau_da.md` | inchangé ✅ | **fait** (non commité) |
| ③ | `03_signaux_faune.md` | inchangé | à faire |

## Notes de tronçon

### ① moteur + pont (2026-10-30) — golden `4c696821…` INTACT, pont **0.6.2**
- **Glace** : `fields/ecofields/glace.py` (`glace_next` pur + `GlaceMixin.tick_glace`),
  champ `eco.glace` (container), tick en **3d juste après `tick_marais`** (pas près de
  `tick_snow` : la lame du tick n'est posée qu'en 3/3b). Bilan hebdo : prise ∝ froid de
  `t_min_nuit_at` (même thermomètre que le gel, neige/voile isolent), fonte ∝ T_air au-
  dessus de `GLACE_T_FONTE` 4,5 °C ; lame ≤ SEUIL_FLAQUE → 0. Aucun effet en retour.
- **Écart kickoff** : climat simulé DOUX (T_air hebdo ≥ 1,5 °C, nuits au centre rarement
  sous −0,5 °C [seeds 42/1/2, n=3]) → un réglage « physique » (fonte dès 0 °C) ne prenait
  JAMAIS la mare. Recalé (placeholders commentés) : mare prise (centre ≥ 0,5) **2 / 9 / 14
  sem. sur 104 [seeds 1/2/42, n=3]**, jamais l'été. ⚠ Toutes ces semaines tombent en
  **semaines 3-11 de l'année, étiquetées `printemps`** par `calendrier.SAISONS` (1-13),
  car le creux thermique de `weather` est à la semaine 4 : « glace en hiver » au sens du
  calendrier du jeu = **jamais**. La vue ② doit lire `glace`, PAS la saison. Calendrier
  à trancher par Nico (hors sprint).
- **Marnage** (lame des 9 plots de `MARE_FOND`, 104 sem.) : centre (8,5) **jamais** sous
  SEUIL_FLAQUE [0/104 ×3 seeds] → source non renforcée. Bords découverts **toute l'année**
  (≈ 2-4 plots secs/sem. en été-automne-hiver, ≈ 1,5 au printemps [n=3]) : marnage surtout
  SPATIAL (angles peu profonds), faiblement saisonnier. Sonde :
  `mesures/sonde_glace_marnage.py <seed>`.
- **Dit = peint** : `perception.est_peinte(field)` = LA source (mêmes règles que
  `peindre_presence`). `voix_etres.besoins_bete` ne cite proie/prédateur que s'ils sont
  peints sur la tuile (sinon faim anonyme / pas de prédation). Noms `NOMS_BETES` en
  minuscule + `_majuscule` en tête de phrase (« J'ai senti la libellule »). Carnet
  `carnivorie` (« La nuée de moustiques se raréfie… ») émis seulement si la nuée est
  visible (densité ≥ SEUIL_PRESENCE) sous la Drosera. Info-bulle : déjà bâtie sur les
  sprites peints (aucun changement). Conséquence assumée : le **ver de terre**
  (`NON_PEINTS`) n'est plus jamais nommé comme proie (merle/hérisson disent « faim »).
- Tests : `tests/test_mare_vivante.py` (14/14), `test_sim_server` (+2 checks 0.6.2),
  vision, infobulle_vivant, population, marais, rosée, signes_legende verts.
- Taille : `serialize.py` 393 LDC (🟡, +2), `container.py` 317.

### Format du bloc `marais` (0.6.2) — pour ②
`marais: {tuile: [[r, c, marais, etat, lame, glace], …]}` — plots où
`marais_memory > MARAIS_OFF`. `marais` ∈ [0,1] (3 déc.), `etat` bool (hystérèse),
**`lame`** = `eau_surface` brute en unités d'humidité (3 déc., ≥ 0, **même sous
SEUIL_FLAQUE = 0,10** → vase luisante sous lame mince ; au centre ~2,4-3,0 [n=3], bords
0-1,7 selon la semaine), **`glace`** ∈ [0,1] (3 déc. ; 0 = eau libre, ≥ 0,5 = prise). Entrée à 4 champs
(binaire 0.6.1) → lame ABSENTE (garder le rendu d'avant), glace = 0. Le bloc
`eau_surface` (`[[r,c,lame]]` si lame > SEUIL_FLAQUE) est inchangé.

### ② eau DA 16 bits (2026-10-30) — golden `4c696821…` INTACT, `dotnet build` vert
- **Shader** `visuals/eau_mare.gdshader` posé sur la couche `PuddleLayer` (branché par
  `visuals/PuddleLayer.Eau.cs`) : **un seul lot, un seul draw call** conservé. Prescription
  « shader sur un Node2D dessiné par LotTriangles » faisable telle quelle ; ajustement :
  les triangles de mare se signalent au shader par leur **UV (x ≥ 1)** → il faut passer
  une **texture blanche 1×1** à `LotTriangles.Dessiner` pour que les UV partent (les
  triangles littéraux — flaques, tourbe, berge, rive — restent inchangés : couleur × blanc).
  Nouvelle méthode `LotTriangles.TriangleCode` (couleur PAR SOMMET = paramètres).
- **Contrat de sommet** (triangles codés) : R = lame/3, G = glace, B = bord (1 aux coins qui
  touchent la terre, ½ au centre d'un plot de rive, 0 au cœur). Chaque plot = 4 triangles
  (centre + coins) ; valeurs MOYENNÉES aux coins entre plots voisins → champ continu,
  marnage sans bascule par plot. Grain au pixel interne `floor(VERTEX × clamp(zoom,1,4))`.
- **Rendu** : eau 3 tons tramés Bayer 4×4 (plus sombre ∝ lame) ; eau peu profonde = trame
  eau/vase ; vase luisante (éclats d'eau clairs) → vase sèche (tons clairs) ; reflets =
  traits 5×2 px internes au hash (1/17 cellules en eau profonde, 1/37 peu profonde, 1/29
  sur vase mouillée) qui s'allument/s'éteignent via `TIME` (≈ 7 s/cycle, déphasés) ;
  glace = rampe `glace` tramée + larges bandes diagonales immobiles + fêlures iso,
  scintillement coupé ; prise partielle = **anneau gelé le long de la rive** (seuil
  abaissé par B). Rampes `eau_mare` / `vase` / `glace` ajoutées à `RampesDa.Matieres`
  (uniforms, source unique ; L OKLab ≥ 0,37, aucun quasi-noir).
- **Emprise de la mare** (0.6.2) = plots marais INSTALLÉS dont la lame > SEUIL_FLAQUE OU
  voisin (8-c.) d'un tel plot → un bord qui se découvre reste mare (vase), plus de bascule
  « eau → terre brune ». 0.6.1 (lame absente) : ancienne règle. **Écart** : le moteur met
  glace = 0 sur un plot découvert ; mare prise, la moyenne aux coins ouvrait un faux trou
  d'eau libre → un plot de mare découvert prend la glace max de ses voisins de mare (vue).
- **Captures** (full, seed 42, centre 1725,425, souris écartée ; le losange blanc vu dans
  les 1ʳᵉˢ captures = survol souris, pas l'eau) dans `mesures/` : `t2_ete_s26_x1/x2/x4/x8.png`
  (marnage : (8,4) profonde bleu nuit → vase brune luisante au SE, reflets visibles dès ×1),
  `t2_glace_partielle_s2_x2.png` (anneau de glace, eau libre scintillante au centre),
  `t2_glace_prise_s6_x1/x4.png` (mare prise, coins découverts en vase). Mesures
  `da_image` : 0 quasi-noir sur les 5 zones ; été ×4 = 3 tons d'eau dominants + 2 tons
  de reflet ; scintillement : 285 → 424 px de la mare changent entre t et t+1..4 s
  [×2, n=1, ciel couvert/pluie dans la capture ⇒ inclut des gouttes].
- Taille (LDC) : `PuddleLayer.Mare.cs` 173, `PuddleLayer.cs` 142, `PuddleLayer.Eau.cs` 48,
  `eau_mare.gdshader` 81 — tout 🟢.
- **F5 Nico** : densité/vitesse du scintillement (`reflet` : raretés 17/37/29, `VIF` 0,9) ;
  plafond du grain `clamp(zoom,1,4)` (à ×8+ le tramage reste à 2 px écran) ; teinte des
  rampes ; lisibilité de la vase luisante vs eau peu profonde. Constat annexe : à s26 la
  mare montre une encoche (un plot du fond non installé / hors emprise) — donnée moteur.

## §REPRISE
① fait (commit `e4ab37b`), ② fait (non commité au moment de l'écriture). Prochain : **③**
`03_signaux_faune.md` (C#) — les rides/ronds s'ajoutent dans `eau_mare.gdshader` (branche
codée, eau libre seulement : pixel non gelé et `b < m`), uniforms posés par
`PuddleLayer.Eau.cs` ; lire d'abord les notes ① (format `marais`) et ② ci-dessus.
Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire ».
Lancement : `/sprint-auto sprint_mare_vivante`.
