# sprint_reliquats_plantes — état du sprint

**Conception FIGÉE le 2026-11-25** (`/conception`, Nico : « ok allons y ») →
`docs/rendu/splatting/conception_reliquats_plantes.md`. **S1 d'une séquence de 3 sprints**
pour un style homogène avant le F5 complet de Nico : S1 reliquats des plantes → S2 arbres
(rendu lissé, écorce cuite, brins de graminées, portraits d'arbres ; `/conception` à faire)
→ S3 lisière (b) + écran de chargement en mycélium (g) + liste F5 exhaustive.
**Prêt pour `/sprint-auto sprint_reliquats_plantes`.**
Golden : **`bce813af…` INTACT à tous les tronçons** (vue + outillage, `data/code/` jamais modifié).

## Carte des tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_memoire_x32.md` — budget de précuisson 1 Go, plafonds relevés, ×32 cuit | à faire |
| ② | `02_classes_taille.md` — 3 tailles par recette, correction du √2, recuisson | à faire |
| ③ | `03_details_cuits.md` — inventaire + tous les détails en couches + sonde ×64 | à faire |
| ④ | `04_recettes_neuves.md` — trèfle 3/4, thym, lavande, fétuque, anthères, cœur des fleurons | à faire |
| ⑤ | `05_portraits.md` — portraits ratés hors arbres + baies de la myrtille | à faire |
| ⑥ | `06_revue_paliers.md` — revue ×0,5→×32, finitions, section F5, clôture | à faire |

## Décisions (Nico, 2026-11-25)
- E1 Trois sprints en séquence, sans F5 entre eux.
- E2 (S3) Écran de chargement : philo #5 = pendant le jeu seulement ; le logo est un filament de mycélium qui s'arborise en splats et sert de barre de progression.
- E3/E4 (S2) Le bois est à reprendre, sans aucun joint visible, angles arrondis. RENDU SEUL : `sim/growth.py` n'est pas touché. Piste : tube lissé à travers les nœuds + bande d'écorce cuite par essence.
- E5 Précuisson maximale. E6 Budget mémoire de précuisson de 1 Go.
- E7 ×32 : relever les plafonds sous ce budget (pas de dessin de codes en direct).
- E8 3 classes de taille par recette + correction du √2.
- E9 Les brins et rubans des graminées passent en S2 (ruban lissé + texture cuite).
- E10 Tous les détails des feuilles présents quand on zoome, beaux à chaque palier.
- ×64 : sonde au ③ ; **proof of concept chanvre ×64 après S1-S3** (BACKLOG). Il faudra recuire par palier aussi le sol, la faune, le paillage, etc. (familles c-e).

## Fait vérifié
×32 (capture VM du 2026-11-25, n=1 par cas) : tomate en splats ; tournesol en dessin
direct, ni `[Splats]` ni `[Cuisson]` au journal (refus des plafonds de `PlantBaker`).
Détails : conception §4. Captures de la conception non versionnées (scratchpad).

## Règles du sprint
- Captures VM : `tools/capture_vm.sh` (lues au Read avant de conclure) ; charge (`uptime`) vérifiée avant toute mesure de temps.
- Poids `assets/splats/` mesuré à chaque tronçon ; alerte et arrêt au-delà de 200 Mo.
- Interdits : `test_epaisseur_500ans` ; DeepSeek dans les sous-agents ; `data/code/` ; `tools/splat/vendor/`.

## Compte rendu des tronçons
(rempli par chaque tronçon : fait, mesures, chemins des planches et captures)

## F5 (à remplir par les tronçons, consolidé au ⑥)

## §REPRISE
Lire `CLAUDE.md`, ce fichier, la conception, puis le kickoff du premier tronçon « à faire ».
Outils hérités du sprint (a) : `SplatPlanches.Trouver` / `LireImage`, `PoserPieceSplat`,
`PoserPieceFeuille`, `PoserOrganeSplat`, `PoserFoliolesSplat`, `TouffeGerbe`,
`tools/splat/cuire.js`, `cuire_portraits.js`.
