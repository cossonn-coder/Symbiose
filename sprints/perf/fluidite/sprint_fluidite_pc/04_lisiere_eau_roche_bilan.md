# ④ Lisière en DA SNES : rivière + falaise, puis bilan et protocole PC

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (atlas du ③), `docs/perf/fluidite/conception_fluidite_pc.md`.
**Golden** : intact (vue C# seule).

## Objectif
Finir la lisière dans le style du ③ (pièces patchwork, niveau de détail ×1 / ×0,5) pour les
deux motifs restants, puis clore le sprint avec un protocole PC d'**un seul run**.

## À faire
1. **Rivière** (`DrawRiviere`, à déplacer dans un partial neuf, ex. `DecorLayer.Eau.cs`) :
   eau en rampe de bleus avec reflets, berges en pièces (galets, roseaux, herbe de berge), lit
   piloté par la ligne d'eau du pont (endiguer / dériver). **Scintillement de l'eau admis**
   (seule animation, signal DA) : le faire SANS redessiner tout le décor à chaque image
   (nœud ou couche séparée à fréquence basse, ou shader), coût mesuré.
2. **Falaise** (`DrawFalaise`, partial neuf, ex. `DecorLayer.Roche.cs`) : strates de roche en
   pièces, face claire / face d'ombre selon l'orientation, contours, éboulis au pied piloté
   par l'entaille du pont (`EntailleRefCm`), 3 pentes (douce / verticale / déversante).
3. **Contrôle visuel** : captures VM du banc 4 motifs (argument de capture du ③) à ×0,5 / ×1 /
   ×2 ; les juger. Chemins dans `00_etat.md`.
4. **Bilan perf VM** : banc 3 phases du ① (`-A 1 -W 90 -S 1521550718`, n ≥ 2 runs) : vérifier
   que la lisière n'a pas fait monter draw calls / rendu CPU (A↔avant ③) ; tableau dans
   `00_etat.md` avec limites entre crochets.
5. **Protocole PC pour Nico** dans `00_etat.md` (§F5) — **un seul run** : `git pull`, Main Run
   Args exacts du banc 3 phases (an 2, sem. 90, graine 1521550718, `full`, 1 s/sem), F5, coller
   le rapport, vider Main Run Args (ne pas committer `project.godot`). Puis ressenti : F5
   normal, la lisière au démarrage sans F10, « c'est mieux ? ».
6. **Clôture** : `DETTE.md` — D112 (c)(j) fermées (ou réduites à ce qui reste), D116 mise à jour
   (« diagnostic instrumenté, attend le run PC → 2ᵉ `/conception D116` ») ; `BACKLOG.md` ;
   entrée `journal/` + index `journal.md`.

## Ne PAS faire
- Leviers de cadence (2ᵉ conception). Ombre de lisière sur le jardin. Toucher le moteur.
- Lancer `test_epaisseur_500ans`.

## Fin de tronçon
`dotnet build` vert ; golden intact ; LDC ≤ 300 par fichier ; `00_etat.md` §REPRISE = « sprint
clos, attendre le rapport PC » ; commit.
