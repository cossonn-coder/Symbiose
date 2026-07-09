# 2026-07-09 — Conception RENDU AMBIANCE (D58) — FIGÉE

`/conception` sur D58 « rendu graphique attractif ». **Phase A = constat de
cadrage** : D58 (écrite le 2026-07-02) était **déjà à moitié résorbée** — les
feuilles par espèce (`PlantRenderer.Leaf.cs`, 6 `LeafShape` + nervures +
croissance + litière), la couleur physiologique (D33) et la palette + relief du
sol (SS²) sont **tous faits**. Restaient 4 chantiers hétérogènes.

## Arbitrages Nico
- **Périmètre** = **fleurs par famille + maison normande + décor d'ambiance**.
  **Vent EXCLU** (→ dette **D72**) : collision frontale avec le sprint perf du
  jour (plantes rendues STATIQUES + LOD + culling ; animer le vent = redessiner
  par frame). À concevoir perf-first à part (transform de Node2D, pas re-`_Draw`).
- **Maison = granite + ardoise du Cotentin** (réf. Nico maçon+couvreur,
  Montmartin-sur-Mer), **PAS colombages/chaume** : moellons de granite gris-bleu/
  roux, chaînages d'angle, encadrements granite clair, pignon essenté d'ardoise,
  **toit d'ardoise pentu > 45° + lucarne à bâtière sud**, cheminée brique orangée.
- **Décor = cosmétique maintenant, extensible plus tard** : zones **organiques
  sinueuses** par seed (forêt / rivière+falaise couplées / **prairie fleurie
  défaut**), chemins entre tuiles **enherbés**, couture `SurroundingsProfile`
  prête pour le pont (friche / extensions) — sans câblage (dette **D73
  terraforming** : barrage/coupe/creuser/mare, comptabilisé, moteur à part).
- **Forêt = essences du catalogue, arbres ADULTES d'emblée** : ajout de **Hêtre /
  Bouleau / Charme** au catalogue (vraies espèces + 5 voix, golden NEUTRE).
  Rendu **procédural** : silhouette adulte peinte directement (tronc + houppier =
  amas d'ellipses volumées, `TreeSilhouette` par essence, rayon adulte) → « déjà
  haut et mûr » par construction, **jamais** la structure de segments (perf,
  backdrop statique cullé). Gradient de lisière (bouleau clairsemé → chêne/hêtre
  dense).

## Ajout post-figeage — Feuilles fidèles (T6, même jour)
Nico signale que les feuilles restent « ovales ». Vérifié : `PlantRenderer.Leaf.cs`
synthétise chaque feuille par **amas d'ellipses fusionnées** → lecture en taches.
Décision (arbitrage) : **contours authorés par espèce** (~27) fidèles au modèle
botanique réel (chêne lobé, figuier palmé, tomate composée…), l'amas d'ellipses
devenant le **repli LOD intermédiaire**. Attente honnête posée : fidélité livrée
au **zoom rapproché ×16+** (à ×4/×8 une feuille = 2-5 px, indistinguable). 3
paliers LOD. Nouveau partial `PlantRenderer.LeafOutline.cs`. Couche B, golden
inchangé. → tronçon **T6**, kickoff `06_feuilles_fideles.md`.

## Livrables
- Doc : `docs/conception/CONCEPTION_RENDU_AMBIANCE.md` (§3bis = feuilles fidèles).
- Sprint : `sprints/sprint_rendu_ambiance/` — `00_etat.md` + kickoffs `01`→`06`.
- **6 tronçons**, golden préservé partout : T1 essences (moteur, NEUTRE) → T2
  fleurs → T3 maison → T4 décor ossature → T5 décor motifs → T6 feuilles fidèles
  (vue pure). Vue Godot = T2→T6. Dettes ouvertes : **D72 vent**, **D73 terraforming**.
- Prêt pour `/sprint-auto sprint_rendu_ambiance`.
