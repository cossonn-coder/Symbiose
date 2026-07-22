# SPRINT RENDU FEUILLAGE — état partagé

> Conception figée : `docs/rendu/feuillage/conception_rendu_feuillage.md`.
> Lancement Python depuis `data/code/`. Build C# : `dotnet build Symbiose.csproj`
> (filet de compilation ; F5 visuel = Nico).

## Objectif

Combler les trous du **rendu des feuilles** par espèce (forme, couleur, nervures,
croissance, insertion, chute) dans la continuité du pixel-art 16-bit (SS④). Couche
**B** (`visuals/PlantRenderer.*`) sauf T5/T6 qui *transportent* une donnée déjà
calculée par le moteur via le pont. **Rendu = vue passive → golden trivialement
préservé sur TOUS les tronçons** (T5/T6 inclus : transport, pas calcul).

## Périmètre — 6 exigences Nico (cf. doc §Périmètre)

- **E1** croissance progressive des feuilles (1-2 sem) · **E2** nervures couleur ≠ limbe ·
  **E3** forme **et** couleur par espèce · **E4** jamais d'aplat (≥ 2 valeurs) ·
  **E5** feuille émerge d'une branche verte (+ **E5bis** chute au pétiole, reste au sol) ·
  **E6** vrilles grimpantes → **DIFFÉRÉ, gated dette D49** (hors sprint).

## Verrous tranchés (Nico, 2026-06-24)

- **①b** croissance ancrée sur l'**âge réel du segment** (`age_weeks`), exposé au pont.
- **②b** mécanique de grimpe des vrilles = sprint moteur séparé (**D49**), hors ce sprint
  (seul le contrat de rendu est pré-cadré, §7 du doc).
- **③** forme de feuille codée **directement en C#** (dérogation assumée à D10).

## Invariants transverses (vérifiés à CHAQUE tronçon, doc §1/§8)

1. **Jamais d'aplat (E4)** : tout organe ≥ 2 valeurs (`DrawVolumeEllipse`), sauf
   mini-feuille naissante sous le **plancher de rayon** (~2-3 px, exception transitoire).
2. **Déterminisme total** : zéro `Random`, toute variation dérive d'un **hash** stable
   de l'identité du segment/organe (philo #3, condition du golden).
3. **Le bois n'est jamais teinté par le feuillage** : `WoodRamp` reste maîtresse du rendu
   des segments ; une feuille colore le limbe, pas le rameau.

## Tronçons (doc §8 — couche B pure d'abord, pont ensuite)

| # | Tronçon | § doc | Couche | Pont | Exigence | Golden | Statut |
|---|---------|-------|--------|------|----------|--------|--------|
| ① (T1) | Couleur du limbe par espèce — étendre la table `Palettes` aux cultivées | §3.1 | B pure | — | E3-couleur | NEUTRE (inchangé `2ab026ad…`) | ✅ |
| ② (T2) | Forme par espèce — `enum LeafShape`, `LeafProfile`, tracé des 6 archétypes (jitter par hash) | §2 | B pure | — | E3-forme | NEUTRE (inchangé `2ab026ad…`) | ✅ |
| ③ (T3) | Nervures = 3ᵉ valeur — topologie par archétype, sens du shift par espèce | §3.2 | B pure | — | E2 | NEUTRE (inchangé `2ab026ad…`) | ✅ |
| ④ (T4) | Insertion — verrou « feuille ⟹ vert » + pétiole vert | §5 | B pure | — | E5 | NEUTRE (inchangé `2ab026ad…`) | ✅ |
| ⑤ (T5) | Croissance progressive — `age_weeks` au segment (pont), facteur `leafGrowth` | §4 | B + pont | `ENGINE_VERSION` 0.5.4→**0.5.5** | E1 | NEUTRE (inchangé `2ab026ad…`) | ✅ |
| ⑥ (T6) | Chute + litière — abscission au pétiole, semis de litière de feuilles au sol | §6 | B + pont | `ENGINE_VERSION` 0.5.5→**0.5.6** | E5bis | NEUTRE (inchangé `2ab026ad…`) | ✅ |

**Dépendances** : ③ dépend de ② (topologie de nervure ∝ archétype). ⑤ et ⑥ partagent
le geste « champ au snapshot + re-bump » → **regrouper le re-bump** (un seul saut de
version si faits dans la foulée). ①, ②, ④ indépendants.

**Contrat pont** : `ENGINE_VERSION = "0.5.5"` depuis ⑤ (0.5.4 au départ). ⑥ le bumpera à 0.5.6.

## §REPRISE

**① (T1) CLOS** (golden inchangé `2ab026ad…`, build C# vert). La table `Palettes`
vit dans `visuals/PlantRenderer.Organs.cs` (et **non** `.Palette.cs` comme l'annonçait
le kickoff — `.Palette.cs` ne porte que le moteur hue-shift/volume). Étendue à 23
espèces : 9 cultivées potagères, 5 compagnes/mellifères, 2 aromatiques, 1 acidophile,
5 pérennes ligneuses. Clé = nom de classe Python (`species` du snapshot). Couleurs
non vérifiées au F5 (validation visuelle à venir).

**② (T2) CLOS** (golden inchangé `2ab026ad…`, build C# vert). `enum LeafShape`
(6 archétypes), `readonly record struct LeafProfile(Shape, Aspect, Count, VeinLighter)`
et la table `LeafProfiles[species]` (22 espèces) vivent dans un **partial dédié
`visuals/PlantRenderer.Leaf.cs`** (et **non** dans `Organs.cs` ni `.Palette.cs` :
`Organs.cs` était déjà à ~250 ldc avec `Palettes`, ajouter forme + tracé l'aurait
poussé hors seuil → partial autonome, namespace Symbiose). Tracé déterministe des
6 archétypes par composition de `DrawVolumeEllipse` (jitter d'angle/longueur des
lobes/folioles par `Hash01` canaux 31/37/41 → zéro Random). Plancher de rayon
`LeafFloorRadiusPx=3` (1 ellipse 1 valeur sous le seuil) + repli LOD
`CurrentZoom<4` → `Elliptique`. `Organs.cs` : l'unique `DrawVolumeEllipse` de la
boucle feuilles remplacé par `DrawLeafShape(c, rx, ry, col, i, j)`. `VeinLighter`
DÉCLARÉ, pas exploité (réservé ③). Silhouettes lobées/composées non vérifiées au F5.

**③ (T3) CLOS** (golden inchangé `2ab026ad…`, build C# vert). Les nervures vivent
dans le **même partial `visuals/PlantRenderer.Leaf.cs`** (choix signalé : +~100 ldc →
201 ldc code pur mesuré par `tools/compte_ldc.py`, SOUS le seuil 350 ; responsabilité
cohérente « silhouette + nervation »). 3ᵉ valeur posée APRÈS le volume : teinte =
`HueShift(limbe, ±VeinShift)` selon `LeafProfile.VeinLighter` (true=plus claire),
constante `VeinShift=0.22f` (ajustable F5). Tracé = `DrawVein` (lignes 1 px,
`antialiased: false`). Topologie par archétype : penninerve (médiane + 1-3 paires
latérales obliques, écartement au hash canal 43/47) pour Elliptique/Lanceolee/Cordee ;
palmée (rayons de la base, mêmes angles/jitter que `DrawLobee` canal 31) pour Lobee ;
rachis + médiane par foliole (mêmes positions que `DrawComposee` canal 41) pour
Composee ; AUCUNE pour Aciculaire. Plancher respecté : `DrawLeafShape` retourne avant
les nervures sous `LeafFloorRadiusPx`, et repli LOD (`CurrentZoom<4`) → pas de nervure
(ligne 1 px illisible de loin). `VeinLighter` enfin exploité. Pétiole (④), croissance
(⑤) intacts.

**④ (T4) CLOS** (golden inchangé `2ab026ad…`, build C# vert). Deux gestes, couche B
pure dans `visuals/PlantRenderer.Organs.cs`.

(a) **VERROU « feuille ⟹ vert »** : les deux seuils n'étaient **PAS strictement
cohérents** avant. `IsLeafy` testait `ThicknessCm ≤ LeafMaxThickCm = 1.6` ; or la
rampe `WoodRamp` (Palette.cs) quitte le vert-tendre dès `Lignification = ThicknessCm
/ LignifyFullCm = 0.5`, soit **1.5 cm**. La bande [1.5, 1.6] cm était donc feuillue
tout en commençant à olivir — violation discrète d'E5. Resserré `LeafMaxThickCm =
1.5f` (= `LignifyFullCm * 0.5`), avec commentaire WHY au cœur du code (règle de
ré-alignement si `LignifyFullCm` bouge). Apex toujours vert pur (Lignification=0).

(b) **PÉTIOLE vert** : nouvelle méthode `DrawPetiole(insert, leaf, s)` appelée dans
la boucle feuilles, AVANT le tracé du limbe (le limbe recouvre la jonction). Couleur
= `WoodRamp(Lignification(s))` = teinte verte du rameau LOCAL au point d'insertion,
**jamais brune** par l'invariant (a). Orientation = vecteur insert→leaf (= déport
`LeafOffsetCm`, axe rameau → extérieur). Largeur 1 px (<zoom 4) ou 2 px (≥4), non
antialiasé. Trait jusqu'à 75 % vers le limbe (la base reste visible). **Point de
rupture de l'abscission (⑥)**. Pleine taille en attendant ⑤ : branchement `leafGrowth`
préparé (commentaire = interpoler `petTip` par le facteur) mais NON pré-implémenté.

Taille `Organs.cs` ≈ 260 ldc code pur (`tools/compte_ldc.py`), sous le seuil 350.
Croissance (⑤) et chute (⑥) intactes. F5 non vérifié (validation visuelle Nico).

**⑤ (T5) CLOS** (golden inchangé `2ab026ad…`, build C# vert, `ENGINE_VERSION` 0.5.4
→ **0.5.5**). **Premier tronçon au pont — transport PUR confirmé** (golden NEUTRE).

PONT : aucune écriture moteur, et **aucune ligne de sérialisation Python ajoutée** —
`age_weeks` était DÉJÀ émis par `Segment.to_dict()` (`plants/base/stades.py`) dans
`structure_to_dict()` (snapshot, `serialize.py`). Le travail pont = (a) bump
`ENGINE_VERSION` 0.5.5 (commentaire dans `version.py`) ; (b) côté C#, `record struct
Segment` (`core/PlantStructure.cs`) gagne `int AgeWeeks` + `ParseSegment` le LIT
TOLÉRAMMENT (`ContainsKey` → 0 par défaut, flux muet géré). Le smoke pont
`tests/simserver/structures.py` figeait l'attendu de version à `"0.5.0"` (jamais
re-bumpé depuis !) → corrigé à `"0.5.5"`. NB outil : `tools/export_structure.py`
(maquette `structure.json`, sœur du pont) construisait le segment À LA MAIN sans
`age_weeks` → ajouté aussi (sinon feuilles invisibles dans l'aperçu SVG/maquette).

RENDU (couche B, `visuals/PlantRenderer.Organs.cs`) : constante `LeafMaturityWeeks =
1.5f` + helper `LeafGrowthFactor(s) = clamp(AgeWeeks/maturité,0,1)` adouci en ease-out
quadratique `t*(2-t)`. Le rayon du limbe `r` est multiplié par `leafGrowth` ; le centre
`c` du limbe est interpolé `insert.Lerp(c, leafGrowth)` (le limbe colle au rameau à
l'émergence, s'écarte en grandissant) → le pétiole (④) s'allonge de pair (branchement
préparé en ④, désormais câblé). Synergie plancher §1 : age≈0 → rayon < plancher → 1
valeur nue sans nervure ; en grandissant franchit le plancher → volume puis nervures.
Pas de pop-in (§4.3) : segment établi (age ≥ 2 sem) → leafGrowth = 1, feuilles pleines.

⚠️ Smoke pont = **184/185** : la SEULE rouge restante (« pommier pré-âgé a noué des
fruits @ S52 », `tests/simserver/morts.py`) **PRÉ-EXISTE** ce tronçon (vérifié par
`git stash` : déjà rouge sans mes changements) — sans lien avec le transport `age_weeks`,
à traiter hors ce sprint.

Point F5 (à valider Nico) : la jeune feuille grandit visiblement sur ~1,5 sem sans
pop-in ; pétiole qui s'allonge avec ; segments établis pleins d'emblée au chargement.

**⑥ (T6) CLOS** (golden inchangé `2ab026ad…`, build C# vert, smoke pont 185/186 —
seule rouge = pommier @S52 préexistante, hors périmètre ; `ENGINE_VERSION` 0.5.5 →
**0.5.6**). **Dernier tronçon du sprint — transport PUR confirmé** (golden NEUTRE).

PONT (déjà posé par le sous-agent précédent, conservé) : `tools/simserver/serialize.py`
— le bloc `litiere` par plot gagne un 5ᵉ champ → `[r, c, tissu_dominant, masse,
age_sem]`. `age_sem` = âge moyen pondéré par la masse des parcelles de SURFACE (proxy
d'état de décompo, donnée déjà calculée `Parcelle.age_sem`) → TRANSPORT pur. `version.py`
bumpé 0.5.6 (+ doc). Tests `tests/simserver/litiere.py` + `structures.py` (attendu
version `"0.5.6"`) ajustés.

PRIMITIVE DE RENDU (déjà posée, conservée) : `visuals/PlantRenderer.Leaf.cs` — méthode
PUBLIQUE `DrawLitterLeaf(species, c, rx, ry, col, seed)` + refactor `DrawShapeBySpecies`
(cœur commun feuille vivante + litière). L'espèce d'origine N'EST PAS traçable côté
moteur → repli `Elliptique` assumé (§6.3).

CALQUE MONDE (NEUF, ce qui MANQUAIT) : **`visuals/LeafLitterLayer.cs`** — calque batché
qui AFFICHE la litière de feuilles. Choix de conception : le calque **HÉRITE de
`PlantRenderer`** et s'en sert comme « stylo » (les primitives de tracé d'une feuille
sont des méthodes d'instance de CanvasItem, valides seulement dans `_Draw`). On
neutralise les deux gestes « plante vivante » du parent : `_Ready` (ombre-capsule) →
no-op, `_Draw` (exige `_structure`) → remplacé par le semis de litière. `_structure`
reste null (jamais lu : `DrawLitterLeaf` prend l'espèce en argument). Le calque lit le
bloc `litiere`, ne retient QUE le tissu dominant `"feuille"` (les autres restent à
`LitterLayer`), pose un semis déterministe (hash djb2 du plot, zéro Random) de
silhouettes : **POSE À PLAT** (ry = rx × 0.45, calotte aplatie, ≥ 2 valeurs §1),
**TEINTE morte** brun-roux `FreshLeaf` → **dérive vers l'humus** `HumusLeaf` ∝
`age_sem` (Lerp sur `AgeFullDecompSem=12 sem`), **QUANTITÉ bornée** ∝ masse (1→6
feuilles, `MasseRef=2.5`). LOD `MinZoom=2` (aligné LitterLayer). Lecture TOLÉRANTE du
5ᵉ champ (snapshot pré-0.5.6 → âge 0).

CÂBLAGE `WorldView` : `world/WorldView.Compost.cs` — champ `_leafLitterLayer`,
instancié dans `BuildLitterLayer` (APRÈS LitterLayer, même bande ZIndex 1 → feuilles
par-dessus les amas terreux), nourri dans `ApplyLitiere` (les deux layers lisent le
MÊME bloc).

CASSURE AU PÉTIOLE (§6.2) — **vérifié OK, rien à implémenter** : le pétiole vert (④)
est dessiné UNIQUEMENT dans la boucle feuilles de `Organs.cs` ; une feuille qui
disparaît de `_structure` (feuillage baissé) emporte son pétiole avec elle. Et la
teinte du pétiole = `WoodRamp(Lignification)` est verte par l'invariant (a) de ④
(`LeafMaxThickCm = LignifyFullCm·0.5`) → **jamais de moignon brun proéminent**. La
matière « réapparaît » au sol via le bloc `litiere` (conservation moteur), pas une
trajectoire (§6.1).

Point F5 ⑥ (à valider Nico) : feuilles mortes brun-roux semées au sol sur les
parcelles à litière de feuilles, posées à plat, qui s'assombrissent/désaturent vers
l'humus à mesure que `age_sem` monte ; cassure nette au pétiole (pas de moignon brun) ;
densité ∝ masse de litière. Repli Elliptique assumé (pas de silhouette d'espèce, le
moteur ne trace pas l'espèce de la nécromasse).

Point F5 ⑤ (toujours à valider Nico) : la jeune feuille grandit visiblement sur
~1,5 sem sans pop-in ; pétiole qui s'allonge avec ; segments établis pleins d'emblée.

---

## ✅ SPRINT RENDU FEUILLAGE — CLOS le 2026-06-24

**6 tronçons ①→⑥ tous CLOS.** Le rendu des feuilles par espèce est complet : forme,
couleur, nervures, croissance, insertion, chute + litière.

- **Golden** : inchangé `2ab026ad2b3f484777a2a29f804e1a4785ecffd6976fc0058fe0a33dd1498646`
  sur TOUT le sprint (couche B = vue passive ; ⑤ et ⑥ = transport pont pur).
- **Pont** : `ENGINE_VERSION` 0.5.4 → **0.5.6** (deux entorses couche B, transport de
  données déjà calculées) : ⑤ `age_weeks` au segment (0.5.5), ⑥ `age_sem` au bloc
  `litiere` (0.5.6, 5ᵉ champ).
- **Smoke pont** : 185/186 (seule rouge = « pommier pré-âgé noue des fruits @ S52 »,
  `tests/simserver/morts.py`, PRÉEXISTANTE et hors périmètre).
- **Build C#** : vert (0 avertissement, 0 erreur).
- **Knobs F5** (couche B, ajustables à la validation visuelle Nico) :
  - ① `Palettes` (Organs.cs) — couleurs du limbe par espèce (23 espèces).
  - ② `LeafProfiles` (Leaf.cs) — forme par espèce ; `LeafFloorRadiusPx=3`,
    `LeafShapeMinZoom=4`.
  - ③ `VeinShift=0.22` — amplitude de teinte des nervures.
  - ④ `LeafMaxThickCm=1.5` (= `LignifyFullCm·0.5`) — seuil feuille⟹vert + pétiole.
  - ⑤ `LeafMaturityWeeks=1.5` — durée de croissance d'une jeune feuille.
  - ⑥ `LeafRadiusPx=5`, `FlatRatio=0.45`, `AgeFullDecompSem=12`, `MasseRef=2.5`,
    `Min/MaxLeaves=1/6`, `FreshLeaf/HumusLeaf`, `MinZoom=2` (LeafLitterLayer.cs).
- **E6 (vrilles grimpantes)** : DIFFÉRÉ, dette **D49** (sprint moteur séparé) — hors
  périmètre, seul le contrat de rendu est pré-cadré (doc §7).
- **Fichiers du sprint** : `visuals/PlantRenderer.Leaf.cs` (②③⑥-primitive),
  `visuals/PlantRenderer.Organs.cs` (①④⑤), `visuals/LeafLitterLayer.cs` (⑥-calque NEUF),
  `world/WorldView.Compost.cs` (⑥-câblage), `tools/simserver/serialize.py` +
  `version.py` (⑤⑥-pont), `tests/simserver/{litiere,structures}.py` (⑤⑥-attendus).
