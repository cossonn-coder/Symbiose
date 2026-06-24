# SPRINT RENDU FEUILLAGE — état partagé

> Conception figée : `docs/conception/CONCEPTION_RENDU_FEUILLAGE.md`.
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
| ⑤ (T5) | Croissance progressive — `age_weeks` au segment (pont), facteur `leafGrowth` | §4 | B + pont | `ENGINE_VERSION`↑ | E1 | NEUTRE (transport) | ⏳ |
| ⑥ (T6) | Chute + litière — abscission au pétiole, semis de litière typée au sol | §6 | B + pont | `ENGINE_VERSION`↑ | E5bis | NEUTRE (transport) | ⏳ |

**Dépendances** : ③ dépend de ② (topologie de nervure ∝ archétype). ⑤ et ⑥ partagent
le geste « champ au snapshot + re-bump » → **regrouper le re-bump** (un seul saut de
version si faits dans la foulée). ①, ②, ④ indépendants.

**Contrat pont au départ** : `ENGINE_VERSION = "0.5.4"`. ⑤/⑥ le bumpent.

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

Prochain tronçon = **⑤ (T5)** Croissance progressive — `age_weeks` au segment (pont,
`ENGINE_VERSION`↑), facteur `leafGrowth ∈ [0,1]` qui multiplie le rayon du limbe ET
allonge le pétiole (branchement préparé en ④), cf. doc §4. B + pont, golden NEUTRE
(transport pur). ⑤ et ⑥ partagent le re-bump → regrouper si faits dans la foulée.
