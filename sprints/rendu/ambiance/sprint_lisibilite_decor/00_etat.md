# Sprint LISIBILITÉ DÉCOR — état vivant (carnet de bord /conception)

**Type/thème :** rendu / ambiance · **Ouvert :** 2026-07-23 · **Statut :** FIGÉ — prêt `/sprint-auto` (4 tronçons)
**Doc conception :** `docs/rendu/ambiance/conception_lisibilite_decor.md`
**Origine :** amorce « décor éclaté au sol » (falaise/forêt/rivière), reprise D58 (RENDU AMBIANCE T4/T5).
**Nature :** pure vue C#, aucun impact moteur, **golden préservé** (aucun re-figeage prévu).

## Fichiers concernés (repris, PAS réécrits)
- `visuals/DecorLayer.cs` (352 LDC, T4 : ossature 4 secteurs + rivière/falaise/prairie)
- `visuals/DecorLayer.Arbres.cs` (210 LDC, T5 : silhouettes d'arbres `DrawForet`)
- `visuals/Palette16.cs` (couleurs décor l.122-158)
- doc : `docs/rendu/ambiance/conception_rendu_ambiance.md`

## DIAGNOSTIC ÉTABLI (vérifié dans le code + build)
- **T5 S'AFFICHE** (résout la question n°0 de l'amorce). Build 0 erreur ; `DrawEllipse`
  est **natif Godot 4.6** (`GodotSharp.dll`), pas le privé de PlantRenderer. Méthodes appelées,
  visible LOD zoom ≤ 4. → **reprise ciblée du rendu**, pas un bug, pas une refonte.
- **CAUSE #1 — contraste forêt (PRINCIPAL).** Feuillage ≈ assise : hêtre `#2c5730` vs fond
  forêt `#2f5738` = quasi identiques ; houppier assombri −0.16 → colle encore plus au sol.
  Seul le bouleau `#6f9a4c` (clair) tranche, mais réservé à la lisière peu dense. → « tache
  verte plate amorphe ».
- **CAUSE #2 — pas de volume.** Aucune ombre portée au sol ; amplitude de valeur timide
  (±15 %) ; pas de lumière directionnelle unifiée → rien ne se « décolle ». Les canopées
  (340 cm) >> cellule (130 cm) donc la masse EST continue, mais sans structure ni silhouette
  de cime (pas de « skyline » forêt contre jardin).
- **CAUSE #3 — falaise.** RARE (dérive d'un couplage rivière+prairie voisine → souvent 0
  secteur) ; rendue en bandes de redans à plat, sans face verticale ni ombre → ne surplombe pas.
- **CAUSE #4 — rivière.** La plus lisible (bleu vs vert) mais surface plate ; reflets 2 px
  sous-pixel au dézoom ; berges = juste l'assise. Lit = bande bleue morte.
- **CAUSE #5 — échelle détail/distance.** Détails (fleurs 1.5 px, reflets 2 px, chevrons
  1.5 px) invisibles à la distance d'observation (zoom 0.5, monde ~1560 px final). Décor pensé
  vue large, détaillé vue proche → incohérence.

## Repères techniques (mesurés)
- Projection : `PxPerCmX = PxPerCmZ = 0.39`, `PxPerCmY = 0.195` (px internes, avant zoom caméra).
  Monde 2000 cm → ~1560 px final à zoom 0.5. Chêne : canopée ~133 px, fût ~86 px (≈ 8 % largeur monde).
- LOD décor : visible `CurrentZoom ≤ MaxZoom=4` (zoom steps 0.5/1/2/4/8/16/32). `DepthCm=900`.
- Déterminisme : hash djb2 + 3-sinus, **zéro Random** (à préserver, philo #3).

## DÉCISIONS ARRÊTÉES (arbitrages Nico 2026-07-23)
- **D-a : hiérarchiser, forêt d'abord.** Effort concentré forêt > rivière > falaise (gain visuel max).
- **D-b : rester procédural peint.** Reprise de DecorLayer (valeurs pixel-art dures + ombre portée
  + silhouette de cime + face de falaise + surface d'eau). Pas de sprites. Rationale : déterminisme
  par seed (#3), léger (perf), cohérent avec tous les placeholders procéduraux (maison comprise).
- **D-c : falaise laissée au seed.** On NE force PAS sa présence (fidèle #7 hétérogénéité) ; on la
  rend seulement lisible QUAND elle apparaît (face verticale + ombre).
- **D-transversal : cap qualité = maison normande** (ombre portée + marches de valeur franches +
  face verticale contrastée). Respect cap pixel-art SS² : 2-3 valeurs/masse, pas de dégradé continu,
  Palette16, invariant DrawVolumeEllipse (masse froide + calotte éclairée décalée SO).

## DÉCOUPAGE PRESSENTI (4 tronçons, pure vue, golden INCHANGÉ partout)
- **T1 — Forêt** (`DecorLayer.Arbres.cs` + `Palette16`) : contraste feuillage↔sol, valeurs dures,
  ombre portée au pied, lumière SO unifiée, highlight de cime en lisière. LE gros gain.
- **T2 — Rivière** (`DecorLayer.cs` DrawRiviere + `Palette16`) : berges franches, surface eau 2-3
  valeurs, reflets agrandis orientés courant, ombre de berge (creuse le lit).
- **T3 — Falaise** (`DecorLayer.cs` DrawFalaise + `Palette16`) : vraie face verticale (montée −Y),
  ombre portée au pied (surplomb), éboulis, 3 valeurs roche contrastées.
- **T4 — Transitions/échelle + banc F5** : lisière nette côté jardin, recalibrage taille détails
  (LOD 2 niveaux : détails fins si zoom ≥ 2), banc seed exposant les 4 motifs, MAJ doc conception.

## CARTE DES TRONÇONS (kickoffs autosuffisants présents)
- `01_foret.md` — T1 forêt (PRIORITÉ) : contraste + valeurs dures + ombre portée + cime.
- `02_riviere.md` — T2 rivière : berges + surface 2-3 valeurs + reflets courant.
- `03_falaise.md` — T3 falaise : face verticale + ombre (surplomb), non forcée.
- `04_transitions_banc.md` — T4 (vue finale) : lisière nette + LOD détail 2 niveaux + banc F5 + MAJ doc.

Golden **INCHANGÉ** aux 4 tronçons (pure vue C#, zéro moteur — ne PAS lancer test_golden).

## AVANCEMENT EXÉCUTION
- **T1 — Forêt : CLOSE** (2026-07-24). Pure vue C#, golden non concerné (aucun moteur touché).
  Faits : (a) marches de valeur franches dans `DrawVolumeBlob` (masse ×0.75 / calotte ×1.25,
  bornes `Assombrir`, au lieu de ±15 %), calotte décalée SO (bas+ouest) ; (b) ombre portée
  aplatie au pied de chaque arbre (`DrawOmbrePied`, teinte = `DecorForetFond` −0.30, décalée NE) ;
  (c) accent de cime clair au sommet du houppier (`DrawCimeAccent`, `Lerp` feuillage→`DecorForetCime`,
  hauteur par port) → skyline bosselée ; (d) palette : `DecorForetFond` poussé plus sombre/froid
  (`223a2b`), feuillages ré-étalés en valeurs distinctes (hêtre `35603a` / chêne `44703f` /
  charme `4f7d47` / bouleau `74a250`), nouveau `DecorForetCime` (`a6c56e`).
  Build `dotnet` = 0 err / 0 warn. LDC : `DecorLayer.Arbres.cs` 163 code, `Palette16.cs` 79 code (🟢).
  Géométrie de placement `DrawForet` INCHANGÉE. Zéro `Random` (philo #3 préservée).
  **F5 Nico requis** : la forêt se lit-elle comme masse volumée détachée du sol, cime bosselée ?

- **T2 — Rivière : CLOSE** (2026-07-24). Pure vue C#, golden non concerné (aucun moteur touché,
  test_golden NON lancé). `DrawRiviere` réécrit : (a) **berges franches** de galets (`BergeGalet`)
  sur chaque rive du lit (`ax ± half`, berge = `DepthCm·0.11`) au lieu de l'assise nue ; (b) **surface
  eau 2 valeurs** en damier hashé (parité du pas × moitié du lit : `EauProfonde`/`EauSurface`),
  frémissement sans dégradé ; (c) **ombre de berge** = liseré d'eau assombri (`Assombrir(EauProfonde,-0.18)`)
  le long des deux rives → creuse le lit ; (d) **reflets orientés courant** : streaks `DrawLine`
  (`EauReflet`, largeur 2.5) tracés le long de la tangente du lit (segment d'axe), longueur ∝ pas
  monde (suit zoom/rotation) — remplacent les cercles 2 px sous-pixel. Facteur commun extrait en
  helper `Bande(...)`. Palette : +`EauSurface` (`4a7d9c`), +`BergeGalet` (`9a8f76`), `EauReflet`
  reclassé streak. Zéro `Random` (hash + 3-sinus, philo #3 préservée). Géométrie de l'axe/secteur
  INCHANGÉE (couplage rivière↔falaise `BuildProfile` non touché).
  Build `dotnet` = 0 err / 0 warn. LDC : `DecorLayer.cs` 244 code / `Palette16.cs` 81 code (🟢).
  **F5 Nico requis** : la rivière se lit-elle comme surface d'eau creusée (berges nettes, courant
  perceptible via les streaks) ?

- **T3 — Falaise : CLOSE** (2026-07-24). Pure vue C#, golden non concerné (aucun moteur touché,
  test_golden NON lancé). `DrawFalaise` réécrit : la falaise SURPLOMBE désormais. (a) **Face
  verticale** montée en −Y écran (offset `Vector2(0,-facePx)`, même patron que `WorldView.Maison`
  upWall), **stratifiée** en 3 valeurs de roche (base la + sombre → strate claire, `RocheOmbre/
  Median/Clair`), nb de strates ∝ pente (Douce 3 / Verticale 4 / Déversante 5), hauteur ∝ pente
  (190/330/470 cm). (b) **Plateau végétalisé** (`DecorRocheHaut`) lui-même élevé de la hauteur de
  face → coiffe la paroi, recule en profondeur (0.55·DepthCm). (c) **Ombre portée au pied** côté
  jardin (bande `Assombrir(RocheOmbre,-0.25)` en avant du pied, depth < dFront) = le surplomb.
  (d) **Éboulis** : semis hashé de taches `RocheClair` (~42 %) au pied. Front SINUEUX partagé
  (helper local `Wob`, même ondulation pour ombre/face/plateau → un seul bord cohérent). **NON
  forcée** : `BuildProfile`/couplage rivière↔falaise INTOUCHÉS (philo #7) ; aucun forçage laissé.
  Palette : `DecorRocheHaut` a39a8b→8a9668 (plateau herbeux, distinct de la roche grise),
  `RocheClair` 9c9182→aca291 + `RocheOmbre` 5c5449→4c453a (contraste creusé). Zéro `Random`
  (hash + 3-sinus, philo #3). Build `dotnet` = 0 err / 0 warn.
  LDC : `DecorLayer.cs` 276 code / `Palette16.cs` 81 code (🟢).
  **F5 Nico requis** : quand une falaise est présente (rare, au gré du seed), surplombe-t-elle
  bien (face verticale stratifiée + ombre au pied + plateau végétalisé au-dessus) ?

- **T4 — Transitions / échelle / banc F5 : CLOSE** (2026-07-24). Pure vue C#, golden non concerné
  (aucun moteur touché, test_golden NON lancé). Faits : (a) **LISIÈRE NETTE** — seuil sombre franc
  (`Assombrir(near,-0.24)`, largeur `DepthCm·0.06`) collé au tracé sinueux côté décor, dans
  `DrawSecteur`, sur les 4 motifs → la frontière jardin/décor se lit au lieu de fondre (passe sous
  les berges/éboulis de passe 2, ne les gêne pas). (b) **LOD DÉTAIL 2 niveaux** (`DetailZoom = 2f`,
  helper `DetailsVisibles`) : la MASSE (assises, houppiers, surface d'eau, face de falaise) reste
  sur toute la plage visible ; les DÉTAILS FINS ne se peignent qu'à `CurrentZoom ≥ 2` — reflets de
  courant (`DrawRiviere`), éboulis (`DrawFalaise`), fleurs (`DrawPrairie` return anticipé), chevrons
  bouleau (`DrawTronc`, Arbres.cs) ; `_Process` redessine aussi au basculement `DetailZoom` (2e
  seuil de LOD, reste inerte sinon). (c) **BANC F5 = TOGGLE F10** (`DecorLayer.Banc.cs`, off par
  défaut) → **PAS un seed de démo** : découverte T4, aucun seed n'expose les 4 motifs (cf. BLOCAGE
  ci-dessous). Le toggle force un profil forêt N / rivière E / falaise S / prairie O UNIQUEMENT
  quand activé — distribution par seed intacte (philo #7). (d) MAJ doc conception §7 « état livré ».
  Build `dotnet` = 0 err / 0 warn. LDC : `DecorLayer.cs` 289 code, `DecorLayer.Arbres.cs` 163,
  `DecorLayer.Banc.cs` 23, `Palette16.cs` 81 (TOUS 🟢 — le banc sorti en partial a maintenu
  `DecorLayer.cs` sous 300 malgré T2+T3+T4 cumulés). Zéro `Random` (philo #3).
  **F5 Nico requis** : F10 → les 4 motifs se lisent d'un regard, démarqués du jardin, détails nets
  à zoom ≥ ×2 et masse lisible au dézoom ?

## ⚠️ BLOCAGE / DÉCOUVERTE T4 (à verser en dette par Nico)
**La falaise n'apparaît sur AUCUN seed en jeu normal.** Dans `BuildProfile` (DecorLayer.cs), les 4
côtés d'un même seed dérivent d'un hash `decor|seed|cote` qui ne diffère que du DERNIER caractère
(0..3) → le djb2-xor ne brasse que les bits bas → les 4 rolls %100 tombent quasi identiques → un
terrain porte presque toujours un ANNEAU UNIFORME d'un seul motif. La falaise, qui exige une rivière
clockwise-adjacente à une prairie, ne réunit JAMAIS ses conditions : **0 falaise sur 300 000 seeds**
(vérifié par réplication Python du hash). Le tronçon T3 (face verticale de falaise) n'est donc
visible qu'au banc F10. **Corriger `BuildProfile`** (décorréler les 4 côtés — p.ex. hash sur une
chaîne plus brassée par côté — pour que forêt/rivière/falaise/prairie coexistent) **déborde T4**
(changerait la distribution par défaut, interdit par le kickoff, philo #7) → **candidat dette** :
« BuildProfile : motifs de décor quasi uniformes par seed, falaise jamais produite ».

## §REPRISE — SPRINT TERMINÉ
T1 (forêt) + T2 (rivière) + T3 (falaise) + T4 (transitions/LOD/banc) **CLOSES**. Pure vue C#,
**golden jamais touché** (aucun moteur), build vert. **Reste = F5 Nico** (validation visuelle des
4 tronçons + banc F10) puis clôture sprint : commits (par Nico), MAJ `DETTE.md` (D58 résorbée +
ouvrir la dette `BuildProfile` ci-dessus), `BACKLOG.md`, `journal.md`. Aucun `/refactor` requis
(tous fichiers 🟢).
