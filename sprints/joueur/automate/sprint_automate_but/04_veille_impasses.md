# Tronçon ④ — Veille, re-sonde, impasses honnêtes

> Sprint **Automate dirigé par le but** (D87). Conception :
> `docs/joueur/automate/conception_automate_but.md` (§4, §5). Lis `CLAUDE.md` +
> `00_etat.md` + ce fichier. ①-③ sont faits : la planif est branchée et émet des
> plans créatifs + des veilles brutes.

## Objectif

Rendre le planificateur **honnête dans le temps long** : gérer la **germination
incertaine** (`planter` ≠ plante), le **re-semis armé sur changement de condition**,
la **mise en veille + re-sonde sur déclencheur**, et les **impasses typées**. C'est
le tronçon qui empêche à la fois le retry cosmétique et le sur-replanning.

## Rappels

- `planter` dépose un `GrainEnAttente` qui lève PLUS TARD (plot libre + niche
  favorable) — peut ne **jamais** lever. Le sous-but « adulte présent » cache donc
  deux portes (lever, survivre) que Liebig ne garantit pas.
- État planif persistant (②) : `game_state["automate_plans"][obj_id] =
  {tentatives_semaille, essai_precedent:(saison,plot)|None, en_veille, chainon}`.
- `saison_de(engine.week)` (déjà importé dans `boucle.py`) donne la saison.

## Fichiers à toucher

- `tools/jardinier_auto/planification.py` — logique veille/re-sonde/re-semis.
- `tools/jardinier_auto/impasses.py` — 2 constantes neuves (voir plus bas).
- `tests/test_automate_planif.py` — étendre (réveil, re-semis armé, impasses).

## Modèle

### Suivi de germination (T1)

Quand `avancer_plans` émet un `planter` pour un objectif, enregistrer l'essai :
`essai_precedent = (saison_courante, plot_choisi)` et `tentatives_semaille += 1`.
Aux ticks suivants, tant qu'aucune cultivée vivante de l'espèce n'apparaît, le
grain est « en attente ». Distinguer :
- **germination réussie** (une cultivée vivante apparaît) → sous-but atteint,
  réinitialiser le suivi (le relais passe à Liebig). Trace `resultat`
  `{sous_but:"semer", issue:"leve"}`.
- **échec** (K semaines écoulées sans levée — `K = FENETRE_LEVEE`, constante
  nommée, p.ex. 3-4 sem — ET aucune cultivée vivante).

### Re-semis armé sur changement de condition (C3)

Sur échec de levée, un re-semis n'est **armé QUE si** au moins une variable a bougé :
`(saison_courante, plot_libre_courant) != essai_precedent`. Sinon → **impasse
`niche_defavorable` directe** (pas de retry cosmétique — la simulation déterministe
redonnerait la même mort). Garde-fou dur : `tentatives_semaille <= 2` ; au-delà →
`niche_defavorable` quoi qu'il arrive.

### Veille + re-sonde (Q7)

- `chainon_manquant` (pas de graine, pas d'offre magazine) et `niche_defavorable`
  mettent l'objectif **en veille** (`en_veille=True`, `chainon` renseigné), MAIS
  l'objectif **reste actif** (ne pas le marquer accompli/retiré). Impasse tracée
  **une fois** (patron `marquer_inatteignable_signale`).
- **Re-sonde sur déclencheur** (pas par tick) : à chaque tick, un objectif en veille
  est ré-évalué UNIQUEMENT si un déclencheur a changé son horizon :
  - `chainon_manquant` : l'offre magazine s'est ouverte (palier 3 atteint depuis) OU
    un plot s'est libéré → sortir de veille, retenter le chaînage.
  - `niche_defavorable` : la saison a avancé OU un autre plot libre existe → réarmer
    un re-semis (si `tentatives <= 2`).
  Implémente ça en comparant l'état courant aux conditions mémorisées ; garde tout
  **déterministe** (aucun compteur horloge). Trace le réveil (`plan`
  `{sous_but:…, raison:"reveil:<declencheur>"}`).

### Suffisance N dans les déclencheurs (C1)

Une cultivée qui MEURT alors que `progression < quantite` et `n_vivantes < nb_cible`
ré-arme l'« advenir » (re-planter) — déjà couvert par le comptage `n_vivantes` du ②,
mais VÉRIFIE que la mort d'une cultivée réveille bien un objectif non-accompli.

### Impasses (`impasses.py`)

Ajouter `CHAINON_MANQUANT = "chainon_manquant"` et `NICHE_DEFAVORABLE =
"niche_defavorable"`. (L'ancien `OBJECTIF_INATTEIGNABLE` d'`objectifs.py` reste pour
le cas « cible hors catalogue / aucune voie » ; les deux neufs sont plus précis et
portent le **chaînon nommé** dans leur `detail`.)

## Golden

**INTACT** (`57c166d8…`). Hors tick, opt-in. Vérifie `python3 -m tests.test_golden`.
**NE PAS lancer** `test_epaisseur_500ans` (interdit — long/inutile).

## Tests

- **Réveil chaînon** : objectif en veille `chainon_manquant`, puis on ouvre l'offre
  magazine (simuler palier 3) → au tick suivant l'objectif sort de veille et propose
  `acheter_magazine`.
- **Re-semis armé** : un `planter` échoue (pas de levée après K sem) ; même
  `(saison, plot)` → `niche_defavorable` directe, PAS de 2e semis ; saison avancée ou
  autre plot → un 2e semis armé ; `tentatives > 2` → `niche_defavorable`.
- **Objectif reste actif** en veille (pas marqué accompli) ; impasse tracée une fois.
- Déterminisme préservé (oracle du ①).

## Ne PAS faire

- NE PAS abandonner/retirer un objectif en veille (il reste actif).
- NE PAS re-semer sans changement de condition (retry cosmétique interdit).
- NE PAS masquer un bug bio : si la tomate meurt tôt, l'impasse `niche_defavorable`
  doit le RÉVÉLER (Q8), pas le contourner.
- NE PAS toucher le moteur/tick ni re-figer le golden.

## Fin de tronçon

Golden intact + tests verts → `00_etat.md` (§REPRISE : ④ fait, planif complète côté
moteur) + commit (`feat(automate ④) : veille + re-sonde + impasses honnêtes`).
