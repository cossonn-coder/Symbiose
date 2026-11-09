# ① Le grain sauvage — socle de la zoochorie (D42)

Lire d'abord : `CLAUDE.md`, `00_etat.md` (ce dossier), doc
`docs/faune/vie_macro/conception_zoochorie.md` §4.1.

## Objectif
Faire de `GrainEnAttente` le véhicule de toute graine **sauvage** (tombée ou portée par
une bête), sans rien changer aux graines plantées par le joueur. Aucun producteur de
grain sauvage n'existe encore : ce tronçon pose le socle et le teste en labo.

## Fichiers
- `fields/seedbank.py` — `GrainEnAttente` : champs neufs avec défauts qui gardent le
  comportement actuel : `origine: str = "joueur"` (`"chute"`, `"merle"`, `"geai"`,
  `"ecureuil"`, `"mulot"`, `"ceinture"` pour les sauvages), `levee_des: int = 0`
  (semaine absolue minimale de levée), `perime_a: int | None = None` (semaine absolue
  où le grain meurt ; `None` = jamais). Un grain sauvage a `cultive=False`.
  Fonction pure `grain_sauvage(cls, genes, expression, origine, semaine, x_cm, y_cm)`
  qui calcule `levee_des` (premier printemps STRICTEMENT après le dépôt : utiliser
  le calendrier du projet — `calendrier.saison_de`/`wiy_de`, module racine, déjà
  importé par `sim/clonal.py`) et `perime_a = semaine + round(viabilité × 52)`.
  Fonction `deposer_grain_sauvage(tile, r, c, grain)` : refuse (renvoie False) si le
  plot porte déjà `GRAINS_SAUVAGES_MAX_PLOT` (= 3) grains sauvages ; sinon ajoute.
- `plants/base/familles.py` (à côté de `graine_si_hiver_min_c`) : trait
  `graine_viabilite_ans = 1.0`. Valeurs : framboisier 5, fraisier 3, cerisier 2,
  pommier 2 [ordres de grandeur ; Rubus = banque persistante]. Chêne, hêtre, noyer :
  défaut 1 (graines récalcitrantes).
- `sim/succession.py::_lever_grains_en_attente` :
  1. purge en tête de traitement de chaque plot les grains `perime_a` dépassé
     (log seulement si utile aux voix — pas de spam) ;
  2. choisit le **plus ancien grain éligible** (`week >= levee_des`) au lieu de
     `grains[0]` ; retire CE grain à la levée ;
  3. la ligne de log distingue l'origine : `🌱 Levée (planté)` inchangée pour
     `origine == "joueur"` ; sinon `🌱 Levée (semé par <origine>)` — format exact à
     poser une fois, il sera lu par les voix au ⑦.
  `marquer_replante` reste réservé à `cultive=True` (déjà le cas).
- Sauvegarde : si `GrainEnAttente` est sérialisé (chercher `grains_en_attente` dans
  `tools/simserver/` et le save), y porter les champs neufs avec défauts au chargement.

## Ne PAS faire
- Ne pas changer la levée d'un grain planté (FIFO, pas de péremption) : un grain
  `origine == "joueur"` doit se comporter au bit près comme avant.
- Ne créer aucun producteur (chute, merle…) : c'est ② et ④-⑥.
- Ne pas toucher `SeedBank.species` ni `germination_candidates`.
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Tests
Neuf `tests/test_grain_sauvage.py` :
(a) un grain sauvage déposé en été ne lève pas avant le printemps suivant, puis lève ;
(b) un grain périmé disparaît sans lever ; (c) plafond : le 4ᵉ dépôt sur un plot est
refusé ; (d) un grain en dormance en tête ne bloque pas un grain éligible derrière ;
(e) un grain `joueur` lève comme avant (même semaine qu'avec l'ancien code sur un
scénario fixé — contre-factuel noté).

## Golden
`a10b7225…` **INCHANGÉ** attendu (`grains_en_attente` vide au smoke). Lancer aussi
`test_evenements`, `test_carnet`, `test_encyclopedie`, `bancs.test_verger_mur`.

## Perf
Nul (chemin event-driven, vide hors grains).

## F5
Aucun.
