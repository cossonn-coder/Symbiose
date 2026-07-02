# Sprint ÉPAISSEUR DE SOL (D57) — état de sprint

> État partagé léger, mis à jour en fin de chaque tronçon par `/sprint-auto`.
> Reprise à froid : lire `CLAUDE.md` + CE fichier + le kickoff `0N` courant.
> Conception figée : `docs/conception/CONCEPTION_EPAISSEUR_SOL.md`.

## Sujet
D57 — **Litière → humus → ÉPAISSEUR de sol visible** (Nico 2026-07-02, F5 S5+S11).
La MO qui tombe épaissit le sol (couche fraîche foisonnante), le tassement + la
décompo la rognent, l'humus stable persiste et s'accumule sur les ans → le sol
**monte/descend** visiblement. Champ à **effet écologique** (eau + accès NPK), pas
une simple dérivée d'affichage.

## Phase
**Conception FIGÉE le 2026-07-02.** Prêt pour `/sprint-auto`. Lots 1-2-3 tous
tranchés (voir décisions ci-dessous). Aucun tronçon encore exécuté.

## Modèle arbitré (les 3 décisions clés)
- **Champ stocké à RELAXATION vers cible** (pas accumulateur, pas dérivée pure) :
  `cible = E_fresh·om_fresh_eff(age) + E_active·om_active + E_stable·om_stable`,
  `epaisseur += (cible−epaisseur)·taux_asym − erosion`. L'inertie asymétrique
  (montée vite / descente lente) EST le seul état stocké → satisfait D5 sans état
  superflu. Tassement de litière encapsulé dans `om_fresh_eff` (foisonnement ↓
  avec `Parcelle.age_sem`). Consommation faune/mycélium/minéralisation ⇒ `om_*` ↓
  ⇒ cible ↓ : **zéro double-comptage**, aucun couplage direct plante (philo #2).
- **Plantes = SOURCE seulement** (litière + exsudats), pas puits. Puits =
  décomposeurs uniquement (faune D31, mycélium saprophyte, minéralisation,
  tassement, érosion). Priming rhizosphérique → **dette reportée**.
- **Effet écolo double, émergent, modulé composition** (`cec_norm_at`) : rétention
  d'eau (greffe `tick_hydrology:109`) + accès NPK (borné vs D41).

## Carte des tronçons
- **①a champ + dynamique** — `GridField epaisseur_sol` stocké + `tick_epaisseur`
  (relaxation, foisonnement age_sem, érosion) + save + bump engine_version.
  Golden **RE-FIGÉ ANNONCÉ** (dérive attendue ~nulle : aucun effet en retour).
  → `01a_champ_dynamique.md`.
- **①b effets écolo** — rétention eau (modulée soil_type) + accès NPK (borné vs
  D41). Golden **RE-FIGÉ ANNONCÉ**. **Test 500 ans** anti-emballement.
  → `01b_effets_ecolo.md`.
- **② rendu** — relief extrudé `PxPerCmZ` + expo snapshot (patron `t_sol`,
  re-bump pont) + recalage objets posés. **Pur-vue, golden NEUTRE**, points F5.
  → `02_rendu_relief.md`.

## Couplages dette
D40 (vitesse décompo module la cible), D31 (faune = puits), D41 (accès NPK à
BORDER, ne pas masquer la famine), D50 (litière typée = source foisonnement),
D39 (asphyxie = revers non bridé), D56 (fond om_stable hétérogène = plancher).
**Nouvelle dette** ouverte : priming rhizosphérique (plantes puits indirect).

## §REPRISE
Conception figée, rien exécuté. `ENGINE_VERSION` de départ = `0.5.13`.
Lancer `/sprint-auto sprint_epaisseur_sol` : il exécute ①a → ①b → ② dans l'ordre,
golden re-figé annoncé aux tronçons ①a et ①b, neutre au ②. Détails de code
(chemins, lignes, patrons vérifiés) dans chaque kickoff `0N`.
