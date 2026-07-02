# ⑥ UI Godot — encyclopédie 7 onglets + hover carpophore (D60)

> Kickoff autosuffisant. Reprise à froid : `CLAUDE.md` + `00_etat.md` + ce fichier.
> Dépend de ①–⑤ (backend unifié taggué + corpus complets). Golden **NEUTRE** (C#
> pur). **Point F5** (rendu Godot).

## Objectif
Rendre l'encyclopédie **multi-règnes filtrable** : 7 onglets (plante · animal ·
champignon · concept · technique · outil · geste) dans `EncyclopediePanel`, et
finaliser le **hover carpophore** (survol → observation champignon, si pas déjà
posé en ②). C'est le tronçon qui rend visible tout le travail backend.

## Contexte C# actuel
`world/EncyclopediePanel.cs` (spécialise `VoicePanel`) :
- `AfficherIndex()` : lit `Bridge.Encyclopedie()` → `index` (AUJOURD'HUI liste de
  strings ; APRÈS ① = **liste de dicts** `{cle, type, titre}`), un bouton par
  entrée. → à réécrire pour grouper/filtrer par type.
- `AfficherFiche(espece)` : lit `Bridge.Encyclopedie(espece)` → `fiche`
  `{espece, niveau_max, niveaux}`, rend N1..niveau_max verbatim. → à étendre pour
  les fiches **mono-niveau avec graphe** (animal/champignon : champ
  `interconnexions`).
- `core/SimBridge.cs:Encyclopedie(string espece=null)` — étendre pour passer un
  **filtre type** optionnel (`Encyclopedie(type: …)` ou un 2ᵉ appel) correspondant
  au `msg.type` de `cmd_encyclopedie` (①).

## À faire
- **MODIFIER `world/EncyclopediePanel.cs`** :
  - Barre de **7 onglets** (boutons de filtre) en tête. Chaque onglet filtre
    l'index par `type` (soit via `Bridge.Encyclopedie(type)`, soit en filtrant
    localement la liste tagguée — préférer le filtre pont pour rester « Godot
    bête »). Onglet actif = surbrillance ; défaut = plante (ou « tout »).
  - Index : bouton par entrée du type courant, libellé = `titre`. Vide → message
    neutre « (rien de découvert dans cette catégorie) ».
  - Fiche : dispatcher selon `type` de la réponse :
    - plante / concept / technique / outil / geste → rendu N1..niveau_max EXISTANT ;
    - animal / champignon → **mono-niveau** : blurb (N1) + une section
      « Interconnexions » listant `fiche.interconnexions` (le graphe de
      `faune_encyclo`/`champignon_encyclo`). Pas de N2/N3 (cap palier 1).
  - ⚠️ `TitresNiveau` reste pour les types 3-niveaux ; pour animal/champignon,
    titre de section « Interconnexions » (pas « N2 — Biologie »).
  - Garder l'invariant « Godot bête » : tout le TEXTE vient verbatim du pont ; le
    C# ne fabrique aucune phrase, il met en page (onglets, sections, graphe).
- **MODIFIER `core/SimBridge.cs`** : surcharge/param pour le filtre type + s'assurer
  que `Encyclopedie(cle)` lit la fiche par clé (le champ peut rester `espece` côté
  protocole pour compat — cf. ①).
- **hover carpophore** (si non fait en ②) : `visuals/CarpophoreLayer.cs` +
  `world/WorldView.Observation.cs` → survol d'un carpophore émet
  `Observer("champignon")`. Réutiliser le pattern de dédup.

## Ce qu'il NE faut PAS faire
- Ne PAS fabriquer de texte côté C# (verbatim pont uniquement).
- Ne PAS inventer de niveaux pour les fiches mono (animal/champignon).
- Ne PAS toucher au moteur / golden (C# = vue).
- Ne PAS ajouter d'onglet hors des 7 (taxonomie figée QA).

## Golden / build
NEUTRE (C# pur). `dotnet build Symbiose.csproj` doit passer (filet de compilation ;
⚠️ ① a pu laisser `EncyclopediePanel` cassé sur la forme de l'index — c'est ICI
qu'on répare). Le F5 visuel reste à Nico.

## Points F5 (Nico, sur Godot)
- Ouvrir l'encyclopédie (hub maison) : 7 onglets présents.
- Survoler puceron / coccinelle / abeille (zoom ≥ 4×) → apparaît sous
  animal (fiche blurb + interconnexions).
- Survoler un carpophore → onglet champignon (fiche générique).
- Utiliser des gestes (arroser, planter…) → apparaissent sous geste/outil/
  technique ; répéter → niveaux N2/N3 se débloquent (progression ③).
- Vérifier qu'un règne non encore découvert affiche le message neutre.
