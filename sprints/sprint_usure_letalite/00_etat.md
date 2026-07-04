# Sprint « usure, pas punition » — létalité & compétition (D64 reframé)

> Carnet de bord VIVANT (skill /conception §0bis). Reconstructible à froid :
> lire `CLAUDE.md` + ce fichier suffit à reprendre sans le fil de conversation.

## Phase courante
**FIGÉ — prêt pour `/sprint-auto`.** Conception arbitrée + doc + 3 kickoffs écrits.
Doc : `docs/conception/CONCEPTION_USURE_LETALITE.md`. Tronçons :
`01_conflit_non_letal.md`, `02_cap_letalite_chronique.md`, `03_vue_godot.md`.

## Carte des tronçons (golden)
- **① Conflit non-létal** (`sim/engine/mortalite.py::_resoudre_conflits`) —
  golden **RE-FIGÉ** `a6c2f651…` → `a1c9c51f61c60fd6edf2500663ebcecfb9eac9d02a1120670f7ecf3fecd434cf` (mesuré).
- **② Cap létalité chronique** (`sim/effects/perturbations.py::apply_disturbances`)
  — cumul voies de fond borné à −1/tick ; golden neutre attendu, re-figeage
  localisé pré-autorisé.
- **③ Vue Godot & F5** (`grimpantes`, rendu `ombre` déjà en place) — golden intact.

## Le vrai bug (confirmé par repro, banc `grimpantes`, seed 42)
Le tournesol-hôte de la démo ③ ne meurt PAS d'herbivorie ni de mortalité de fond
(hypothèse D64 = **fausse** : `pressure = ravageur·0,012 × HERBIVORY_GAIN 0,20 =
0,0024 < seuil 0,005` → l'herbivorie ne tire jamais). Il meurt du **système de
conflit spatial** (`_resoudre_conflits` + `detect_conflicts` + `regress`) :

1. **Double comptage** : une même paire (Tournesol vs Haricot) génère DEUX
   `ConflictNotification` indépendants — un `foliar`, un `root` (deux couches
   d'empreinte). `_resoudre_conflits` les résout **séparément dans le même tick**,
   chacun appelant `loser.regress()`. Résultat w12 : jeune→semis (foliar) PUIS
   semis→health=0=mort (root) = **double régression en un tick**.
2. **`regress()` létal & brutal** : régresser = perdre un stade entier + reset
   `age_weeks` ; au stade 0, `regress()` met `health = 0` (mort sèche). Une
   **seule** relation de compétition peut donc tuer une plante saine (health 3).
   Viole philo #6 (usure, pas punition) et #1/#2 (malus DIRECT sur la plante, pas
   flux → contrainte → réponse émergente).
3. **« le plus jeune perd » + reset d'âge à la montée de stade** : `loser()` =
   `min(age_weeks)`. Or avancer d'un stade remet `age_weeks=0` → **grandir fait
   de toi le perdant**. Rétroaction perverse (le tournesol qui pousse à w11
   devient perdant des 2 conflits).

## Sous-problème connexe : stacking multi-voies dans un tick (théorique)
Même hors conflit, plusieurs `ReduceHealth` indépendants s'empilent sans plafond
dans `apply_disturbances` (herbivorie létale −2 + mortalité de fond ×0,7…). Sur
l'échelle **santé = entier 0-3**, un cumul peut passer 3→0 en un tick. « Usure
progressive » est inexprimable sur 4 crans. Racine commune avec le bug conflit :
**létalité multi-voies non bornée + granularité santé grossière**.

## Volet (b) de D64 — lisibilité des auxiliaires
Réel mais SÉPARÉ (perceptif, croise D31/D60, concerne la VUE Godot). À rattacher
au tronçon vue final (règle permanente : tout sprint finit par sa vue Godot), pas
au cœur moteur.

## Décisions arrêtées (Nico, AskUserQuestion 2026-07-04)
- **Q1 périmètre = REFRAME complet** de D64 (modèle compétition + létalité), pas
  patch étroit.
- **Q2 modèle = C (hybride)** : `detect_conflicts` reste une NOTIFICATION
  diégétique ; la résolution n'est plus létale (plus de `regress()`/kill). La mort
  du perdant émerge des voies de stress continu (ombrage LightField + ponction
  racinaire + sénescence).
- **Q3 = OUI cap de létalité chronique par tick + santé 0-3 conservée** (élargir
  l'échelle = hors périmètre).

## Ancrage FORT : le code viole une conception DÉJÀ figée
`docs/conception/CONCEPTION_COMPETITION_INTRAPLOT.md` (Nico 2026-06-13) tranche
**Q3 : « la mort du perdant ÉMERGE du déclin de santé (`_tick_senescence_health`)
— JAMAIS de mortalité verdict »**, et décrit `detect_conflicts` comme informatif
(« `resolved` n'est jamais positionné → aucune mortalité »). Or `_resoudre_conflits`
(mortalite.py) positionne `resolved` ET tue via `regress()`. **L'option C = ALIGNER
le code sur cette conception figée, pas inventer un modèle neuf.** `regress()`
n'est appelé QUE là (grep) → neutralisation propre.

## Mesure décisive (regress-kill neutralisé, banc grimpantes seed 42, 1 an)
- Tournesol (le plus HAUT) survit et prospère (240 cm, maturité) → gagne la lumière.
- Haricot (plus bas) : `shade_memory` monte 0,07→0,45→0,64→0,69 (> seuil 0,6),
  santé 3→2 à w52 → **dépérissement émergent par ombrage** = la mort de Q3.
- **AUCUN zombie** → le §2.3 (densité incluant les co-occupants) n'est PAS
  nécessaire (condition Q3 : « §2.3 seulement si embouteillage »). Sprint plus petit.

## Découpage proposé (à confirmer avant figer)
- **① Conflit non-létal** — `_resoudre_conflits` ne régresse/tue plus ; conflit =
  notification. Corrige d'un coup le double-comptage foliar+root, le `regress()`
  létal et le « plus jeune perd + reset d'âge » (tous rendus caducs). Golden
  **re-figé annoncé** (morts par conflit → déplacées vers stress/sénescence).
- **② Cap létalité chronique/tick** — cumul des voies de FOND {herbivorie,
  mortalité de fond, stress hydrique, carence lumineuse, maladie fongique} borné à
  −1 santé/tick par plante. Exempt : aigu/gated (fonte des semis, gel, grêle, vent).
  Tue le mort-éclair herbivorie-létale(−2)+fond(×0,7). Point : `apply_disturbances`
  avant `apply_mutations`. Golden **re-figé annoncé** (ticks où le cumul >−1).
- **③ Vue Godot** — signe de dépérissement progressif / étranglement émergent +
  lisibilité des auxiliaires (volet (b) de D64, croise D31/D60) + banc grimpantes
  rejoué F5 (hôte survit, se fait ombrer, plus de mort-éclair). Golden intact.

## §2.3 en réserve (NON implémenté)
Si un jour deux compétiteurs de MÊME hauteur zombifient (embouteillage), le remède
est déjà conçu (CONCEPTION_COMPETITION_INTRAPLOT §2.3 Q4 : inclure les co-occupants
dans `_local_density`). Hors périmètre ici (mesure = pas d'embouteillage).

## Coût perf
Diagnostic seul pour l'instant. Toute option reste O(plantes) local, sans
nouvelle passe spatiale globale → budget ≤ +10 %/tick tenable.

## §REPRISE
**Conception FIGÉE et commitée (2026-07-04).** Rien à décider : lancer
`/sprint-auto sprint_usure_letalite`. Il exécute ① (golden re-figé `a1c9c51f…`,
valeur pré-mesurée dans `01_*.md`) → ② (cap chronique, golden neutre attendu,
re-figeage localisé pré-autorisé) → ③ (vue Godot/F5, golden intact). Après clôture :
**F5 Nico** sur le banc `grimpantes` (hôte survit, dominé s'ombre lentement).
Doc de référence : `docs/conception/CONCEPTION_USURE_LETALITE.md`. Suite (séparée) :
ouvrir une `/conception` pour **D65 luxuriance/stratification**.
