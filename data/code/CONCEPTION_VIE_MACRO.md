# Conception — Vie macroscopique observable (SYMBIOSE)

> **Document de conception. Aucun code moteur écrit.** Spec de référence pour le
> futur sprint d'implémentation de la vie macroscopique (auxiliaires, ravageurs,
> pollinisateurs, vers de terre), qui sera découpé en sous-sprints D31.x et devra
> gérer le re-figeage du golden (cf. §1 et §8).
>
> Issu du **Sprint conception Vie macroscopique** (2026-06-04). Couvre la dette
> **D31**. Recoupe **D27** (« champ auxiliaire dédié = sprint futur »), **D30**
> (structure/aération du sol), **D19** (action manger), **D32** (perf — pourquoi
> un champ et pas des agents). S'appuie sur le patron de
> `CONCEPTION_VIGUEUR.md` §1 (façade Vigueur read-only) avec un `qi_local`
> **trophique** au lieu du sol racinaire.

---

## 0. Le constat de départ

Le moteur ne modélise aujourd'hui **aucune entité vivante macroscopique à
vitalité propre**. Il n'a que des **flux abstraits** :

| Ce qui existe | Où | Limite |
|---|---|---|
| `herbivory_pressure` — scalaire recalculé chaque tick | `sim/effects.py:451` | « pas de ravageur visible », sans mémoire |
| terme `predator` reconstruit de proxies (biodiv, rondelles, stabilité) | `sim/effects.py:487` | aucun état, aucun décalage temporel |
| `ALEAS_RAVAGEURS` (Pucerons, Limaces, Doryphores, Chenilles…) | `sim/engine.py:105` | **événements narratifs** début de saison, pas des populations |
| rondelles `auxiliaire` / `pollinisateur` | `world/tile.py:16` | termes **instantanés** (régulation, `pollinator_reach`) |

**L'intention de Nico** (gravée en mémoire `project_vie_macroscopique`) : son
plaisir central est de **se balader dans le jardin et de voir la vie s'organiser**
— auxiliaires, pollinisateurs, nuisibles qui **apparaissent, croissent, déclinent
en nombre et en activité**. Le mot d'ordre : *« si ce n'est qu'un champ
mathématique, je n'apprendrai rien. »* L'apprentissage doit être **visuel AVANT**
d'être lisible sur la santé des plantes.

**Modèle technique TRANCHÉ le 2026-06-04** (après le profilage de perf, cf.
`perf_profile_simulation` + D32) = **hybride** :
- **Dynamique** = des **`GridField` déterministes persistants** (densité par
  guilde), bornés aux 432 plots, ~gratuits (le profilage montre que la couche
  biotique pèse ~13 % du CPU et que la mémoire n'est pas un sujet ; un champ est
  gratuit là où des agents coûteraient ∝ population).
- **Perception** = sprites **échantillonnés depuis le champ**, population
  **bornée + marge**.

Ça préserve à la fois l'**exigence visuelle** (les sprites reflètent la densité
réelle → on apprend en regardant) et le **déterminisme** (philo #3).

---

## 1. La décision structurante : la dynamique vit DANS le tick (golden re-figé)

**Décision actée avec Nico (2026-06-04).** Les champs de densité **nourrissent la
simulation écologique** : l'herbivorie, la prédation, la pollinisation et
l'aération du sol **lisent les champs persistants** et remplacent la
reconstruction `predator` de proxies. Ils ne sont **pas** une couche décorative
au-dessus du tick.

**Pourquoi (le piège du découplage).** Si les champs ne servaient qu'à dessiner
des sprites pendant que la santé restait pilotée par l'ancien scalaire
`herbivory_pressure` recalculé séparément, **ce qu'on voit et ce qui mord les
plantes seraient deux vérités distinctes**. On pourrait voir trois pucerons et
perdre une plante, ou voir une nuée sans dégât. La **boucle d'apprentissage** —
*je vois les ravageurs → mes plantes souffrent → j'installe de l'habitat → les
auxiliaires arrivent → les ravageurs refluent → mes plantes récupèrent* — ne se
referme **que si le champ qui dessine est le champ qui agit**. C'est le cœur de
l'intention de Nico. Le découplage la casserait et créerait une dérive
visuel↔santé.

**Conséquence sur le golden.** Câbler les champs dans l'herbivorie/prédation
modifie des **trajectoires écologiques réelles** → le golden
(`tests/test_golden.py`) **sera re-figé**, exactement comme au sprint météo (qui
a câblé `temperature` → santé). C'est **une** re-figeage, propre, déjà éprouvé,
**journalisé**. Ce qui re-fige : le câblage santé/services (§8, D31.2). Ce qui ne
re-fige PAS : les sprites (pure lecture, §3) et les gestes joueur (event-driven,
§5) — comme la Vigueur.

> **Contraste avec `CONCEPTION_VIGUEUR.md`.** La Vigueur joueur ne re-figeait
> jamais le golden (couche gameplay au-dessus du tick). Ici, c'est l'inverse
> assumé : la vie macroscopique **est** de l'écologie, elle entre dans le tick
> déterministe. Seules les façades Vigueur de ces entités (§4) restent des
> lectures au-dessus.

---

## 2. Le modèle : un champ de population générique, instancié 4 fois

### 2.1 Le pivot — une seule abstraction trophique

Décision actée avec Nico : **pas** quatre dynamiques bricolées au cas par cas,
mais **un mécanisme générique** paramétré par **(ressource trophique, prédateurs,
habitat)**, instancié une fois par guilde. Même esprit data-driven que l'objet de
maîtrise générique de D12.3 (`CONCEPTION_MAITRISE.md`). Chaque guilde est
**attirée dans son milieu par la ressource dont elle se nourrit**.

Chaque tick, intégration avec inertie (patron `DisturbanceField`,
`fields/grids.py:97` — `champ' = champ·inertie + flux·(1−inertie)`), bornée
`[0, max]` :

```
PopulationField(nom, ressource, prédateurs, habitat) :
    naissance ∝ ressource_locale (= qi_local trophique) + habitat (plancher) + chaleur
    mort      ∝ prédation (Σ champs prédateurs locaux) + hiver(froid) + disturbance + famine
    champ'[r,c] = clamp( champ[r,c]·INERTIE + (naissance − mort)·(1−INERTIE),  0, MAX )
```

L'**inertie** est le moteur de la pédagogie : elle introduit un **décalage
temporel** entre une guilde et sa proie. Les ravageurs montent **d'abord**, les
auxiliaires rattrapent **avec retard**, les ravageurs s'effondrent → **cycles
boom-bust visibles** (la dynamique proie-prédateur classique, tempérée et
déterministe). C'est ce qui rend l'observation gratifiante (observer → hypothèse
→ test, philo #6).

### 2.2 Les quatre instances et leur chaîne trophique

| Champ | Ressource (= `qi_local`) | Prédateurs (puits biotique) | Habitat / plancher | Service rendu à la sim |
|---|---|---|---|---|
| **ravageur** | feuillage des plantes (biomasse-hôte locale) | **auxiliaire** | chaleur, **monoculture** (faible biodiversité) | mange les plantes → **herbivorie** |
| **auxiliaire** | **ravageur** (proie animale) | — (oiseaux : abstrait, futur) | nectar + rondelle `auxiliaire`, **stabilité** (faible `disturbance`) | régule le ravageur → **prédation** |
| **pollinisateur** | **fleurs en floraison** (nectar/pollen des plantes) | — | rondelle `pollinisateur` | élargit **`pollinator_reach`** (reproduction) |
| **vers_de_terre** | **microbiome + OM** (matière en décomposition, part fongique) | — | sol **non perturbé** | aération/structure (**D30**) + enrichissement |

Notes :
- Le **« champignon »** cité par Nico = la part fongique de la ressource des vers
  (microbiome/OM), **pas** un 5ᵉ champ. Si une guilde fongique propre devient
  utile (la rondelle `maladie` existe déjà, `world/tile.py:16`), ce sera une
  **5ᵉ instance** du même mécanisme — l'abstraction est extensible sans
  refactor.
- Les **rondelles** `auxiliaire`/`pollinisateur` cessent d'être des termes
  instantanés : elles deviennent des **termes-source d'habitat/nectar** des
  champs (plancher persistant — cf. §5, « favoriser un auxiliaire »).
- Le terme `predator` reconstruit de proxies (`effects.py:487`) **disparaît** :
  la prédation devient la lecture du champ `auxiliaire` local.
- Les **prédateurs des auxiliaires/pollinisateurs/vers** (oiseaux) sont laissés
  vides au départ — sommet de chaîne abstrait, à ouvrir plus tard si besoin.

### 2.3 Persistance — oui, c'est le changement clé

Les champs **persistent** (mémoire/inertie), à la différence du scalaire
`herbivory_pressure` recalculé sans mémoire aujourd'hui. La persistance apporte :
1. les **cycles temporels** et le **décalage** proie-prédateur (la pédagogie) ;
2. un substrat **stable** que les sprites échantillonnent sans téléporter à
   chaque tick (§3) ;
3. la **cohérence vu↔agi** (§1).

Coût : 4 `GridField` de 432 plots + une intégration/tick. Négligeable (le
profilage donne ×339 de marge gameplay ; la couche biotique est à ~13 % du CPU,
dominée par le LightField à ~53 %, cf. D32).

---

## 3. Perception : la règle d'échantillonnage sprite ← densité

La moitié « perception » de l'hybride. Déterministe, bornée, golden-neutre.

- **Nombre** de sprites dans un plot = `floor(densité / DENSITÉ_PAR_SPRITE)`,
  plafonné à `SPRITES_PAR_PLOT_MAX` (~3-4), avec un **cap global + marge**. Un
  sprite = **un quantum de densité**. Quand le champ monte, les sprites
  **apparaissent un à un** (naissance lisible) ; quand il baisse, ils
  **disparaissent** (déclin lisible).
- **Position** de chaque sprite dans le plot =
  `_hash_noise(seed, r, c, slot_index)` — **indépendant de la semaine**
  (`fields/noise.py:16`). Un slot occupe **toujours le même point** ; il bascule
  seulement visible/caché quand la densité franchit son seuil. On lit « le 3ᵉ
  insecte est apparu **ici** » — pas de téléportation tick-à-tick.
- **Activité** (le « *en nombre **et en activité*** » de l'intention) = un scalaire
  `activite(r,c)` exposé par le champ (p.ex. ressource disponible) qui pilote la
  **vitesse d'animation / le rayon d'errance** côté Godot. **Pur rendu**, zéro
  impact sim. Une population vigoureuse fourmille ; une population qui décline
  s'engourdit.
- **Cap + marge** : au-delà du cap, les sprites **saturent** (on voit
  « beaucoup ») mais le champ garde le **vrai** nombre. Le coût de rendu est donc
  **borné** quoi qu'il arrive — c'est le seul point que le profilage signalait
  comme potentiellement hors budget si des agents se reproduisaient sans borne.

**Déterminisme & golden.** La présence d'un sprite est une **fonction pure**
(densité du champ, seed, position) — aucun spawn par RNG vivant, aucun feedback
vers la sim. Les sprites **lisent** le champ ; ils ne le modifient pas. Donc
**golden-neutres** par construction (ils n'apparaissent pas dans
`tests/test_golden.py`, qui n'a pas de rendu). Implémentables en D31.1 sans
re-figeage.

---

## 4. Façades `vigueur_*` — lecture diégétique, jamais pilote

Patron `CONCEPTION_VIGUEUR.md` §1 : **fonctions pures read-only, aucun état
stocké, aucun budget énergétique à équilibrer**. Différence assumée avec les
plantes : le `qi_local` n'est **pas** le sol racinaire mais la **ressource
trophique** de la guilde — c'est exactement la `ressource` du champ générique
(§2), donc rien à dupliquer.

```python
def vigueur_nuisible(r, c, eco) -> float:
    # vitalité de la POPULATION ravageur locale (lecture diégétique)
    return f(ravageur[r,c], qi_nuis)        # qi_nuis = biomasse-hôte + chaleur − prédation

def vigueur_auxiliaire(r, c, eco) -> float:
    return f(auxiliaire[r,c], qi_aux)       # qi_aux = proie(ravageur) + nectar + habitat + stabilité
```

(Idem `vigueur_pollinisateur`, `vigueur_ver`.)

**Populations, pas individus.** Auxiliaires/ravageurs/etc. sont modélisés comme
**populations** (un champ), pas comme des individus. La façade lit donc une
**vitalité de population à un endroit**, pas une vitalité par sprite — les sprites
sont des **échantillons**, ils ne portent pas de Vigueur. C'est la différence
structurelle avec les plantes (qui sont des `PlantInstance` individuelles).

**Usages** (lecture seule) : descriptions du carnet/encyclopédie (« la population
de coccinelles est vigoureuse »), overlay debug, et — *en dette* — le signe du
gain de « manger un individu » (§5). **Jamais un pilote de simulation.**

---

## 5. Les gestes joueur branchés

Tous **event-driven, au-dessus du tick**, modifiant les champs comme **donnée
d'entrée** (comme les actions de `CONCEPTION_VIGUEUR.md` §3). Donc **ne re-figent
PAS le golden** (le golden n'a pas de joueur). Granularité : **un geste = un
individu = un quantum** (≈ `DENSITÉ_PAR_SPRITE`), pas toute la population du plot
(décision Nico).

| Geste | Effet sur le(s) champ(s) | Coût Vigueur | Pédagogie |
|---|---|---|---|
| **Favoriser un auxiliaire** (hôtel à insectes, nichoir, point d'eau, bande fleurie — déjà `CONCEPTION_VIGUEUR.md` §3.2) | ↑ terme **habitat** du champ `auxiliaire` (plancher persistant) | `MODÉRÉ` (action sur le milieu) | rien tout de suite ; **semaines plus tard** les auxiliaires s'installent **et restent** → régulation émergente. Le canal vertueux, pendant d'« écraser ». |
| **Écraser** un ravageur (devient **réel** — `actions.py:ecraser` n'était que comptabilité) | retire **un quantum** de `ravageur` au plot ciblé (le sprite cliqué) | `MODÉRÉ × URGENCE` | le champ **repousse** depuis sa ressource (l'hôte est toujours là) → **la pression revient**. Net négatif sec, le raccourci s'use (philo #1), sans sermon. |
| **Fourche-bêche / bêcher** (déjà `CONCEPTION_VIGUEUR.md` §3.2, `microbiome` ↓) | tue la faune du sol → **sprites « vers morts » transitoires** + ↓ `vers_de_terre` local | `FAIBLE` | **vers morts visibles = feedback viscéral immédiat**, *avant* la dette différée `microbiome → uptake → vigueur`. **Visuel avant santé.** La **grelinette** ne tue pas de vers (préserve) → contraste enseigné à l'œil, pas par un texte. |
| **Manger un individu** (ravageur / auxiliaire / pollinisateur / ver) | retire **un quantum** du champ correspondant | gain **signé selon l'espèce** | **EN DETTE** (cf. §7). On ne mange qu'**un individu**, pas la population. Manger un nuisible → perte de Vigueur. « Option rigolote, pas prioritaire » (Nico). |

**Prérequis débloqué.** « Manger / écraser un nuisible » était impossible faute
d'entité **ciblable** (aveu dans `sim/actions.py:ecraser`). Les **sprites
échantillonnés** (§3) *sont* cette cible cliquable → D31 débloque techniquement
ce volet de D19, même si le **gain signé** reste en dette.

---

## 6. Section bio — document à étudier (Nico, hors expertise)

> Cette section est un **doc à lire**, pas des questions à trancher (garde-fou
> « part bio hors expertise de Nico → produire un doc à étudier »). Elle fixe
> l'écologie qui justifie le modèle des §2-5. À enrichir au calibrage.

### 6.1 Les guildes

- **Ravageurs** (phytophages) : pucerons, limaces, doryphores, chenilles
  (lépidoptères), otiorhynques, aleurodes, acariens. Se nourrissent du
  **feuillage / de la sève / des racines**. Prolifèrent par temps chaud et en
  **monoculture** (ressource abondante, peu de régulation).
- **Auxiliaires** (prédateurs & parasitoïdes) : coccinelles, **syrphes**,
  chrysopes, carabes (sol), staphylins, **parasitoïdes** (trichogrammes,
  micro-guêpes). Point clé : chez beaucoup, **ce sont les LARVES qui dévorent les
  pucerons**, tandis que **les ADULTES se nourrissent de nectar/pollen**. D'où
  l'importance des **plantes-nectar** (achillée, phacélie, ombellifères) : elles
  nourrissent les adultes → ponte sur place → larves prédatrices. C'est le
  fondement des *insectary plants* / bandes fleuries.
- **Pollinisateurs** : abeilles domestiques & sauvages, **bourdons**, syrphes.
  **Recouvrement** avec les auxiliaires (les syrphes sont les deux à la fois) —
  d'où, dans le moteur, deux champs distincts mais des sources communes (fleurs,
  rondelles). Service : transport de pollen → fécondation croisée
  (`pollinator_reach`).
- **Faune du sol** (décomposeurs) : **vers de terre** (lombrics), collemboles,
  cloportes. Se nourrissent de **matière organique en décomposition** (incluant
  la **biomasse fongique** : mycélium, mycorhizes). Rendent : **aération**,
  **infiltration**, **brassage** des horizons, libération de nutriments. Très
  **sensibles au bêchage** (sectionnement mécanique) et à la sécheresse.

### 6.2 L'écologie proie-prédateur (pourquoi le modèle a un décalage)

- **Lag prédateur-proie.** Les prédateurs **suivent** leurs proies avec retard :
  il faut que les pucerons soient là pour que les coccinelles pondent, puis que
  les larves grandissent. D'où les **oscillations** (boom de ravageurs → boom
  d'auxiliaires → effondrement des ravageurs → effondrement des auxiliaires →
  re-boom). L'inertie des champs (§2.1) reproduit ce retard.
- **Refuge & habitat.** Sans **refuge** (haies, bandes enherbées, sol non
  travaillé, abris d'hivernage), les auxiliaires **disparaissent** entre deux
  pics de proie et ne sont pas là quand le ravageur revient. Avec un **habitat
  permanent**, une **population de fond** subsiste → régulation rapide. → le
  **plancher d'habitat** du champ `auxiliaire`.
- **Nectar = carburant des adultes prédateurs.** Cf. 6.1 : les plantes-nectar ne
  « nourrissent » pas directement la lutte, elles **soutiennent les adultes** qui
  pondent les larves prédatrices. → la ressource `nectar` du champ `auxiliaire`.

### 6.3 Pourquoi « agir sur le milieu » marche (philo #1/#2)

On **n'ajoute pas** des prédateurs (ce serait un bonus direct, interdit par la
philo #2). On **offre le milieu** — nectar + habitat + refuge + proies — et **ils
viennent et restent**. La régulation **émerge**. C'est exactement le canal
vertueux « favoriser un auxiliaire » (§5), symétrique du raccourci destructeur
« écraser ». Le **bêchage** illustre l'inverse : un geste qui **détruit le milieu
biologique** (faune du sol, microbiome) pour un gain mécanique immédiat → dette
écologique différée.

---

## 7. Interfaces avec les autres dettes

- **D27** — « champ auxiliaire dédié = sprint futur » : **c'est ce sprint**. Le
  terme `predator` reconstruit de proxies est remplacé par le champ `auxiliaire`.
- **D30** (structure/compaction du sol) — le champ `vers_de_terre` est un
  **support naturel** du bénéfice d'aération de la grelinette et du malus du
  bêchage. À coordonner : soit le bonus d'aération transite par `vers_de_terre`,
  soit par un champ `structure_sol` dédié (la question D30 reste ouverte ; ce
  doc fournit une option supplémentaire).
- **D19** (action manger) — **porte désormais le gain signé de « manger un
  individu »** (négatif pour un nuisible, etc.). **Mis en dette** sur décision de
  Nico (« option rigolote, pas prioritaire »). D31 fournit le **prérequis**
  (l'entité ciblable) ; D19 fournira la **valeur nutritive signée par espèce**.
- **D32** (perf LightField) — justifie le choix « champ plutôt qu'agents » : un
  champ est gratuit (borné aux 432 plots) là où des agents coûtent ∝ population.
- **`CONCEPTION_VIGUEUR.md`** — patron de façade (§1) réutilisé pour `vigueur_*`
  avec `qi_local` trophique ; actions `écraser`/`manger` y sont déjà cataloguées
  (§3.3) — ce doc les rend **réelles**.

---

## 8. Périmètre proposé pour le sprint d'implémentation (à venir)

Sprint **gros**, découpé en sous-sprints autosuffisants :

1. **D31.1 — Champs + perception.** Mécanisme `PopulationField` générique +
   4 instances (dynamique persistante, ressources/prédateurs/habitat) + règle
   d'échantillonnage sprite (§3). **Calculés mais pas encore lus par la santé/les
   services → golden INTACT.** Livre déjà le **visuel** (le cœur de l'intention
   de Nico). Golden de champ dédié (les densités doivent être déterministes et
   reproductibles).
2. **D31.2 — Câblage écologique.** L'herbivorie lit `ravageur` (remplace le
   scalaire `herbivory_pressure`) ; la prédation lit `auxiliaire` (le terme
   `predator` disparaît) ; `pollinator_reach` lit `pollinisateur` ;
   l'aération/structure lit `vers_de_terre` (coord. D30). **RE-FIGEAGE du golden
   écologique — unique, journalisé** (comme le sprint météo). Toute trajectoire
   qui bouge ici est **attendue**, pas un bug.
3. **D31.3 — Façades + gestes.** `vigueur_*` (§4, read-only) ; gestes « favoriser
   un auxiliaire » (plancher habitat), « écraser » (réel, retire un quantum),
   « fourche-bêche → vers morts visibles ». **Golden INTACT** (event-driven,
   au-dessus du tick). Golden joueur étendu si besoin.

**Hors périmètre (gated) :**
- **Gain signé de « manger un individu »** (D19) — en dette.
- **Prédateurs de sommet** (oiseaux mangeant auxiliaires/pollinisateurs/vers) —
  laissés vides, à ouvrir si la dynamique le réclame.
- **Sprites/animations Godot** (le rendu, l'« activité » visuelle) — côté C#,
  ce doc ne fixe que le **contrat** (densité → nombre/position/activité).
- **Calibrage** (`DENSITÉ_PAR_SPRITE`, caps, inerties, intensité du boom-bust) —
  post-test.
- **Portage C#** (D24).

---

## 9. Déterminisme & golden — récapitulatif

| Élément | Re-fige le golden ? |
|---|---|
| Champs de densité **calculés** (D31.1) | **Non** (rien ne les lit encore) |
| Sprites échantillonnés (§3) | **Non** (lecture pure, pas dans le golden) |
| **Câblage** herbivorie/prédation/pollinisation/aération (D31.2) | **OUI — re-figeage unique, journalisé** |
| Façades `vigueur_*` (§4) | **Non** (read-only) |
| Gestes joueur favoriser/écraser/fourche-bêche (§5) | **Non** (event-driven, le golden n'a pas de joueur) |

Principe : la vie macroscopique **est** de l'écologie → elle entre légitimement
dans le tick déterministe (philo #2/#3) ; seul son câblage à la santé/aux
services re-fige, **une fois**. Tout le reste (perception, lecture, gestes) reste
golden-neutre.
