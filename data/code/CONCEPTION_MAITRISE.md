# Conception — Paliers de maîtrise (SYMBIOSE)

> **Document de conception. Aucun code écrit.** Spec de référence pour le futur
> sprint d'implémentation des paliers de maîtrise.
>
> Issu du **Sprint conception paliers de maîtrise** (2026-06-04). Couvre la
> dette **D12**. Remplit l'interface laissée stubbée par le Sprint Vigueur
> (`sim/vigueur.py:palier_bonus() == 1.0`, cf. `CONCEPTION_VIGUEUR.md` §2.3/§7).
>
> **Périmètre : le squelette réutilisable seulement** (décision Nico). Ce doc
> conçoit le *modèle* de maîtrise (objet atomique → progression → agrégats →
> ponts). Il **ne câble pas** chaque action ni n'énumère le catalogue d'objets :
> la définition fine du « succès » par axe, la table palier→déblocage et la
> taxonomie des objets sont déclarées comme **sous-sprints suivants** (§8).

---

## 0. Le constat de départ (et le pivot qui structure tout)

La tentation naïve serait d'attacher la maîtrise aux **5 familles botaniques**.
C'est un piège : le catalogue va grossir (D23/D26), et le jeu visé par Nico est
un **« énorme ensemble d'objets interfaçables, système vivant aux milliers de
secrets »** — outils, structures, techniques, êtres vivants, concepts. Coder la
maîtrise sur 5 familles condamnerait le modèle dès le premier ajout.

**Pivot de cette conception :** l'unité atomique de maîtrise n'est ni l'espèce
ni la famille — c'est l'**objet de maîtrise** générique (§1). Tout le reste
(progression, Vigueur, coût des actions, déblocages) **lit** cet état, ne le
duplique pas.

**Décisions actées avec Nico (4 et 5 juin 2026) :**

| Décision | Acté |
|---|---|
| Unité atomique = **objet de maîtrise** générique, data-driven, catalogue-agnostique | §1 |
| Progression **conditionnée au succès**, sauf la **découverte** (observation seule) ; difficulté **log/exponentielle** ; succès **répétés** aux hauts paliers | §2 |
| Réversibilité **monotone** (un palier ne se perd pas) | §2.4 |
| Spillover **intra-famille uniquement** (pour les êtres vivants) | §3.1 |
| **Deux mesures globales** : complétude-ratio (seuils) ≠ accumulation-log (Vigueur) | §3.2 |
| `palier_bonus(player)` reste **scalaire intact** ; le coût d'action est un **seam séparé** sur `actions.py` | §4 |
| Maîtrise **stockée par objet**, l'action est un **lecteur** (pas d'état par paire action×objet) | §4.2 |
| Méta-état **strictement par avatar** (comme l'encyclopédie/paliers, cf. CLAUDE.md) | §6 |
| **Succès = action joueur qui améliore le résultat au-delà du cours spontané, observée** (≠ événement émergent, ≠ action payée) ; nature de preuve **croissante** par palier ; palier 5 = **conjonction** action experte **+** naturalisation | §9 |

---

## 1. L'objet de maîtrise — l'unité atomique (strate 0)

Chaque **objet de maîtrise** du jeu porte son propre niveau : un palier dans
`{0, 1, 2, 3, 4, 5}` où `0 = inconnu`, puis les 5 paliers de CLAUDE.md :

```
0 inconnu → 1 découverte → 2 investissement → 3 maîtrise → 4 expertise → 5 transcendant
```

Les objets se répartissent en **catégories ouvertes** (data-driven, on en ajoute
sans toucher la structure) :

| Catégorie | Exemples | `qi`/sens |
|---|---|---|
| **Être vivant** | espèces (tomate, framboisier, haricot…), plus tard auxiliaires/nuisibles (D31) | regroupable par **famille** botanique → spillover (§3.1) |
| **Concept transversal** | météo/climat (déjà nommé), sol/microbiome, eau, lumière, succession, pollinisation | la « connaissance écologique/biologique » au sens large |
| **Outil** | sécateur, grelinette, bêche, arrosoir… | geste qualifié |
| **Structure** | serre, palissage, treillis, brise-vent, voile d'hivernage… | aménagement persistant |
| **Technique / geste** | tailler, marcotter, palisser, bouturer, inoculer… | savoir-faire |

> La liste exhaustive des catégories et des objets relève de la **taxonomie des
> objets** (sous-sprint, §8). Ce doc ne fixe que l'**abstraction** : un objet, un
> palier, une catégorie, et — pour les êtres vivants — une famille.

---

## 2. Progression *à l'intérieur* d'un objet (strate 1)

### 2.1 Découverte = gratuite, par observation
Le passage `0 → 1` (découverte) s'obtient par **simple observation** — voir
l'objet (une espèce qui germe, un outil pris en main, un signe météo). C'est le
même signal que l'entrée encyclopédie basique (CLAUDE.md). **Aucun succès requis**
pour découvrir ; la découverte *motive* (et alimente la Vigueur, §4.3).

### 2.2 Paliers supérieurs = succès conditionnés et répétés
`1 → 2 → 3 → 4 → 5` exigent des **succès** de plus en plus pointus. Un « succès »
= un **résultat réussi** mesurable sur l'objet (pour une espèce : un cycle bouclé
sainement jusqu'à maturité/reproduction ; pour un concept météo : un aléa
traversé sans perte ; pour un outil/structure : un usage qui produit l'effet
visé). Aux **hauts paliers**, le succès doit être **répété** — c'est ainsi que la
**fiabilité et la régularité** sont valorisées (un coup de chance ne fait pas un
expert).

> *La définition fine du « succès » par catégorie/axe est traitée en **§9
> (D12.1, 2026-06-04)**. Il n'y reste ouvert que la **calibration** du nombre de
> répétitions par palier (les Nᵢ) → D12.4.*

### 2.3 Courbe de difficulté logarithmique
Le nombre de preuves pour franchir `k → k+1` croît **géométriquement** :

```
preuves(k) ≈ ceil(BASE * R**(k-1))      # BASE, R à calibrer post-test
```

Conséquence voulue (Nico) : un joueur qui **sait déjà** et applique correctement
enchaîne **découverte/investissement vite**, puis **ralentit fortement** vers
expertise/transcendant. La connaissance théorique ne dispense pas de la preuve
répétée — elle accélère seulement le début.

### 2.4 Réversibilité : monotone
Un palier acquis **ne se perd jamais** (décision actée). Cohérent avec « le savoir
voyage à l'avatar au déménagement » (CLAUDE.md) et avec philo #6 (pas de punition
scriptée) : la pression écologique qui revient punit déjà *via la Vigueur dépensée*
(cf. `CONCEPTION_VIGUEUR.md` §3.3), inutile de dégrader la maîtrise.

---

## 3. Agrégats dérivés (strate 2)

Tous **calculés** à partir des objets, jamais stockés en double.

### 3.1 Famille — spillover intra-famille (êtres vivants)
La maîtrise d'une **famille** est un agrégat des espèces de cette famille. Elle
ouvre un **spillover *intra-famille uniquement*** : être avancé sur la tomate
**accélère** la progression de l'aubergine (mêmes Solanaceae) — **pas** celle du
haricot (Fabaceae). Modélisé comme un **bonus de vitesse** (ou un plancher de
départ au-dessus de découverte) sur les autres espèces de la même famille. Le
spillover **ne traverse jamais** les frontières de famille.

### 3.2 Deux mesures globales — *qui ne servent pas à la même chose*
Le piège de dilution (« ajouter une espèce ferait baisser la Vigueur d'un joueur
inactif ») se désamorce en **distinguant deux mesures** :

- **Complétude (ratio)** = `Σ paliers / (5 × nb d'objets DÉCOUVERTS)`. Dénominateur
  = **découverts seulement** → aucune dilution quand le catalogue grossit. Reflète
  « à quel point je maîtrise *ce que je connais* ». **Sert aux seuils de
  déblocage** (paliers globaux, magazine D13, terrain D15).
- **Accumulation (absolue, log-saturée)** = somme brute de maîtrise + activité,
  écrasée par un log. **Sert au plafond de Vigueur max + régen** (§4.1). Porte
  « jardinier actif = vigoureux, mais pas super-héros » : monte avec l'ampleur de
  l'activité, sans jamais exploser ; un *narrow-expert* ne maxe pas la Vigueur — il
  faut de l'ampleur, pas qu'un objet poussé à fond.

Êtres vivants **et** concepts transversaux alimentent les deux mesures dans le
**même pool**.

---

## 4. Ponts — comment la maîtrise agit (strate 3)

La maîtrise a **trois effets distincts** sur la Vigueur (Nico), portés par **deux
seams séparés**.

### 4.1 `palier_bonus(player)` — scalaire intact (plafond + régen)
Les effets **plafond Vigueur max** et **régen passive** sont *globaux par nature*
(« ma vigueur d'ensemble »). Le scalaire `palier_bonus(player)` actuel leur va
parfaitement, alimenté par l'**accumulation-log** (§3.2) :

```python
def palier_bonus(player) -> float:
    # remplit le stub de sim/vigueur.py SANS retoucher la couche Vigueur (decouplage acte §2.3)
    return 1.0 + K * log1p(accumulation_globale(player))   # log -> rendements decroissants
```

**`sim/vigueur.py` n'est pas retouché** : D12 ne fait que *remplir* la fonction
(`vigueur_max = max_base × palier_bonus`, `regen_rate = REGEN_BASE × palier_bonus`,
déjà câblés). Le découplage acté tient.

### 4.2 Coût d'action — un seam *séparé* sur `actions.py`
La **réduction de coût d'un geste** est d'une autre nature : elle vit là où le
coût est calculé (`sim/actions.py`), **pas** dans `sim/vigueur.py`, et n'a aucune
raison de passer par `palier_bonus`. C'est un **second seam, contextuel** :

```python
def cout_action(player, action, objets_touches) -> float:
    base = COUTS[action]                          # cf. CONCEPTION_VIGUEUR §3.1
    # deux termes (formulation Nico) :
    #  1. connaissance globale ecologie/biologie (agregat des concepts + vivants)
    #  2. maitrise PARTICULIERE des objets que CETTE action touche
    attenuation = f_globale(player) * f_objets(player, objets_touches)
    return base * attenuation                     # attenuation in ]0,1], -> calibrage
```

**Maîtrise stockée par objet, action = lecteur** (décision actée) : aucune
maîtrise « par paire action×objet » n'est stockée — ça exploserait
combinatoirement avec des milliers d'objets. Chaque action **déclare la liste des
objets qu'elle touche** (seule donnée nouvelle à câbler par action) et **lit**
leur maîtrise au moment du calcul.

**Exemple `tailler(framboisier)`** : lit `maîtrise(framboisier)` +
`maîtrise(sécateur)` + global. Débutant → coût élevé (charge mentale : « quand ?
comment ? ») ; après pratique ces deux objets montent → coût quasi nul (« coup de
sécateur précis »). `construire(serre)` lit `maîtrise(serre)` + global, **pas**
framboisier ni sécateur → strictement indépendant. **Spillover gratuit** :
pratiquer la taille du framboisier fait monter *l'objet framboisier* → tailler,
récolter, bouturer le framboisier deviennent **tous** moins chers (et le spillover
Rubus/Rosaceae de §3.1 joue).

### 4.3 Sources ponctuelles de Vigueur (découverte & succès)
En plus des sources de `CONCEPTION_VIGUEUR.md` §2.2 (récolte, méditation, manger) :

- **Découverte d'un objet** (`0 → 1`) → petit `+` Vigueur — *la motivation* :
  chaque découverte donne envie d'en savoir plus.
- **Franchissement de palier / succès** → `+` Vigueur — *la récompense* de
  l'effort. « Un jardinier actif est un jardinier vigoureux. »

Ces gains sont **event-driven** (couche gameplay joueur, hors tick écologique
déterministe), comme toute la couche Vigueur.

---

## 5. Récapitulatif des trois effets

| Effet | Mesure source | Seam | Forme |
|---|---|---|---|
| Plafond Vigueur max ↑ | accumulation-log globale (§3.2) | `palier_bonus` (§4.1) | **logarithmique** (anti-super-héros) |
| Régen passive ↑ | accumulation-log globale | `palier_bonus` (§4.1) | × `palier_bonus` |
| Coût d'action ↓ | global éco/bio + objets touchés | `cout_action` sur `actions.py` (§4.2) | **contextuel** par action |

Plus deux **sources ponctuelles** : découverte (+) et succès/palier (+) (§4.3).

---

## 6. Méta-état, déterminisme & golden

Le méta-état de maîtrise vit dans `game_state["maitrise"][player]` (en miroir de
`game_state["vigueur"]`), **par avatar** — l'encyclopédie et les paliers sont
*strictement par avatar*, pas de méta-savoir inter-avatars (CLAUDE.md). Comme la
couche Vigueur :

- Il vit **au-dessus du tick écologique déterministe**, event-driven.
- Le golden (`tests/test_golden.py`) est une **succession spontanée pure, sans
  joueur** → aucune clé `maitrise` → **golden intact, jamais re-figé**. Si un hash
  bouge à l'implémentation, c'est un **bug** (fuite dans le tick).
- Un **golden joueur** distinct (séquence d'actions → trajectoire de maîtrise
  attendue) testera cette couche, sans toucher au golden écologique.

---

## 7. Interfaces avec les autres dettes

- **D11 (Vigueur)** — D12 *remplit* `palier_bonus` (§4.1) et ajoute le seam
  `cout_action` (§4.2). Ne retouche pas `sim/vigueur.py`.
- **D13 (magazine)** — consomme la **complétude-ratio** + paliers pour débloquer
  des espèces (table de mapping, sous-sprint §8).
- **D14 (carnet)** — bascule descriptif → interprétatif au **seuil de maîtrise**
  d'un concept (table de mapping, §8).
- **D15 (extension terrain)** — tuile thématique apparaît au palier **maîtrise**
  d'une famille (table de mapping, §8).
- **Encyclopédie** — partage les signaux de découverte/cycle ; sa complétude
  (basique → bio → effets écosystémiques) suit les mêmes paliers.
- **D31 (vie macroscopique)** — auxiliaires/nuisibles deviendront des **objets de
  maîtrise** (catégorie être vivant) quand ils auront une vitalité propre.
- **D24 (portage C#)** — le méta-état se logera dans `GameManager` (analogue du
  `game_state` dict). `palier_bonus` et `cout_action` = méthodes read-only.

---

## 8. Sous-sprints à venir (ce que ce squelette NE fait PAS)

Le squelette ci-dessus est volontairement **générique**. Restent, en
sous-sprints indépendants :

1. ~~**Définition du « succès » par catégorie/axe**~~ — **FAIT (D12.1, §9)**. Ne
   reste que la calibration des Nᵢ (nombre de répétitions par palier) → point 4.
2. **Table de mapping palier → déblocage** — quel palier ouvre le magazine (D13),
   bascule le carnet (D14), fait apparaître la tuile thématique (D15), enrichit
   l'encyclopédie. La coordination inter-dettes, sans leur mécanique interne.
3. ~~**Taxonomie des objets de maîtrise**~~ — **FAIT (D12.3, §10)**. La liste
   réelle des catégories et objets (espèces réelles, concepts, outils/structures/
   techniques déclarés), et **la liste des objets touchés par chaque action** (la
   donnée que lit `cout_action`, §4.2 → table §10.4).
4. **Calibrage** — `K`, `BASE`, `R`, atténuations de coût, gains ponctuels
   (post-test, comme toute la couche Vigueur).
5. **Portage C#** (D24).

---

## 9. Le succès — définition par axe (D12.1)

> **Sous-sprint D12.1 (2026-06-04), conception seule.** Remplit le point §8.1.
> Précédé d'une **lecture moteur** (les signaux que le tick émet déjà) — le point
> de vigilance acté. Reste ouvert : les **Nᵢ** (répétitions/palier) → calibrage
> D12.4 ; le **câblage par objet** → taxonomie D12.3.

### 9.0 Le pivot — ce qu'est un « succès » (décisions Nico, 4 juin 2026)

> **Un succès = une action joueur dont l'effet émergent améliore le résultat
> au-delà du cours spontané — et qui est observée.**

Ce n'est **ni** un événement émergent sur le terrain (*une tomate qui pousse seule
= bonnes conditions, pas maîtrise*), **ni** une action simplement payée (*cliquer
ne suffit pas*). C'est l'**intervention qui change la trajectoire pour le mieux** —
le geste du jardinier qui obtient un résultat que le milieu n'aurait pas produit
seul (ex. *tailler les gourmands d'une tomate indéterminée → plus de récolte*).

**Opérationnalisation (moteur déterministe, donc pas de contrefactuel calculable) :**
« améliorer au-delà du cours spontané » se mesure par des signaux **déjà émis** —
soit *un stress présent que l'action lève*, soit *un stress qui frappe les
non-protégés et que la préparation prévient*. La couche maîtrise **lit** ces
signaux ; elle n'ajoute aucun état au tick (cf. §6 — golden intact).

### 9.1 Les signaux que le tick émet déjà (lecture moteur)

Transitions discrètes lisibles depuis la couche gameplay (au-dessus du tick) :

| Famille | Signal concret | Source |
|---|---|---|
| Stade | `advance_stage()→True` ; atteinte du **dernier stade** (`maturite==1`, `is_seed_bearing`) | `engine._avancer_stades`, `vigueur_plante`, `reproduction` |
| Santé | `health` 3→…→0 (déclin/mort) ; +1 (convalescence) | `_tick_senescence_health` |
| Mort (par cause) | sénescence · conflit · hiver (annuelle/bisannuelle) · dégât médié (gel/grêle) | `_tick_senescence_health`, `_resoudre_conflits`, `_winter_transition`, `_mediated_damage` |
| Reproduction | parent fructifie → gènes enfant en banque-sol ; recrue 🌰 ; **tag** `auto`/`biparental`/`introgr.` | `engine._reproduction`, `reproduction.py` |
| Floraison/Récolte | phases déclenchées ; graine → `player_seed_bank` si `is_seed_bearing` | `engine.tick_semaine` |
| Météo/aléa | `event.kind`+`intensity` ; **dégât médié renvoie un log VIDE si zéro perte** | `weather_at`, `_mediated_damage`, `appliquer_alea` |
| Stagnation | `⏸ sec` (`ok_hum` faux) · `🌑 ombre` · `❄ froid` | `_avancer_stades` |
| Succession | recrue **férale** issue de la banque-sol qui s'établit | `sim/succession.py`, `eco.tick_seed_bank` |
| Champs (trajectoire) | `microbiome`, `soil_memory`, `fertilite`, `vitalite`, `om_*` (continus, échantillon fin de saison) | `eco.summary()` |
| Actions joueur | `recolter→ratio` (1.0 = payé) · `manger→gain` · `deraciner/ecraser→bool` | `sim/actions.py` |

**Constat structurant :** le moteur possède *tous* les signaux pour les **êtres
vivants** et les **concepts transversaux**. En revanche **outils, structures et
techniques n'existent pas encore** (seuls 4 gestes sur le vivant codés ; le
catalogue d'actions-milieu de `CONCEPTION_VIGUEUR.md` §3.2 est conçu mais non
codé). Leur succès est donc fixé ici comme **patron**, pas comme table calibrable
(câblage → D12.3 + sprints d'action).

### 9.2 Être vivant (espèce) — nature de preuve croissante

| Palier | Preuve = une intervention qui… | Signal lu |
|---|---|---|
| 0→1 **découverte** | …rien : **observer** l'espèce (gratuit, §2.1) | germination vue |
| 1→2 **investissement** | …fait franchir un cap **non franchi seul** (lever une stagnation sec/ombre/froid → reprise de croissance) | flag `⏸/🌑/❄` qui se lève après le geste |
| 2→3 **maîtrise** | …amène à **reproduction** (favoriser pollinisateurs → croisement ; tailler → mise à fruit) | tag `biparental`, `advance_stage` post-geste |
| 3→4 **expertise** | …**optimise** récolte/repro de façon **répétée, fiable, en pleine santé** (tailler les gourmands → récolte ↑) | récolte/repro + `health==3`, répété |
| 4→5 **transcendant** | **conjonction** (§9.4) | voir §9.4 |

### 9.3 Concept transversal — toujours « grâce à ton intervention »

Jamais émergent pur : le stress doit être **levé/prévenu par une action**.

| Concept | Succès |
|---|---|
| météo/climat | **préparation** (paillage/voile/brise-vent) → sujets protégés traversent l'aléa **sans perte** *là où les exposés souffrent* (`_mediated_damage` vide sous protection) |
| sol/microbiome | amender/inoculer/grelinette → `microbiome`/`soil_memory` ↑ et uptake/vigueur suit |
| eau | pailler/drainer → **aucune stagnation hydrique** en saison sèche sur la zone traitée |
| lumière | tailler/éclaircir → strate basse qui repart (un `🌑` chronique qui se lève) |
| pollinisation | favoriser auxiliaires → **croisement biparental** (tag, vs autofécondation) |
| succession | semer/bouturer au bon endroit → recrue **établie** (atteint jeune/adulte) |

### 9.4 Palier 5 (transcendant) = conjonction action **+** naturalisation

Décision Nico : la transcendance est **très dure** car elle exige **les deux** à la
fois (les deux principes de CLAUDE.md cessent de s'opposer — l'action est la
**preuve**, l'auto-suffisance est l'**état atteint**) :

- **(a) Action experte/extraordinaire réussie** (Nₐ fois) — gérer le cas le plus
  dur : un aléa du **~20 % imprévisible** (météo), une intervention de **sauvetage**
  réussie, une optimisation de pointe. *La maîtrise résulte d'actions du joueur.*
- **ET (b) Naturalisation** — une **génération férale** (auto-semée depuis la
  banque-sol, **non replantée** par le joueur) **boucle son cycle en pleine santé**
  dans le sol/microbiome que le joueur a façonné : « le sol et l'environnement
  l'accueillent **comme si elle était native** ». *L'écosystème tient seul.*

C'est le **seul** endroit où le « ça pousse tout seul » compte — uniquement
**conjoint** à (a). Seul, l'auto-semis reste « bonnes conditions », pas maîtrise.

> Les concepts transcendent par analogie : (a) une action experte sur le concept
> (météo : le ~20 % imprévisible géré) **ET** (b) le domaine s'auto-régule sans
> intervention (le sol auto-entretient son microbiome, le cycle de l'eau
> s'auto-tamponne).

### 9.5 Outil / Structure / Technique — patron (câblage D12.3)

Action par nature → succès = l'action via l'objet **produit son effet visé**,
observé dans une fenêtre :

- **outil** : `arroser`→`ok_hum` restauré ; `grelinette`→infiltration ↑ ;
  `sécateur`/`tailler`→empreinte réduite → lumière livrée.
- **structure** : prouve sa fonction **pendant un stress** (`voile` au gel → semis
  intact ; `tuteur` → grand sujet ne verse pas).
- **technique** : son issue émergente (`bouture` reprend N semaines ;
  `inoculer`→microbiome ↑).

v1 minimal acceptable : « action payée **et** effet visé observé = 1 preuve ». Le
détail « quels objets chaque action touche » est la donnée que lit `cout_action`
(§4.2) → **taxonomie D12.3**.

### 9.6 Implications pour la couche maîtrise (sans toucher au tick)

- **État gameplay nouveau, minimal** (au-dessus du tick, par avatar, §6) :
  (i) un **tag de provenance** par plante (*féral* vs *replanté par le joueur*) pour
  distinguer la naturalisation §9.4(b) ; (ii) une **fenêtre d'imputation** liant un
  geste joueur à l'amélioration qu'il produit (le stress levé/prévenu). Aucun de ces
  états ne vit dans le tick déterministe → **golden intact** (§6).
- **Gate d'observation** : un succès se **registre quand il est observé** (carnet
  auto / notification) — cohérent avec « émergent sur le terrain *si c'est observé
  par le joueur* » et avec les trois voix narratives (CLAUDE.md).
- **Répétition (Nᵢ)** : la *nature* de la preuve est fixée ici ; le *nombre* par
  palier suit la courbe log §2.3 et se **calibre post-test** (D12.4).

---

## 10. Taxonomie des objets de maîtrise (D12.3)

> **Sous-sprint D12.3 (2026-06-04), conception seule.** Remplit le point §8.3.
> Précédé d'une **lecture des catalogues moteur** (le point de vigilance acté) : la
> taxonomie **reflète** `plants/` (espèces) + `sim/actions.py` &
> `CONCEPTION_VIGUEUR.md` §3.2/§3.3 (actions) — elle n'invente **aucun** catalogue
> parallèle. Reste ouvert : le **câblage** des objets outil/structure/technique
> (n'existent pas encore dans le moteur → sprints d'action D29/D30/D31) ; les Nᵢ et
> atténuations → calibrage D12.4.

### 10.0 Le pivot — la taxonomie reflète les catalogues, n'en crée pas

Deux catalogues réels existent déjà ; D12.3 ne fait que les **déclarer comme
objets de maîtrise** sans dupliquer leur contenu :

- **Espèces** — `plants/catalogue.py` (`PLANT_CATALOGUE` + `PERENNIAL_CATALOGUE`) :
  **17 espèces** réparties sur **11 familles** botaniques.
- **Actions** — `sim/actions.py` (4 gestes codés sur le vivant) + le catalogue
  *conçu* de `CONCEPTION_VIGUEUR.md` §3.2 (milieu) / §3.3 (vivant) / §3.4
  (ressourcement).

Les catégories **outil / structure / technique** (§1) **n'ont aucun support
moteur** (seuls 4 gestes sur le vivant sont codés). D12.3 les **déclare** comme
objets de maîtrise — patron §9.5 — mais leur **câblage** suit les sprints qui les
introduiront (D29 taille/auxine, D30 structure du sol, D31 vie macroscopique, +
sprints d'action-milieu). **Déclarer ≠ câbler** : la structure data les accueille
(§0), le moteur les remplira plus tard.

### 10.1 Catégorie « être vivant » — le catalogue d'espèces actuel

| Famille | Espèces (clé catalogue) | Spillover §3.1 |
|---|---|---|
| **Solanaceae** | tomate, poivron | ✅ (≥2 espèces) |
| **Fabaceae** | haricot, trèfle, minette | ✅ |
| **Asteraceae** | tournesol, achillée, pissenlit | ✅ |
| **Rosaceae** | pommier, cerisier | ✅ |
| Lamiaceae | basilic | — (singleton) |
| Poaceae | pâturin | — |
| Boraginaceae | phacélie | — |
| Brassicaceae | bourse_pasteur | — |
| Moraceae | figuier | — |
| Juglandaceae | noyer | — |
| Fagaceae | chêne | — |

**Le spillover est data-driven sur la famille réelle, pas sur une liste figée.**
Les 5 familles « cœur » de `plants/base.py` (Solanaceae, Fabaceae, Asteraceae,
Lamiaceae, Poaceae) **ne sont pas privilégiées** : Rosaceae (deux arbres) spille
exactement comme Solanaceae. Une famille ne **spille** qu'à partir de **2 espèces
découvertes** ; les singletons actuels attendent que le catalogue grossisse
(D23/D26) — ils rejoindront le spillover **sans toucher la structure** (tout le
sens du pivot §0). Les adventices (bourse, minette, pâturin, pissenlit) sont des
objets de maîtrise au même titre : **on peut maîtriser une pionnière**.

> D31 ajoutera **auxiliaires / nuisibles** comme objets « être vivant » quand ils
> auront une vitalité propre (cf. §7). Leur regroupement (ordre, guilde) — support
> d'un éventuel spillover — sera fixé alors.

### 10.2 Catégorie « concept transversal »

Six concepts (les mêmes qu'en §1/§9.3), chacun objet de maîtrise à part entière :

> **météo/climat · sol/microbiome · eau · lumière · succession · pollinisation**

Leur **succès** est déjà défini (§9.3). Ils alimentent **les deux mesures
globales** (§3.2) **et** le **terme global** de `cout_action` (§10.4, terme 1) —
**jamais** le terme par-objet : la connaissance écologique est **holistique**
(mieux comprendre l'eau allège *un peu toute* action, pas seulement « arroser »).

### 10.3 Catégories « outil / structure / technique » — déclarées, non câblées

Inventaire **dérivé des actions** de `CONCEPTION_VIGUEUR.md` §3.2/§3.3 (rien
d'inventé hors du catalogue d'actions) :

- **Outils** — *geste qualifié, l'objet qui rend le geste précis* :
  arrosoir, grelinette, bêche, sécateur.
- **Structures** — *aménagement persistant, prouve sa fonction pendant un stress
  (§9.5)* : tuteur, voile d'hivernage, brise-vent, treillis/palissage, serre,
  aménagement-habitat (hôtel à insectes / nichoir / point d'eau / bande fleurie).
- **Techniques / gestes** — *savoir-faire, son issue émergente prouve la maîtrise
  (§9.5)* : semis, arrosage, paillage, amendement, pose-structure,
  bouturage/division/marcottage, drainage, inoculation, aménagement-habitat,
  ameublissement (grelinette), bêchage, récolte, arrachage, **taille**.

Aucun de ces objets n'a d'état moteur aujourd'hui. Ils sont **déclarés** ici pour
que `cout_action` (§10.4) puisse les **nommer** ; le **niveau** de chacun ne
montera que lorsque le sprint correspondant câblera son succès (§9.5).

### 10.4 La donnée que lit `cout_action` — objets touchés par action

Livrable central de D12.3 : pour **chaque action**, la liste d'objets que
`cout_action(player, action, objets_touches)` lit (§4.2).

**Rappel du modèle (§4.2), précisé ici :**

- **Terme 1 — global** `f_globale(player)` : agrégat de **tous** les concepts +
  êtres vivants découverts (la « connaissance écologique générale »). Allège
  **uniformément** toute action. *Les concepts vivent ici, jamais dans le terme 2.*
- **Terme 2 — par-objet** `f_objets(player, objets_touches)` : maîtrise des objets
  **concrets** que CE geste manipule. **Décision D12.3** — le terme 2 est l'union :
  1. **la technique** que l'action incarne (toujours — tout geste qualifié est une
     technique qui s'affûte) ;
  2. **l'être vivant cible** s'il y en a un (→ **spillover famille** §3.1) ;
  3. **l'outil** si le geste en requiert un ;
  4. **la structure** si le geste en pose / emploie une.

> **Réconciliation avec l'exemple §4.2.** Cet exemple (`tailler(framboisier)` lit
> `framboisier + sécateur + global`) était *pré-taxonomie* et son espèce
> (framboisier, Rubus/Rosaceae) est **illustrative** (hors catalogue actuel).
> D12.3 le **raffine** en honorant les catégories §1 : l'**outil** (sécateur) et
> la **technique** (taille) sont **deux objets distincts** — maîtriser le sécateur
> (précision du geste) n'est pas maîtriser *quand/comment* tailler. `tailler` lit
> donc `{taille, sécateur, espèce(→famille), global}`.

**Table des objets touchés** (— = aucun ; *cursive* = objet pas encore câblé côté
moteur ; les **espèces** existent déjà au catalogue, donc non cursivées) :

| Action (phase) | Technique | Outil | Structure | Cible vivante (→ famille) |
|---|---|---|---|---|
| **semer / planter** (planif.) | *semis* | — | — | espèce semée |
| **arroser** (saison) | *arrosage* | *arrosoir* | — | — (agit sur `humidite`) |
| **pailler / mulcher** (planif.) | *paillage* | — | — | — |
| **amender** (planif.) | *amendement* | — | — | — |
| **poser une structure** (planif.) | *pose-structure* | — | *voile / brise-vent / tuteur / serre…* | — |
| **multiplier végét.** (planif.) | *bouturage / division / marcottage* | — | — | pied-mère |
| **drainer** (planif. / saison) | *drainage* | — | — | — |
| **inoculer** (planif.) | *inoculation* | — | — | — |
| **favoriser un auxiliaire** (planif.) | *aménagement-habitat* | — | *hôtel / nichoir / point d'eau* | — (*futur auxiliaire, D31*) |
| **grelinette** (planif.) | *ameublissement* | *grelinette* | — | — |
| **biner / bêcher** (planif.) | *bêchage* | *bêche* | — | — |
| **récolter** (—) | *récolte* | *sécateur* (opt.) | — | espèce récoltée |
| **tailler / éclaircir** (—) | *taille* | sécateur | — | espèce taillée |
| **déraciner** (—) | *arrachage* | *bêche* (opt.) | — | espèce |
| **écraser** un nuisible (saison) | — *(geste brut, peu d'affût)* | — | — | *nuisible (D31)* |
| **manger** (—) | — *(coût NUL → §10.5)* | — | — | espèce (organe) |
| **méditer / observer** (—) | — | — | — | — *(coût NUL, jamais taxé)* |

Les actions **sur le milieu** n'ont **pas de cible vivante** (philo #2 : on agit
sur un champ, la plante répond par émergence) — leur terme 2 se réduit à
technique (+ outil / structure). Les actions **sur le vivant** ajoutent l'espèce
ciblée → **spillover famille gratuit** (§4.2 : pratiquer la taille du cerisier
fait monter *l'objet cerisier* → tailler / récolter / bouturer le cerisier **et**
le pommier (Rosaceae) deviennent moins chers).

### 10.5 Implications & ce qui reste

- **Actions gratuites / triviales** : `observer` et `méditer` (coût NUL, §3.4) et
  `manger` (coût NUL, §3.3) → `cout_action` renvoie 0, terme 2 **vide** : aucune
  technique à lire (rien à alléger). Elles restent objets de **découverte** (voir
  une espèce qu'on mange l'inscrit, §2.1), mais ne portent pas de technique.
- **C'est une donnée, pas un calibrage.** La table fixe *quels* objets chaque
  action lit ; *combien* chaque maîtrise allège (atténuations) et les Nᵢ → **D12.4**
  (post-test).
- **Extensible sans toucher la structure** (§0) : une espèce ajoutée (D23/D26)
  rejoint « être vivant » et sa famille ; un outil / une structure introduit(e) par
  un sprint d'action rejoint sa catégorie et se **branche** sur les actions
  concernées via cette même table. La taxonomie **grandit en largeur**, le modèle
  ne bouge pas.
- **Câblage & dégradation gracieuse** : transformer les objets *en cursive* en
  objets à niveau réel suit les sprints qui les introduisent (D29 taille, D30
  structure du sol, D31 auxiliaires/nuisibles, + sprints d'action-milieu). Jusque-là
  `cout_action` peut déjà **lire** les espèces et concepts réels (terme 1 + cible
  vivante) ; les termes outil / structure / technique restent **neutres (1.0)** tant
  qu'ils ne sont pas câblés.
