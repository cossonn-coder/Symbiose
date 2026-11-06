# sprint_chronique_especes — état du sprint (D127, outillage des runs longs)

**Sujet** : outiller les runs longs (D127, Nico 2026-11-06 : « il faut s'outiller
pour ») — savoir QUAND une espèce disparaît et DE QUOI.
**Phase** : conception FIGÉE le 2026-11-06 (accord Nico), prête pour
`/sprint-auto sprint_chronique_especes`. Conception :
`docs/perf/run_eternel/conception_chronique_especes.md`. Golden `a10b7225…`
INTACT sur tout le sprint ; pont 0.6.9 → 0.6.10 au ②.

## Tronçons
| # | kickoff | état |
|---|---|---|
| ① | `01_causes_de_mort.md` — espèce + cause canonique des morts, carnet, aide, tests | FAIT 2026-11-06 (golden `a10b7225…` intact, non commité) |
| ② | `02_chronique.md` — module serveur, `cmd_perf_report`, pont 0.6.10 | FAIT 2026-11-06 (golden `a10b7225…` intact, non commité) |
| ③ | `03_outil_sans_ecran.md` — `tools/chronique_run.py` + run `verger_mur` 200 ans → D127 | FAIT 2026-11-06 (golden `a10b7225…` intact, non commité) |
| ④ | `04_vue_rapport_c.md` — section `[chronique]` touche C, `dotnet build`, clôture | à faire |

## Constats vérifiés au code (2026-11-06)
1. `tools/simserver/perf_annees.py` : `MAX_ANNEES = 60` → un run de 192 ans ne
   montre que les 60 dernières années. « Plus que des noyers dès l'an 132 » de
   D127 est très probablement le BORD DE LA FENÊTRE, pas un fait écologique.
2. Bilan annuel = `top` 3 espèces seulement → une espèce minoritaire qui
   s'éteint est invisible.
3. Causes de mort : le moteur ne journalise la mort que par le `log` texte.
   `sim/evenements.py` lit `🪦` (sénescence/asphyxie) et range TOUT `✗` en
   « conflit ». Or plus aucune mort par conflit n'existe (`mortalite.py:254`,
   `regress()` retiré) : chaque `✗` est un `ReduceHealth` (herbivorie, maladie,
   gel, grêle, vent, stress hydrique, carence lumineuse, fonte des semis,
   mortalité de fond, limaces/chenilles). Le `[reason]` est DÉJÀ dans la ligne
   (`Santé X@pos -n [reason] → meurt`). Conséquence jeu : le carnet écrit « a
   cédé la place à plus vigoureux » pour une plante mangée. `❄` (annuelle à
   l'hiver) et `✿` (bisannuelle) sans cause. Gestes (`gestes.py`, greffe)
   hors log ✗.
4. Golden = hash du `log` + digest final → changer le TEXTE du log re-fige ;
   lire `[reason]` côté `evenements.py` est golden NEUTRE.
5. Outils existants : `tools/diag_population.py` (headless, top 6 tous les 26
   ticks, sans causes), rapport C (touche C, `cmd_perf_report`), bancs
   `bancs/verger_mur.py`.

## Décisions arrêtées
- A1 (Q1) chronique VM + rapport C, MÊME code de comptage : outil headless que
  Claude lance seul (200 ans en fond) + section au rapport C des runs PC.
- A2 (Q2) la lecture des causes se corrige UNE fois dans `sim/evenements.py`
  (lire `[reason]` des `✗`) ; le carnet et l'aide en profitent (textes par
  cause). Golden intact.
- A3 (Q3) périmètre = toutes les espèces végétales ; faune renvoyée à D119.

## Constats complémentaires (2026-11-06)
6. Sur une ligne `✗ Santé Pommier@(3, 4) -1 [herbivorie …] → meurt`,
   `evenements()` rend `espece=None` (préfixe « Santé » non retiré) ET
   `cause="conflit"` (vérifié en Python). `tests/test_evenements.py` teste un
   format `✗ Tournesol@(8, 8) meurt (conflit)` que le moteur n'émet plus.
7. Raisons `ReduceHealth` relevées : `herbivorie p=…`, `Limaces`, `Chenilles`,
   `maladie fongique`, `oïdium`, description d'effet d'espèce (mildiou…),
   `fonte des semis`, `gel (tissu tendre)`, `Gelée tardive`, grêle,
   `vent (tige cassée)`, `stress hydrique sévère`, `carence lumineuse`,
   `mortalité de fond (noise=…)`. Précédent de lecture : `tests/diag_morts_field.py`.
8. `verger_mur` : levées coupées, herbivorie coupée. Longévités : cerisier 60,
   pommier 70, figuier 80, noyer 200, onset 0,7, plantés à 15-16 ans → hypothèse
   (non mesurée) : fruitiers morts de vieillesse vers l'an 30-65 du run, d'où
   « plus que des noyers ». Mais 2 → 5 noyers prouve un recrutement par une
   autre voie (dépôt génétique de `_reproduction`) : à trancher par le run ③.

## Proposition validée (OK Nico 2026-11-06)
Causes canoniques : herbivorie · maladie · gel · grêle · vent · sécheresse ·
ombre · usure (mortalité de fond) · sénescence · asphyxie · fin_de_cycle
(`❄`/`✿`) · autre (raison brute gardée, jamais « conflit » par défaut). Concept
carnet : herbivorie→ravageurs, maladie→maladie, gel/grêle/vent→météo,
sécheresse→eau, ombre→lumière (noms à vérifier au code par le tronçon).
Tronçons (golden INTACT partout) :
- ① causes lues : `sim/evenements.py` + textes carnet D/I + remèdes `aide.py` + tests.
- ② chronique : module côté serveur (effectifs/an toutes espèces, morts/an
  espèce×cause, levées/an, registre des disparitions et retours non borné),
  alimenté après le tick ; section texte composée côté Python, rendue dans
  `cmd_perf_report` ; pont bump.
- ③ outil sans écran `tools/` + premier run `verger_mur` 200 ans VM → faits dans D127.
- ④ vue : le rapport C (touche C, `WorldView.PerfReport.cs`) affiche la section
  telle quelle ; `dotnet build` ; F5 = Nico presse C sur un run.
Coût : ① nul dans le tick ; ② comptage O(N) par tick ≤ ~1 ms [estimation, non mesurée].

## Tronçon ① — fait (2026-11-06)
- `sim/evenements.py` : `Evenement` gagne un 6ᵉ champ `raison` (défaut None ;
  rempli SEULEMENT pour une mort `autre` = raison brute, pour la chronique ②).
  Table `CAUSE_DE_RAISON` (préfixes casefold) + `cause_de_raison(raison)` publique
  (réutilisable par ②). Branche `✗` : regex `_RE_MORT_SANTE` (préfixe « Santé »
  retiré, exige `→ meurt`). Branche `❄`/`✿ … meurt` → `fin_de_cycle`. Plus aucune
  production de `conflit` (`_RE_CONFLIT` gardé, inutilisé). `_evenements` intact.
- Seul effet d'espèce `reduce_health` au code : « Sensibilité familiale au
  mildiou » (Solanacées) → `maladie`.
- `sim/carnet.py` : concepts (herbivorie→ravageurs, maladie→maladie, grele/vent→
  météo, secheresse→eau, ombre→lumière, fin_de_cycle→sénescence ; usure/autre sans
  concept → fallback `observation`) + gabarits D/I. `sim/aide.py` : remèdes milieu
  pour herbivorie/maladie/grele/vent/secheresse/ombre (pas usure/autre/fin_de_cycle).
- Tests : `test_evenements` 42/42 (format réel via `apply_mutations`), carnet,
  maitrise_detection, journal, peripherie_voix, inoculum, flore_spontanee, vent verts.
- Hors log (non lus, à savoir pour ②) : annélation campagnol (`vitalite=0` direct,
  `perturbations.root_herbivory`) et gestes joueur → morts « hors tick ».
- Effet de bord : les annuelles mortes à l'hiver produisent désormais une entrée
  carnet `fin_de_cycle` (le ledger se remplit un peu plus vite, borné JOURNAL_MAX).

## Tronçon ② — fait (2026-11-06)
- `tools/simserver/chronique.py` (classe `Chronique`, 121 LDC) : comptage par
  IDENTITÉ des plantes vivantes (`id(p)`→p, référence tenue), DEUX recensements par
  semaine : `avant_tick` (hors chrono) → morts entre deux ticks = `hors_tick`
  (gestes joueur/automate) ; `apres_tick(engine, log)` → morts du tick appariées à
  l'événement `mort` de `evenements(log)` par (tuile, plot, espèce), sinon
  `non_consignee` (annélation campagnol). Levées = plantes NOUVELLES entre deux
  recensements, toutes voies. Raisons brutes des morts `autre` → `autres`.
  Bilan clos à `semaine % 52 == 0` ; année d'une semaine = `ceil(s/52)` (même n°
  que `perf_annees`). Registre non borné disparition (semaine, espèce, cause, âge,
  tuile) / retour. `texte()` = seul formateur ; `brut()` = {annees, registre}.
- `commands.py` : `Chronique()` à l'init ; `avant_tick` avant `SONDE_TICK.debut()` ;
  `apres_tick` juste après `J.consigner`, avant `gs["log"].clear()` ;
  `perf_report.chronique = {texte, brut}`. Pont 0.6.10 (`version.py` + 4 tests
  `tests/simserver/` qui épinglent la version).
- Écarts au kickoff : (a) levées NON lues au flux — l'événement `germination` est
  toute avance de stade 🌱 (pas une levée), la germination férale n'a pas de
  marqueur ; la différence d'identité est exacte. (b) `evenements(log)` est lu une
  3ᵉ fois (après `consigner` et `observer_apres_tick`) : partager le flux changerait
  `sim.journal.consigner` (moteur). (c) Périmètre = plantes des tuiles (pas des
  conteneurs, comme `perf_annees`) ; une plante déplacée hors tuile vivante compte
  comme mort `hors_tick`. (d) Pas d'« arrivée » d'une espèce jamais vue : seuls
  disparitions et retours.
- Tests : `tests/test_chronique.py` 14/14 ; `test_sim_server` 322/322 ;
  `test_perf_sonde` vert ; golden `a10b7225…` PASS.
- Coût mesuré (full seed 42, semaines 157-182 ≈ an 3, ~690 plantes, VM 16 cœurs
  charge ~1-3) : chronique 3,9 ms/tick médiane [n=26, VM] (max 4,8) pour un tick
  de 879 ms → 0,45 % [n=26, VM]. Un parse complet du log (~2 500-3 300 lignes)
  coûtait 12,8 ms [n=10, VM] → `apres_tick` ne passe à `evenements` que les lignes
  contenant « meurt » + les en-têtes `[T…]` (0,7 ms, mêmes événements `mort`).
  Écart à l'estimation de la conception (~1 ms) : deux recensements de ~1 ms
  chacun.
- Observé au passage (full, seed 42, 3 ans) : morts du trèfle surtout herbivorie
  (180/an 2) et vent (57) ; `non_consignee` présent (7 trèfles an 2).

## Tronçon ③ — fait (2026-11-06)
- `tools/chronique_run.py` (46 LDC) : `cmd_init` puis `cmd_step_week` × 52·N (MÊME
  chemin que le serveur → chronique identique au rapport C), écrit `chronique.txt`
  (`texte()`) + `chronique.json` (`brut()`), progression stderr tous les 10 ans.
  Snapshot jeté = 6,4 % du pas [verger_mur an 1, n=1, VM] < 30 % → pas de
  factorisation du post-tick.
- Run court `--config smoke --annees 2` OK (7 s). Run `verger_mur --seed 42
  --annees 200` : 93 min [n=1 run, VM, charge 0,65 → 8,8], sorties dans `mesures/`.
- Faits (détail dans D127) [seed 42, n=1 run, VM] : cerisier an 32, pommier an 41,
  figuier an 103 disparaissent tous par sénescence du dernier pied ; 30 recrues
  (noyer 18, figuier 9, pommier 3) ; 25 morts sur 34 par ombre ; 1 noyer en an 200.
  Hypothèse vieillesse tranchée pour les fondateurs ; point écologique ouvert dans
  D127 (recrues tuées par l'ombre, pas de relève), moteur NON corrigé.
- Écart : seed explicite 42 (le défaut serveur est `0x5AB1057E`) pour coller au run
  PC de D127 — même compte d'arbres en an 15 (9).

## §REPRISE
Lire ce fichier + D127 (`DETTE.md`). ①, ② et ③ faits. Prochaine étape : tronçon ④
`04_vue_rapport_c.md` (section `[chronique]` dans `WorldView.PerfReport.cs`,
`dotnet build`, clôture du sprint).
