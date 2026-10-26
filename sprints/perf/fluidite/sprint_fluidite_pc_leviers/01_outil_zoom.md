# ① Outil « à-coup de zoom » + balayage VM

**Golden** : intact (`fecccded…`, vue C# seule). **Build** : `dotnet build Symbiose.csproj` vert.

## Objectif
Nico sent un à-coup à chaque changement de zoom et demande un outil qui l'extrait pendant
qu'il zoome / dézoome. Cet outil sert aussi de mesure aux tronçons ② ③.

## À faire
1. **Journal par changement de palier** (dans la vue, partial neuf de `WorldView` du type
   `WorldView.ZoomJournal.cs`) : à chaque palier changé, consigner palier avant → après,
   puis sur la fenêtre suivante (~1 s ou ~30 images) : pire image (ms), somme des images,
   nombre d'images > 33 / > 100 ms, coût du redessin du décor (le `[DecorLayer] _Draw` existe
   déjà en console — le capter plutôt que le recalculer), nombre de plantes invalidées et
   longueur de la file de cuisson au départ / quand elle se vide, postes `PerfPostes` de la
   pire image. Garder les N derniers changements (borné).
2. **Rapport copiable** : une touche LIBRE (vérifier dans `world/WorldView.Controls.cs` ; F8
   ou Maj+une lettre semblent libres — à confirmer) copie au presse-papier un texte du même
   style que le rapport perf (`CopyPerfReport`), une ligne par changement + une synthèse
   par paire de paliers (pire, médiane). Ligne d'aide dans le HUD Aide (F1) si la convention
   l'exige.
3. **Balayage scripté** en capture VM : nouvel argument (style `--capture-*` existant dans
   `world/WorldView.Capture.cs` / `tools/capture_vm.sh`) qui enchaîne ×0,5 → ×32 → ×0,5 avec
   un temps de repos par palier, puis imprime le rapport sur stdout.
4. Mesurer sur VM (graine 1521550718, monde `full`, une semaine d'été an 2 type s90) et
   consigner le tableau « avant » dans `00_etat.md` : c'est la référence des tronçons ② ③.

## Ne PAS faire
Corriger les à-coups (c'est ③). Toucher au moteur Python. Ouvrir une dette.

## F5 Nico
Zoomer / dézoomer quelques fois, presser la touche, coller le rapport.
