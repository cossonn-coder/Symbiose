# ⑦bis Bois mort en continu (ceinture + décompo par grosseur) & parasite qui tue

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (§②ter : un seul jeune arbre dans `full` →
0 branche/an, le bois initial fond ~60 %/an ; §④ : le parasite plafonne la perte racinaire
à ~50 % et ne tue jamais).
**Golden** : RE-FIGÉ annoncé si la décompo du `bois` change pour une parcelle du smoke
(B) ou si le pommier du smoke meurt/décline par le parasite (C) — dérive expliquée, hash
consigné, une fois en fin de tronçon. A (ceinture) : le smoke n'a pas de ceinture → neutre.
**Décisions Nico (2026-10-22)** : « oui la ceinture forestière fournit du bois » ; « le bois
met plus de temps à se décomposer s'il est plus gros (et les tiges de l'année des plantes
comme courge, tomates etc. se décomposent assez vite) » ; « le parasite peut tuer : oui ».

## A. La ceinture forestière fournit du bois
- Les secteurs boisés de la ceinture (`fields/peripherie.py` : `densite_ligneuse`, hauteur,
  `plots_de_bord(cote, rows, cols, …)`) laissent tomber du bois dans les plots de BORD du
  jardin qui les jouxtent (couronnes qui débordent, branches portées par le vent).
- Masse ∝ densité ligneuse × hauteur du secteur, décroissante avec la distance au bord
  (pénétration de quelques plots, ordre de grandeur d'une couronne). Plus en tempête
  (même signal vent/rafale que `sim/engine/branches.py`) et en automne-hiver. Un secteur
  coupé/défriché (`couper_secteur`) en fournit moins : la cause reste au milieu (philo #1).
- Déterministe (hash, jamais de RNG vivant), écrit par la couche `sim/engine` via
  `eco.deposer_litiere(r, c, "bois", masse)`.
- Cible : le bois au sol de `full` ne tend PAS vers 0 sur 2-3 ans (flux ≳ décomposition),
  concentré en lisière, et c'est là que les saprophytes du bois (pleurote, hypholome,
  collybie) fructifient.

## B. Le bois se décompose selon sa grosseur
- Écologie : brindilles (< 1 cm) 1-3 ans ; branches (1-10 cm) 5-10 ans ; troncs/souches
  (> 10 cm) plusieurs décennies. Aujourd'hui `bois` = un seul taux (0,02/sem, constants.py
  `TISSU`) → tout fond ~60 %/an.
- Intention : le taux de décompo du bois dépend de son DIAMÈTRE. Deux voies, au choix du
  sous-agent après lecture des lecteurs de `bois` (fongique, pont, NPK, faim d'azote, pile) :
  (a) un attribut de grosseur moyenne par parcelle `bois` (fusion pondérée par la masse,
  comme `age_sem`) qui module le taux — lecteurs inchangés ; (b) des classes de tissu
  séparées (ajoutées EN FIN de `TISSU_ORDER`). Préférer (a) si elle suffit.
- Tous les écrivains de bois passent leur grosseur : branches tombées (`thickness_cm` du
  segment), squelette à la mort (`deposer_mort`), arbustes, bois initial (souches/branches
  d'âges variés, `sim/bois_initial.py`), ceinture (A), gestes joueur (`sim/actions/gestes.py`).
- **Tiges de l'année** (courge, tomate, annuelles) : vérifier qu'elles vont bien en
  `herbace` (décompo rapide, 0,15/sem) et JAMAIS en `bois` ; le tester.
- Pont : exposer la grosseur (la vue ⑧ dessine branche vs souche).

## C. Le parasite peut tuer
- Lever le plafond de perte racinaire (`sim/engine/racines.py`, ~50 %) pour qu'un hôte
  affaibli attaqué durablement perde ses racines jusqu'à mourir — de préférence par la
  voie déjà en place (`eau_percue` → stress hydrique → mort), pas une mort ad hoc.
- Garde-fous : un hôte SAIN n'est jamais attaqué (inchangé) ; un hôte qui se rétablit
  (meilleure eau/lumière) peut s'en sortir ; la mort passe par `deposer_mort` → squelette
  de bois → saprophytes : la boucle de la conception est fermée.
- Cible [ordre de grandeur, n à consigner] : banc hôte affaibli + parasite → mort en
  quelques années ; hôte sain → jamais.

## Mesure & vérif
- `mesures/bois_mort.py` + `mesures/fongique.py` + `mesures/parasite.py` : graine
  1521550718, `full`, 156 sem. [n=1 run] : masse de bois sem. 0/52/104/156, plots en
  lisière vs centre, fructifications des saprophytes du bois, morts par parasite.
- Tests : étendre `test_bois_mort` (gros bois plus lent que brindille ; tige de tomate =
  `herbace` ; ceinture dépose en bord seulement ; secteur coupé → moins) et `test_parasite`
  (hôte affaibli meurt ; hôte sain jamais ; déterminisme).
- **Perf** : ≤ +5 % de tick vs après ⑦ (D114 ouverte, ne pas la résorber ici).
- Bump du pont si le snapshot change.

## Ne PAS faire
Pas de C# (⑧). Pas d'ajout de plante dans `full`. Pas de RNG vivant. Pas de test 500 ans.
