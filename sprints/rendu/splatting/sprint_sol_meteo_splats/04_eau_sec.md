# ④ Vue : eau, marais, mare, craquelé — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md` (①→③), conception §3.2 (eau, E6),
`visuals/PuddleLayer.cs` + `.Eau.cs` + `.Mare.cs` + `.Signaux.cs`, `visuals/eau_mare.gdshader`,
`visuals/TracesSolLayer.cs` (craquelé, hystérésis `SeuilApparition`), `visuals/EclaboussuresLayer.cs`,
le shader et la carte du tapis livrés au ③.
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
Ajouter au tapis : **craquelé** (plots secs), **marais** (palette tourbe), **eau de surface** dans les creux,
et brancher la **mare** sur le tapis.

## Modèle (intention)
- Craquelé : géométrie craquelé à la place de la terre sur les plots secs ; l'hystérésis actuelle
  (apparition sous `SeuilApparition`, effacement à la sortie de la liste) est conservée côté C#, la carte
  reçoit l'état déjà filtré.
- Marais : palette tourbe sur la terre, ∝ `marais`.
- Eau : `lame` → seuil par hauteur sur le ton du dessous (une lame mince = creux seulement, puis les
  creux se rejoignent) ; pixel d'eau = palette eau + reflet du ciel (nébulosité du snapshot) + liseré au
  bord ; pendant la pluie, ronds d'impact (hash, aucun `Random`). Le recalage sur le relief
  (`ReliefRiseAtPlot`) reste juste.
- Mare : `eau_mare.gdshader` garde l'eau permanente ; rive et voisins marécageux = vase/tourbe du tapis.
- Éclaboussures au sol : laissées à ⑥ (pièces cuites) ; ici seulement vérifier qu'elles restent au-dessus.
- Interrupteur : anciennes couches intactes derrière Maj+F11.

## Mesures
Captures ×0,5 → ×32 avant/après : flaque qui monte (bancs avec pluie prolongée), marais, mare, sol sec
→ craquelé → retour ; `mesures/04_*`. ms par image, draw calls.

## Ne PAS faire
Données neuves au pont ; recalculer l'hydrologie. `data/code/`, `test_epaisseur_500ans`, DeepSeek.

## F5
Flaque qui naît dans les creux puis s'étend ; reflet qui suit le ciel ; craquelé qui ne clignote pas.

## Fin
`00_etat.md`, commit `feat(tapis④) : …`.
