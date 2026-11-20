# sprint_precuisson_splats — état du sprint

**Conception FIGÉE le 2026-11-20** (`/conception`, Nico : « vas-y ») →
`docs/rendu/splatting/conception_precuisson_splats.md`. Sprint (a) « plantes » du
programme « tout en splats » (D7). **Prêt pour `/sprint-auto sprint_precuisson_splats`.**
Golden : **INTACT à tous les tronçons** (vue + outillage, `data/code/` jamais touché).

## Carte des tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_atelier_cuisson.md` — outil `tools/splat/` + feuille composée, format palette indexée, tous paliers, mesures — **PORTE DE DÉCISION** | à faire |
| ② | `02_feuilles.md` — bibliothèque des feuilles (formes, variantes, vues, trous D5) | à faire |
| ③ | `03_tetes_fruits_bois.md` — têtes, fleurs, fruits, bourgeons, bois (couture mesurée) | à faire |
| ④ | `04_vue_paliers_hauts.md` — vue ×4 → ×32 | à faire |
| ⑤ | `05_vue_paliers_bas.md` — vue ×0,5 → ×2 (kit) | à faire |
| ⑥ | `06_portraits.md` — 162 portraits | à faire |
| ⑦ | `07_vue_encyclopedie.md` — encyclopédie + magazine, clôture | à faire |

## Règles du sprint
- Si la porte du ① échoue (pièce illisible à 3-9 px, ou ton/orientation non
  extractibles) : **arrêt**, retour en `/conception`.
- Poids (D2) mesuré à chaque tronçon ; alerte et arrêt si les pièces dépassent ~200 Mo.
- Capture VM sans écran pour voir avant le F5 : `tools/capture_vm.sh` (Godot + Xvfb
  sous `~/opt`, cf. `tools/lib_vm_godot.sh`).
- Interdits : `test_epaisseur_500ans` ; DeepSeek dans les sous-agents (protocole) ;
  modifier les sources copiées d'ink-studio.

## Compte rendu des tronçons
(rempli par chaque tronçon : fait, mesures, chemins des planches et captures)

## F5 (recette pour Nico — complétée par ④⑤⑦)
(à écrire)

# Carnet de conception (historique)

## Contexte
- Prototype tomate validé par Nico (« c'est ça que je veux pour Symbiose ») :
  `docs/rendu/splatting/prototype/` (ink-studio CPU sur la VM, 106 000 splats,
  cuisson 17 s [n=1 plant, VM]).
- Refonte 3D temps réel = horizon (mémoire `project_refonte_splatting`) ; PC de Nico
  en cours d'achat, budget serré : carte 8 Go probable, 16 Go de RAM.
- Ce sprint = amener le rendu splat DANS la vue actuelle (iso 2D) par PRÉCUISSON
  hors ligne (images produites sur la VM, affichées par Godot).

## Faits vérifiés (code)
- Vue : cuisson EN JEU par plante (`visuals/PlantBaker.cs`, atlas de poses de vent
  ≤ 8, pages communes `AtlasPages`) depuis un dessin vectoriel ; paliers bas
  ×0,5-×2 = « plante assemblée » : vrais segments + TOUFFES du kit
  (`PlantRenderer.Kit.cs`, 3-9 px, codes de palette indexée ton + orientation de
  face lus par shader, lumière côté soleil réel).
- Moteur : la tomate n'est qu'une tige droite (port inventé côté vue).
- Catalogue : 54 espèces [classes distinctes des 5 tables de `plants/catalogue.py`].
- ink-studio : export `atlas --directions N --maps depth,normal,...` (cartes de
  normales → codes d'orientation de face possibles).

## Décisions arrêtées
- **D1 (Nico 2026-11-20) fidélité MAX au moteur dans le jardin** : la plante en jeu
  suit ses vrais segments (taille au segment, phototropisme, vent, santé, rotation
  D35). → plantes entières précuites (A) EXCLUES en jeu ; reste B (kit d'organes
  précuits assemblé sur les segments) ou C (B + portraits entiers hors jeu).
- **D2 (Nico 2026-11-20) images versionnées dans git** (git = seul canal
  VM→Windows) avec les recettes. Place disque côté Nico non limitante (30 Go libres
  sur le PC actuel). Garde-fou retenu : poids du dépôt mesuré à chaque tronçon,
  alerte si le kit dépasse ~200 Mo (croissance de l'historique à chaque
  régénération, pas le disque) ; régénérer seulement ce qui a changé.

- **D3 (Nico 2026-11-20) option C** : kit d'organes précuits en splats assemblé
  sur les vrais segments DANS le jardin + PORTRAITS entiers (façon prototype
  tomate) pour encyclopédie / magazine / carnet (hors jeu, sans contrainte de
  fidélité segment par segment).

- **D4 (Nico 2026-11-20) TOUS les zooms en splats** (×0,5 → ×32) : le kit pixel
  des paliers bas (touffes 3-9 px, fleurons) est lui aussi généré depuis les
  recettes splat (réduction + quantification), plus de pièce dessinée à la règle.
  « Tous les graphismes » : périmètre au-delà des plantes → lot 3.
- **D5 (Nico) symptômes ×16** : TROUS (morsures, criblage de grêle) = variantes
  précuites de chaque feuille, 2-3 degrés ; COULEURS (nécrose, taches, givre) =
  palette / peint par-dessus, comme aujourd'hui.
- **D6 (Nico) portraits** : 3 par espèce (jeune · mûre en pleine saison · fin de
  cycle / hiver), dévoilés avec les 3 niveaux de fiche de l'encyclopédie ; le
  magazine montre le portrait mûr.

- **D7 (Nico 2026-11-20) programme « tout en splats »**, un sprint par famille,
  F5 entre chaque : (a) plantes [CE sprint] → (b) décor de lisière → (c) faune +
  champignons → (d) structures + maison → (e) sol, litière, eau, neige, météo →
  (f) icônes. Les sprints (b)-(f) sont à concevoir après le F5 de (a).
- **D8 (Nico) icônes de gestes = petits objets en splats** (trois quarts), sous
  réserve d'un F5 de lisibilité avant de remplacer les icônes actuelles (sprint f).

## Faits vérifiés (lot 2)
- Grammaire de la vue (`PlantRenderer.PortsFiches.cs`) : 7 ports (Rosette, Tige,
  Chaume, Tapis, Buisson, Rampante, Volubile) + arbres (Houppier/Arbres), 15 formes
  de feuille, 14 formes de tête (inflorescences), 8 marques. → bibliothèque de
  recettes = ce vocabulaire, PAS 54 recettes d'espèce.
- Paliers hauts (`PaliersHauts.cs`) : ×4 masses de feuillage + points ; ×8 organes
  (forme de feuille, fleur par famille, fruit globe) ; ×16 symptômes (morsures,
  grêle, nécrose, taches, givre) ; ×32 intime (nervures 2ᵉ, étamines, poils).
- Palette indexée (`visuals/PaletteIndexee.cs:14`) : pixel = n° de palette (R,G) +
  B = 128 | ton(0-4) << 4 | orientation(0-7 écran, 8 plat). Une pièce splat peut
  s'y couler : ton = volume (creux/ombre/base/clair), orientation = normale
  quantifiée (carte de normales ink-studio), palette posée à l'assemblage → UNE
  géométrie de feuille sert toutes les teintes (espèce, saison, santé, maturité).
- Panneaux existants : `world/EncyclopediePanel.cs`, `MagazinePanel.cs`,
  `CarnetPanel.cs`.

## §REPRISE
Lire `CLAUDE.md`, ce fichier, la conception, puis le kickoff du premier tronçon
« à faire » de la carte. Prochain : ① (`01_atelier_cuisson.md`).
