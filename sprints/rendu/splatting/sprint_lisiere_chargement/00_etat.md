# sprint_lisiere_chargement — état (S3 du style homogène)

**Conception FIGÉE le 2026-11-26** (`/conception`, Nico : « vas-y ») → `docs/rendu/splatting/conception_lisiere_chargement.md`.
**En cours (`/sprint-auto`)** : ① fait et commité ; ② fait côté code (2026-11-26, non commité par le sous-agent).
Source : `docs/rendu/splatting/backlog_splatting.md` (S3 = (b) lisière + (g) chargement),
`conception_reliquats_plantes.md` §2 (E2 : barre de progression permise à l'écran de chargement,
philo #5 = pendant le jeu seulement), `conception_bois_arbres.md` (C2 : `RubanTexture` réutilisable).
Golden attendu : `bce813af…` INTACT (vue + outillage, `data/code/` jamais modifié).

## Faits vérifiés au code (2026-11-26)
- Lisière = `DecorLayer` (19 partials) : UNE maille (ArrayMesh) par palier ×0,5/×1/×2/×4, un seul
  atlas de CODES (palette indexée, dialecte 2, `DecorLayer.KitCodes.cs`), shader `decor_indexe.gdshader`
  (saison par bouquet, neige, givre, vent). `MaxZoom = 4` : à ×8-×32 la maille ×4 est grossie.
- Kit du décor (`DecorLayer.Kit.cs`) : 10 formes peintes à la règle (Herbe, HerbeHaute, Fleur, Roncier,
  SousBois, Feuillu, Conifere, Galet, Bloc, Roseau) × 1-5 tailles × 3 variantes × 16 teintes.
- Arbres de lisière : silhouettes par essence (`DecorLayer.Arbres.cs`, 8 essences : chêne, hêtre,
  bouleau, charme, sapin, noyer, aulne, saule — toutes dans les 12 écorces de S2) ; dessin =
  ombre → tronc cerné → charpentières en traits (`DecorLayer.Branches.cs`) → enveloppe → bouquets du kit.
- Adaptateur existant pour les plantes : `PlantRenderer.KitSplats.cs` (planche splat → même format
  que le kit généré, interrupteur Maj+F11 / `SYMBIOSE_SPLATS=0`).
- Chargement (`world/WorldView.Chargement.cs`) : fond uni + touffe ×8 + « Le jardin se prépare ».
  Séquence : 2 images → `AssurerGerbes` (BLOQUANT) → `StartSimulation` (`_bridge.Init` BLOQUANT +
  montage) → cuisson du cadre (`BakeQueue.ModeChargement`, jusqu'au repos ou 30 s).
  Le pont a déjà un verrou d'I/O et sert déjà depuis `Task.Run` (step, action, fields).
- S2 laisse un reste : recette « rameau aplati » du sapin (aiguilles ×8-×32) non cuite.

## Décisions arrêtées (Nico, lot 1, 2026-11-26)
- **L1 Arbres de lisière = silhouette améliorée** : architecture gardée (ombre, tronc, charpentières,
  enveloppe, bouquets) ; charpente en `RubanTexture` + écorce cuite S2 (bandes recopiées dans l'atlas
  du décor → un seul envoi), pied évasé, sapin en étages, bouquets feuillus/conifères en pièces splat.
  Saison pied par pied, neige, vent : inchangés (shader). Raison : centaines d'arbres, imposteurs =
  une variante par saison/état et perte de la saison qui gagne le bois.
- **L2 Paliers ×8-×32 = atlas par palier** : même géométrie (maille ×4), atlas des pièces cuit 2×/4×/8×
  plus fin, permuté au changement de palier → pixel natif partout. ~64 Mo à ×32 [estimé, non mesuré],
  sous le budget 1 Go (E6). Grains procéduraux du shader (roche, eau, neige, givre) : constater au-delà
  de ×4 par capture et les caler sur la même règle.
- **L3 Mycélium = carte des âges + mycorhize** : image splat cuite hors ligne (illustration en palette
  pleine, comme les portraits) + carte « date d'apparition » par pixel ; le shader révèle âge ≤
  progression, front lumineux aux pointes. Récit : spore qui germe → hyphes qui s'arborisent →
  rejoignent la racine d'une plantule (manteau mycorhizien) → petit carpophore à 100 %. Porte de
  décision : maquette mesurée (carte des âges lisible au mélange gaussien ; repli = N images cuites).
- **L4 (Claude)** : rameau aplati du sapin cuit en S3, sert la lisière ET le sapin du jardin ×8-×32
  (reste de S2).
- **L5 (Claude)** : `_bridge.Init` part en `Task.Run` (verrou d'I/O existant) → l'écran vit pendant
  l'init ; montage seul sur le fil principal (gel mesuré). Progression MONOTONE pondérée par phases
  mesurées (gerbes, init, montage, cuisson du cadre = 1 − file restante / file initiale).

## Tronçons (golden `bce813af…` intact partout)
| # | Kickoff | État |
|---|---|---|
| ① | `01_kit_lisiere.md` — kit de lisière en splats + rameau aplati | **fait** (F5 attendu) |
| ② | `02_arbres_lisiere.md` — arbres de lisière sur le bois de S2 + sapin du jardin ×8-×32 | **fait** (F5 attendu) |
| ③ | `03_paliers_hauts.md` — atlas par palier ×8-×32 | à faire |
| ④ | `04_chargement_mycelium.md` — écran de chargement en mycélium (porte : maquette) | à faire |
| ⑤ | `05_revue_f5.md` — revue, liste F5 exhaustive S1+S2+S3, clôture | à faire |
Ordre : ① avant ②③ ; ④ indépendant ; ⑤ en dernier.

## Compte rendu ① (2026-11-26)
- **Recettes** : fabrique `tools/splat/recettes/lisiere.js` + 10 `lisiere_<forme>.js` (planche `kit`,
  cases = `Tailles` de `DecorLayer.Kit.cs` recopiées dans `BOITES` — à garder en phase). Réutilisées :
  corolle de `fleuron` (fleurette, face tournée vers l'œil sinon 3×1 px), `feuille_composee` (roncier
  en dôme + 3 cannes), `feuille_plume` (sous-bois), `feuille_ovale` (bouquet feuillu en dôme),
  arc de `feuille_ruban` (herbes, feuilles du roseau), sculpteur mandataire des portraits (`place`).
  Neuves : `rameau_aplati.js` (L4, couches aiguilles | stomates, cuit aux 7 paliers pour ②),
  galet, bloc (deux pavés), roseau (tiges + massette en couche 1).
- **Outil** : `cuire.js` accepte `boites: [[w,h]…]` — zoom ajusté (≤ 10 photos, dichotomie) pour
  REMPLIR la case sans la dépasser. Chemin `tailles`/paliers inchangé (fleuron recuit identique à l'octet).
- **Adaptateur** `visuals/DecorLayer.KitSplats.cs` : couches fondues sur l'attache, pièce posée en
  bas-centre de sa case (= ancrage de `PoserPiece`), codes G copiés ; fleurette → orientation
  `OrientFleur`, cœur ton 4 ; massette → ton 0. Pièce absente → kit généré entier + avertissement.
- **Écart au kickoff** : la bascule Maj+F11 ne reconstruit PAS les mailles — les cases ne bougent
  pas d'une source à l'autre, l'atlas est réécrit en place et renvoyé (`DecorLayer.BasculerSplats`,
  appelé par `WorldView.Controls`). Non testable au banc (pas de touche simulée) → **F5**.
- **Mesures** (`mesures/01_*`) : banc F10 `full`, avant (`SYMBIOSE_SPLATS=0`) / après, ×0,5 ×1 ×2 ×4,
  -w 44. Effet net sur les bouquets de houppier (bulles → feuillage), roseaux dressés à massette,
  blocs anguleux ; herbes de prairie plus pâles et moins contrastées que les grains d'avant (à juger F5).
  Lecture du kit splat : 37-102 ms [VM chargée 4-8, n=2], une fois par partie. Maille ×2
  construite : 250-487 ms avant / 249-489 ms après [VM chargée, n=3 par côté, bruit > écart] → pas
  de régression visible. `assets/splats/` : 66 Mo (+0,8 Mo), sous l'alerte 200 Mo.
- Cuisson : `lisiere_conifere` ~25 min [VM chargée, n=1] (21 rameaux posés × 3 variantes) — à
  ne recuire que si la recette change.

## Compte rendu ② (2026-11-26)
- **Lisière** (`visuals/DecorLayer.Charpente.cs`, neuf) : fût, axe et charpentières en rubans (`RubanTexture`
  `Normales` + `PoserBandePeriodique` + `Verser` dans le lot du décor → passent par l'encodeur de sommets :
  plan, vent, phase du pied). Flancs = aplats orientés par la normale du ruban (soleil réel) ; fût à pied
  évasé (+60 % au sol, éteint à 15 %) et légère flèche au hash ; charpentière = courbe du 2ᵉ degré passant
  par départ/coude/bout (reste dans l'ellipse) ; plus de cerne. Sapin en étages (3-8 rangs de bouquets
  conifères, plus courts vers le haut, bouts retombants, enveloppe sombre entre deux rangs).
- **UN envoi gardé** : bandes branche + tronc des 8 essences (×4) recopiées dans l'atlas du décor
  (`RangerEcorces`, à la suite des étagères du kit ; palette de l'écorce, classe inerte pour le tronc,
  sans saison pour la branche). Accès brut : `BandesCuites.CodesBruts` (+ `d_cm` lu du manifeste),
  `Ecorces.CodesBruts`. Draw calls de la lisière inchangés (1 maille).
- **Écart au kickoff (mesuré)** : la bande ×4 réduite au-delà de 2 texels/px tourne au sel (bouleau gris
  tacheté à ×1-×2, capture du 1er essai). Règle ajoutée (`EcorceReductionMax` = 2) : on réduit d'abord le
  nombre de colonnes côte à côte (≤ 3, selon `d_cm`), et si même une colonne est trop réduite, pas de
  bande : le fût garde les stries procédurales (orient. 11/12) et le bouleau ses lenticelles. Résultat :
  écorce cuite sur les fûts larges à ×2, partout à ×4 ; ×0,5-×1 = ruban lissé + stries. ③ (atlas ×8-×32)
  devra recopier les bandes du palier (même `CodesBruts`).
- **Interrupteur** : Maj+F11 change aussi la géométrie → `_versionBois` + `SuivreBois` (appelé par
  `AvancerFond`) jettent les mailles. Non testable au banc (touche) → **F5**.
- **Sapin du jardin ×8-×32** (`PlantRenderer.SapinRameaux.cs`, neuf ; crochet dans `DrawFeuillesHouppier`) :
  un `rameau_aplati` tous les 8 cm de chaque rameau/brindille du petit bois, alternés ±0,45 rad, lacet et
  inclinaison du brin, même densité/tons/tri ; couche `stomates` = ton clair (`CouleurCouche`). Effet net :
  le poteau hérissé de tirets devient un sapin en rameaux plats (planches ×8, ×32).
- **Mesures** (banc `full -B`, forêt N, `-c 1000,-300`, ×1/×2/×4, été -w 6 / hiver -w 32 ; sapin :
  `-b houppiers -c 1775,1025 -l 2 -n 220 -w 28 -H` ; captures `mesures/02_*`, avant = HEAD ①). Sommets de
  la maille avant → après : ×1 129 684 → 149 112 (+15 %), ×2 149 532 → 187 650 (+25 %), ×4 149 532 →
  237 240 (+59 %) [n=2 saisons, identiques]. Construction : avant 250-410 ms, après 318-400 ms [VM chargée
  5-10, n=2 par palier] : bruit > écart, pas de hausse mesurable ; le 30-37 ms du kickoff est une
  référence PC, non reproduite ici → à relire au rapport C du PC. Draw calls : 1 maille, inchangé.
  `assets/splats/` 66 Mo (inchangé, rien cuit).
- Ripisylve : le banc F10 ne porte pas de dominante (pas d'aulne/saule semés) → non capturée, **F5**.
- **F5 ②** : Maj+F11 sur la lisière (bois reconstruit) ; ripisylve aulne/saule ; écorce du bouleau à ×4
  (marques grises denses, celles de la bande S2) ; sapin de lisière en étages (lisibilité, nombre de rangs) ;
  sapin du jardin ×8-×32 (pas de 8 cm, écart ±0,45 rad, ton des stomates).

## §REPRISE
Relire ce fichier + `docs/rendu/splatting/conception_lisiere_chargement.md`. ①② faits (② non commité par
le sous-agent : commit `feat(lisiere②)` à faire par l'orchestrateur). Prochaine étape : tronçon ③
`03_paliers_hauts.md` — y recopier aussi les bandes d'écorce du palier (`Ecorces.CodesBruts(…, palier, …)`,
`RangerEcorces`) pour que le bois de lisière garde son écorce au-delà de ×4.
