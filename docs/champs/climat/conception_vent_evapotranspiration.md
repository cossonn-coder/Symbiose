# CONCEPTION — VENT & ÉVAPOTRANSPIRATION (D37)

> Doc de conception **à étudier** (sujet bio/éco hors expertise de Nico → on pose
> le modèle avant de coder). État : **PROPOSITION**, en attente de validation Nico.
> Une fois figé, on en tire les kickoffs `0N_*.md` du sprint et on implémente.
>
> Filiation : prolonge `docs/champs/climat/conception_meteo.md` (météo déterministe) et
> `docs/champs/climat/conception_meteo_champs.md` (rosée, lessivage, microbiome climatique).
> Résout **D37** (vent continu) et, par effet de bord, **D39** (régression
> `test_senescence`).

---

## 0. Déclencheur & décision

`tests/test_senescence.py` est ROUGE : un pommier isolé meurt **asphyxié à
19,5 ans** au lieu de mourir de sénescence (~60 ans). Diagnostic (sprint
`sprint_senescence_rosee.md`) : le sprint météo→champs a ajouté la **rosée**, qui
dépose de l'humidité chaque nuit claire ; or le climat de laboratoire du test
(15 °C, calme, ciel clair) **maximise** la rosée et **minimise** l'évaporation
existante (température < seuil) → l'humidité monte de façon **monotone** sur
~19 ans jusqu'à franchir le seuil d'asphyxie.

**Décision Nico (2026-06-29)** : on ne ré-isole PAS le test (rustine). On **traite
le fond** : enrichir le moteur d'évaporation et **introduire le vent** comme
facteur micro-climatique de plein droit (D37 complet). Périmètre validé en
conversation, incluant tous les effets ci-dessous.

### Le déséquilibre, chiffré (pourquoi ça monte)

Modèle d'eau actuel (`tick_hydrology`, par plot et par tick) :
- **Apports** : `BASE_RAIN=0.015` infiltrée ∝ structure (~0.7 sur terre) ≈ +0.0105,
  + rétention `soil_memory·SOIL_RETENTION`, + **rosée** (≈ +0.01 à +0.04 par nuit
  claire fraîche, `ROSEE_PAR_DEGRE=0.010`).
- **Pertes** : évaporation `h·(1−evap)` avec `evap = EVAPORATION(0.997) −
  EVAP_TEMP_COEF·max(0, T−EVAP_TEMP_REF)`. À 15 °C : `evap≈0.9938` → perte ≈
  0,62 %·h. + drainage `h·(1−0.993)` ≈ 0,7 %·h.

À 15 °C calme **sans rosée**, l'équilibre tombe vers `h≈1,7`. La rosée ajoute un
apport net que **rien ne compense** (l'évaporation ne réagit qu'à la température,
pas au ciel clair ni au vent) → l'équilibre grimpe et sature vers `h≈3` →
asphyxie. **La correction de fond = donner à l'évaporation les deux pilotes qui
manquent : le rayonnement (ciel clair) et le vent.**

---

## 1. Principe directeur (philo #2, ne jamais dériver)

Tout effet du vent passe par **flux → contrainte écologique → réponse biologique
émergente**. Jamais de bonus/malus direct sur la plante. Concrètement :
- le vent est un **champ** (comme lumière, humidité, température) ;
- il agit sur le **milieu** (évaporation, nébulosité, température ressentie,
  transport de matière) et sur le **tissu exposé** via des **susceptibilités
  médiées par gène** (comme le gel/grêle de `_mediated_damage`) ;
- les effets « bénéfiques » (semis renforcés) passent par la **plasticité**
  (expression de gène induite par un stimulus), pas par un buff.

Déterminisme strict (philo #3) : le vent dérive du **hash météo** (`_hash_noise`),
zéro RNG vivant. Deux runs identiques → vent identique.

---

## 2. Le champ de vent

### 2.1 Fonction pure `wind_at(seed, week)` — la masse d'air

Sur le modèle de `weather_at` (canaux-sentinelles décorrélés, `weather.py`), une
fonction PURE renvoie l'état de vent **de la masse d'air** pour la semaine :

```
WindState = (force, direction)
  force      ∈ [0, 1+]   # 0 = nul ; ~0.3 brise ; ~0.7 vent soutenu ; >1 coup de vent
  direction  ∈ [0, 2π)   # d'où vient le vent (déterministe, varie lentement)
```

- **force de fond** : dérivée d'un canal `K_WIND` + saisonnalité (automne/hiver
  plus venteux, cf. fenêtres Tempête/Pluie prolongée du catalogue).
- **événements** : `Tempête`/`Orage` forcent une force haute (le vent existait déjà
  comme dégât ponctuel — on le **continuise**) ; `Beau temps` ≈ brise faible.
- **direction** : marche lente déterministe (le vent « tourne » progressivement —
  réutilise le signe diégétique *« le vent tourne »* déjà présent pour Tempête).

### 2.2 Régimes intra-journaliers (specs Nico)

La force hebdo est **modulée dans la journée/tick** par des régimes déterministes
(zéro RNG vivant, dérivés de `_hash_noise` sur des sous-canaux) :
- **nul** : fenêtres de calme plat (force ≈ 0) — la rosée et la chaleur stagnent.
- **risées** : rafales (pics de force courts) → pic d'assèchement et de
  sollicitation mécanique ponctuel.
- **brise de fin de journée (effet venturi thermique)** : en fin d'après-midi, une
  brise se lève (réchauffement différentiel) ; **accélérée par venturi** dans les
  goulets entre obstacles (cf. §4 géométrie d'abri).

> Note d'implémentation : on garde un **scalaire+direction par tick** (pas une
> simulation fluide). Les « régimes » sont une **enveloppe temporelle** appliquée
> à la force hebdo, calculée par fonction pure du `week`/sous-tick.

### 2.3 Couplage vent ↔ nébulosité (specs Nico : amène / chasse / disperse)

Aujourd'hui `nebulosite` vient d'une **table figée** par type d'événement
(`NEBULOSITE`, lue par `weather_state`). On la rend **dynamique sous le vent** :
- vent fort venant d'un secteur « humide » → **amène** les nuages (nébulosité ↑) ;
- vent fort soutenu → **chasse/disperse** la couverture (nébulosité ↓ après coup) ;
- vent nul → la couverture **stagne** (ciel constant, gris ou clair selon l'état).

Conséquence en cascade (déjà câblée dans le moteur) : la nébulosité gouverne la
**lumière** (`tick_light`), la **rosée** (refroidissement nocturne) et la
**thermique** (`t_min_nuit_at`). Donc le vent devient un **pilote amont** de tout
ce bloc — c'est le couplage le plus structurant du sprint.

> ⚠️ Point d'attention golden : modifier la source de `nebulosite` touche lumière +
> rosée + thermique → **re-figeage golden LARGE attendu** (annoncé, cf. §7).

### 2.4 Le champ spatialisé `eco.vent` (force locale par plot)

La masse d'air (§2.1) est **uniforme** sur la tuile ; la **force locale par plot**
résulte de la géométrie d'abri (§4). On stocke un `GridField` `eco.vent`
(force locale ∈ [0,1+]) recalculé chaque tick depuis `wind_at` + abris. C'est lui
que lisent l'évaporation (§3) et les effets sur le vivant (§5).

---

## 3. Évapotranspiration enrichie (le cœur, débloque D39)

On enrichit le multiplicateur `evap` de `tick_hydrology` (étape 1) avec deux
pilotes nouveaux, **additifs** à la perte (formule proposée) :

```
evap = EVAPORATION
       − EVAP_TEMP_COEF  · max(0, T_sol − EVAP_TEMP_REF)     # (existant) chaleur
       − EVAP_RAD_COEF   · (1 − nebulosite)                  # NOUVEAU rayonnement
       − EVAP_WIND_COEF  · vent_local[r,c]                   # NOUVEAU vent
evap = max(EVAP_MIN, evap)
```

- **rayonnement** : ciel clair (`nebulosite→0`) ⇒ forte évaporation diurne. C'est
  le **contre-flux exact de la rosée** : le même ciel clair qui condense la nuit
  assèche le jour. Calibrer `EVAP_RAD_COEF` pour que, sous climat clair calme à
  15 °C, l'équilibre hydrique **redescende sous le seuil d'asphyxie** → le pommier
  isolé meurt enfin de **sénescence** (critère D39).
- **vent** : le vent balaie la couche limite humide au ras du sol → évaporation ↑.
  C'est l'effet « dessèchement » (a) de D37.

> Calibrage : `EVAP_RAD_COEF` et `EVAP_WIND_COEF` sont des **knobs post-test**. La
> cible quantitative est le retour au vert de `test_senescence` (mort sénescente
> ∈ [49, 112] ans) SANS assécher tout le jardin (vérifier le golden + les suites
> croissance/eau). Garde-fou `EVAP_MIN` conservé (jamais d'assèchement brutal).

**Transpiration foliaire (effet additionnel retenu)** : le vent assèche aussi la
**plante**, pas que le sol. Modélisation sobre : le vent **amplifie l'uptake/perte
hydrique** de la plante exposée (demande évapotranspiratoire) → renforce le stress
hydrique foliaire des grandes feuilles par grand vent. Greffe dans le calcul de
stress hydrique de croissance (lit `vent_local`).

---

## 4. Géométrie d'abri (brise-vent + venturi)

Analogue au calcul d'ombre du `LightField` (capsule projetée). Un **obstacle**
(mur de maison, structure posée, haie dense) projette une **zone abritée SOUS LE
VENT** (force locale réduite) — la « capsule » est orientée par la **direction**
du vent (≠ ombre orientée par le soleil).

- **abri** : `vent_local` réduit dans le sillage de l'obstacle, sur une portée ∝
  hauteur de l'obstacle (règle empirique réelle : abri ≈ 10× la hauteur).
- **venturi** : dans les **goulets** entre deux obstacles, `vent_local`
  **accéléré** (effet de constriction) — c'est la brise de fin de journée qui
  s'engouffre (§2.2).
- une **haie** (plante haute alignée) devient un brise-vent émergent → la
  permaculture du brise-vent s'enseigne par le placement (philo #1 : agir sur le
  milieu). Couple le `LightField` (hauteur des plantes déjà connue).

> Réutilisation : la machinerie de projection orientée existe déjà pour l'ombre
> (capsule). On la **généralise** (un balayage orienté paramétrable), on ne
> réécrit pas. Détail d'archi à trancher au kickoff du tronçon abri.

---

## 5. Effets du vent sur le vivant

### 5.1 Thigmomorphogénèse — le bouclage plasticité (specs Nico)

**Mécanisme moteur** : ajouter une paire dans `_EXPR_MEMOIRE` (`croissance.py`) :

```
"port_trapu": "wind_memory"
```

- **`wind_memory`** : mémoire d'exposition mécanique, intégrée lentement (lerp,
  comme `drought_memory`/`shade_memory`) depuis `vent_local` au plot de la plante.
- **`expressed_gene("port_trapu")`** glisse vers `1 + EXPR_GAIN·wind_memory`
  (hystérèse) → phénotype **trapu/robuste** : tige plus courte et plus résistante.
  Effets : **réduit l'étiolement** (entre-nœuds courts) et **abaisse la
  susceptibilité au dégât de vent** (§5.2).
- **Semis extérieur renforcé** : exposé au vent dès la levée → `wind_memory` monte
  → port trapu → robuste. ✅ effet « renforcer les semis en extérieur ».
- **Semis d'intérieur fragile à la sortie** : élevé à l'abri (semis intérieur de la
  maison, OU conteneur jamais sorti — sprint pots/bacs **mobilité**) → `vent_local`
  ≈ 0 → `wind_memory=0` → port_trapu au repos → **choc à la transplantation
  extérieure** (= absence d'*endurcissement*/hardening off). ✅ effet demandé.
- **Priming transgénérationnel** : `child_expression` fait déjà voyager
  l'expression de la mère avec la graine → une **lignée éprouvée par le vent naît
  pré-armée** (port trapu d'emblée), une lignée de serre non. Aucun code neuf : on
  hérite du système plasticité ④.

> C'est le bouclage le plus élégant du sprint : le vent devient un **nouveau
> stimulus de plasticité**, strictement homogène aux 5 gènes adaptogènes existants.

### 5.2 Dégât des tiges étiolées (specs Nico)

Dégât **médié** (modèle `_mediated_damage`, comme gel/grêle) sur le tissu exposé :

```
sévérité_vent = f(vent_local, risée)
susceptibilité = étiolement(plant) / expressed_gene("port_trapu")
dégât = sévérité_vent · susceptibilité · (1 − protection_abri)
```

- `est_etiole(plant)` existe déjà (sprint Q7) : une tige grêle non sollicitée est
  un bras de levier fragile → casse au vent (surtout en **risée**, §2.2).
- une plante **trapue** (port_trapu exprimé, §5.1) encaisse ; une plante étiolée de
  serre **casse** → la boucle se referme (l'endurcissement protège réellement).
- périmètre de stade : viser le tissu tendre/élancé (cohérent avec le sélecteur de
  `_mediated_damage`, à étendre au-delà du seul « semis » si besoin — décision au
  kickoff, comme la note différée de la gelée blanche).

### 5.3 Pollinisation & dispersion (effet additionnel retenu)

- **Anémophilie** : les espèces à pollen porté par le vent (graminées, noisetier…)
  reçoivent du `pollen_recu` ∝ `vent_local` × densité de congénères en amont
  (direction !) → voie de nouaison **parallèle** à l'entomophilie du pommier.
  Trait d'espèce `pollinisation: "anemophile" | "entomophile"` (registre
  data-driven, cf. arc pollinisation conçu).
- **Butineurs cloués** : grand vent → les butineurs ne volent plus → la
  pollinisation **entomophile** chute par temps venteux (`eco.foragers` modulé par
  `vent_local`). Tension réaliste : jour venteux = mauvais pour l'abeille, bon pour
  la graminée.
- **Anémochorie** : dispersion des graines (samares, aigrettes) **sous le vent** →
  dépôt en banque-sol à distance et **dans la direction** du vent (élargit/oriente
  la succession). Couple `seed_bank` (rayon/direction de dépôt ∝ force).

### 5.4 Vent × maladies fongiques (effet additionnel retenu)

Double tranchant cohérent avec le diagnostic (le pommier isolé chopait « maladie
fongique ») :
- **assèche le feuillage** → réduit la pression fongique locale (le champignon a
  besoin d'eau ; lit `infection_memory`/humidité foliaire) → **la ventilation est
  un remède**, ce qui enseigne l'aération (espacement, taille). ✅ pédagogie permaculture.
- **disperse les spores** → propage l'inoculum **sous le vent** (direction !) entre
  plots/plantes. Net = un arbitrage local entre assèchement protecteur et transport
  contaminant.

### 5.5 Refroidissement éolien (wind chill) (effet additionnel retenu)

Le vent abaisse la **température ressentie / nocturne** :
- aggrave le **gel** des semis exposés (couple `t_min_nuit_at` / gel tissulaire) ;
- **accélère la fonte/évaporation** de la rosée et du givre (couple `tick_rosee`,
  carte `eco.givre`).
Greffe : un terme `−WINDCHILL_COEF·vent_local` dans `t_min_nuit_at` (un abri
réchauffe la nuit, cohérent avec le brise-vent §4).

### 5.6 Transport de litière & neige (effet additionnel retenu)

Le vent **transporte** la litière de surface (`om_fresh`) et la neige et les
**dépose en zone abritée** (sous le vent, §4) → hétérogénéité du sol (un coin
abrité accumule matière + manteau neigeux isolant). Couple décompo/structure.
Modélisation sobre : transfert net d'une fraction de `om_fresh`/neige des plots
ventés vers les plots abrités voisins **dans la direction** du vent.

---

## 6. Ordre dans la boucle & couplages

Insertion proposée (cohérente avec l'ordre nocturne existant) :

```
1.  météo (weather_state)  → + wind_at (masse d'air)         [NOUVEAU]
2a. eco.vent (champ spatialisé via abris)                     [NOUVEAU §2.4/§4]
2b. nébulosité dynamique (pilotée par le vent)                [NOUVEAU §2.3]
2c. thermique (t_min_nuit ± wind chill)                       [enrichi §5.5]
2d. rosée (inchangée, lit nébulosité+thermique déjà ventés)
3.  hydrologie (evap enrichie : +rayonnement +vent)           [enrichi §3]
4.  croissance (thigmo : wind_memory→port_trapu ; transpi)    [enrichi §5.1/§3]
5.  mortalité/dégât (dégât vent médié sur étiolées)           [enrichi §5.2]
6.  repro/pollinisation (anémophilie, butineurs, anémochorie) [enrichi §5.3]
7.  décompo/transport (litière+neige sous le vent)            [enrichi §5.6]
8.  populations/maladies (assèchement vs spores)              [enrichi §5.4]
```

Les `[NOUVEAU]/[enrichi]` sont les seuls points touchés ; le reste est inchangé.

---

## 7. Impact golden (à annoncer)

- **Re-figeage LARGE attendu** dès qu'on touche la nébulosité dynamique (§2.3) et
  l'évaporation enrichie (§3) : lumière + rosée + thermique + eau bougent ensemble.
- Procédure : `python3 -m tests.test_golden --capture` (+ population/vigueur si
  elles bougent), consigner le **nouveau hash** + la **raison** (vent introduit).
- **D39** se résout en effet de bord : `test_senescence` doit repasser au **vert**
  (mort sénescente ∈ [49, 112] ans) — c'est un **critère d'acceptation chiffré** du
  tronçon évaporation (§3). Le test n'est **pas** ré-isolé : il valide désormais que
  le bilan hydrique réel (rosée vs évaporation ventée/radiative) est équilibré.
- Suites à relancer : `test_rosee`, `test_eau`, `test_croissance`,
  `test_stress_chronique`, `test_plasticite`, `test_fruits`, `test_sim_server`.

---

## 7B. Budget de performance — CONTRAINTE #1 (prioritaire)

> Préoccupation **dominante** de Nico (2026-06-29) : ne pas ralentir le moteur. Le
> modèle de vent doit être **le plus riche possible SANS coûter cher**. Quitte à
> découper en plus de tronçons et re-figer large. Cette section prime sur le reste.

**État de l'art (mesuré le 2026-06-29, monde complet 1600 plots / 81 plantes)** :
**~3561 ms/tick**, dont **LightField ≈ 59 %** (`tick_light`→`light.py:compute`→
`_point_in_capsule`), et `_point_in_capsule` **seul = 35 %** (27 M appels/10 ticks).
Suivent `fungal_disease`/`_local_density`/`plots_within_radius` ≈ 25 % (D32 voisin).
En **gameplay** (1 sem = 60 s) la marge tient (×~17), mais un **banc d'essai de
500 ans** = ~25 h → c'est là que « le moteur est trop lent » mord.

**Le danger précis, CONFIRMÉ par la mesure** : la **géométrie d'abri** (§4) est une
projection orientée par obstacle — **la même `_point_in_capsule` qui pèse déjà 35 %
du tick**. Une 2ᵉ capsule recalculée chaque tick **doublerait le poste le plus
cher**. Le **cache + la mutualisation** (leviers 1-2 ci-dessous) passent donc de
« recommandés » à **OBLIGATOIRES**.

**La piste mesurée (2026-06-29) — gather → scatter, GOLDEN-SAFE** : la boucle
lumière-sol (`light.py` L266-291) teste aujourd'hui **chaque plot contre chaque
plante** (gather, **aucun élagage spatial**) ; c'est la part dominante des 27 M
appels (la boucle par-plante, elle, est déjà coupée par le tri-hauteur + `break`).
L'ombre d'une plante est une **capsule de bounding-box minuscule** devant la grille
→ on l'inverse en **scatter** (chaque ombre ne visite que les plots de sa bbox).
Un plot hors bbox renvoie de toute façon `False` → l'opération est **bit-identique**
(golden intact, zéro re-figeage). Mesuré sur le monde déterministe réel
(`tools/diag_light_coverage.py`, 3 ans) : **×5.6 à ×7.1** sur cette boucle selon la
saison, et c'est un **plancher** — le monde de mesure est dense (~70-90 % de plots
ombrés), le banc complet est **20× plus clairsemé** (5 %) → gain réel **>> ×6**.
**C'est la résolution de D32**, faite en **tronçon ⓪** avant tout code de vent :
elle abaisse la base de référence ET prépare la mutualisation (levier 2) dont ③
hérite. **Garde-fou obligatoire** : un **test d'équivalence** (scatter vs gather
bit-à-bit sur le monde smoke) doit verrouiller l'identité avant de solder D32 — un
off-by-one sur l'indexation plot→bbox dériverait le golden en silence.

### Règle d'or : séparer ce qui change VITE de ce qui change LENTEMENT

| Élément | Granularité | Recalcul | Coût |
|---|---|---|---|
| Force/direction masse d'air (`wind_at`) | scalaire/tuile | chaque tick (fonction pure) | O(1) |
| Régimes intra-jour (nul/risées/brise) | scalaire (enveloppe) | chaque tick | O(1) |
| Nébulosité dynamique | scalaire/tuile | chaque tick | O(1) |
| **Champ d'abri `eco.vent`** | **spatial/plot** | **SEULEMENT si direction OU obstacles changent (CACHE)** | amorti ~0 |
| Évaporation enrichie (§3) | dans boucle hydro EXISTANTE | chaque tick (+2 lectures/plot) | marginal |
| wind_memory / thigmo / pollinisation | par PLANTE (peu nombreuses) | chaque tick | négligeable |
| Transport litière/neige (§5.6) | spatial/plot | conditionnel (si vent > seuil) | amorti |

### Leviers anti-coût (intégrés à la conception)

1. **Cache du champ d'abri** : l'abri ne dépend que de (obstacles, direction). Les
   obstacles sont quasi statiques (maison fixe, structures posées rarement, haies =
   plantes hautes à dynamique lente) et la direction est une marche lente → on ne
   recalcule `eco.vent` **que quand la direction franchit un pas angulaire** ou
   qu'un obstacle change. En régime permanent : **coût ≈ 0**. C'est ce qui rend le
   modèle « riche » abordable.
2. **Mutualiser avec le LightField** : capsule d'ombre et capsule d'abri = la même
   machinerie de balayage orienté. Les calculer dans **la même passe géométrique**
   (une traversée, deux sorties) au lieu de deux passes. Optimiser D32 profite alors
   aux deux.
3. **Greffe sans nouvelle boucle** : l'évaporation enrichie (§3) ajoute 2 lectures
   dans `tick_hydrology` **déjà existante** → zéro nouvelle traversée. Idem wind
   chill dans `t_min_nuit_at` (déjà parcouru).
4. **Effets par-plante** (thigmo, anémophilie, anémochorie) : les plantes sont
   ordres de grandeur moins nombreuses que les plots → négligeable.
5. **Transport litière/neige conditionnel** : passe spatiale **sautée les jours
   calmes** (exécutée seulement si le vent dépasse un seuil).

### Conséquence majeure sur le découpage

**On débloque D39 à coût quasi NUL** : les tronçons ① (vent masse d'air, scalaires
O(1)) + ② (évaporation enrichie greffée dans la boucle hydro) suffisent à
rééquilibrer la rosée et faire repasser `test_senescence` — **sans le champ d'abri
spatial**. Le seul morceau potentiellement cher (③ abri spatial) est **isolé,
caché, mutualisé et mesuré seul** → on peut même le reporter si la mesure dérape,
sans bloquer le reste.

### Budget de perf par tronçon (garde-fou d'implémentation)

Chaque tronçon mesure `ms/tick` AVANT/APRÈS sur **le monde complet (1600 plots)**
ET sur un **run long** (banc d'essai). Règle : aucun tronçon n'ajoute plus de
**~+X %** au tick complet sans justification explicite (X fixé par la mesure de
référence du tronçon ⓪). Le tronçon abri (③) est le seul réellement à risque.

---

## 8. Découpage en sous-sprints (révisé perf-first, 8 tronçons)

Chaque tronçon est une unité testable qui préserve (ou re-fige de façon annoncée)
le golden ET respecte le budget de perf (§7B). Ordre choisi pour **débloquer D39 à
coût quasi nul** (⓪→②) avant d'attaquer le seul morceau cher (③ abri).

| # | Tronçon | Contenu | Coût | Golden |
|---|---------|---------|------|--------|
| ⓪ | **Référence perf + scatter LightField (D32)** | profil `ms/tick` monde complet + run long (fixe le budget +X %) PUIS gather→scatter de la boucle lumière-sol (élagage par bbox de capsule), verrouillé par un **test d'équivalence bit-à-bit** ; **mesuré ×5.6-7.1, plancher** | mesure + **gain** | **INTACT** (bit-identique) |
| ① | **Vent masse d'air** | `wind_at` pur (force+direction, saisonnalité, régimes nul/risées/brise venturi) + nébulosité dynamique — **tout scalaire O(1)** | O(1) | neutre (calculé, pas encore lu) |
| ② | **Évapotranspiration enrichie** | `evap` + rayonnement + vent (masse d'air uniforme) greffé dans la boucle hydro EXISTANTE → **`test_senescence` au vert / D39 résolu** | marginal | **re-figeage LARGE annoncé** |
| ③ | **Champ d'abri spatial** | brise-vent + venturi (capsule orientée mutualisée avec le LightField) + **CACHE** (recalcul sur Δdirection/obstacle) → `eco.vent` spatialisé ; wind chill | **À BUDGÉTER** (seul morceau à risque) | re-figeage probable |
| ④ | **Thigmomorphogénèse** | paire `port_trapu↔wind_memory` ; dégât étiolées médié ; transpiration foliaire ; endurcissement semis intérieur/extérieur (+ priming hérité) | par-plante (négligeable) | re-figeage probable |
| ⑤ | **Pollinisation & dispersion** | anémophilie + butineurs cloués + anémochorie | par-plante (négligeable) | re-figeage probable |
| ⑥ | **Maladies fongiques** | assèchement (réduit pression) vs dispersion des spores sous le vent | par-plante (négligeable) | re-figeage probable |
| ⑦ | **Transport & voix** | transport litière/neige (passe **conditionnelle** si vent fort) + signes diégétiques + voix narratives | amorti | re-figeage probable |

> Découpage **perf-first** : le seul tronçon réellement coûteux (③, abri spatial)
> est isolé, caché, mutualisé et **mesuré seul** — il peut même être **reporté en
> dette** si la mesure dérape, sans bloquer la résolution de D39 (⓪→②) ni les
> effets par-plante (④-⑥, négligeables). ① et ② sont le cœur non négociable.
> « Plus de tronçons OK » (Nico) : ④-⑦ peuvent encore se sous-découper si besoin.

---

## 9. Dette / hors-périmètre

- **Arbres en drapeau** (déformation morphologique long terme des arbres exposés au
  vent dominant) : joli mais lourd (état morpho persistant orienté) → **dette**,
  pas ce sprint.
- Réalisme avancé du champ de vent (turbulence, rotor sous le vent d'un mur) :
  hors-périmètre (on reste sur capsule orientée + venturi simple).

---

## 10. Garde-fous (rappel projet)

- Source de vérité Python `data/code/`, lancement depuis `data/code/`.
- Déterminisme : vent dérivé du **hash météo**, zéro RNG vivant.
- Philo #2 partout : flux → contrainte → réponse ; effets « positifs » via
  plasticité, jamais de buff direct.
- Un fichier = une responsabilité, ~350 lignes de code pur, commentaires
  pédagogiques au cœur.
- Toute espèce ajoutée (anémophiles ⑤) = ses 5 voix narratives.
- Décisions de design ouvertes (calibrage des knobs, sélecteur de stade du dégât
  vent, archi de la capsule orientée) → tranchées aux kickoffs, remontées à Nico.

---

## 11. À valider avant de figer les kickoffs

1. Le **modèle de vent riche** (§2) + la **stratégie anti-coût** (§7B : scalaires
   O(1) + champ d'abri caché et mutualisé avec le LightField) te conviennent-ils ?
2. Le **découpage perf-first en 8 tronçons** (§8) : ⓪→② résolvent D39 à coût ~nul,
   ③ (abri spatial) isolé/budgété/reportable, ④-⑦ par-plante négligeables ?
3. Le **re-figeage golden LARGE** (§7) accepté d'emblée (inévitable dès la
   nébulosité dynamique) ?
4. **Perf = contrainte #1** : valides-tu le principe d'un **budget +X %/tronçon**
   mesuré sur le monde complet, avec **report en dette de ③** si la mesure dérape ?
   → **DÉCIDÉ (2026-06-29)** : le LightField/D32 (goulot à 59 %) est intégré au
   **tronçon ⓪** via le scatter golden-safe (mesuré ×6 plancher, §7B) — pré-requis
   acté, pas optionnel.
