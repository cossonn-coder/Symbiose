## 2026-06-11 → 2026-06-12 — Sprints Intégration·4, ·5 et ·6 : le jardin devient JOUABLE et LISIBLE — tranches CLOSES

> Entrée de synthèse (3 tranches, ~10 F5 de Nico, détail complet par volet
> dans `sprints/sprint_integration_godot/00_etat.md`). Le golden écolo
> `16a1b937…` n'a **jamais été re-figé** sur les trois tranches : tout ce qui
> suit est de la VUE + des façades joueur/lecture, le tick moteur est intact.

### Tranche 4 (2026-06-11) — caméra, actions joueur, ombre solaire
- **Volet A — caméra D35** : pan flèches, zoom molette par paliers
  {0.5..32} centré souris, rotation par quarts de tour (`_orientation`
  dans la projection — re-projection, pas rotation canvas). Retours F5 :
  toit pyramidal orienté monde, boussole, étiquettes (F3), maison
  transparente (H), modes simu (M). **D35 levée.**
- **Volet B — actions joueur, protocole v1 (0.2.0)** : Vigueur au snapshot,
  commande `action` (verbe+cible+params → ACK/NAK + snapshot frais),
  8 gestes au clavier 1..8 (PhysicalKeycode, AZERTY), clic = désignation
  par position (±0,1 cm), urgence = phase Saison. Python ne fait que des
  façades `sim/actions.py` — règles et coûts restent au moteur. Correctifs
  F5 : file d'UNE intention (Turbo n'affame plus les clics), flash jaune
  du geste réussi, messages instructifs (gain de manger, ravageurs
  avant/après).
- **Volet C — ombre solaire animée** : `solar_slice` porté côté vue
  (latitude 49°N, lever/coucher astronomiques) ; 1 semaine vécue ≈ 1
  journée visuelle ; ombres-capsules au pied des plantes, hull convexe
  pour la maison. Les saisons se LISENT (hiver : ombres 3,15×h ; été :
  lever au NE → ombres du soir vers le sud, réalisme gratuit). Correctif
  C2 perf : l'ombre devient un nœud enfant (`PlantShadow`) — le balayage
  solaire ne redessine plus les segments ; touches O (ombres) et F4
  (overlay de perfs).

### Tranche 5 (2026-06-11) — taille au segment près
- `tailler(segment_id)` côté façade (compat totale : sans id = sélecteur
  t4), protocole 0.2.1 `target.segment`, surbrillance du segment sous la
  souris (même géométrie que le dessin, leçon D2), collet exclu du
  hit-test. Correctif t5·B : `FindSegmentGlobal` — la couronne débordante
  d'un arbre redevient taillable. Au passage, vérifié par expérience :
  **la repousse à deux têtes après écimage EXISTE déjà** (émergence du
  débourrement auxine, rien de codé en dur — philo #2).

### Tranche 6 (2026-06-11 → 12) — organes, vie macro, heatmaps
- **Volet A — organes procéduraux (0.2.2)** : 3 hints lecture seule au
  snapshot (`foliage_density` caduc l'hiver, `organ` proxy saisonnier,
  `organ_site`) ; `_draw_organs` porté en C# (feuilles au hash stable,
  fleurs/fruits aux apex, palette espèce×saison).
- **Volet B — vie macro visible (0.2.3, D31 côté vue)** : bloc `sprites`
  compact (mesuré : 210 Ko vs 705 Ko verbeux au pic de 8 600 sprites),
  `MacroLife.cs` = UN nœud batch, formes SANS nom (naturaliste débutant),
  errance sin/cos ancrée déphasée par hash. Correctif B2 après FPS 3 au
  F5 : LOD ×4 + culling viewport + touche I. Pédagogie actée : le tiret
  du ver = turricules (indice de sol vivant), le pollinisateur déambule
  (±120 cm) mais reste un quantum de densité ancré, pas un agent.
- **Volet C — heatmaps debug F6 (0.3.0)** : commande `fields` HORS
  snapshot, registre par INTROSPECTION (16 champs — un futur champ moteur
  apparaîtra tout seul), `FieldOverlay.cs` en _Draw de losanges (redraw
  rare, rotation gratuite). Le « mode debug champs écologiques » de la
  conception existe enfin. Péripétie : 1er F5 « F6 inerte » = build resté
  B2 (sync Nextcloud, piège récurrent → témoin de build systématisé).
- **Sous-sprint C3 — finitions** : diagnostic conservé
  (`tools/diag_fields_span.py`) : `temperature` uniforme PAR CONSTRUCTION
  (fill hebdo de l'air) ; le min/max auto étalait le bruit de 0,001
  d'`om_stable` sur toute la palette = le « rendu binaire » vu au F5.
  → **échelle FIXE par champ** (bornes sourcées moteur : temp −5..35 °C,
  hum/fert/microbiome 0..3, lumière/guildes 0..1 ; om_*/soil_memory*
  auto), légende en rampe continue 14 nuances + « grille a..b »,
  pédagogie air≠sol au HUD, **FocusGuild** (heatmap d'une guilde → ses
  points se resserrent sur l'ancre : l'instrument montre la corrélation).

### Gravés au BACKLOG pendant ces tranches (moteur, pas le pont)
Planter/arroser (gestes sans équivalent moteur) · compétition intra-plot ·
décomposition & compost · écraser maladroit multi-guildes (philo #1 : la
maladresse enseigne) · saisonnalité vie macro (dormance automne, réveil
printemps) · physico-chimie du sol (température du sol ≠ air + pH —
l'introspection 0.3.0 les exposera à F6 automatiquement).

**Statut.** Tranches 4, 5, 6 **CLOSES** (tous volets confirmés F5).
`DebugSecondsPerWeek` remis à 0 — le jeu tourne au rythme design
(60 s/semaine). Protocole pont : v0 → **0.3.0**. `test_sim_server` : 30 →
**87/87**. **Prochaine : tranche 7 = packaging PyInstaller (kickoff
`07_packaging.md`), DERNIÈRE tranche du sprint Intégration.**

---
