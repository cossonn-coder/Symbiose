# 00_etat — Sprint GRIMPANTES (mécanique moteur de la grimpe, D49)

> Carnet de bord VIVANT (skill /conception §0bis). Phase A en cours = challenge,
> RIEN n'est figé. Reprise à froid : lire `CLAUDE.md` + ce fichier.

## Sujet
Volet A SEUL de D49 : une plante grimpante cherche un SUPPORT, s'y accroche,
grimpe pour de vrai → hauteur → accès lumière (LightField). L'avantage doit
ÉMERGER d'une géométrie (philo #2), jamais d'un bonus direct. Couche A Python
(vérité) AVANT tout rendu C#. Rendu de vrille (CONCEPTION_RENDU_FEUILLAGE §7/E6)
HORS périmètre. Rampantes/traçantes + violettes = HORS (reporté D62).

## Vérifications CODE faites en phase A (ancrage)
1. **Bean (Haricot) est `procedural_growth = True`** (Fabaceae, `species/cultivees.py:42`,
   Bean l.136). Sa hauteur = `footprint_value("height")` = **max(z) des extrémités
   de segments** (`base/instance.py:176-204`). Sa canopée = extension horizontale
   max. → la hauteur est DÉJÀ émergente de la géométrie des segments, PAS un
   scalaire. Les `canopy_height=150/200` des stades grimpante sont des potentiels,
   pas la hauteur lue.
2. **Bean EST dans le golden** (`tests/test_golden.py:76 add_plant(Bean,4,2)`).
   → toute modif de sa croissance RE-FIGE le golden (smoke test).
3. **L'apex a déjà un plancher de verticalité** `MIN_APEX_Z` dans
   `_phototropic_bias` (`growth/geometrie.py:88-115`) : si la composante z tombe
   sous le plancher, l'apex est redressé « jamais à plat ». C'est LE hook naturel
   du port grimpant : moduler ce plancher selon l'état de support.
4. **`current_height` est lu par PLUSIEURS consommateurs** hors lumière :
   `container.py:209` (occupation pot), `engine/decompo.py:85` (nécromasse
   abscission), `effects/perturbations.py:34,382` (nécromasse + establishment),
   `fields/abri.py:64` (abri faune), sérialisation pont. → si « hauteur effective »
   DIVERGE de la biomasse réelle, ces consommateurs sous-comptent (une grimpante
   affalée a une grande biomasse mais une faible hauteur debout).
5. **StakeSlot ≠ tuteur de grimpe** (`world/tile.py:18-56`). C'est le porte-
   **rondelles** du système MTG (0-9 tiges × max 3 rondelles homogènes, `is_bonus`).
   AUCUNE position, AUCUNE hauteur. → la prémisse du brief et de D49 (« 10 tuteurs/
   tuile réutilisables ») est FAUSSE. Un tuteur/treillis/pergola de grimpe est une
   STRUCTURE NEUVE (position + hauteur), proche des bac/pile posables (⑤ décompo).
6. **Mur maison** existe avec hauteur + albédo espalier (`world/building.py:31-32`,
   height 600, wall_albedo 0.35). Support « mur » réel et gratuit.

## Décisions ARRÊTÉES (Nico, batch 1)
- **A1 = GÉOMÉTRIQUE.** La hauteur émerge de la géométrie des segments : au-delà
  de `hauteur_autoportante` sans support, l'apex retombe (plancher de verticalité
  effondré → `max_z` bas + étalement horizontal = affalement). Accroché → biais
  d'apex vers l'axe du support → grimpe. `height_at`/`current_height` restent la
  vraie `max_z`, JAMAIS de clamp/divergence → consommateurs (nécromasse, abri,
  pot) justes. Réutilise `_phototropic_bias` + `MIN_APEX_Z` (growth/geometrie).
- **A2 = PANOPLIE COMPLÈTE.** Supports posables NEUFS : tuteur + treillis +
  pergola + geste `palisser`, PLUS le mur maison (existe) et la plante-hôte
  vivante (émergent). StakeSlot NON réutilisé (c'est le porte-rondelles MTG).
- **A3 = DÉMO RÉDUITE.** 2-3 plantes pour prouver la mécanique ; le reste du
  catalogue → D26.

## Micro-choix Claude (tranchés)
- **mode_grimpe** = 3 valeurs `crampon` / `vrille_volubile` / `sarmenteux`
  (gouverne QUELS supports sont valides).
- **Plantes démo** = HARICOT (déjà là, `vrille_volubile`, coût 0) + LIERRE
  (`crampon`, monte au mur nu) + JASMIN (`sarmenteux`, démontre `palisser`).
  → couvre les 3 modes avec 2 espèces neuves. GLYCINE écartée (redondante avec
  haricot : Fabaceae + vrille_volubile déjà couverts) → part en D26 avec
  courge/kiwi/vigne/akébia.
- **Étranglement** par ombre du LightField : émergent, pas de règle dédiée, assumé.
- **Verse/vent** : attaché → résistance ; tuteur ne casse PAS (écarté).
- **Vue Godot** = INCLUSE (tronçon ⑥, décision Nico 2026-07-03) : rattache le
  **rendu de vrille** différé (`CONCEPTION_RENDU_FEUILLAGE §7/E6`) + rendu des
  supports. Bonus décision A : la vue suit la géométrie GRATUITEMENT (les
  segments montent/s'affalent déjà dans le snapshot → PlantRenderer les dessine).

## RÈGLE PERMANENTE (Nico 2026-07-03)
La **vue Godot est TOUJOURS le dernier tronçon** de chaque sprint (ici et pour
tous les prochains). Gravée en mémoire + skill `/conception` (phase B). Un sprint
moteur sans son tronçon vue est incomplet.

## Découpage FIGÉ (6 tronçons, perf-first)
- ① traits (`hauteur_autoportante`, `mode_grimpe`, état `support`) + affalement
  géométrique SANS support → **golden RE-FIGÉ maîtrisé** : le haricot s'affale
  (`growth_factor`/`shade_memory` bougent), `a6c2f651…` → nouveau hash annoncé.
- ② structures-support posables (tuteur/treillis/pergola) + mur + recherche
  d'accroche bornée + grimpe → golden NEUTRE vs ① (haricot=vrille_volubile ne
  peut PAS s'accrocher au mur nu, aucun tuteur posé dans le golden).
- ③ plante-hôte vivante comme support + détachement à la mort de l'hôte +
  étranglement émergent → golden NEUTRE (Bean(4,2) : aucune haute à portée ;
  Sunflower en (0,1) hors rayon — vérifié).
- ④ gestes joueur (`poser_tuteur/treillis/pergola`, `palisser`) + maîtrise
  (outil `tuteur`, technique `palissage`) + résistance verse → event-driven,
  golden INTACT.
- ⑤ catalogue lierre + jasmin + 5 voix chacune + SOIL_SIGNATURE → golden NEUTRE.
- ⑥ **vue Godot** : rendu supports + accroche + vrilles (§7 feuillage) + pont
  (supports au snapshot, bump ENGINE_VERSION) + **banc d'essai `grimpantes`**
  (Nico 2026-07-03 : haricot À CÔTÉ du tournesol pour la grimpe sur hôte, champ
  tomates/basilic/poivrons au sud, départ début printemps=automatique wiy1) →
  golden INTACT (vue pure + banc jamais monté pour smoke/full).

## §REPRISE
CONCEPTION FIGÉE 2026-07-03. Doc = `docs/conception/CONCEPTION_GRIMPANTES.md`.
6 kickoffs `01→06` écrits. Prêt pour `/sprint-auto sprint_grimpantes`.
Golden : re-figé au ① SEUL (annoncé), NEUTRE/INTACT ②→⑥.
