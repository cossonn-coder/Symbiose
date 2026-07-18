# Sprint JARDINIER AUTOMATE — état de sprint

> Carnet de bord `/conception` → **CONCEPTION FIGÉE le 2026-07-18**. Reprise à
> froid = lire `CLAUDE.md` + CE fichier + le kickoff `0N` du tronçon en cours.
> Doc : `docs/conception/CONCEPTION_JARDINIER_AUTOMATE.md`. Kickoffs `01`→`07`
> autosuffisants présents. **Prêt pour `/sprint-auto sprint_jardinier_auto`.**
>
> Carte des tronçons : ① socle · ② table+budget+impasses · ③ comptabilité+trace ·
> ④ objectifs+onglet · ⑤ banc jardin tenu · ⑥ vue Godot · ⑦ semiologique (opt).
> **Golden INTACT partout** (H2 : automate hors tick). **①②③④⑤⑥⑦ FAITS**
> (2026-07-18) — SPRINT CLOS (chaîne obligatoire + tronçon optionnel ⑦).

## RECENSEMENT DES SIGNES DIÉGÉTIQUES (préalable ⑦) — ce que le joueur PEUT voir
Sources réelles côté moteur, relues (jamais écrites) par le profil `semiologique` :
- **`plant.etat`** — état DISCRET {sain/affaibli/malade/mort} (`plants/base/instance.py`,
  discrétise `vitalite`) → couleur/texture à l'écran.
- **`sim.semiologie.leaf_symptoms(plant, eco, saison)`** — LA liste de symptômes
  FOLIAIRES que la vue affiche (identique au snapshot F5). Détecteurs : `chlorose`,
  `secheresse`, `asphyxie`, `ravageurs`, `rongeur_racinaire`, `ombre`, `senescence`,
  `acclimatation` + marques événementielles (maladie/gel/grêle). Chaque signe = miroir
  DRY du seuil de la mécanique qui blesse → il n'apparaît qu'une fois le DÉGÂT installé.
- **Sprites visibles** : adventices dans le rang, voisin manifestement dominant, fruit
  MÛR — perçus par les mêmes helpers géométriques que l'omniscient (ce sont des sprites).
- **INVISIBLES** (aucun rendu direct) : `humidite`/`structure_sol`/`paillage`/`qi`/
  `vitalite` continus → les facteurs `sol_compacte` et `sol_nu` n'ont AUCUN signe.

**Mapping facteur→signe** (câblé dans `diagnostic.facteur_limitant_semio`) :
`hydrique`←secheresse · `exces_eau`←asphyxie · `ombrage`←ombre+voisin visible ·
`concurrence_ferale`←adventices visibles · `organe_mur`←fruit mûr. `sol_compacte`/
`sol_nu` = **non diagnosticables** (INVISIBLES, `impasses.FACTEURS_INVISIBLES`).

## Avancement
- **⑦ Profil `semiologique` + banc de mesure de l'écart — FAIT (2026-07-18, OPTIONNEL).**
  L'automate a désormais un second regard : `perception="semiologique"` ne lit QUE les
  signes visibles (`leaf_symptoms` + `etat` + sprites), jamais un champ continu. Le
  stub `NotImplementedError` du ① est remplacé. Nouveaux/touchés (tous 🟢, code pur) :
  - `perception.py` (74 LDC) : dataclass `PerceptionSemio` + `_percevoir_semio` +
    dispatch dans `percevoir(..., saison=None)`. Importe `sim.semiologie.leaf_symptoms`.
  - `diagnostic.py` (40 LDC) : `facteur_limitant` devient POLYMORPHE (isinstance) →
    `_facteur_limitant_omni` (inchangé) OU `facteur_limitant_semio` (dérivé des seuls
    signes, plus grossier ET plus tardif ; `sol_compacte`/`sol_nu` absents = invisibles).
  - `impasses.py` (19 LDC) : cause `FACTEUR_INVISIBLE` + set `FACTEURS_INVISIBLES`
    ({sol_compacte, sol_nu}) — trou de sémiologie remonté, JAMAIS bouché (kickoff).
  - `boucle.py` : `_collecter` calcule `saison_de(engine.week)` et le passe à
    `percevoir` (leaf_symptoms l'exige). Omniscient inchangé (saison ignorée).
  - **NOUVEAU banc** `tools/bancs/semiologie_ecart.py` (90 LDC) : rejoue UN monde
    abandonné (les plantes souffrent → les signes sortent), calcule les DEUX perceptions
    par tick/plante, imprime la table de recensement + la MATRICE DE CONFUSION des
    décisions + la CÉCITÉ par facteur + un CHIFFRE de qualité sémiologique.
  - **Golden INCHANGÉ** (`3076c154dc3d5fbf…`, bit-identique — H2 tenu, chemin omniscient
    intact). Déterminisme 3/3, tronçon2 9/9. Aucun C# (⑦ = mesure Python pure).
  - **VÉRIF DE SORTIE CONFIRMÉE** (banc `full`, 1 an, 3742 obs plante×tick) : la boucle
    `jouer_tick` tourne aussi sous profil semio (smoke 8 sem : recolter/deraciner, pas de
    crash). **RÉSULTAT CLÉ mesuré : qualité sémiologique ≈ 16 %** — l'omniscient et le
    joueur diffèrent massivement. Deux causes chiffrées : (a) **signes TARDIFS** —
    l'omniscient déclenche `hydrique` dès humidite<0.8 mais le signe `secheresse` n'arrive
    qu'après dégât installé (miroir du seuil moteur) → 1201 obs « omni=hydrique / semio=
    organe_mur » + cécité hydrique×58, ombrage×125 ; (b) **INVISIBLE structurel** —
    `sol_nu` vu 865+438 fois par l'omniscient, **jamais** par le joueur (aucun signe SUR
    LA PLANTE). C'est un DÉFAUT DE DESIGN #5 chiffré pour la 1re fois, PAS un bug de
    l'automate — à verser en réflexion conception (voir §DÉCISION IMPRÉVUE).
  - **DÉCISION IMPRÉVUE (design, à remonter à Nico — RIEN implémenté)** : le chiffre bas
    dit deux choses réelles du jeu, pas de l'automate — (1) les seuils du diagnostic
    OMNISCIENT sont bien plus précoces que les seuils d'APPARITION des signes (calibrage
    volontaire des signes = « miroir du dégât installé ») ; (2) `sol_nu`/`sol_compacte`
    n'ont aucun signe foliaire — un vrai trou de sémiologie. **Piste conception** (hors
    scope, à trancher par Nico) : signe de sol nu/compacté au niveau du PLOT (pas de la
    plante) ou signe hydrique plus précoce (feuillage qui pique du nez avant le dégât).
    Non tranché ici : le kickoff interdit d'ajouter un signe pour « boucher le trou ».
- **⑥ Vue Godot — automate en OPTION F5 + journal/impasses + onglet objectifs —
  FAIT (2026-07-18).** Dernier tronçon de la chaîne obligatoire (règle permanente).
  **Golden INCHANGÉ** (`3076c154dc3d5fbf…`, bit-identique — H2 tenu, automate hors
  tick). Déterminisme 3/3, tronçon2 9/9. **Build C# VERT** (`dotnet build
  Symbiose.csproj` : 0 avertissement, 0 erreur).
  - **Pont Python** (pont **0.5.30**) : nouveau `tools/simserver/automate_cmd.py`
    (57 LDC 🟢, `AutomateCmdMixin`) — commande `automate` op ∈ {on, off, objectif,
    status}. `on` monte `JardinierAutomate(profil)` (profil dict, défaut LIBRE +
    désherbage curatif) et appelle `marquer_jardin_cultive` (tutelle=cultivées, hors
    tick). Le HOOK réel vit dans `commands.py cmd_step_week` : SI `self._automate`
    actif, `jouer_tick(engine)` APRÈS `tick_semaine` (invariant H2). `cmd_init` remet
    `self._automate=None` (monde neuf). `serialize.py` : bloc OPT-IN `automate` =
    {actif, profil, trace (60 dernières entrées gestes/impasses/conséquences),
    objectifs (id/geste/quantité/cible/progression/accompli)} — présent UNIQUEMENT si
    automate actif → snapshot F5 ordinaire bit-identique. `server.py` : mixin +
    dispatch. `version.py` bump 0.5.30 (commenté).
  - **Vue C#** (namespace `Symbiose`, GDScript nul) : `core/SimBridge.cs` +2 méthodes
    (`Automate(on, profil)`, `AutomateObjectif(...)`). Nouveau partial
    `world/WorldView.Automate.cs` (125 LDC 🟢) : touche **A** branche/débranche
    l'automate (panneau texte à droite = profil + objectifs/progression + onglet du
    1er objectif actif + journal récent, impasses en ROUGE) ; **Maj+A** pousse un
    objectif démo (récolter 5 tomate) pour valider l'onglet en F5. Hooks : `_Ready`
    (BuildAutomatePanel), `ApplySnapshot` (ApplyAutomate, tolérant), `Controls` (case
    Key.A), légende HUD + témoin `Build` MAJ.
  - **Retour visuel des gestes = v1 « ligne de log défilante »** (kickoff : « confort
    de débogage, pas un chef-d'œuvre » ; le marqueur au plot viendra à la demande).
  - **Vérif de sortie CONFIRMÉE** (smoke serveur `full`, 6 sem, `SimServer` direct) :
    bloc absent sans `automate on` (opt-in) ; après `on` → 81 cultivées sous tutelle ;
    trace = gestes (tailler/ombrage `ok`…) + impasses (`sol_nu → ravitaillement_
    manquant`, le trou de gameplay du ②/⑤ qui SAUTE aux yeux) ; objectif suivi
    (`recolter tomate 0/3`) ; bloc disparu après `off`.
- **⑤ Banc « jardin tenu vs abandonné » + rapport d'impasses agrégé — FAIT
  (2026-07-18).** Le LIVRABLE DE MESURE. Deux fichiers CRÉÉS, aucune machinerie
  moteur neuve, `sim/` intact :
  - `tools/jardinier_auto/rapport.py` (35 LDC 🟢) — `rapport_impasses(gs) -> str`
    (+ `agreger_impasses` testable) : relit `automate_journal`, agrège les entrées
    `impasse` par (cause, facteur, tuile) en résumé texte groupé par cause. Pure
    lecture, ré-exporté par `__init__.py`.
  - `tools/bancs/jardin_tenu.py` (124 LDC 🟢) — monte DEUX mondes déterministes
    identiques (même config/seed), joue l'un avec `JardinierAutomate` (tenu) et
    l'autre sans (abandonné), N ans (défaut **2**, `--years`), imprime le
    comparatif (démographie cultivées/férales, couverture paillage, **perf
    LightField**) + rapport d'impasses. Perf : `perf_counter` autour de
    `tick_semaine` (ms/tick moteur) + cProfile 2 ticks → part `tick_light`.
  - **Golden INCHANGÉ** (`3076c154dc3d5fbf…`, bit-identique — H2 tenu, automate
    hors tick). Déterminisme 3/3, tronçon2 9/9.
  - **VERDICT PERF Q9 (résultat clé, banc `full`, 2 ans, LIBRE)** : **le régime
    tenu N'EST PAS plus cher** — ms/tick moteur ≈ **794 (tenu) vs 800 (abandonné)**,
    surcoût **−0,8 % → coût comparable**. L'hypothèse « jardin tenu → plus de
    biomasse → LightField plus cher » n'est **PAS confirmée** à 2 ans : au contraire
    l'automate désherbe les férales (démographie tenu vs abandonné : cultivées
    **64 vs 56**, N total 640 vs 598 — le tenu porte un peu plus de plantes MAIS
    mieux réparties). Part `tick_light` mesurée **~10-12 %** (≠ 53-62 % de la
    mémoire perf : ici an 2 non mûr + light caché + échantillon 2 ticks cProfile
    → SOUS-représentation, caveat consigné dans le fichier). **Rien à recalibrer**
    (le kickoff l'interdit) — résultat consigné, pas de chantier.
  - **TROU DE GAMEPLAY confirmé et AGRÉGÉ** (le livrable) : `sol_nu →
    ravitaillement_manquant` **×3541 en 2 ans** (monde `full` sans aucune chaîne de
    mulch — 0 squelette ligneux, 0 `mulch_source`). C'est la découverte du ② désormais
    QUANTIFIÉE par tuile (S×1025, E×527…). À traiter hors sprint (semer/poser une
    source de mulch dans `build_world_full`, ou geste `recolter_paille` sur une
    prairie) → note DETTE. Temps mur banc 2 ans ≈ 180 s (perf OK, jamais 500 ans).
- **④ Objectifs (cœur mécanique) + onglet — FAIT (2026-07-18).** Nouveaux fichiers :
  `objectifs.py` (dataclass `Objectif(geste, quantite, cible, id)` + état opt-in
  `game_state["automate_objectifs"]` = `{id: {objectif, progression, semaine_debut,
  semaine_fin}}` ; API `ajouter_objectif`/`objectifs_actifs`/`incrementer`/
  `est_accompli`/`sert`/`objectifs_servis`/`est_atteignable`/`marquer_inatteignable_
  signale` + `BONUS_OBJECTIF=100`) et `onglet.py` (`onglet(gs, obj_id)` = journal
  filtré sur `objectif_id` + événements du `log` de la FENÊTRE active, parsés par
  en-tête `S{wiy}/Y{annee}`). `boucle.py` : snapshot `actifs` en tête de tick →
  biais de priorisation (bonus dans la clé de tri, biais PAS exclusivité) + comptage
  (incrément par geste-cible `resultat != echec`, conséquence `objectif:<id>:accompli`)
  + détection `objectif_inatteignable` (une fois par objectif, §7). `trace.entree`
  porte désormais `objectif_id` (clé de l'onglet). `impasses.py` : 4ᵉ type
  `OBJECTIF_INATTEIGNABLE`. Banc : flag `--objectif GESTE:QTE:CIBLE` (répétable) +
  impression de l'onglet.
  - **Golden INCHANGÉ** (`3076c154dc3d5fbf…`, bit-identique — H2 tenu, automate hors
    tick). Déterminisme 3/3 (rejeu 4015 entrées identiques), tronçon2 9/9.
  - **Vérif de sortie CONFIRMÉE** (banc 104 sem) : `recolter:3:basilic` → ACCOMPLI
    3/3 (sem 1→12), onglet liste les 3 gestes + fenêtre d'événements ; conséquence
    `objectif B:accompli` consignée ; `recolter:1:kiwi` (hors catalogue) → impasse
    `objectif_inatteignable ×1` (semaine 2, signalée une seule fois). Aucun geste
    quand la cible est absente/verrouillée (biais nul ⇒ comportement ①-③ intact).
  - **CHOIX de sémantique documentés** : (a) comptage = +1 par geste-cible non-échec
    (récolte tronquée comprise) ; (b) `est_accompli(gs, obj_id)` prend `gs` (déviation
    assumée de la signature `est_accompli(obj)` du kickoff — la progression ne peut
    vivre sur un `Objectif` frozen) ; (c) un geste servant plusieurs objectifs même
    cible n'est tagué `objectif_id` que du min-id (mais incrémente TOUS) — l'onglet du
    2ᵉ ne le montre pas (edge case dev, complet = D79). Fichiers 🟢 (objectifs 68,
    onglet 38, boucle 104 LDC). Aucun C# touché (vue Godot = ⑥).
- **③ Comptabilité commutable + trace des conséquences — FAIT (2026-07-18).**
  Nouveau `comptabilite.py` (responsabilité unique : Vigueur, gating, conséquences) :
  `assurer_solde_libre` (mode `paie_vigueur=False` → solde sentinelle `1e9`, ne
  noie plus le journal d'`arroser echec`), `separer_verrouilles` (mode payé →
  gestes hors `gestes_debloques` écartés → impasse `geste_verrouille`),
  `snapshot_paliers`/`snapshot_vivantes` + `consequences_maitrise`
  (`evaluer_deblocages` + diff paliers) + `consequences_morts` (diff vivantes
  avant/après gestes, corrèle un `deraciner`). `boucle.py` : étape 4bis (gating +
  budget OU solde libre) + étape 6 (consigne les conséquences). `trace.py` :
  catégorie `consequence` (`entree_consequence`). `automate_demo.py` : flags
  `--credite-maitrise` + `--amorce-maitrise OBJET` (dev only, `M.decouvrir`) +
  affichage des conséquences.
  - **Golden INCHANGÉ** (`3076c154dc3d5fbf…`, bit-identique — H2 tenu). Déterminisme
    3/3, tronçon2 9/9. Banc BRIDE (`--paie-vigueur --credite-maitrise
    --amorce-maitrise paillage`, 12 sem) : Vigueur consommée, `ombrage →
    geste_verrouille ×100` (tailler gated), `deblocage pailler`+`deblocage broyer`
    consignés → **3 éléments de la Vérif de sortie confirmés**.
  - **DÉVIATION de design assumée** : le kickoff plaçait le gating dans
    `execution.py` ; il vit dans `comptabilite.py` (`separer_verrouilles` appelé
    par `boucle.py`) pour garder « comptabilité = une responsabilité isolée ».
    `execution.py` n'a PAS été touché. Golden intact, comportement conforme.
- **② Table + budget + impasses — FAIT (2026-07-18).** Table `regles.py` COMPLÈTE
  (7 facteurs : hydrique/exces_eau/ombrage/concurrence_ferale/sol_compacte/sol_nu/
  organe_mur ; règles multiples par facteur, chaîne de repli). Nouveaux fichiers :
  `tutelle.py` (cultivé/féral via set `replante`, `marquer_jardin_cultive`),
  `impasses.py` (3 types §7), `proposition.py` (cerveau : choix geste OU impasse +
  chaînage `broyer→pailler` + repli). `diagnostic.py` étendu (seuils nommés),
  `perception.py` enrichi (paillage, structure, voisinage férale/ombrage, scan
  LOCAL par tuile O(N²) négligeable), `execution.py` câble les 8 verbes,
  `profil.py` porte `seuil_concurrence()` + `n_a_recolter()`, `boucle.py` intègre
  part_recoltee + tri + budget Vigueur + consignation impasses, `trace.py` a la
  catégorie `impasse`.
  - **TUTELLE=CULTIVÉES câblée** (POINT À DURCIR du ① résolu) : `sous_tutelle`
    croise le set `replante`. Le monde `full` ne marque personne → le banc et le
    test déterminisme appellent `marquer_jardin_cultive` (hors tick, déclare le
    jardin initial ; les férales de succession restent hors set).
  - **Golden INCHANGÉ** (`3076c154dc3d5fbf…`, bit-identique — H2 tenu). Déterminisme
    3/3 (rejeu 3989 entrées identiques). Nouveau `tests/test_automate_troncon2.py` :
    9/9 (chaînage broyer→pailler, 2 types d'impasse, repli hydrique, seuils
    désherbage, cible deraciner, part_recoltee, priorité pailler>arroser).
  - **DÉCOUVERTE (impasse réelle)** : le monde `full` n'a AUCUNE chaîne de mulch
    (0 squelette ligneux `bois_restant`, 0 espèce `mulch_source`) → l'automate
    consigne `sol_nu → ravitaillement_manquant` en masse. C'est un vrai trou de
    gameplay remonté par le détecteur (pas un bug) — à agréger au banc ⑤. Le
    chaînage broyer→pailler est prouvé fonctionnel par `test_automate_troncon2`
    (scénario avec squelette). Banc : désherbage commutable vérifié (aucun=0
    deraciner / curatif≈117 / systematique=143 sur 52 sem) ; `--paie-vigueur`
    coupe le flot d'échecs (129 gestes vs ~2000) ; `--part-recoltee 0.5` halve la
    récolte. Tous fichiers ≤ 69 LDC code (bande 🟢). Aucun C# touché.
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
**SPRINT CLOS — ⑦ FAIT (optionnel), tous les tronçons livrés** (golden intact
`3076c154…`, déterminisme 3/3, troncon2 9/9, pont 0.5.30, build C# VERT au ⑥). Le
profil `semiologique` est câblé (perception par signes seuls) et un banc de mesure
`tools/bancs/semiologie_ecart.py` chiffre l'écart de décision omniscient↔semio :
**qualité sémiologique ≈ 16 %** sur `full`/1 an → deux trous de sémiologie mesurés
(signes hydriques/ombre TARDIFS ; `sol_nu`/`sol_compacte` INVISIBLES). Ce chiffre est
un RÉSULTAT DE DESIGN #5, pas un bug — piste conception consignée à l'⑦ (§Avancement),
non tranchée (le kickoff interdit d'ajouter un signe pour boucher le trou). Aucune
suite obligatoire ; toute correction de sémiologie = sprint de conception à part.
**POINTS À VALIDER EN F5 PAR NICO** (le F5 visuel reste à lui) :
1. Touche **A** : l'automate tient-il visiblement le jardin (arrosage/paillage/
   récolte/taille visibles dans le monde) et le panneau s'ouvre-t-il à droite ?
2. Le journal et les **impasses** (rouge) sont-ils lisibles ? Le trou `sol_nu →
   ravitaillement_manquant` du monde `full` (pas de chaîne de mulch) doit crever
   l'écran.
3. **Maj+A** puis observer l'onglet : l'objectif démo (récolter 5 tomate)
   progresse-t-il ? (la tomate meurt tôt en démo — cf. mémoire `tomate_mort_precoce`
   — l'onglet peut donc rester à 0/5 : c'est un fait de sim, pas un bug ; tester
   éventuellement une cible plus robuste via un objectif custom).
4. **Perf F5** en régime tenu acceptable (lien verdict Q9 du banc ⑤ = coût comparable) ?
DETTE : **D78** (ce sprint, « conçu, prêt à implémenter ») ; **D79** (système de
quêtes complet, hors scope). Défauts figés : `part_recoltee=1.0`,
`desherbage=curatif`. Rappel gestes réels : voir « Faits code établis » ci-dessus
(pailler consomme un stock de mulch ; drainer/creuser n'existent pas). **NE PAS
COMMIT sans l'aval de Nico** (règle du prompt d'exécution ⑥).
