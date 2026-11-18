# Sprint PLANTE VIVANTE (D140 G, sprint A) — état

> Conception FIGÉE le 2026-11-18 : `docs/vegetal/sante/conception_plante_vivante.md`
> (à lire en entier). Suite : `sprints/vegetal/sante/sprint_stress_au_bilan/` (B).
> Ce sprint débloque `sprints/vegetal/genetique/sprint_depart_jardin/` (reprise au ④).

## But
Les plantes n'ont plus de PV : elles vivent d'un bilan carbone (photosynthèse −
entretien − part racinaire), tiennent un `feuillage` et des `reserves`, meurent de
famine ou de destruction. Herbivorie par atteinte (la limace ne mange pas le
chêne), souches à réserve finie (fin de la cascade de rejets), ouverture du monde
`full` à mortalité partielle.

## Décisions clés (Nico, 2026-11-18)
- Règle de dégât actuelle aberrante → refonte des dégâts, des cibles de chaque
  ravageur et de leurs effets. Mesuré : la faune n'est pas en cause (pré-rouler
  la faune AGGRAVE : 130/136 morts vs 121).
- Plantes sans PV ; tout le vivant végétal passe au bilan (sprints A puis B).
- `vitalite` = lecture dérivée (réserves × feuillage) ; écrire 0 = destruction.
- Plus de mort ni de guérison au sort ; causes de mort : famine, destruction,
  défaillance hydraulique, racines perdues, fin de cycle, vieillesse (§5).
- Unité = semaine d'entretien ; 3 paramètres d'espèce neufs (`reserve_semaines`,
  `photo_max`, `cout_feuillage`) dans `plants/physiologie.py` ; tout le reste
  réutilisé (plage thermique D139, tolérances, gènes de feuille).
- Critère d'ouverture (`full`, seed 42, s10→s30) : 0 arbre posé mort ; ≤ 25 %
  d'herbacées posées mortes hors fin de cycle ; ≤ 4 rejets par arbre mort.

## Golden
Départ `25671775…` (fin du ③ de `sprint_depart_jardin`). ① **INTACT** ·
② **RE-FIGÉ annoncé** (modèle de vie) · ③ **RE-FIGÉ annoncé** (herbivorie seule,
preuve par neutralisation) · ④ intact attendu · ⑤ ⑥ **INTACT**.
Perf de référence à mesurer au ① (tick `full` s10-s30, commit de départ).

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_socle_bilan.md` — bilan en ombre + paramètres 52 espèces + banc | à faire |
| ② | `02_bascule_vie.md` — vitalité dérivée, famine, `erode` = tissus | à faire |
| ③ | `03_herbivorie_atteinte.md` — chaque ravageur mange ce qu'il atteint | à faire |
| ④ | `04_souches_reserve.md` — réserve de souche, rejets sans souche propre | à faire |
| ⑤ | `05_ouverture_mesure.md` — critères `full` s10→s30 + âge de la chronique | à faire |
| ⑥ | `06_vue_banc.md` — pont, rendu du feuillage, info-bulle, banc, clôture | à faire |

## Diagnostic d'origine (2026-11-18, seed 42, n=1 par cas)
Ouverture s10 → morts des 136 posées à s21 : tel quel 121 ; faune pré-roulée 130 ;
prédateurs seuls pré-roulés 97 ; `stress_memory` amorcée 0,12 → 49. Semis de
chêne : vagues de rejets ×3 (9 → 27 → 75 → 153, s20-s32), toutes à < 1,5 m d'un
arbre mort. Scripts jetables : instrumenter `herbivory_pressure` et compter les
naissances par espèce/semaine via `SimServer().cmd_init({"config":"full","seed":42})`
puis `engine.tick_semaine()`.

## REPRISE
Lire `CLAUDE.md`, ce fichier, la conception, puis le kickoff du premier tronçon
« à faire ». Lancer : `/sprint-auto sprint_plante_vivante`.
