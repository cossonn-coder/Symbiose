# ③ Accéléré : banc + postes + suspects ; bug légende F1 — kickoff autosuffisant

## Lire d'abord
`CLAUDE.md` · `00_etat.md` · `docs/rendu/pixelart/conception_plante_assemblee.md` §2.3 + §4.2 ·
`sprints/perf/lod/sprint_perf_vue/00_etat.md` (« F5 ressenti — réponses de Nico », banc E, ④).

## Contexte chiffré
PC de Nico (i5-4200H 2 cœurs/4 fils, HD 4600) : Continu 3 s/semaine à ×8 = **5 FPS, 199 ms/image,
936 draw calls**, tick serveur 2 354 ms (s34) contre ≤ 1 495 ms au banc nominal [PC, n=1 chacun] ;
vie macro 311 entrées, 70 butineurs. Le rapport F4 n'avait PAS les postes. La VM (16 fils) ne
reproduit pas la contention de 2 cœurs : on **instrumente** pour que Nico tranche en UN run en fin
de sprint (⑦), et on corrige dès maintenant les suspects vérifiés.

## Objectif
1. **Banc accéléré** au F5 : une touche (à côté de E — vérifier les touches libres au code, cf.
   `Key.` dans `world/`) qui rejoue le cas de Nico : jardin full, semaine ~35, ×8, Continu 3 s/semaine,
   mesure 20 s, rapport **copié** comme E. Équivalent VM : `tools/perf_vm.sh -E 20 -z 8 -A 3 -W 35`
   (vérifier les options existantes, `-A` existe déjà).
2. **Postes** au rapport en accéléré : `ForagerLayer` (_Process/_Draw), application de semaine
   (étalement, par famille — existe), **réception/parse du snapshot**, GC, temps d'attente du step,
   et **classe de priorité effective** du process serveur lue après coup (`Process.PriorityClass`) —
   la ligne doit dire si `BelowNormal` tient sous Windows.
3. **`ForagerLayer`** (`visuals/ForagerLayer.cs`, `QueueRedraw()` à chaque image l.~280) : borner le
   redessin (cadence bornée, ou lot redessiné sur signal à la manière du peintre vie macro, PERF VUE ②)
   — choisir sur mesure VM du poste, aspect au F5 inchangé à l'œil (pas de saut visible).
4. **Bug légende F1** (`world/WorldView.Hud.cs` ~l.185-192) : la ligne « F3 étiquettes … I vie macro … »
   déborde en bas d'écran. Faire tenir la légende (retour à la ligne / repli / taille) sans perdre
   d'entrée ; ajouter la nouvelle touche de banc. Vérifier par capture VM avec F1 affiché.

## Vérifications
- `tools/perf_vm.sh -E 20 -z 8 -A 3` (et nominal `-E 20 -z 4`) : rapport avec les nouveaux postes,
  consigné dans `00_etat.md` [VM, n=…] ; poste `ForagerLayer` avant/après.
- Capture VM de la légende F1 entière.
- `dotnet build` vert ; golden `22768f33…` ; `Hud.cs` est à 294 LDC → si > 300, scinder (partial).

## NE PAS
Changer la cadence de simulation ni le moteur · promettre le critère accéléré sur la VM (c'est le PC
qui tranche en ⑦) · lancer `test_epaisseur_500ans`.

## Golden
Intact.
