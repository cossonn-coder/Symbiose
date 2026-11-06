# ② La chronique des espèces, côté serveur

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §3
(`docs/perf/run_eternel/conception_chronique_especes.md`).
**Prérequis** : ① fait (causes canoniques dans `evenements(log)`).
**Golden : INTACT** — tout se passe hors tick, dans le serveur.

## Objectif
Un instrument qui dit, sur un run de n'importe quelle longueur, **quand** chaque
espèce végétale disparaît (ou revient) et **de quoi** meurent les plantes.

## À faire
1. Nouveau module `tools/simserver/chronique.py` (une responsabilité, ≤ 300 LDC,
   commentaires pédagogiques). Patron : `perf_annees.py` (`ajouter` après tick,
   clôture annuelle à `semaine % 52 == 0`). Contenu :
   - bilan annuel : vivants par espèce (TOUTES), morts de l'année par
     espèce × cause, levées de l'année par espèce (événements `germination`,
     émissions clonales, `reproduction` du flux) ;
   - registre **non borné** des disparitions (dernier vivant mort : semaine,
     espèce, cause de cette mort, âge, tuile) et des retours (semaine) ;
   - morts hors tick (gestes joueur/automate, absents du `log`) comptées à part
     `hors_tick` : l'intention est de ne pas les perdre ; le moyen (écart de
     vivants entre fin de tick et tick suivant, ou autre) est à choisir au code ;
   - `texte()` : la section lisible, composée EN PYTHON (tableau tous les 10 ans
     + toute année avec disparition/retour, puis le registre complet). C'est le
     seul formateur : la vue et l'outil ③ l'affichent tel quel.
   Clés d'espèce : celles du catalogue (comme `evenements`), pas `__name__`.
2. Brancher dans `cmd_step_week` (`tools/simserver/commands.py`) après le tick,
   à côté de `self._annees.ajouter(...)`, en lisant `gs["log"]` AVANT
   `gs["log"].clear()`. Ne pas re-parser le log deux fois si le flux peut être
   partagé avec `J.consigner` sans changer son comportement (règle « pas de
   recalcul ») ; sinon une lecture de plus est acceptable, à signaler.
3. `cmd_perf_report` : ajouter `"chronique": {"texte": ..., "brut": ...}`.
4. Pont : bump `ENGINE_VERSION` dans `tools/simserver/version.py` (0.6.9 →
   0.6.10) avec sa ligne d'historique (ajout rétro-compatible).
5. Test `tests/test_chronique.py` : banc court déterministe où une espèce
   disparaît (ex. annuelle à l'hiver) → registre correct, causes comptées,
   texte non vide ; chronique hors serveur = golden inchangé.

## Mesurer
Coût par tick de `ajouter` sur `full` an 3 (≤ 1 % du tick attendu) [préciser n
et machine]. Vérifier la charge VM (`uptime`) avant toute mesure de temps.

## Vérifier
`python3 -m tests.test_golden`, `python3 -m tests.test_chronique`, `python3 -m tests.test_sim_server`.
NE PAS lancer
`test_epaisseur_500ans`.

## Ne pas faire
Toucher au moteur (`sim/`, `fields/`, `plants/`) ; borner le registre ;
formater côté C#.
