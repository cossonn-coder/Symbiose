# 2026-07-23 — Sprint AUTOMATE DIRIGÉ PAR LE BUT (D87) — CLOS

`/sprint-auto sprint_automate_but`, ①→⑤. Implémente la conception figée le
2026-07-23 (cf. entrée 129) : un **étage de planification moyens-fins**
DÉTERMINISTE au-dessus du jardinier automate réactif (D78). **Golden
`57c166d8…` INTACT sur les 5 tronçons, ZÉRO re-figeage** (planif opt-in, hors
tick → `automate OFF = golden bit-identique`, vérifié dans le test de
déterminisme).

## Tronçons

- **① LOG STRUCTURÉ** (`f68f447`) — fondation : `trace.py` enrichi (schéma commun
  `{categorie, semaine, niveau, objectif_id, espece, zone, detail}` sur toutes
  les lignes, 6 constructeurs réservés ②-④, legacy normalisé), `filtre.py` NEUF
  (`filtrer`/`trier`/`rendre`, lecture seule, ne mute jamais le log),
  `profil.verbosite_log`. Test oracle de déterminisme (log rejoué bit-identique).
  Frontière stricte avec le carnet D14 (canal technique ≠ voix « je »).
- **② OPÉRATEURS + PLANIFICATION** (`18c4173`) — `operateurs.py` NEUF : 3
  opérateurs créatifs (`acheter_magazine`/`planter`/`favoriser_auxiliaire`),
  post-condition **organe-typée `fruitier` dès la définition** (fruit mûr vs
  maturité végétative, C2), sous-chaîne pollinisation conditionnelle (C4),
  placement déterministe canonique (1er plot libre en balayant `tiles` puis
  `(r,c)`, T5). `planification.py` NEUF : `avancer_plans` chaînage arrière borné
  (profondeur ≤4), état persistant `automate_plans`, `nb_cible=min(N,3)` (C1).
  Non branché (③ câble). Zéro RNG.
- **③ BOUCLE + PRÉEMPTION SURVIE** (`7458801`) — plans créatifs emballés au
  format réactif et triés avec les gestes Liebig dans `boucle.jouer_tick`.
  **Préemption survie** : `PRIO_CREATIF=5` sans `BONUS_OBJECTIF` → créatifs
  toujours SOUS la survie (10-20), valable payé ET libre. Mode payé : créatifs
  budget-coupés tracés `geste_coupe {cause:budget}`. `execution.executer` étendu
  aux 3 verbes (actions + magazine), `favoriser_auxiliaire` one-shot.
- **④ VEILLE + RE-SONDE + IMPASSES** (`06dead3`) — comble le trou **T1** (semer =
  `GrainEnAttente` qui lève plus tard, pas une plante) : un semis en attente ne
  re-sème plus chaque tick, levée détectée (n_vivantes monte) → `resultat` leve +
  relais Liebig ; `FENETRE_LEVEE=4` sans levée → échec. Re-semis armé (C3) SEULEMENT
  si `(saison, plot)` a bougé ET `tentatives ≤ 2`, sinon `niche_defavorable`
  directe (pas de retry cosmétique). Veille = objectif reste actif, impasse tracée
  1×/cause, réveil sur déclencheur (palier 3 / plot libéré / cultivée morte).
- **⑤ BANC PARAMÉTRÉ + VUE GODOT** (`8f6bd1e`) — `banc_culture_depuis_rien(espece,
  quantite, source_graine ∈ {auto,banque,magazine,aucune}, cout_vigueur, nb_plants)`
  force chaque branche de l'arbre, récit depuis le log filtré par `objectif_id`,
  mode `--matrice`. Résultats : haricot/basilic/courgette **accomplis** ; tomate
  **partielle** (mildiou révélé, Q8 — l'impasse honnête ne masque pas le bug bio) ;
  `aucune` → impasse honnête `chainon_manquant`. Onglet automate Godot
  (`WorldView.Automate.cs`) : log **filtrable par catégories** (F / Maj+F),
  `LigneTrace` étendu ; `dotnet build` vert.

## Finding à trancher (consigné 00_etat, remonté à Nico)

Branche **magazine inatteignable en régime LIBRE** : `pre_acheter_magazine`
exige Vigueur ≥ 120 (`SEUIL_MAGAZINE`/`COUT_MAGAZINE=120`) alors que la régen
passive plafonne à 100 avant `assurer_solde_libre`. Le banc provisionne la
Vigueur pour tester la chaîne complète (dev). Contredit partiellement l'exigence
B « coût 0 = rien coupé » → **follow-up ② possible** (soit le plafond de régen
libre monte au-dessus du seuil magazine, soit `assurer_solde_libre` s'applique
avant la pré-condition). Non bloquant : les 4 autres branches fonctionnent.

## Bilan

Golden final `57c166d8d3626444…08da` (inchangé depuis le début du sprint).
Refactor auto-léger **no-op** (tous les fichiers du sprint 🟢, max LDC pur
`WorldView.Automate.cs`=195, `planification.py`=154). DETTE D87 → CLOSE.
**Reste F5 Nico** : banc `--source magazine` puis `--source aucune` puis
`--matrice` ; onglet automate Godot (A/Maj+A, F/Maj+F filtrage log).
