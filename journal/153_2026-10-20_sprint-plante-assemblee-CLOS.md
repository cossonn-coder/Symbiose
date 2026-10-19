# 2026-10-20 — Sprint PLANTE ASSEMBLÉE — CLOS (verdict PC en attente)

`/sprint-auto`, ①→⑦. **Golden `22768f33…` jamais re-figé**, `dotnet build` vert à
chaque tronçon. Doc : `docs/rendu/pixelart/conception_plante_assemblee.md` ; mesures
détaillées : `sprints/rendu/pixelart/sprint_plante_assemblee/00_etat.md`.

- **① Decor + couvre-sol en lot** (`1c0ccb8`) : `visuals/LotTriangles.cs`, un `DrawMesh`
  par couche. ×4 : 2 030 → 471 draw calls [VM, n=1] ; image identique à ±1/255 [VM, n=22].
- **② Plantes en pages d'atlas + maison en lot** (`22e1e3d`) : `visuals/AtlasPages.cs`.
  Prémisse corrigée : `Objects` = maison ≈ 345 draw calls, plantes ≈ 36 [VM, n=1].
  ×4 : 471 → 114 [VM, n=1] ; 0 px d'écart [VM, n=24] ; VRAM ×4 34 → 48 Mo [VM, n=1].
- **③ Banc accéléré + légende F1** (`b90f52b`) : Maj+E (s35, ×8, Continu 3 s/sem), postes par
  semaine, pollen redessiné au changement (`PollenLot.cs`, 1,54 → 0,58 ms/image [VM, n=1]).
- **④ Kit d'éléments** (`5b60743`) : atlas de niveaux 84×70 (6 `LeafShape` × 4 tailles × 3
  variantes + 3 fleurons), sans `Random`, planche `capture_vm.sh -k`.
- **⑤ Plante assemblée aux paliers bas** (`53a725e`) : vraies tiges + touffes du kit à ×0,5/×1/×2 ;
  ×4/×8 identiques au pixel [VM, n=4]. Décision imprévue : ombre/lumière permutées quand le sud
  est en haut (orientations 2-3) plutôt que retourner les touffes.
- **⑥ Signes côté Python** (`a5ca441`) : corpus 11 signes + 20 bêtes non nommées, `observer` +
  `signe` (carnet, hors tick, sans maîtrise), `player.appris`, encyclopédie type `signe`,
  commande `legende`. Pont **0.5.46**.
- **⑦ Info-bulle 2 niveaux + bilan** (`05b4acb`) : description puis cause/nom une fois appris,
  Maj+F3 affichage technique, onglet Signes. Suspect accéléré tranché : création de pages
  d'atlas 2048² en boucle (non corrigé). Bilan ×4 : **2 013 → 111 draw calls** [VM, n=1].

**Dette** : D109 archivée (soldée), **D110** ouverte (bête jamais nommée en jeu normal — à
trancher ; carpophores sans `vu` ; recyclage des pages d'atlas ; verdict PC D1 ; réglages du kit).
**Refactor** : aucun fichier > 400 LDC ; vigilance `serialize.py` 368, `WorldView.Snapshot.cs` 306,
`SimBridge.cs` 305. **Reste** : F5 Nico (E + Maj+E sur le PC, 3 questions de ressenti).
