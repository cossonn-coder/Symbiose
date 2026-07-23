# Tronçon ② — Vue Godot : recalibrage du rendu ligneux + banc F5

> Kickoff **autosuffisant**. Lis `CLAUDE.md`, `00_etat.md` (même dossier) et ce
> fichier. Doc de référence :
> `docs/vegetal/croissance/conception_lisibilite_ligneuse.md`. Ce tronçon suppose
> le tronçon ① fait (nouveau modèle d'épaisseur `thickness_cm` côté moteur).

## Contexte
Le tronçon ① a changé l'**échelle** de `thickness_cm` : le bois s'amincit du tronc
(épais, borné par `girth_max_cm`) vers les brindilles (fines). Les valeurs
absolues d'épaisseur ne sont plus celles de l'ancienne accumulation uniforme. Le
rendu C# lit `thickness_cm` à deux endroits qu'il faut **recalibrer** contre la
nouvelle échelle.

## Objectif
Que la silhouette du **vieux pommier** en jeu se lise comme un arbre : tronc épais
net, charpentières marquées, brindilles fines et feuillues. Golden **intact**
(pur-vue C#, `dotnet build Symbiose.csproj` = filet de compilation ; F5 = Nico).

## Fichiers à toucher (C#)

### 1. Largeur de trait — `visuals/PlantRenderer.cs`
- Deux sites : ~l.452 et ~l.505 : `w = max(1, round(thickness_cm · PxPerCmX ·
  2.2))`. Le facteur `2.2` était calibré pour l'ancienne échelle (tronc pouvant
  atteindre ~120 cm). Avec le nouveau `girth_max_cm` (~18 cm pour le pommier), le
  tronc rendrait beaucoup plus fin — **recalibrer** le facteur pour que le tronc
  ait une largeur de trait lisible (quelques px à ×8) et que les brindilles
  restent à ~1 px. Garde le `max(1, …)` (une brindille ne disparaît pas). Centralise
  le facteur en constante nommée si les deux sites doivent rester cohérents.

### 2. Seuil feuilles — `visuals/PlantRenderer.Organs.cs`
- `LeafMaxThickCm = 1.5f` (l.26) : un segment `Thickness ≤ LeafMaxThickCm` porte
  des feuilles (l.201). Sous le nouveau modèle, les brindilles sont fines
  (~`THICKNESS_INIT` + un peu) et le bois structurel épaissit — **recaler**
  `LeafMaxThickCm` pour que brindilles/rameaux restent feuillus et que
  tronc/charpentières soient nus. Aligne la valeur sur ce que ① a posé côté
  maquette (`LEAF_MAX_THICK_CM` de `tools/maquette/organes.py`, noté dans
  `00_etat.md`).
- **NB couleur** : la lignification (vert→brun) est pilotée par l'**âge**
  (`LignifyFullWeeks`, `PlantRenderer.Palette.cs`), **pas** par l'épaisseur → ne
  PAS y toucher. Le commentaire d'en-tête d'`Organs.cs` (l.19-25) décrit encore
  l'ancien lien épaisseur↔lignification : le **corriger** pour refléter que le
  seuil feuilles est désormais calé sur l'échelle de `girth_max`, pas sur
  `LignifyFullCm`.

### 3. Pont / snapshot
- Aucun changement de protocole attendu : `thickness_cm` transite déjà (mirroir
  `Segment.ThicknessCm`, `core/PlantStructure.cs`). Vérifier qu'aucune valeur
  n'est clampée/scalée en dur côté pont sur l'ancienne échelle ; sinon ajuster.
  **Ne PAS bump le protocole** si le contrat de champ est inchangé.

## Banc F5
- Fournir un **banc d'observation** « vieux pommier » : un pommier vieilli
  (plusieurs décennies simulées) isolé, cadré pour juger la silhouette (tronc /
  charpentières / brindilles / feuillage). Réutiliser le mécanisme de bancs F5
  existant (cf. bancs précédents `floraison_saisons`, `grimpantes` — chercher le
  point d'entrée des bancs côté `data/code/bancs/` et/ou un flag de scène Godot).
  But : Nico juge à l'œil et calibre `TAPER_EXP`, `GIRTH_TAU`, `girth_max_cm`
  (moteur, ①) + le facteur de largeur (②).

## Complément narratif (optionnel, non bloquant)
Si utile, un complément d'**encyclopédie** sur le port de l'arbre âgé (tronc
dégagé, charpentières, houppier) — voix « naturaliste ». Le pommier existe déjà,
donc **aucune** voix nouvelle obligatoire ; ne l'ajouter que si ça sert la
lecture. Ne pas bloquer le tronçon dessus.

## Golden
**INTACT** — ce tronçon ne touche que le rendu C# et des complements narratifs,
jamais le moteur. Si un hash bouge, c'est une erreur → annuler. `dotnet build
Symbiose.csproj` doit rester vert.

## À NE PAS faire
- Ne PAS re-changer le modèle d'épaisseur moteur (c'est ①).
- Ne PAS toucher à la lignification age-based (couleur du bois).
- Ne PAS bump le protocole du pont sans nécessité de champ.

## Fin de tronçon
Mettre à jour `00_etat.md` (valeurs de calibrage rendu posées, points F5 pour
Nico), commit. Sprint clos → journal + dette.
