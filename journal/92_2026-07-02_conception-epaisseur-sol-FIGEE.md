# 2026-07-02 — Conception ÉPAISSEUR DE SOL (D57) — FIGÉE

> `/conception d57`, phase B (conception SEULE, aucun code moteur écrit).
> Doc : `docs/conception/CONCEPTION_EPAISSEUR_SOL.md`. Sprint prêt :
> `sprints/sprint_epaisseur_sol/` (00_etat + 01a/01b/02). Prêt pour `/sprint-auto`.

## Sujet

D57 (Nico 2026-07-02, F5 S5+S11) : la matière organique qui tombe doit **épaissir
le sol visiblement**, le tassement + la décompo le rognent, l'humus stable
persiste et s'accumule sur les ans → le sol **monte/descend**. Champ à **effet
écologique**, pas une dérivée d'affichage.

## Décisions arbitrées (3 questions à Nico, recos toutes retenues)

1. **Loi = RELAXATION vers cible bulk-density** (pas accumulateur, pas dérivée
   pure). `cible = E_fresh·om_fresh_eff(age) + E_active·om_active + E_stable·om_stable`,
   `epaisseur += (cible−epaisseur)·taux_asym − erosion`. L'**inertie asymétrique**
   (montée vite / descente lente) est le **seul état stocké** → satisfait D5
   (champ mémorisé, pas instantané) avec un état minimal. Le **tassement de
   litière** est encapsulé dans `om_fresh_eff` (foisonnement ↓ avec
   `Parcelle.age_sem`, déjà tracé). La **consommation** (faune D31, mycélium,
   minéralisation) baisse déjà `om_*` ⇒ cible ↓ ⇒ épaisseur suit : **zéro
   double-comptage**, aucun couplage direct plante (philo #2). Seul flux propre au
   champ = l'érosion baseline.
2. **Plantes = SOURCE seulement** (litière + exsudats), pas puits — biologiquement
   correct. Puits = décomposeurs uniquement. Le **priming rhizosphérique** (racines
   accélèrent la décompo) → **nouvelle dette ouverte**, reporté.
3. **Découpage 3 tronçons** : ①a champ+dynamique (golden re-figé annoncé, dérive
   attendue ~nulle car aucun effet en retour) ; ①b effets écolo eau+NPK bornés vs
   D41 + **test 500 ans** anti-emballement (golden re-figé annoncé) ; ② rendu
   relief extrudé `PxPerCmZ` + snapshot (patron `t_sol`) + recalage objets posés
   (pur-vue, golden neutre, F5).

## Effets écologiques (émergents, philo #2, modulés composition)

- **Rétention d'eau** : greffe miroir dans `tick_hydrology` (après la ligne
  `soil_memory·SOIL_RETENTION`, `hydrologie.py:109`), modulée par `cec_norm_at`
  (effet MO plus fort sur sable que sur argile). L'hydro lit l'épaisseur du **tick
  précédent** (elle tourne avant `tick_epaisseur`) → décalage 1 tick déterministe.
- **Accès NPK** : volume de stock accessible ∝ épaisseur, **plafonné et borné vs
  D41** (atténue la carence sur sol humifère, ne supprime pas la famine voulue ;
  si incalibrable sans casser D41 → réduire à symbolique + dette).

## Contexte vérifié dans le code (fonde les kickoffs)

Ordre de tick (`sim/engine/boucle.py`) : hydro (3) → décompo (4) → mycélium →
populations — tous les consommateurs de MO après l'hydro. `Parcelle.age_sem`
tracé (`matiere_organique.py`). Patron dérivé `_OmIndexField`/`vitalite`
(`sol.py`). `cec_norm_at` (`nutriments.py:78`). Snapshot grille 2D `t_sol`
(`serialize.py:255`). Rendu `BuildGround`/`BuildHouse` + `PxPerCmZ=0.39`
(`WorldView.Monde.cs`). `ENGINE_VERSION="0.5.13"`.

## Couplages dette

D40 (vitesse décompo module la cible), D31 (faune = puits), **D41** (accès NPK à
BORDER), D50 (litière typée = source foisonnement), D39 (asphyxie = revers non
bridé), D56 (fond `om_stable` hétérogène = plancher). **Nouvelle dette** :
priming rhizosphérique.

Conception seule, rien implémenté. Prêt pour `/sprint-auto sprint_epaisseur_sol`.
