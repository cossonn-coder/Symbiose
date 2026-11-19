# Sprint DÉPART DU JARDIN (D140 A+B+C) — état

> Conception FIGÉE le 2026-11-18 : `docs/vegetal/genetique/conception_depart_jardin.md`
> (à lire en entier). Hors périmètre : trèfle (D140 D, non mesuré — Nico), éclaboussures
> de pluie et Ctrl+molette des graines (D140 E-F).

## But
Un jardin qui démarre vivant et réaliste : pâturin anémophile et autogame, gènes muets
gratuits, limites de froid physiquement possibles, mort par froid consignée, monde `full`
ouvert mi-mai avec une plante mûre de chaque espèce, semis d'intérieur et repiquage.

## Décisions clés (Nico, 2026-11-18)
- A : pâturin = vent + autofécondation ≈ 0,9. B : caractère non exprimé (aucun lecteur
  pour l'espèce) = coût nul, gène porté et hérité.
- C : ouverture `full` en **semaine 10** (juste après les saints de glace) ; **au moins
  une plante MATURE de chaque espèce du catalogue**, arbres compris (âge = première
  fructification) ; garde-fou catalogue ⊂ `full` ; semis (existe) + graines déjà
  semées ; pot dans la maison (chaud, peu de lumière) + geste `repiquer` (choc de
  repiquage ∝ racines à l'étroit) ; repiquage différé = choix du joueur, l'automate
  repique quand les nuits passent au-dessus de la limite de froid.
- Gel impossible au-dessus de ≈ −0,5 °C ; tournesol non sensible au froid sans gel ;
  rythme du froid sans gel (`FROID_LESION_K`) inchangé.

## Faits vérifiés au code (2026-11-18)
- `full` = 15 espèces sur 52 ; départ via `BANC_WEEK_DEPART.get(config, 1)` (commands.py).
- 68 cultivées repiquées s1 mortes en 2 semaines [seed 42] ; nuits s1-s9 entre −2,8 et
  +5 °C, > 7 °C dès s10.
- `lim_gel` tomate +2,8 °C, basilic +1,2, poivron −4,4 (gène `rusticite_froid` de variété).
- Semis (`planter` → `GrainEnAttente` + `bell(T_sol)`) et pots (`deplacer_pot`) existent.

## Golden
Départ `db4d6b75…` → après ① **`98a050cf…`** (re-figé : divergence 100 % due à B —
A seul et la dérivation `_POLLEN_VIBRE_BOURDON` sont bit-identiques ; coût allégé dès s1
chez achillée, haricot, phacélie, pommier, tournesol, trèfle (gènes muets `pollen`,
`limite_froid`, `fixation_azote`, `allelopathie`) ; 1ʳᵉ divergence du log en s9 ;
`population_hash`/`vigueur_hash` intacts). ① **RE-FIGÉ annoncé** · ② **RE-FIGÉ → `25671775…`** (1ʳᵉ divergence s1 : la tomate du smoke ne gèle plus à une nuit > −0,5 °C — borne de la sève — et le tournesol n'a plus de lésion de froid sans gel ; σ_A des tendres bit-identique sur le smoke, chronique neutre) ·
③④ **INTACT** (④ vérifié : `bce813af…`, golden courant après les sprints plante vivante /
stress au bilan) · ⑤ **INTACT** (vérifié `bce813af…`) · ⑥ **INTACT** attendu.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_paturin_genes_muets.md` — pâturin + gènes muets | **FAIT** 2026-11-18 (golden re-figé `98a050cf…`) |
| ② | `02_froid_tendres.md` — borne du gel, audit des tendres, chronique | **FAIT** 2026-11-18 (golden re-figé `25671775…`) |
| ③ | `03_monde_full_complet.md` — semaine 10, 52 espèces mûres, garde-fou, perf | **FAIT** 2026-11-18 (golden intact) |
| ④ | `04_semis_interieur_repiquer.md` — pot dans la maison + `repiquer` | **FAIT** 2026-11-19 (golden intact `bce813af…`, pont 0.6.25, commit `848dbd3`) |
| ⑤ | `05_automate_repiquage.md` — repiquage différé par l'automate | **FAIT** 2026-11-19 (golden intact `bce813af…`, pont 0.6.26, non commité) |
| ⑥ | `06_vue_banc.md` — palette, pots visibles, banc `depart_jardin`, clôture | à faire |

## Acquis du ①
- Registre `plants/caracteres.py` : champ `exprime` (prédicat sur la classe, None = toutes)
  + `couteux_exprimes(cls)` mémoïsé par espèce, lu par `cout_genetique`. Muets possibles :
  `nectar` (nectar d'espèce 0), `taille_fleur`/`guide_nectar` (ni nectar ni anthères
  poricides), `pollen` (ni vent ni poricide — la phacélie aussi !), `limite_froid`
  (`t_froid_lesion` None), `fixation_azote`, `allelopathie` (effets déclarés). Universels
  vérifiés au code : `rusticite_froid`, `limite_chaud`, `parfum` (ravageurs),
  `coriacite_feuille`, `mycorhization`.
- `FAMILLES_ANTHERES_PORICIDES` (caracteres.py) = source unique ; `registry._POLLEN_VIBRE_BOURDON`
  en dérive.
- Pâturin : `pollination_mode = "wind"`, autofécondation neutre 0,9 → fécondation ≥ 0,9.
- Test : `tests/test_genes_muets.py` (18/18).

## Acquis du ②
- `T_CONGELATION_SEVE = −0,5` (plants/base/instance.py) : `lim_gel` = min(borne, calcul) —
  point unique lu par dégâts (`reponse_thermique`), signes (`posture_thermique`) et pont.
- `SIGMA_GEL_TENDRE = 0,5` (caracteres.py) : σ_A de `rusticite_froid` surchargé
  (`genetique`) chez les 5 tendres sans endurcissement (tomate, poivron, basilic,
  haricot, courgette) → variétés entre ≈ −2,3 et −0,5 °C (poivron −4,4 → −2,1).
- Tournesol : `t_froid_lesion` None.
- Chronique : cause `froid` ajoutée à `CAUSE_DE_RAISON` ; la nuit froide (comme grêle,
  aléas, ravageurs) est loguée AVANT les en-têtes `[T0]` (boucle.py) → lignes sans
  tuile ; repli FIFO `(None, pos, espèce)` dans `chronique._appliquer` (log intact :
  il entre dans le golden). Vérifié monde `full` s1 : tomate/basilic → `froid`.
- Tests : `test_niche_thermique` [1b] (30/30), `test_chronique` (froid/gel sans en-tête).
- À noter : `brûlure (feuille échaudée)` tombe encore en `autre` (hors périmètre).

## Acquis du ③
- `sim/monde_complet.py` (neuf) : `SEMAINE_OUVERTURE = 10`, `AGE_ARBRES_DEMO` (déplacé de
  commands.py), table `PLACEMENTS` (45 plantes : 7 arbres + 38 herbacées, plots libres,
  niche par tuile), `SEMIS_OUVERTURE` (6 `GrainEnAttente` tuile S, dont haricot/courgette),
  `ouvrir_monde_complet(tiles, seed, semaine)`, `especes_matures(tiles)`.
  Herbacées : dernier stade + 1 an de squelette (lianes 3 ans, patron `planche_especes`) ;
  arbres : âge = max(11, `maturity_years`) (charme 11 → 15, chêne 25, hêtre 30, sapin 20,
  noyer 15). Pré-croissance prolongée de `semaine − 1` semaines (calendrier continu).
- `cmd_init` : `start_week` calculé AVANT la fabrique ; `full` ET `propre` (même monde,
  décidé) ouvrent en s10 ; `_pre_vieillir_ligneux` remplacé par `ouvrir_monde_complet`
  (logique déplacée, pas perdue). `main.py` et le smoke intouchés.
- Garde-fou : `tests/test_monde_full_complet.py` (7/7 ; « ajouter <espèce> au monde full »,
  vérifié en retirant le thym). `tests/simserver/base.py` : 91 → 136 plantes posées.
  `test_fleurs_lisiere` [5] : départ `week: 1` épinglé (son calendrier « mai-juin après
  15 pas » datait du départ s1). Suites `full` toutes vertes (test_sim_server 349/349).
- Vérifié : rien n'assume `week == 1` au 1er tick (chronique `_an` et `perf_annees`
  en semaines absolues ; 1ʳᵉ année de bilan = s10-s52, plus courte).
- Perf [3 paires alternées, charge VM 1,1-1,7 / 16 cœurs] : tick s10-s30 477 → 616 ms
  (+29 % [n=3, écart ±20 ms], juste sous le seuil de 30 %) ; init 1,3 → 3,8 s (×2,9 —
  pré-croissance des arbres de 15-30 ans). Vivants à s31 : 63 → 228.
- ⚠️ CONSTAT pour Nico (non corrigé, hors périmètre) : ouvrir en s10 provoque une
  HÉCATOMBE d'herbivorie dans les 6 premières semaines — DÉJÀ présente sur HEAD lancé
  à `week: 10` (91 plantes initiales → 16 vivantes à s16 ; aulnes, bouleau, charme
  morts « herbivorie »). Au départ s1 ils restent à vitalité 1,0. Cause mesurée :
  plantes neuves sans `stress_memory` (≈ 0,12-0,15 chez un arbre à s10 après un départ
  s1 ; gate `pressure > stress_memory·0,5`, perturbations.py) + auxiliaires à 0 à
  l'init (0,39 à s10 après un départ s1). Essai : amorcer `stress_memory` à la
  perturbation locale ne suffit pas (≈ 61/136 vs ≈ 40/136 à s17). Le chêne de 25 ans
  meurt d'herbivorie comme un semis (aucun effet de taille). Décision de design à
  trancher (amorcer la faune de saison ? la mémoire des plantes ? l'herbivorie selon
  la taille ?) — à verser en dette / conception, pas dans ce sprint sans accord.

## Acquis du ④ (2026-11-19)
- **Geste `repiquer`** : `sim/actions/conteneurs.repiquer(game_state, player, container,
  tile, r, c) -> str | None` (ré-exporté `sim.actions.repiquer`) — sort la 1ʳᵉ plante
  VIVANTE du conteneur, la pose au centre du plot (même objet : gènes, âge, stade,
  réserves ; segments translatés d'un bloc), le pot reste vidé ; renvoie la cause du choc
  `motte`/`chignon`, None si refus (plot hors tuile, pot vide, Vigueur) — refus sans coût.
  Coût MODÉRÉ, objets `("jardinage_hors_sol",)` + l'espèce ; déblocage `[("action",
  "poser_pot")]` ; famille `semis` ; palette cible `conteneur`. Fiche `geste_corpus`.
- **Pont 0.6.25** : commande `{"cmd":"action","verb":"repiquer","target":{"container":
  idx,"tile":"S","r":r,"c":c}}` (`tools/simserver/conteneurs_route._repiquer`) ; snapshot :
  `containers[].interieur` (bool), `plants[].memoires.racines_coupees`. Comparé avant/après
  (full seed 42) : seules ces clés ajoutées, valeurs des tuiles identiques.
- **Choc = bilan** (`sim/repiquage.py`, champ `PlantInstance.racines_coupees` hors
  `_PLANT_ATTRS`) : coupe = `COUPE_MOTTE` 0,25 + `COUPE_CHIGNON` 0,45 × serrage
  (`Container.serrage` = signal root-bound EXISTANT de l'effet nain) ; (1) `bilan.f_eau` ×
  (1 − coupe) — absorption plafonnée (poils absorbants perdus), même en sol frais ;
  (2) repousse `REPRISE_RACINES` 0,15/sem payée `cout_feuillage` × Δ sur le net, seulement
  plante active (pas en dormance/froid). **Écart au kickoff (mesuré)** : la 1ʳᵉ version
  passait par `eau_percue` (comme la pourriture) + coût seul → **inerte en jeu** (sol S
  1,0-1,5 ≫ seuil sec 0,30 ; surplus > 1 sem sature le `growth_factor`). Effet mesuré après
  correction (`mesures/effet_repiquage.py`, full seed 42, n=1, 3 godets repiqués s10 en S) :
  net −0,4 à −0,5 la 1ʳᵉ semaine (témoin +1,6 à +2,0), 2-3 sem de stagnation, passage de
  stade retardé d'1 sem (basilic, poivron), écart de hauteur à s19 : tomate −1,9 cm,
  basilic −2,9 cm, poivron −4,3 cm ; aucun mort.
- **Pot dans la maison** (`world/interieur.py`) : intérieur = toute l'emprise de la maison
  (choix le plus simple, pas de « rebord » dédié) ; `T_INTERIEUR` 17,5 °C (jour 20 / nuit 15)
  écrit dans `eco.temperature`, lumière ciel ouvert × `FENETRE` 0,3 (`LightField.filtrer`,
  invalide le cache géométrique — pas de double filtrage). Pas de pluie (aucun pot n'en
  reçoit, déjà vrai).
- **Monde full/propre** : `sim/monde_complet.pots_interieur(house, seed, semaine)` →
  `game_state["containers"]` = 3 godets 2 L de terreau (tomate, basilic, poivron) au mur sud
  de la maison, stade 0, 8 semaines de pousse TICKÉE en pot (`Container.tick`). Index 0-2 de
  `containers` ; un pot posé par le joueur arrive en 3.
- **Voix** : ligne `🪴 Repiquage [S] @(r, c) : tomate, chignon` (`ligne_repiquage`/
  `lire_repiquage`) écrite une fois par joueur et par cause (`game_state["repiquages_notes"]`)
  → `evenements` kind `repiquage` → carnet concept `jardinage_hors_sol`, 4 gabarits D/I.
- Tests : `tests/test_repiquage.py` 19/19 ; `tests/simserver/conteneurs.py` adapté (3 godets
  à l'init, indices décalés de n0, section repiquer) ; versions 0.6.25. Vertes : golden,
  mobilite, confinement, couplage, monde_full_complet, pressentis, encyclopedie,
  atteignabilite, carnet, bilan, gestes_lisibles (+ bancs), acces_gestes, ouverture_vivante,
  chronique, maladies_racines, embolie, test_sim_server (367/367).
- LDC : `geste_corpus.py` 360 (🟡, corpus de données), `carnet.py` 310 (🟡), reste < 300.
- ⚠️ **Pour Nico / ⑤-⑥** :
  (a) **le signal root-bound** (`ROOTBOUND_SEUIL` 0,30 cm de hauteur par litre) déclare à
  l'étroit presque tout plant en pot (godet 2 L : saturé dès 0,6 cm) → en pratique tout
  repiquage est un `chignon` (choc 0,70) ; la gradation « plus fort si à l'étroit » n'existe
  que pour de très grands pots. Recalibrer ce seuil change l'effet nain (pots/bacs) —
  décision de design, pas faite ici.
  (b) **Étiolement absent chez les tendres** : `est_etiole` exige une tolérance à l'ombre
  < 1 ; tomate 1,0, poivron 1,0, basilic 1,25 → aucun ne file à la fenêtre ; seul le
  `growth_factor` (0,6 + 0,4 × lumière) ralentit leur pousse. Non inventé (kickoff).
  (c) **Pots dehors sans météo** (pré-existant) : `Container.tick` n'écrit jamais T_air ni
  pluie ni gel pour un pot hors maison (11 °C constants, `T_AMBIENT_INIT`) ; un pot dehors
  ne gèle donc pas non plus, et aucun pot ne peut être arrosé (pas de route `arroser`).
  L'intérêt du semis d'intérieur face au pot dehors n'existe pas encore.
  (d) **Déblocage** : à l'ouverture, `repiquer` est fermé tant que le joueur n'a pas posé
  un pot (porte `poser_pot`, elle-même gatée par la maîtrise `jardinage_hors_sol`) — il voit
  les godets sans pouvoir les repiquer. L'automate ⑤ n'est pas concerné ; à trancher pour ⑥.
  (e) Les plantes en pot n'ont toujours pas de bilan (inchangé) : réserves/feuillage pleins
  au repiquage.

## Acquis du ⑤ (2026-11-19)
- **Règle réactive** `tools/jardinier_auto/repiquage.py` (pas un opérateur de plan : aucun
  objectif requis, décision relue chaque semaine) : `proposer_repiquages(engine)` →
  plans `(cle, tile, eco, plant, Plan(verbe="repiquer", facteur="nuits_douces",
  priorite=PRIO_REPIQUAGE 7))` ajoutés aux plans réactifs AVANT le tri dans
  `boucle.jouer_tick` → même gating (`repiquer` gated), même budget, même trace.
  `execution._jouer` câble `repiquer` (`CibleRepiquage(container, tile, r, c)`) ;
  `point_vise` = centre du plot d'arrivée.
- **Quand** : hors fenêtre « Gelée tardive » (`sim.weather.fenetre_evenement`, accesseur
  pur ajouté, (2, 9)) sur toutes les semaines lues, ET nuit la plus froide
  (`t_min_nuit_at` sur `weather_state`, même formule que le tick) de la semaine écoulée
  + 2 prévues (`NUITS_RECENTES` 1, `HORIZON_NUITS` 2), au plot visé, ≥
  `max(lim_froid, lim_gel)` + `MARGE_NUIT` 0,5 °C. Couvert du plot = celui du jour.
- **Où** : `operateurs.plot_libre` scindé en générateur `plots_libres` (+ `plot_libre` =
  le premier, inchangé) ; le repiquage prend le plot libre le PLUS LUMINEUX
  (`eco.lumiere.at_plot`, tri stable), un balayage par tick partagé par tous les pots.
  Écart au kickoff : `planter` n'a aucune notion de niche (premier plot libre) ; « niche »
  = soleil ici (les plants élevés au chaud sont des cultures de soleil).
- **Mesuré** (full seed 42, départ s4, LIBRE, n=1) : aucune tentative s4-s14 ; 1ʳᵉ
  tentative s15 (nuits ≥ 10,5 °C : tomate/basilic/poivron ont `lim_froid` 10 °C) ;
  tomate + basilic repiqués s17 (tuile N r0), poivron s18 (tuile O). Nuits du jardin :
  7,9 °C en s10, > 10 °C seulement à partir de s14 → « fin mai » n'est pas atteignable
  avec la limite actuelle des tendres (le moteur dit mi-juin).
- **Déblocage (point du ④ d)** : l'automate PASSE par le déblocage (mode `paie_vigueur`,
  `separer_verrouilles`). Corrigé à l'init du pont (`commands.cmd_init`) : si la fabrique
  a posé des conteneurs, `marquer_action("poser_pot")` + `evaluer_deblocages` (« posséder
  vaut avoir posé », patron du bac d'Odette) → `repiquer`, `planter_conteneur`,
  `deplacer_pot` ouverts dès l'ouverture, pour le joueur aussi.
- **Plant repiqué = cultivé** : `repiquer` (sim/actions/conteneurs.py) appelle
  `marquer_replante` (comme un semis qui lève) → l'automate le soigne ensuite.
- **Pont 0.6.26** : aucune clé neuve ; snapshot comparé (full seed 42, init + 2 sem.) :
  seuls `gestes_debloques` (+3 verbes) et `gestes_pressentis` (−3) changent.
- Tests : `tests/test_automate_repiquage.py` 16/16 (fenêtre, limite, init débloqué, rien
  pendant la fenêtre, 3 réussis après, plots cultivés, OFF = godets pleins, déterminisme).
- ⚠️ **Constat (pré-existant, non corrigé)** : en profil LIBRE la Vigueur n'est PAS
  illimitée — le solde sentinelle 1e9 est rabattu au plafond par `vigueur.gain` dès la 1ʳᵉ
  récolte du tick (`recolter` priorité 20), puis épuisé (≈ 33 `tailler` en échec/sem). Les
  repiquages s15-s16 échouent ainsi faute de Vigueur et passent en s17-s18.

## REPRISE
**SUSPENDU avant ④ (2026-11-18)** : hécatombe par herbivorie à l'ouverture, confirmée au F5 de Nico → DETTE.md D140 (G), CONÇU le 2026-11-18 : attendre la clôture de `sprints/vegetal/sante/sprint_plante_vivante/` puis `sprint_stress_au_bilan/` (les plantes vivent d'un bilan carbone, plus de PV — le choc de repiquage du ④ doit s'exprimer en feuillage/réserves, relire `docs/vegetal/sante/conception_plante_vivante.md`). Noms d'espèces en français → D141 (hors sprint).
④ FAIT (`848dbd3`), ⑤ FAIT (non commité). Lire `CLAUDE.md`, ce fichier (§Acquis du ④ et du ⑤), puis
le kickoff ⑥ `06_vue_banc.md`. Au ⑥ : `repiquer` est déjà ouvert à l'init (point ④ d
réglé) ; F5 automate = les godets sortent mi-juin (s17-s18), pas fin mai.
