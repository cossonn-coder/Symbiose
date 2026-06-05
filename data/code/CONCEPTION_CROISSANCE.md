# Conception — Croissance procédurale & morphogénèse des plantes (SYMBIOSE)

> **Document de conception. Aucun code écrit.** Spec de référence pour le futur
> chantier d'implémentation du **rendu procédural de croissance** des plantes,
> piloté par l'auxine et la lumière.
>
> Issu du **Sprint conception Croissance procédurale** (2026-06-05). Ce document
> **absorbe et refond** `CONCEPTION_HORMONES.md` : le modèle « 2 scalaires
> hormonaux » y est **abandonné** — l'auxine devient un **niveau le long d'une
> structure morphologique réelle**. Le doc hormones reste en archive (en-tête de
> renvoi), on n'y revient pas.
>
> Décisions actées avec Nico (8 forks structurants + profil par espèce, cf. §B).

---

## A. Objectif diégétique

La plante **cesse d'être une image figée par stade**. Sa forme **naît et se
transforme** sous l'effet de deux forces que le moteur simule déjà ou va simuler :
l'**auxine** (l'hormone de croissance, qui commande où la plante pousse) et la
**lumière** (`LightField`, déjà calculé). On *voit* :

- le jeune plant qui **file en flèche** (dominance apicale forte) ;
- l'**écimage / la taille** qui lève la dominance → la plante **débourre** et
  **buissonne** ;
- le vieux sujet qui **s'étale** naturellement (la dominance se relâche avec l'âge) ;
- la branche qui **pousse vers la trouée de lumière** (phototropisme).

C'est la philosophie #5 (indices biologiques visuels) poussée au maximum : la
**simulation et l'image racontent la même histoire**. La plante **porte sa
biographie dans sa forme** — cohérent avec le run éternel et le sol-mémoire.

---

## B. Les 8 décisions actées (+ la raison, condensée)

| # | Décision | Choix | Pourquoi |
|---|---|---|---|
| 1 | Représentation | **Structure de segments** (branches) | une vraie morphologie, pas deux chiffres |
| 2 | Où elle vit | **Moteur Python**, source de vérité, déterministe | règle du projet : ce qui influe la sim vit en Python |
| 3 | Construction | **Accumulation bornée** | la forme a une mémoire, mais bornée par la taille (run éternel) |
| 4 | Auxine | **Niveau le long des segments** | remplace les 2 scalaires ; fidèle à la dominance apicale |
| 5 | Direction | **Phototropisme** (biais `LightField`) | atout unique du projet : la lumière est déjà là |
| 6 | Empreinte | **Dérivée de la structure** | remplace les courbes de stades → **golden re-figé** |
| 7 | Organes | **Tout procédural** (branches + feuilles/fleurs/fruits) | cohérence visuelle, zéro dépendance sprite |
| 8 | Racines | **Rayon dérivé** (pas de structure souterraine) | suffisant pour la sim, invisible, économe |

> **Le mur qui est tombé.** `CONCEPTION_HORMONES.md` §B justifiait le repli
> « scalaire » par l'**absence de rendu végétal**. En décidant de **construire** ce
> rendu, on ouvre la porte que le doc hormones laissait entrouverte : la **vraie
> topologie** (option (i) d'alors) devient possible — et elle est plus fidèle à la
> biologie décrite (auxine qui descend, inhibe, débourrement).

> **Le critère « golden intact » disparaît.** L'ancien modèle visait un repos
> no-op. Ici la structure **remplace** le calcul d'empreinte issu des stades, donc
> le comportement de **toutes** les plantes change → le golden **sera re-capturé**
> (re-figeage légitime, comme succession/sénescence en leur temps). Nouvelle
> stratégie : **valider** le nouveau comportement (visuel + numérique), **puis
> figer**, et migrer **espèce par espèce** (cf. §I).

---

## C. Le modèle de données — la structure de segments

Une plante n'est plus décrite par son seul stade : elle **possède une structure**,
un arbre de segments enraciné au collet (le point sol `x_cm, y_cm` déjà existant).

### C.1 Le segment (unité, §grain « branches » acté)

```python
# (futur) — esquisse de contrat, PAS du code livré
@dataclass
class Segment:
    parent: int | None      # index du segment porteur (None = collet)
    base:   tuple           # (x_cm, y_cm, z_cm) — origine (z = hauteur sol)
    dir:    tuple           # vecteur directeur unitaire (3D : porte le phototropisme)
    length_cm: float        # longueur courante
    thickness_cm: float     # épaisseur (épaissit avec l'âge → vieux bois)
    age_weeks: int          # âge du segment
    auxin: float            # niveau d'auxine local [0,1] (cf. §D.1)
    is_apex: bool           # True si extrémité de croissance active
    organs: list            # feuilles/fleurs/fruits portés (cf. §H.2)
```

La plante porte `segments: list[Segment]` (+ un cache de l'empreinte dérivée, §G).
**Borné** (§3 acté) : pas un journal infini — la **structure présente vivante**.
Le vieux bois meurt et **tombe** (`_elaguer`, §D.6), les cicatrices vivent dans la
**forme du bois restant**, pas dans un historique conservé.

### C.2 Déterminisme (philo #3, non négociable)

Aucune décision de croissance n'utilise de RNG. Chaque choix stochastique-en-
apparence (direction d'un nouveau segment, quel latéral débourre, jitter d'angle)
passe par **`_hash_noise`** alimenté par `(seed_global, x_cm, y_cm, age, segment_id)`.
Même seed + mêmes gestes → **la même plante, au pixel près, sur toute machine**.

---

## D. L'algorithme de croissance — le cœur

À chaque tick (semaine simulée), pour chaque plante vivante, dans l'ordre :

### D.1 L'auxine le long de la structure

- **Production** : chaque apex actif produit de l'auxine (`AUXIN_SOURCE`).
- **Transport descendant** : l'auxine **descend** des apex vers le collet en
  **décroissant** (`auxin(parent) ← max(auxin(parent), auxin(enfant) · AUXIN_DECAY)`).
- **Inhibition latérale** : un bourgeon/segment latéral est **dormant** tant que
  l'auxine locale dépasse `AUXIN_INHIB_THRESHOLD`. Sous le seuil → **éligible au
  débourrement** (§D.3). C'est la **dominance apicale**, émergente de la structure.
- **Relâchement avec l'âge** : la production d'auxine de l'apex **décroît** quand la
  plante mûrit (`× f(age/maturité)`) → le vieux sujet **s'étale** tout seul. C'est
  le « moteur permanent » acté : l'architecture dérive en continu, sans perturbation.

### D.2 Allongement & émission (apex)

- Chaque apex actif **allonge** son segment de `growth_speed · vigueur · saison`
  (cf. profil espèce §E ; `vigueur` = lumière intégrée / `growth_factor` existant ;
  `saison`/température via `temp_min_growth` existant).
- Au-delà d'une longueur seuil, l'apex **émet un nouveau segment** dans sa direction
  (la flèche progresse). Épaississement du bois porteur (`thickness_cm ↑`).

### D.3 Débourrement (le latéral libéré)

Quand l'auxine d'un site latéral passe sous le seuil (relâchement naturel **ou**
perturbation §F), un **nouveau segment latéral** naît : direction = direction du
porteur **tournée** de `branch_angle` (profil espèce) + jitter déterministe. Ce
latéral devient un **nouvel apex** → il produit son auxine → une nouvelle hiérarchie
s'installe (le débourrement s'auto-limite, comme dans la nature).

### D.4 Phototropisme (biais lumière)

La direction d'un segment en croissance est **inclinée vers la lumière disponible** :
on échantillonne le `LightField` autour de l'apex et on biaise `dir` vers le gradient
lumineux, d'une force `phototropism_gain` (profil espèce). Une plante à l'ombre
**cherche la trouée** ; en plein soleil, elle pousse droit.

### D.5 Mise à fruit (lien reproduction)

Les organes reproducteurs se forment **selon le profil espèce** (§E, §H.2) : sur le
**bois latéral** (`fructification_laterale`, ex. pommier) ou en **terminal**. La
densité de bois latéral (issue du débourrement) **module le `reproduction_rate`
effectif** lu par `reproduction.py` — la taille « met à fruit » émerge, sans `+=`
scripté (philo #2).

### D.6 Bornage (vital — run éternel)

- **Sénescence du bois** : un segment dont l'âge dépasse `wood_persistence` (profil
  espèce) et qui ne porte plus d'apex actif **meurt** ; le sous-arbre détaché
  **tombe** (retour de nécromasse au sol — chaînage avec la sénescence existante D27).
- **Plafond de structure** : `MAX_SEGMENTS` par plante (gabarit espèce) — au-delà,
  les plus vieux segments improductifs sont élagués en priorité.
- Conséquence : la structure reste **bornée par la taille de la plante**, le save et
  le CPU restent sous contrôle même après 100 ans.

---

## E. Profil de croissance par espèce — **à décrire pour chaque plante**

> **Exigence actée par Nico (2026-06-05).** Chaque plante a sa **propre vitesse** et
> sa **propre stratégie** de croissance. Ce n'est pas un réglage global : c'est un
> **profil par espèce**, et **il faudra décrire chaque espèce du catalogue** pour la
> relier à ce modèle. Tant qu'une espèce n'a pas son profil, elle ne peut pas
> pousser proprement dans le moteur procédural.

### E.1 Le schéma du profil (nouveaux attributs de classe sur `PlantBase`)

```python
# (futur) — profil de croissance, par classe d'espèce
growth_speed:          float   # vitesse d'allongement / cadence d'émission
port_archetype:        str     # stratégie de port (cf. E.2)
apical_dominance_base: float   # force de la dominance au repos [0,1] (flèche↔buisson)
branch_angle:          float   # angle d'insertion des latéraux (degrés)
phototropism_gain:     float   # sensibilité à la lumière
wood_persistence:      int     # longévité du bois (semaines) → bornage §D.6
max_height_cm:         float   # gabarit (repris des stages/age_curve existants)
max_extent_cm:         float   # rayon max de couronne
organ_site:            str     # "terminal" | "lateral" — où naissent fleurs/fruits
```

Le trait `reponse_taille` du doc hormones est **absorbé ici** : la réponse à la
taille n'est plus un cas spécial, c'est une **conséquence** de
`apical_dominance_base` + du débourrement (§D.3). Une « graminée » (méristème basal)
a `port_archetype="graminee"` → pas de débourrement le long d'une tige → insensible
à l'écimage **par construction** (plus besoin d'un drapeau dédié).

### E.2 Les archétypes de port (la « stratégie »)

| `port_archetype` | Comportement | Exemples catalogue |
|---|---|---|
| `fleche` (excurrent) | axe dominant fort, peu ramifié, vertical | conifères ; jeunes arbres |
| `etale` (decurrent) | dominance qui se relâche vite, couronne large | **pommier**, cerisier, noyer, chêne (adultes) |
| `buissonnant` | dominance modérée, ramifie volontiers | **tomate**, poivron, basilic |
| `rosette` | méristème ras du sol, feuilles en rosette | pissenlit, capselle |
| `graminee` | talle à la base, méristème basal | pâturin (insensible à l'écimage) |
| `grimpant` | tiges longues, phototropisme fort, s'appuie | haricot |
| `rampant` | étalement horizontal au sol | trèfle |

### E.3 Reliure à l'existant — **on ne jette pas les données**

Les `growth_stages` (annuelles) et `age_curve` (ligneuses, perennials.py) actuels
décrivent **déjà** une vitesse (durées / âges) et un gabarit (hauteurs/rayons). Ils
deviennent les **cibles de calibration** du profil : on règle `growth_speed`,
`max_height_cm`, etc. pour que la **structure en croissance libre reproduise
l'allure actuelle** (cf. conseil « reproduire d'abord, enrichir ensuite »), puis on
laisse le moteur procédural enrichir (dérive âge-dépendante, phototropisme). C'est ce
qui rend la migration **espèce par espèce** sûre (§I).

### E.4 Le catalogue à décrire (travail explicite)

**14 espèces** à doter d'un profil. Démonstratrices détaillées d'abord, le reste à
décrire au fil de la migration :

| Espèce (clé) | `port_archetype` pressenti | Statut profil |
|---|---|---|
| Tomate (`tomate`) | `buissonnant` | **démonstratrice — à détailler** |
| Pommier (`pommier`) | `etale` (fructif. latérale) | **démonstratrice — à détailler** |
| Poivron, Basilic | `buissonnant` | à décrire |
| Haricot | `grimpant` | à décrire |
| Trèfle | `rampant` | à décrire |
| Tournesol | `fleche` | à décrire |
| Capselle, Pissenlit | `rosette` | à décrire |
| Pâturin | `graminee` | à décrire |
| Luzerne lupuline | `rampant`/`buissonnant` | à décrire |
| Figuier | `buissonnant` | à décrire |
| Cerisier, Noyer, Chêne | `etale` | à décrire |

> **Règle :** ajouter/migrer une espèce = lui **écrire son profil de croissance**
> (vitesse + archétype + leviers), calibré sur ses `growth_stages`/`age_curve`. Cette
> description par espèce est une **étape de première classe** du chantier, pas un
> détail post-hoc.

---

## F. Le seam de perturbation — `atteindre_segment(intensité)`

Découplage acté : le mécanisme hormonal ne sait pas **qui** abîme la plante.

```python
# (futur) — un seul point d'entrée, intensité CONTINUE [0,1] (acté)
def atteindre_segment(plant, segment_id, intensite: float):
    seg = plant.segments[segment_id]
    seg.auxin = max(0.0, seg.auxin - intensite)   # chute → lève l'inhibition aval
    if intensite >= COUPE_NETTE:                   # écimage : on retire l'apex
        seg.is_apex = False                        # + retrait géométrique du sous-arbre
```

- **`tailler` (action joueur)** = **premier appelant** : `intensite ≈ 1` sur l'apex
  (écimage) ou sur une branche (égourmandage). Reste dans `actions.py`, coût
  `MODERE`, binaire, seam `cout_action`, gain ∝ maturité (inchangé vs doc hormones).
- **Plus tard (sprint dédié)** : grêle (`intensite ∝ sévérité`), herbivorie du
  bourgeon par un ravageur (vie macro D31), vent. Ils appellent **le même seam** →
  l'écosystème peut « tailler » une plante tout seul (philo #1/#2). **Hors périmètre
  immédiat** (acté : « nature → apex plus tard, par étapes »).

---

## G. Dérivation de l'empreinte (structure → simulation)

Le `LightField` et la sim ne lisent **pas** la structure brute : ils lisent
l'**empreinte** que la structure **produit**. Les classmethods existantes deviennent
des **lecteurs du cache d'empreinte** recalculé après la croissance :

- `height_at` ← `max(z)` des segments vivants.
- `canopy_radius_at` ← extension horizontale max de la couronne.
- `foliage_density_at` ← densité de segments feuillés (bornée ≤ 1).
- `root_radius_at` ← **rayon dérivé** (acté §8) : `k · max_extent` ou `k · height`,
  pas de structure souterraine. Conserve `root_plots` tel quel.

Avantage : **le reste du moteur ne change pas d'interface** (le `LightField`
appelle toujours `height_at`…). On substitue la **source** des valeurs (structure au
lieu de stades), pas le contrat. C'est ce qui rend le golden re-figé **localisé**.

---

## H. Le rendu pixel — tout procédural (acté §7)

> Pédagogie Godot (Nico débute le frontend) : aujourd'hui les `visuals/*` sont des
> **stubs**, seul `SpriteLoader` charge des fichiers. On conçoit donc le **premier**
> vrai rendu de plantes — page quasi blanche, peu de legacy à défaire.

### H.1 Projection structure → pixels

La structure vit en **cm 3D** (espace sol). Le rendu la **projette** dans l'espace
iso d'affichage, puis **rastérise** chaque segment en pixels (ligne épaissie de
`thickness_cm`), au **palier de zoom courant** (×4/×8/×16/×32, entiers, filtre
Nearest). Cohérence pixel art : la rastérisation arrondit aux pixels du palier.
Déterminisme du rendu = déterminisme de la structure (§C.2) + projection pure.

### H.2 Organes procéduraux (le risque n°1 — cf. §K)

Feuilles / fleurs / fruits **dessinés par algorithme** (pas de sprites), accrochés
aux segments selon `organ_site` (§E.1) : feuilles le long des segments feuillés,
fleurs/fruits en terminal ou latéral. Forme/taille **fonction du stade de l'organe**
(bouton → fleur → fruit vert → fruit mûr) et de la **saison**. Palette par espèce +
**décalage saisonnier** (vert → jaune/rouge automnal ; caducs nus l'hiver, déjà géré
par `deciduous`/`foliage_density_at`).

### H.3 Niveau de détail (perf rendu)

Aux zooms faibles (×4), on ne rastérise pas chaque brindille : **simplification** en
silhouette de couronne (l'empreinte §G donne le contour). Aux zooms forts (×16/×32),
détail segment + organes. LOD piloté par le palier de zoom.

---

## I. Articulation avec l'existant

- **Modèle hormonal** : `CONCEPTION_HORMONES.md` refondu ici. Les 2 scalaires
  (`dominance_apicale`/`ramification`) → **auxine par segment** + **densité de bois
  latéral**. L'action `tailler` survit (appelant du seam §F). La détection de succès
  maîtrise (marqueur `🌿`, §9.5) reste valable : « débourrement observé imputé à la
  taille » = montée de bois latéral dans la fenêtre d'imputation.
- **Stades de croissance** : `growth_stages`/`age_curve` ne pilotent plus directement
  l'empreinte ; ils deviennent **cibles de calibration** du profil (§E.3) et peuvent
  rester pour le carnet/encyclopédie (nommer « semis/jeune/adulte/mature »).
- **Stratégie golden (re-figeage maîtrisé)** :
  1. On implémente le moteur procédural **derrière** l'interface d'empreinte (§G).
  2. On migre **une espèce démonstratrice** (tomate), on **compare** sa trajectoire
     d'empreinte à l'ancienne (doit coller au gabarit, §E.3), on **valide visuel**.
  3. On **re-fige** le golden une fois le comportement jugé correct ; les espèces non
     encore migrées gardent l'ancien chemin (stades) → migration **incrémentale**.
  4. Le nouveau golden protège les régressions futures.

---

## J. Sauvegarde (cycle existant : passage de saison, JSON lisible)

La structure **fait partie de l'état** → sérialisée dans le save JSON, par plante :
liste de segments (champs §C.1). Bornée (§D.6) → taille de save maîtrisée. Champ
`engine_version` déjà prévu (casse explicite, pas de migration < v1.0).

> **Option d'allègement** (calibrage) : si le save grossit trop, on peut ne stocker
> que les **segments de bois** (structurels) et **régénérer les organes** (feuilles)
> à la volée depuis l'état + seed — les organes sont les plus nombreux et les plus
> reconstructibles. À trancher au calibrage, après mesure.

---

## K. Perf & risques

- **Risque n°1 — générateur d'organes procéduraux convaincant.** Dessiner feuilles/
  fleurs/fruits beaux *par algorithme* en pixel art est le vrai défi esthétique →
  **sous-sprint dédié, itératif** (§M). C'est là que le projet peut déraper en temps.
- **CPU sim** : la croissance de structure s'ajoute au tick (177 ms aujourd'hui,
  marge gameplay ×339). Coût ∝ nombre de segments → **bornage §D.6 = garde-fou**.
- **CPU/GPU rendu** : distinct de la sim ; maîtrisé par le **LOD §H.3** et la
  rastérisation au palier de zoom.
- **Couplage `LightField`** : déjà 53 % du CPU (dette perf D32). La structure ne
  l'alourdit pas si l'empreinte (§G) reste l'unique interface échantillonnée.

---

## L. Points ouverts → calibrage (leviers nommés, valeurs post-test)

| Levier | Rôle |
|---|---|
| `AUXIN_SOURCE`, `AUXIN_DECAY`, `AUXIN_INHIB_THRESHOLD` | dynamique de la dominance apicale |
| `growth_speed`, `branch_angle`, `phototropism_gain` (par espèce) | vitesse & stratégie §E |
| `wood_persistence`, `MAX_SEGMENTS` (par espèce) | bornage §D.6 |
| `COUPE_NETTE` | seuil d'intensité retirant l'apex §F |
| densité bois latéral → `reproduction_rate` (seuil/pente) | mise à fruit §D.5 |
| paramètres de palette / décalage saisonnier des organes | rendu §H.2 |
| seuil d'allègement save (organes régénérés ?) | save §J |

---

## M. Découpage proposé du chantier (sprint **gros** → sous-sprints)

Conception seule ici ; voici l'ossature d'implémentation (à raffiner en kickoffs) :

1. **Structure & croissance Python (cœur)** — `Segment`, auxine le long de la
   structure, allongement/débourrement/bornage, déterministe. Tests de croissance
   libre (une espèce). *Golden re-figé à ce tronçon (comportement change).*
2. **Profil par espèce + dérivation d'empreinte** — schéma §E sur `PlantBase`,
   profil de la **démonstratrice (tomate)** calibré sur ses stages, branchement de
   `height_at`/`canopy_radius_at`… sur le cache d'empreinte (§G). Migration
   incrémentale (§I).
3. **Seam de perturbation + `tailler`** — `atteindre_segment` (§F), `tailler`
   rebranché dessus (apex/branche), coût/gain inchangés. Démonstratrice **pommier**
   (`etale`, fructification latérale). *Le sprint D29 hormones est absorbé ici.*
4. **Rendu pixel structure (Godot)** — projection iso + rastérisation segments aux
   zooms ×4…×32, LOD §H.3. Premier rendu visible des branches.
5. **Organes procéduraux (Godot) — risque n°1** — générateur feuilles/fleurs/fruits,
   stades d'organe, palette/saison. Itératif.
6. **Save de la structure** — sérialisation JSON bornée (§J), option d'allègement.
7. **(plus tard, hors chantier)** — déclencheurs naturels du seam (grêle/chenille/
   vent) ; marqueur `🌿` ; profil de croissance du **reste du catalogue** (§E.4).

**Hors périmètre (gated) :** structure racinaire réelle (§8 = rayon dérivé), rendu
végétal vectoriel/L-system avancé, portage C# (D24), déclencheurs naturels (sprint
ultérieur).
