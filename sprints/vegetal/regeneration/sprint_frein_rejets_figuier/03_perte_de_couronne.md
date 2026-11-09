# ③ La souche rejette après une grosse perte de couronne

À lire d'abord : `CLAUDE.md`, `00_etat.md`,
`docs/vegetal/regeneration/conception_rejets_de_souche.md` §3.4-3.5.
Prérequis : ② fait (trait `rejet_souche`, critère souche vivante, module
d'émission).

## Objectif
Un arbre VIVANT qui perd une part majeure de sa couronne en peu de temps (casse
par tempête ou neige, cladoptose, effondrement, taille du joueur) fait partir des
rejets au pied. La taille sévère devient un recépage émergent, sans geste neuf.

## Modèle
1. **Mémoire** `perte_couronne ∈ [0,1]` sur `PlantInstance`
   (`plants/base/instance.py`, commentée comme ses voisines) : à chaque perte de
   bois, `+= masse perdue / masse de bois de la structure avant la perte` ;
   décroissance lente (ordre de grandeur : vidée en ~1 an, une constante nommée).
   **Où incrémenter — à vérifier au code, ne pas deviner** : les pertes passent
   par `sim/engine/branches.py::mort_des_branches` (causes ombre, tempête, neige,
   effondrement, via `deposer_bois_tombe`) et par la taille joueur
   `sim/actions/gestes.py::tailler` (`atteindre_segment`, ~l.329). Chercher s'il
   existe un point commun (couper/retirer des segments) ; sinon incrémenter aux
   deux sites via une même fonction. La masse de bois d'un segment : réutiliser
   ce qu'utilisent déjà ces sites (`BOIS_PAR_CM`, `BOIS_MORT_PAR_CM3`…), ne pas
   en créer une troisième.
   Où décroître : une fois par tick, là où les autres mémoires de plante
   décroissent (le lire au code).
2. **Déclencheur** : `perte_couronne ≥ SEUIL_PERTE_COURONNE` (~0,5) ET souche
   vivante (critère pur du ②, appliqué à la plante vivante) ET hors hiver
   (sinon la vague attend le printemps, tant que la mémoire est haute) →
   vague de rejets par le module du ②, N ∝ `rejet_souche` × intensité, ≤ 4.
   Une vague par épisode : remettre à zéro ou marquer pour qu'une même perte ne
   rejette pas chaque semaine.
3. **Log** : même format que le ② (la cause « perte de couronne » vs « mort »
   peut figurer dans la ligne, utile au carnet du ④).

## Golden
**INCHANGÉ** attendu : le pommier du smoke est jeune ; la mémoire peut monter
sans déclencher. Si le hash bouge (p. ex. champ lu ailleurs) : STOP.

## Mesure
Un figuier mûr en labo, taille au ras (`tailler` sur ses charpentières) → vague
de rejets au printemps ; même chose sur un sapin → 0 ; une casse de vent normale
(une ou deux branches) → pas de vague. Consigner [labo, n=1 run].

## Tests
Ajouter à `tests/test_rejets_souche.py` : (f) taille sévère d'un figuier → rejets ;
(g) petite casse → aucun ; (h) arbre mort d'ombre puis taillé (mémoire d'ombre
haute) → aucun ; (i) une seule vague par épisode. Plus les suites du ②.
**Jamais `test_epaisseur_500ans`.**

## Ne PAS faire
- Geste joueur « recéper » neuf sur les arbres de tuile.
- Gel des rameaux (dette D131).
