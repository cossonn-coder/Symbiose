# Sprint « usure, pas punition » — létalité & compétition (D64 reframé)

> Carnet de bord VIVANT (skill /conception §0bis). Reconstructible à froid :
> lire `CLAUDE.md` + ce fichier suffit à reprendre sans le fil de conversation.

## Phase courante
**SPRINT CLOS (2026-07-04, `/sprint-auto`).** ①②③ faits et commités (532e50c,
9a7973c, 7c07788) ; journal 98, DETTE D64 ✅, BACKLOG à jour. Golden final
`15073be1…`. Reste à Nico : **F5 de validation** (cf. §F5 et §REPRISE).
Doc : `docs/conception/CONCEPTION_USURE_LETALITE.md`. Tronçons :
`01_conflit_non_letal.md`, `02_cap_letalite_chronique.md`, `03_vue_godot.md`.

## Carte des tronçons (golden)
- **① Conflit non-létal** (`sim/engine/mortalite.py::_resoudre_conflits`) —
  **FAIT (code)** le 2026-07-04. Résolution non-létale : conflit = notification
  pure (`detect_conflicts` + log `⚠ Conflit`), plus AUCUN verdict — `regress()`,
  `resolved`-mort et `deposer_mort(loser,…)` retirés de ce chemin. `resolved` ne
  sert plus qu'à ÉLAGUER un conflit périmé (plante morte OU chevauchement disparu),
  via nouvelle statique `_conflit_perime` (lecture seule, ne touche aucune plante).
  Repro OK : Tournesol@(2,2) du banc `grimpantes` (départ w14, +30 sem) SURVIT
  (mature, plus de mort w12) ; Haricot décline émergent, aucun zombie.
  `test_competition` 14/14, `test_senescence` PASS.
  - **✅ GOLDEN RE-FIGÉ `007be1393f5c544ba6c6c5aaf1f21ec0f0d47cf6d0956b01439c6b58749b714c`**
    (2026-07-04, orchestrateur `/sprint-auto`). Divergence avec le hash pré-mesuré
    du kickoff `a1c9c51f…` **investiguée et tranchée par PREUVE** : reconstruit le
    variant de l'auteur du kickoff (garder la ligne de log `↓ … (conflit)` sans le
    `regress()`) → il redonne **exactement `a1c9c51f…`**. Donc le digest d'état des
    plantes est **IDENTIQUE** entre les deux (les deux suppriment le seul geste qui
    mutait l'état, le regress-kill) ; la seule différence est **une ligne de log
    fantôme** (le golden hashe log+digest, cf. `test_golden.py`). `a1c9c51f…`
    laissait un log annonçant une régression qui n'a plus lieu (mensonger, contre la
    prose du kickoff). `007be139…` est la version **honnête et fidèle** → figée.
    La condition STOP du kickoff (« hash différent ⇒ effet de bord sur l'état ») est
    donc FALSIFIÉE : aucun effet de bord, log seul. `regress()` désormais INUTILISÉ
    (conservé, règle « ne jamais jeter de code »).
- **② Cap létalité chronique** (`sim/effects/perturbations.py::apply_disturbances`)
  — **FAIT (code)** le 2026-07-04. Ventilation des mutations en DEUX flux :
  `acute_muts` (fonte des semis, INTACT) vs `chronic_muts` (herbivorie + fongique +
  sécheresse + ombre + mortalité de fond). Nouvelle statique `_cap_chronique` :
  pour chaque plante, ne garde QU'UN `ReduceHealth` d'`amount=1` (le premier, en
  privilégiant un coup à `cause` non vide → marque foliaire préservée). Ordre
  d'appel des fonctions INCHANGÉ (tirages `_hash_noise` corrélés) ; seule la
  ventilation change. Une plante saine (health 3) tient ≥ 3 ticks de fond → usure
  (philo #6). Aigu (fonte) reste décisif. Zéro RNG. Fichier 219 LDC pur (🟢).
  Suites : `test_competition` 14/14, `test_senescence` PASS.
  - **✅ GOLDEN RE-FIGÉ `15073be1a80bb2aedd686bdf09fe96e96b3979fa093fa494628f3ce4de8d6d62`**
    (2026-07-04). Divergence **LOCALISÉE et EXPLIQUÉE** (re-figeage pré-autorisé par
    le kickoff § « re-figeage LOCALISÉ »). Preuve par diff baseline↔capé
    (`_cap_chronique` = identité vs actif) : TOUTES les divergences dérivent de
    coups chroniques dépassant −1/tick — (a) bites herbivorie LÉTALE `−2` ramenées
    à `−1` (ex. Bourse-à-pasteur@(1,6), Pissenlit@(4,2), Minette@(3,3)) ; (b) deux
    voies chroniques empilées dans un tick `−1`+`−1`=`−2` ramenées à `−1` (ex.
    Minette@(2,4) herbivorie+carence lumineuse). Le reste = CASCADE aval (des
    adventices annuelles qui survivent un peu plus, meurent ensuite de sénescence
    annuelle/vent/sécheresse à d'autres semaines ; comptes de plantes 11→12,
    om_fresh/exsudats/humidité décalés de quelques millièmes). AUCUN système hors
    périmètre ne diverge, jamais le cœur du jardin ni les pérennes. Exactement le
    mort-éclair visé (philo #6).
- **③ Vue Godot & F5** (`grimpantes`, rendu `ombre` déjà en place) — **FAIT (vérif +
  aucune modif)** le 2026-07-04. Chaîne de données VÉRIFIÉE de bout en bout sur
  `grimpantes` (seed `0x5AB1057E`, départ w9, +44 sem) via le serializer RÉEL du pont
  (`SerializeMixin._snapshot`) : le **tournesol-hôte@(2,2) SURVIT** (dead=False toute
  l'année, atteint 225 cm → il gagne la lumière) et le **haricot@(2,3) porte un
  `leaf_symptoms` `cause="ombre"` d'intensité CROISSANTE** (apparaît ~w37 à 0.038,
  monte régulièrement → 0.17 à w53). Plus AUCUNE mort-éclair w12. C'est l'usure
  lisible visée (philo #6). Mapping C# VÉRIFIÉ complet en lecture : `PlantRenderer.cs`
  (`SetSymptoms`/`ColorantTints`) et `PlantRenderer.Organs.cs` mappent DÉJÀ `ombre`
  (teinte `SymOmbre` + réduction calotte `_ombre`), `senescence` (`SymSenescence`),
  `secheresse` (teinte + affaissement `_drought`) — **aucune cause de dépérissement
  lent n'est orpheline** → conformément au kickoff (« aucun changement si tout est
  déjà mappé ») **ZÉRO C# touché**. Volet (b) D64 (lisibilité auxiliaires) : DÉJÀ
  noté « subsumé par D60 » dans la ligne D64 de DETTE.md → rien à ajouter.
  - **✅ GOLDEN INTACT `15073be1a80bb2aedd686bdf09fe96e96b3979fa093fa494628f3ce4de8d6d62`**
    (tranche VUE / lecture pure, aucun moteur touché — confirmé par `python3 -m
    tests.test_golden` PASS).

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

## §F5 — protocole d'observation pour Nico (banc `grimpantes`)
Objectif : VOIR à l'écran que « l'usure remplace la punition » sur le banc.
1. Lancer Godot (F5), sélecteur de banc → `grimpantes` (= `init config="grimpantes"`,
   départ mi-printemps w9 câblé par `BANC_WEEK_DEPART`). Seed par défaut du pont.
2. Laisser tourner ~1 an simulé (jusqu'à ~w52). Cibler la tuile GRIMPE, coin haut-
   gauche : le **tournesol@(2,2)** et le **haricot@(2,3)** collés l'un à l'autre.
3. À VÉRIFIER (ce que la VM a déjà prouvé côté données) :
   - **Le tournesol-hôte reste VIVANT toute l'année** et monte haut (~225 cm),
     coiffant le haricot. **PLUS de disparition brutale vers w12** (l'ancienne
     mort-éclair de conflit spatial est corrigée par ① — c'est LE point de non-
     régression du sprint).
   - **Le haricot voisin JAUNIT/DÉLAVE lentement** sous l'ombre du tournesol en
     fin de saison (limbe pâle anémié `SymOmbre` + feuillage un peu plus terne au
     nord, calotte éclairée réduite). Dépérissement PROGRESSIF, jamais une mort
     sèche instantanée. L'intensité `ombre` reste modérée (~0.17 à w52) : le signe
     est SUBTIL — regarder de près, comparer au haricot palissé (5,2) resté en
     pleine lumière. Si Nico juge le signe trop faible pour être lu, c'est un
     réglage de calibrage (seuil/amplitude), PAS un bug de chaîne (les données
     sont bien là) → à verser en dette, pas à corriger dans ce sprint.
4. Les 3 autres accroches (tuteur 5,2 / treillis 5,5 / mur lierre) et le potager sud
   restent des témoins de contexte — rien de neuf à valider dessus ici.

## §REPRISE
**SPRINT PRÊT À CLORE (2026-07-04).** Les 3 tronçons ①②③ sont FAITS côté VM.
① (conflit non-létal, golden `007be139…`) commité. ② (cap létalité chronique,
golden re-figé `15073be1…`) fait code. ③ (vue) = **vérification pure, ZÉRO code
touché** : chaîne de données prouvée de bout en bout (hôte survit + `ombre`
croissant sur le dominé), mapping C# déjà complet, golden **INTACT** `15073be1…`.
**Reste à Nico** : (a) commit du bundle ②+③ non commité ; (b) **F5 de validation**
sur le banc `grimpantes` selon §F5 ci-dessus (hôte survit, dominé s'ombre lentement,
plus de mort-éclair). Rien d'autre à faire en dev sur ce sprint.
Suite (séparée) : ouvrir une `/conception` pour **D65 luxuriance/stratification**.

--- (historique tronçons ①② ci-dessous) ---
**① CLOS et commité (2026-07-04).** `_resoudre_conflits` non-létal, golden re-figé
`007be139…` (divergence avec `a1c9c51f…` du kickoff tranchée par preuve : log
fantôme seul, état plantes identique — cf. Carte des tronçons). Suites ciblées
vertes, repro banc OK.
**② FAIT (code, PAS ENCORE COMMITÉ — Nico commit) (2026-07-04).** Cap létalité
chronique dans `sim/effects/perturbations.py` (`_cap_chronique` + ventilation
aigu/chronique). Golden **re-figé** `15073be1a80bb2aedd686bdf09fe96e96b3979fa093fa494628f3ce4de8d6d62`
(divergence localisée/expliquée = bites `−2`→`−1` et cumuls chroniques `−2`→`−1`,
+ cascade aval sur adventices ; preuve par diff baseline↔capé). `test_competition`
14/14, `test_senescence` PASS. C# non concerné.
**Reprendre à ③** (vue Godot/F5, golden intact — signe de dépérissement progressif /
étranglement + lisibilité auxiliaires volet (b) D64 + mapping couleur/texture `ombre`
côté `PlantRenderer` C# reporté du sprint stress chronique + banc `grimpantes`
rejoué F5). Après clôture : **F5 Nico** sur le banc `grimpantes` (hôte survit,
dominé s'ombre lentement, plus de mort-éclair).
Doc de référence : `docs/conception/CONCEPTION_USURE_LETALITE.md`. Suite (séparée) :
ouvrir une `/conception` pour **D65 luxuriance/stratification**.
