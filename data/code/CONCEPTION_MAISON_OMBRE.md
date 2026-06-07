# CONCEPTION — Maison & ombre déterministe + phototropisme

> Doc de conception **figée AVANT code** (règle projet). Sprint **GROS** →
> découpé. Objectif : la maison centrale projette une **ombre déterministe**
> dans le `LightField`, les apex **se penchent** vers la lumière, et la maquette
> montre 3 secteurs contrastés (plein sud / semi-ombre NE / ombre NW).
>
> **Ce doc doit te CHALLENGER sur le coût CPU/RAM de chaque choix.** Le facteur
> limitant du jeu n'est pas la richesse biologique en soi mais *combien
> d'information on peut simuler sans casser l'immersion temps réel*. Chaque
> section « coût » est là pour ça. Les **questions ouvertes (§8)** sont à
> trancher par Nico — défauts proposés signalés.

---

## 0. Décisions déjà verrouillées (conversation 2026-06-07)

| Décision | Valeur |
|---|---|
| Périmètre | **B** — vrai chantier moteur (maison-obstacle + phototropisme + maquette) |
| Maison | **8 × 8 m, 6 m de haut**, centrée, obstacle en espace continu (cm) |
| Anneau de jardin | **6 m** tout autour de la maison |
| Monde | **20 × 20 m = 40 × 40 plots = 1600 plots** (×3,7 vs 432) |
| `PLOT_CM` | **inchangé** (50 cm) |
| Plante à l'ombre | **se penche** vers la lumière (phototropisme directionnel) |

---

## 1. LE point d'architecture — lumière tuile-locale vs globale

**Constat (vérifié dans le code).** Le monde actuel = **9 tuiles
spatialement indépendantes**. Chaque `Tile` a son propre `EcoFields` donc son
propre `LightField`. `engine` appelle `tick_light(tile.plants, saison)` **tuile
par tuile**. Conséquences :

- Les plantes d'une tuile **n'ombragent jamais** celles d'une tuile voisine.
- Il **n'existe aucune coordonnée monde** : une plante est `(row, col)` *dans sa
  tuile*, point. Le « 3×3 » est purement mental, pas géométrique.

Or **la maison projette une ombre à travers les secteurs voisins** : c'est par
nature une ombre **inter-tuiles**. Deux façons de la modéliser, au coût très
différent :

### Option A — `LightField` global unique (espace continu sur tout le monde)
On abandonne les champs lumière par tuile, on calcule la lumière sur **un seul
champ 40×40** où toutes les plantes + la maison coexistent.

- ✅ Physiquement juste : tout s'ombrage avec tout, la maison comme le reste.
- ❌ **Coût explosif.** Le calcul lumière-sol est `O(plots × plantes)`. Le
  partitionnement par tuile est aujourd'hui ce qui *borne* ce coût (chaque plot
  ne teste que les ~quelques plantes de SA tuile). En global, **chaque plot
  teste TOUTES les plantes du monde**. Estimation : plots ×3,7 **et** plantes
  testées ×~9 (plus de partition) → **jusqu'à ~30× le coût lumière actuel** si
  fait naïvement. Le `LightField` est déjà 53 % du CPU → rédhibitoire sans
  structure d'accélération spatiale (grille de hachage / quadtree) = **gros
  sur-coût d'ingénierie** (dette D32 aggravée).

### Option B — champs lumière par tuile CONSERVÉS + injection de la maison ⭐
On garde l'archi tuile-locale (plantes s'ombragent localement, dans leur
parcelle) et on **injecte la SEULE ombre de la maison** dans le `compute` de
chaque tuile, selon la **position monde de la tuile** par rapport à la maison.

- ✅ **Quasi gratuit** : la maison = **un seul obstacle** ajouté au test de
  chaque plot/plante. Surcoût ≈ +1 capsule par itération ≈ **quelques %** sur le
  CPU lumière, pas ×30.
- ✅ Récit pédagogique **propre et vrai** : *les plantes s'ombragent dans leur
  voisinage immédiat ; la maison est la seule structure qui impose une ombre
  globale, déterministe, à l'échelle du jardin.* C'est exactement la « ombre
  certaine » que tu veux mettre en avant.
- ✅ Disruption minimale : on ajoute juste un **offset monde** par tuile
  (`origin_x_cm, origin_y_cm`) — pur data, plumbing trivial.
- ✅ Limite **justifiée diégétiquement** (décision Q1) : les tuiles sont séparées
  par des **chemins en pierre** (allées de circulation, rien n'y pousse) → deux
  plantes de tuiles voisines ne s'ombragent pas *parce qu'*elles sont sur des
  planches séparées. Le découplage n'est plus un postulat, c'est la structure du
  jardin (cf. §2). Seule la maison ombrage globalement.

> **Recommandation forte : Option B.** Elle livre l'ombre de maison voulue pour
> un coût marginal, sans ouvrir le chantier perf de l'option A. L'option A
> resterait pertinente *un jour* si on veut un ombrage inter-plantes continu —
> mais c'est un autre sprint (et il faudrait D32 d'abord).

---

## 2. Layout du monde recommandé — 3×3 où le centre est la maison

L'agrandissement se mappe **élégamment** sur le modèle « 3×3 » existant : on
passe de **9 tuiles jardin** à **8 tuiles jardin + 1 maison au centre**. Ça
colle littéralement à ta phrase « la maison au centre, entourée de tuiles de
permaculture ».

```
   20 m (40 plots)
 ┌──────┬────────┬──────┐
 │  NW  │   N    │  NE  │   coins : 6×6 m  (12×12 = 144 plots)
 │ 6×6  │  8×6   │ 6×6  │   arêtes N/S : 8×6 m (16×12 = 192 plots)
 ├──────┼────────┼──────┤   arêtes E/W : 6×8 m (12×16 = 192 plots)
 │  W   │ MAISON │  E   │
 │ 6×8  │  8×8   │ 6×8  │   MAISON : 8×8 m (16×16 = 256 plots, non cultivés)
 ├──────┼────────┼──────┤
 │  SW  │   S    │  SE  │   Total grille : 40×40 = 1600 plots
 │ 6×6  │  8×6   │ 6×6  │   Cultivable : 1344 plots (×3,1 vs 432)
 └──────┴────────┴──────┘
```

- Les **8 secteurs = les 8 orientations** (N, NE, E, SE, S, SO, O, NO). La
  maquette à 3 secteurs = **3 de ces tuiles** : **S** (plein soleil), **NE**
  (semi-ombre matin), **NO** (ombre soir). Mapping direct, zéro invention.
- À 49°N : l'ombre de **midi pointe vers le Nord** ; le **matin** (soleil ESE)
  l'ombre part vers l'ONO ; le **soir** (soleil OSO) vers l'ENE. Donc **S = jamais
  ombré par la maison**, **N fortement**, **NE/NO partiellement** et de façon
  **asymétrique** (matin vs soir) → contraste pédagogique réel.
- ⚠️ Les tuiles n'ont plus toutes la même taille (144 vs 192 plots). Le code
  tuile est déjà paramétré `rows, cols` (`init_eco(tid, rows, cols)`) → **pas de
  régression**, juste des dimensions variées. **Décision Q2 : tailles
  hétérogènes conservées** (le code le supporte, zéro sur-coût).

### Chemins en pierre entre tuiles (décision Q1)

**Entre chaque tuile court une allée en pierre** où le jardinier circule et où
**aucune plante ne pousse**. Rôle :

- **Diégétique** : c'est la raison concrète pour laquelle les plantes de deux
  tuiles voisines ne s'ombragent pas — elles sont séparées par une allée. On ne
  *postule* plus le découplage, le jardin *est* fait de parcelles séparées par
  des allées (potager en carrés / permaculture en planches).
- **Technique** : les plots d'allée sont **non-cultivables** (ni semis, ni
  succession spontanée). Ils peuvent être exclus du calcul lumière-plante (rien
  n'y pousse) → léger gain. La maison, elle, ombrage *par-dessus* les allées
  comme le reste.
- **Largeur** : **défaut 1 plot (50 cm)** entre tuiles — à confirmer au
  sous-sprint 1 (50 cm = sentier étroit ; 1 m = 2 plots = allée brouette). Les
  allées **rognent** légèrement les tuiles dans les 20×20 m (le plot-arithmétique
  exact se fige au sous-sprint 1, c'est un détail de layout, pas de design).
- **Rendu** (plus tard, Godot) : tuiles de pierre claire → repère visuel de
  circulation, cohérent avec le calcaire de la maison.

---

## 3. Modèle d'ombre du bâtiment

L'ombre actuelle d'une plante est une **capsule** : un disque de rayon `r`
balayé le long de la direction d'ombre sur `longueur = hauteur × inv_tan(élév)`
(`_point_in_capsule`). La maison est un **pavé 8×8×6 m**. Trois modèles, du moins
au plus fidèle (et cher) :

| Modèle | Fidélité | Coût/plot | Verdict |
|---|---|---|---|
| **Capsule-disque** (rayon ≈ 4–5,6 m) | ombre ronde, NE≈NO symétriques au midi | = 1 capsule (≈ existant) | repli si la maths bloque |
| **Rectangle balayé** (footprint carré × déplacement) | ombre « hexagonale », coins nets, asymétrie correcte | ≈ 2–3× une capsule | ⭐ **recommandé** |
| **Projection 3D exacte du pavé** | photoréaliste | lourd, inutile vu le pixel-art iso | ❌ overkill |

- **Recommandation : rectangle balayé** = l'ombre est l'union, pour
  `s ∈ [0, hauteur·inv_tan]`, du carré-footprint translaté de `s·(dx,dy)`.
  Test point-dans-zone analytique (pas de raster), déterministe, ~quelques
  lignes. Coût négligeable (1 obstacle, évalué 1×/plot/tranche).
- **Hauteur 6 m** → longueur d'ombre : été midi ≈ 2,9 m ; hiver midi ≈ 19 m
  (soleil rasant) ; matin/soir bien plus longue et oblique. L'anneau de 6 m
  capte donc une **forte saisonnalité** d'ombre — excellent pour la pédagogie
  (le même coin est cultivable l'été, à l'ombre l'hiver).
- **Opacité** : la maison est **opaque** (≠ canopée à `foliage_density < 1`).
  Sous son ombre pleine, on tombe au **plancher `LIGHT_FLOOR = 0.15`** (lumière
  diffuse du ciel).

### Albédo du mur calcaire — l'effet espalier (décision Q5)

Le mur est en **calcaire de Montmartin** (pierre claire, **albédo ≈ 0.35**). Une
face **ensoleillée** ne fait pas qu'arrêter la lumière : elle en **renvoie** une
fraction sur le sol *devant elle*. À 49°N, c'est surtout la **face sud** qui est
éclairée → un **point chaud lumineux au pied du mur sud** = l'effet **espalier**
bien connu en horticulture (on plante les fruitiers contre un mur sud chaud).
**Pédagogiquement riche** (microclimat, exposition).

- **Modèle borné (coût OK)** : pour chaque plot situé **devant une face de mur
  actuellement éclairée**, dans un **rayon court** (≈ 2–3 m), ajouter une
  contribution `+= albédo × intensité_incidente × falloff(distance)`, plafonnée à
  1.0. Hors de ce rayon, ou si la face est à l'ombre → rien. **Coût** : quelques
  plots concernés seulement (pas tout le monde) → **négligeable**.
- ⚠️ L'albédo **n'éclaire pas** les secteurs ombragés (la face nord est elle-même
  à l'ombre) : il **renforce le secteur déjà ensoleillé**. C'est voulu (espalier),
  pas une correction de l'ombre nord.
- **Désactivable** : `wall_albedo = 0.0` retombe sur le modèle opaque pur. Si le
  sous-sprint 2 devient lourd, l'albédo peut glisser en **2b** sans bloquer
  l'ombre de base.

### Maison paramétrable — config de terrain (décision Q5)

La maison n'est **pas codée en dur** : elle est décrite par une **config de
terrain** (objet `House`/`Building`), choisie **à la création d'une instance** :

| Paramètre | Défaut | Plus tard |
|---|---|---|
| Position (centre) | centrée | n'importe où dans le monde |
| Empreinte | 8×8 m | variable |
| Hauteur | 6 m | variable (longueur d'ombre) |
| Matériau mur / albédo | calcaire Montmartin (0.35) | brique, bois, crépi… |
| Climat / latitude | 49°N (Normandie) | autres climats |

Se relie à la **« seed d'origine du terrain persistée »** (profils/terrains) :
le placement + matériau + climat font partie de l'identité d'un terrain. **Ce
sprint** implémente la **structure paramétrable** avec ces **défauts** ; l'UI de
choix viendra avec la création de profil/terrain (backlog).

---

## 4. Phototropisme directionnel

Aujourd'hui **stubé neutre** dans `growth.py` (apex tout droit + jitter latéral
déterministe). À brancher : l'apex **biaise sa direction horizontale vers la
lumière**.

- **Source du gradient** : le `LightField` donne la lumière-sol par plot
  (`at_plot`). On échantillonne la lumière dans quelques directions autour de
  l'apex et on incline vers la plus lumineuse (ou on suit le gradient discret).
- **Déterministe, zéro RNG** (contrainte dure). Le biais doit être **continu**
  et **borné** (un apex ne se couche pas à plat — angle max/tick).
- **Coût** : quelques `at_plot` supplémentaires par apex/tick. Négligeable
  devant le `LightField` lui-même.
- ⚠️ **Impact comportemental GLOBAL** : ça modifie la croissance de **toutes**
  les plantes (même en lumière uniforme le bruit crée un micro-gradient). C'est
  le morceau **risqué** côté golden (§7).
- **Intensité (décision Q3)** : **MARQUÉ par défaut** (plus lisible/pédagogique),
  mais l'intensité est un **paramètre** (`phototropism_strength`). Le sous-sprint
  3 **rend les deux** (subtil ET marqué) côte à côte dans la maquette → **Nico
  tranche à l'œil** la valeur finale. Dans tous les cas : **borné** (angle
  max/tick, l'apex ne se couche jamais à plat) et **déterministe**.

---

## 5. Cadre de coût CPU / RAM — ce qui te limite vraiment

> Référence mesurée (perf_profile) : **177 ms/tick** à 432 plots, dont
> **`LightField` ≈ 53 %** (~94 ms). Marge gameplay ÉNORME (1 semaine = 60 s réel
> → ×339). **Le vrai coût n'est pas le jeu, c'est le golden** (test de
> non-régression rejoué des centaines de ticks à chaque modif), déjà réduit à
> 10 ans pour cette raison.

**Lois d'échelle à garder en tête (c'est ça, le facteur limitant) :**

| Levier | Loi de coût | Effet d'un ×2 |
|---|---|---|
| Nombre de plots | linéaire (lumière-sol) | ×2 CPU lumière |
| Nombre de plantes | linéaire (par plot et reçu) | ×2 CPU lumière |
| Densité d'obstacles/capsules | linéaire | +1 obstacle ≈ +qq % |
| Tranches solaires (`SOLAR_HOUR_ANGLES`) | linéaire (×3 aujourd'hui) | ×2 = ×2 CPU lumière |
| **Global vs tuile-local (option A)** | **quadratique caché** (perte de partition) | **~×30** |
| Phototropisme | qq `at_plot`/apex | négligeable |

**Conclusion chiffrée pour ce sprint (option B) :**
- Monde ×3,7 plots → CPU lumière **×~3,7** (la maison elle-même ≈ +qq %).
- Golden : passer à 1600 plots le rend **~3,7× plus lent**. Tick golden ~177 ms
  → ~650 ms. Sur 520 ticks (10 ans) ≈ **5–6 min** de test. **Tolérable mais à
  l'œil.** → **Question Q4 (§8)** : garde-t-on le golden sur un **petit monde
  dédié** (rapide) et couvre-t-on maison/phototropisme par des **tests ciblés**,
  ou bascule-t-on le golden sur le grand monde ?
- RAM : 1600 plots × ~quelques champs `float` ≈ qq Mo. **Non-sujet** (mesuré
  27 Mo aujourd'hui, marge énorme).

---

## 6. Triage pédagogique — qui mérite d'être VISUEL, qui reste un champ math

Tu l'as posé comme principe directeur : *certains détails de la nature sont
invisibles (racines) et restent des champs mathématiques ; d'autres sont visuels
et porteurs d'enseignement*. Voici la **grille de tri** que je propose
d'appliquer à chaque mécanique, AVANT de dépenser du CPU dessus :

**Une chose mérite un rendu VISUEL (donc du coût) si :**
1. elle est **observable dans la vraie nature** à l'œil du jardinier, **et**
2. la **voir** enseigne quelque chose qu'un chiffre n'enseignerait pas (forme,
   direction, dynamique spatiale), **et**
3. son coût de rendu est **borné** (pas de explosion combinatoire).

**Sinon → champ mathématique invisible** (lu via overlay debug si besoin).

Application à ce sprint :

| Élément | Visuel ? | Justification |
|---|---|---|
| **Ombre de la maison au sol** | ✅ **OUI** | Observable, structurante, enseigne « oriente tes cultures » — cœur pédagogique du sprint |
| **Inclinaison des apex (phototropisme)** | ✅ **OUI** | Observable (les plantes « cherchent » la lumière), enseigne l'étiolement/la course à la lumière |
| **Maison elle-même (sprite/volume)** | ✅ OUI (rendu Godot, plus tard) | Repère spatial, hub |
| **Champ de lumière-sol** | ❌ champ math (+ overlay debug) | Déjà un `GridField` ; le *résultat* (ombre, plantes penchées) est ce qu'on voit |
| **Racines** | ❌ champ math | Invisibles dans la nature ; rayon dérivé suffit (déjà acté) |
| **Gradient de lumière utilisé par le tropisme** | ❌ math interne | C'est l'*effet* (apex penché) qui est pédagogique, pas le gradient |

> **Garde-fou anti-dérive de coût** : avant d'ajouter une mécanique *visuelle*
> future, repasser cette grille. Si elle échoue au test 2 (« voir enseigne plus
> qu'un chiffre ») ou 3 (coût borné), elle reste un champ math. C'est la
> discipline qui protège l'immersion temps réel.

---

## 7. Stratégie golden (non-régression déterministe)

Le golden est sacré (règle de design #3). Trois choses le perturbent ici :
agrandir le monde, l'ombre de la maison, le phototropisme.

- **Agrandir le monde** = nouveau scénario `main.py` → le golden **change par
  construction**. Inévitable.
- **Phototropisme** modifie la croissance de **toutes** les plantes → re-figeage.
- **Ombre maison** ne touche que les plots ombrés → re-figeage *localisé*.

**Décision Q4 — golden = SMOKE TEST, réduit au plus petit pertinent.** Le golden
de non-régression tourne sur un **petit monde, peu d'années** (rapide, à lancer
souvent). Les cas qui *exigent* une longue simulation (ex. **sénescence du
pommier ~70 ans**) deviennent des **tests dédiés séparés, plus longs**, lancés à
la demande — pas dans le smoke test quotidien. Le nouveau comportement est
couvert par des **tests ciblés** :
- `test_ombre_maison` : « un plot au N de la maison reçoit moins de lumière qu'au
  S, à saison donnée » ; déterminisme ; l'ombre s'allonge en hiver ; **albédo :**
  un plot au pied du mur sud ensoleillé reçoit *plus* que le plein champ.
- `test_phototropisme` : « un apex sous gradient se penche vers le clair ; apex
  en lumière uniforme reste ~droit ; déterminisme ; angle borné ».

Avantage : le golden reste **rapide** (pas 1600 plots ni 70 ans) et le nouveau
comportement est couvert **finement** (mieux qu'un hash global opaque). C'est
exactement la doctrine déjà appliquée à la croissance procédurale (test d'allure
plutôt que golden gonflé). ⚠️ **Conséquence** : le scénario `main.py` actuel
(9 tuiles, jusqu'à 30 ans, pommier sénescent) **n'est plus le golden** — il
devient une **démo/banc d'essai**, et le golden smoke test est **reconstruit
minimal** au sous-sprint 1.

---

## 8. DÉCISIONS DE DESIGN (tranchées par Nico — 2026-06-07)

- **Q1 — Ombrage inter-tuiles → RÉSOLU : option B + chemins en pierre.**
  **Entre chaque tuile court un chemin en pierre** où le jardinier circule et où
  **aucune plante ne pousse**. Ça **justifie diégétiquement** l'absence d'ombrage
  inter-tuiles (les tuiles sont séparées par des allées) au lieu de l'« assumer ».
  **Seule la maison ombrage globalement.** Coût ×30 (option A) évité. → impacte §2.
- **Q2 — Tailles de tuiles → RÉSOLU : hétérogènes, intégrant les chemins (Q1).**
  Les tuiles peuvent être agrandies si besoin ; si leur taille est dictée par la
  localité des ombres, on les garde telles quelles (les ombres sont locales).
- **Q3 — Phototropisme → RÉSOLU : MARQUÉ par défaut (meilleur pédagogiquement),
  MAIS Nico tranchera sur exemples.** Le sous-sprint 3 produit **les deux**
  (subtil ET marqué) côte à côte dans la maquette pour comparaison à l'œil. →
  impacte §4 et §9.
- **Q4 — Golden → RÉSOLU : smoke test rapide, réduit au plus petit pertinent.**
  Le golden = **petit monde, court** (style smoke test, quelques années). Les cas
  qui exigent une longue simulation (ex. sénescence ~70 ans) ont des **tests
  dédiés plus longs, à part**. Maison/phototropisme couverts par tests ciblés. →
  impacte §5, §7.
- **Q5 — Mur & albédo → RÉSOLU : mur calcaire de Montmartin, AVEC albédo borné,
  maison PARAMÉTRABLE.**
  - Mur en **calcaire de Montmartin** (pierre normande, claire) → **albédo ~0.35**
    qui renvoie de la lumière vers sa **face ensoleillée** = **point chaud
    « espalier »** au pied du mur sud (microclimat pédagogique). **Inclus car coût
    OK si borné** (seulement plots proches d'une face éclairée). → impacte §3.
  - **Maison paramétrable** : position, type d'architecture, climat = **config de
    terrain** choisie à la création d'une instance. Défauts : centrée, 8×8×6,
    calcaire. Se relie à la « seed d'origine du terrain persistée ». → impacte §3.
- **Q6 — Maquette → RÉSOLU : cycle annuel, image tous les 3 mois.**
  Pour **chaque secteur** (S / NE / NO) **et chaque plante testée**, **4 images**
  (une par saison, tous les 3 mois) → montre la variation saisonnière de l'ombre
  et de la croissance. Grille `secteurs × 4 saisons × plantes`. → impacte §9.

---

## 9. Découpage en sous-sprints (chacun autosuffisant, préserve/re-fige le golden)

> Structure standard projet : `sprints/sprint_maison/00_etat.md` (état partagé
> léger) + `01_*.md`, `02_*.md`… (kickoffs autonomes). `/clear` entre tronçons.

1. **Monde agrandi + maison-obstacle INERTE.** Nouveau layout 3×3 (centre =
   maison), offset monde par tuile (`origin_*_cm`), géométrie maison (data
   seule, **ne projette pas encore d'ombre**). Nouveau scénario `main.py`.
   → golden re-figé (monde change) **ou** golden gelé sur petit monde (selon Q4).
2. **Ombre de la maison dans `LightField.compute`.** Rectangle balayé injecté
   (sol + reçu par plante), par position monde de la tuile. `test_ombre_maison`.
   → re-figeage localisé.
3. **Phototropisme branché dans `growth.py`.** Apex se penche vers le gradient,
   déterministe, borné, intensité paramétrable. `test_phototropisme`. La maquette
   rend **subtil ET marqué** côte à côte → Nico tranche l'intensité (Q3).
   → re-figeage maîtrisé. **(risqué)**
4. **Maquette saisonnière 3 secteurs.** `render_structure.py` +
   `export_structure.py` : pour chaque secteur (S / NE / NO) et chaque plante
   testée, **4 images (1/saison, tous les 3 mois)** dans un vrai `LightField` +
   maison (+ albédo). Grille `secteurs × 4 saisons × plantes`. Montre la
   variation saisonnière de l'ombre et de la croissance. → outil seul, golden
   intact.
5. *(plus tard, hors ce sprint)* Rendu Godot de la maison + ombre, portage C#
   (D24).

---

*Doc créé le 2026-06-07. À figer après réponses §8. Source de vérité = ce doc
pour le sprint maison.*
