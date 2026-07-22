# Conception — Vigueur universelle + coûts d'action (SYMBIOSE)

> **Document de conception. Aucun code écrit.** Spec de référence pour le
> futur sprint d'implémentation Vigueur (qui sera découpé en sous-sprints et
> devra préserver `tests/test_golden.py`).
>
> Issu du **Sprint conception Vigueur** (2026-06-04). Couvre la dette **D11**
> (Vigueur universelle + coûts d'action), prépare le recâblage du gène
> `vigueur` provisoire (D22b) et l'action « manger » (D19). Décisions actées
> avec Nico : **façade dérivée** pour la Vigueur des plantes, **interface
> paliers stubbée** pour la dépendance D12.

---

## 0. Le constat de départ (et le pivot qui structure tout)

La tentation naïve serait d'ajouter un nouveau scalaire « Vigueur » à chaque
être vivant et de faire transiter de l'énergie partout. **C'est inutile : le
moteur modélise déjà la quasi-totalité de la Vigueur des plantes sous d'autres
noms.**

| Concept « Vigueur » (CLAUDE.md) | Déjà implémenté comme |
|---|---|
| « se puise dans le territoire » | l'**uptake** racinaire sur `fertilite` / `microbiome` (`_apply_uptake`) |
| « y retourne à la mort » | la **nécromasse** ∝ hauteur (`add_necromass`, flag `harvested`) |
| Vigueur = énergie propre d'une plante | la **santé dynamique** + `vitalite()` + le gène `vigueur` (provisoire) |
| Vigueur joueur logée quelque part | `game_state["current_player"]` + `scores` existent déjà |
| Coût d'une action joueur | hook `HARVEST_VIGUEUR_COST` déjà câblé (neutre) |

**Pivot de cette conception :** la Vigueur n'est pas *un* système, c'est **deux
strates distinctes** qui partagent un vocabulaire narratif (« Vigueur ≡ Mana »)
mais jouent des rôles mécaniques différents :

1. **Cœur écologique déterministe** (le tick `engine`) — la Vigueur d'une plante
   est une **lecture façade** d'états existants, pas un nouvel état. Reste pur,
   seed + hash spatial, **golden intact**.
2. **Couche gameplay joueur** — event-driven, vit dans `game_state` par joueur,
   **au-dessus** du tick. C'est le seul *vrai nouveau* système.

> **Principe directeur, valable partout dans ce doc :** le déterminisme
> écologique (philo #3) est sacré. La Vigueur joueur et les coûts d'action sont
> des **entrées/comptabilités gameplay** qui ne font jamais avancer la
> simulation par elles-mêmes — elles réagissent aux actions et modifient l'état
> écologique *comme une donnée d'entrée*, jamais comme un RNG vivant.

---

## 1. Vigueur des êtres vivants — façade dérivée (décision actée)

**Pas de nouvel état stocké.** La Vigueur d'une plante est une fonction pure,
read-only, de ses états existants :

```python
def vigueur_plante(p) -> float:
    # facade unificatrice : aucune ecriture, aucun budget energetique a equilibrer
    return sante(p) * maturite(p) * qi_local(p) * p.gene("vigueur")
```

- `sante(p)` — santé dynamique déjà gérée par la sénescence (D27).
- `maturite(p)` — avancement de stade (un semis a peu de Vigueur, un adulte
  plein).
- `qi_local(p)` — Qi territorial lu sous l'empreinte racinaire (cf. §4).
- `p.gene("vigueur")` — **garde ses usages actuels** (`needed = duration / gène`,
  `heal × gène`). On ne le débranche pas ; on l'**enveloppe**.

**Pourquoi façade et pas champ stocké :** zéro risque golden, zéro état nouveau,
zéro budget énergétique entrant/sortant à calibrer. La Vigueur d'une plante sert
de **lecture diégétique** (l'encyclopédie/carnet peuvent la décrire, un futur
overlay debug peut l'afficher) et de **modulateur de la valeur des organes
consommés/récoltés** (§3) — pas d'une variable pilote. Les auxiliaires et
nuisibles suivront le même patron façade quand leur champ ambiant sera conçu.

---

## 2. Vigueur joueur — l'unique nouvel état

Vit dans `game_state` par joueur (le `current_player` existe déjà), **hors du
tick écologique déterministe**. Modèle de base (chiffres CLAUDE.md, *à calibrer
post-test*) :

```
game_state["vigueur"][player] = {
    "courante": 100,     # montant actuel
    "max_base": 100,     # plafond avant bonus paliers
}
```

### 2.1 Cycle
- **Régen passive** : `+REGEN_BASE` (≈ +10) par semaine simulée, calculée sur la
  *tranche joueur* de `game_state` lors du tick — **n'affecte pas le golden** (le
  golden ne contient aucun joueur).
- **Plein au passage de saison** : `courante = vigueur_max(player)`.
- **Plafonnée** à `vigueur_max(player)` (cf. §2.3).

### 2.2 Sources (gains)
1. **Récolte de plantes/organes mûrs** — gain ∝ maturité de l'organe (cf. §3,
   net après coût du geste).
2. **Méditation au foyer** (maison normande) — recharge dédiée, point de
   ressourcement.
3. **Manger** (action « manger », D19) — consommer feuille / fleur / fruit ;
   gain ∝ `maturite(organe)`. Détruit l'organe. *La modélisation des organes
   consommables relève de D19 ; ce doc fixe seulement la comptabilité Vigueur du
   gain.*

### 2.3 Plafond et régen scalent avec la maîtrise — **interface stubbée** (décision actée)
Les paliers de maîtrise (D12) ne sont pas construits. On conçoit la Vigueur de
façon **autonome** derrière une interface propre :

```python
def vigueur_max(player) -> float:
    return MAX_BASE * palier_bonus(player)        # plafond

def regen_rate(player) -> float:
    return REGEN_BASE * palier_bonus(player)      # vitesse de regen passive
```

`palier_bonus(player)` est un **stub renvoyant 1.0** tant que D12 n'existe pas.
Quand les paliers arriveront, ils remplissent cette fonction **sans retoucher la
couche Vigueur**. C'est le même découplage que météo↔paliers (le signe météo
porte un flag, l'appelant palier filtre).

---

## 3. Catalogue des actions joueur — l'usure de la solution facile (philo #1)

Le joueur agit **principalement sur le milieu**. L'action directe sur le vivant
reste possible mais **coûte de la Vigueur et perturbe** — c'est ainsi que la
permaculture s'enseigne (philo #1). La Vigueur n'est pas qu'un compteur : son
**signe** encode la pédagogie. Soigner le milieu est soutenable ; forcer le
vivant s'use.

### 3.1 Trois axes de classement

- **Cible** — *milieu* (canal vertueux, philo #1/#2) vs *vivant* (possible mais
  coûteux).
- **Phase** — *planification* (temps figé, geste réfléchi, coût modéré) vs
  *saison* (temps réel, urgence, coût majoré). Une même action peut exister dans
  les deux phases à des coûts différents (arroser en prévention ≠ arroser en
  catastrophe).
- **Signe Vigueur** — `+` source, `0` neutre, `−` dépense.

Paliers de coût proposés (*relatifs à la base 100 / +10 par semaine, à calibrer
post-test*) : `NUL = 0`, `FAIBLE ≈ 5`, `MODÉRÉ ≈ 15`, `ÉLEVÉ ≈ 30`. L'urgence
(phase saison) applique un **multiplicateur** (`× URGENCE`, ≈ 1.5–2) au coût de
base.

### 3.2 Actions sur le milieu — le canal vertueux (philo #2)

**Principe non négociable (philo #2) :** l'action ne touche **jamais** la plante
directement. Elle modifie un **champ écologique** ; la plante répond par
**émergence**. C'est la seule façon d'agir « gratuitement » au sens où le milieu,
lui, encaisse et redistribue.

| Action | Phase | Champ modifié | Coût | Réponse émergente |
|---|---|---|---|---|
| **Semer / planter** | planif. | introduit une graine (banque-joueur) à `x_cm,y_cm` | `FAIBLE` | germination → succession ordinaire |
| **Arroser** | saison | `humidite` locale ↑ | `MODÉRÉ × URGENCE` | sort de la stagnation sécheresse (`ok_hum`) |
| **Pailler / mulcher** (paille, BRF, feuilles, broyat) | planif. | `om_fresh` ↑, `humidite` retenue, `temperature` tamponnée | `MODÉRÉ` | atténue gel/grêle (déjà lu par `weather.py`), freine l'évaporation, nourrit le sol en se décomposant |
| **Amender** (compost, fumier) | planif. | `fertilite` / OM ↑ | `MODÉRÉ` | uptake facilité → vigueur dérivée ↑ |
| **Poser une structure** (voile d'hivernage, brise-vent, **tuteur**) | planif. | tampon météo local persistant | `MODÉRÉ` | abaisse l'exposition gel/vent ; le **tuteur** débloque la résistance à la **verse** (gène `hauteur`, déjà « prêt côté gène ») |
| **Multiplier végétativement** (bouture / division / marcottage) | planif. | introduit un **clone** (gènes = parent) à `x_cm,y_cm` ; léger prélèvement sur le pied mère | `FAIBLE` | reprise → individu génétiquement identique (canal de création sans brassage, cf. D22) |
| **Drainer** / évacuer l'excès d'eau | planif. (saison si urgence) | `humidite` ↓ | `MODÉRÉ` | soulage l'asphyxie racinaire (sols gorgés, climat océanique) |
| **Inoculer le sol** (compost vivant, thé de compost, mycorhizes) | planif. | `microbiome` ↑ | `MODÉRÉ` | uptake & régulation facilités (cf. chantier C — réseau mycorhizien) |
| **Favoriser un auxiliaire** (hôtel à insectes, nichoir, point d'eau, bande fleurie) | planif. | habitat → futur **champ auxiliaire** ↑ | `MODÉRÉ` | régulation des nuisibles **émergente** — le pendant vertueux d'« écraser » (cf. D27, champ auxiliaire dédié) |
| **Grelinette** (ameublir **sans retourner**) | planif. | décompacte, **microbiome préservé** | `MODÉRÉ` | aération + infiltration ↑, structure et biologie intactes |
| **Biner / bêcher** (retourner la terre) | planif. | aération courte **mais `microbiome` ↓** | `FAIBLE` | « fausse bonne idée » : effet immédiat, **dette biologique différée** (philo #1/#6) |

> Toutes ces actions sont des **données d'entrée** du tick déterministe : elles
> changent l'état initial d'un champ, jamais la trajectoire par un aléa (cf. §5).

**Le couple biner / grelinette — pédagogie par l'outil.** Même but (décompacter),
conséquences opposées : le **bêchage** retourne les horizons et **casse le
microbiome** (effet immédiat, dette biologique), la **grelinette** ameublit *sans
inverser* et **préserve la vie du sol** (principe no-dig de la permaculture).
Aucun sermon (philo #6) : c'est la chute de `microbiome` après bêchage — donc
d'uptake, donc de vigueur dérivée des plantes — qui enseigne. Le joueur **découvre
le bon outil par la conséquence**.

**Favoriser un auxiliaire** comble un trou du catalogue : jusqu'ici seule la
mauvaise réponse au nuisible existait (« écraser », coûteuse, la pression revient).
Agir sur le **milieu** (habitat) pour que la régulation **émerge** est la réponse
permaculturelle (philo #1/#2) — le canal vertueux symétrique.

### 3.3 Actions directes sur le vivant — coûteuses par conception (philo #1)

| Action | Coût | Gain | Effet écologique |
|---|---|---|---|
| **Manger** un organe (feuille/fleur/fruit) | `NUL` | **`+` ∝ maturité organe** | organe détruit ; cf. D19 |
| **Récolter** un organe / plante mûr | `HARVEST_VIGUEUR_COST` (`FAIBLE`) | **`+` ∝ maturité**, → banque-joueur | organe prélevé (`harvested=True`, le Qi part vers le joueur, §4) ; plante vivante |
| **Déraciner** une plante vivante | `ÉLEVÉ` | aucun | mort → nécromasse au sol (`harvested=False`, §4) |
| **Écraser** un nuisible | `MODÉRÉ × URGENCE` | aucun | suppression locale ; **la pression revient** tant que le milieu ne régule pas |
| **Tailler / éclaircir** (couper apex ou branche) | `MODÉRÉ` | `+` faible si organe mûr récupéré | réduit l'empreinte (hauteur / `foliage_density` / canopée) → **effet lumière immédiat** ; réponse architecturale riche = sprint auxine (**D29**, ci-dessous) |

- **Manger / récolter du mûr = net positif** (gain ≫ coût du geste) : le canal de
  ressourcement légitime.
- **Déraciner / écraser = net négatif sec.** Pas de punition scriptée (philo #6) :
  ce qui enseigne, c'est (a) l'**épuisement de Vigueur** qui rend la solution
  facile non soutenable et (b) le **retour de la pression écologique** (le
  nuisible revient si la régulation par auxiliaires/biodiversité n'est pas
  installée). L'écosystème répond ; le jeu ne sermonne pas.
- **Tailler = action sur le vivant, mais formatrice, pas destructrice.** À la
  différence de déraciner/écraser, c'est un **geste de jardinier qualifié** :
  coûteux (intervention directe, philo #1) mais légitime et **productif**. Sa
  vraie richesse — couper l'apex lève la **dominance apicale**, l'**auxine**
  redistribue, les bourgeons latéraux débourrent → ramification, port buissonnant,
  mise à fruit — est une **modélisation hormonale à part entière** (dominance
  apicale, rebourgeonnement, redirection de croissance). **Différée à un sprint
  dédié (D29 « auxine / dominance apicale »).** En v1, `tailler` se contente de
  l'**effet géométrique immédiat** (réduction d'empreinte → lumière), sans la
  réponse architecturale ; le hook reste en place pour que D29 s'y branche.

### 3.4 Actions de ressourcement et de connaissance

| Action | Coût | Rôle |
|---|---|---|
| **Méditer au foyer** (maison normande) | `+` (source dédiée) | recharge de Vigueur, point de ressourcement (§2.2) |
| **Observer** (cliquer pour examiner, consulter encyclopédie/carnet) | `NUL` | le canal **gratuit** de la méthode scientifique (observer → hypothèse → test). Jamais taxé : comprendre ne coûte rien. |

### 3.5 `HARVEST_VIGUEUR_COST` devient réel

Le hook (aujourd'hui `0`) devient le **paramètre du geste de prélèvement** de la
récolte sélective. **L'activer ne re-fige PAS le golden** (le golden ne récolte
jamais — cf. §5).

### 3.6 Points encore ouverts (à trancher avant impl.)

- **Multiplicateur d'urgence** : valeur exacte et liste des actions « saison »
  vs « planification » à figer au calibrage.
- **Granularité du gain « manger »** : par organe (feuille/fleur/fruit distincts)
  ou par plante entière — dépend du modèle d'organes de **D19**.
- **Champ « structure / compaction du sol »** (dette **D30**) : le **malus** du
  bêchage s'attache au `microbiome` existant, mais le **bonus** de la grelinette
  (aération, infiltration) n'a aujourd'hui **aucun champ support**. Soit on
  l'approxime via `humidite` (meilleure infiltration), soit on introduit un petit
  champ `structure_sol` — à trancher avant impl. des actions de sol.
- **Bouture = cas dégénéré de `reproduction.py`** : enfant à gènes copiés
  (aucun brassage, aucune mutation) au lieu de l'appariement biparental — à câbler
  côté **D22** lors de l'implémentation.

> **Tailler** est acquis comme action de v1 (effet géométrique immédiat). Sa
> profondeur botanique — réponse hormonale à la coupe — est portée par la dette
> **D29 (auxine / dominance apicale)**, un sprint dédié.

---

## 4. Qi territorial — formalisation des flux existants

Le « Qi territorial » de CLAUDE.md = les champs écologiques déjà là
(`fertilite`, `microbiome`, `soil_memory`, `om_*`). La Vigueur **n'ajoute aucun
flux nouveau** ; elle **nomme** les flux existants :

- **Puiser** = l'uptake racinaire (`_apply_uptake`) qui consomme `fertilite` sous
  l'empreinte racinaire. `qi_local(p)` de §1 lit ce même voisinage.
- **Retourner à la mort** = la nécromasse (`add_necromass(..., harvested=False)`)
  qui réinjecte de l'OM ∝ hauteur au sol. Le flag `harvested` distingue déjà :
  - `harvested=False` → mort naturelle / déracinage : **le Qi retourne au sol**.
  - `harvested=True` → récolte/manger joueur : **le Qi part vers le joueur** (sa
    Vigueur), il ne revient pas au sol.

C'est exactement la boucle « la Vigueur se puise dans le territoire et y retourne
à la mort » — déjà bouclée, il suffit de la documenter et de brancher le versant
joueur sur le flag `harvested`.

---

## 5. Déterminisme & golden — la propriété clé

Le golden (`tests/test_golden.py`) est une **succession spontanée pure : aucune
action joueur, aucune récolte, aucun déracinage**. Donc :

- Rendre `HARVEST_VIGUEUR_COST` réel, ajouter manger/déracinage/écraser, ajouter
  la régen passive joueur, la façade `vigueur_plante` (read-only) →
  **n'altèrent aucune trajectoire du golden**.
- Le golden **ne devra PAS être re-figé** par le sprint d'implémentation Vigueur
  (contraste avec le sprint gènes du vecteur, qui modifiait des voies écologiques
  réelles). Si un hash bouge, c'est un **bug** : quelque chose a fui dans le tick
  écologique.
- Un **golden joueur** distinct (séquence d'actions scriptée → trajectoire de
  Vigueur attendue) pourra être ajouté pour tester la couche gameplay, sans
  toucher au golden écologique.

---

## 6. Recâblage du gène `vigueur` provisoire (D22b)

Le gène `vigueur` est aujourd'hui un multiplicateur de fitness au sens
**PROVISOIRE** (accélère stade + heal). La décision **façade** (§1) le
**conserve tel quel** : il reste le modulateur génétique, désormais **enveloppé**
par `vigueur_plante()`. Pas de recâblage destructeur, pas de re-figeage du
golden. Le gène gagne juste une **lecture unifiée** au-dessus de lui. La dette
D22b passe ainsi de « sens provisoire à recâbler » à « sens stabilisé par la
façade ».

---

## 7. Interfaces avec les autres dettes

- **D12 (paliers de maîtrise)** — fournit `palier_bonus(player)` (stub `1.0`
  d'ici là). Aucune autre dépendance.
- **D19 (action manger)** — fournit le modèle d'organes consommables ; ce doc
  fixe la comptabilité Vigueur du gain (∝ maturité). À concevoir/implémenter en
  tandem ou juste après.
- **D13 (magazine de botanique)** — consomme Vigueur joueur + maîtrise pour
  débloquer des espèces ; se branche sur `game_state["vigueur"]`.
- **D24 (portage C#)** — la couche Vigueur joueur se logera dans `GameManager`
  (le `game_state` dict a déjà son analogue prévu). Façade plante = méthode
  read-only sur l'instance C#.
- **D29 (auxine / dominance apicale)** — sprint dédié, surfacé ici via l'action
  `tailler` (§3.3). Modélise la réponse hormonale à la coupe : levée de dominance
  apicale, débourrement latéral, ramification, redirection de croissance. La v1
  de `tailler` n'expose que l'effet géométrique ; D29 branche la réponse riche.

---

## 8. Périmètre proposé pour le sprint d'implémentation (à venir)

Sprint **moyen**, découpable en sous-sprints autosuffisants, **golden écologique
préservé sans re-figeage** :

1. **Couche Vigueur joueur** : état `game_state["vigueur"]`, cycle (régen passive
   sur la tranche joueur, plein à la saison), interface `vigueur_max` /
   `regen_rate` + stub `palier_bonus`. Golden écolo inchangé. Golden joueur créé.
2. **Coûts d'action** : activer `HARVEST_VIGUEUR_COST`, brancher déracinage /
   écraser nuisible sur la dépense, brancher le flag `harvested` côté gain joueur.
3. **Façade `vigueur_plante`** (read-only) + exposition au carnet/encyclopédie
   (lecture diégétique). Aucun pilotage de simulation.
4. **(optionnel, tandem D19)** action « manger » : organes consommables → gain
   Vigueur ∝ maturité.

**Hors périmètre (gated) :** contenu réel des paliers (D12), magazine (D13),
structures de préparation météo (sprites/gameplay Godot), portage C# (D24).
