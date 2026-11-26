## 2026-11-26 — Sprint LISIÈRE ET CHARGEMENT (S3 du style homogène) CLOS côté code — séquence S1-S3 close

`/sprint-auto sprint_lisiere_chargement`, cinq tronçons, golden `bce813af…` **intact à chaque
tronçon** (vue + outillage, `data/code/` jamais touché). Build C# vert, 0 avertissement.
Sprint : `sprints/rendu/splatting/sprint_lisiere_chargement/` ; conception (figée le même jour,
commit `b5a0e2b6`) : `docs/rendu/splatting/conception_lisiere_chargement.md`.

| # | Commit | Fait |
|---|---|---|
| ① | `d69a0cd0` | Kit de lisière en splats : 10 recettes (`tools/splat/recettes/lisiere_*.js`), adaptateur `DecorLayer.KitSplats.cs` (mêmes cases, atlas réécrit en place) ; recette « rameau aplati » du sapin cuite aux 7 paliers (L4). |
| ② | `26fe9017` | Arbres de lisière sur le bois de S2 (`DecorLayer.Charpente.cs`) : fût et charpentières en `RubanTexture`, écorce cuite recopiée dans l'atlas du décor (un seul envoi), pied évasé, sapin en étages ; sapin du jardin ×8-×32 en rameaux aplatis (`PlantRenderer.SapinRameaux.cs`). |
| ③ | `1d643143` | Atlas par palier ×8/×16/×32 (`DecorLayer.Hauts.cs`) : pièces recuites 2×/4×/8×, construites hors fil principal, un seul atlas haut vivant (×32 = 100,8 Mo mesuré) ; uniform `zoom` = palier réel ; scintillement de l'eau jusqu'à ×32. |
| ④ | `5049c696` | Écran de chargement en mycélium : carte des âges (porte de décision mesurée), récit spore → réseau → mycorhize → carpophore ; init du pont en `Task.Run`, progression monotone pondérée par phases (`ProgressionChargement.cs`). |
| ⑤ | (orchestrateur) | Revue des paliers ×0,5→×32 (4 bords, 4 saisons, neige, vent, rotation) ; message de repli des paliers hauts corrigé ; **liste F5 exhaustive S1+S2+S3** dans le `00_etat.md` du sprint. |

**Écarts aux kickoffs (tranchés en tronçon) :**
- ① la bascule Maj+F11 ne reconstruit pas les mailles (cases identiques), elle réécrit l'atlas.
- ② écorce cuite réduite au-delà de 2 texels/px = sel → seuil `EcorceReductionMax` = 2, stries procédurales en dessous.
- ③ atlas ×32 = 100,8 Mo, pas ~64 Mo estimés ; construction ×32 sur le fil principal = 746 ms → passée en tâche de fond.
- ④ racine nue puis gainée impossible en une image → deux couches (fond | mycélium) dans la texture couleur.

**Mesures :** voir les comptes rendus ①→⑤ du `00_etat.md` [VM llvmpipe, non transposables au PC].
Chargement 34-36 s [VM, n=2], dont gel du montage ~1,4 s ; `assets/splats/` 67 Mo.

**Restes (non ouverts en dette, règle « pas de dette neuve sans en fermer une » — à trancher par Nico au F5) :**
à-coup de la 1ʳᵉ arrivée ×32 (préparation + envoi GPU de l'atlas de lisière) ; roche de falaise ×16-×32
au grain très fin ; ripisylve aulne/saule jamais capturée ; poids des phases du chargement à recaler sur
le PC ; restes S1/S2 (plantain, framboisier caduc, marche de couleur du bois, écorces grises claires).

**F5 :** la séquence « style homogène » (S1 → S2 → S3) est CLOSE côté code ; le F5 complet de Nico se joue
maintenant, sur la liste exhaustive du `00_etat.md` de S3 (9 sections : chargement → jardin par palier →
plantes → arbres → graminées → lisière → portraits → Maj+F11 → perf).
**Prochain : F5 complet de Nico, puis proof of concept ×64 (chanvre).**
