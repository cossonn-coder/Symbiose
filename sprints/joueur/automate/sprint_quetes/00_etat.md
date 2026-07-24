# Sprint QUÊTES (D79) — état de conception

> Carnet de bord vivant (skill `/conception`, §0bis). Phase A = challenge en
> cours. RIEN n'est figé tant que Nico n'a pas validé la conception globale.
> Type/thème : `joueur/automate`. Dépend de D78 (fait) / couple D87 (clos).

## Phase courante
**SPRINT CLOS CÔTÉ IMPLÉMENTATION le 2026-07-24.** Les 5 tronçons ①→⑤ sont FAITS.
Golden INCHANGÉ `57c166d8…` sur tout le sprint (opt-in strict). Reste F5 Nico + la
clôture documentaire (DETTE D79→CLOSE + D93, BACKLOG, journal) au moment du commit.
Doc de conception : `docs/joueur/automate/conception_quetes.md`.

## Carte des tronçons
- ① `01_module_conditions_cumulees.md` — **FAIT (2026-07-24).** `sim/quetes.py`
  (`Quete` frozen, état opt-in `game_state["quetes"]`, API
  ajouter/actives/progression/est_accomplie + hook `notifier_geste`) +
  `recolte_cumulee` compté par hook geste joueur, câblé dans
  `tools/simserver/plante_route.py` (rebind local de `bilan` → notifie APRÈS
  geste réussi, zéro changement des branches) + consignation ledger ✉ dans
  `game_state["log"]`. Tests `tests/test_quetes.py` (12/12 verts).
  **Golden INCHANGÉ** `57c166d8…` (opt-in strict). NB : `test_sim_server` a un
  échec PRÉEXISTANT (pommier pré-âgé, nouaison — sans rapport, vérifié au stash).
- ② `02_conditions_etat.md` — **FAIT (2026-07-24).** 3 évaluateurs d'état purs
  ajoutés à `sim/quetes.py` (`hauteur_min`/`floraison_min`/`nombre_vivant_min`),
  registre `_EVALUATEURS_ETAT`, aiguillage par tag ; lecture SNAPSHOT hors tick
  (`tiles → plants`, prédicats EXISTANTS `current_height`/`floraison ≥ SEUIL_FLEURI`
  — seuil 0.5 redéfini localement, règle de couches `sim ← engine`). Nouvelle API
  publique : `evaluer_etat(gs)` (clôt les quêtes d'état comblées, ✉ au ledger,
  à appeler HORS tick) + `avancement(gs, id)` (phrase DIÉGÉTIQUE V2, 4 bandes
  <1/3/<2/3/<1/accompli, zéro chiffre ; couvre aussi `recolte_cumulee`).
  `_consigner_accomplissement` généralisé via `_decrire_condition` (message ①
  inchangé). Tests `tests/test_quetes.py` 25/25 (5 suites d'état ajoutées).
  **Golden INCHANGÉ** `57c166d8…` (évaluation opt-in hors tick). LDC 161 (🟢).
- ③ `03_declenchement_habillage.md` — **FAIT (2026-07-24).** Corpus déclaratif
  `sim/quetes_corpus.py` (6 LETTRES anonymes V1, chaleureuses/non-directives ;
  couvre les 2 familles de conditions, les 5 récompenses simples, les 3 formes de
  déclencheur ; une lettre vise le kiwi = cible inatteignable assumée F3). Champ
  `Quete.texte_lettre` ajouté (défaut `""`, ①② intacts). Nouvelle API `sim/quetes.py`
  (hors tick, opt-in) : `evaluer_declencheurs(gs, player)` (ouvre les lettres dont
  le déclencheur `None`/`("palier",objet,seuil)`/`("saison",semaine_min)` est
  satisfait, DÉTERMINISTE ids triés, plafond `PLAFOND_QUETES_ACTIVES=6` #6),
  `remettre_recompenses(gs, player)` (verse graine/vigueur/maitrise/page via les API
  EXISTANTES, drapeau `recompense_versee` idempotent, `None`=plaisir pur), et
  `est_atteignable(condition)` (kiwi hors catalogue → jamais accomplie #4). Zéro RNG.
  Tests `tests/test_quetes.py` 42/42 (8 suites ③ ajoutées). **Golden INCHANGÉ**
  `57c166d8…` (tout hors tick, opt-in). LDC quetes.py 222 (🟢), quetes_corpus.py 52
  (🟢). NON câblé au pont (= tronçon ⑤). Carnet-parseur de la ligne ✉ laissé au ⑤
  (émise, ignorée sans dommage — hors scope kickoff ③).
- ④ `04_recompenses_materielles.md` — **FAIT (2026-07-24).** Récompenses MATÉRIELLES
  rares (V3, #2 respecté : un ACTEUR neuf apparaît, jamais un buff) ajoutées à
  `sim/quetes.py` :
  - `("vivace", espece, annees)` → `_offrir_vivace` instancie une pérenne LIGNEUSE du
    `PERENNIAL_CATALOGUE` puis la FAIT POUSSER par le VRAI chemin (`grow_plant` sur
    `annees×52` ticks, growth_factor plein soleil = la sonde de calibration des arbres) →
    structure de segments cohérente « comme si elle avait poussé » ; `form_seed` amorcé
    par `form_seed_at(seed,…)` → DÉTERMINISTE, zéro RNG. Placement au plot (0,0) de la
    1ʳᵉ tuile (tri `tile_id`). Test : pommier 6 ans → 8 segments, 211 cm, reproductible.
  - `("structure", kind)` → `_offrir_structure` pose un `bac` (`Structure` + append à
    `eco.structures`, patron `poser_bac`) GRATUITEMENT (pas de Vigueur : cadeau ≠ geste
    payant), unicité tuile respectée (`structure_de_tuile`).
  Aiguillage branché dans `_appliquer_recompense` (③) sans toucher aux tags simples ;
  imports LOCAUX (rare, évite tout cycle). 2 lettres corpus ajoutées
  (`lettre_vieux_pommier_gaston` vivace pommier, `lettre_bac_compost_odette` structure).
  **OUTIL DIFFÉRÉ EN DETTE** (aucun inventaire d'outils n'existe → D93, cf. DETTE.md).
  Tests `tests/test_quetes.py` 52/52 (2 suites ④). **Golden INCHANGÉ** `57c166d8…`
  (opt-in, hors tick). LDC quetes.py 260 (🟢), quetes_corpus.py 68 (🟢).
- ⑤ `05_vue_godot_courrier.md` — **FAIT (2026-07-24).** VUE de bout en bout.
  - **Pont** : commande read-only `courrier` (mixin NEUF `tools/simserver/courrier.py`,
    `CourrierMixin`, câblé dans `server.py`) → `sim.quetes.etat_courrier(gs, debug)` =
    lettres triées par id {id, donneur, texte_lettre, avancement DIÉGÉTIQUE, accomplie,
    atteignable} ; chiffre exact (progression/condition) SEULEMENT si `msg.debug` (V2/#5).
    Ouvrir le panneau évalue les quêtes d'état (`evaluer_etat`, hors tick) sans verser de
    récompense. **DRIVER** `avancer_quetes` (même mixin) câblé dans `cmd_step_week` HORS
    tick (déclencheurs → clôture d'état → récompenses idempotentes) ; les cumulées se
    closent au hook geste. Opt-in strict → golden intact. Protocole **0.5.40**.
  - **Godot (C#)** : `SimBridge.Courrier(debug=false)` + panneau `world/CourrierPanel.cs`
    (VoicePanel : lettre verbatim, coche ✉/☑, avancement diégétique, gris si rêve hors
    catalogue) + onglet « Courrier » dans `WorldView.Hub.cs`. Build **vert** (0/0).
  - **Banc F5** : `bancs/courrier.py` (registré `BANCS`/`BANC_POST_INIT`/`BANC_WEEK_DEPART=12`) :
    monde 8×8 (tournesol, lavandes adultes, trèfles, 2 pommiers mûrs) ; post_init POSE
    5 lettres curées, UNE par famille + le kiwi inatteignable.
  - **Golden INCHANGÉ** `57c166d8…`. Tests `tests/test_quetes.py` 52/52. LDC quetes.py 279
    (🟢), courrier.py 13 (🟢), banc 32 (🟢).
  - **RESTE (clôture doc, hors ce tronçon car pas de commit ici)** : maj DETTE
    (D79 → CLOSE ; rattacher D93 outil différé du ④), BACKLOG, entrée journal.
  - **Carnet-parseur de la ligne ✉ NON câblé** (déféré au ③, resté hors scope) : la ligne
    `✉ Quête accomplie …` est émise dans le log mais ignorée par `sim/evenements.py`
    (parseur par marqueurs positionnés `@(r,c)` ; le ✉ social est positionless → régex +
    kind `Evenement` à ajouter). Ignorée sans dommage → petite DETTE à ouvrir.

## Faits vérifiés dans le code (source de vérité, revérifiés au grep)
- **F1 — D78 n'est PAS sur le chemin joueur.** `objectifs.py` vit dans
  `tools/jardinier_auto/` (harnais automate). `incrementer()` appelé par la
  boucle automate ; `sim/actions/gestes.py` (gestes joueur) ignore les objectifs ;
  le pont ne l'expose que derrière `automate on` (`automate_cmd.py`).
  → D79 = système MOTEUR joueur neuf (`sim/quetes.py`), pas un enveloppement de
  D78. Partage la FORME `(geste, quantite, cible, id)`, pas le code d'exécution.
- **F2 — `sim/evenements.py` = parseur de log texte (regex), pas un bus.**
  → quêtes cumulées comptées par HOOK sur le geste joueur (pas de re-parse du
  ledger) ; quêtes d'état lues sur le SNAPSHOT des tiles hors tick. Le ledger
  n'est PAS le substrat des quêtes.
- **F3 — Kiwi ABSENT du catalogue** (grimpante différée D26,
  `conception_grimpantes.md`). Trèfle EXISTE (`cultivees.py:199`, stolonifère).
  Espèces hautes dispo pour démo `hauteur_min` : `Sunflower`, `AppleTree`.
  → NE PAS créer le kiwi ici (importerait D26). Cible absente = `inatteignable`
  (déjà géré par `est_atteignable`). Démo sur tournesol/pommier + trèfle fleuri.
- **F4 — Évaluation couche `sim` hors tick → golden intact.** Confirmé faisable.

## Décisions provisoires (recommandations, à confirmer)
- D79 = module moteur `sim/quetes.py`, état dans `game_state` (sauvegardé),
  exposé au pont ; hook comptage sur dispatch des gestes joueur.
- 2 familles de conditions : `recolte_cumulee` (compteur/hook) et
  `etat_instantane` (`hauteur_min`, `floraison_min`) lues sur snapshot.
- Déclenchement déterministe : palier maîtrise D12.2 + jalon saison, zéro RNG.
- Toute quête optionnelle, ignorable, jamais bloquante, sans échéance dure (#6).

## Décisions VISION tranchées par Nico (2026-07-24)
- **V1 — Donneurs = LETTRES ANONYMES** signées d'un prénom, sans figure ni
  dialogue ni récurrence obligatoire (voix épistolaire). Compatible « pas de
  PNJ » → ajuster le garde-fou CLAUDE.md pour autoriser les voix épistolaires.
- **V2 — Affichage DIÉGÉTIQUE approximatif** en primaire (« de quoi remplir un
  cageot », « à hauteur d'homme », « ça y est presque ») ; chiffre exact réservé
  au mode debug (#5 respecté).
- **V3 — Récompenses (catalogue déclaratif ouvert)** : plaisir pur (base) /
  graine / page secrète / Vigueur joueur / maîtrise (crédit) ; + RARE :
  outil, structure permanente, PLANTE VIVACE déjà enracinée de plusieurs années
  (= instanciation d'une pérenne à âge avancé, PAS un buff → #2 OK). JAMAIS de
  buff direct sur plante existante.

## Coût perf estimé
Négligeable : K conditions actives lues sur snapshot hors tick, K petit
(plafond de quêtes actives). Aucun O(N²). Golden intact.

## §REPRISE (tous tronçons FAITS — reste F5 + clôture doc)
①②③④⑤ CLOS côté implémentation. Golden INCHANGÉ `57c166d8…`, build C# vert (0/0),
`tests/test_quetes.py` 52/52.

**F5 Nico** : lancer la vue, monter le banc `init config="courrier"` (sélecteur de
bancs, catégorie « courrier »), cliquer la maison → onglet **Courrier** : 5 lettres
attendues (Marcel/cageot tomates = recolte_cumulee « le panier est encore vide » ;
Léa/tournesol = hauteur_min « à peine sorti de terre » ; Amélie/lavande = floraison_min ;
Marcel/verger = nombre_vivant_min « presque le compte » ; Léa/kiwi = rêve INATTEIGNABLE
grisé). En jeu normal (config full), les lettres arrivent seules au fil des semaines
(driver `step_week`) ; les cumulées se cochent en récoltant, les quêtes d'état à
l'ouverture du panneau.

**Clôture doc à faire au commit** (pas fait ici, subagent sans commit) :
1. `DETTE.md` : **D79 → CLOSE** ; ouvrir/rattacher **D93** (outil de récompense différé,
   pas d'inventaire d'outils) + une micro-dette « carnet-parseur de la ligne ✉ »
   (marqueur social positionless à reconnaître dans `sim/evenements.py`).
2. `BACKLOG.md` : sprint quêtes → terminé.
3. `journal.md` (+ entrée `journal/`) : décision figée + clôture D79.
Golden à garder INCHANGÉ. Ne pas re-figer.

---
Lire : `CLAUDE.md` + cette fiche + l'amorce (dans le fil `/conception D79`) +
`docs/joueur/automate/conception_jardinier_automate.md` (D78) +
`data/code/tools/jardinier_auto/objectifs.py`. Prochaine étape : recueillir les
3 réponses vision, puis trancher Q4 (représentation condition), Q6 (couplage
D87), Q8 (persistance), Q9 (espèces) — la plupart techniquement tranchables.
Ensuite figer (phase B) : doc `docs/joueur/automate/conception_quetes.md` +
kickoffs. Découpage pressenti : ① module `sim/quetes.py` + conditions cumulées
(hook geste) → ② conditions d'état (snapshot) → ③ déclenchement déterministe +
table déclarative + voix donneurs → ④ vue Godot panneau courrier. Golden intact
partout.
