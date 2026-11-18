# ①c Paternité — le père est celui dont le pollen arrive

> Lire d'abord : `CLAUDE.md`, `00_etat.md` (§Conception FÉCONDATION + bilan ①b), puis
> `docs/vegetal/genetique/conception_caracteres_vivants.md` §6.2-6.3.
> Golden attendu : **RE-FIGÉ annoncé** (le choix du père change les gènes des enfants).

## Objectif
Une fleur attirante exporte plus de pollen et engendre plus de graines chez ses voisines
(principe de Bateman). C'est le levier principal de la sélection des 6 caractères floraux.

## À faire
1. **Compteur mâle `pollen_donne`** (nouvel attribut de `PlantInstance`, hors digest).
   - **Butineurs** : `fields/foragers.py::sample_foragers` dépose déjà `(espèce, r, c,
     charge)` ; il doit aussi rendre les **recharges** `(espèce, r, c, charge prise)` (la
     couche `fields` ne touche jamais une plante : elle rend une liste, la couche `sim`
     applique). Dans `sim/engine/butineurs.py`, créditer `pollen_donne` aux fleurs
     conspécifiques du plot ∝ leur poids floral, en miroir de `_apply_deposits` (même
     `bucket`).
   - **Vent** : dans `sim/engine/anemophilie.py`, chaque source `src` créditée de ce
     qu'elle envoie à la cible (`coef × vent × src.floraison × src.gene("pollen")`) ;
     la part auto-anémophile crédite la cible elle-même.
   - **Remise à zéro** : une fois par an, en début d'année florale (là où
     `sim/engine/floraison.py` remet `gdd_accum`/`bloom_week` à zéro, ou équivalent
     vérifié), **pas** à la fanaison : le père doit garder son crédit jusqu'à la mise en
     graine de la mère (automne, ou fin de cycle d'une annuelle).
2. **Loterie paternelle** (`sim/reproduction.py::find_father`) : parmi les candidats à
   portée déjà filtrés, poids `w = pollen_donne × (1 − d²/reach²)` ; tirage au hash
   pondéré. Le canal de hash doit être **dédié** : vérifier au `grep` qu'aucun autre tirage
   ne l'emploie (canaux `week * N` libres au 2026-11-18 : 79, 97, 101, 103). Si tous les
   poids sont nuls → règle actuelle (le plus proche, départage au hash existant).
   Garder la signature : tous les appelants (`_reproduction`, `semer_fin_de_cycle`, récolte,
   `sim/zoochorie.py`, `sim/caches.py`) en profitent sans modification.
3. **Banc** (`mesures/`) : deux bourraches (ou phacélies) à égale distance d'une mère,
   l'une à `nectar`/`taille_fleur` hauts, l'autre basse ; sur une saison, la part de
   paternité de la plus attirante doit dépasser 1/2. Puis relancer `banc_fleurs.py` (a) sur
   plusieurs générations si possible : la moyenne de `couleur_fleur` des descendants doit
   bouger vers la préférence du butineur dominant. **Si rien ne bouge, enquêter** (un
   tronçon inerte n'est pas un succès).
4. **Perf** : la recharge est déjà parcourue, on n'ajoute qu'une écriture ; budget ≤ +2 %
   au smoke (paires alternées, `uptime` d'abord).

## Tests
- Ciblés : `pollen_donne` croît avec les visites et le poids floral ; une source au vent
  est créditée ; `find_father` choisit plus souvent (sur plusieurs semaines/positions) le
  père au plus fort `pollen_donne` ; poids nuls → plus proche ; un père hors portée n'est
  jamais tiré.
- Suites butineurs, vent, pollinisation, génétique vertes.

## Golden
Re-figé : 1ʳᵉ divergence attendue au premier `heredite` croisé dont le père change. Diff
du digest lu, hash consigné.

## Ne PAS faire
- Suivre l'identité du donneur dans la charge du butineur (trop cher, inutile : le crédit
  au moment de la recharge suffit).
- La levée des pools (①d).
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`00_etat.md` : ①c FAIT, hash, mesures de paternité. Commit.
