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
| ② | `02_eau_da.md` | inchangé | à faire |
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

## §REPRISE
① fait (non commité au moment de l'écriture). Prochain : **②** `02_eau_da.md` (C#),
lire d'abord « Format du bloc `marais` (0.6.2) » ci-dessus.
Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire ».
Lancement : `/sprint-auto sprint_mare_vivante`.
