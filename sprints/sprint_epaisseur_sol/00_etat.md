# Sprint ÉPAISSEUR DE SOL (D57) — état de sprint

> État partagé léger, mis à jour en fin de chaque tronçon par `/sprint-auto`.
> Reprise à froid : lire `CLAUDE.md` + CE fichier + le kickoff `0N` courant.
> Conception figée : `docs/champs/sol/conception_epaisseur_sol.md`.

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
- **①a champ + dynamique** — ✅ **FAIT** (golden **INCHANGÉ** `98bdf772…`, aucun
  effet en retour comme prévu). `GridField epaisseur_sol` stocké (borné [0,60])
  + `tick_epaisseur` (relaxation vers cible bulk-density `E_FRESH·foisonnement(age)
  + E_ACTIVE·om_active + E_STABLE·om_stable`, inertie asym. montée/descente, érosion)
  + init AU REPOS dans `init_eco` (cible sur om_stable de fond D56) + `get_field`
  + bump `ENGINE_VERSION` 0.5.13→0.5.14. **Save disque = DIFFÉRÉ** : aucun save
  disque n'existe encore (backlog save global) → rien à sérialiser ; le champ est
  exposé au registre `get_field`/`fields` par introspection. → `01a_champ_dynamique.md`.
- **①b effets écolo** — ✅ **FAIT** (non commité — Nico commit). Golden **RE-FIGÉ**
  `a6c2f651…` (raison : deux flux neufs lisent enfin `epaisseur_sol`). Rétention d'eau
  greffée dans `tick_hydrology` (terme miroir de la rétention soil_memory, `ep_n·
  EPAISSEUR_RETENTION·cec_norm_at(soil_type,om_n)` — plus fort sur sable pauvre que
  sur argile déjà rétentrice) + accès NPK dans `plant_uptake` (amplificateur BORNÉ du
  BESOIN `×(1+EPAISSEUR_NPK_BONUS·ep_n)`, patron MYCO_P_BONUS → à épaisseur=0 facteur
  1.0 ⇒ **D41 PRÉSERVÉE**, Liebig plafonne toujours par le stock réel). Les deux lisent
  l'épaisseur du tick PRÉCÉDENT (décalage 1 tick uniforme ①a). `ENGINE_VERSION` 0.5.14
  →0.5.15. Test 500 ans anti-emballement écrit (`tests/test_epaisseur_500ans.py`).
  → `01b_effets_ecolo.md`.
- **② rendu** — ✅ **FAIT** (code ; F5 visuel = Nico). Golden **INCHANGÉ**
  `a6c2f651…` (pur-vue). **A** : bloc `epaisseur` par tuile au snapshot (grille 2D
  dense cm, patron `t_sol`), pont **0.5.15→0.5.16** ; `test_sim_server` **242/242**
  (2 checks neufs). **B** : relief extrudé dans le partial NEUF
  `world/WorldView.Relief.cs` (79 LDC) — dessus du plot remonté de
  `epaisseur_cm × PxPerCmZ × ReliefExaggeration` + flanc sombre, mis à jour par
  snapshot (`ApplyEpaisseur`/`UpdateRelief`), reconstruit sur rotation
  (`BuildGround` capture les plots). **C** : helper UNIQUE
  `ReliefRisePx(tile,lx,ly)` — les PLANTES suivent le relief (recalées à la
  naissance ET à la croissance, `WorldView.Snapshot.cs`). `dotnet build` **vert**.
  **Reste F5 Nico** : calibrer `ReliefExaggeration` (défaut 2.0) ; recalage des
  AUTRES couches (litière/macro/structures/carpophores/conteneurs) laissé au F5
  (voie incrémentale du kickoff « relief d'abord, recalage ensuite »), extension
  mécanique via `ReliefRisePx`. → `02_rendu_relief.md`.

## Couplages dette
D40 (vitesse décompo module la cible), D31 (faune = puits), D41 (accès NPK à
BORDER, ne pas masquer la famine), D50 (litière typée = source foisonnement),
D39 (asphyxie = revers non bridé), D56 (fond om_stable hétérogène = plancher).
**Nouvelle dette** ouverte : priming rhizosphérique (plantes puits indirect).

## §REPRISE
①a + ①b **FAITS** (non commités — Nico commit). `ENGINE_VERSION` = `0.5.15`.
Golden **RE-FIGÉ** `a6c2f651d4289295474918ad25d060c9c7b27f5e2389f9c7806015ad92118209`
(raison : ①b, deux flux neufs lisent `epaisseur_sol`). Dérive PETITE, localisée,
cohérente : sur 4 ans terre hum 0.071→0.079 (+eau retenue), n 0.095→0.087 /
k 0.012→0.011 (uptake un peu plus grand) ; argile hum inchangée 0.008 (déjà
rétentrice → cec module l'effet à la baisse, comme voulu). Pas d'emballement.

Fichiers touchés ①b : `fields/ecofields/constants.py` (EPAISSEUR_NORM_REF /
EPAISSEUR_RETENTION / EPAISSEUR_NPK_BONUS), `hydrologie.py` (import `cec_norm_at`
+ terme rétention step 3b), `uptake.py` (amplificateur `ep_uptake` sur le BESOIN
N/P/K, patron MYCO_P_BONUS), `tools/simserver/version.py` (0.5.14→0.5.15 + changelog),
tests `simserver/{structures,conteneurs,voix}.py` (assert 0.5.15), `test_substrat.py`
(rétrocompat drainage : même tile_id pour isoler la variable — l'om_stable/epaisseur
de fond est hétérogène par tile_id depuis ①a, la rétention ①b la lit). NOUVEAU
`tests/test_epaisseur_500ans.py` (anti-emballement, conservé). LDC pur OK
(hydrologie 36, uptake 53). Suites : golden re-figé, sim_server 234/234,
eau/lessivage/confinement/substrat/conteneur verts.

**② rendu FAIT le 2026-07-03** (code ; F5 visuel = Nico). Pont **0.5.16**, golden
INCHANGÉ `a6c2f651…`, `sim_server` **242/242**, `dotnet build` vert. Fichiers :
`tools/simserver/serialize.py` (bloc `epaisseur`) + `version.py` (0.5.16),
tests `simserver/{conteneurs,structures,voix}.py` (assert 0.5.16 + présence bloc),
NEUF `world/WorldView.Relief.cs`, `world/WorldView.{Monde,Snapshot}.cs`.
**SPRINT TERMINÉ côté code** — reste F5 Nico : calibrer `ReliefExaggeration`
(défaut 2.0) et, si désiré, étendre le recalage aux couches litière/macro/
structures/carpophores/conteneurs via `ReliefRisePx` (helper unique déjà en place).
