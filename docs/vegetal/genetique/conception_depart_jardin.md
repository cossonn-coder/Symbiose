# Conception — Départ du jardin (D140 A+B+C)

> Figée le 2026-11-18 (`/conception`, arbitrages de Nico). Sprint :
> `sprints/vegetal/genetique/sprint_depart_jardin/`. Trèfle envahissant (D140 D) et
> vue pluie / Ctrl+molette (D140 E-F) : **hors périmètre**.

## 1. Pourquoi
F5 du 2026-11-18 (`sprint_caracteres_vivants`) : à l'ouverture du monde `full`, les 68
cultivées repiquées en semaine 1 (≈ 20 mars) meurent en deux semaines. Les nuits du
seed 42 sont réalistes (−0,4 °C en s1, gelée tardive −2,8 °C en s4, > 7 °C seulement à
partir de s10) : **c'est le scénario qui est faux**, pas le moteur. S'y ajoutent des
données thermiques physiquement impossibles (tomate qui gèle à +2,8 °C), une mort par
froid absente de la chronique, le pâturin traité en plante à insectes, et des gènes
qui coûtent à des espèces qui ne les expriment pas.

## 2. Décisions (Nico, 2026-11-18)

### A — Pâturin réaliste
*Poa annua* est une graminée pollinisée par le vent et **surtout autogame** : on lui
donne le mode de pollinisation « vent » et un neutre d'`autofecondation` élevé
(≈ 0,9, comme les autogames du catalogue).

### B — Un gène non exprimé ne coûte rien
`cout_genetique` ne compte l'excès d'un caractère coûteux **que si l'espèce l'exprime**,
c'est-à-dire si au moins une mécanique le lit POUR elle (ex. `nectar` chez une
anémophile, `fixation_azote` hors fixatrices, `allelopathie` chez une espèce sans
exsudat, `limite_froid` chez une espèce non sensible au froid sans gel). Le gène reste
**porté et hérité** (variation cryptique, réaliste) : seul son prix disparaît.

### C — Départ du jardin
1. **Ouverture du monde `full` juste après les saints de glace** : semaine 10 du
   calendrier unique (≈ 22 mai ; la fenêtre des gelées tardives de `sim/weather.py`
   couvre s2-s9). Le golden (smoke) garde sa semaine 1.
2. **Au moins une plante MATURE de chaque espèce du catalogue** (52) dans le jardin à
   l'ouverture, chacune dans une tuile à sa niche. **Arbres mûrs** = âge de LEUR
   première fructification (`maturity_years`), structure pré-croissante de cet âge
   (chêne ≈ 25 ans, hêtre ≈ 30 ans : ils occupent une tuile, c'est le réel).
   Garde-fou permanent : un test vérifie catalogue ⊂ monde `full` (toute espèce
   ajoutée doit y entrer).
3. **Semis** : existe (`planter` → `GrainEnAttente`, levée sur `bell(T_sol, t_germ_opt,
   t_germ_tol)`). À l'ouverture, quelques graines déjà semées en terre.
4. **Semis d'intérieur** : un pot posé DANS la maison vit au chaud (pas de gel, pas de
   pluie) mais à la lumière d'une fenêtre ; trop longtemps dedans, le plant file
   (étiolement émergent de la faible lumière, pas de malus direct). À l'ouverture,
   quelques pots de tendres dans la maison.
5. **Repiquage** : geste neuf `repiquer` — sort la plante du pot et la met en pleine
   terre avec sa motte. Choc de repiquage = croissance ralentie quelques semaines,
   plus fort si les racines étaient à l'étroit (volume du pot). **Différé** : c'est le
   joueur qui choisit le moment ; l'automate repique quand les nuits passent
   au-dessus de la limite de froid de l'espèce.
6. **Données thermiques** : rien ne gèle au-dessus de ≈ −0,5 °C (point de congélation
   de la sève) — borne physique sur `lim_gel`, quelle que soit la dérive génétique ;
   tournesol non sensible au froid sans gel ; audit des tendres (tomate, basilic,
   poivron, haricot, courgette, tournesol). Le rythme du froid sans gel reste
   (`FROID_LESION_K`) : à 0-2 °C, une semaine tue réellement un jeune plant tendre.
7. **Mort par froid consignée** : cause `froid` / `gel` dans la chronique, plus de
   `non_consignee`.

## 3. Philo
#1/#2 : aucun bonus — la maison est un milieu (chaleur, peu de lumière), le choc de
repiquage est une conséquence physique (racines coupées), l'étiolement émerge de la
lumière. #3 : tout déterministe. #6 : on apprend le calendrier par le gel, pas par une
règle. Pas de béquille : on ne protège pas les tendres, on les ouvre au bon moment.

## 4. Coût perf
Le monde `full` passe de 15 à ≥ 52 espèces et reçoit des arbres de 25-30 ans : la
lumière (1er poste) grossit. À **mesurer** au tronçon ③ (tick s10-s30 avant/après,
init comprise) ; signaler au-delà de +30 %. Les autres tronçons sont event-driven
(gestes, pots) ou de la donnée : ≤ +2 %.

## 5. Tronçons
① pâturin + gènes muets (golden re-figé) · ② froid des tendres + chronique (re-figé) ·
③ monde `full` complet (intact) · ④ pot dans la maison + `repiquer` (intact) ·
⑤ automate : repiquage différé (intact) · ⑥ vue Godot + banc (intact).
