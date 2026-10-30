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
| ① | `01_moteur_pont.md` | inchangé | à faire |
| ② | `02_eau_da.md` | inchangé | à faire |
| ③ | `03_signaux_faune.md` | inchangé | à faire |

## Notes de tronçon

## §REPRISE
Lire `CLAUDE.md` + ce fichier + le kickoff du premier tronçon « à faire ».
Lancement : `/sprint-auto sprint_mare_vivante`.
