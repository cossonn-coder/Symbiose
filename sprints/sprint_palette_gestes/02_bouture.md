# ② BOUTURE (moteur + voix) — kickoff autosuffisant

> Sprint PALETTE DE GESTES. Lire d'abord : `CLAUDE.md` + `00_etat.md` +
> `docs/conception/CONCEPTION_PALETTE_GESTES.md` §3.5. Démarre à FROID.
> Prérequis : ① fait (le geste sera exposé/débloqué ; ici on l'IMPLÉMENTE).

## Objectif
Implémenter le geste **`bouturer`** : multiplication végétative par clone
génétique exact, à 2 temps (mère bouturable → plot cible). Réutilise le modèle
`sim/clonal.py`. Golden NEUTRE. + toutes ses **voix** (règle projet).

## Modèle (philo #1/#2/#3)
- **Gate d'espèce** : nouveau flag `bouturable: bool` sur `PlantBase` (défaut
  `False`). Le mettre `True` sur les espèces qui se bouturent réellement
  (ligneuses souples, aromatiques : saule, cassis, romarin, menthe… — choisis
  parmi le catalogue existant, `grep` les classes dans `data/code/plants/`). Ne
  crée PAS d'espèce neuve pour ce tronçon (le cadre suffit ; l'enrichissement du
  catalogue peut venir plus tard).
- **Gate physiologique** (réutilise le patron `clonal.py`) : mère VIVANTE,
  assez MÛRE (`clonal._mature`-like : dernier stade atteint), et Vigueur/santé
  suffisante (façade `vigueur_plante` au-dessus d'un seuil bas). Refus EN AMONT
  de toute dépense sinon (patron `planter`/lot vide).
- **Effet** : pose un clone sur le plot cible via `tile.add_plant(cls, r, c)` ;
  `ramet.genes = dict(mother.genes)` + `ramet.expression.update(mother.expression)`
  (priming maternel hérité, exactement comme `clonal.emettre_ramets`). Position
  continue = point du clic (2e temps). **Aucun brassage** (≠ reproduction).
- **Coût** : DÉTERMINISTE, double canal —
  (a) **Vigueur joueur** via `couts.cout_action("bouturer", …)` : ajoute
  `"bouturer"` à `COUTS` (proposition MODERE — geste direct sur le vivant, philo
  #1) + `OBJETS_TOUCHES["bouturer"] = ("bouture",)` (technique) ;
  (b) **bouffée de `stress_memory`** sur la MÈRE (`min(1.0, stress + COST)`,
  reprends `clonal.CLONAL_STRESS_COST` comme ordre de grandeur) : prélever un
  greffon fatigue le pied mère → arbitrage émergent, jamais malus direct.
- **Binaire tout-ou-rien** : le clone n'est posé QUE si le coût Vigueur est
  intégralement payé (`spend >= 1.0`), comme `planter`/`deraciner`.
- **2 temps côté pont** : 1er clic = désigner la MÈRE (plante par position/index),
  2e clic = le PLOT cible. Modèle exact = `epandre`/`deplacer_pot` (kind à 2
  temps). Le serveur mémorise la mère entre les deux clics.

## Fichiers à toucher
- `data/code/plants/base.py` : flag `bouturable` sur `PlantBase` (défaut False).
- Espèces concernées (`data/code/plants/species.py`/`perennials.py`) : `bouturable
  = True` sur les quelques espèces qui se bouturent.
- **Nouveau** `data/code/sim/actions/bouture.py` (≤ 300 LDC) : `def bouturer(
  game_state, player, mother, tile, eco, r, c) -> bool`. Réutilise les helpers de
  `clonal.py` (`_plot_of`, `_mature`, seuils) — importe-les ou factorise sobrement
  SANS casser `clonal.py`. Ne DUPLIQUE pas la logique de clonage : si un helper
  commun émerge, extrais-le proprement (mais reste minimal — 2 usages ≠ refonte).
- `data/code/sim/actions/couts.py` : entrées `bouturer` dans `COUTS` +
  `OBJETS_TOUCHES`.
- **Voie expérimentale émergente (D12)** — marqueur `bouture_spontanee` : la 3ᵉ
  voie de déblocage de `bouturer` (①) est « planter une branche taillée + la
  garder humide → elle s'enracine ». Modélisation SOBRE proposée : quand un geste
  `tailler`/`couper` produit un rameau ET que le joueur le **plante** puis que le
  plot reste humide assez longtemps pour un **enracinement spontané**, poser le
  marqueur `bouture_spontanee` au ledger du joueur (`game_state`, lu par
  `("evenement","bouture_spontanee")` en ①). Si la mécanique « planter un rameau
  physique » n'existe pas encore, **implémente le strict minimum** qui rende la
  voie jouable (ex. bouturer réussi une 1ʳᵉ fois via la voie savoir POSE aussi le
  marqueur ; OU un hook léger sur `planter` d'un rameau + humidité soutenue).
  Reste MINIMAL : la voie savoir composée (① `et`) est le chemin principal, la
  voie émergente est le bonus diégétique — ne sur-conçois pas.
- `data/code/sim/actions/__init__.py` : ré-exporter `bouturer` si le paquet le fait
  pour les autres gestes.
- **Voix** (règle « toute plante/tout geste = ses voix ») :
  - `data/code/sim/geste_corpus.py` : fiche 3 niveaux de `bouturer` (voix
    naturaliste ; N1 = ce qu'on voit, N2 = mécanisme clone génétique, N3 = rôle
    permacole + limites/contrepartie). Vérifie que `encyclopedie_types.type_de`
    classe bien `bouturer` en `"geste"` (le test du corpus l'exige).
  - Technique `bouture` : ajoute sa fiche dans `sim/technique_corpus.py` (miroir).
  - Concept carnet : si un `CONCEPT_DE` relie le geste à un concept
    (« multiplication végétative »), câble-le (cf. `CONCEPTION_VOIX_NARRATIVES.md`
    §5). Optionnel : page secrète si lore.
- **Pont** : route `bouturer` à 2 temps dans `tools/simserver/actions.py`
  (+ `actions_cibles.py` pour la résolution mère/plot). Bump `ENGINE_VERSION`
  (→ 0.5.24) + commentaire de version.
- Après un `bouturer` réussi : rien de spécial pour le déblocage (bouturer est
  débloqué par la maîtrise « bouture », géré en ①) — mais si tu veux qu'une
  bouture réussie CRÉDITE la maîtrise « bouture » (`crediter_succes`), c'est
  cohérent (le faire → ouvre `greffer` plus vite). Reste sobre.

## Golden attendu
**INCHANGÉ** (`452b5256…`). Le smoke n'appelle pas `bouturer`, le flag
`bouturable` par défaut False ne change aucun tick, `COUTS["bouturer"]` neutre
tant qu'inutilisé. Vérifie `python3 -m tests.test_golden`.

## Ne PAS faire
- Pas de RNG live (déterminisme #3 : la bouture est un acte joueur, pas un tirage).
- Pas de malus direct sur la mère autre que `stress_memory` (philo #2).
- Pas la greffe (③).
- Ne casse pas `clonal.py` (l'émission de ramets automatique reste intacte).

## Vérifs de fin
1. Golden inchangé.
2. Test ad hoc dans `tests/` : bouturer une mère mûre bouturable → nouveau clone
   sur le plot, gènes identiques, `stress_memory` mère montée, Vigueur joueur
   débitée ; espèce non `bouturable` → refus sans dépense.
3. Test du corpus de gestes passe (`bouturer` a sa fiche + classé "geste").
4. Pont : `bouturer` routable à 2 temps ; version bumpée + commentaire.
5. MAJ `00_etat.md` (§REPRISE).
