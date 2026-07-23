# 2026-07-23 — Sprint HYDROLOGIE DE RELIEF & MARÉCAGES — CLOS (`/sprint-auto`, ①→⑧)

**Objectif** : ajouter la dimension hydraulique **latérale** au moteur. L'eau va
des plots hauts aux bas (ruissellement), un plot saturé fait une **flaque**, une
flaque durable devient un **marécage** (état de milieu persistant → tourbe, pH
acide, niche). Guilde interconnectée (aulne, sphaigne, drosera carnivore + faune
de mare) et gestes de terrassement (`creuser`/`drainer`). Conception figée le
2026-07-03 (`docs/champs/eau/conception_hydrologie_marecage.md`).

**Ampleur** : gros, découpé en 8 tronçons perf-first (moteur ①→⑦, vue ⑧).
**Golden écolo final `57c166d8…`** (population `cc886bdd…`). Un seul re-figeage
golden, **annoncé au kickoff** (② ruissellement : l'eau circule → bilan hydrique
par plot changé) ; ③→⑧ tous NEUTRES/hors smoke. `dotnet build` vert.

## Tronçons

- **① altitude** — champ `altitude` déterministe NEUF (micro-relief topographique
  par bruit spatial, FIXE, ≠ épaisseur d'humus D57). Surface hydraulique =
  `altitude + epaisseur_sol`. Golden NEUTRE.
- **② eau_surface + ruissellement** (`284a3dc`) — champ `eau_surface` (lame de
  surface) + `tick_ruissellement` (mixin `ruissellement.py`, double-buffer
  déterministe multiple-flow ∝ pente von Neumann, exutoire aux bords,
  infiltration ∝ structure, évaporation). **Golden RE-FIGÉ LARGE annoncé.** Test
  dédié `test_ruissellement.py`.
- **③ marécage** — `marais_memory` (GridField) + **hystérèse** (entrée 0.60,
  sortie 0.30, zone morte anti-clignotement) ; effets émergents : décompo
  ralentie (anaérobie → tourbe via `tick_epaisseur`), pH tiré vers 4.5. Banc
  `tourbiere`. Golden NEUTRE (marais=0 au smoke).
- **④ faune de mare** (`a0f3674`) — moustique (proie) + libellule (prédateur)
  data-driven (`TrophicSpec`), grilles ressource/habitat sur `eau_surface`/marais,
  boom-bust décalé. 5 voix (dont page P34). Golden écolo intact, **population
  re-figée maîtrisée** (additif : densité 0 au smoke) `5824ee3f…`→`cc886bdd…`.
- **⑤ aulne + sphaigne** (`cde4d97`) — **aulne** (Betulaceae, fixe l'azote
  actinorhizien via la route générique `inject_field n`, tolérance asphyxie) ;
  **sphaigne** (Sphagnaceae NEUVE, ingénieur : acidifie + retient l'eau +
  nécromasse-tourbe quasi indécomposable via tissu `mousse` neuf). Attribut
  d'espèce `asphyxie_tolerance_base` (≠ gène per-instance). 5 voix (P35).
- **⑥ drosera carnivore** (`894422c`) — 1ᵉʳ végétal-prédateur (Droseraceae NEUVE) :
  **PUITS** `_tick_carnivore` retirant de la densité `moustique` sur ses
  `foliar_plots` + **faim d'azote neutralisée** (N retiré de Liebig dans
  `qi_local` → survit sur tourbe pauvre sans pousser plus vite). Attribut
  `carnivore` + drapeau transient `a_capture` (🪰). Concept carnet NEUF
  `carnivorie` + P36. Golden écolo/population intacts.
- **⑦ gestes creuser/drainer** (`29676c8`) — terrassement joueur (philo #1,
  coûteux Vigueur). `creuser` abaisse `altitude` d'un cran (cuvette qui capte
  l'eau au ruissellement) + perturbe le microbiome comme `becher` ; `drainer`
  vide `eau_surface` + fait reculer `marais_memory` (assèchement forcé).
  Event-driven, gaté Vigueur, `GESTES_BASE`. Pont **0.5.35**. Golden NEUTRE.
- **⑧ vue Godot** (`071dd4b`, ce session) — PUR-VUE C#. Relief extrudé sur
  `altitude + epaisseur` (`WorldView.Relief.cs`, parseur `ParseDenseGrid`
  factorisé + accesseur public `ReliefRiseAtPlot`). Calque NEUF
  `visuals/PuddleLayer.cs` : flaques bleutées translucides ∝ profondeur + voile
  de tourbe brun-noir ∝ `marais_memory`, recalés sur la surface (un CanvasItem,
  patron Couverture/Litter, LOD+culling). Faune de mare (`MacroLife`) +
  palettes d'organes aulne/sphaigne/drosera (`PlantRenderer.Organs`). Gestes
  creuser/drainer routés (kind `'q'`) + icônes. Overlays F6 dédiés
  `eau_surface`/`marais_memory`/moustique/libellule. **Pont : `eau_surface`
  enfin émis au snapshot** (était calculé mais jamais exporté — le ② l'avait cru
  en place). `dotnet build` vert.

## Constats consignés

- **`eau_surface` était un angle mort** : calculé (`eau_surface_by_tile`) depuis le
  ② mais jamais inséré au dict de sortie du snapshot → la vue ne l'aurait jamais
  reçu. Réparé au ⑧ (1 ligne additive). Rappel que le bloc « FAIT » d'un `00_etat`
  décrit l'intention, pas toujours l'état du disque — d'où la vérification.
- **Refactor auto-léger : no-op de périmètre.** Seul `world/WorldView.Actions.cs`
  dépasse 400 LDC pur (561, 🔴), mais c'est une dette **historique** (D31/D29/D55/⑦
  ont gonflé la table de routage des gestes) — l'hydrologie n'y a ajouté que 8
  lignes, elle ne l'a donc pas fait *franchir* la bande. Consigné en **D88**
  (`/refactor` ciblé : scinder par famille de geste en partials).

## Bugs préexistants NON traités (orthogonaux à l'hydrologie, à trancher hors sprint)

`test_sim_server` (dérive de chaîne `engine_version` 0.5.28 vs courant + fruits
pommier), `test_senescence` (pommier mort ~4.5 ans), `test_encyclopedie` (gestes
sans fiche), banc édaphique `carence` — tous vérifiés préexistants par `git stash`
sur les tronçons concernés.

**F5 Nico restant** : micro-relief lisible (cuvettes/bosses) ? flaques qui
brillent dans les creux ? marais qui « noircit » ? guilde
aulne/sphaigne/drosera/moustiques/libellules crédible ? gestes creuser/drainer
lisibles ? Calibrage de l'exagération de relief et des palettes.
