# Sprint QUÊTES (D79) — état de conception

> Carnet de bord vivant (skill `/conception`, §0bis). Phase A = challenge en
> cours. RIEN n'est figé tant que Nico n'a pas validé la conception globale.
> Type/thème : `joueur/automate`. Dépend de D78 (fait) / couple D87 (clos).

## Phase courante
**FIGÉE le 2026-07-24.** Conception validée par Nico, doc écrit
(`docs/joueur/automate/conception_quetes.md`), 5 kickoffs `01→05` écrits. Prêt
pour `/sprint-auto sprint_quetes`. Golden INCHANGÉ sur les 5 tronçons.

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
- ② `02_conditions_etat.md` — `hauteur_min`/`floraison_min`/`nombre_vivant_min`
  sur snapshot hors tick + progression diégétique. Golden intact.
- ③ `03_declenchement_habillage.md` — déclenchement déterministe (maîtrise/saison)
  + table `quetes_corpus.py` + voix lettres + plafond #6 + récompenses simples.
- ④ `04_recompenses_materielles.md` — vivace enracinée + structure (outil différé
  en dette si pas d'inventaire).
- ⑤ `05_vue_godot_courrier.md` — pont `cmd_courrier` + panneau lettres + banc F5.
  Clôture : maj DETTE/BACKLOG/journal.

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

## §REPRISE (prochaine étape : tronçon ②)
Tronçon ① CLOS. Prochaine étape = **② `02_conditions_etat.md`** : conditions
`hauteur_min` / `floraison_min` / `nombre_vivant_min` lues sur le SNAPSHOT hors
tick + progression diégétique. L'aiguillage par TAG est déjà prévu dans
`notifier_geste` (branche `cond[0] != "recolte_cumulee"`) et dans le mini-catalogue
déclaratif — ② ajoute ses évaluateurs sans toucher l'existant. Le parseur carnet
de la ligne ✉ reste à câbler au tronçon ③ (habillage/voix). Golden à garder
INCHANGÉ. Ne pas re-figer.

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
