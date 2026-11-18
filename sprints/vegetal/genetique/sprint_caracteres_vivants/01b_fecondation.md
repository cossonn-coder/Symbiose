# ①b Fécondation — la fleur visitée fait des graines

> Lire d'abord : `CLAUDE.md`, `00_etat.md` (§① bilan + §Conception FÉCONDATION), puis
> `docs/vegetal/genetique/conception_caracteres_vivants.md` §6.
> Golden attendu : **RE-FIGÉ deux fois, annoncé** — (1) changement de scénario du smoke,
> (2) mécanique. Deux commits distincts, deux hashes consignés.

## Objectif
Le nombre de graines d'une plante dépend du pollen qu'elle a reçu, avec une assurance par
autofécondation ; le compteur `pollen_recu` repart de zéro à chaque floraison.

## À faire
1. **Smoke : un fruitier mûr** (`tests/test_golden.py`, `build_world`). Pré-vieillir le
   pommier comme le fait le jeu en config « full » (`tools/simserver/commands.py`, voir
   aussi `bancs/mesure_nouaison.py::_monde_full` : `age_years = maturity_years`).
   **Vérifier** qu'il fleurit et noue pendant le smoke (ligne `🍎 Nouaison` dans le log).
   Si ce n'est pas le cas, enquêter (stade, gdd, pollinisateurs sur T0) avant de toucher au
   moteur. Mettre à jour l'en-tête du test. `--capture`, consigner le hash, **commit seul**.
2. **`fecondation`** (nouvel attribut de `PlantInstance`, hors digest, défaut 0.0) figé à la
   **fanaison** pour **toute** plante vivante qui a fleuri (armement `a_fleuri` au-dessus de
   `SEUIL_FLEURI`, fanaison sous `SEUIL_NOUAISON` : le mécanisme existe pour les fruitiers
   dans `sim/engine/decompo.py::_tick_fruits`, il est à généraliser) :
   `fecondation = a + (1 − a)·frac_nouaison(pollen_recu)`, `a = plant.gene("autofecondation")`,
   mode `self` → 1. Puis `pollen_recu = 0`. Une seule fonction, réutilisée par la nouaison
   des fruitiers (qui ne fait plus `frac_nouaison` seul ; la glandée continue de multiplier).
   Les conditions propres aux fruitiers (maturité, `pollen_sterile` à la chaleur) restent
   dans le chemin des fruits ; à toi de voir si la stérilité thermique doit aussi bloquer la
   fécondation des herbacées (cohérent biologiquement : oui) et de le signaler.
3. **Lecteurs** : partout où la mise en graine lit `reproduction_rate`, utiliser
   `rate × fecondation` — `_reproduction` (`sim/engine/mortalite.py`, porte de hash ET
   densité déposée), `semer_fin_de_cycle` (`sim/engine/fin_de_cycle.py`, densité
   d'archétype ET pool). Graine récoltée par le joueur (`sim/engine/boucle.py`, phase
   récolte) : aucune si `fecondation == 0`. Après la mise en graine annuelle, **remettre
   `fecondation` à 0** (une plante qui ne refleurit pas l'an prochain n'a pas de graine).
   Vérifier au code l'**ordre** récolte (11) → reproduction (11b) avant de placer cette
   remise à zéro : elle doit suivre le dernier lecteur de l'année.
4. **Part autofécondée** (`sim/reproduction.py::heredite`) : le tirage d'autofécondation
   compare au seuil `a / fecondation` au lieu de `a` (borné à 1). Si `fecondation <= 0`
   (appelants hors cycle floral : zoochorie, caches…), garder `a` (comportement actuel).
   Recenser au `grep` tous les appelants de `heredite`/`child_genes` et le noter.
5. **Inventaire de risque** (banc headless, monde « full », 3 ans) : pour chaque espèce,
   dose `pollen_recu` à la fanaison (min/médiane/max) et `fecondation` ; lister les espèces
   qui produisaient des graines avant et **n'en produisent plus** (jamais fleuries, mode
   `wind` sans vent…). **Ne pas corriger en silence** : consigner dans `00_etat.md`. Seule
   exception autorisée : une espèce sans cycle floral réel (spores, ex. sphaigne en mode
   `self`) garde `fecondation = 1` sans fleurir, à justifier.
6. **Banc** : relancer `mesures/banc_fleurs.py` (a) ; attendu : la moitié bleue des
   bourraches a une `fecondation` moyenne plus haute que l'autre. Le pool de bourrache
   n'est pas encore levé (c'est ①d) : mesurer la fécondation et la densité déposée, pas
   la descendance.
7. **Perf** : smoke avant/après, paires alternées, budget ≤ +2 %. Vérifier la charge de la
   VM avec `uptime` avant de mesurer.

## Tests
- Ciblés : `fecondation` = 1 en mode `self` ; = `a` sans pollen ; croît avec `pollen_recu`
  et tend vers 1 ; `pollen_recu` vaut 0 après la fanaison ; une plante non fleurie ne
  dépose rien ; sans pollen, toutes les graines sont autofécondées (F de l'enfant > 0).
- Suites existantes vertes (fruits, nouaison, vent, lot2, caractères fleurs). Adapter
  `tests/test_fruits.py` si sa valeur attendue suppose `frac = g(pollen)` seul (la
  nouvelle formule, avec `a`, est voulue).

## Golden
(1) Re-figé par le scénario : diff du digest lu, le pommier porte des fruits. (2) Re-figé
par la mécanique : 1ʳᵉ divergence attendue à la première fanaison d'une herbacée
pollinisée par insectes. Consigner les deux hashes et `population_hash` s'il bouge.

## Ne PAS faire
- La paternité (①c), la levée des pools et la pondération de `choisir_espece` (①d).
- Calibrer `POLLEN_DEMI` : mesurer seulement, consigner la saturation observée.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.
- Ne pas appeler DeepSeek en routine (règle du sprint-auto, `CLAUDE.md`).

## Fin de tronçon
`00_etat.md` : ①b FAIT, hashes, inventaire de risque, mesures. Commit.
