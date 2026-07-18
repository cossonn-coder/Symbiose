# Sprint JARDINIER AUTOMATE — état de sprint

> Carnet de bord `/conception` → **CONCEPTION FIGÉE le 2026-07-18**. Reprise à
> froid = lire `CLAUDE.md` + CE fichier + le kickoff `0N` du tronçon en cours.
> Doc : `docs/conception/CONCEPTION_JARDINIER_AUTOMATE.md`. Kickoffs `01`→`07`
> autosuffisants présents. **Prêt pour `/sprint-auto sprint_jardinier_auto`.**
>
> Carte des tronçons : ① socle · ② table+budget+impasses · ③ comptabilité+trace ·
> ④ objectifs+onglet · ⑤ banc jardin tenu · ⑥ vue Godot · ⑦ semiologique (opt).
> **Golden INTACT partout** (H2 : automate hors tick). **① FAIT** (2026-07-18).

## Avancement
- **① Socle — FAIT (2026-07-18).** Paquet `tools/jardinier_auto/` (profil,
  perception, diagnostic, regles, execution, trace, boucle) + banc
  `tools/bancs/automate_demo.py` + `tests/test_automate_determinisme.py`.
  Boucle 5 étapes câblée, gestes `arroser`+`recolter` seulement, perception
  `omniscient`, profil `LIBRE`. **Golden INCHANGÉ** (`3076c154dc3d5fbf…`,
  bit-identique — H2 vérifié). Déterminisme : 3/3 (rejeu identique, opt-in strict,
  automate OFF = golden). Aucun C# touché. Tous fichiers ≤ 39 LDC code (bande 🟢).
  - **POINT À DURCIR au ② (tutelle)** : `PlantInstance` n'a AUCUN attribut
    `cultive` — la distinction cultivé/féral vit dans le dict de détection de
    maîtrise comme un set de ZONES `(tile_id, r, c)` (`marquer_replante`), pas un
    champ de plante. Conformément au kickoff (« ne PAS inventer d'attribut »), la
    tutelle ① = **toutes les plantes vivantes** (`sous_tutelle` dans `boucle.py`).
    Effet visible au banc : l'automate arrose aussi les FÉRALES (Pissenlit,
    Minette, Pâturin…) → Vigueur épuisée → flot d'`arroser echec`. Au ② : croiser
    avec le set `replante` par plot-foyer pour ne soigner que les cultivées.
  - Observations banc (104 sem, LIBRE) : `recolter ok ×11496`, `arroser ok ×573`,
    `arroser echec ×38753` (épuisement Vigueur, attendu en LIBRE non borné au ①).

## Sujet
Un **jardinier automate** déterministe qui joue le jardin à la place du testeur
pendant les phases de test accélérées (2,5 J/s). Intention : faire pousser les
plantes et récolter les fruits, « de son mieux pour chaque plante ». Ancrage
comportemental = **loi du minimum de Liebig** (lever le facteur limitant).
Amorce source : `docs/amorce/amorce_conception_automate.md`.

## Cadres déjà posés par Nico (amorce §0, 2026-07-18) — NON rediscutés
- **Perception** : deux profils **commutables** (`omniscient` / `semiologique`).
- **Exécution** : **Python**, headless **ET** attaché F5 (via `sim_server`).
- **Comptabilité** : commutable par profil (`bride` / `libre`).

## Invariant architectural (H2) — le pilier du sprint
L'automate est un **module AU-DESSUS du moteur**, jamais dans `tick_semaine`. Il
s'intercale **entre deux ticks**, côté APPELANT. Conséquence : **golden INTACT
par construction** (le moteur ne change pas d'une ligne ; on ajoute un appelant ;
`tests/test_golden.py` ne l'invoque jamais). À vérifier au tronçon ①.

## Faits code établis (Q1 RÉSOLU — lecture réelle du 2026-07-18)
Emplacement gestes = **paquet** `sim/actions/` (ré-exporté via `sim.actions`).
- **Boucle** : `Engine.tick_semaine()` (`sim/engine/boucle.py:76`). `main.py`
  boucle `for y in years: for _ in range(52): engine.tick_semaine()` (l.245-254).
- **Monde** : `engine.tiles` = `game_state["tiles"]` (liste de `Tile`) ;
  `engine._eco(tile)` = `game_state["eco"][tile.tile_id]` (EcoFields par tuile) ;
  `tile.plants` = liste de `PlantInstance`. `game_state["current_player"]="joueur_1"`.
- **Perception par plante** : `plant.vitalite` (continu, D75) ; `plant.etat`
  (discret {sain/affaibli/malade/mort}) ; `eco.light_received(plant)` (lumière
  reçue) ; `eco.humidite.at_plot(r,c)` ; façade `vigueur_plante.qi_local(plant,eco)`
  / `sante` / `maturite`. `plant.position`=(r,c) plot-foyer ; `plant.root_plots`.
  PAS d'uid stable → tiebreak déterministe = `(tile_id, plant.y_cm, plant.x_cm)`
  (positions continues, uniques).
- **Gestes réels utiles** (signatures) :
  - `arroser(gs, player, eco, r, c, urgence=False)` — MODÉRÉ, écrit `humidite`. ✓
  - `pailler(gs, player, eco, r, c, *, nature="paille")` — MODÉRÉ **MAIS
    CONSOMME un stock de mulch** (`mulch_stock`) → **refus si stock insuffisant**,
    y compris en mode `libre` (le stock n'est pas de la Vigueur). Chaînage requis :
    `broyer`/`recolter_paille` alimentent le stock AVANT de pouvoir pailler.
  - `recolter(gs, player, plant, eco)` — FAIBLE, GRADUÉ, gain ∝ maturité. ✓
  - `deraciner(gs, player, plant, eco)` — ÉLEVÉ, tue (désherbage curatif féral). ✓
  - `tailler(gs, player, plant, eco, *, cible, segment_id)` — MODÉRÉ (réduire un
    voisin ombrageant). ✓
  - `grelinette(gs, player, eco, r, c)` — MODÉRÉ (structure_sol ↑). ✓
  - `favoriser_auxiliaire(gs, player, tile)` — MODÉRÉ. ✓
  - `planter(gs, player, tile, eco, species, r, c, x_cm, y_cm)` — FAIBLE,
    **consomme la banque-joueur** (`player_seed_bank`).
- **Corrections à la table §2.3 de l'amorce** :
  - `drainer`/`creuser` (excès d'eau) **N'EXISTENT PAS** (hydrologie conçue,
    non implémentée) → ligne à RETIRER (ce sprint ne crée aucun geste).
  - Carence minérale → `epandre` existe mais exige une chaîne compost mûre
    (poser_bac→composter→retourner→epandre) → hors socle, tardif.
- **Coûts** : NUL/FAIBLE(5)/MODÉRÉ(15)/ÉLEVÉ(30), ×URGENCE_MULT(1.5) en phase
  saison. `cout_action` atténué par la maîtrise (neutre 1.0 sans maîtrise).
- **Déblocage** : `gestes_debloques` par avatar ; BASE = {planter, arroser,
  recolter, manger, ecraser, becher, favoriser_auxiliaire, deraciner, grelinette}.
  `pailler`/`broyer`/`tailler` sont GATED (maîtrise/action) → en mode `bride`
  l'automate ne peut PAS pailler tant que la maîtrise n'est pas acquise.

## Découpage CONSOLIDÉ (perf-first, golden intact partout)
- **①** Socle : paquet `tools/jardinier_auto/` (percevoir→diagnostiquer→proposer→
  prioriser→exécuter), profil = **dataclass configurable** (tous les axes, seuls
  `arroser`/`recolter` câblés), perception `omniscient`, **journal minimal**
  {geste, facteur, cible, résultat}, verrous déterminisme (rejeu → même hash ;
  automate OFF → golden bit-identique). Tutelle = cultivées.
- **②** Table facteur→geste complète (règles priorisées, `regles.py`) +
  priorisation par budget + chaînage `broyer→pailler` + `tailler`/`deraciner`
  (désherbage `curatif`/`aucun`/`systematique`) + `part_recoltee` (slider) +
  **DÉTECTEUR D'IMPASSES** (facteur limitant sans geste-réponse applicable).
- **③** Comptabilité commutable : flags `paie_vigueur` + `credite_maitrise`,
  respect de `gestes_debloques`, **trace des CONSÉQUENCES** (déverrouillages de
  maîtrise / paliers / morts consignés au journal).
- **④** OBJECTIFS (cœur mécanique) : structure `(geste, quantité, cible)`,
  injection début/planification, biais de priorisation + comptage de progression,
  **onglet** = trace scopée + événements monde ; objectif inatteignable → impasse.
- **⑤** Banc « jardin tenu » : tenu vs abandonné (démographie, couverture sol,
  **perf LightField** §2.7/Q9) + **rapport d'impasses agrégé** (le livrable
  « trous de gameplay »). Le livrable de mesure.
- **⑥** Vue Godot (RÈGLE PERMANENTE) : automate branché dans `sim_server` (option
  F5) + retour visuel des gestes + journal/impasses + **onglet objectifs**. Neutre.
- **(⑦ optionnel, hors chaîne)** profil `semiologique` — mesure la qualité de la
  sémiologie du jeu (écart omniscient↔sémiologique) ; coûteux (recenser les signes
  émis) ; seulement si ①-⑤ tiennent.

## Arbitrages TRANCHÉS par Nico (2026-07-18)
- **Q3 tutelle** → tutelle = **cultivées** ; **désherbage COMMUTABLE par profil**,
  défaut = **curatif** (« désherbe si nuisible » = seulement quand une férale est
  le facteur limitant d'une cultivée). Modes : `curatif` (défaut) / `aucun` /
  `systematique`.
- **Q5 récolte** → **récolter dès mûr**, avec une **`part_recoltee ∈ [0,1]`
  ajustable (slider)** pour tester différents réglages. Défaut proposé = 1.0.
- **Q4 comptabilité** → **`paie_vigueur` ET `credite_maitrise` COMMUTABLES par
  profil** (flags orthogonaux). Plus de modes `bride`/`libre` figés : ce sont des
  presets de ces flags.

## OBJECTIFS donnés à l'automate (Nico 2026-07-18) — germe du système de QUÊTES
- **Objectif = `(geste, quantité, cible espèce/structure)`** (ex. `récolter, 1,
  tomate` ; `récolter, 10, pomme_de_terre`). Injectable **au début** de la sim OU
  **à tout moment en phase de planification** (temps figé).
- **Effet sur la boucle** : biaise la PRIORISATION vers la cible + **compte la
  progression** (incrément sur chaque geste-cible réussi). Objectif accompli quand
  la quantité est atteinte.
- **Onglet** = vue de la TRACE **filtrée sur l'objectif** + événements du monde
  pendant sa poursuite (réutilise le journal de ③, aucune machinerie neuve).
- **Couplage émergent** : un objectif inatteignable (cible absente + aucun moyen
  de l'obtenir) → **impasse** consignée (compose avec le détecteur d'impasses).
- **SCOPE ce sprint = cœur mécanique SEULEMENT.** Le **système de quêtes complet**
  part en **DETTE D79** (suite logique) : sources diégétiques (courrier voisin/
  oncle/enfant), objectifs à **condition d'état** au-delà de geste+quantité (« kiwi
  de 5 m » = hauteur, « trèfles fleuris » = floraison), panneau de quêtes Godot,
  voix narratives. C'est l'habillage ludique du cœur.

## DEUX exigences NEUVES de Nico (2026-07-18) — structurantes
- **TRACE structurée** = livrable central : journal par tick {semaine, cible,
  facteur limitant, geste, coût, résultat} + **conséquences** (déverrouillages de
  maîtrise via `evaluer_deblocages`, morts, franchissements de palier). Progressif :
  minimal ① → conséquences ③ → rapport agrégé ④ → visuel ⑤.
- **DÉTECTEUR D'IMPASSES** = objectif important : quand un facteur limitant
  diagnostiqué n'a **aucun geste-réponse APPLICABLE** (geste inexistant / verrouillé
  / stock manquant), consigner une **impasse typée** = « trou de gameplay » à
  remonter. L'automate devient un instrument de découverte des problèmes insolubles
  dans l'état actuel du jeu.

## Profil d'automate = dataclass configurable (remplace bride/libre)
`perception` (omniscient|semiologique) · `paie_vigueur` (bool) ·
`credite_maitrise` (bool) · `desherbage` (curatif|aucun|systematique) ·
`part_recoltee` (float [0,1]) · `ecrit_carnet` (bool). Presets nommés
`LIBRE`/`BRIDE` = combinaisons de ces axes.

## Décidables par défaut (reco, pas de question)
- **Q2 format table** : liste ORDONNÉE de règles priorisées dans un module Python
  dédié (`regles.py`), lisible/éditable — PAS de fichier de données externe
  (simplicité #2, pas de config spéculative pour un outil de dev).
- **Q10 nommage** : paquet `tools/jardinier_auto/` (perception / diagnostic /
  regles / execution / boucle). « IA » proscrit (ni apprentissage, ni RNG).
- **Q6 découpage** : voir ci-dessus (5 tronçons + 1 optionnel).
- **Q7 futur diégétique** : ne pas trancher, garder l'automate SANS état narratif
  propre → porte transcendant ouverte à coût nul.
- **Q8 retour F5** : fusionné dans le tronçon ⑤ (vue Godot obligatoire).

## §REPRISE
**① FAIT et vérifié (golden intact, déterminisme 3/3), NON COMMITÉ** (Nico
commit). Prochaine étape = **tronçon ②** : lire `02_*.md` → table `regles.py`
complète + priorisation par budget + chaînage `broyer→pailler` +
`tailler`/`deraciner` (désherbage `curatif`/`aucun`/`systematique`) +
`part_recoltee` + **détecteur d'impasses**. **Câbler la tutelle=cultivées** au ②
(croiser le set `replante` — voir POINT À DURCIR ci-dessus). Chaque tronçon :
lire `0N` → bosser → golden intact → maj CE fichier → commit → tronçon suivant.
DETTE : **D78** (ce sprint, « conçu, prêt à implémenter ») ; **D79** (système de
quêtes complet, hors scope). Défauts figés : `part_recoltee=1.0`,
`desherbage=curatif`. Rappel gestes réels : voir « Faits code établis » ci-dessus
(pailler consomme un stock de mulch ; drainer/creuser n'existent pas).
