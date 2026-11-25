# tools/splat — atelier de précuisson des pièces en gaussian splats

Sprint `sprints/rendu/splatting/sprint_precuisson_splats/` (conception :
`docs/rendu/splatting/conception_precuisson_splats.md`). Outil **VM seulement**
(Node ≥ 18, aucune dépendance npm) : il produit des images versionnées que la vue
Godot affiche. Le moteur Python n'est pas concerné (golden intact).

## Provenance d'ink-studio (copie figée, ne pas modifier)

`vendor/ink/` = <https://github.com/siliconjungle/shapeshift-labs-ink-studio>,
commit `fb9403158198400df87f49c169ce42d0cf7345fa` (2026-11-20), copié le
2026-11-20 sans `.git`, licence MIT (`vendor/ink/LICENSE`). 11 Mo, 1 004 fichiers.
Au premier lancement, ink-studio compile `vendor/ink/dist/standalone.js` (ignoré
par son propre `.gitignore`). Une limite d'ink-studio se NOTE, elle ne se corrige
pas dans la copie.

`tools/splat/.gdignore` : Godot n'importe rien de ce dossier (fichiers `.obj`,
`.js` d'ink-studio).

## Usage

```sh
# cuire une recette → assets/splats/<recette>_x<palier>.png + <recette>.json
node tools/splat/cuire.js feuille_composee --controle sprints/…/mesures
# mesurer le nombre de vues (lacets / inclinaisons) d'une recette
node tools/splat/mesurer_vues.js feuille_composee
# planche de contrôle de toute la bibliothèque (relit assets/splats, ne recuit rien)
node tools/splat/controle_feuilles.js sprints/…/mesures/controle_feuilles.png
```

Portraits (⑥, ~10 processus) : `node tools/splat/cuire_portraits.js --liste | xargs -P 10 -n 1 node tools/splat/cuire_portraits.js` puis `node tools/splat/cuire_portraits.js --manifeste` et `node tools/splat/controle_portraits.js <dossier>`.

Cuire toute la bibliothèque (② : 24 recettes, ~12 processus en parallèle) :
`ls tools/splat/recettes | sed 's/\.js$//' | grep -v '^touffe$' | xargs -P 12 -I{} node tools/splat/cuire.js {}`.
Ne recuire que les recettes modifiées (D2 : chaque régénération grossit l'historique git).
Organes (③, 22 recettes) : même commande filtrée par
`grep -E '^(tete_|fruit_|gousse|chaton|epi_|panicule|bouton|fleuron)'`.

Options de `cuire.js` : `--sortie` (défaut `assets/splats`), `--controle DOSSIER`
(planche de contrôle humaine), `--lacets N` (défaut : la recette, sinon 8),
`--inclinaisons` (défaut : la recette, sinon `-30,0,30`),
`--paliers 0.5,1,…`, `--actuel capture.png:x,y,w,h` (pièce actuelle de la vue
collée sous le contrôle). Deux cuissons donnent des fichiers identiques à l'octet
(`sha256sum assets/splats/*`).

## Fichiers

| Fichier | Rôle |
|---|---|
| `cuire.js` | orchestration : sculpter une fois, photographier N fois, écrire |
| `mesurer_vues.js` | mesure des sauts de silhouette selon le nombre de vues |
| `lib/iso.js` | caméra de cuisson calée sur `WorldView.Projection.cs` (0,39 px/cm × palier) |
| `lib/codes.js` | passes ink-studio → codes de palette indexée (ton + orientation) |
| `lib/planche.js` | rangement en planches (une par palier) + manifeste JSON |
| `lib/controle.js` | planche de contrôle : rampe 5 tons + soleil fixe (règle du shader) |
| `controle_feuilles.js` | planche de contrôle de toute la bibliothèque (relue sur disque) |
| `lib/limbe.js` | un limbe en volume depuis un contour 2D de la vue (pli, gaufrage, pétiole) |
| `lib/feuille.js` | fabrique de recettes de feuille (fiche → recette) |
| `lib/trous.js` | degrés de trous D5 : morsures (bord) et grêle (criblage), solides négatifs |
| `recettes/*.js` | une recette = un organe sculpté (contrat en tête de `feuille_composee.js`) |
| `recettes/touffe.js` | fabrique des touffes du kit (`touffe_<forme>.js`, une par `LeafShape`) |
| `lib/organe.js` | ③ fabrique des recettes d'organes (têtes, fruits, boutons, bois) : couches, axe tassé à l'oblique de la vue, briques pétale/boule/tige/corolle |
| `recettes/tete_*.js`, `fruit_*.js`, `gousse`, `chaton`, `epi_*`, `panicule`, `bouton`, `fleuron` | ③ organes (une recette par forme dessinée par la vue, champ `vue` du manifeste) |
| `controle_organes.js` | ③ planche de contrôle des organes (relue sur disque, couches superposées) |
| `recettes/bois.js` + `couture_bois.js` | ③ tronçons d'écorce + MESURE de couture sur le pommier an 10 — bois NON livré (joints visibles), cf. 00_etat ③ |
| `cuire_portraits.js` | ⑥ PORTRAITS : 3 par espèce (jeune · mûre · fin de cycle / hiver), plante entière en pleine couleur → `assets/portraits/<Espece>_<etat>.png` + `portraits.json` (`--manifeste`, `--liste`) |
| `controle_portraits.js` | ⑥ planches de contrôle des portraits (relues sur disque) |
| `portraits/table_cs.js` | ⑥ lit la table des espèces DANS le C# de la vue (littéraux FichePort, FicheLiane, RecetteRameaux, palettes…) — source unique |
| `portraits/moteur.py` | ⑥ cycle de vie, stades et squelettes (lianes, arbres) rejoués par le moteur Python, lecture seule |
| `portraits/sculpteur.js` | ⑥ sculpteur mandataire (pose une recette ②③ déplacée/tournée/à l'échelle) + palettes pleine couleur |
| `portraits/organes.js` | ⑥ index « nom vue → recette » lu dans les recettes + contexte d'un portrait (boîte englobante) |
| `portraits/etats.js` | ⑥ les 3 états (D6) depuis `life_cycle` / `deciduous` du moteur, couleurs d'état |
| `portraits/ports_bas.js`, `ports_hauts.js`, `arbres.js` | ⑥ les ports en 3D : rosette, tapis, rampante, prairie · tige, chaume, buisson, volubile · arbres et lianes sur segments moteur |

## Format d'une pièce (= atlas du kit actuel, `PlantRenderer.Kit.cs`)

PNG RGBA8 : **R** = niveau du kit (2 ombre · 3 base · 4 lumière, éclairé vers le
bas — rendu littéral F11 OFF) ; **G** = code indexé `128 | ton << 4 | orientation`
(`visuals/PaletteIndexee.cs`) ; **B** = 0 ; **A** = 255 posé / 0 vide. Le n° de
palette (R,G du pixel final) est posé à l'assemblage par `modulate`.
Manifeste : `vue` (noms de la vue servis par la recette = table « nom vue →
recette »), `trous` (paliers, variantes et degrés cuits) ; par pièce `palier`,
`taille_px` (touffes du kit, planche `kit`), `trou` + `degre` (pièces trouées), `inclinaison_deg`, `variante`, `lacet_deg`
(0 = organe vers l'est, sens trigo vu du dessus), `planche`, `rect` [x, y, w, h],
`attache` [x, y] en px de la pièce (là où l'organe tient à sa tige).
③ : `couches` (manifeste) et `couche` (pièce) — un organe multicolore donne une pièce
PAR COUCHE et par vue, même attache ; la vue pose une palette par couche.
