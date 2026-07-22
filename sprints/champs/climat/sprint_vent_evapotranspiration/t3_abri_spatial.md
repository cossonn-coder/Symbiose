# Tronçon ③ — Champ d'abri spatial (brise-vent + venturi)

> Kickoff autonome. Design : `docs/champs/climat/conception_vent_evapotranspiration.md` **§4** + **§2.4**
> + **§7B** (perf). **SEUL morceau réellement coûteux du sprint — À BUDGÉTER.**
> Re-figeage golden probable. **Reportable en dette** si la mesure dérape, sans
> bloquer la suite.

## But
Spatialiser le vent : un `GridField` `eco.vent` (force locale/plot) calculé depuis
la masse d'air (①) **modulée par la géométrie d'abri** :
- **abri** : `vent_local` réduit dans le **sillage** d'un obstacle (mur maison,
  structure posée, haie = plante haute), portée ∝ hauteur (≈ 10× la hauteur).
- **venturi** : `vent_local` **accéléré** dans les goulets entre obstacles (brise de
  fin de journée §2.2).
- une **haie** (plantes hautes alignées) = brise-vent émergent (philo #1).

## Contrainte perf #1 (OBLIGATOIRE, §7B)
La capsule d'abri = **la même machinerie** que `_point_in_capsule` (déjà 35 % du
tick). Donc :
1. **Mutualiser avec le LightField** : capsule d'ombre + capsule d'abri = une seule
   passe géométrique orientée (deux sorties), pas deux passes. Le scatter du tronçon
   ⓪ s'applique aussi à l'abri.
2. **CACHE** : `eco.vent` ne dépend que de (obstacles, direction du vent). Obstacles
   quasi statiques + direction = marche lente → **recalculer seulement quand la
   direction franchit un pas angulaire OU qu'un obstacle change**. Régime permanent
   = coût ≈ 0.
3. **Mesurer ms/tick avant/après** sur le monde complet + run long. Si l'ajout
   dépasse le budget +X % (fixé au tronçon ⓪) sans pouvoir être caché → **reporter
   ③ en dette** (D37 partiel) et continuer aux tronçons ④+. ① et ② tiennent seuls.

Brancher aussi le **wind chill** (§5.5) : `−WINDCHILL_COEF·vent_local` dans
`t_min_nuit_at` (un abri réchauffe la nuit). Une fois `eco.vent` spatialisé,
l'évaporation (②) lit `vent_local[r,c]` au lieu de la masse d'air uniforme.

## Critères de succès
- `eco.vent` spatialisé cohérent (abri sous le vent, venturi dans les goulets),
  testé (`test_vent` étendu : un obstacle réduit le vent dans son sillage selon la
  direction).
- **Budget perf respecté** (cache effectif : ms/tick stable en régime de direction
  constante) — sinon report documenté.
- Golden re-figé (annoncé) si le branchement évaporation/wind chill bouge l'eau/thermie.
- Suites : `test_eau`, `test_rosee`, `test_stress_chronique`, `test_sim_server`.

## Clôture
MAJ `00_etat.md` (③ ✅ OU ③ reporté en dette + raison perf). Commit. `/clear`.
Lancer `t4_thigmomorphogenese.md`.
