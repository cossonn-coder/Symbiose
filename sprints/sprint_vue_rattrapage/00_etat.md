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

## Les DEUX manques du snapshot (à exposer en lecture, golden neutre)
- **Plantes mortes persistantes (squelettes)** : `_snapshot` fait
  `if not p.is_alive: continue` → les squelettes (`morte`, `stade_mort`
  `seche`/`couchee`, `bois_restant`, `semaines_mort`) sont **invisibles**. À
  exposer (sous-sprint 02).
- **Litière par plot** : `EcoFields.litiere` (parcelles `{tissu, masse, age}`)
  n'est pas dans le snapshot. À exposer de façon compacte (sous-sprint 03).

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
| 02 | **Cycle de vie visible** : fruits réels (maturité vert→mûr→sur-mûr) + squelettes post-mortem + abscission. Snapshot expose les morts (lecture) | `02_fruits_squelettes.md` | snapshot RO | neutre | ⬜ |
| 03 | **Sol vivant & compost** : litière au sol + structures bac/pile + jauge `compost_mur` + 6 gestes compost. Snapshot expose la litière (lecture) | `03_litiere_structures.md` | snapshot RO | neutre | ⬜ |
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
**01 CLOS** (build vert, golden `908f591bee…` inchangé, F5 à valider par Nico).
Prochain : **02** (lire `02_fruits_squelettes.md`) — premier à toucher le
snapshot en LECTURE (exposer les plantes mortes/squelettes), donc re-vérifier
`908f591bee…` + `tests/test_sim_server.py` après chaque ajout serialize.
État moteur de référence : golden `908f591bee…` / population `435e6f72…`, pont
`ENGINE_VERSION 0.3.5`, `tests/test_sim_server.py` 123 checks. Détail des features
moteur à rendre : `sprints/sprint_decomposition_compost/00_etat.md` (§Acquis ①–⑤)
+ `docs/conception/CONCEPTION_DECOMPOSITION_COMPOST.md`.

## Journal de bord (rempli en fin de sous-sprint)
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
