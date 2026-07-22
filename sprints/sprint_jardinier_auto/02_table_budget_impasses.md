# ② Table complète + priorisation par budget + détecteur d'impasses

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` +
> `docs/joueur/automate/conception_jardinier_automate.md` (§5, §7). Prérequis : ① fait.

## Objectif
Compléter la **table facteur → geste** (`regles.py`), ajouter la **priorisation par
budget de Vigueur**, le **chaînage de ravitaillement `broyer → pailler`**, les
gestes `tailler` (ombrage) et `deraciner` (désherbage commutable), le slider
`part_recoltee`, et le **détecteur d'impasses**.

## Fichiers à toucher (paquet `tools/jardinier_auto/`)
- `diagnostic.py` — ajouter les facteurs : `"sol_nu"` (paillage/couverture bas),
  `"concurrence_ferale"` (densité férale dans le rayon racinaire d'une cultivée),
  `"ombrage"` (`eco.light_received` bas + voisin plus haut), `"sol_compacte"`
  (`eco.structure_sol` bas). Seuils = constantes nommées.
- `regles.py` — compléter la liste ordonnée avec les lignes de la table §5 de la
  conception. Ordre = priorité permacole (H7 §5) : durable (pailler) avant répétitif
  (arroser) à facteur égal.
- `execution.py` — câbler `pailler`, `broyer`, `recolter_paille`, `tailler`,
  `deraciner`, `grelinette`. Signatures exactes dans `sim/actions/gestes.py` et
  `sim/actions/paillage.py`.
- `profil.py` — appliquer `desherbage` (curatif/aucun/systematique) et
  `part_recoltee` (fraction récoltée).
- `impasses.py` (CRÉER) — `detecter_impasse(facteur, contexte) -> Impasse|None` +
  types d'impasse (§7 : geste_inexistant / geste_verrouille / ravitaillement_manquant).
  Consignées via `trace.py` (nouvelle catégorie d'entrée `impasse`).
- `boucle.py` — insérer l'étape budget + le détecteur dans la boucle.

## Modèle / points précis
- **Chaînage `broyer → pailler`** : `pailler(gs, player, eco, r, c, nature=...)`
  **refuse si le stock de mulch de cette nature est insuffisant** (voir
  `sim/actions/gestes.py:pailler` et `stock_disponible`). Donc, avant de proposer
  `pailler`, l'automate vérifie `mulch_stock(game_state)` ; si vide, il propose
  d'abord `broyer` (bois → BRF) ou `recolter_paille` (si matière dispo). Si aucun
  moyen de produire du mulch → **impasse `ravitaillement_manquant`**.
- **`desherbage`** : `curatif` (défaut) = `deraciner` une férale UNIQUEMENT si elle
  est diagnostiquée `concurrence_ferale` d'une cultivée ; `aucun` = ne jamais
  proposer `deraciner` sur une férale ; `systematique` = `deraciner` toute férale à
  portée d'une cultivée. Reconnaître féral vs cultivé via l'attribut retenu en ①.
- **`tailler`** pour l'ombrage : cibler le **voisin ombrageant** (plus haut, dans le
  rayon) — `tailler(gs, player, plant_voisin, eco, cible="apex")`. Attention : c'est
  un geste sur le VIVANT (coûteux, philo #1) → priorité basse.
- **`part_recoltee`** : à la récolte, ne prélever que cette fraction des organes
  mûrs (le reste tombe). En pratique : ne pas appeler `recolter` sur tous les fruits
  mûrs, seulement `round(part_recoltee × n_mûrs)`. Défaut 1.0 → comportement ① inchangé.
- **Budget** : si `profil.paie_vigueur`, trier les gestes candidats par priorité
  (avec départage stable `(tile_id, y_cm, x_cm)`) et **couper quand la Vigueur
  disponible est épuisée** (`vigueur.solde` du joueur). En mode `LIBRE`
  (`paie_vigueur=False`), pas de coupe (tous les gestes passent). NB : le VRAI
  bridage par `gestes_debloques` est câblé au ③ ; ici on gère seulement le budget.

## Détecteur d'impasses (§7)
Quand `facteur_limitant` renvoie un facteur mais qu'aucune règle applicable ne
produit un geste **jouable** (geste absent de la table / stock impossible à
produire), consigner une `Impasse{facteur, cause, cible, semaine}` au journal.
NE PAS bloquer la boucle — c'est un signalement, on continue.

## Golden attendu
**INCHANGÉ.** L'automate reste hors tick. Tests déterminisme du ① toujours verts.

## Ce qu'il NE faut PAS faire
- NE PAS créer de geste moteur (`drainer`/`creuser` restent des impasses).
- NE PAS toucher le moteur. NE PAS câbler la comptabilité maîtrise (③) ni les
  objectifs (④). NE PAS lancer `test_epaisseur_500ans`.
- NE PAS dépasser 300 LDC/fichier (scinder).

## Vérif de sortie
Golden intact + tests déterminisme verts + banc `automate_demo` montrant des
paillages (après broyage), des désherbages selon profil, et **au moins une impasse
consignée** (ex. forcer un excès d'eau → impasse geste_inexistant). Mettre à jour
`00_etat.md`.
