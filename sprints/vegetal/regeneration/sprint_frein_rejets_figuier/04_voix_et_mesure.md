# ④ Voix du rejet de souche + mesure 200 ans

À lire d'abord : `CLAUDE.md`, `00_etat.md`,
`docs/vegetal/regeneration/conception_rejets_de_souche.md` §6-7,
`../sprint_releve_ligneuse/00_etat.md` §Tronçon 4 (mesure de référence).
Prérequis : ①-③ faits.

## 1. Voix
- **Événement** : la ligne de log du ②/③ devient un événement au ledger
  (`sim/evenements.py` ; suivre le patron de `ramet`, cf. `tests/test_evenements.py`
  ~l.102). Type au choix, p. ex. `("rejet", "souche")`.
- **Carnet** (`sim/carnet.py`) : la cause `rejet_de_souche` existe déjà
  (`("coupe", "receper")`, ~l.156) → y rattacher le nouvel événement ; gabarits
  descriptif (« des rejets partent au pied du figuier mort ») et interprétatif
  (la souche gardait ses réserves ; un arbre mort d'ombre ne repart pas). Vérifier
  le gabarit existant avant d'en écrire un.
- **Encyclopédie** (`sim/encyclopedie_corpus/ligneux.py` + fichiers voisins
  selon l'espèce) : pour chaque espèce à `rejet_souche > 0`, une phrase au niveau
  2 ou 3 (rejette fort / un peu) ; le sapin : « ne rejette pas ». Corriger la
  phrase du figuier posée au ③ de la relève (rejets après perte, pas en continu).
- Pas de page secrète obligatoire.

## 2. Outil de mesure
`data/code/tools/diag_releve.py` classe la voie de naissance `graine`/`ramet` en
lisant le log. Ajouter la voie `rejet` (nouvelle ligne de log). Ne rien casser
d'autre.

## 3. Mesure (VM, vérifier la charge avec `uptime` avant)
`python3 -m tools.diag_releve --config verger_mur --annees 200 --seed 42 --sortie <scratch>`
(~90 min attendues ; tourner en arrière-plan). Critères (conception §6) :
- fourré max ≤ 10 sous toute couronne ;
- remplacement ≥ 1 pour chaque espèce dont un fondateur meurt pendant le run ;
- figuiers vivants à l'an 200 ≤ 10 ;
- tableau par espèce comme au ④ de la relève, avec la colonne voie `rejet`.
Perf `full` : tick médian an 3/4/5 avant (commit de début de sprint, worktree) /
après, critère ≤ +10 %. Tout chiffre avec ses crochets [n=…, VM].

Si un critère rate : **ne pas re-concevoir**. Calibrage autorisé dans les bornes
suivantes seulement : `N_REJETS_MAX` 1-4, `RAYON_REJET_CM` 40-100,
`SEUIL_PERTE_COURONNE` 0,3-0,7, seuils de souche vivante ±25 %. Au-delà :
consigner dans `00_etat.md` comme décision pour Nico.

## Golden
**INCHANGÉ** (voix et outil hors digest). S'il bouge : STOP.

## Tests
`test_evenements`, `test_carnet`, `test_encyclopedie`, `test_rejets_souche`,
`tests.test_golden`. **Jamais `test_epaisseur_500ans`.**
