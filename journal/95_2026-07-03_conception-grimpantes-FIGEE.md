## 2026-07-03 — Conception PLANTES GRIMPANTES (D49) — FIGÉE

**Décision :** conception figée du **volet A** de D49 (la GRIMPE seule ; le volet
B rampantes/traçantes clonales est scindé → dette **D62**). `/conception`, phase B,
conception SEULE. Doc `docs/conception/CONCEPTION_GRIMPANTES.md` + sprint
`sprints/sprint_grimpantes/` (00_etat + 01→06), prêt pour `/sprint-auto`.

**Deux prémisses du brief corrigées par le code (phase A) :**
- `StakeSlot` (`world/tile.py`) **n'est PAS un tuteur** : c'est le porte-rondelles
  du jeu de plateau (aucune position/hauteur). Tuteur/treillis/pergola = structures
  **NEUVES**. L'énoncé de D49 (« 10 tuteurs/tuile ») était une erreur d'inventaire.
- Le haricot est **déjà procédural** : sa hauteur = `max(z)` des segments. Il n'y a
  aucun « scalaire de longueur » ni « contraction ressort » à réutiliser.

**Décisions Nico :**
- **A1 = modèle GÉOMÉTRIQUE** (retenu contre le clamp du brief) : au-delà de
  `hauteur_autoportante` sans appui, le **plancher d'apex** (`MIN_APEX_Z` de
  `_phototropic_bias`) s'effondre → la tige retombe (affalement émergent) ;
  accrochée, biais d'apex vers l'axe du support → grimpe. `height_at` reste
  `max(z)` **honnête, jamais de clamp** → les consommateurs de `current_height`
  (nécromasse, abri, pot) restent justes.
- **A2 = panoplie complète** : tuteur + treillis + pergola posables + mur maison +
  **plante-hôte vivante** (étranglement émergent par l'ombre du `LightField`, sans
  règle dédiée) + geste `palisser` (sarmenteux).
- **A3 = démo réduite** : trait `mode_grimpe` 3 valeurs (crampon/vrille_volubile/
  sarmenteux) démontré sur **haricot + lierre + jasmin** (5 voix chacun) ; glycine/
  courge/kiwi/vigne/akébia → **D26**.
- **Vue Godot INCLUSE** (tronçon ⑥) + **règle permanente** : la vue Godot est
  désormais **toujours le dernier tronçon** de chaque sprint (gravé mémoire + skill
  `/conception`). Absorbe le rendu de vrille différé (`CONCEPTION_RENDU_FEUILLAGE §7`).
- **Banc d'essai `grimpantes`** (⑥, demande Nico) : haricot **à côté** du tournesol
  (grimpe sur hôte), champ tomates/basilic/poivrons au **sud**, départ **début
  printemps** (automatique : `week=1`→wiy1, `printemps=range(1,14)`).

**Golden :** re-figé **maîtrisé au ① SEUL** (le haricot s'affale, dérive localisée,
`a6c2f651…`→nouveau, annoncé) ; **NEUTRE/INTACT** aux tronçons ②→⑥.

**6 tronçons :** ①traits+affalement → ②supports+accroche → ③hôte vivant+étranglement
→ ④gestes+maîtrise → ⑤catalogue lierre+jasmin+5 voix → ⑥vue Godot+banc.
