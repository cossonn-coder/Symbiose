# Maîtrise — §0-8 · Le modèle (squelette réutilisable)

> Partie 1/3 de la conception des paliers de maîtrise. Index :
> [`conception_maitrise.md`](conception_maitrise.md).
> Suite : [`02_succes_par_axe.md`](02_succes_par_axe.md) (le succès, D12.1),
> [`03_taxonomie_objets.md`](03_taxonomie_objets.md) (la taxonomie, D12.3).

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
(cf. `docs/joueur/vigueur/conception_vigueur.md` §3.3), inutile de dégrader la maîtrise.

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
En plus des sources de `docs/joueur/vigueur/conception_vigueur.md` §2.2 (récolte, méditation, manger) :

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
