# Sprint SANTÉ & RÉSILIENCE — état vivant (carnet de bord)

> Carnet `/conception` mis à jour EN CONTINU (règle §0bis). Reprise à froid =
> lire `CLAUDE.md` + ce fichier. **CONCEPTION FIGÉE 2026-07-13 — 4 kickoffs prêts
> pour `/sprint-auto`.** Doc : `docs/conception/CONCEPTION_SANTE_RESILIENCE.md`.

## Objectif
Remplacer les PV plats `health: int 0–3` (uniformes toutes espèces) par une
**vitalité continue [0,1]** différenciée par espèce, via une **constitution
`resilience_base` data-driven par espèce** (PAS un gène — audit anti-doublon §ci-
dessous). Compléter la couche niche (grêle, déficit racinaire) et replier le **fix
du canal chronique campagnol** (herbivorie racinaire → perte d'uptake, couplage
mycorhize, annélation létale conservée).

## Carte des tronçons (figée)
- **① `01_socle_vitalite.md`** — `health→vitalite [0,1]`, `etat`, `erode()` no-op,
  migration lecteurs/écrivains. Golden **RE-FIGÉ #1**.
- **② `02_constitution_niche.md`** — `resilience_base` COMPLET par espèce +
  `hail_resistance_base` (niche grêle). Golden **RE-FIGÉ #2**.
- **③ `03_campagnol_uptake.md`** — `root_herbivory_memory`→uptake, mycorhize,
  `root_loss_tolerance_base`, annélation létale conservée. Golden **NEUTRE**.
- **④ `04_vue_godot.md`** — pont `vitalite`/`etat` (0.5.28) + `PlantRenderer`
  dégradé continu. Golden **INTACT**.

## État des lieux du modèle actuel (lecture faite)
- `plants/base/instance.py:30` : `health: int = 3` (3 sain / 2 affaibli / 1 malade / 0 mort).
- **Écrit par** : `ReduceHealth` (resolution.py `health = max(0, health-amount)`),
  sénescence/asphyxie/heal (`mortalite.py` ±1), gestes (`gestes.py` écraser=0,
  manger −1), greffe (scion=0), `regress()` (stade 0 → health=0).
- **Lu par** (rayon d'impact du passage int→float) :
  - `sim/vigueur_plante.py:43` `sante = health/3.0` (HEALTH_MAX=3.0)
  - `sim/engine/croissance.py:204` photosynthèse `health_factor = health/3.0`
  - `fields/population/resources.py` (5×) poids `health/3.0`
  - `sim/maitrise_detection.py:245` `health == 3` (« pleine santé »)
  - `plants/base/instance.py:294` `is_alive = health > 0`
  - sémiologie (miroir sénescence), `__repr__` `santé=/3`
- **Dégât** : `DAMAGE_STEP` (division ENTIÈRE, gel/grêle/vent) ; cap chronique
  `_cap_chronique` = **−1 max/tick/plante** (usure pas punition, philo #6).
- **Guérison** (`mortalite.py:106-122`) : proba ±1 modulée par
  `Q = light×hum×(1−disturb)` × `gene("vigueur")` × `cout_defense()`.
- **Canal campagnol** (`perturbations.py:398 root_herbivory`) : lit
  `category_density("herbivore_vertebre")` → `ReduceHealth −1` chronique
  (capé, en concurrence avec les autres voies) + **annélation −2 létale**
  (jeune ligneux, dens ≥ LETHAL). ⚠️ Aujourd'hui = simple érosion plate.

## Décisions arrêtées (Nico, phase A)
- **D1. resilience ADAPTOGÈNE** (Nico penche adaptogène ; perf négligeable
  < +1 % tick — machinerie plasticité déjà là, +1 lerp mémoire + 1 itération
  dans la boucle d'expression O(N), hors point chaud LightField). Bonus : la
  sur-expression coûte de la vigueur (`cout_defense`) → une plante qui BLINDE
  sa résilience RÉCUPÈRE moins vite (vigueur = récup) → tension CSR émergente
  gratuite. → resilience ∈ `ADAPTOGENIC_GENES`, apparié à une mémoire
  `resilience_memory`.
- **D2. Séparation sémantique par CÔTÉ (Nico)** : `resilience` = **encaisser**
  (érosion : dégât/resilience_eff) ; `vigueur` = **volonté de récupérer**
  (convalescence : formule INCHANGÉE, garde `gene("vigueur")`). Zéro
  double-compte résolu par côté, PAS en retirant vigueur. Recadre la commande
  initiale (« resilience pilote érosion ET récupération ») → resilience pilote
  l'ÉROSION SEULE.
- **D3. Renommer `health` → `vitalite ∈ [0,1]`** + property `etat` (0-3
  discrétisé) pour lecteurs discrets restants + sémiologie.
- **D4. Signal d'exposition de resilience_memory (tranché seul, doc)** :
  hormèse = érosion de vitalité récente (dégât net subi) → durcissement borné
  par `EXPR_MAX` (pas d'invulnérabilité galopante).
- **D5. Primitive d'érosion unique `plant.erode(amount)` (Nico : « attention
  aux décréments directs, certaines plantes plus résilientes à l'asphyxie »)** :
  `vitalite −= amount / resilience_eff`. TOUTES les voies d'insulte EXTERNE y
  passent → `ReduceHealth` (résolution), **asphyxie** (mortalite.py:99, APRÈS
  sa médiation amont par `tolerance_asphyxie`), `PropagateDisease`. Deux couches
  empilées SANS double-compte : la tolérance spécifique rend l'événement plus
  RARE, resilience rend chaque coup plus PETIT.
  HORS tampon (décréments directs assumés) : **sénescence** (mortalite.py:80 —
  horloge interne de vieillissement, pas un stress subi) et **gestes joueur**
  (écraser/déraciner/regress/greffe → vitalité 0, mécanique brute).
  `erode()` introduite au ① (divisor = 1.0, no-op) ; resilience l'active au ②.

## AUDIT tolérance vs résilience (Nico 2026-07-13 : « font doublon ? »)
- Les 6 tolérances = axes de NICHE par stresseur (sécheresse/ombre/asphyxie/
  froid/pathogène/vent), individuelles + plastiques. NON redondantes entre elles.
- Bases d'ESPÈCE existantes SEULEMENT pour ombre (`shade_tolerance_base`) et
  fongique (`fungal_susceptibility` 0.2→0.6). Les 4 autres = gène seul → aucune
  espèce plus coriace qu'une autre pour sécheresse/froid/asphyxie/vent + voies
  SANS gène (grêle/campagnol/mortalité de fond/fonte).
- VERDICT : un gène `resilience` générique INDIVIDUEL ferait DOUBLON avec les
  tolérances sur l'érosion. Le vrai manque = la CONSTITUTION D'ESPÈCE.
- SYNTHÈSE proposée (remplace D1) : `resilience` = **base data-driven par
  espèce** (constitution CSR fast-fragile/slow-tough) appliquée génériquement à
  `erode()`, **SANS gène ni adaptogène**. Enveloppe les tolérances (comble le
  trou + couvre les voies sans gène) au lieu de les doubler. Individualité =
  tolérances (par stresseur) + vigueur (récupération). → **D1/D2.2 CADUQUES
  si Nico valide l'option A.**

## ARCHITECTURE FINALE (Nico 2026-07-13, option A + 2 exigences) — REMPLACE D1/D2
Deux couches, rôles distincts, AUCUN doublon, `GENE_NAMES` INCHANGÉ (aucun gène
ajouté — « ajout en queue » de la commande devient sans objet) :
- **Couche 1 — NICHE (par stresseur, susceptibilité À LA SOURCE)** : gènes
  existants (secheresse/ombre/asphyxie/froid/pathogène/vent) + bases d'espèce
  existantes (`shade_tolerance_base`, `fungal_susceptibility`) + **2 niches
  MANQUANTES à ajouter (base d'espèce SEULE, pas de gène)** : `hail_resistance_base`
  (grêle, aujourd'hui `gene_name=None`) et `root_loss_tolerance_base` (déficit
  racinaire campagnol, module memory→uptake).
- **Couche 2 — CONSTITUTION `resilience_base` (générique, EN AVAL à `erode()`,
  SANS gène)** : « combien un coup qui passe me terrasse ». Orthogonale à la niche
  (cactus = niche sécheresse haute mais constitution faible ; arbre = niche
  moyenne, constitution haute). **Table COMPLÈTE : valeur CSR explicite pour
  CHAQUE espèce du catalogue**, pas de défaut silencieux.
- **Récupération** = `vigueur` (gène individuel, inchangé).
- Pas de double-compte : niche = *ce qui* blesse (source) ; constitution =
  *combien* (aval) → points différents du pipeline.

## Décisions caduques
- D1 (resilience adaptogène) & D2.2 (gène en queue de GENE_NAMES) : ANNULÉES —
  resilience n'est plus un gène. D2 (séparation érosion/récupération) et D3
  (renommage vitalite) et D5 (primitive erode) TIENNENT.

## Questions ouvertes
- (aucune — reste 1 confirmation légère à Nico : grêle/root = base d'espèce
  seule, pas de gène individuel. Si OK tacite → figer.)

## Modèle pressenti (à valider)
- `vitalite ∈ [0,1]`, 1.0 = sain neuf. `etat(vitalite)` → {sain/affaibli/malade/mort}
  par seuils (préserve la sémantique 0-3).
- `resilience_eff = resilience_base(espèce) × gene("resilience")`.
- **Érosion** : dégât appliqué = dégât_brut / resilience_eff. Les TOLÉRANCES
  (secheresse/ombre/asphyxie/froid/pathogène/vent) restent en amont sur la
  susceptibilité SPÉCIFIQUE au stresseur ; resilience = tampon GÉNÉRIQUE final
  (pas de double-compte).
- **Récupération** : heal = Q × HEAL_RATE × resilience_eff × cout_defense
  (vigueur retirée).
- **Campagnol** : nouvelle mémoire `root_herbivory_memory` (lerp ∝ densité
  campagnol) → réduit l'uptake effectif (racines rongées) → la plante souffre
  par les voies eau/azote EXISTANTES (philo #2) au lieu d'un ReduceHealth plat.
  **Mycorhize** (champ mycélium, rôle mycorhize) compense la perte racinaire.
  **Annélation létale conservée** (bascule aiguë, hors ce canal).

## Coût perf estimé
- Vitalité continue : neutre (float remplace int).
- +1 gène : négligeable (dict +1, bruit indexé +1 position, ajout EN QUEUE).
- `root_herbivory_memory` : +1 lerp O(N)/tick ; mycorhize = lecture champ O(1)/plante.
- Budget ≤ +10 %/tronçon respecté.

## Golden
Re-figeage **maîtrisé et ANNONCÉ** attendu : dès qu'une plante dévie de
vitalité 1.0 (photosynthèse `health/3`→vitalite, tous les ReduceHealth,
convalescence), les sorties numériques du smoke bougent. Dérive localisée aux
plantes qui subissent/guérissent ; le canal campagnol reste NEUTRE au smoke
(densité `herbivore_vertebre` = 0).

## §REPRISE
CONCEPTION FIGÉE. Prochaine étape = **exécution** : `/sprint-auto
sprint_sante_resilience`. Ordre ①→②→③→④, chacun re-figeage golden annoncé
(① et ② uniquement) ou neutre/intact (③, ④). L'orchestrateur met à jour ce
fichier (hash re-figés) au fil des tronçons. Rien à trancher côté conception.
