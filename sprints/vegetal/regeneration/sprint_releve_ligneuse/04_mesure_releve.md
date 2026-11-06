# ④ Mesure — la relève tient-elle sur 200 ans, sans fourré ni surcoût ?

À lire d'abord : `CLAUDE.md`, `00_etat.md` (§Diag, §Décisions), `docs/vegetal/regeneration/conception_releve_ligneuse.md`. Prérequis : ①②③ faits.

## Objectif
Vérifier le critère de fin de D130 (Q1) et calibrer, dans des bornes fixées,
`H_GAULE` et `SEUIL_SEMIS` (`sim/effects/perturbations.py`). Un tronçon dont l'effet
n'est pas mesuré en jeu n'est pas un succès.

## Outil
Créer `data/code/tools/diag_releve.py` (gardé au dépôt) : `SimServer.cmd_init`
(config + seed), `cmd_step_week` × 52·N (même chemin que `tools/chronique_run.py`),
suivi par `id(p)` de chaque plante ligneuse absente au départ (espèce, position,
semaine de naissance, voie : recrue directe / ramet si lisible au log `🌿 Ramet`),
échantillon toutes les 13 semaines de `light_received`, `shade_memory`, hauteur
(`plant_class.height_at`). Sorties JSON + résumé texte :
- par espèce : recrues, recrues ayant atteint `maturity_years` vivantes, âge et
  cause de mort (lire la cause via la chronique ou le `[reason]` du log) ;
- **remplacement** : pour chaque fondateur mort, nombre d'individus de son espèce
  ayant atteint `maturity_years` (avant ou après sa mort) ;
- **fourré** : nombre max de ligneux vivants de hauteur < `H_GAULE` à moins d'un
  rayon de couronne de chaque adulte, sur tout le run ;
- présence de chaque espèce en fin de run.
Le diag de conception (75 ans, ~35 min VM) en est le patron (décrit dans `00_etat.md`).

## Runs (VM, en fond ; vérifier la charge avec `uptime` avant toute mesure de temps)
1. `verger_mur`, seed 42, 200 ans (~1 h 30) + `tools/chronique_run.py` si utile.
2. Perf : tick médian `full` seed 42 sur les années 3-5 avant (commit du début de
   sprint, `git stash` interdit : utiliser un `git worktree` du commit parent de ①)
   et après. Critère ≤ +10 %.

## Critères
- Chaque espèce ligneuse de `verger_mur` dont la graine est fertile (pommier,
  cerisier, noyer) : remplacement ≥ 1 par fondateur. Figuier : ≥ 1 rejet mûr.
- Pas de fourré : max ≤ 10 semis par couronne [choix de conception, à confirmer
  par Nico au F5].
- `full` : tick ≤ +10 %.

## Calibrage autorisé
`H_GAULE` ∈ [100, 400] cm, `SEUIL_SEMIS` ∈ [0,65 ; 0,85]. Chaque essai refait le
golden (doit rester `a10b7225…`). Hors bornes, ou si le critère reste raté : ne pas
forcer, consigner le constat chiffré (avec sa limite entre crochets) dans
`00_etat.md` et en reliquat de D130.

## Point connu
Le cerisier n'a eu **aucune** recrue en 200 ans au run D127 (pommier 3, même taux
0,15). Hypothèse non vérifiée : sa position (bord ouest, ombre de la ceinture
périphérique) n'offre aucun plot > 0,35 dans 150 cm. Si le cerisier n'a toujours
aucune recrue après ②, diagnostiquer (lumière autour, tirages) et consigner ; ne
pas corriger hors du périmètre (pas de dispersion animale : D42).

## Golden
INCHANGÉ. **Jamais `test_epaisseur_500ans`.** DeepSeek : non.
