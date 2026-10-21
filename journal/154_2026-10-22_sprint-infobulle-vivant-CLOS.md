# 2026-10-22 — Sprint INFO-BULLE DU VIVANT — CLOS

`/sprint-auto`, ①→③. **Golden `22768f33…` jamais re-figé**, `dotnet build` vert. Doc :
`docs/narration/semiologie/conception_infobulle_vivant.md` ; état et mesures :
`sprints/narration/semiologie/sprint_infobulle_vivant/00_etat.md`. Absorbe D110 (a)(b)(g).

- **① Python** (`11317ea`, pont 0.5.47) : corpus (rôle de 20 bêtes, champignon, voix saine,
  libellés), crédit +1 palier par saison neuve d'observation (plafond 3), `appris` inclut le
  champignon, rôle local du carpophore au snapshot (bois / racines / humus), nourriture des
  butineurs, bornes de nourriture mesurées 0,23 / 0,50 [VM, n=18697 sprites].
- **② Vue plante** (`2bc9233`) : seuil de visibilité mesuré au rendu par cause (banc VM), voix
  saine (vert franc / automne / terne), technique avec « (sous seuil) / (hors palier) ».
- **③ Vue faune / champignon** (pont 0.5.48) : picking enrichi (`MacroPick` : abondance dans
  le plot, nourriture, rôle, densité), lignes bête / carpophore tirées de la légende, dédup
  d'observation par (clé, saison), technique. `observer` renvoie `appris` → le nom apparaît dès
  le survol qui franchit le palier ; debug `palier3` crédite aussi le champignon.

**Décision :** butineurs lus avec les bandes de nourriture communes (bornes propres
dégénérées : tertiles 0,00 / 0,27 [VM, n=3205]) — à confirmer par Nico.

**Constat :** aucun carpophore en 5 automnes sur `full` [VM, seed 42, 269 sem.] (mycélium
≤ 0,17 < 0,30, humidité en baisse sous 1,5) → le champignon n'est pas nommable en jeu normal.

**Dette** : D110 (a)(b) fermés, (g) levé côté vue (reste le pessimisme du moteur :
acclimatation quasi universelle), + (h) carpophores absents, (i) nourriture des butineurs.
**Reste** : F5 Nico (procédure `00_etat.md` §F5).
