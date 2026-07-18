# 2026-07-18 — Sprint JARDINIER AUTOMATE (D78) — CLOS (`/sprint-auto`, ①→⑦)

**Objet.** Agent **déterministe** (pas d'IA/RNG, philo #3) qui tient le jardin à
2,5 J/s pendant que le testeur observe — sinon toutes nos mesures (D69, D66/67/70/71,
D74) portent sur un jardin ABANDONNÉ. Comportement = **loi du minimum de Liebig**
(lever le facteur limitant). Spec figée : `docs/conception/CONCEPTION_JARDINIER_AUTOMATE.md`.

**Invariant H2 tenu de bout en bout.** L'automate est un module AU-DESSUS du moteur,
joué ENTRE deux ticks côté appelant — jamais dans `tick_semaine`. Conséquence : le
**golden n'a JAMAIS bougé** (`3076c154…`, bit-identique aux 7 tronçons) — golden intact
par construction, aucun re-figeage sur tout le sprint.

## Reprise (préconditions)

Sprint repris avec ①② déjà commités (`ad78439`, `5a17442`) et un **WIP ③ non commité,
non vérifié, non documenté** dans l'arbre (session antérieure). Précondition §1 (git
propre) en échec → arbitrage remonté à Nico, qui a tranché « **finir + commiter ③,
puis ④→⑦** ». Le WIP ③ était sain (golden intact, déterminisme 3/3) mais **incomplet** :
les 2 flags du banc (`--credite-maitrise`, `--amorce-maitrise`) étaient documentés sans
être câblés → complétés + démo BRIDE confirmée avant commit.

## Tronçons

**③ Comptabilité commutable + trace des conséquences** — commit `8822ea5`, golden
INTACT `3076c154…`.
- `comptabilite.py` (neuf, responsabilité isolée) : `assurer_solde_libre` (mode
  `paie_vigueur=False` → solde sentinelle `1e9`, ne noie plus le journal
  d'`arroser echec`), `separer_verrouilles` (gestes hors `gestes_debloques` →
  impasse `geste_verrouille`), `snapshot_paliers`/`snapshot_vivantes` +
  `consequences_maitrise` (`evaluer_deblocages` + diff paliers) + `consequences_morts`
  (diff vivantes avant/après gestes, corrèle un `deraciner`).
- `boucle.py` : étape 4bis (gating OU solde libre) + étape 6 (consigne conséquences) ;
  `trace.py` : catégorie `consequence` ; banc : flags `--credite-maitrise` /
  `--amorce-maitrise OBJET` (dev only, `M.decouvrir`) + affichage des conséquences.
- **Déviation assumée** : le gating vit dans `comptabilite.py` (pas `execution.py`,
  intact) pour garder « comptabilité = une responsabilité isolée ».
- Vérif de sortie confirmée (banc BRIDE `--amorce-maitrise paillage`) : Vigueur
  consommée, `ombrage → geste_verrouille ×100` (tailler gated), `deblocage
  pailler`+`deblocage broyer` consignés.

**④ Objectifs `(geste, quantité, cible)` + onglet** — commit `d720586`, golden
INTACT `3076c154…`. Germe du système de quêtes (complet → D79).
- `objectifs.py` (neuf) : dataclass `Objectif` + état opt-in `automate_objectifs`
  (progression, fenêtre `semaine_debut/fin`), API `ajouter/actifs/incrementer/
  est_accompli/sert/est_atteignable` + `BONUS_OBJECTIF`.
- `onglet.py` (neuf) : `onglet(gs, id)` = journal filtré sur `objectif_id` +
  événements du `log` de la fenêtre active.
- `boucle.py` : biais de priorisation (bonus **non exclusif** dans la clé de tri) +
  comptage + conséquence objectif accompli + détecteur `objectif_inatteignable` ;
  `trace.entree` porte `objectif_id` ; `impasses.py` 4ᵉ type.
- Banc : `recolter:3:basilic` → ACCOMPLI 3/3 ; `recolter:1:kiwi` (hors catalogue) →
  `objectif_inatteignable`.
- Choix de sémantique documentés : comptage = +1 par geste-cible non-échec ;
  `est_accompli(gs, id)` prend `gs` (progression ne peut vivre sur un `Objectif`
  frozen — déviation de signature assumée) ; multi-objectif même cible tagué du
  min-id (edge case → D79).

**⑤ Banc « jardin tenu vs abandonné » + rapport d'impasses agrégé** — commit
`9d55116`, golden INTACT `3076c154…`. Le livrable de MESURE du sprint.
- `rapport.py` (neuf) : `rapport_impasses(gs)`/`agreger_impasses` — agrège les
  impasses par (cause, facteur, tuile) = le livrable « trous de gameplay ».
- `jardin_tenu.py` (neuf) : deux mondes déterministes identiques, l'un joué par
  l'automate, l'autre nu ; comparatif démographie / couverture / perf
  (`perf_counter` + cProfile sur `tick_light`).
- **Verdict Q9** : le régime tenu n'est **PAS plus cher** (~−0,8 %/tick à 2 ans) —
  l'hypothèse « tenu → + biomasse → LightField plus cher » non confirmée à cet
  horizon. Trou de gameplay quantifié : `sol_nu → ravitaillement_manquant` (monde
  `full` sans chaîne de mulch).

**⑥ Vue Godot — automate branché dans `sim_server` (option F5)** — commit `b9c72ec`,
golden INTACT `3076c154…`, `dotnet build` vert.
- Python (pont **0.5.30**) : commande `automate` (`automate_cmd.py`, mixin) op
  on/off/objectif/status ; hook dans `cmd_step_week` (joue APRÈS `tick_semaine`,
  H2) ; bloc snapshot OPT-IN `automate` {profil, trace, objectifs} présent si actif ;
  `cmd_init` remet l'automate à None.
- C# : `SimBridge` +2 méthodes ; `WorldView.Automate.cs` (neuf) — touche **A**
  branche/débranche (panneau profil + objectifs + onglet + journal + impasses en
  rouge), **Maj+A** pousse un objectif démo. Profil F5 = LIBRE+curatif.

**⑦ Profil `semiologique` + banc d'écart omniscient↔semio** (optionnel/hors chaîne)
— commit `325643f`, golden INTACT `3076c154…`.
- `perception.py` : dataclass `PerceptionSemio` (ne lit que `plant.etat` +
  `leaf_symptoms` + sprites visibles, comme un joueur humain) ; `diagnostic.
  facteur_limitant` polymorphe (dispatch omni/semio) ; `impasses.py` type
  `FACTEUR_INVISIBLE` ; banc `semiologie_ecart.py` (neuf) = matrice de confusion +
  chiffre de qualité sémiologique.
- **Verdict** : qualité sémiologique ≈ **16 %** (`full`/1 an) — signes hydriques/
  ombre tardifs (miroir du dégât installé), `sol_nu`/`sol_compacte` structurellement
  invisibles. Défaut de design #5 **chiffré** (pas un bug ; kickoff interdit d'ajouter
  un signe pour boucher le trou) → piste versée en dette.

## Bilan

- **Golden final `3076c154dc3d5fbff8a4e32414be6d7ed4ad30b6970cd2c3114d49717b515253`**
  — **0 re-figeage** sur tout le sprint (invariant H2 : automate hors tick). Déterminisme
  3/3, `test_automate_troncon2` 9/9, `dotnet build` vert.
- Refactor auto-léger **no-op** (tous les fichiers touchés en 🟢, max 125 LDC pur ;
  aucun fichier franchi en rouge par le sprint).
- **Dette ouverte** : **D78** (ce sprint) → FAIT ; **D79** (système de quêtes complet :
  sources diégétiques courrier voisin/oncle/enfant, objectifs à condition d'état
  « kiwi de 5 m »/« trèfles fleuris », panneau de quêtes Godot, voix narratives) ;
  piste ⑦ (signe de sol au niveau plot, ou signe hydrique précoce — corriger le trou
  sémiologique) à trancher par Nico en sprint séparé.
- **Reste F5 Nico** (Godot pas sur la VM) : touche **A** tient le jardin visiblement +
  panneau lisible (profil, objectifs+progression, onglet, journal, impasses en rouge) ;
  **Maj+A** → l'onglet progresse (⚠ tomate meurt tôt : viser une cible robuste, ex.
  basilic, pour voir l'onglet avancer) ; perf tenue au régime automate.
