# sprint_lisiere_chargement — état (S3 du style homogène)

**Conception FIGÉE le 2026-11-26** (`/conception`, Nico : « vas-y ») → `docs/rendu/splatting/conception_lisiere_chargement.md`.
**Prêt pour `/sprint-auto sprint_lisiere_chargement`.** Aucun tronçon exécuté.
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
| ① | `01_kit_lisiere.md` — kit de lisière en splats + rameau aplati | à faire |
| ② | `02_arbres_lisiere.md` — arbres de lisière sur le bois de S2 + sapin du jardin ×8-×32 | à faire |
| ③ | `03_paliers_hauts.md` — atlas par palier ×8-×32 | à faire |
| ④ | `04_chargement_mycelium.md` — écran de chargement en mycélium (porte : maquette) | à faire |
| ⑤ | `05_revue_f5.md` — revue, liste F5 exhaustive S1+S2+S3, clôture | à faire |
Ordre : ① avant ②③ ; ④ indépendant ; ⑤ en dernier.

## §REPRISE
Relire ce fichier + `docs/rendu/splatting/conception_lisiere_chargement.md`. Prochaine étape :
`/sprint-auto sprint_lisiere_chargement` → tronçon ①.
