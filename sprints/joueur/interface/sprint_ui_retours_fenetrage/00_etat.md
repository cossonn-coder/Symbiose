# Sprint « retours UI/HUD post-fenêtrage » — état vivant

**Type/thème :** `joueur/interface` (même que le sprint fenêtrage).
**Nature :** pure VUE C#/Godot, SAUF l'item 4 (lecture d'état moteur + éventuel ajout selon fork Q1).
**Golden attendu :** INCHANGÉ partout (au pire, ajout de champs de sérialisation = snapshot, hors golden ; ou nouvel état moteur défaut-inerte si fork B → golden NEUTRE annoncé).
**Statut :** ✅ FIGÉ 2026-07-23 (Phase A close, arbitrages D1-D5). Doc :
`docs/joueur/interface/conception_retours_ui_fenetrage.md`. Kickoffs : 01_palette ·
02_chrome_navigation · 03_dossier_plante. PRÊT pour `/sprint-auto`. Reste F5 Nico.

## Origine — 5 retours de Nico
1. Palette de gestes gérable comme les panneaux : masquer les non débloqués, plafond 10 (touches 0-9), édition clic droit.
2. Enlever le texte du bas de la simu → dans le HUD.
3. Launcher pleine hauteur (jusqu'en bas d'écran).
4. Clic sur une plante → son historique (outil de TEST).
5. Depuis la simu, revenir à l'écran d'accueil (launcher).

## Constats de CODE (lus le 2026-07-23, vérité terrain)
- **Item 1** — `world/WorldView.Palette.cs` lit DÉJÀ `gestes_debloques` (snapshot) et
  **GRISE** les verrouillés (choix assumé « plus pédagogique », ligne 109 : « passer
  à Visible=false pour masquer »). `Gestes[]` (`WorldView.Actions.cs:27`) = **~28
  entrées**. Accélérateurs = **1..9** (9 touches), pas 0-9. AUCUN modèle de slot,
  AUCUNE édition. Palette = colonne verticale gauche (10,150), CanvasLayer Layer 6.
- **Item 2** — le « texte du bas » = le `Label legend` (`WorldView.Hud.cs:155`),
  aide-mémoire clavier `PROVISOIRE`, pleine largeur à `y=1080-96`, **recouvre le bas
  du champ de jeu**. DÉJÀ enfant du CanvasLayer HUD → « mettre dans le HUD » = le
  SORTIR DU CHAMP (le HUD chrome haut-gauche est déjà pris : clock/action/field/perf/genes).
- **Item 3** — `world/WorldView.Selecteur.cs:103` : `UiScroll.Envelopper(_liste, 360f)`
  plafonne à 360 px. Panneau ancré TopLeft (16,16). Relever le plafond = trivial.
- **Item 4** — PAS d'historique chronologique par plante. `plants/base/instance.py`
  porte des **mémoires SCALAIRES intégrées** (shade/drought/asphyxie/cold/infection/
  wind/root_herbivory/stress_memory ∈ [0,1]) + `vitalite`/`etat` + `expression`
  (plasticité) + `symptom_marks` + stade/âge/`genes`. Pas d'ID unique ; identité =
  clé spatiale `tile|species|x|y` (déjà clé de diff du snapshot). Le SEUL chrono =
  `sim/journal.py` : ledger `{semaine, zone=(tile,r,c), kind, cause, espece}`,
  **par joueur, OPT-IN, borné 200, dérivé du log texte** — donc SPATIAL, pas par
  instance (plusieurs plantes/plot → attribution ambiguë). Snapshot
  (`tools/simserver/serialize.py`) expose déjà species/name/stage_name/vitalite/etat/
  genes/symptoms/segments ; PAS les mémoires ni l'expression. Picking `FindPlant(pos,r)`
  existe (réutilisé par étiquettes/survol gènes F7).
- **Item 5** — launcher = `CanvasLayer _selecteur` **DÉTRUIT** (`QueueFree`) au
  « Lancer » (`Selecteur.cs:169`), puis `StartSimulation` monte ~20 couches sous
  `_worldVp`/WorldView. `_ExitTree` (`WorldView.cs:372`) ferme proprement le pont
  (`_bridge.Quit`). → `GetTree().ReloadCurrentScene()` redémarre TOUT (pont neuf +
  `BuildSelecteur`) sans démontage manuel. Contexte banc/test = abandon d'état OK
  (auto-save = passage de saison seulement ; bancs rejouables).

## Fork central à trancher (item 4) — voir Q1
- **A — Dossier INSTANTANÉ (état, pas chrono).** Panneau au clic = état physiologique
  courant : stade/âge, vitalité/état, symptômes actifs, gènes, expression plastique,
  mémoires scalaires. Read-only. Coût = ajouter qq champs au snapshot (mémoires +
  expression + âge) = golden NEUTRE. HONNÊTE (pas de fausse chronologie ; les mémoires
  SONT l'histoire compressée : shade_memory=0.8 = « longtemps à l'ombre »). RECO.
- **B — Vrai LOG chronologique par instance.** Ajout moteur : chaque plante consigne
  des événements horodatés (naissance, changement de stade, pics de stress, apparition
  de symptôme, floraison, dégâts). Coût MÉMOIRE par plante en run éternel → bornage
  fenêtre glissante. Golden NEUTRE si défaut-inerte. Sprint plus lourd, recoupe
  `journal.py`. À ne prendre que si Nico veut une vraie timeline.
- **C — Hybride via journal.py spatial.** Filtrer les entrées zone==plot de la plante.
  Fragile (multi-plantes/plot ambigu, opt-in joueur, granularité log texte). Écarté sauf avis contraire.

## Décisions arrêtées (lot 1, 2026-07-23 — réponses Nico)
- **D1 (item 4) = FORK A, dossier INSTANTANÉ.** Pas de log chronologique moteur. Le
  clic ouvre un panneau lisant l'état physiologique courant de la plante pointée
  (stade/âge, vitalité/état, symptômes actifs, gènes, expression plastique, mémoires
  scalaires). Read-only. Les mémoires = l'« histoire compressée ». Rationale : honnête,
  quasi gratuit, sert le besoin de diagnostic F5 sans fausse timeline.
- **D2 (item 1) = masquer les non débloqués** (renverse le grisé actuel). **Modèle
  SLOT : cap 10, touches 1..9 + 0** (10 slots). **Auto-remplissage** dans l'ordre de
  `Gestes[]` parmi les débloqués ; un geste débloqué **au-delà du 10e n'apparaît pas**
  tant qu'il n'est pas assigné à un slot par **clic droit** (menu : assigner un
  débloqué non-encore-slotté / vider le slot). **Persistance GLOBALE** (`user://`,
  survit au retour accueil). Rationale : simple, prévisible, pas de layout qui bouge seul.
- **D3 (item 2) = legend ESCAMOTABLE, touche F1, MASQUÉE par défaut** (champ dégagé,
  D54-a). Sortie du bas du champ de jeu.
- **D4 (item 5) = Échap → retour accueil IMMÉDIAT** via `GetTree().ReloadCurrentScene()`,
  **sans confirmation** (bancs rejouables, abandon assumé). Précédence : si un panneau
  (Consultation/Voix) est ouvert, Échap le ferme d'abord ; sinon → accueil.
- **D5 (item 3) = launcher pleine hauteur** : plafond `UiScroll.Envelopper` relevé à
  la hauteur d'écran − marges/widgets. Trivial, sans arbitrage.

## Défauts d'implémentation tranchés seul (senior defaults)
- Touche F1 libre (toggles pris : F3/F4/F6/F7, H, I, O, M, G, A, C, S, B, N). Échap =
  `ui_cancel`, à gérer dans `_UnhandledInput` avec la précédence D4.
- Item 4 : le dossier lit le **dict plante du DERNIER snapshot** (pas de nouvel appel
  pont) via `FindPlant()` (picking existant). Le pont ajoute au snapshot : mémoires
  (7 + stress) + `expression` + `age_weeks`/`age_years` (species/état/genes/symptoms
  déjà présents). Golden NEUTRE (snapshot hors `test_golden`). Panneau debug (rang F6/F7),
  hors HUD de découverte (philo #5). Bump pont annoncé.

## Découpage FIGÉ — 3 tronçons (perf-first, golden intact ; dernier = vue+pont)
- **T1 — Palette gérable (item 1).** `WorldView.Palette.cs` + `WorldView.Controls.cs`
  (remap slots 1..9+0) + petit store de prefs `user://`. Masquer + modèle slot +
  auto-remplissage/débordement invisible + édition clic droit + persistance globale.
  Pure vue, golden INTACT.
- **T2 — Chrome & navigation (items 2, 3, 5).** `WorldView.Hud.cs` (legend → overlay
  F1 masqué) + `WorldView.Selecteur.cs`/`UiScroll` (pleine hauteur) + `WorldView.Controls.cs`
  (Échap → `ReloadCurrentScene`, précédence panneaux). Pure vue, golden INTACT.
- **T3 — Dossier de plante au clic (item 4), VUE+PONT.** `tools/simserver/serialize.py`
  (champs mémoires+expression+âge, bump version) + panneau debug C# (clic `FindPlant`
  → lit le dict du dernier snapshot). Golden NEUTRE annoncé (snapshot). Dernier tronçon = vue+pont.

## Avancement T1 — Palette gérable (item 1) — FAIT le 2026-07-23
- **Modèle SLOT (D2) livré, pure vue C#.** `_slots[10]` (index de geste ou -1),
  masquage des non débloqués (plus de grisé), auto-remplissage dans l'ordre de
  `Gestes[]` parmi les débloqués, débordement invisible au-delà du 10ᵉ.
- **Touches 1..9 + 0** → slots 0..8 puis 9 (`SelectSlot`, PhysicalKeycode AZERTY-safe) ;
  **Tab** cycle les slots OCCUPÉS (`CycleSlots`, remplace `CyclePalette` supprimé).
- **Édition clic droit** : `GesteIcon._GuiInput` capte le bouton droit → `OnRightClick` →
  `PopupMenu` (vider ce slot / assigner un débloqué absent). Assignation/vidage
  reconstruit + persiste.
- **Persistance GLOBALE par VERBE** : nouveau `world/PaletteLayout.cs` (`user://palette.json`,
  {slots:[verbes]}). Chargée au montage, complétée par auto-remplissage. Verbe
  inconnu/non débloqué ignoré (purgé au 1er snapshot). AUCUNE collision avec
  `player.palette.macros` du serveur (ApplyPalette ne lit que `macros`).
- **Golden INCHANGÉ** : `57c166d8…` (aucune touche `data/code/`). **Build C# VERT**
  (0 warning / 0 erreur). LDC : Palette.cs 189 🟢, PaletteLayout.cs 35 🟢,
  GesteIcon.cs 235 🟢 ; Actions.cs 554 (⚠ pré-existant, réduit de 7 par la suppression
  de CyclePalette — dette antérieure, hors T1).
- **Fichiers touchés** : `world/WorldView.Palette.cs` (réécrit, modèle slot),
  `world/PaletteLayout.cs` (NEUF, persistance), `world/GesteIcon.cs` (+clic droit),
  `world/WorldView.Controls.cs` (remap 1..9+0 → slots, Tab → CycleSlots),
  `world/WorldView.Actions.cs` (CyclePalette retiré au profit de CycleSlots).
- **Points F5 Nico** : (a) HUD action (`WorldView.Hud.cs:223`) affiche encore
  `[{_gesteIndex+1}]` = index de geste, PAS le n° de slot → indice de touche trompeur ;
  laissé pour T2 (chrome HUD). (b) « vider un slot » n'est durable que jusqu'au
  prochain déblocage (l'auto-remplissage recomble alors le trou, conforme au kickoff) —
  à calibrer si gênant. (c) Menu clic droit positionné à droite de l'icône.
- **Reste T2** (chrome/navigation) **et T3** (dossier plante, vue+pont).

## Avancement T2 — Chrome & navigation (items 2, 3, 5) — FAIT le 2026-07-23
- **Item 2 (D3) — légende clavier escamotable.** `WorldView.Hud.cs` : le `Label
  legend` passe `Visible = false` par défaut (champ de jeu dégagé) et est mémorisé
  dans `_legendLabel` ; nouvelle méthode `ToggleLegend()`. Toggle **F1** câblé dans
  `WorldView.Controls.cs` (touche libre — non prise). Texte inchangé (D54-a = plus tard).
- **Item 3 (D5) — launcher pleine hauteur.** `WorldView.Selecteur.cs` : plafond de
  `UiScroll.Envelopper` relevé de 360 px à `1080 − 16 − 16 − 220 ≈ 832 px` (const
  locale `hauteurListe`, écran − marges − widgets fixes). Comportement « défile si
  débordement » conservé (`UiScroll` inchangé).
- **Item 5 (D4) — Échap → retour accueil, avec précédence.** `WorldView.Controls.cs`,
  dans `_UnhandledInput` (déjà gardé par `_started` → jamais pendant le sélecteur) :
  `Key.Escape` → si `_consultation` ouvert (`!= null && IsInstanceValid`) le ferme
  (`Fermer()`) et s'arrête ; sinon `GetTree().ReloadCurrentScene()` (pont refermé
  proprement par `_ExitTree`, sélecteur reconstruit). Pas de confirmation.
- **Cohérence T1 préservée** : slots 1..9+0 et Tab intacts ; F1 ajouté au `switch`
  sans collision ; Échap géré AVANT le `switch` (return, ne perturbe pas les slots).
- **Golden INCHANGÉ** : `57c166d8…` (aucune touche `data/code/`). **Build C# VERT**
  (0 warning / 0 erreur).
- **Fichiers touchés** : `world/WorldView.Hud.cs` (legend masquée + `_legendLabel`
  + `ToggleLegend`), `world/WorldView.Controls.cs` (F1 → ToggleLegend ; Échap →
  précédence panneau/ReloadCurrentScene), `world/WorldView.Selecteur.cs` (hauteur liste).
- **Points F5 Nico** : (a) F1 affiche/masque l'aide clavier, champ dégagé par défaut ;
  (b) launcher descend jusqu'en bas et défile si trop d'entrées ; (c) Échap en jeu →
  accueil (nouveau pont, nouveau choix de monde) ; Échap panneau ouvert → ferme le
  panneau seulement.
- **Reste T3** (dossier plante au clic, vue+pont).

## Avancement T3 — Dossier de plante au clic (item 4), VUE+PONT — FAIT le 2026-07-23
- **PONT (`data/code/tools/simserver/serialize.py`)** — dans la sérialisation par
  plante VIVANTE (après `base["etat"]`), TROIS ajouts lecture-seule : `memoires`
  (dict des 8 intégrateurs — shade/drought/asphyxie/cold/infection/wind/
  root_herbivory/stress, arrondis 3 déc.), `expression` (dict des facteurs de
  plasticité ≠ 1.0, filtré — vide pour une plante non acclimatée), `age_weeks`
  (int) + `age_years` (round 2). Noms d'attributs VÉRIFIÉS dans
  `plants/base/instance.py` (dataclass `PlantInstance`). Hors `_PLANT_ATTRS`.
- **Version pont bumpée `0.5.37 → 0.5.38`** (`version.py`, changelog ajouté).
- **VUE C#** — mode INSPECTION debug touche **F2** (registre F6/F7) : tant qu'il
  est ON, le clic gauche ouvre le dossier de la plante pointée (picking `FindPlant`)
  au lieu d'exécuter un geste. Source = dict du DERNIER snapshot (cache
  `_plantPayloads` clé `tile|species|x|y` == `PlantKey`, rempli dans `ApplySnapshot`),
  AUCUN appel pont. Panneau `world/DossierPlantePanel.cs` (`CanvasLayer` Layer 9,
  read-only) : espèce/nom · tuile+plot(x,y) · stade+âge · vitalité/état · symptômes ·
  mémoires (non nulles) · expression · gènes. Fermable : clic ailleurs / **Échap**
  (inséré dans la précédence T2 : dossier → consultation → retour accueil) / F2 off.
- **Golden INCHANGÉ** : `57c166d8…` (les ajouts pont sont hors `_PLANT_ATTRS`, le
  golden tourne hors serveur). **Build C# VERT** (0 warning / 0 erreur).
- **LDC** : `DossierPlantePanel.cs` 114 🟢, `WorldView.Dossier.cs` 45 🟢.
- **Fichiers touchés** : `serialize.py` (3 champs), `version.py` (bump 0.5.38),
  `world/DossierPlantePanel.cs` (NEUF, panneau), `world/WorldView.Dossier.cs` (NEUF,
  wiring mode inspection + cache + précédence Échap), `world/WorldView.Controls.cs`
  (F2 → ToggleInspectMode ; clic → InspecterAuClic prioritaire ; Échap → dossier
  d'abord), `world/WorldView.Snapshot.cs` (remplissage `_plantPayloads`).
- **Points F5 Nico** : (a) F2 arme le mode inspection (message console), clic sur une
  plante → panneau tiers-droit avec son état complet ; clic dans le vide referme.
  (b) Une plante stressée montre des mémoires élevées (ombre/soif…) cohérentes avec
  l'observation. (c) Échap ferme le dossier avant de fermer un panneau, puis avant le
  retour accueil (précédence T2 respectée). (d) Le panneau absorbe les clics sur sa
  propre surface (Panel MouseFilter Stop) → aucun geste parasite dessous.

## §REPRISE
Lire `CLAUDE.md` + ce fichier. Phase A CLOSE (D1-D5). **T1 + T2 + T3 TOUS FAITS**
(golden `57c166d8…` intact, pont bumpé **0.5.38**, build vert, non commités — Nico
commit). Les 3 tronçons du sprint sont livrés. **Reste = clôture (Phase C)** : MAJ
DETTE (D54/D55/D59)/BACKLOG/journal + F5 Nico. Aucun dev restant.
