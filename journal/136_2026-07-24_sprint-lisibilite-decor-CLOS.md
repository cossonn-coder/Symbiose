# 2026-07-24 — Sprint LISIBILITÉ DÉCOR (reprise D58 / D83) — CLOS

**Type/thème :** rendu / ambiance · **Mode :** `/sprint-auto` (T1→T4) · **Dette soldée :** D83

Reprise du rendu du **décor de pourtour** « éclaté au sol » (forêt / rivière /
falaise) jugé « pas du tout ressemblant » au F5 (D83). **Retour de qualité, pas
un bug** : le diagnostic de conception avait confirmé que le décor s'affiche bien
(`DrawEllipse` natif Godot 4.6, LOD zoom ≤ 4) — le problème était le **rendu**
(contraste feuillage↔sol quasi nul, aucun volume/ombre portée). Reprise ciblée,
**procédurale peinte** (pas de sprites — déterminisme #3, perf, cohérence avec
tous les placeholders procéduraux). Cap qualité = maison normande (ombre portée
+ marches de valeur franches + face verticale).

## Nature du sprint — pure vue C#, golden jamais touché

Les 4 tronçons ne touchent **aucun fichier moteur** (`data/code/`). Le golden
`57c166d8…` est **trivialement inchangé** ; `test_golden` n'a pas été lancé
(conforme au kickoff, philo #3 non concernée). Filet de compilation :
`dotnet build Symbiose.csproj` = **vert** partout. Tous les fichiers touchés
restent 🟢 (LDC pur ≤ 289).

## Tronçons

- **T1 — Forêt volumée** (`3a1960e`, `visuals/DecorLayer.Arbres.cs` +
  `Palette16.cs`). LE gros gain. Marches de valeur franches dans `DrawVolumeBlob`
  (masse ×0.75 / calotte éclairée ×1.25, calotte décalée SO écran) au lieu de
  ±15 % timides. **Ombre portée** aplatie au pied de chaque arbre
  (`DrawOmbrePied`, teinte fond −0.30, décalage NE) peinte avant le houppier → la
  masse se décolle du sol. **Silhouette de cime** claire (`DrawCimeAccent` +
  nouveau `DecorForetCime`) → skyline bosselée forêt contre jardin. Palette forêt
  ré-étalée : fond froid sombre (`223a2b`), 4 feuillages en valeurs distinctes
  (hêtre `35603a`, chêne `44703f`, charme `4f7d47`, bouleau `74a250`) pour
  trancher feuillage↔sol. Contrainte notée : `Assombrir` plafonne à ×1.25 →
  l'accent de cime est une **vraie couleur claire** (`DecorForetCime`), pas un
  sur-éclaircissement.
- **T2 — Rivière creusée** (`b877e43`, `DecorLayer.cs` `DrawRiviere` +
  `Palette16.cs`). Berges franches de galets (`BergeGalet`) sur chaque rive ;
  surface d'eau en **damier hashé 2 valeurs** (`EauProfonde`/`EauSurface`) ;
  **ombre de berge** liserée creusant le lit ; **reflets en streaks** `DrawLine`
  orientés le long de la tangente du courant (remplacent les cercles 2 px
  sous-pixel morts au dézoom). Helper `Bande(…)` factorisé.
- **T3 — Falaise qui surplombe** (`d33a1f7`, `DecorLayer.cs` `DrawFalaise` +
  `Palette16.cs`). Vraie **face verticale** montée en −Y écran (patron `upWall`
  de la maison), **stratifiée en 3 valeurs** de roche selon la pente
  (Douce/Verticale/Déversante) ; **plateau végétalisé** (`DecorRocheHaut`
  herbeux) coiffant la paroi et reculant en profondeur ; **ombre portée au pied**
  côté jardin (le surplomb) ; **éboulis** hashés. **Falaise NON forcée** (D-c,
  philo #7) — `BuildProfile` intouché. Décision assumée non littérale au kickoff :
  redans (3 valeurs) placés sur la face verticale en strates et sommet rendu
  végétalisé — plus fidèle à un vrai ressaut rocheux.
- **T4 — Transitions / LOD / banc F5** (`7bad9cc`, `DecorLayer.cs` +
  `DecorLayer.Arbres.cs` + **nouveau** `DecorLayer.Banc.cs` +
  `world/WorldView.Controls.cs` + doc). **Lisière nette** côté décor sur les 4
  motifs (`DrawSecteur`, seuil sombre franc). **LOD détail 2 niveaux**
  (`DetailsVisibles`, `DetailZoom=2f`) : masse toujours dessinée, détails fins
  (reflets rivière, éboulis, fleurs prairie, chevrons bouleau) seulement à
  zoom ≥ ×2 — corrige l'incohérence détail/distance (détails 1.5-2 px invisibles
  à zoom 0.5). **Banc F5 = toggle F10** (partial `DecorLayer.Banc.cs`, off par
  défaut) forçant forêt N / rivière E / falaise S / prairie O. Le partial a
  maintenu `DecorLayer.cs` sous 300 LDC malgré T2+T3+T4 cumulés.

## Découverte T4 → dette D92

Le **banc-par-seed** prévu par le kickoff s'est révélé **impossible**. Dans
`BuildProfile`, les 4 côtés d'un même seed dérivent d'un hash `decor|seed|cote`
qui ne diffère **que du dernier caractère** (0..3) → le djb2-xor ne brasse que
les bits bas → les 4 tirages `%100` tombent quasi identiques → un terrain porte
presque toujours un **anneau uniforme** d'un seul motif. La falaise (qui exige
une rivière clockwise-adjacente à une prairie) ne réunit **jamais** ses
conditions : **0 falaise sur 300 000 seeds** (vérifié par réplication Python du
hash). D'où le choix du **toggle F10** (même objectif : exposer les 4 motifs pour
F5) et l'ouverture de la dette **D92** (« décorréler `BuildProfile` ») — corriger
la distribution par défaut déborde T4 (change la distribution, philo #7 à
respecter).

## Bilan

- **Golden `57c166d8…` jamais touché** (pure vue C#, zéro moteur), `dotnet build`
  vert partout, tous fichiers 🟢 (`DecorLayer.cs` 289 LDC pur). Refactor
  auto-léger non requis.
- Dette **D83 → ✅ CLOS** ; **D92** ouverte (BuildProfile).
- **Reste F5 Nico** : validation visuelle des 4 tronçons + banc F10 (F10 → les 4
  motifs se lisent d'un regard, démarqués du jardin, détails nets à zoom ≥ ×2,
  masse lisible au dézoom).
