# ④ Paliers hauts ×4 → ×32 dans la même grammaire

Lire d'abord : `CLAUDE.md`, `00_etat.md` (§Notes ① et ③ — l'encodage indexé choisi),
`docs/rendu/pixelart/etude_brief_da_16bits.md` (§ Anatomie : arbre de jour, buisson, fleurs,
lierre), `docs/rendu/pixelart/conception_casse_ecran.md` §2 point 1 et §4.
**Golden intact.** Filet : `dotnet build Symbiose.csproj`. Pas d'appel DeepSeek.
Ne JAMAIS lancer `test_epaisseur_500ans`.

## Problème (D112 i, m)
Le ×2 paraît plus beau que le ×4 parce que ce sont **deux moteurs** : ×0,5→×2 = touffes
estampillées (`PlantRenderer.Kit.cs`, `Paliers.cs`) ; ×4→×32 = segments + organes
(`PlantRenderer.PaliersHauts.cs`, `Leaf.cs`, `LeafOutline.cs`, `Organs.cs`, `Assemblee.cs`).

## Objectif
Une seule grammaire : la **même recette** (rampe, motif, squelette, accent, ancrage) à tous
les paliers. Le squelette reste la structure procédurale du moteur (segments, organes) ; à
×4+ on **estampille des motifs** (feuille ≈ 3×4 px logiques, au moins 4 orientations au
hash, brin, grain) le long de ce squelette, en plus grand nombre et plus petits
relativement à la plante à mesure qu'on zoome. « Partir du complet, retirer en dézoomant » :
le ×32 montre le plus de motifs ; chaque palier plus large en retire, la silhouette et les
masses de valeur restant les mêmes (vérifiable : la planche L floutée doit se ressembler
d'un palier à l'autre). Troncs : stries verticales sur 2-3 tons, empattement de racines en
éventail, halo d'ancrage dithéré (brief). Fleurs = taches de couleur pure, contour teinté.
Même encodage indexé que ③ → éclat côté soleil gratuit.

## Perf-first
Risque principal du sprint (nombre de motifs à ×16/×32). Estampiller **à la cuisson**, une
fois, dans les pages d'atlas (`AtlasPages.cs`, plantes « prêtes par palier » du sprint
LEVIERS) — jamais par frame. Mesurer au banc E et à l'outil d'à-coup de zoom (touche Z,
`world/WorldView.ZoomJournal.cs`, `tools/perf_vm.sh -Z`) avant / après. Budget frame ≤ +10 %,
pire à-coup de cran pas pire qu'avant. Si ×16/×32 explosent : livrer ×4/×8 d'abord
(④a), consigner ×16/×32 en ④b dans `00_etat.md` et le faire dans le même tronçon si le
budget le permet, sinon s'arrêter proprement.

## Validation
Banc ① sur la planche ×2/×4/×8/×16/×32 : mêmes critères qu'en ③ + **continuité** ×2→×4
(distance entre la planche ×4 réduite à la taille du ×2 et la planche ×2 : doit baisser
nettement par rapport à la mesure de base ①). Lire les captures avec Read.

## Ne PAS faire
Changer la forme des plantes côté moteur ; viser la ressemblance botanique exacte (acceptée
comme future par Nico) ; toucher `data/code/`.

## Fin de tronçon
`00_etat.md` §Notes ④ (mesures, perf, ④b éventuel) ; commit. F5 Nico : zoomer de ×2 à ×32
sur un pommier et une touffe — « même plante, plus de détails ».
