# CONCEPTION — Rendu du feuillage et des organes végétaux par espèce

Cap : combler les trous du **rendu des feuilles** par espèce (forme, couleur,
nervures, croissance, insertion, chute) dans la continuité du **rendu pixel-art
16-bit** — cf. [`CONCEPTION_RENDU_PIXELART.md`](CONCEPTION_RENDU_PIXELART.md)
(SS④ « plantes/organes »). Couche **B** (pixellisation, `visuals/PlantRenderer.*`)
sauf deux tronçons « pont » (§4, §6) qui transportent une donnée déjà calculée par
le moteur.

**Golden trivialement préservé** : le rendu est une vue passive, zéro moteur
touché. Les deux entorses pont ne font que *transporter* (pas calculer) → golden
inchangé.

## Périmètre — 6 exigences Nico

- **E1** — croissance progressive des feuilles sur 1 à 2 semaines.
- **E2** — nervures d'une couleur ≠ du reste de la feuille.
- **E3** — forme **et** couleur de la feuille dépendent de l'espèce.
- **E4** — jamais d'aplat (couleur unie) : toujours des nuances.
- **E5** — chaque feuille émerge d'une branche verte.
  - **E5bis** (ajout 2026-06-24) — quand la feuille tombe, elle casse au pétiole
    et reste apparente au sol (litière).
- **E6** — certaines grimpantes produisent des vrilles (spirales) qui grimpent en
  s'accrochant et se contractant comme un ressort.

### Verrous tranchés (Nico, 2026-06-24)

- **①b** — la croissance des feuilles est ancrée sur l'**âge réel du segment**
  (`age_weeks`), à exposer au pont (re-bump `ENGINE_VERSION`).
- **②b** — la **mécanique de grimpe** des vrilles SORT de ce doc = sprint moteur
  Python séparé, suivi en **dette D49**. Seul le *contrat de rendu* est pré-cadré
  ici (§7).
- **③** — la **forme de feuille** est codée **directement en C#** (dérogation
  assumée à D10).

## §0 — État des lieux (acté, `Organs.cs`)

- **Placement** : feuilles déjà ancrées aux segments « feuillus »
  (`IsLeafy = IsApex || ThicknessCm ≤ LeafMaxThickCm`) → **E5 quasi acquis**.
- **Forme** : ellipse générique unique → **E3-forme = vrai trou**.
- **Couleur** : table `Palettes` par espèce existe mais **2 entrées** (Tomato,
  AppleTree) + défaut → **E3-couleur = étendre la table**.
- **Nervures** : aucune → **E2 = trou**.
- **Croissance** : feuille à pleine taille (`FoliageDensity` ne règle que la
  densité) → **E1 = trou**.
- **Nuances** : SS② a supprimé les aplats (volume 2 valeurs + hue-shift) →
  **E4 = à ériger en règle**.
- **Affaissement sécheresse** : DÉJÀ implémenté (`Organs.cs:134-136`,
  `lz -= _drought * DroughtDroopCm`) — pas un trou.

## §1 — Principes et invariants (couche B)

Quatre règles non négociables qui gouvernent tout le rendu du feuillage. Elles
héritent de SS② (palette 16-bit) et de la philo #3 (déterminisme).

1. **Jamais d'aplat (E4).** Aucun organe végétal n'est peint d'une seule couleur
   unie. Tout limbe est au minimum un **volume 2 valeurs** (ombre froide + calotte
   éclairée sud), via `DrawVolumeEllipse`. Les nervures ajoutent une 3ᵉ valeur.
   C'est la signature pixel-art : on lit le relief, pas une gommette.
   - **Exception bornée** : sous un **rayon plancher** (~2-3 px écran), une feuille
     naissante (premiers jours de croissance, §4) est peinte en **1 valeur** — le
     croissant d'ombre serait illisible à cette taille. Exception transitoire, le
     temps que la feuille grandisse.

2. **Déterminisme total.** Zéro `Random`. Toute variation (taille, inclinaison,
   choix de silhouette, jitter de nervure) dérive d'un **hash** stable de
   l'identité du segment/organe (position, indice). Re-rendre la même plante au
   même tick donne exactement la même image — condition du golden et du débogage
   visuel.

3. **Le bois n'est jamais teinté par le feuillage.** La rampe de lignification
   (`WoodRamp`, vert-tendre → olive → brun) reste maîtresse du rendu des segments.
   Une feuille « verte » colore le limbe, pas le rameau porteur. (Le rameau peut
   être vert s'il est jeune/apex — c'est la rampe qui le dit, §5.)

4. **Couche B pure = golden préservé.** Tout ce doc décrit du **rendu**
   (`visuals/PlantRenderer.*`). Deux exceptions assumées : la croissance
   progressive (§4) a besoin de `age_weeks` au segment, et la litière (§6) a besoin
   de la litière typée par parcelle — données qui transitent par le **pont**
   (couche A → snapshot). Ce sont les seuls tronçons qui touchent le contrat
   Python↔Godot (re-bump `ENGINE_VERSION`), et seulement pour *transporter*.

> **Frontière forme.** Dérogation actée à D10 (③ direct C#) : les **silhouettes de
> feuilles** sont prototypées et codées **directement en C#**, sans maquette SVG
> Python préalable. Justification : la forme de feuille est un fait de *rendu*
> (décoration de vue), sans équivalent moteur — contrairement à la morphogénèse
> des branches qui, elle, vit en couche A.

## §2 — Forme de feuille par espèce (E3-forme)

Aujourd'hui toute feuille est une **ellipse générique unique**
(`DrawVolumeEllipse`, `LeafSizeCm`). C'est le vrai trou de E3. On le comble par un
**catalogue d'archétypes de silhouette**, choisi par espèce, dessiné directement
en C# (dérogation D10, §1).

### 2.1 — Archétypes (petit catalogue fermé)

Un `enum LeafShape` couvre les grandes familles morphologiques observables au
pixel, du plus simple au plus composé :

| Archétype | Construction pixel | Exemples espèces |
|---|---|---|
| `Elliptique` | l'ellipse actuelle (défaut) | générique, basilic |
| `Lanceolee` | ellipse très élancée (ratio long/large ↑) | saule, graminées |
| `Cordee` | ellipse + échancrure basale (cœur) | haricot, lierre |
| `Lobee` | 3-5 lobes = ellipses fusionnées autour d'un centre | vigne, érable, courge |
| `Composee` | N folioles = petites ellipses le long d'un rachis | tomate, frêne, rosier |
| `Aciculaire` | trait court épais (aiguille) | conifères |

Fermé volontairement : 6 formes couvrent le catalogue (27 plantes) sans explosion
combinatoire. Une espèce non mappée → `Elliptique` (défaut, comme la palette).

### 2.2 — Descripteur par espèce

On étend le principe de la table `Palettes` (déjà per-espèce) avec un
**`LeafProfile`** : la forme + ses paramètres morphologiques.

```
readonly record struct LeafProfile(
    LeafShape Shape,
    float Aspect,      // élancement = longueur/largeur (1 = rond, 3 = très étiré)
    int    Count,      // nb de lobes (Lobee) ou de folioles (Composee), sinon 0
    bool   VeinLighter); // sens du shift nervure (§3.2) : true = plus claire
```

Une table `LeafProfiles[species]` en regard de `Palettes[species]`. Mappage initial
pour les espèces déjà peintes, défaut `Elliptique` partout ailleurs — on enrichit
progressivement, sans bloquer.

### 2.3 — Tracé déterministe

Chaque archétype est une **composition de primitives volumées** (chaque
sous-élément passe par `DrawVolumeEllipse` → garde l'invariant 2 valeurs §1) :
- `Lobee` / `Composee` placent leurs N sous-ellipses par un **hash** du segment
  (jitter d'angle/longueur stable, philo #3) — pas deux feuilles identiques, mais
  reproductibles.
- L'orientation générale suit déjà l'axe du rameau porteur (placement existant
  `Organs.cs`).
- Le **plancher de rayon** du §1 s'applique au volume global : sous le seuil, on
  tombe sur une seule ellipse 1 valeur quelle que soit la forme (une mini-feuille
  naissante n'a pas de lobes lisibles).

> **Coût.** `Lobee`/`Composee` multiplient les `DrawEllipse` par feuille (3-5×). À
> borner au F4 si la densité de feuillage pèse — repli LOD : au dézoom, toute forme
> retombe sur `Elliptique` (la silhouette fine est invisible de loin de toute
> façon).

## §3 — Couleur du limbe et nervures (E3-couleur + E2)

Deux trous traités ensemble car la nervure est une **dérivée chromatique** du
limbe.

### 3.1 — Couleur du limbe par espèce (E3-couleur)

La table `Palettes[species]` existe mais n'a que **2 entrées** (Tomato, AppleTree)
+ défaut. Le geste est simple : **étendre la table** aux espèces cultivées du
catalogue, chacune avec sa teinte de base. Pas de nouveau mécanisme — juste du
contenu.

- La teinte de base reste passée à `DrawVolumeEllipse`, qui applique déjà le volume
  2 valeurs (ombre froide / calotte sud) via `HueShift` (SS②). **E4 garanti par
  construction.**
- La modulation saisonnière (`LeafColor`, SS②) reste appliquée par-dessus la teinte
  d'espèce — une feuille de pommier vire au jaune-roux à l'automne **à partir de**
  son vert d'espèce, pas d'un vert générique.
- Espèce non mappée → `DefaultPalette` (statu quo). On enrichit au fil de l'eau,
  jamais bloquant.

### 3.2 — Nervures = 3ᵉ valeur (E2)

La nervure n'est **jamais** de la couleur du limbe (exigence E2 explicite). Règle
déterministe :

- **Teinte** : dérivée du limbe par un `HueShift` léger. Le **sens du shift**
  (plus claire / plus sombre) est un **champ du profil par espèce**
  (`LeafProfile.VeinLighter`) — certaines espèces portent une nervation pâle
  gravée, d'autres une nervation sombre marquée. Une constante `VeinShift` règle
  l'amplitude (ajustable F5).
- **Tracé** : fines lignes **1 px** (jamais antialiasées, cohérent pixel-art),
  posées **après** le volume → la nervure est la 3ᵉ valeur qui se lit par-dessus
  l'ombre+lumière.
- **Topologie par archétype** :
  - `Elliptique` / `Lanceolee` / `Cordee` → **penninerve** : 1 nervure médiane +
    2-4 latérales obliques (hash pour l'écartement).
  - `Lobee` → **palmée** : une nervure par lobe, rayonnant de la base.
  - `Composee` → une médiane par foliole.
  - `Aciculaire` → **aucune** (trop fin, illisible au pixel).
- **Plancher §1** : sous le rayon plancher, **pas de nervure** (feuille naissante =
  1 valeur nue) ; les nervures n'apparaissent qu'une fois la feuille assez grande —
  ce qui sert aussi la croissance progressive (§4).

> **Lien E4.** Avec la nervure, une feuille adulte porte **3 valeurs** (ombre /
> calotte / nervure). L'aplat est doublement impossible. La mini-feuille naissante
> (1 valeur) est la seule exception, transitoire et bornée par le plancher.

## §4 — Croissance progressive de la feuille (E1)

Aujourd'hui la feuille naît à **pleine taille** (`FoliageDensity` ne règle que la
densité, pas la taille individuelle). E1 veut une feuille qui **grandit sur 1 à 2
semaines**. Choix acté **①b** : la croissance est ancrée sur l'**âge réel du
segment porteur** (`age_weeks`), pas sur un timer de vue.

### 4.1 — Le pont (couche A → snapshot)

`Segment` (miroir C# `PlantStructure.cs`) **omet** aujourd'hui `age_weeks`. On
l'expose :
- Côté Python : `age_weeks` du segment ajouté au snapshot de structure.
- Côté C# : champ ajouté au `record struct Segment` + lecture dans `FromSnapshot`.
- **Re-bump `ENGINE_VERSION`** (contrat Python↔Godot modifié).

> C'est de la donnée déjà calculée par le moteur (la morphogénèse connaît l'âge de
> chaque segment) ; on ne fait que la **transporter**. Aucun calcul moteur nouveau
> → golden inchangé.

### 4.2 — Le facteur de croissance (couche B)

Un facteur `leafGrowth ∈ [0,1]` dérivé de l'âge du segment :

```
leafGrowth = clamp(seg.AgeWeeks / LeafMaturityWeeks, 0, 1)   // LeafMaturityWeeks ≈ 1.5
```

- Il **multiplie le rayon** du volume de la feuille (`LeafSizeCm * leafGrowth`).
- Synergie avec le **plancher §1** : à l'émergence (`age ≈ 0`), le rayon est sous
  le plancher → **1 valeur nue, pas de nervure** ; en grandissant il franchit le
  plancher → volume 2 valeurs, puis nervures (§3). La feuille se **construit
  visuellement** au fil des jours, gratuitement.
- Optionnel : une légère **courbe d'accélération** (ease-out) pour un démarrage
  doux — une constante, ajustable F5.

### 4.3 — Pas de pop-in

Les segments déjà mûrs au chargement (`age ≥ maturity`) rendent `leafGrowth = 1` →
feuilles pleines immédiatement, aucun « surgissement » à l'ouverture d'une partie
existante. Seules les feuilles **réellement jeunes** sont vues en croissance.

> **Âge du segment, pas de la feuille.** On utilise l'âge du segment porteur comme
> proxy (déjà calculé, zéro travail moteur). Un âge propre à chaque feuille serait
> plus fidèle mais demanderait au moteur de tracer la date d'émergence de chaque
> feuille — hors périmètre rendu.

## §5 — Insertion de la feuille sur un rameau vert (E5)

E5 : chaque feuille **émerge d'une branche verte**. C'est l'exigence la plus proche
de l'acquis — on la verrouille plutôt qu'on ne la construit.

### 5.1 — L'acquis (déjà en place)

- Le placement des feuilles est **déjà ancré** aux segments « feuillus » :
  `IsLeafy(s) = s.IsApex || s.ThicknessCm ≤ LeafMaxThickCm` (`Organs.cs`). Une
  feuille ne naît jamais sur un gros tronc lignifié.
- Or un segment fin/jeune a une **lignification faible** → `WoodRamp` le rend en
  **vert tendre** (côté `ApexColor` de la rampe, SS②). Donc *par construction*, le
  rameau porteur d'une feuille **est déjà peint en vert**. E5 est cohérent sans
  travail supplémentaire.

### 5.2 — Le verrou (invariant explicite)

On **érige en règle** ce qui est aujourd'hui une coïncidence heureuse : **feuille
⟹ segment rendu vert**. Si une évolution future rendait un segment feuillu
non-vert (p. ex. un seuil de lignification désaccordé du seuil `IsLeafy`), ce
serait un bug. Garder `LeafMaxThickCm` cohérent avec le point de bascule
vert→olive de la rampe (`LignifyFullCm`).

### 5.3 — Le pétiole (renfort lisibilité, optionnel)

Pour rendre l'**émergence** explicite (et pas une feuille « posée » dans le vide),
un court **pétiole vert** de 1-2 px relie le point d'insertion au limbe :
- couleur = teinte verte **du rameau local** (rampe au point d'insertion), jamais
  brune — réaffirme E5 ;
- orientation = celle déjà calculée (`LeafOffsetCm`, axe rameau → extérieur) ;
- soumis au facteur `leafGrowth` (§4) : le pétiole s'allonge avec la feuille ;
- c'est aussi le **point de rupture** de l'abscission (§6).

## §6 — Chute de la feuille (abscission) et litière au sol

E5bis (ajout Nico 2026-06-24) : quand une feuille tombe, elle **casse au pétiole**,
et la **feuille tombée reste apparente au sol**.

### 6.1 — Le déclenchement (couche A, déjà émis)

La chute n'est **pas** une décision de vue. Le moteur fait déjà décroître le
feuillage (sénescence, sécheresse/gel sévères, caducité saisonnière) **et**
alimente la **litière de la parcelle** (sprint Décomposition & compost). Côté
rendu, « une feuille est tombée » = le feuillage de la plante a baissé **et** la
litière de la parcelle a monté. On ne fait que **traduire** ces deux faits.

### 6.2 — La cassure au pétiole (couche B)

Le pétiole vert (§5.3) est le **point de rupture** : une feuille qui disparaît de
la plante ne laisse **pas** de moignon brun proéminent — elle se détache nettement.
Pas d'animation de chute (la sim est par ticks, pas frame-à-frame) : la feuille
**cesse d'être peinte sur la plante** et **apparaît dans la litière au sol** de la
même parcelle au tick suivant. La continuité est assurée par la conservation de
matière du moteur, pas par une trajectoire.

### 6.3 — La litière au sol (couche B procédurale)

La feuille tombée est rendue comme **litière** : un semis déterministe de
silhouettes de feuilles au sol, sur la parcelle, à la manière de `MacroLife`
(échantillonnage stable, pas de `Random`).
- **Forme** : la même `LeafProfile` que l'espèce (§2) — une litière de pommier a
  des feuilles de pommier. (Repli `Elliptique` si l'origine n'est pas traçable.)
- **Couleur** : teinte **morte/sèche** (brun-roux désaturé), qui **dérive vers le
  sol** au fil de la décomposition (le moteur connaît l'état de décompo de la
  parcelle → on assombrit/désature progressivement jusqu'à fondre dans l'humus).
- **Quantité** : nombre de feuilles au sol **∝ quantité de litière** de la parcelle
  (bornée, comme la pop macro).
- **Pose** : à plat, **volume aplati** (calotte réduite) — une feuille au sol n'a
  pas le même relief qu'une feuille dressée, mais reste ≥ 2 valeurs (invariant §1).

### 6.4 — Le pont (à vérifier)

À confirmer : la **litière par parcelle** (quantité + type/espèce + état de
décompo) est-elle déjà dans le snapshot du pont ? Si non, c'est une **2ᵉ entorse
couche B** (comme `age_weeks` au §4) → exposer la litière au snapshot + re-bump
`ENGINE_VERSION`. Donnée déjà calculée par le moteur → golden inchangé, simple
transport. Le rendu par silhouette d'espèce (§6.3) **suppose la litière typée par
espèce** dans le snapshot.

## §7 — Vrilles grimpantes (note de rendu, différée)

E6 : certaines grimpantes produisent des **spirales (vrilles)** qui s'accrochent et
se contractent comme un ressort pour grimper.

### 7.1 — Hors périmètre de ce doc (pour l'instant)

La **mécanique de grimpe** (la vrille cherche un support `StakeSlot`/mur,
s'accroche, se contracte, gagne en hauteur → accès lumière) est une
**transformation de géométrie** : c'est de la **couche A** (morphogénèse Python),
suivie en **dette D49** comme un sprint moteur à part entière. Tant que D49 n'a pas
livré la **topologie de vrille** dans la structure (segments de type vrille, état
accroché/libre, pas de l'hélice), il n'y a **rien à pixelliser**. Le rendu de
vrille **attend D49**.

### 7.2 — Ce que le rendu fera, le moment venu (pré-cadrage)

Pour que D49 sache quoi exposer, on fixe l'attendu rendu :
- une vrille = un **segment fin** (donc déjà **vert**, rampe SS②, cohérent §5)
  rendu en **arc/hélice** plutôt qu'en trait droit — un tracé de spirale
  déterministe le long du segment ;
- l'état **accroché vs libre** (fourni par D49) change l'allure : libre = spirale
  lâche qui « cherche » ; accroché = spirale **serrée/contractée** (le ressort
  tendu) ;
- pas d'animation de contraction frame-à-frame : comme la chute (§6), on **rend
  l'état courant** fourni par le moteur à chaque tick.

> **Dépendance explicite.** Ce §7 ne produit **aucun code** dans le tronçonnage
> (§8) tant que D49 n'est pas livrée. Il sert de **contrat d'interface** : voilà ce
> que le rendu réclamera à la couche A. Lien : `DETTE.md` D49.

## §8 — Tronçonnage (chaque tronçon préserve le golden)

Rendu = vue passive → **golden trivialement préservé** sur tous les tronçons (même
T5/T6 qui ne font que *transporter* des données déjà calculées). Ordre : **couche
B pure d'abord** (zéro pont), **tronçons pont ensuite**.

| Tr | Contenu | § | Couche | Pont | Exigence |
|----|---------|---|--------|------|----------|
| **T1** | Couleur du limbe par espèce — étendre la table `Palettes` aux cultivées | §3.1 | B pure | — | E3-couleur |
| **T2** | Forme par espèce — `enum LeafShape`, `LeafProfile`, tracé des 6 archétypes (jitter par hash) | §2 | B pure | — | E3-forme |
| **T3** | Nervures = 3ᵉ valeur — topologie par archétype, sens du shift par espèce | §3.2 | B pure | — | E2 |
| **T4** | Insertion — verrou « feuille ⟹ vert » + pétiole vert | §5 | B pure | — | E5 |
| **T5** | Croissance progressive — `age_weeks` au segment, facteur `leafGrowth` | §4 | B + pont | `ENGINE_VERSION`↑ | E1 |
| **T6** | Chute + litière — abscission au pétiole, semis de litière typée au sol, dérive de décompo | §6 | B + pont | `ENGINE_VERSION`↑ | E5bis |
| ~~T7~~ | ~~Vrille~~ — **différé, gated D49** (couche A non livrée) | §7 | — | — | E6 |

**Invariants transverses** (pas des tronçons, vérifiés à chaque T) :
- **E4 « jamais d'aplat »** : tout organe ≥ 2 valeurs (sauf mini-feuille sous
  plancher, transitoire) ;
- **déterminisme** : zéro `Random`, tout par hash ;
- **bois non teinté** par le feuillage.

**Dépendances** : T3 dépend de T2 (topologie de nervure ∝ archétype). T5 et T6
partagent le geste « ajouter un champ au snapshot + re-bump » — **regrouper le
re-bump** si faits dans la foulée (un seul saut de version). T1, T2, T4
indépendants entre eux.

**Filet de compilation** : `dotnet build Symbiose.csproj` sur la VM après chaque
tronçon C# (le F5 visuel reste à Nico).

## Liens

- Cap pixel-art : [`CONCEPTION_RENDU_PIXELART.md`](CONCEPTION_RENDU_PIXELART.md)
  (SS② palette = fondation chromatique, SS④ plantes/organes).
- Sémiologie foliaire (modèle moteur des symptômes) :
  `CONCEPTION_SEMIOLOGIE_FOLIAIRE.md` (D33, clos).
- Sémiologie visuelle (mapping symptômes rendu) :
  [`CONCEPTION_SEMIOLOGIE_VISUELLE.md`](CONCEPTION_SEMIOLOGIE_VISUELLE.md)
  (🅿️ parké, D48).
- Dettes : D10 (discipline forme SVG→C#, dérogée ici ③), D49 (mécanique grimpe
  vrilles, pré-requis E6).
- Code touché : `visuals/PlantRenderer.Organs.cs`, `.Palette.cs`,
  `core/PlantStructure.cs` (segment `age_weeks`), pont `tools/sim_server.py`
  + `core/SimBridge.cs`.
