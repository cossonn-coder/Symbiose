# Conception — Hormones de croissance : auxine & dominance apicale (SYMBIOSE)

> ⚠️ **REFONDU (2026-06-05) — ce document est ARCHIVÉ.** Son modèle « 2 scalaires
> hormonaux, repos neutre » a été **abandonné** au Sprint conception Croissance
> procédurale : l'auxine devient un **niveau le long d'une structure morphologique
> réelle** (segments), pilotée en moteur **permanent**, avec rendu pixel procédural.
> **Source de vérité actuelle : [`CONCEPTION_CROISSANCE.md`](CONCEPTION_CROISSANCE.md).**
> On conserve ce fichier pour l'historique (biologie §A toujours valable, action
> `tailler` absorbée comme appelant du seam §F du nouveau doc). Ne plus l'implémenter
> tel quel.

> **Document de conception. Aucun code écrit.** Spec de référence pour le futur
> sprint d'implémentation Python de la réponse hormonale à la taille (dette
> **D29**), qui devra préserver `tests/test_golden.py`.
>
> Issu du **Sprint conception Hormones** (2026-06-04). Surface l'action `tailler`
> déjà décrite dans `CONCEPTION_VIGUEUR.md` §3.3 (effet géométrique v1) et lui
> ajoute la **réponse architecturale émergente** (débourrement, ramification,
> mise à fruit). Décisions actées avec Nico : **modèle scalaire émergent** (pas de
> topologie de branches), **2 scalaires hormonaux**, **démonstrateur tomate +
> pommier**.

---

## A. La biologie, rédigée pour toi (à étudier, pas à trancher)

*Ton « naturaliste qui observe ». Tu es ingénieur, expert simulation — la botanique
est hors de ton domaine, donc je te pose le terrain ; tu n'as rien à trancher ici.*

### A.1 L'auxine et la dominance apicale

Une plante qui pousse en hauteur a, tout en haut de sa tige, un **bourgeon
apical** (l'« apex », le point de croissance terminal). Ce bourgeon fabrique une
hormone, l'**auxine**, qui **descend** le long de la tige. En chemin, l'auxine
**inhibe** les **bourgeons axillaires** (les bourgeons latéraux, nichés à
l'aisselle de chaque feuille). Tant que l'apex est là et produit son auxine, les
latéraux restent **dormants** : ils existent mais ne se développent pas.

C'est la **dominance apicale** : l'apex « commande », la plante mise tout sur sa
flèche verticale et garde ses bourgeons latéraux en réserve.

```
   AVANT TAILLE (dominance apicale forte)
   ───────────────────────────────────────
            ▲ apex actif  ── produit l'AUXINE
            │
            │   l'auxine descend et INHIBE ↓
            ●  ← bourgeon latéral dormant (inhibé)
            │
            ●  ← bourgeon latéral dormant (inhibé)
            │
          ──┴──  la plante pousse droit, peu ramifiée
```

### A.2 La levée de dominance : couper l'apex

Quand on **coupe l'apex** (la taille, l'écimage, le pincement), la source
d'auxine disparaît. L'inhibition se lève. En quelques jours à quelques semaines,
les bourgeons latéraux **débourrent** (ils sortent de dormance et démarrent leur
croissance — le « débourrement »). La plante, privée de sa flèche, **redirige sa
croissance** vers les côtés : elle **ramifie**, devient **buissonnante**.

```
   APRÈS TAILLE (dominance apicale levée)
   ───────────────────────────────────────
            ✂  apex coupé  ── plus d'auxine
            ╳
            │
        ●──►●  ← le latéral DÉBOURRE (croissance)
            │
        ●──►●  ← le latéral DÉBOURRE (croissance)
            │
          ──┴──  port buissonnant, ramifié, plus large et plus bas
```

À terme, l'un des nouveaux rameaux prend le dessus et **rétablit** une dominance
apicale (un nouveau « chef »). C'est pour ça que la réponse est **transitoire** :
l'effet hormonal de la coupe s'estompe à mesure qu'une nouvelle hiérarchie
s'installe — mais la **ramification déjà acquise**, elle, **reste**.

### A.3 Pourquoi tailler met à fruit

Chez beaucoup d'espèces, **les fleurs et les fruits ne se forment pas sur la
flèche verticale, mais sur le bois latéral** (les rameaux de l'année, les
« coursonnes » ou « lambourdes » d'un arbre fruitier). En favorisant la
ramification, la taille **multiplie les sites de fructification**. C'est tout le
principe de la **taille de fructification** : on sacrifie de la croissance
végétative verticale pour gagner du bois fructifère.

Deux cas concrets que le jeu démontrera :

- **Le gourmand de la tomate (indéterminée).** Une tomate indéterminée a une
  dominance apicale forte : laissée libre, elle file en hauteur. Les jardiniers
  pratiquent l'**écimage** (couper la tête en fin de saison pour arrêter la montée
  et pousser les fruits déjà noués à mûrir) et l'**égourmandage** (retirer les
  « gourmands », ces rameaux latéraux vigoureux). Le geste **redirige l'énergie de
  la croissance vers la mise à fruit** plutôt que vers la flèche et le feuillage.

- **La taille de fructification du pommier.** On taille pour ouvrir la charpente,
  laisser entrer la lumière, et favoriser le **bois latéral porteur de fruits**
  plutôt que les « gourmands » verticaux stériles. Un pommier bien taillé fructifie
  plus et mieux qu'un pommier abandonné qui s'épuise en hauteur. (Thème normand :
  c'est exactement la conduite d'un verger à cidre.)

### A.4 Toutes les plantes ne répondent pas pareil

Point important pour le modèle : **la réponse à la taille est spécifique**. Une
**graminée** (famille des Poaceae) ne « rebourgeonne » pas comme une tomate : son
point de croissance est **à la base** (au ras du sol — c'est pour ça que la tonte
d'une pelouse ne la tue pas), elle n'a pas de bourgeons latéraux le long d'une tige
à débourrer. Couper une graminée ne déclenche aucune ramification hormonale de ce
type. Le modèle doit donc traiter la réponse à la taille comme un **trait par
espèce**, neutre par défaut (cf. §F).

---

## B. Faisabilité topologique — point ouvert n°1, instruit ET tranché

**Question :** faut-il modéliser une vraie **topologie** (des objets « branche » et
« bourgeon » par plante) pour rendre la réponse à la taille, ou peut-on s'en tenir
à des **variables scalaires** ?

**Règle de décision posée par Nico (kickoff §B) :** topologie réelle *seulement si*
le calcul **et** la RAM **et** l'affichage peuvent suivre ; sinon repli scalaire.
On instruit les trois budgets, puis on tranche.

### B.1 Budget calcul — large, non contraignant

Référence perf (mémoire `perf_profile_simulation`) : ~177 ms/tick sur 432 plots,
**LightField = 53 % du CPU**, marge gameplay **×339**, coût ∝ taille de canopée.

Une topologie *légère* (disons quelques « charpentières » + une poignée de
bourgeons abstraits par plante × ~quelques centaines de plantes) resterait dans le
bruit : on parle de quelques milliers d'objets scalaires parcourus une fois par
tick, négligeable devant le LightField (qui échantillonne la canopée pixel par
pixel). Le **scalaire**, lui, est quasi gratuit (1-2 `float` par instance, lus dans
la boucle de croissance déjà existante). **Le calcul n'est pas le facteur
limitant** dans un cas comme dans l'autre.

### B.2 Budget RAM — non-sujet

27 Mo aujourd'hui (mémoire perf). Même une topologie légère n'ajouterait que
quelques objets par plante : sans effet sur ce budget. **Pas le facteur limitant.**

### B.3 Budget rendu — **le vrai mur**

Les plantes sont des **sprites PNG par stade** (sheets 1408×768 + PNG individuels),
pas un rendu végétal procédural. **Il n'existe aucun système de rendu de squelette,
de L-system, ni de variantes de sprite par état de ramification.** Rendre une
*vraie* ramification à l'écran demanderait de **construire ce système** — un sprint
frontend Godot dédié, explicitement **hors périmètre** (kickoff « Hors périmètre »).

Ce que l'affichage **peut** refléter **sans** nouveau système de rendu : l'**empreinte
métrique** qui pilote déjà le sprite et la lumière — `canopy_height`,
`canopy_radius`, `foliage_density`. Une tomate écimée qui **baisse en hauteur** et
**s'élargit** (canopée plus large, feuillage plus dense) est déjà exprimable via les
métriques existantes qui modulent l'échelle du sprite et l'ombre projetée. On ne voit
pas « des branches » apparaître, mais on voit la plante **changer de port** (plus
basse, plus large, plus touffue) — ce qui est exactement la lecture diégétique
attendue.

### B.4 Les trois options et la tranche

| Option | Description | Calcul | RAM | **Rendu** | Golden |
|---|---|---|---|---|---|
| **(i) topologie réelle** | objets branche/bourgeon par plante | ✅ ok | ✅ ok | ❌ **système à construire (inexistant)** | risque (état riche lu au tick) |
| **(ii) scalaire émergent** | 1-2 variables d'état hormonal par instance | ✅ trivial | ✅ ok | ✅ reflété par l'empreinte existante | ✅ neutre par défaut |
| **(iii) hybride léger** | pseudo-charpentières abstraites + variantes de sprite | ✅ ok | ✅ ok | ❌ variantes de sprite **inexistantes** | complexité de neutralité |

**Décision : option (ii) — scalaire émergent.** La règle de Nico tranche
mécaniquement : le rendu **ne peut pas** suivre (ni topologie réelle, ni variantes
de sprite n'existent), donc on **se replie sur le scalaire**. Ce n'est pas un pis-
aller : c'est cohérent avec toute l'architecture du projet — **plante = un point +
des scalaires** — et avec les deux patrons déjà éprouvés (**Vigueur = façade
read-only**, **Maîtrise = couche au-dessus du tick**). La richesse botanique vit
dans la **dynamique** (la cinétique hormonale), pas dans la géométrie d'un arbre
d'objets.

> **Porte laissée ouverte.** Le jour où un sprint frontend dotera Godot d'un rendu
> végétal (squelette/L-system/variantes), l'option (iii) hybride devient possible
> *par-dessus* le modèle scalaire (les scalaires `ramification` piloteraient le
> choix de variante). Le scalaire n'est donc pas un cul-de-sac, c'est le socle.

---

## C. Le modèle retenu — 2 scalaires hormonaux, repos strictement neutre

### C.1 L'état nouveau (sur `PlantInstance`)

Deux champs, défauts choisis pour un **repos no-op** (critère golden #1) :

```python
# (futur) sur PlantInstance — defaults = repos NEUTRE
dominance_apicale: float = 1.0   # signal hormonal TRANSITOIRE
ramification:      float = 0.0   # etat architectural CUMULATIF persistant
```

- **`dominance_apicale ∈ [0, 1]`**, défaut **1.0** = apex intact, l'auxine inhibe
  à fond les latéraux (état naturel d'une plante non taillée). Couper l'apex la fait
  **chuter vers 0**. Elle **se rétablit** ensuite vers 1.0 en N semaines (un nouveau
  leader reprend la main) → c'est la **cinétique transitoire** du débourrement.
- **`ramification ∈ [0, RAMIF_MAX]`**, défaut **0.0** = port non ramifié (la plante
  pousse selon ses stades/sa courbe d'âge habituels). Monte quand la dominance est
  levée, et **reste acquise** (mémoire architecturale) même une fois la dominance
  rétablie.

### C.2 Pourquoi DEUX scalaires et pas un (décision tranchée)

La biologie a deux temporalités distinctes (§A.2) : un **signal hormonal qui passe**
(l'auxine chute puis remonte) et une **structure qui reste** (les rameaux, une fois
sortis, ne rentrent pas). Un seul scalaire ne peut pas porter les deux : ou bien il
revient à zéro (et on perd la ramification acquise), ou bien il reste (et on perd la
cinétique de rétablissement). **`dominance_apicale` = le transitoire ; `ramification`
= le persistant.** C'est minimal (2 `float`) et fidèle.

### C.3 Repos neutre — la propriété clé (critère golden #1)

Le golden (`tests/test_golden.py`) est une **succession spontanée sans joueur** :
**personne ne taille**. Donc `dominance_apicale` reste à 1.0 et `ramification` à 0.0
pour toutes les plantes, indéfiniment. Tous les mappings du §C.4 sont écrits pour
que **`dominance_apicale = 1.0` et `ramification = 0.0` donnent ×1 / +0** sur chaque
variable de croissance → le tick lit un **no-op strict**. Golden `c950f06c…`
(engine) / `b005d9ba…` (champ) **intacts, sans re-figeage**.

> **Critère de design #1, à vérifier à chaque choc d'implémentation :** si un mapping
> impose que le tick *lise au repos* une valeur non neutre, c'est un **bug de
> design**. Le repos doit être l'identité.

### C.4 Mapping coupe → réponse émergente (sur variables EXISTANTES)

Jamais un `+=` scripté sur la plante (philo #2) : on **module** des variables que le
tick lit déjà. `f(0) = neutre` pour chacune.

| Variable existante | Modulation proposée | Au repos (`ramification=0`) | Sens biologique |
|---|---|---|---|
| `canopy_radius_at` | `× (1 + K_R · ramification)` | ×1 | la plante s'étale en buisson |
| `canopy_height` / `height_at` | `× (1 − K_H · ramification)` | ×1 | port plus bas (flèche sacrifiée) |
| `foliage_density_at` | `↑ avec ramification` (borné ≤ 1) | inchangé | feuillage dense des latéraux |
| `reproduction_rate` (effectif) | **mise à fruit** modulée par `ramification` **via un modèle** | inchangé | le bois latéral porte les fruits |
| `growth_factor` | redirection : la croissance verticale bloquée alimente la ramification | inchangé | l'énergie change de destination |

**Cinétique (le cœur dynamique) :**

1. **Coupe de l'apex** → `dominance_apicale` chute (vers 0).
2. Chaque tick, tant que `dominance_apicale < 1` : un **potentiel de débourrement**
   `p = 1 − dominance_apicale` alimente la montée de `ramification`
   (`ramification += DEBOURR_RATE · p`, plafonné à `RAMIF_MAX`).
3. En parallèle, `dominance_apicale` **se rétablit** vers 1.0
   (`dominance_apicale += DOMINANCE_RECOVERY · (1 − dominance_apicale)`) — sur N
   semaines, un nouveau leader reprend la main, le débourrement s'arrête.
4. `ramification` **reste** à sa valeur acquise (persistante).

**Déterminisme (philo #3) :** aucune des étapes n'utilise de RNG. Si une variabilité
du débourrement est souhaitée (toutes les plantes ne réagissent pas identiquement),
elle passe par **`_hash_noise`** (position + seed), comme tout le reste du moteur —
même seed + mêmes gestes → même réponse.

**Bornes anti-emballement :** `dominance_apicale` clampée `[0, 1]`, `ramification`
clampée `[0, RAMIF_MAX]`. Tailler dix fois ne fait pas un buisson infini : la
ramification sature, et chaque coupe coûte de la Vigueur (§E) — l'usure de la
solution facile s'applique aussi au bon geste répété sans raison.

---

## D. L'action `tailler`

Place : `sim/actions.py`, sur le modèle exact des **6 gestes existants** (lecture du
coût via `cout_action`, dépense via `spend`, mutation **au-dessus** du tick, jamais
de RNG). C'est une **action directe sur le vivant** (philo #1 : permise mais
coûteuse) dont la **réponse est émergente** (philo #2 : on écrit l'état hormonal, le
tick produit l'architecture).

### D.1 Deux gestes

- **Couper l'apex** (écimage / pincement / étêtage) — `dominance_apicale → 0`.
  Déclenche le débourrement (§C.4). **Hook géométrique immédiat** (la « v1 » jamais
  codée de §3.3) : `canopy_height` réduite tout de suite → **lumière livrée aux
  strates basses** dès le tick suivant. C'est l'effet déjà acquis de `tailler` v1 ;
  la réponse hormonale se **branche par-dessus**, on ne jette rien.
- **Couper une branche** (éclaircir / supprimer un gourmand) — réduit l'empreinte
  **locale** (canopée/`foliage_density`), effet hormonal **moindre** (la dominance
  apicale est peu affectée si l'apex reste). Sert surtout à ouvrir la lumière et,
  sur la tomate, à l'égourmandage (rediriger vers le fruit).

### D.2 Ce que le geste écrit

```python
# esquisse — PAS du code livré, juste le contrat
def tailler(game_state, player, plant, eco, *, cible="apex") -> bool:
    cost = cout_action(game_state, player, "tailler", _objets_action("tailler", plant))
    if spend(game_state, player, cost) < 1.0:
        return False                     # binaire : tout-ou-rien (cf. deraciner)
    if not _repond_a_la_taille(plant):   # trait espece (§F) — defaut insensible
        # hook geometrique seulement (reduction d'empreinte), pas de reponse hormonale
        ...
        return True
    if cible == "apex":
        plant.dominance_apicale = 0.0    # leve la dominance -> debourrement
        # hook geometrique immediat : empreinte reduite (deja v1)
    else:  # cible == "branche"
        ...                              # reduction locale, dominance ~inchangee
    # gain Vigueur faible si organe mur recupere a la coupe (cf. §E)
    return True
```

- **Coût `MODÉRÉ`** (table `COUTS`, cf. §E). Action **binaire** tout-ou-rien comme
  `deraciner`/`ecraser` : si la Vigueur ne couvre pas le coût, rien n'est écrit (on
  ne taille pas « à moitié »).
- **Objets touchés** : `("taille", "sécateur")` + la **cible vivante** (clé d'espèce,
  via `_objets_action`) — déjà prévus par la taxonomie maîtrise (§10.3/§10.4).
- **Repos golden inchangé** : `tailler` n'est **jamais appelée** par le golden (pas
  de joueur) → aucun état hormonal ne bouge dans le tick déterministe.

---

## E. Liens Vigueur + Maîtrise

### E.1 Vigueur

- **Coût** : `tailler` rejoint la table `COUTS` de `actions.py` à `MODÉRÉ` (déjà
  acté `CONCEPTION_VIGUEUR.md` §3.3). Passe par le seam `cout_action` →
  atténuable par la maîtrise comme les autres gestes.
- **Gain** : `+` faible **si un organe mûr est récupéré à la coupe** (couper une
  branche portant un fruit mûr) — même logique que `recolter`/`manger` (∝ maturité
  de l'organe). Nul si on coupe du bois vert. Net : tailler reste **coûteux** (c'est
  une intervention directe), formateur mais pas gratuit.

### E.2 Maîtrise

`tailler` est une **« technique »** au sens de la taxonomie de maîtrise — « taille »
est explicitement déclarée objet de maîtrise (`CONCEPTION_MAITRISE.md` §10.3).

**Détection de succès (patron §9.5 : « action payée ET effet visé observé = 1
preuve »).** Branchement futur dans `sim/maitrise_detection.py` (i4), **sans le
coder ici** :

- Le module lit déjà des **marqueurs** post-tick (`🌱/⏸/🌑/❄/🌰`) et une **fenêtre
  d'imputation** geste → amélioration. La taille y ajoute son **effet visé observé** :
  un **débourrement** (montée de `ramification` au-dessus d'un seuil) et/ou une
  **mise à fruit** consécutive, **imputés au geste `tailler`** s'ils tombent dans la
  fenêtre d'imputation après la coupe.
- Proposition de **nouveau marqueur** : `🌿` (débourrement). Le détecteur le lit comme
  les autres, sous **gate d'observation** (palier ≥ 1) et **nature croissante**
  (§9.2). 1 preuve = `tailler` payée **et** `🌿`/mise à fruit observé dans la fenêtre.
- `maitrise_detection.py` reste **pur au sens golden** (il lit l'état post-tick, ne
  fait jamais avancer le tick) ; `actions.py` n'importe pas la détection (sens de
  dépendance acté i4).

---

## F. Démonstrateur — trait `reponse_taille` par espèce

**Nouveau trait sur `PlantBase`**, **défaut `insensible` = strictement neutre**
(golden-safe : une espèce non démontrée ignore la coupe au-delà du hook géométrique).

```python
# (futur) sur PlantBase
reponse_taille: str = "insensible"   # defaut : pas de reponse hormonale
```

| Espèce | `reponse_taille` | Comportement |
|---|---|---|
| **Tomate** (`Tomato`, Solanaceae, annuelle) | `"buissonnante"` | forte dominance apicale ; écimage → arrêt de la montée + **mise à fruit** ↑, hauteur ↓ ; égourmandage (couper-branche) → redirige vers le fruit |
| **Pommier** (`AppleTree`, Rosaceae, ligneux) | `"fructification_laterale"` | **taille de fructification** : la coupe favorise le **bois latéral porteur de fruits** → `reproduction_rate` effectif ↑ via `ramification`, port ouvert |
| **toutes les autres** (dont graminées) | `"insensible"` (défaut) | aucune réponse hormonale ; une graminée a son méristème à la base, elle ne rebourgeonne pas ainsi (§A.4) |

**Choix du fruitier : pommier** (et non figuier) — justifié par le **thème normand**
(verger à cidre) et par le fait que la **taille de fructification du pommier** est
l'exemple canonique en zone tempérée. Le `AppleTree` est déjà au catalogue
(`perennials.py`, `maturity_years=5`, `age_curve` définie). Le figuier
(`reponse_taille="buissonnante"`) reste un candidat trivial à ajouter plus tard.

**Généralisation :** `reponse_taille` est une **chaîne d'archétype** (comme
`life_cycle`, `winter_strategy`, `archetype`). Ajouter une espèce répondante = lui
donner l'archétype voulu + d'éventuels overrides de coefficients. Le reste du
catalogue migrera espèce par espèce au calibrage, sans toucher au modèle.

---

## G. Points ouverts → calibrage post-test (placeholders nommés)

Aucun « bon chiffre » ici : on **nomme** les boutons, on les règle jeu en main.

| Placeholder | Rôle | Calibrage |
|---|---|---|
| `DEBOURR_RATE` | vitesse de montée de `ramification` (cinétique du débourrement, N semaines) | post-test |
| `DOMINANCE_RECOVERY` | vitesse de rétablissement de `dominance_apicale` vers 1.0 | post-test |
| `RAMIF_MAX` | plafond de `ramification` (anti-emballement) | post-test |
| `K_R` | gain `canopy_radius` par unité de ramification (étalement) | post-test |
| `K_H` | baisse `canopy_height` par unité de ramification (port abaissé) | post-test |
| seuil mise à fruit | niveau de `ramification` au-delà duquel `reproduction_rate` effectif monte | post-test |
| coût exact de `tailler` | base `MODÉRÉ` (déjà), valeur fine | post-test (D12.4 / calibrage Vigueur) |
| seuil marqueur `🌿` | niveau de débourrement qui déclenche le marqueur observable (succès maîtrise) | post-test |

---

## H. Interfaces avec les autres dettes

- **D11 (Vigueur)** — `tailler` consomme le seam `cout_action`/`spend` et le gain ∝
  maturité ; rien de neuf côté Vigueur, juste une ligne de plus dans `COUTS`.
- **D12 (Maîtrise)** — `tailler` = technique (§10.3) ; succès détecté par
  `maitrise_detection.py` (marqueur `🌿`, patron §9.5). Coût atténuable via le seam.
- **D19 (organes fins)** — la valeur exacte de l'organe récupéré à la coupe
  (feuille/fleur/fruit distincts) relève de D19 ; ici on ne fixe que la
  comptabilité ∝ maturité. **Ne pas rouvrir D19 dans l'impl. hormones.**
- **D24 (portage C#)** — les 2 scalaires se logeront sur l'instance C#
  (`PlantInstance`), le geste dans le système d'actions, le mapping dans la boucle
  de croissance. Patron façade/scalaire trivial à porter.
- **Modèle d'organes / bouture / rendu végétal procédural** — **hors périmètre**
  (D19 / D22 / sprint frontend dédié), cf. §B.3.

---

## I. Périmètre proposé pour le sprint d'implémentation (à venir)

Sprint **moyen**, **golden écologique préservé sans re-figeage** :

1. **État hormonal** : 2 champs sur `PlantInstance` (defaults neutres) + trait
   `reponse_taille` sur `PlantBase` (défaut `insensible`). Golden **intact**
   (personne ne taille). Test de neutralité au repos.
2. **Cinétique** : la boucle de croissance (`engine._tick_*`) lit les 2 scalaires et
   applique le mapping §C.4 ; au repos = identité (vérifié golden). Débourrement +
   rétablissement + bornes.
3. **Action `tailler`** dans `actions.py` (apex/branche), entrée dans `COUTS` +
   `OBJETS_TOUCHES`, hook géométrique conservé, gain ∝ maturité. Golden joueur dédié
   (séquence taille → trajectoire `ramification`/mise à fruit attendue).
4. **Démonstrateur** : `reponse_taille` sur `Tomato` + `AppleTree`.
5. **(plus tard)** branchement du marqueur `🌿` dans `maitrise_detection.py`
   (succès §9.5) + généralisation du trait au reste du catalogue.

**Hors périmètre (gated) :** rendu végétal procédural Godot, organes fins (D19),
bouture (D22), portage C# (D24).
