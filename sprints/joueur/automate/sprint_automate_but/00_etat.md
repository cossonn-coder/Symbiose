# Sprint « Automate dirigé par le but » (D87) — état de conception

> **Phase A (challenge) EN COURS.** Rien n'est figé. Ce fichier est le carnet de
> bord autosuffisant (skill /conception §0bis) : reprise à froid = lire `CLAUDE.md`
> + ce fichier + la dette D87 (`DETTE.md`).

Type/thème : `joueur/automate` (même que D78). Amorce d'origine :
`docs/joueur/automate/brief_amorce_automate_but_D87.md` (écrite SANS accès repo →
recadrée par la lecture du code réel ci-dessous).

## Socle réel vérifié dans le code (ce que le brief ignorait)

- **Automate = paquet `data/code/tools/jardinier_auto/`**, boucle 5 étapes
  (`boucle.py`) intercalée ENTRE deux ticks (H2, golden intact). Il ne soigne QUE
  les **cultivées** (`tutelle.py` = set `replante` de `maitrise_detection`).
- **Cœur réactif = Liebig** : `diagnostic.facteur_limitant` → `regles.REGLES`
  (table déclarative facteur→geste priorisée) → `proposition.proposer` qui **sonde
  l'état vivant** et renvoie `Plan` ou `Impasse`. Gestes couverts : arroser,
  pailler(+ravito broyer/glaner/recolter_paille), deraciner, grelinette, tailler,
  recolter. **PAS** `planter`, **PAS** `favoriser_auxiliaire`.
- **Objectifs (④)** : `objectifs.py`. `Objectif(geste,quantite,cible,id)` frozen ;
  effet = biais de priorité (`BONUS_OBJECTIF=100`) + comptage (`incrementer`).
  `est_atteignable` sonde déjà 3 voies (vivante présente / graine banque / succession)
  → impasse `objectif_inatteignable` signalée UNE fois. **C'est le germe exact de D87.**
- **`planter` (gestes.py:100)** : source = **PlayerSeedBank UNIQUEMENT** (`take`),
  refus sans Vigueur ni graine. **NE fait PAS pousser** : dépose un `GrainEnAttente`
  qui lève PLUS TARD par succession (plot libre + niche favorable) — germination
  **conditionnelle et potentiellement jamais**. `cultive=True` → la levée entre
  d'elle-même sous tutelle.
- **Magazine (`sim/magazine.py`)** : `acheter_au_magazine(gs,player,espece)` existe,
  écrit Vigueur+banque. Gate = palier 3 d'un membre de famille (`SEUIL_MAGAZINE=3`),
  coût `COUT_MAGAZINE=120`. → voie n°2 de l'arbre RÉELLE.
- **`favoriser_auxiliaire`** : geste existant (MODERE) mais AUCUN facteur Liebig ne
  le déclenche → seul le planificateur peut l'émettre. Pollinisation = flux repro,
  pas un déficit Liebig d'un individu.
- Impasses : machinerie existante (`impasses.py`, `trace.entree_impasse`), types
  dont `OBJECTIF_INATTEIGNABLE`.

## Recadrage structurant (mon apport vs brief)

**D87 est BEAUCOUP plus petit que le brief le craint.** Liebig couvre déjà tout le
« MAINTENIR ». Le planificateur ne comble que 2-3 gestes créatifs manquants
(`planter`, `acheter_au_magazine`, `favoriser_auxiliaire`) sur une chaîne
**quasi-linéaire profondeur ≤ 3** : `recolter` ← plante adulte présente ← `planter`
← graine ← magazine. → **archi B (régression générale) = sur-ingénierie** ; la
biologie n'est pas à « régresser », elle est déjà servie réactivement.

## Trous trouvés (absents du brief)

- **T1** — `planter` = graine EN ATTENTE, pas plante. Le sous-but « adulte présent »
  cache 2 portes (lever ? survivre à l'adulte ?) que Liebig ne garantit pas. Que
  fait le planif si rien ne lève après K semaines ?
- **T2** — `favoriser_auxiliaire` n'a pas de facteur Liebig → doit être émis par le
  planif, calé sur la **phase florale de la cible** (lisible via l'arc pollinisation).
- **T3** — voie n°3 « récolter des semences » = circulaire ; `est_atteignable` ne
  l'implémente PAS aujourd'hui → la DROPPER (banque→magazine→veille suffit, #2).
- **T4** — déterminisme des gestes créatifs SANS position de plante (`acheter`,
  choix du plot de `planter`) → clé de départage canonique à définir.
- **T5** — placement : l'automate n'a jamais « choisi où planter ». Politique de
  placement déterministe requise (plot libre d'une zone, ou tuile par défaut).

## Décisions arrêtées (Nico, 2026-07-23)

- **D-ARCHI = A/C** : petit catalogue d'**opérateurs** (1 par geste créatif), pré/post
  **sondées sur l'état vivant du moteur** (patron `est_atteignable`/`proposer`
  étendu). Archi B (régression du modèle bio) REJETÉE = sur-ingénierie (Liebig
  couvre déjà le maintien). 3 opérateurs seulement :
  - `acheter_magazine(sp)` : pre = sp offerte (palier 3 famille) ∧ Vigueur≥120 ;
    post = graine `sp` en banque.
  - `planter(sp)` : pre = graine `sp` en banque ∧ plot libre déterministe ;
    post = grain en attente → (à terme) cultivée de `sp`.
  - `favoriser_auxiliaire(zone)` : pre = cultivée de `sp` avec `plant.floraison>seuil`
    (lisible `instance.py:141`) ; post = pression pollinisation (périodique, bornée).
  - `recolter` reste RÉACTIF (règle `organe_mur`, inchangé).
- **D-VIGUEUR = préemption survie** : gestes créatifs (advenir) en priorité MODÉRÉE
  SOUS les facteurs de survie du vivant existant. Advenir ralenti, jamais au prix
  du vivant. (Le `BONUS_OBJECTIF=100` actuel biaise les gestes sur cultivées
  existantes ; les créatifs prennent une priorité basse ~5, budget-cut normal.)
- **D-ÉCHEC = veille + re-sonde** : objectif reste ACTIF, impasse tracée 1× (chaînon
  nommé), re-plan sur DÉCLENCHEUR seulement (palier 3 ouvre le magazine / plot se
  libère / K semaines sans levée → re-sème 1×, `tentatives ≤ 2` puis impasse
  `niche_defavorable`). État planif persistant par objectif (`automate_plans`).
- **Placement (T5)** : 1er plot libre en balayant `engine.tiles` puis `(r,c)`
  croissant (libre = `plants_at` sans vivant + aucun grain en attente). Canonique.
- **Déterminisme (T4)** : objectifs déjà triés par id ; 1 objectif→1 espèce→1 chaîne ;
  cible florale = plus petit `(tile_id, y_cm, x_cm)`. Zéro RNG.
- **Golden INTACT par construction** : planif opt-in (comme les objectifs ④), le
  golden tourne sans joueur/objectif → no-op strict. AUCUN re-figeage sur tout le
  sprint.
- Q1 (planif symbolique admis #3) : ACTÉ OUI — chaînage arrière déterministe borné,
  pas d'« IA » (ni réseau, ni apprentissage, ni RNG).
- Q4 horizon : profondeur bornée ~4, PAS de simulation temporelle avant ; on émet
  le prochain geste créatif faisable puis on ATTEND la biologie.
- Q5 granularité : opérateurs ATOMIQUES (= gestes existants), pas de macro HTN.
- Q6 stabilité : plan persistant par objectif (comme la progression), re-plan sur
  déclencheur seulement (sous-but atteint / infaisable / cible morte), pas /tick.
- Q8 biologie dure : D87 suppose D84/D86 OK ; tomate peut mourir tôt
  ([[tomate-mort-precoce]]) → banc démo doit choisir un scénario/espèce qui fructifie
  vraiment, sinon l'impasse honnête révèle le bug bio (ne PAS le masquer).

## Retour d'aval (Nico, 2026-07-23) — C1-C4 + exigences A/B, résolutions

- **C1/Q9 — suffisance vs présence.** Le déclencheur « advenir » raisonne en
  CULTURE PERMANENTE, pas en simple présence : le planif maintient
  `nb_plants_cible` cultivées vivantes de l'espèce TANT QUE progression < N.
  `nb_plants_cible` = knob du banc, défaut `min(N, 3)` (« assez pour espérer N »,
  on ne force pas le rendement — réel émergent via `incrementer`). Objectif reste
  actif jusqu'à N atteint OU graines épuisées (→ veille). RESO retenue.
- **C2/Q10 — « récoltable » typé organe.** Signal = `plant.plant_class.fruitier`
  (bool, `familles.py:79`) :
  - `fruitier=True` → but satisfait par FRUIT mûr (`plant.fruits`) ; la sous-chaîne
    pollinisation (`favoriser_auxiliaire`) est AJOUTÉE ;
  - `fruitier=False` → but satisfait à maturité végétative (`maturite ≥ 0.95`, =
    `organe_mur` réactif) ; PAS de sous-chaîne pollinisation.
  Post-condition organe-typée dès la définition des opérateurs (①), pas après coup.
  Aucune donnée nouvelle sur les espèces (on LIT `fruitier`).
- **C3/Q11 — re-semis armé sur changement de condition.** Signature d'essai
  mémorisée = `(saison, plot_choisi)`. Re-semis armé SEULEMENT si un plot libre
  DIFFÉRENT existe OU la saison a avancé depuis le dernier essai ; sinon → impasse
  `niche_defavorable` directe (pas de retry cosmétique). `tentatives ≤ 2` reste un
  garde-fou dur. RESO retenue.
- **C4 — timing `favoriser_auxiliaire`.** Habitat auxiliaire (rondelle persistante)
  posé AU PLUS TÔT : dès qu'une cultivée `fruitier` de l'espèce EXISTE et que sa
  zone n'a pas encore de rondelle `auxiliaire` → posé UNE fois, avant floraison
  (pollinisateurs établis à temps). One-shot déterministe, pas calé sur le pic.
- **Exigence A — banc paramétré (④).** `banc_culture_depuis_rien(espece,
  quantite=N, source_graine="auto", cout_vigueur=…)`. `source_graine ∈ {auto,
  banque, magazine, aucune}` force chaque branche de l'arbre → matrice de test
  (chaîne complète / achat / impasse) × multi-espèces (exhibe C2, révèle bugs bio
  par espèce, Q8). PAS « tomate » en dur.
- **Exigence B/Q12 — coût Vigueur réglable à 0 = DÉJÀ LÀ.** `paie_vigueur=False`
  (preset LIBRE, défaut) → `assurer_solde_libre` rehausse le solde chaque tick →
  rien n'est coupé (= coût 0 effectif). On RÉUTILISE ce flag (pas de nouveau
  `cout_vigueur_actif`), exposé comme param du banc. Golden neutre (automate hors
  tick, opt-in). Progression comptée indépendamment de la Vigueur. **Même à coût 0,
  l'ordre de priorité ② (créatif SOUS survie) reste requis** — non pour couper mais
  pour ORDONNER les gestes déterministement. Deux régimes documentés : coût 0 =
  éprouver chaîne+biologie ; coût normal (BRIDE) = éprouver économie+arbitrage.

## Réponses aux 2 confirmations (Nico, 2026-07-23)

- **B/Q12** = RÉUTILISER `paie_vigueur=False` (LIBRE) pour « coût 0 ». Le param banc
  `cout_vigueur` mappe sur ce flag. Pas de nouveau flag `cout_vigueur_actif`.
- **C1/Q9** = `nb_plants_cible = min(N, 3)` par défaut, surchargeable au banc.

## LOG EXHAUSTIF (exigence Nico + Q13) — enrichissement de `trace.py`

Intention : l'automate TRACE l'intégralité de son raisonnement (pas que les
impasses/récit). Rend le moyens-fins déterministe INSPECTABLE + sert d'ORACLE de
déterminisme (2 runs à entrées égales → log identique).

- **Canal = `automate_journal` existant** (`trace.py`, `game_state["automate_journal"]`),
  ENRICHI — PAS un canal neuf. Technique/debug, JAMAIS diégétique. Frontière avec
  le **carnet D14** déjà nette : le carnet lit `sim/journal.py` (voix « je ») ; le
  flag `ecrit_carnet` gate les écritures diégétiques SÉPARÉMENT. Les deux ne
  fusionnent jamais (sinon #5/#6 violés).
- **Schéma de ligne (Q13)** — dict champs-structurés (jamais du texte libre ; le
  rendu texte se DÉRIVE des champs) :
  - `categorie` ∈ {`perception`, `diagnostic`, `plan`, `geste`, `geste_coupe`,
    `veille`, `impasse`, `consequence`, `resultat`} (les 3 dernières existent déjà) ;
  - `semaine` (int), `niveau` (int : 0=décision · 1=détail · 2=perception fine) ;
  - `objectif_id` (str|None), `espece` (str|None), `zone` = `(tile_id, r, c)`|None
    (plot choisi pour un geste créatif ; None pour `acheter_magazine`) ;
  - `detail` = dict spécifique à la catégorie (ex. plan → `{sous_but, raison}` ;
    geste_coupe → `{verbe, cause: budget|survie|veille}` ; veille → `{chainon,
    source}`).
- **Log TOUJOURS complet** (tous niveaux écrits — préserve l'oracle) ; verbosité et
  filtre = **vues LECTURE SEULE** (`filtre.py` : `filtrer(journal, categorie=…,
  espece=…, objectif_id=…, zone=…, niveau_max=…)` + `rendre(ligne)->str`). Un run
  filtré et un run brut partagent le MÊME log sous-jacent.
- **Ordre total stable** : append déjà déterministe (boucle sur listes, départage
  `(tile_id, y_cm, x_cm)`) ; pour une vue triée, clé
  `(semaine, _rang_categorie, objectif_id, zone)`. Zéro horodatage horloge, zéro id
  non déterministe. **Golden intact** (write-only hors tick).
- **Découpage** : le log est un **TRONÇON À PART ENTIÈRE**, placé en **① (fondation)**
  car le schéma doit précéder ses écrivains (« défini dès ① » de Nico) → les
  tronçons suivants s'y BRANCHENT sans le refondre. Fait passer le sprint à
  **5 tronçons**.

## Découpage FINAL — 5 tronçons (log = ①, vue Godot = ⑤ dernier)

- **①** LOG STRUCTURÉ : enrichir `trace.py` (nouvelles catégories + `niveau` +
  `detail`) + `filtre.py` (filtrer/rendre) + `verbosite` param harnais + TEST
  oracle déterminisme. Golden intact.
- **②** OPÉRATEURS + RÉGRESSION : `operateurs.py` (3 opérateurs, post-condition
  organe-typée `fruitier` DÈS la définition, sous-chaîne pollinisation
  conditionnelle, placement déterministe) + `planification.py` (chaînage arrière
  borné, état persistant `automate_plans`) — émet lignes `plan`/`diagnostic`.
  Golden intact.
- **③** ARTICULATION BOUCLE LIEBIG + PRÉEMPTION SURVIE : câblage `boucle.jouer_tick`,
  priorité créatif<survie (valable avec ET sans coût, régime `paie_vigueur` en
  place), `favoriser_auxiliaire` au plus tôt — émet `geste`/`geste_coupe`. Golden
  intact.
- **④** VEILLE + RE-SONDE + IMPASSES : déclencheurs C1 (suffisance N) / C3
  (re-semis armé `(saison, plot)`), impasses `chainon_manquant`/`niche_defavorable`
  — émet `veille`/`impasse`/`resultat`. Test réveil (palier 3 → objectif reprend).
  Golden intact.
- **⑤** BANC « X DEPUIS RIEN » PARAMÉTRÉ + VUE GODOT : `banc_culture_depuis_rien(
  espece, quantite, source_graine ∈ {auto,banque,magazine,aucune}, cout_vigueur)` —
  matrice de test consommant le log FILTRÉ + surfaçage log filtrable dans l'onglet
  automate Godot (`WorldView.Automate.cs`). Golden intact.

## §REPRISE — CONCEPTION FIGÉE (2026-07-23), prête pour /sprint-auto

Phase B faite. Doc : `docs/joueur/automate/conception_automate_but.md`. Découpage
FINAL = **5 tronçons**, golden `57c166d8…` **INTACT partout** (planif opt-in, hors
tick) :

- **①** `01_log_structure.md` — enrichir `trace.py` + `filtre.py` + verbosité +
  test oracle déterminisme (FONDATION).
- **②** `02_operateurs_regression.md` — `operateurs.py` (3 opérateurs, `fruitier`,
  placement) + `planification.py` (`avancer_plans`, `automate_plans`). Non branché.
- **③** `03_boucle_preemption.md` — brancher dans `boucle.jouer_tick`, préemption
  survie, timing `favoriser_auxiliaire`, exécution + trace.
- **④** `04_veille_impasses.md` — suivi germination, re-semis armé `(saison,plot)`,
  veille + re-sonde, impasses `chainon_manquant`/`niche_defavorable`.
- **⑤** `05_banc_vue_godot.md` — `banc_culture_depuis_rien` paramétré + onglet
  Godot log filtrable (DERNIER = vue).

Nuance log/ordre tranchée : log = tronçon **①** (fondation, le schéma précède ses
écrivains) — cohérent avec « défini dès ① » ; le sprint passe bien à 5 tronçons.

**Prochaine étape** : `/sprint-auto sprint_automate_but`. Toutes les décisions
sont dans les sections ci-dessus + le doc de conception. Aucun code moteur écrit
en conception.
