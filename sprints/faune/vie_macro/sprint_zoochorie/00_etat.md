# sprint_zoochorie — carnet de bord de conception (D42)

**Sujet** : dispersion animale des graines (D42) — le merle mange un fruit et sème
ailleurs ; le geai cache des glands et en oublie (décision Nico 2026-11-06 :
« merle, geai », suite de la relève ligneuse D130).
**Phase** : **CONCEPTION FIGÉE** le 2026-11-09 (« on suit ta reco »), prêt pour
`/sprint-auto sprint_zoochorie`. Doc : `docs/faune/vie_macro/conception_zoochorie.md`.
Golden de départ `a10b7225…` ; **re-figé au ⑥ seulement** (mulot → rapace/couleuvre).

## Constats vérifiés au code (2026-11-09)
1. Deux systèmes de fruits sans lien : les **fruits traçables** (`sim/engine/decompo.py
   _tick_fruits` : nouaison, maturation, chute en litière `fruit`) et la **recrue
   abstraite** (`sim/engine/mortalite.py _reproduction` : tirage hebdo
   `reproduction_rate`, toute l'année, sans lien avec les fruits).
2. Le merle (`fields/population/registry.py`, `resources._merle_food_grid`) lit le
   fruit **tombé** (litière `fruit`, fraîcheur ≤ 3 sem) + lombric. Il ne **retire**
   rien : aucune faune ne consomme de fruit. Habitat uniforme 0,20, `lisiere_w` 0,25.
3. Graines d'arbre déposées en banque-sol (`add_species`) : **jamais germées** — la
   germination férale ne passe que par les archétypes (`germination_candidates`).
   Seule recrue d'arbre = directe, sous la couronne du parent (relève ②).
4. Véhicule existant idéal : `GrainEnAttente` (`fields/seedbank.py`) — gènes PROPRES,
   `expression` (priming), position sous-plot, levée différée gatée niche/lumière ×
   tolérance/pH/T_sol/allélopathie (`sim/succession._lever_grains_en_attente`).
   Manques : pas de viabilité (un grain attend pour toujours), `cultive=True` par
   défaut, aucun plafond par plot.
5. Fruitiers traçables : figuier (stérile), pommier, cerisier, noyer ; tomate,
   courgette, fraisier, framboisier. Chêne, hêtre : **pas de fruits traçables**.
   Myrtille (`Vaccinium`), lierre : non fruitiers au moteur.
6. Faune : pas de geai, d'écureuil ni de mulot. Ceinture `foret` : `densite_ligneuse`
   par secteur, apport à la banque via `tick_apport_peripherie` (archétype
   `competitor`, sans espèce).
7. Golden smoke : Tomato (meurt S2-3) + AppleTree (< 5 ans) → aucun fruit mûr →
   frugivorie neutre attendue. À revérifier au tronçon.
8. Boucle par tuile (`boucle.py` l.221) ; chaque tuile a `origin_x_cm/origin_y_cm`
   → une graine peut changer de tuile (monde 20×20 m < portée d'un merle).

## Décisions arrêtées (Nico, 2026-11-09)
- Q1 périmètre : **merle + geai + écureuil + mulot** (4 disperseurs). Rôles proposés :
  merle = endozoochore (baies, sème sous les perchoirs) ; geai = caches de glands /
  faînes / noix en terrain découvert, longue portée (ceinture → jardin) ; écureuil =
  caches dispersées près des arbres, portée moyenne, arboricole ; mulot = caches
  courtes sous couvert + prédateur de graines au sol, proie du rapace/couleuvre.
- Q2 **unifié** : pour les espèces zoochores, la recrue passe par les VRAIS fruits
  (tombé → graine au pied, mangé → graine au loin) ; `_reproduction` abstraite
  retirée pour elles. Recalibrage de la relève (D130) accepté.
- Q3 graine du merle sous les perchoirs naturels **+ geste « poser un perchoir »**.
- Golden : une guilde neuve (mulot surtout, proie du rapace) peut faire dériver le
  smoke → re-figeage probable, à vérifier au code et annoncer au kickoff.

- Q4 (lot 2) **chêne + hêtre fruitiers** (glands/faînes traçables) **+ noisetier
  ajouté** au catalogue (5 voix, chatons = nectar de soudure T6).
- Q5 **mulot prédateur de graines** (au sol + grains en attente) **+ années de
  glandée** (masting déterministe par espèce/an → satiation des prédateurs).
- Q6 graine tombée au pied = `GrainEnAttente` aussi (levée par la niche) ; fin de
  la pose directe « plot le plus lumineux » pour les zoochores.
- Sans question (bio, décidé par Claude) : durée de vie des grains sauvages par
  espèce ; dormance (noyau, gland → printemps suivant) ; plafond de grains par plot.

## Tronçons
| # | kickoff | golden | état |
|---|---|---|---|
| ① | `01_grain_sauvage.md` — `GrainEnAttente` sauvage : dormance, péremption, plafond | inchangé | à faire |
| ② | `02_chute_unifiee.md` — fruit tombé → grains ; `_reproduction` coupée pour les fruitiers pérennes ; chêne/hêtre fruitiers ; glandée ; recalibrage relève | inchangé | à faire |
| ③ | `03_noisetier.md` — espèce neuve + 5 voix | inchangé | à faire |
| ④ | `04_merle_perchoirs.md` — `sim/zoochorie.py`, prise saturante, grille perchoir, tampon monde, geste `poser_perchoir` | inchangé | à faire |
| ⑤ | `05_geai_ecureuil.md` — 2 guildes `disperseur`, caches + oubli, apport ceinture | inchangé | à faire |
| ⑥ | `06_mulot.md` — guilde, prédation saturante des grains, caches ; proie rapace/couleuvre | **RE-FIGÉ annoncé** | à faire |
| ⑦ | `07_voix_mesure.md` — événements, carnet `dispersion`, signes ; 200 ans verger_mur + banc `nucleation` ; calibrage | inchangé depuis ⑥ | à faire |
| ⑧ | `08_vue_godot.md` — faune, fruits à coque, noisetier, perchoir, banc F5 ; clôture D42 | inchangé | à faire |

## Coût perf (estimé)
Frugivorie : boucle sur les fruitiers mûrs (quelques plantes) ; pose : un tirage
pondéré par plot sur une grille « perchoir » (couronnes ligneuses) déjà connue
(`foliar_plots`). Grains : plafond par plot. Attendu ≪ +10 % de tick.

## §REPRISE
Lire `CLAUDE.md`, ce fichier, le doc de conception, puis le premier kickoff « à
faire » du tableau. Chaque tronçon met à jour sa ligne + une section « Tronçon N —
fait » courte (constats chiffrés avec leur limite entre crochets).
