# Intégration Godot — avancement archivé : tranches 4 à 6

> Historique détaillé des tranches **closes** 4 (caméra D35 + actions joueur +
> ombre solaire + perfs), 5 (taille au segment près), 6 (organes + vie macro +
> heatmaps debug). Extrait de `00_etat.md` au Sprint refactor global (SS①,
> 2026-06-15). Amont : `_avancement_t1_t3.md`. État actif : `00_etat.md`.

## Avancement (tranches 4-6)

### Tranche 4 — volet A (caméra D35) : ✅ CLOS (2026-06-11, confirmé F5)
- **Livré** : `world/WorldView.cs` + `visuals/PlantRenderer.cs`. Caméra
  jouable : **pan flèches** (vitesse px écran, bornée monde + marge 10 %),
  **zoom molette** par paliers {0.5, 1, 2, 4, 8, 16, 32} centré souris
  (paliers < 4 provisoires, cf. kickoff), **rotation PageUp/PageDown** par
  quarts de tour (`_orientation` dans `WorldToScreen` + `RebuildWorld()` ;
  variante **`WorldToScreenOffset`** point/vecteur pour les offsets plante —
  le phototropisme penche vers le même point monde à toute orientation).
  **Légende des commandes** au HUD (bas-gauche). **D35 levée.**
- **Retours Nico (1er F5 t4) intégrés** : toit **pyramidal** 4 pans + façades
  teintées côté MONDE (soleil au sud — la maison tourne visiblement) ;
  **boussole** N/S/E/O au sol ; **étiquettes** espèce·stade sous chaque
  plante (toggle **F3**) ; **maison transparente** (toggle **H**) ; **modes
  simu** (touche **M**) : Saison / Continu / Turbo ; **ombres placeholder**
  (maison vers le nord, disque au pied des plantes) ; sens de rotation =
  caméra orbite à droite sur PageUp.
- **Retour Nico (2e F5, 2026-06-11) — triage** :
  - **Ombre solaire animée** (direction/longueur selon heure du jour et
    saison, au lieu du nord fixe) : le modèle existe déjà côté moteur
    (`fields/light.py:solar_slice`, azimut+élévation astronomiques). Décision
    Nico : **après le volet B** (volet C de cette tranche ou t5) — portage
    de la formule côté vue, balayage de l'arc solaire pendant la semaine
    vécue (le moteur n'a pas de notion de jour : 1 semaine vécue ≈ 1 journée
    visuelle, fidèle au modèle, zéro Python touché).
  - **Étiquette au survol uniquement** (pas toutes à la fois) : intégrée au
    **volet B** — premier consommateur du picking `ScreenToWorld`.
  - **Plusieurs plantes par plot** : limite réelle du MOTEUR
    (`sim/succession.py` : « Plot déjà occupé → pas de germination ») →
    **sprint Python dédié** gravé au backlog (compétition intra-plot).
  - **Plantes mortes visibles + décomposition** : moteur aussi → **sprint
    « décomposition & compost »** gravé au backlog.
### Tranche 4 — volet B (actions joueur) : CODÉ (2026-06-11), en attente F5
- **Livré Python** : `sim_server.py` protocole **v1** (`ENGINE_VERSION
  0.2.0`) — `ensure_player` à l'init (le tick moteur fait seul régen+refill,
  hook existant `engine.py:774` gardé par `"vigueur" in game_state`) ; bloc
  `player {vigueur, vigueur_max}` au snapshot ; commande **`action`**
  (verbe+target+params → `result` ACK/NAK + **snapshot frais joint**).
  Désignations : plante PAR POSITION (±0,1 cm, `PLANT_EPSILON_CM`), plot
  `(tile,r,c)` borné, tuile, rien. Refus métier = `ok:true` +
  `applied:false` + message (le `ok:false` reste aux commandes malformées).
  Le serveur appelle les façades `sim/actions.py` SANS réimplémenter de
  règle (coût×maîtrise×urgence, effets — tout côté moteur).
- **Tests** : `test_sim_server.py` **47/47** (bloc player, régen +10/sem via
  tick, refill plein à la semaine 14, manger/deraciner par position +
  disparition dans le snapshot JOINT, URGENCE_MULT 15→22,5 visible, refus
  verbe inconnu/cible introuvable/plot hors tuile/Vigueur insuffisante avec
  serveur survivant, déterminisme 2 runs MÊMES actions byte-identiques).
  **Golden écolo intact** (`16a1b937…`, vérifié).
- **Livré C#** : `SimBridge.Action(verb, target, params)` (réponse complète
  result+snapshot) ; `WorldView.cs` — **`ScreenToWorld`** (inverse analytique
  + orientation défaite dans l'ordre inverse, à côté de l'aller, leçon D2) ;
  touches **1..8 en `PhysicalKeycode`** (AZERTY : la rangée chiffres émet
  `&é"'(…` en Keycode) dans l'ordre de la table `COUTS` ; clic gauche →
  désignation par famille de cible (plante ≤ 30 cm monde, plot/tuile par
  containment, grelinette sans cible) → action en **Task** (pipe
  maître/esclave : UNE requête en vol, step OU action ; clic ignoré sinon ;
  `_ExitTree` attend les deux) ; `tailler` Maj+clic = branche ; `ecraser`
  `urgence` = phase Saison (Pause = tarif planification, temps figé) ; HUD
  2ᵉ ligne « Vigueur x/y — geste : … » + dernier message, flash rouge sur
  refus ; **étiquette AU SURVOL** (F3 cycle survol/toutes/aucune, défaut
  survol — demande Nico 2e F5) via le même `FindPlant` que le clic ; légende
  enrichie gestes 1..8.
- **1er F5 Nico (2026-06-11)** : actions ✓, refus/flash ✓, survol ✓. Retour
  triagé + correctifs :
  - **Turbo affamait les clics** (pipe jamais libre) → **file d'UNE
    intention** : clic mémorisé (le dernier gagne), part en priorité dès que
    le pipe se libère, avant la semaine suivante.
  - **« tailler ne montre rien »** : la coupe est réelle et immédiate
    (prouvé : 6→5 segments dans le snapshot joint) mais invisible sur de
    jeunes sujets → **flash jaune de la plante ciblée** à chaque geste
    réussi (après ApplySnapshot — pas de conflit avec le fondu de mort).
  - **Messages instructifs serveur** : `manger` affiche le gain
    (« +4.1 Vigueur — gain ∝ maturité ») ; `ecraser` affiche
    « ravageurs 0.80 → 0.60 » (lecture pure du champ — les sprites = t5).
  - **Pas des bugs (design expliqué)** : régen = +10/semaine SIMULÉE (rien
    en Planification, temps figé — la « méditation au foyer » comblera) ;
    manger à 0 Vigueur fonctionne (coût nul, gain ∝ maturité — un semis ne
    nourrit pas) ; spam manger = D19 (déplétion d'organe, déjà gravé) ;
    ombre disque uniforme = placeholder → volet C.
- **Décisions Nico (2026-06-11)** : ordre de fin de tranche = **volet C
  (ombre solaire animée) PUIS volet D (taille au segment près à la souris)**.
  Volet D pré-étudié : moteur prêt (`atteindre_segment(seg_id)`), il faudra
  étendre la façade `tailler` de `sim/actions.py` (couche joueur, golden
  écolo intact), le protocole (`target.segment`), et le hit-test/surbrillance
  des segments côté vue.
- **2e F5 Nico (2026-06-11) : correctifs volet B VALIDÉS** (« ok c'est
  bon ») → **volet B CLOS, commit 48f1bdd**.

### Tranche 4 — volet C (ombre solaire animée) : CODÉ (2026-06-11), en attente F5
- **Livré (C# seul, zéro Python)** : `WorldView.cs` — portage de
  `fields/light.py:solar_slice` (latitude 49°N, déclinaison saisonnière
  ±23,4°, lever/coucher astronomiques `cos H = −tan φ·tan δ`) ; la **jauge
  intra-semaine devient l'heure du jour** (1 semaine vécue ≈ 1 journée
  visuelle, du lever au coucher) ; statiques partagées `SunShadowDir` /
  `SunInvTan` (borné 3,5× la hauteur) / `SunStrength` ; Planification/
  Turbo → midi figé, Pause → ombre figée (accumulateur gelé) ; **early-out
  < 2°** (≈ 1 redraw/s à 60 s/sem, ~15/s en debug 3 s). Ombre MAISON =
  enveloppe convexe monde (empreinte + coins déplacés + faîte,
  `Geometry2D.ConvexHull`) re-projetée — survit à la rotation D35. Alpha ∝
  force solaire (soleil bas = ombre pâle et longue). `PlantRenderer.cs` —
  le disque devient une **ombre-capsule** (disque glissé le long de la
  direction sur hauteur × 1/tan(élévation)) = le modèle EXACT des
  ombres-capsules du moteur ; `_heightCm` calculé au `SetStructure`.
- **Valeurs attendues** (vérifiées sur le `solar_slice` Python) : hiver
  jour court ±60°, ombre midi 3,15×h ; été ±120°, midi 0,48×h, ombres du
  soir pointant légèrement SUD (soleil levé au nord-est — réalisme
  gratuit). Les saisons se lisent à l'œil.
- **F5 Nico (2026-06-11) : volet C VALIDÉ, 5/5 critères** (balayage,
  saisons contrastées, pause/planification, rotation, maison transparente
  qui ombre toujours). Témoin de build vu et adopté. Au passage Nico a
  observé les ombres SUD des matins/soirs d'été — réel (azimut du lever
  `cos A = sin δ/cos φ` → lever au NE à δ=+23,4°), pédagogie donnée.
- **Idée design Nico consignée (2026-06-11)** : un événement météo se
  représentera comme l'ombre — déroulé sur la SEMAINE vécue (pluie, vent,
  gel), même granularité hebdo que le moteur, et son impact (humidité,
  température, ombrage, vent) suivra le même patron visuel. À reprendre au
  sprint rendu météo (cf. `CONCEPTION_METEO.md`).

### Tranche 4 — volet C2 (perf ombres + mesures) : CODÉ (2026-06-11), F5 rapide à faire
- **Retour perf Nico** : « plus la simulation avance plus l'ombre ralentit
  le jeu ». Cause racine : le balayage solaire faisait `QueueRedraw` sur la
  PLANTE entière (tous segments, ~15×/s en debug). Livré :
  - **Ombre = nœud enfant `PlantShadow`** (`ShowBehindParent`) : le soleil
    ne redessine QUE les ombres (1 petit polygone chacune), plus jamais les
    segments — le coût ne grandit plus avec l'âge des plantes.
  - **Touche O** : coupe toutes les ombres (`WorldView.ShadowsOn`,
    `_Draw` no-op + `UpdateSun` endormi = coût strictement nul).
  - **Touche F4 — overlay de perfs** (demande Nico) : FPS, durée du dernier
    tick complet (pipe+sim+parse), cadence réelle s/semaine (+ jours
    simulés/s), plantes (+pousses), segments, état ombres, zoom. Mesuré
    côté vue, moteur non instrumenté.
  - Témoin de build → **« t4·C2 ombres O + perfs F4 — 2026-06-11 »**.
- **TRANCHE 4 CLOSE après ce F5** (volets A, B, C, C2). La taille au
  segment près (ex-volet D) devient la **tranche 5 — kickoff PRÊT :
  `05_taille_segment.md`** (façade `tailler(segment_id)` + protocole
  `target.segment` + hit-test/surbrillance). Après t5 : t6 = organes +
  overlays + vie macro (kickoff `06_*.md` à écrire).
- **Workflow acté (2026-06-11, cf. mémoire feedback-format)** : un retour
  Nico sur livrable → tri en sprint indépendant ou dette + clôture
  facilitée du sprint en cours (pas de dev immédiat) — appliqué ici même.

### Tranche 5 — taille au segment près (souris) : CODÉE (2026-06-11), en attente F5
- **Livré Python (commit 5b8d793)** : `sim/actions.py:tailler` accepte
  `segment_id` keyword — valide (existe, pas le collet) → REMPLACE le
  sélecteur `_segment_cible`, sinon comportement t4 inchangé (compat prouvée :
  `test_vigueur` 110/110 et `test_croissance` 67/67 SANS modification) ; coût/
  gain identiques (on ne tarife pas la précision). `sim_server.py` protocole
  **0.2.1** : `target.segment` optionnel sur `tailler` (= index dans
  `segments` du snapshot, ordre `structure_to_dict()` stable), validé AVANT
  la façade — hors bornes / collet / non entier = refus métier à **coût
  NUL** ; message « taillé (segment i) ». `test_sim_server.py` **58/58**
  (le snapshot joint perd EXACTEMENT le sous-arbre ciblé — vérifié via les
  champs `parent`, repli `params.cible` intact, serveur survivant).
  **Golden écolo intact** (`16a1b937…`).
- **Livré C#** : `PlantRenderer.cs` — propriété `HighlightSegment` (setter
  early-out : écrite chaque frame, redraw seulement au CHANGEMENT ; remise à
  −1 à chaque `SetStructure`, les index changent à chaque snapshot) ;
  `FindSegmentNear(canvasPos, maxPx)` = distance point-segment via la MÊME
  géométrie que le dessin (Iso, leçon D2) — **segment 0 (collet) exclu** :
  clic au pied → repli t4, jamais un refus surprise ; surbrillance jaune
  clair (la couleur du flash de geste réussi — un seul langage visuel)
  dessinée par-dessus le bois. `WorldView.cs` — `UpdateTailleHighlight()`
  chaque frame en mode tailler (même résolution que le clic : ce qui est
  surligné = ce qui part) ; tolérance **8 px ÉCRAN** à tout zoom
  (divisée par le palier) ; clic → `target.segment` si une branche est
  trouvée, `params.cible` toujours joint en repli ; légende mise à jour.
  Témoin de build → **« t5 taille au segment — 2026-06-11 »**.
- **Critères F5** (kickoff `05_taille_segment.md`) : surbrillance suit la
  souris en mode 7 ; clic → CETTE branche + sous-arbre disparaissent, flash
  jaune ; clic au pied = comportement t4 ; segment disparu entre temps →
  refus propre.
- **1er F5 Nico (2026-06-11) : 3/3 critères validés.** Retours triagés :
  - **« Les segments qui dépassent le carré de départ ne peuvent pas être
    taillés »** → défaut du livrable (le filtre par collet à 30 cm excluait
    la couronne débordante d'un arbre) → **correctif t5·B (C# seul)** :
    `FindSegmentGlobal` cherche LA branche sous la souris chez TOUTES les
    plantes (préfiltre `PickExtentCm` = 1,5×(étalement+hauteur) — la hauteur
    compte car la souris est re-projetée au sol z=0), survol ET clic ; sans
    branche sous le curseur, repli collet 30 cm = t4. `FindSegmentNear`
    renvoie aussi la distance (comparaison entre plantes). Build témoin →
    **« t5·B portée de taille — 2026-06-11 »**. En attente F5.
  - **« Taillée, la plante devrait repousser à deux têtes (hors
    monocotylédones) »** → **le moteur le fait DÉJÀ** (vérifié par
    expérience, 2026-06-11) : tomate écimée semaine 9 → **2 apex** dès le
    tick suivant (témoin : 1 apex), émergent du débourrement §D.3 (bourgeons
    sous le seuil d'auxine une fois l'apex dominant coupé — rien de codé en
    dur, philo #2). Les monocotylédones (graminées) sont insensibles par
    construction (profil d'espèce, CONCEPTION_CROISSANCE). Les nouvelles
    têtes font quelques cm la 1ʳᵉ semaine — probablement invisibles au
    moment du F5 ; à ré-observer sur 2-3 semaines simulées. Si le port
    « touffu » reste jugé trop timide à l'usage → sprint CALIBRAGE moteur
    (AUXIN_INHIB_THRESHOLD / dominance), pas de mécanique manquante.
- **CLAUDE.md rafraîchi** (demande Nico, même date) : tranches 1-5 closes,
  prochaine = t6, D1–D35, rappel DebugSecondsPerWeek.
- **2e F5 Nico (2026-06-11) : correctif t5·B validé (« ok c'est bon ») →
  TRANCHE 5 CLOSE.** Prochaine : **tranche 6 (organes + vie macro + overlays
  debug), kickoff PRÊT `06_organes_overlays_viemacro.md`** — dernière tranche
  de contenu avant t7 = packaging.

### Tranche 6 — volet A (organes procéduraux) : CODÉ (2026-06-11), en attente F5
- **Livré Python** : `sim_server.py` protocole **0.2.2** — 3 hints par plante
  au snapshot (lecture seule, kickoff §1) : `foliage_density`
  (`foliage_density_at(plant, saison)`, déjà saisonnier — caduc hiver = 0),
  `organ` (proxy saisonnier `REPRO_BY_SEASON` **importée de
  `tools.render_structure`** — outil→outil, zéro duplication ; espèce absente
  → repli `DEFAULT_REPRO` : fleur printemps, fruit mûr été/automne, rien
  l'hiver), `organ_site` (profil d'espèce). Moteur JAMAIS touché.
  `test_sim_server.py` **68/68** (section 9 : hints présents/bornés, printemps
  = flower partout, été = pommier `fruit_unripe` ≠ tomate `fruit_ripe`
  (cycles distincts, critère F5), hiver = organ null partout + pommier caduc
  densité 0). **Golden écolo intact** (`16a1b937…`). Mesure : hints ≈ +60
  o/plante comme prévu (snapshot smoke sem 40 : ~39 Ko / 23 plantes).
- **Livré C#** : `PlantStructure.cs` — 3 champs DTO (lecture TOLÉRANTE,
  défauts si snapshot pré-0.2.2 ; `organ` null JSON → "" = rien) ;
  `PlantRenderer.cs` — portage de `_draw_organs` : feuilles (segments apex ou
  ≤ 1,6 cm, 1/11 cm, déport 7 cm au hash, ellipse-polygone 10 pts, opacité
  0,92, **sous-échantillonnage au hash si densité < 1** — ajout kickoff vs
  prototype), couleur palette espèce × saison (printemps ×1,25, automne
  AUTUMN_LEAVES au hash, hiver ×0,7 persistants), fleurs 5 pétales + cœur /
  fruits disque + reflet aux bouts d'apex (`terminal`) ou latéraux hors
  meneur (`lateral`), plafond 10 ; **hash C# local** (mix entier xorshift,
  stable inter-frames/sessions, zéro Random — pas de parité bit-à-bit avec le
  SVG, assumé kickoff). Dessin dans `DrawSegments` APRÈS le bois, AVANT la
  surbrillance t5 ; redraw **uniquement au SetStructure** (leçon perf C2).
  `WorldView.cs` — statique `CurrentSeason` (assigné dans ApplySnapshot AVANT
  les SetStructure), témoin de build → **« t6·A organes procéduraux —
  2026-06-11 »**.
- **Signalé (design, pas bug)** : le proxy saisonnier fleurit TOUTE plante à
  apex, même une pousse d'une semaine (fidèle au prototype SVG — le vrai état
  reproducteur = D19/D33). Si le F5 juge ça gênant : filtre par stade = 1
  ligne côté serveur, à trancher.
- **F5 Nico (2026-06-12) : volet A VALIDÉ** → enchaînement direct volet B.

### Tranche 6 — volet B (vie macro visible) : CODÉ (2026-06-12), en attente F5
- **Livré Python** : `sim_server.py` protocole **0.2.3** — bloc `sprites` au
  snapshot : par tuile et par guilde, tableaux **COMPACTS**
  `[r, c, x_frac, y_frac, activite]` issus de `sample_sprites` (échantillonnage
  CÔTÉ SERVEUR, fonction PURE de `fields/population.py` — la vue n'a pas besoin
  de `_hash_noise`). Arrondis déterministes (x/y 3 déc. = 0,05 cm, activité 2).
  **Compact d'emblée, tranché à la MESURE** (kickoff §4 : mesurer avant
  d'optimiser) : pic d'automne du monde full ≈ **8 600 sprites** → 705 Ko en
  format objet verbeux vs **210 Ko** en tableaux (smoke : 173 sprites sem 20,
  snapshot total 24 Ko). Moteur JAMAIS touché. `test_sim_server.py` **77/77**
  (section 10 : bloc par tuile × 4 guildes, forme/bornes, cap 4/plot/guilde,
  zéro sprite sem 1, émergence estivale, positions STABLES entre semaines
  (slots ancrés), 2 snapshots sans step identiques = lecture pure).
  **Golden écolo intact** (`16a1b937…`, vérifié).
- **Livré C#** : `visuals/MacroLife.cs` (nouveau) — **UN seul nœud** pour tous
  les points (8 600 Node2D engorgeraient la scène ; un CanvasItem batch tout),
  ZIndex 5 entre sol (0) et objets (10), enfant direct de WorldView (survit à
  RebuildWorld, se re-projette à chaque dessin → rotation D35 gratuite).
  Formes sobres SANS nom (kickoff §5 — naturaliste débutant) : ravageur point
  sombre, auxiliaire point clair, pollinisateur point jaune qui erre plus
  large, ver tiret terre orienté monde. **Errance** sin/cos sur l'horloge
  réelle, déphasée par hash djb2 de la clé (zéro Random, stable
  inter-sessions), amplitude ∝ activité (plancher 0,3). **Diff doux** : clé
  `tile|guild|r|c|x|y`, fondus 0,6 s / 0,9 s (les durées des plantes t3), slot
  qui re-franchit son seuil pendant son fondu de mort → reprend sans pop.
  **Anim à 20 Hz** (accumulateur dans `_Process`, leçon perf C2), coût nul si
  0 sprite. `WorldView.cs` : création du nœud, `SetSprites` dans ApplySnapshot
  (lecture TOLÉRANTE pré-0.2.3), compteur « vie macro N » au F4. Témoin de
  build → **« t6·B vie macro — 2026-06-12 »**.
- **Choix signalé (design)** : l'errance continue en Planification (animation
  d'ambiance, pas du temps simulé — comme les fondus t3). Si le temps figé
  doit TOUT figer : une ligne à ajouter, à trancher au F5.
- **Critères F5** (kickoff) : points vivants sur les tuiles, plus nombreux où
  ça fleurit/paille ; geste écraser → des points disparaissent au plot (le
  message « ravageurs 0.80 → 0.60 » devient VISIBLE) ; aucune étiquette de
  nom ; FPS stable au F4 (comparer avant/après, ~700 sprites smoke en
  automne ; couper avec O ne joue PAS sur eux — pas de toggle dédié, pas
  demandé).
- **1er F5 Nico (2026-06-12) — retours triagés** (écraser un ravageur ✓) :
  - **« FPS à 3, vie macro à 9 500 »** + **« beaucoup trop, petits animaux,
    ne devraient apparaître qu'en zoomant »** → défaut du livrable →
    **correctif t6·B2 (C# seul)** : **LOD** (invisibles sous le palier ×4 —
    la plage pixel art commence là) + **culling viewport** (seul le cadre
    caméra se dessine ; à ×4+ c'est une fraction du monde — 9 500 DrawCircle
    plein cadre était LE coût) + **touche I** (vie macro ON/OFF, coût nul à
    OFF, demande explicite) ; F4 affiche « OFF » / « (LOD : zoomez ×4) ».
  - **« Les pollinisateurs devraient se déplacer sur toute la carte »** →
    correctif partiel B2 : amplitude d'errance 18 → **120 cm** (déambulation
    de butinage ~2,5 m, fréquences non commensurables, ~1 m/s). Le vol libre
    sur toute la carte serait un AGENT à trajectoire — hors modèle tranché
    (sprite = quantum de densité ANCRÉ, CONCEPTION_VIE_MACRO §3) ; si le
    butinage élargi ne suffit pas au F5 → sprint conception dédié.
  - **« Vers de terre = traits immobiles, pour montrer leur présence ? »** →
    OUI, design : le ver vit DANS le sol — le tiret = indice de présence en
    surface (turricules), il dit « ce sol est vivant », pas « regarde-moi
    bouger ». Indicateur de sol, pas un animal de surface.
  - **« Écraser un pollinisateur/auxiliaire impossible — il faut pouvoir se
    tromper »** → MOTEUR (`sim/actions.py:ecraser` ne touche que le champ
    ravageur) → **sprint « écraser maladroit / impact multi-guildes » gravé
    au BACKLOG** (philo #1 : la maladresse enseigne).
  - **« Grouille en hiver, devrait dormir dès l'automne ; ne se réveille
    qu'à l'été, devrait au printemps »** → MOTEUR (inertie 0.85 ≈ 13 sem
    d'extinction ; warmth=(T−6)/18 quasi nul au printemps frais) → **sprint
    « saisonnalité vie macro (calibrage) » gravé au BACKLOG** (golden
    re-figeage maîtrisé à prévoir — D31.2 lit ces champs).
  - Témoin de build → **« t6·B2 vie macro LOD+I — 2026-06-12 »**.
- **2e F5 Nico (2026-06-12) : correctif B2 VALIDÉ (« ok c'est tout bon ») →
  volet B CLOS.**

### Tranche 6 — volet C (heatmaps debug F6) : CODÉ (2026-06-12), en attente F5
- **Livré Python** : `sim_server.py` protocole **0.3.0** (fin de tranche) —
  commande **`fields`** HORS snapshot (kickoff §8 : le snapshot hebdo
  n'embarque pas les grilles, la vue ne paie que l'overlay ouvert). Sans
  argument → **registre découvert par INTROSPECTION** (tout attribut
  `GridField` d'`EcoFields`, trié, + les 4 guildes — un champ ajouté au
  moteur apparaîtra tout seul) : **16 champs** (humidite, fertilite,
  microbiome, soil_memory ×3, om_ ×3, temperature, disturbance, lumiere +
  ravageur/auxiliaire/pollinisateur/vers_de_terre). Avec `field` → grilles
  par tuile `{rows, cols, values row-major}` (round 4). Champ inconnu →
  `ok:false`, serveur survivant. `test_sim_server.py` **87/87** (section
  11 : registre, dimensions exactes, guilde interrogeable, refus + survie,
  lecture pure, avant init). **Golden écolo intact** (`16a1b937…`, vérifié).
- **Livré C#** : `SimBridge.Fields(field?)` ; `visuals/FieldOverlay.cs`
  (nouveau) — **_Draw de losanges** par plot, choix justifié vs ImageTexture
  (kickoff §9 laissait le choix) : zéro gestion Image/Texture/Transform
  oblique, re-projection gratuite à la rotation D35 (un QueueRedraw), et le
  redraw est RARE (1×/semaine + toggle + rotation) — 1 188 polygones une
  fois par minute ≠ coût (BuildGround en pose autant en permanence).
  **Normalisation AUTO par champ** (min/max de la grille), dégradé bleu →
  rouge (HSV 240°→0°), alpha 0,7, ZIndex 3 (sol < heatmap < vie macro <
  objets). `WorldView.cs` : **F6** ON/OFF (« OFF = coût strictement nul » :
  aucune requête ne part), **Maj+F6** champ suivant ; machine de requêtes
  dans la MÊME file que step/action — propriété **`PipeFree`** (les 3
  pendings), priorité action en file > fields > step ; ligne HUD « heatmap
  (debug) : nom · min · max » ; légende mise à jour ; `_ExitTree` attend les
  trois Tasks. Témoin de build → **« t6·C heatmaps F6 — 2026-06-12 »**.
- **Critères F5** (kickoff) : F6 → heatmap lisible qui SUIT la simulation
  (humidité qui sèche entre semaines, microbiome qui s'étend) ; Maj+F6
  cycle les 16 champs (dont les 4 guildes — la heatmap ravageur double les
  points de vie macro) ; rotation/zoom suivent ; OFF → FPS inchangé
  strictement.
- **1er F5 Nico (2026-06-12) — retours triagés** :
  - **« Aucune heatmap, F6/Maj+F6 inertes »** → suspicion n°1 = **build
    resté en t6·B2** (le symptôme exact : pas de `case F6` → silence total,
    pas même la ligne HUD « chargement » ni un print console ; piège sync
    Nextcloud→build documenté depuis t3). Vérif au prochain F5 : témoin
    haut-droit = **« t6·C2 légendes heatmap »**. Si le témoin était DÉJÀ
    t6·C : relever les messages console `[WorldView]`/`[SimBridge]` au F6
    (un print « heatmap … min/max » a été ajouté à la réception de grille).
  - **Légende couleur demandée** (sous la Vigueur, au-dessus du FPS ; bleu
    froid → rouge chaud pour la température, code couleur approprié PAR
    champ ; visible seulement quand le champ l'est) → **correctif t6·C2** :
    table de **palettes par champ** dans `FieldOverlay` (température
    bleu→rouge, humidité sec-ocre→bleu d'eau, lumière ombre→jaune soleil,
    fertilité pauvre→vert, OM paille→humus, soil_memory gris→indigo,
    disturbance calme→magenta, 4 guildes pâle→teinte MacroLife — un seul
    langage visuel ; champ inconnu → bleu→rouge générique), le dessin
    interpole CES pôles ; légende = `RichTextLabel` BBCode à y=80 (sous
    Vigueur y=52, au-dessus du F4 descendu à y=112) : « heatmap (debug) —
    humidite : ██ sec (0.12) → ██ humide (0.87) · Maj+F6 champ suivant ».
  - **« Il manque température du sol ≠ air, et pH du sol »** → MOTEUR (un
    seul champ `temperature` = l'air de `weather_at` ; pH inexistant) →
    **sprint « physico-chimie du sol : température du sol + pH » gravé au
    BACKLOG** — l'introspection 0.3.0 les exposera automatiquement à F6 le
    jour où ils existeront.
  - Témoin de build → **« t6·C2 légendes heatmap — 2026-06-12 »**.
- **2e F5 Nico (2026-06-12, build C2) : F6 FONCTIONNE** (« c'est bien de
  pouvoir enfin voir les heatmaps des différents fields, content de
  l'avancée ») — le 1er échec était bien le build resté en B2. **4 retours
  → SOUS-SPRINT INDÉPENDANT t6·C3, kickoff PRÊT
  `06b_finitions_heatmap.md`** (décision Nico : à lancer APRÈS le /clear,
  pas de dev immédiat) :
  1. légende = rampe dégradée continue (pas 2 pavés) + repenser la
     normalisation (échelle FIXE par champ recommandée — le min/max auto
     rend les champs uniformes « binaires/bruités ») ;
  2. température identique partout malgré l'ombre → diagnostic lecture
     (champ = AIR hebdo, probablement uniforme par construction) +
     pédagogie ; l'ombre→température du sol = sprint physico-chimie déjà
     au BACKLOG ;
  3. OM/microbiome « aléatoires » → pédagogie (hétérogénéité de fondation
     voulue, design #7) + vérifier la corrélation avec le vivant à
     l'échelle fixe ;
  4. sprites visibles sur des plots « absents » → errance visuelle
     (pollinisateur ±120 cm) + fondu de mort ; recommandation : en mode
     heatmap de guilde, resserrer l'errance sur l'ancre.

### Tranche 6 — sous-sprint C3 (finitions heatmap) : ✅ CLOS (2026-06-12, confirmé F5)
- **Diagnostic Python (lecture seule, conservé `tools/diag_fields_span.py`)** :
  `temperature` est **uniforme PAR CONSTRUCTION** (`engine.py:587`
  `temperature.fill(temp_now)` — l'air hebdo, un seul nombre par semaine) ;
  `om_stable` span 0,001 et `soil_memory_deep` span 0,0014 = bruit
  microscopique que le min/max AUTO étalait sur toute la palette — c'était
  LE rendu « binaire/aléatoire » du F5. Humidité/microbiome/om_fresh ont de
  vrais gradients (span 0,45..0,92), corrélés au vivant.
- **Livré C# (zéro Python, golden intact `16a1b937…` vérifié)** :
  - `FieldOverlay.cs` — **échelle FIXE par champ** (option a du kickoff) :
    la table `Palettes` gagne `FixMin`/`FixMax` (NaN = repli auto). Bornes
    SOURCÉES du moteur : temperature **−5..35 °C** (`temp_norm` 11±7 +
    dérive + gel/canicule), humidite/fertilite/microbiome **0..3** (le
    moteur normalise par /3.0), lumiere/disturbance/guildes **0..1**
    (`_clamp01`) ; om_*/soil_memory* restent AUTO (pas de bornes
    naturelles). Valeur hors bornes → clamp (sature au pôle). Exposés :
    `GridMin`/`GridMax`/`FixedScale` pour le HUD.
  - `WorldView.cs` — légende = **rampe continue 14 pavés** interpolés en
    BBCode (le Lerp exact du dessin) ; sur échelle fixe, ajout
    « grille a..b » (où la grille VIT — « grille 14.11..14.11 » = uniforme,
    vérité du modèle) ; champ temperature → suffixe pédagogique « air
    hebdo (uniforme — temp. du sol : à venir) ».
  - `MacroLife.cs` — **mode instrument** (option b du kickoff, retour 4) :
    propriété `FocusGuild` posée par WorldView quand la grille AFFICHÉE est
    une guilde → les points de CETTE guilde resserrent leur errance à
    ±4 cm sur l'ancre (la corrélation carte↔points saute aux yeux) ;
    errance libre rétablie au F6 OFF ; un nom non-guilde est sans effet
    (aucun sprite ne porte ce nom — zéro cas spécial).
  - Témoin de build → **« t6·C3 finitions heatmap — 2026-06-12 »**.
- **Retour 3 (OM « aléatoires »)** : pas de correctif — pédagogie
  (hétérogénéité de fondation voulue, design #7 ; l'OM se dépose où la vie
  meurt) + l'échelle fixe/auto assainie rend les motifs lisibles ; à
  vérifier visuellement au F5 (corrélation om_fresh ↔ zones de mortalité).
- **F5 Nico (2026-06-12, après une sync Nextcloud PARTIELLE — WorldView
  resté C2 + FieldOverlay C3 = CS8132, résolu par attente de sync) :
  « ok c'est bien » → C3 VALIDÉ.**

### TRANCHE 6 — ✅ CLOSE (2026-06-12, volets A + B/B2 + C/C2/C3 tous confirmés F5)
Dernière tranche de CONTENU du sprint Intégration. Bilan : protocole
0.2.2 → 0.3.0 (hints organes, bloc sprites compact, commande `fields` par
introspection), `MacroLife.cs` + `FieldOverlay.cs` nouveaux, organes
procéduraux portés, 87/87 au test serveur, golden `16a1b937…` JAMAIS re-figé
sur toute la tranche. Mesures finales : snapshot smoke ~24 Ko sem 20
(sprites inclus) ; full ~210 Ko au pic d'automne (8 600 sprites, format
compact) — toujours négligeable à 1 snapshot/60 s. **`DebugSecondsPerWeek`
REMIS À 0** (rythme design 60 s/semaine ; c'est un `[Export]` : re-réglable
à 3 dans l'inspecteur pour une validation rapide). Témoin de build →
**« t6 CLOSE (rythme design 60 s/sem) — 2026-06-12 »**. Gravés au BACKLOG
pendant la tranche : écraser maladroit multi-guildes, saisonnalité vie
macro (calibrage), physico-chimie du sol (temp sol + pH), compétition
intra-plot, décomposition & compost.
