# ① Mémoire de précuisson et palier ×32

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (ce dossier), `docs/rendu/splatting/conception_reliquats_plantes.md`
(§4), et dans `../sprint_precuisson_splats/00_etat.md` les comptes rendus ④ (chargeur
`SplatPlanches`, cache du palier courant) et ⑤ (`LireImage`).

## Objectif
À ×32 (et ×16), **toute** plante à l'écran doit être cuite, donc montrer ses pièces splat.
Aujourd'hui, une grande plante (tournesol ×32) dépasse les plafonds de `PlantBaker`. Elle
retombe alors en dessin direct, sans splats (constat vérifié par capture, conception §4).

## À faire
1. **Budget global de 1 Go** (décision E6 de Nico) sur la mémoire de précuisson : les pages
   des images cuites (`AtlasPages`, `PlantBaker.TotalBytes`) **et** les planches de codes
   chargées (`SplatPlanches`, cache du palier courant). Aujourd'hui, aucun plafond global
   n'existe. Au-delà du budget, on évince d'abord les plantes hors champ, puis les plus
   lointaines du centre de l'écran. Une plante qui ne trouve pas de place reste en dessin
   direct : c'est le repli, à journaliser.
2. **Relever `MaxSidePx` et `MaxAtlasPx`** (`visuals/PlantBaker.cs:43,46`) pour qu'un
   tournesol ×32 et un arbre adulte ×16/×32 se cuisent. Ne jamais dépasser 16 384 px par
   côté de texture (limite GPU). Si un atlas de poses ne tient pas en largeur, autoriser
   plusieurs rangées ou moins de poses. Intention : **cuire plutôt que dessiner** (E5) ; le
   placement est à choisir après lecture du code.
3. Vérifier ce que coûte le pinceau à ×32 : 729 ms pour une tomate au journal du
   2026-11-25 [n=1]. Une cuisson longue ne doit pas geler l'image : vérifier qu'elle passe
   par la file (`BakeQueue`, budget par image) et mesurer l'à-coup.
4. **Machine du F5 actuelle** (rapport perf de Nico du 2026-11-25) : i5-4200H, GPU intégré
   Intel HD 4600 (mémoire vidéo PRISE SUR LA RAM), ×1 à 30 FPS, 116 draw calls. Le budget
   de 1 Go reste la décision ; il doit être une constante unique, facile à régler, et la
   mémoire de précuisson doit apparaître dans le rapport perf (ligne `[client]` ou `[rendu]`)
   pour qu'on la lise sur ce PC comme sur le prochain (carte 8 Go probable).
5. Journaliser au F4 ou au rapport : mémoire de précuisson courante / budget, et nombre de
   plantes en repli.

## Mesures attendues (captures lues au Read)
`tools/capture_vm.sh -b planche_especes -z 32 -w 0 -n 40 -c <x,y>` (positions dans
`data/code/bancs/planche_especes.py`, `POSITIONS` : tournesol 125,1725 ; tomate 525,1725 ;
chanvre 125,1525). Il faut cadrer plus haut pour voir le feuillage d'une grande plante :
`-c 0,1550` montre le haut du tournesol. Arbre : un banc verger (`verger_floraison`) à ×16
et ×32. Avant / après : `[Splats]` présent au journal, pièces visibles, mémoire, ms par
image. Captures dans `mesures/`. Vérifier la charge (`uptime`) avant de chronométrer.

## Ne pas faire
- Toucher `data/code/` (le golden doit rester `bce813af…`).
- Dessiner les codes en direct (option écartée par E7).
- Lancer `test_epaisseur_500ans`, appeler DeepSeek.

## Fin
`dotnet build Symbiose.csproj` vert, sans avertissement. Golden intact
(`cd data/code && python3 -m tests.test_golden`). LDC via `tools/compte_ldc.py`. Compte
rendu ① dans `00_etat.md`, avec un point F5 : à ×32 sur un tournesol, les feuilles sont en
volume ; un à-coup au zoom est-il gênant ?
