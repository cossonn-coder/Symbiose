# ② La chute sème — recrue unifiée sur les vrais fruits, glands, glandée (D42)

Lire d'abord : `CLAUDE.md`, `00_etat.md`, doc
`docs/faune/vie_macro/conception_zoochorie.md` §4.2-4.3. Socle ① fait
(`grain_sauvage`, `deposer_grain_sauvage`, levée par la niche).

## Objectif
Pour les **fruitiers pérennes à graine fertile**, la relève ne vient plus du tirage
abstrait de `_reproduction` mais des fruits qui **tombent** : chaque cohorte qui chute
dépose sa chair (inchangé) ET des grains sauvages (`origine="chute"`). Chêne et hêtre
deviennent fruitiers (glands, faînes) avec **glandée**. Puis on **recalibre** la relève
(critère D130 : remplacement ≥ 1 par génération, sans fourré).

## Périmètre « unifié »
Espèce concernée ⇔ `fruitier` ET `life_cycle == "perennial"` ET `graine_fertile(cls)`
(`sim/reproduction.py`). Aujourd'hui : pommier, cerisier, noyer, framboisier, fraisier ;
après ce tronçon chêne et hêtre ; au ③ le noisetier. Figuier : stérile → ni grains ni
recrue (rejets de souche seulement, inchangé). Tomate, courgette (annuelles) :
inchangées. Écrire un prédicat unique (ex. `recrue_par_fruits(cls)`) lu aux deux
endroits.

## Fichiers et modèle
- `sim/engine/mortalite.py::_reproduction` : `continue` en tête de boucle pour les
  espèces `recrue_par_fruits` (ni `add_species`, ni recrue directe). Les autres
  espèces : strictement inchangées.
- `sim/engine/decompo.py::deposer_fruits` (appelé à la chute des sur-mûrs ET à la
  nouaison pour la cohorte de l'an passé) : pour une espèce unifiée, après la litière,
  `n = nombre × P_GRAIN_CHUTE` (placeholder ≈ 0,02 : la plupart des graines tombées
  sont mangées, pourrissent ou restent dormantes sans lever — à calibrer), partie
  fractionnaire résolue par `_hash_noise` (canal libre, à vérifier par grep des
  `week * N` existants). Les `n` grains vont sur des plots tirés par hash parmi les
  plots foliaires valides (arbre) ou au plot du pied (herbacée), position sous-plot
  déterministe. Gènes : `child_genes(mère, find_father(...))`, expression :
  `child_expression(mère)` — mêmes fonctions que `_reproduction`. Plafond par plot
  (①) : un dépôt refusé est perdu. `deposer_fruits` n'a pas `seed`/`week` ni la liste
  des plantes : élargir la signature au besoin (appelants : `_tick_fruits` et, à
  vérifier par grep, la mort/coupe).
- `plants/perennials/forestiers.py` : `OakTree` et `BeechTree` → `fruitier = True`,
  `fruits_par_site`, `fruit_masse`, `fruit_semaines_maturation` (gland mûr fin
  septembre-octobre, faîne idem) [ordres de grandeur, commentés comme le cerisier].
  Vérifier qu'ils nouent : `pollination_mode = "wind"` → la dose vient du panache
  anémophile (`sim/engine/anemophilie.py`) ; un chêne seul peut ne rien nouer —
  c'est le modèle, le noter.
- **Glandée** : trait `glandee_periode_ans = None` (`plants/base/familles.py`) ;
  chêne ≈ 4, hêtre ≈ 6 [odg]. Fonction pure `facteur_glandee(cls, annee, seed)` :
  `None` → 1,0 ; sinon année forte si `_hash_noise(seed, annee, id_espece, 0) <
  1/période` → 1,0, sinon `GLANDEE_MAIGRE` (≈ 0,15). Le hash ne dépend QUE de
  l'espèce et de l'année (synchrone pour tous les pieds). Multiplie `frac` dans
  `_tick_fruits` avant `nouer`. Identifiant d'espèce stable : le `name` haché, pas
  `id()`.
- Encyclopédie chêne/hêtre : niveau 2 mentionne glands/faînes et les années de
  glandée (`sim/encyclopedie_corpus/ligneux.py`).

## Recalibrage (critère D130)
`data/code/tools/diag_releve.py` sur `verger_mur` (seed 42, 200 ans) ; le banc coupe
la germination férale (`germination_candidates = []`) mais PAS
`_lever_grains_en_attente` — vérifier que les grains lèvent bien dans ce banc.
Critères : chaque espèce unifiée à graine fertile (pommier, cerisier, noyer) a un taux
de remplacement ≥ 1 ; fourré ≤ 10 petits ligneux sous une couronne. Levier unique :
`P_GRAIN_CHUTE` (et au besoin `GRAINS_SAUVAGES_MAX_PLOT`). Pas de disperseur encore :
la relève sera plus proche du parent qu'au ⑦ — c'est attendu. Consigner [n=1 run]
dans `00_etat.md`. Le run est long : le lancer en arrière-plan, vérifier la charge VM
(`uptime`) avant toute mesure de temps.

## Ne PAS faire
- Ne pas toucher aux espèces non unifiées dans `_reproduction`.
- Ne pas changer le chemin `manger` / récolte du joueur.
- Ne pas créer de disperseur (④-⑥).
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Tests
`tests/test_chute_seme.py` : (a) un cerisier mûr dont une cohorte tombe dépose des
grains `chute` sous sa couronne, aux gènes hérités ; (b) plus aucune recrue directe
pour lui (contre-factuel : ancien code → recrue directe) ; (c) figuier : 0 grain ;
(d) glandée synchrone : deux chênes, même année → même facteur ; sur 40 ans, part des
années fortes ≈ 1/4. Mettre à jour `tests/test_banque_semis.py` (d)/(e) et
`test_figuier_realiste` si leurs prémisses (recrue directe d'un arbre) tombent : les
réécrire sur le nouveau chemin, ne pas les supprimer.

## Golden
`a10b7225…` **INCHANGÉ** attendu : le pommier du smoke a < 5 ans (jamais fructifère),
aucun chêne/hêtre. Si le hash bouge, chercher la cause (ne pas re-figer).

## Perf
`full` 5 ans, tick médian an 3-5 avant/après, ≤ +10 %.

## F5
Aucun (vue au ⑧).
