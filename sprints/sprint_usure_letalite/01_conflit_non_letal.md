# ① Conflit non-létal — aligner le code sur la conception intra-plot (Q3)

> Kickoff AUTOSUFFISANT. Lis `CLAUDE.md` + `00_etat.md` + ce fichier. Tu ne sais
> rien d'autre : tout est ici. Source de vérité = Python `data/code/`. Lancement
> depuis `data/code/`.

## Objectif
Rendre le **conflit spatial NON-LÉTAL**. Aujourd'hui `_resoudre_conflits`
(`sim/engine/mortalite.py`) résout les `ConflictNotification` en appelant
`loser.regress()`, qui régresse d'un stade et, au stade 0, met `health = 0`
(MORT). Une plante saine peut donc mourir en un tick — pire, deux conflits d'une
même paire (un `foliar`, un `root`) se résolvent le même tick → **double
régression** jeune→semis→mort (bug D64, tournesol du banc `grimpantes`).

C'est en contradiction avec une décision DÉJÀ figée
(`docs/conception/CONCEPTION_COMPETITION_INTRAPLOT.md`, Q3) : *« la mort du perdant
ÉMERGE du déclin de santé — jamais de mortalité verdict »*. Ce tronçon aligne le
code : le conflit reste une **notification** (détection conservée), sa résolution
n'inflige plus rien. La mort du dominé tombe des voies continues déjà en place
(ombrage LightField → `shade_stress_damage`, ponction racinaire partagée,
sénescence). **Mesuré** : sans le regress-kill, le dominé décline lentement, pas
de zombie (cf. `00_etat.md`).

## Fichier à toucher
`data/code/sim/engine/mortalite.py` — méthode `MortaliteMixin._resoudre_conflits`
(≈ lignes 217-235). **Un seul fichier.**

## Ce qu'il faut faire
Dans `_resoudre_conflits` :
- **Conserver** `tile.detect_conflicts()` et le log des conflits (notification
  diégétique — ne rien retirer de la détection).
- **Supprimer la résolution létale** : plus d'appel à `loser.regress()`, plus de
  `c.resolved = True` destiné à sceller une mort, plus de `deposer_mort(loser, …)`
  dans ce chemin. Le bloc `if c.weeks_active >= loser.plant_class.space_tolerance_weeks:`
  qui régressait/tuait disparaît.
- **Borner `tile.conflicts`** (sinon la liste enfle) : marquer `resolved = True`
  (donc élaguable) un conflit **périmé** — dès qu'une de ses plantes est morte
  (`not p.is_alive`) OU que le chevauchement a disparu (les plots litigieux ne
  sont plus co-occupés). Un simple passage : pour chaque conflit non résolu,
  `c.tick()` puis, s'il est périmé, `c.resolved = True`. Garder le log
  « ⚠ Conflit … » des conflits actifs pour la notification.
- La méthode retourne toujours son `log` (liste de chaînes).

## Ce qu'il NE faut PAS faire
- Ne PAS toucher `PlantInstance.regress()` (`plants/base/instance.py`) : elle
  devient **inutilisée** mais on la **conserve** (règle projet « ne jamais jeter
  de code »). Signale-le juste dans `00_etat.md`.
- Ne PAS toucher `detect_conflicts` (`world/tile.py`) ni le double comptage
  foliar/root : il devient inoffensif une fois la résolution non-létale (deux
  notifications au lieu d'une = cosmétique). Ne pas « réparer » le loser/âge.
- Ne PAS implémenter le §2.3 (densité incluant co-occupants) : mesure = pas de
  zombie, hors périmètre.
- Ne PAS ajouter de mortalité de remplacement : la mort DOIT rester émergente
  (`_tick_senescence_health` + voies de stress).

## Golden attendu — RE-FIGÉ (annoncé)
Le smoke exerce des morts par conflit : elles disparaissent/glissent vers le
stress. Hash **mesuré à l'avance** pour la neutralisation exacte du regress-kill :

    a6c2f651…  →  a1c9c51f61c60fd6edf2500663ebcecfb9eac9d02a1120670f7ecf3fecd434cf

Procédure : depuis `data/code/`, `python3 -m tests.test_golden` (doit FAIL avec
divergence), vérifier que le hash obtenu == `a1c9c51f61c60fd6edf2500663ebcecfb9eac9d02a1120670f7ecf3fecd434cf`,
puis re-figer `python3 -m tests.test_golden --capture`. **Si le hash obtenu diffère
de cette valeur**, c'est que le pruning a un effet de bord sur l'état des plantes
(il ne devrait pas — il ne touche que `conflicts`) → STOP, investiguer, ne pas
capturer à l'aveugle.

## Vérifications
- `python3 -m tests.test_golden --capture` → hash `a1c9c51f…` consigné.
- Suites ciblées : `python3 -m tests.test_competition` (compétition émergente —
  ne doit pas régresser ; si une assertion supposait la mort par conflit, la
  corriger vers la mort émergente et le signaler). Lancer aussi
  `python3 -m tests.test_senescence`.
- Repro du bug résolu : construire `bancs.grimpantes()`, `Engine(week=9)`, avancer
  ~30 semaines → le **Tournesol@(2,2) survit** (plus de mort à w12).

## Mise à jour de fin de tronçon
`00_etat.md` : marquer ① fait, nouveau golden `a1c9c51f…`, noter que
`regress()` est désormais inutilisé (conservé). Commit (message style projet,
fichiers nommés).
