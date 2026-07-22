# Dossier d'étude — Physico-chimie du sol (pH · nutriments N/P/K · structure)

> **Dossier d'ÉTUDE, pas une conception figée.** But : te donner de quoi te
> forger une opinion avant qu'on tranche les décisions de design ensemble.
> Structure par volet : *la science (permaculture)* → *l'état du moteur (vérifié)*
> → *chantiers possibles* → *interconnexions* → *questions ouvertes*. Aucune
> décision n'est prise ici. Pédagogie volontairement appuyée côté agronomie
> (hors de ton cœur d'expertise), télégraphique côté moteur (tu connais).
>
> Périmètre acté avec toi le 2026-06-19 : **pH + nutriments N/P/K + structure
> (D30)**. La **température du sol est déjà faite** (sprint thermique-microclimat
> ①→⑩ clos, `docs/champs/climat/conception_thermique_microclimat.md`) — elle n'est rappelée ici que
> comme modèle de référence d'un « champ physico-chimique » réussi.

---

## 0. Vue d'ensemble — pourquoi ce chantier

Aujourd'hui le sol de SYMBIOSE a une **chimie réduite à un seul axe nutritif** :
le champ `fertilite`. Il fait proxy de *tout* (azote, phosphore, potasse, oligo-
éléments confondus), le `microbiome` fait proxy de la vie + d'une part de la
chimie, et le pH **n'existe pas**. C'est suffisant pour un sol vivant générique,
mais ça plafonne trois mécaniques que tu veux ouvrir :

1. **Le pH** — la variable qui décide *quelle plante pousse où* dans la vraie
   permaculture (terre de bruyère vs sol calcaire). Sans lui, pas de calcifuges
   ni de calciphiles, pas d'amendement chaux/soufre, pas de « pourquoi ma
   myrtille dépérit sur mon sol calcaire ».
2. **Les nutriments distincts (N/P/K)** — aujourd'hui fusionnés. Les séparer
   ouvre la *faim d'azote* (BRF/bois frais), la *fixation* (légumineuses),
   les *gourmandes vs frugales*, la rotation des cultures.
3. **La structure / compaction (D30)** — déjà à moitié posée : le bêchage *tape*
   le sol (malus codé), mais la grelinette est un *no-op* faute de champ où
   inscrire le bénéfice d'aération.

Les trois sont **physiquement couplés** (le pH commande la disponibilité des
nutriments ; la structure commande l'eau et l'air donc l'activité microbienne
donc la minéralisation). C'est tout l'intérêt de les concevoir **ensemble** même
si on les **implémente séparément**.

---

## 1. État du moteur sol — ce qui existe VRAIMENT (vérifié dans le code)

`fields/ecofields/container.py` (le cœur) + `constants.py`. Champs continus par
plot (`GridField`, 432 plots/tuile), tickés chaque semaine.

| Champ | Rôle actuel | Plage | Qui l'alimente | Qui le consomme |
|---|---|---|---|---|
| `humidite` | eau du sol | ~[0,3] | pluie de fond, rétention, arrosage | évaporation, drainage, uptake |
| `fertilite` | **proxy unique de TOUS les nutriments** | ~[0,3] | minéralisation de la décompo, météo | `plant_uptake`, lessivage |
| `microbiome` | vie microbienne (≈ Qi + part de chimie) | ~[0,3] | signature des familles, OM | famine (puits), bêchage |
| `soil_memory` ×3 | mémoire lente (fast/deep + composite) | [0,1] | micro+fert+OM+signature | rétention d'eau, succession |
| `litiere` (parcelles typées) | matière fraîche, 6 tissus | masse | morts, abscission, `tailler` | décompo → cascade OM |
| `om_active` / `om_stable` | réserve / humus | [0,10] | cascade de décompo | minéralisation |
| `temperature` / `temperature_sol` | air / sol (sprint thermique) | °C | météo / solaire+inertie | évaporation, croissance |
| `populations[...]` | faune (dont `lombric`) | densité | dynamique trophique | herbivorie, **bioturbation** |
| `disturbance` | perturbation spatiale | [0,1] | bruit + gestes | vitalité, banque graines |

**Points saillants vérifiés** (ils sont nos points d'ancrage, pas à réinventer) :

- **`fertilite` EST déjà le nutriment.** Produit par `tick_decomposition`
  (minéralisation : `fresh_miner + active·MINER + stable·MINER → fertilite.add`),
  consommé par `plant_uptake` (`UPTAKE["fertilite"]` par stade, **boosté par le
  microbiome** `×(1+micro·0.40)`), perdu par `LEACHING_LOSS` (lessivage), diffusé.
  → *Pour séparer N/P/K, c'est CE champ qu'on éclate ou qu'on complète.*
- **La fixation d'azote est déjà esquissée** dans `SOIL_SIGNATURE` :
  `Fabaceae → microbiome +0.15, fertilite +0.10` (les légumineuses enrichissent),
  `Solanaceae → microbiome -0.05` (les gourmandes appauvrissent). C'est un proxy
  grossier mais l'**intention écologique est déjà là** — un vrai cycle d'azote la
  rendrait explicite.
- **`soil_type` existe et sert déjà** : `Tile.soil_type ∈ {terre, argile, sable,
  roche}`, lu par `DRAINAGE_PAR_SOL` (argile retient, sable draine). → *Vecteur
  naturel pour HÉRITER un pH et une texture/CEC par type de sol.*
- **`RONDELLE_TYPES`** (amendements posables sur StakeSlot) =
  `{fertilite, humidite, lombric, maladie, pollinisateur, paillage, auxiliaire}`.
  → *Vecteur pour des amendements pH (chaux, soufre) = nouvelles rondelles.*
- **Aucun gène d'affinité sol.** Les 6 gènes (`hauteur, rusticite_froid, vigueur,
  resistance_pathogene, tolerance_secheresse, tolerance_ombre`) sont
  physiologiques. **Aucune espèce ne déclare de préférence pH/nutriment.** → tout
  est à créer côté catalogue.
- **La structure du sol n'existe pas** comme champ. Le bénéfice d'aération n'a
  « aucun champ où s'inscrire » (cf. kickoff D30).

---

## 2. VOLET A — Le pH du sol

### 2.1 La science (permaculture, pédagogique)

Le **pH** mesure l'acidité (0–14, neutre = 7). Les sols de jardin vont en gros de
**4,5 (très acide, terre de bruyère)** à **8,5 (très calcaire/alcalin)**. Ce n'est
pas un détail cosmétique : c'est **le maître-régulateur de la chimie du sol**.

Trois effets majeurs, par ordre d'importance pour le jeu :

1. **Disponibilité des nutriments (« lockout »).** Un nutriment peut être présent
   dans le sol mais **chimiquement bloqué**, indisponible pour la plante, selon le
   pH. Le **phosphore** est l'exemple roi : disponible seulement autour de pH
   6–7 ; en sol **acide** il se lie au fer/aluminium, en sol **alcalin** au
   calcium → bloqué des deux côtés. Le fer et le manganèse, eux, se bloquent en
   sol **alcalin** (→ chlorose, feuilles jaunes des plantes acidophiles sur
   calcaire). C'est une **courbe en cloche** : un même stock de nutriments « rend »
   plus ou moins selon le pH.
2. **Activité biologique.** Les bactéries (donc la minéralisation, la fixation
   d'azote, la décomposition) sont optimales vers **pH 6–7,5**. En sol très acide,
   la vie bactérienne s'effondre, les champignons dominent, la décompo ralentit et
   la matière organique s'accumule mal digérée (tourbe). → **pH ↔ microbiome ↔
   décompo** sont liés.
3. **Tolérance des espèces.** Chaque plante a une **fenêtre de pH**. Quelques
   familiers :
   - **Acidophiles / calcifuges** (aiment l'acide, *fuient* le calcaire) :
     myrtille, bruyère, rhododendron, châtaignier, fougère, hortensia bleu.
   - **Calciphiles / calcicoles** (aiment le calcaire) : lavande, thym, buddleia,
     vigne, beaucoup d'aromatiques méditerranéennes, légumineuses (luzerne).
   - **Indifférentes / large fenêtre** : la majorité des potagères (pH 6–7).
   - Certaines plantes sont **indicatrices** : l'oseille sauvage, la prêle, la
     bruyère signalent un sol acide — *pile dans ta mécanique d'indicatrices
     existante.*

Comment le pH **bouge-t-il** dans la vraie vie ? **Très lentement.** Il est
tamponné par la roche-mère et l'argile (« pouvoir tampon » ∝ CEC, cf. volet B).
Leviers réels :
- **Roche-mère** : calcaire → alcalin ; granit/grès/sable → acide. C'est l'état
  *hérité*, dominant.
- **Matière organique** : en se décomposant, elle **acidifie doucement** (acides
  humiques) et **tamponne** (amortit les variations).
- **Pluie / lessivage** : lessive le calcium → **acidifie lentement** les sols
  exposés (climat humide = sols plutôt acides).
- **Amendements joueur** : **chaux** (carbonate de calcium) → remonte le pH ;
  **soufre / matière organique acide (aiguilles de pin, tourbe)** → descend le pH.
  Effet **progressif sur des mois/années**, jamais instantané.

### 2.2 État moteur

**Néant.** Pas de champ `ph`. Le `microbiome` et la `fertilite` masquent
partiellement ses effets (sol vivant = bonne décompo ≈ pH correct), mais aucun
lockout, aucune fenêtre d'espèce, aucun amendement pH.

### 2.3 Chantiers possibles (à discuter, pas tranchés)

- **Champ `ph`** : un `GridField` de plus, **hérité du `soil_type`** à l'init
  (table `PH_PAR_SOL` : calcaire→8, terre→6.8, sable→6, roche/granit→5.5…),
  **dérivant très lentement** (lerp décennal façon `soil_memory_deep`) sous l'effet
  de l'OM (↓), du lessivage (↓), des amendements (↑/↓). C'est le frère du
  `temperature_sol` : un champ physico-chimique tamponné à forte inertie.
- **Le lockout** : un **facteur multiplicatif `dispo_nutriment(ph)`** en cloche,
  appliqué à l'uptake de `fertilite` (et plus tard P/K). C'est le couplage le plus
  important — celui qui *donne du sens* au pH. Pédagogiquement honnête : la
  fertilité peut être haute *et* indisponible.
- **Fenêtre d'espèce** : nouveau champ catalogue `ph_min/ph_opt/ph_max` par
  espèce, lu en germination (porte de succession) et en croissance (facteur de
  vigueur). Ouvre calcifuges/calciphiles **et** de nouvelles indicatrices.
- **Amendements** : gestes `chauler` / `acidifier` (ou rondelles `chaux`/`soufre`)
  → poussent `ph` lentement, coûtent de la Vigueur. Le paillage acide
  (aiguilles) tomberait naturellement du système litière.

### 2.4 Interconnexions (règle « tout coexiste »)

`ph` → **microbiome** (activité bactérienne en cloche) → **décompo/minéralisation**
→ **fertilite**. `ph` → **disponibilité** des nutriments (lockout). `ph` ←
**OM/litière** (acidifie) et ← **lessivage** (← `humidite`/climat). `ph` ↔
**catalogue** (fenêtres d'espèces, indicatrices). `ph` ← **amendements joueur**
(gestes/rondelles). C'est la variable la **plus connectée** des trois.

---

## 3. VOLET B — Les nutriments N / P / K

### 3.1 La science (pédagogique)

Les engrais affichent toujours trois chiffres **N-P-K**. Ce sont les trois macro-
nutriments, aux comportements **très différents** — c'est ce qui rend leur
séparation intéressante :

- **N — Azote.** Moteur de la croissance **végétative** (feuilles, tiges, vert).
  **Très mobile** : lessivé par la pluie (part vite), donc **toujours à
  reconstituer**. Sources : fixation par les **légumineuses** (Fabaceae, via
  bactéries Rhizobium dans les nodosités), décomposition de la matière organique,
  apports (compost, fumier). **Piège classique : la « faim d'azote »** — quand on
  enfouit de la matière **carbonée fraîche** (bois broyé/BRF, paille), les microbes
  qui la décomposent **pompent l'azote du sol** pour leur propre croissance et
  l'immobilisent temporairement → les plantes jaunissent. L'azote revient quand la
  décompo est avancée. *Tu as déjà le BRF et la pile à bois (sprint compost ⑤)
  → la faim d'azote est l'interconnexion qui les rend « vivants ».*
- **P — Phosphore.** Racines, floraison, fructification. **Peu mobile** (reste où
  on le met), **fortement dépendant du pH** (lockout, cf. volet A). Libéré
  lentement par l'OM et par certains champignons (mycorhizes — *futur acteur
  champignon, cf. sprint interconnexions à venir*).
- **K — Potasse.** Fruits, résistance (sécheresse, froid, maladies), qualité.
  Mobilité intermédiaire. Sources : cendre de bois, OM, argile (le K est retenu
  par le complexe argilo-humique).

Notion transverse : la **CEC** (capacité d'échange cationique) = le **pouvoir du
sol à retenir les nutriments** (et à tamponner le pH). **Argile + humus = CEC
élevée** (sol « riche » qui retient) ; **sable = CEC basse** (tout lessive). → la
CEC est un *multiplicateur de rétention*, naturellement porté par `soil_type` +
`om_stable`.

### 3.2 État moteur

`fertilite` = **N+P+K fusionnés**. La fixation Fabaceae et l'appauvrissement
Solanaceae sont esquissés dans `SOIL_SIGNATURE`. Le lessivage (`LEACHING_LOSS`)
traite tout comme mobile (faux pour P/K). Pas de faim d'azote, pas de CEC, pas de
distinction végétatif/fructification.

### 3.3 Chantiers possibles

- **Option minimale — garder `fertilite` + ajouter UN axe « azote ».** Le N est de
  loin le plus dynamique et le plus pédagogique (lessivage, fixation, faim
  d'azote). On garde `fertilite` comme « P+K lents » et on ajoute `azote` mobile.
  *Bon ratio richesse/coût ; golden re-figé modéré.*
- **Option complète — trois champs `n`/`p`/`k`.** Fidèle, ouvre rotation des
  cultures, mais **triple** la surface (uptake par stade × nutriment, décompo
  répartie, lessivage différencié, calibrage lourd). *Gros re-figeage golden.*
- **CEC** : un facteur de rétention dérivé de `soil_type` + `om_stable`, modulant
  lessivage et tampon pH. Léger, très rentable.
- **Faim d'azote** : quand de la litière `bois`/carbonée fraîche domine un plot,
  ponctionner temporairement l'`azote` local (les microbes l'immobilisent), puis le
  restituer en fin de décompo. *Interconnexion directe avec le système litière/
  compost et les vers.*

### 3.4 Interconnexions

`azote` ← fixation **Fabaceae** (rend `SOIL_SIGNATURE` explicite) ; ← décompo ;
**← faim d'azote sur litière bois (compost ⑤)** ; → croissance végétative. `P` ↔
**pH** (lockout, volet A) ; ← **mycorhizes** (futur champignon). `K` ↔ **cendre/
argile/CEC**. CEC ← `soil_type` + `om_stable` → module **lessivage** et **tampon
pH**. La rotation des cultures (gourmande après légumineuse) devient lisible.

---

## 4. VOLET C — Structure / compaction (dette D30)

### 4.1 La science (pédagogique)

La **structure** = comment les particules de sol s'agrègent en **grumeaux** avec
des **pores**. Un bon sol grumeleux laisse circuler **l'eau et l'air** ; un sol
**compacté** (piétiné, labouré en semelle, battu par la pluie) devient asphyxiant :
l'eau stagne en surface (ruissellement) ou s'engorge (anoxie → racines qui
étouffent, cf. ton modèle d'asphyxie existant), les racines ne pénètrent plus, la
vie aérobie (vers, bactéries) régresse. Leviers : **vers de terre** (bioturbation),
**racines** (surtout pivots décompactants : radis, luzerne — *tu as déjà
`MedicagoLupulina`*), **grelinette** (aère sans retourner), **paillage** (protège
de la battance). Destructeurs : **bêchage/labour** (effet immédiat trompeur puis
re-tassement), **piétinement**, **pluie battante sur sol nu**.

### 4.2 État moteur + travail déjà fait

La dette D30 a **déjà un kickoff** avec **3 options tranchées** (`sprints/
dette_kickoffs/D30_structure_compaction_sol.md`) :
- **Option A (recommandée là-bas)** : pas de champ neuf — la grelinette **booste
  `lombric`**, le bénéfice transite par le couplage `vers → décompo` qui existe.
  Golden doux.
- **Option B** : champ dédié `structure_sol ∈ [0,1]` modulant **infiltration**
  (couple `humidite`) et **uptake**. Plus fidèle, golden plus large.
- **Option C** : proxy via `humidite`. Déconseillé (sémantiquement faux).

`becher` (malus codé : ↓vers, ↓microbiome) existe ; `grelinette` est le **no-op**
à compléter.

### 4.3 Ce que le périmètre élargi change

Quand D30 était seul, l'Option A (sobre) suffisait. Mais **tu élargis à pH+NPK** :
si on introduit déjà des champs physico-chimiques tamponnés (`ph`, CEC,
éventuellement `azote`), l'**Option B (`structure_sol`)** devient plus cohérente —
elle partagerait l'infrastructure « champ lent hérité du `soil_type` + dérive par
gestes » avec le pH. À rediscuter à la lumière du tout.

### 4.4 Interconnexions

`structure` ↔ **vers** (bioturbation ↑, bêchage ↓) ; → **infiltration/asphyxie**
(← `humidite`, modèle eau existant) ; → **uptake racinaire** ; ← **racines
pivots** (catalogue) ; ← **paillage/battance** (litière). Pont direct avec ton
modèle d'asphyxie déjà codé (`HUM_EXCES`, `asphyxie_factor` dans `plant_uptake`).

---

## 5. Synthèse — interconnexions croisées (la « toile »)

Le cœur du sujet, vu d'ensemble (→ = « influence ») :

```
 soil_type (hérité) ─┬─→ pH ──────┬─→ dispo nutriments (lockout, P surtout)
                     ├─→ CEC ──────┤
                     └─→ drainage  │   ↑
 OM/litière ──→ décompo ──→ N/P/K ─┘   │
      │  acidifie↓pH         ↑ fixation Fabaceae
      │                      ↑ faim d'azote (bois frais, compost ⑤)
 microbiome ←──pH(cloche)────┘
      │
 structure ←─ vers ←─ grelinette ;  structure ─→ infiltration/asphyxie ─→ uptake
      ↑ bêchage↓                                         ↑ humidité (modèle eau)
 catalogue : fenêtres pH (calcifuges/calciphiles) + gourmandes/fixatrices + indicatrices
```

Tout converge vers **deux lecteurs** : l'**uptake** (ce que la plante reçoit
vraiment) et la **germination/succession** (qui peut s'installer). C'est là que le
joueur *voit* la physico-chimie, via les indices biologiques (chlorose, vigueur,
quelles plantes prospèrent), jamais via un chiffre (philo #5).

---

## 6. Décisions à trancher (quand tu auras lu — on les prendra ensemble)

Numérotées pour qu'on les coche une à une. **Ne réponds pas maintenant** — c'est la
carte de notre prochaine conversation de conception.

**pH**
- Q1. `ph` = un `GridField` hérité du `soil_type`, à dérive décennale ? (oui/modèle)
- Q2. Le lockout : courbe en cloche sur l'uptake `fertilite` dès le départ, ou
  branché plus tard ?
- Q3. Fenêtre de pH par espèce : sur **combien** d'espèces au départ (un noyau
  démonstrateur calcifuge + calciphile, ou tout le catalogue) ?
- Q4. Amendements : gestes (`chauler`/`acidifier`) ou rondelles, ou les deux ?

**Nutriments**
- Q5. Minimal (`fertilite` + `azote` mobile) **ou** complet (`n`/`p`/`k`) ?
- Q6. Rend-on `SOIL_SIGNATURE` (fixation/épuisement) explicite via le cycle azote ?
- Q7. Faim d'azote sur litière bois : dans ce sprint ou backlog ?
- Q8. CEC dérivée (`soil_type`+`om_stable`) : oui/non ?

**Structure**
- Q9. À la lumière de l'élargissement : on confirme Option A (vers), ou on bascule
  sur B (`structure_sol`) pour mutualiser l'infra des champs lents ?

**Découpage & golden**
- Q10. Ordre des sous-sprints (proposition §7) ?
- Q11. Stratégie golden : chaque champ physico-chimique introduit **au repos
  NEUTRE** (hérité mais sans lecteur branché) d'abord, lockout/couplages ensuite —
  pour étaler les re-figeages ? (c'est la tactique qui a marché pour le thermique.)

---

## 7. Proposition de découpage en sous-sprints (esquisse, non figée)

Le périmètre complet est **gros** (3 volets, cœur écolo → re-figeages golden). Sur
le modèle du sprint thermique (10 petits tronçons, golden maîtrisé tronçon par
tronçon), une découpe plausible :

1. **pH socle** — champ `ph` hérité du `soil_type`, dérive lente, **aucun lecteur**
   (golden NEUTRE : champ posé, personne ne le lit encore). Overlay F-debug
   gratuit (le registre `fields` par introspection l'expose, comme prévu au pont).
2. **pH → lockout** — courbe de disponibilité sur l'uptake. **Golden re-figé
   maîtrisé** (un seul levier).
3. **pH → catalogue** — fenêtres d'espèces (noyau calcifuge/calciphile) +
   indicatrices acidité. Germination/croissance. Golden ~neutre (espèces neuves).
4. **pH → amendements** — gestes/rondelles chaux/soufre. Hors tick (event-driven)
   → golden NEUTRE côté écolo.
5. **Azote mobile** — champ `azote`, fixation Fabaceae explicite, lessivage propre,
   uptake végétatif. **Re-figé maîtrisé.**
6. **Faim d'azote / CEC** — couplages litière bois + rétention. Re-figé maîtrisé.
7. **Structure** (selon Q9) — A (vers, sobre) ou B (`structure_sol` + infiltration).
8. **Vue** — palettes overlay des nouveaux champs + indices visuels (chlorose).

À ré-arbitrer entièrement après tes réponses au §6 (notamment Q5 qui peut diviser
ou doubler les tronçons nutriments).

---

## 8. Risques & garde-fous

- **Golden.** On touche le **cœur écolo** → re-figeages inévitables, mais
  **étalables** (tactique §7 : poser le champ neutre, brancher après). Smoke test à
  re-figer de façon **maîtrisée et annoncée** à chaque tronçon (règle projet).
- **Sur-modélisation.** Le N/P/K complet (Q5) est le principal risque de gonfler le
  périmètre. La voie minimale (`fertilite` + `azote`) capture 80 % de la pédagogie
  pour 30 % du coût — mon penchant, à débattre.
- **Calibrage.** Comme la maîtrise/la météo, beaucoup de constantes ne se règlent
  que **jeu en main**. Poser des défauts sobres + marqueurs, calibrer post-test.
- **Philo #2/#5.** Jamais de bonus direct sur la plante : pH/nutriments agissent
  **par flux → contrainte → réponse**. Jamais de chiffre en HUD : tout passe par
  les indices biologiques (chlorose, vigueur, qui prospère).
- **Dettes connexes touchées** : D30 (structure, absorbée), le futur acteur
  **champignon/mycorhizes** (P, sprint interconnexions à venir), les **indicatrices**
  (mécanique existante, à nourrir), le **compost ⑤** (faim d'azote).

---

*Fin du dossier d'étude. Prochaine étape : tu lis, puis on tranche le §6 ensemble
et on fige une `CONCEPTION_PHYSICOCHIMIE_SOL.md` (ou un doc par volet). Aucun code
avant.*
