# Sprint D29 — Implémentation Python des hormones (réponse à la taille) — état partagé

> ⚠️ **SUPERSEDED (2026-06-05).** Ce découpage reposait sur le modèle « 2 scalaires,
> golden intact » de `docs/vegetal/croissance/conception_hormones.md`, **abandonné** au profit du modèle
> **structure de segments / auxine structurelle / rendu procédural**. Découpage
> actuel : **`sprints/sprint_croissance/00_etat.md`** (D29 y est absorbé au tronçon
> 3). On conserve ce dossier pour l'historique ; **ne plus le suivre**.

> État léger partagé entre tronçons (≤ ~25 lignes utiles). Mis à jour en fin de
> chaque sous-sprint. Conception figée : `data/code/CONCEPTION_HORMONES.md`.

## Ce qu'on construit
La **réponse architecturale émergente** à la taille (débourrement, ramification,
mise à fruit), par **2 scalaires hormonaux** sur `PlantInstance` (option (ii)
scalaire, topologie écartée — cf. §B). Le geste `tailler` écrit l'état hormonal ;
le **tick** lit les scalaires et produit l'architecture (philo #2 : flux →
réponse émergente, jamais de `+=` scripté). **Repos strictement neutre** :
`dominance_apicale=1.0` / `ramification=0.0` → mapping = identité → **golden écolo
JAMAIS re-figé** (`c950f06c…` engine / `b005d9ba…` champ). Le golden est une
succession spontanée **sans joueur** : personne ne taille. Si un hash bouge → bug.

## Découpage (sprint MOYEN → 3 tronçons autosuffisants ; révisable par Nico)
- **i1 — État hormonal (fondation).** ⬜ À FAIRE.
  2 champs sur `PlantInstance` (`dominance_apicale=1.0`, `ramification=0.0`) +
  trait `reponse_taille="insensible"` sur `PlantBase`. Defaults = repos neutre.
  Test de neutralité (`clone`/sérialisation/égalité au repos). Golden **intact par
  construction** (aucune lecture nouvelle dans le tick à ce stade).
- **i2 — Cinétique dans le tick (cœur).** ⬜ À FAIRE.
  La boucle de croissance (`engine._tick_*`) lit les 2 scalaires et applique le
  mapping §C.4 (canopy_radius ×, height ×, foliage_density ↑, repro via ramification,
  redirection growth_factor) + cinétique (débourrement `p=1−dom`, rétablissement de
  `dom`, bornes). **`f(repos)=identité`** vérifié golden. Test joueur en **injectant**
  l'état hormonal directement (pas encore via `tailler`).
- **i3 — Action `tailler` + démonstrateur (surface).** ⬜ À FAIRE.
  `tailler(game_state, player, plant, eco, cible="apex"|"branche")` dans `actions.py`
  (entrée `COUTS`=MODERE, `OBJETS_TOUCHES`, seam `cout_action`, binaire tout-ou-rien,
  hook géométrique conservé, gain ∝ maturité si organe mûr coupé). `reponse_taille`
  sur `Tomato` (`"buissonnante"`) + `AppleTree` (`"fructification_laterale"`). Golden
  joueur dédié : séquence taille → trajectoire `ramification`/mise à fruit attendue.

## Décisions déjà actées (conception, §B/§C/§F)
- **Scalaire émergent** (option ii) — pas de topologie ni de rendu végétal (le rendu
  ne suit pas : sprites PNG par stade). Porte ouverte vers hybride si sprint frontend.
- **2 scalaires** : `dominance_apicale` = transitoire ; `ramification` = persistant
  (un seul ne porte pas les 2 temporalités). Repos = identité (critère golden #1).
- **Trait `reponse_taille`** = archétype string (`insensible` défaut golden-safe).
  Démonstrateur = tomate + pommier (thème normand, taille de fructification canonique).
- **Déterminisme** : aucune cinétique n'utilise de RNG ; variabilité éventuelle via
  `_hash_noise` (position + seed). Bornes anti-emballement (clamp dom `[0,1]`, ramif
  `[0,RAMIF_MAX]`).

## Hors périmètre (gated — NE PAS ouvrir)
- Marqueur `🌿` dans `maitrise_detection.py` (succès §9.5) → **plus tard** (ligne
  BACKLOG, après i3). Rendu végétal procédural Godot, organes fins (D19), bouture
  (D22), portage C# (D24).

## Points ouverts (à trancher dans le tronçon concerné, défaut sobre + signaler)
- **i2** : forme exacte du modèle de mise à fruit (`reproduction_rate` effectif via
  `ramification`) et où il s'insère dans `reproduction.py`/`engine`. Placeholders
  nommés §G (`DEBOURR_RATE`, `DOMINANCE_RECOVERY`, `RAMIF_MAX`, `K_R`, `K_H`, seuil
  mise à fruit) — valeurs **post-test**, juste les nommer.
- **i3** : effet hormonal exact du `cible="branche"` (dominance ~inchangée) — défaut
  sobre = réduction d'empreinte locale uniquement, signaler le choix.
