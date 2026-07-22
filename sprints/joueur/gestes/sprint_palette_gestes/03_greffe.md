# ③ GREFFE (moteur + voix) — kickoff autosuffisant

> Sprint PALETTE DE GESTES. Lire d'abord : `CLAUDE.md` + `00_etat.md` +
> `docs/joueur/gestes/conception_palette_gestes.md` §3.6. Démarre à FROID.
> Prérequis : ② fait (patron de geste à 2 temps + voix établi).

## Objectif
Implémenter le geste **`greffer`** : le porte-greffe adopte l'identité AÉRIENNE
du greffon tout en gardant son système RACINAIRE. À 2 temps (greffon →
porte-greffe). Golden NEUTRE. + toutes ses voix.

## Modèle (D8, philo #1/#2/#3)
- **Gate de compatibilité** : `plants.genetics.species_compatible(scion_cls,
  rootstock_cls)` (déjà existant = même **famille** botanique). Refus EN AMONT si
  incompatible ou si l'un des deux n'est pas une plante ligneuse greffable —
  ajoute au besoin un flag `greffable: bool` sur `PlantBase` (défaut False, mets
  True sur les ligneuses fruitières du catalogue). Refus = aucune Vigueur
  dépensée (patron `planter`/lot vide).
- **Effet aérien/racinaire** (D8) — sur la plante **porte-greffe** existante :
  - adopte la `plant_class` du greffon (POUR le rendu/floraison/fruit) OU un
    mécanisme équivalent — choisis le plus SIMPLE qui fasse que la plante produise
    désormais les fleurs/fruits du greffon. Le plus direct : **remplacer
    `plant.plant_class`** du porte-greffe par celle du greffon ;
  - **gènes AÉRIENS** = pris du greffon : `hauteur`, `phenologie_florale`,
    `resistance_pathogene` (+ tout gène régissant fleur/fruit s'il en existe) ;
  - **gènes RACINAIRES** = conservés du porte-greffe : `tolerance_secheresse`,
    `tolerance_asphyxie`, `tolerance_ombre`, `vigueur` ;
  - **établissement conservé** : le porte-greffe garde son âge/ses racines/son
    stade → démarrage rapide (ne PAS ré-initialiser au stade graine). C'est
    l'intérêt agronomique de la greffe (précocité).
  - Concrètement : construis le `plant.genes` résultant en piochant chaque gène
    dans la bonne source (dict comprehension sur `GENE_NAMES`, table
    AERIEN/RACINAIRE explicite au cœur du module). Le greffon (plante source) est
    CONSOMMÉ (retiré : c'est un rameau prélevé) OU laissé selon le réalisme —
    décision sobre : le greffon est un rameau, on ne le plante pas ; il disparaît.
- **Coût** : `couts.cout_action("greffer", …)` — ajoute `"greffer"` à `COUTS`
  (proposition ELEVE — geste savant, coûteux, philo #1) + `OBJETS_TOUCHES
  ["greffer"] = ("greffe",)`. Binaire tout-ou-rien.
- **Déterministe** : zéro RNG. La reprise est ACQUISE si le gate passe (pas de
  « échec aléatoire » — un échec de greffe serait un tirage vivant interdit #3 ;
  la difficulté vient du gate famille, pas du hasard).
- **2 temps** : 1er clic = greffon (plante source), 2e clic = porte-greffe
  (plante cible). Patron `bouturer`/`epandre`.

## Fichiers à toucher
- `data/code/plants/base.py` : flag `greffable` (défaut False) si retenu.
- Espèces fruitières concernées : `greffable = True`.
- **Nouveau** `data/code/sim/actions/greffe.py` (≤ 300 LDC) : `def greffer(
  game_state, player, scion, rootstock, eco) -> bool`. Table explicite
  `GENES_AERIENS` / `GENES_RACINAIRES` au cœur du module (commentaire pédagogique
  : quel gène va où et POURQUOI).
- `data/code/sim/actions/couts.py` : `greffer` dans `COUTS` + `OBJETS_TOUCHES`.
- `data/code/sim/actions/__init__.py` : ré-export si pattern du paquet.
- **Voix** : fiche `greffer` dans `geste_corpus.py` (N1 vu / N2 mécanisme
  aérien-racinaire / N3 rôle : cloner une variété, précocité, contraintes de
  compatibilité) ; technique `greffe` dans `technique_corpus.py` ; concept carnet
  via `CONCEPT_DE` si pertinent ; page secrète si lore. Vérifie `type_de` classe
  `greffer` en "geste".
- **Pont** : route `greffer` à 2 temps (`actions.py` + `actions_cibles.py`). Bump
  `ENGINE_VERSION` (→ 0.5.25) + commentaire.

## Golden attendu
**INCHANGÉ** (`452b5256…`). Le smoke n'appelle pas `greffer`, flags par défaut
False, coût neutre tant qu'inutilisé. `python3 -m tests.test_golden`.

## Ne PAS faire
- Pas d'échec aléatoire de reprise (déterminisme #3).
- Pas de ré-init du porte-greffe au stade graine (on garde l'établissement, D8).
- Pas de malus direct ; l'effet est un changement d'IDENTITÉ, pas un bonus chiffré.
- Ne touche pas la bouture (②).

## Vérifs de fin
1. Golden inchangé.
2. Test ad hoc dans `tests/` : greffer scion/rootstock de MÊME famille → la cible
   adopte plant_class + gènes aériens du greffon, garde ses gènes racinaires + son
   stade ; familles DIFFÉRENTES → refus sans dépense.
3. Corpus : `greffer` a sa fiche + classé "geste".
4. Pont : `greffer` routable à 2 temps ; version bumpée + commentaire.
5. MAJ `00_etat.md` (§REPRISE).
