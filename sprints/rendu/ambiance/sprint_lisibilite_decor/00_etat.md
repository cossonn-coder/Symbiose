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

## §REPRISE
T1 (forêt) CLOSE, commit à faire par Nico. **Prochaine étape = T2 rivière** : lire `02_riviere.md`
(berges franches + surface eau 2-3 valeurs + reflets orientés courant + ombre de berge), toucher
`DecorLayer.cs` (`DrawRiviere`) + `Palette16.cs` (teintes eau). Golden INCHANGÉ (pure vue, ne PAS
lancer test_golden). Boucle : `dotnet build` (0 err) → MAJ ce fichier → commit → T3.

## §REPRISE
Lire ce fichier. Phase A en cours : diagnostic posé, 3 arbitrages en attente de Nico.
Prochaine étape : intégrer les réponses → figer découpage en tronçons perf-first (dernier = vue Godot F5) → kickoffs.
