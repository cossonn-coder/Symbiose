# Sprint — Écrasement des plantes (volet 2 du sprint « écraser »)

> **Kickoff autosuffisant** (démarrage à froid). Implémente la **réponse des
> plantes à l'écrasement**. La conception est **figée** : la source de vérité
> des décisions est **`data/code/CONCEPTION_ECRASEMENT.md`** (§5 décisions
> Q1–Q6, §7 découpage). Ce fichier porte le **plan d'implémentation testable**.
>
> Règles projet : **moteur Python = source de vérité** ; **golden à préserver**
> (`16a1b937…` — geste hors tick, doit rester intact) ; pédagogie explicite ;
> conserver tout code/test. Ampleur : **moyen** (touche le cœur croissance,
> mais un seul tronçon cohérent). Pur **Python** — aucun fichier C# (le volet
> Godot du geste viendra plus tard ; le pont expose déjà tout).

## Ce qu'on construit, en une phrase
Écraser une plante (sprite végétal cliqué) la **déforme** le plus souvent, la
**tue** parfois (sentiers), la fait **profiter** parfois (basilic, graminées) —
selon **deux traits d'espèce**, le tout par le **seam de perturbation déjà
existant** (`growth.py:atteindre_segment`) + une atteinte santé en régime fort.

## État de départ (vérifié au kickoff, 2026-06-12)
- **Volet 1 LIVRÉ** (commit `4f4a7f2`) : écraser une **guilde animale** au clic
  marche (`actions.py:ecraser(…, guilde, urgence)`, pont `target.guilde`,
  protocole 0.3.1). Ce volet 2 ajoute le cas **cible = plante**.
- **Le seam existe** : `sim/growth.py:241`
  `atteindre_segment(plant, segment_id, intensite)` — DOUX (`intensite <
  COUPE_NETTE=0.8`) baisse l'auxine du segment (→ débourrement latéral →
  ramification émergente) ; NET (`≥ 0.8`) écime le segment + son sous-arbre,
  **collet protégé** (jamais retiré).
- **Rejet de souche** (`growth.py:431-434`) : `if not any(is_apex):
  segments[0].has_bud = True` → une plante sans apex **repousse toujours** du
  collet (run éternel, philo #4). ⇒ **la structure seule ne peut pas tuer** une
  plante — d'où la décision santé ci-dessous.
- **Santé** : `plants/base.py:187` `health: int = 3` (3 sain … 0 mort),
  `is_alive = health > 0`. Une plante à `health==0` est **retirée au tick**
  (`engine.py:362` et `:453` : `tile.plants = [p for p in … if p.is_alive]`).
- **Traits d'espèce** vivent sur `PlantBase` (`plants/base.py:433`
  `port_archetype`, `:434 apical_dominance_base`) ; valeurs surchargées dans
  `plants/species.py` (12 herbacées) et `plants/perennials.py` (5 ligneux).
- **Pont** : `tools/sim_server.py:_do_action` résout une plante par position via
  `self._plant_at(tile, x_cm, y_cm)` (utilisé par manger/recolter/deraciner/
  tailler) ; `ecraser` actuel est dans la branche `r/c + guilde`.

## Modèle figé (résumé — détail dans docs/joueur/gestes/conception_ecrasement.md §5)
Écraser une plante appelle le seam avec une intensité modulée par l'âge, puis —
**seulement en régime NET** — entame la santé selon la stimulation :
```
intensite = INTENSITE_PIED * (1 - resistance_ecrasement * f_lignification(age))
atteindre_segment(plant, cible, intensite)          # déforme (doux) / écime (net) + auxine
if intensite >= COUPE_NETTE and (1 - stimulation_ecrasement) >= SEUIL_DEGAT:
    plant.health -= 1                                # tue si répété → SENTIER
```
- **cible** = `segment_id` si fourni par la vue, sinon le **collet** (segment 0)
  — Q2.
- **DOUX** (résistante / établie) : aucune atteinte santé, juste déformation /
  ramification émergente. **NET** (fragile / semis) : `health -= 1`, modulé par
  `stimulation` (le basilic `0.85` → `(1-0.85)=0.15 < SEUIL` → 0 dégât, il
  **repart** ; le tournesol `0.05` → dégât 1, mort en ~3 passages) — Q1.
- **Cumulatif** (Q5) : le seam est déjà cumulatif sur l'auxine douce ; les
  écrasements nets répétés font chuter `health` → mort → sentier (Q3).
- **`f_lignification(age)`** (Q4) : ≈ 0 pour un semis (s'écrase), → 1 pour un
  sujet établi (inécrasable). Croissante bornée ; ≈ constante pour les annuelles
  (vie courte). Surtout pour les ligneux.
- **Philo** : aucune chute de santé hors geste direct (philo #1 autorise
  l'action directe sur le vivant, comme `deraciner`) ; la déformation/
  ramification reste **émergente** via l'auxine (philo #2) ; rien n'est annoncé
  (#6) ; les sentiers sont un motif spatial **émergent** (#1, le sol porte la
  mémoire). **Golden intact** : geste event-driven hors tick, traits à défaut
  neutres, `health` non touché au repos.

## Plan (étapes vérifiables)
1. **Traits sur `PlantBase`** (`plants/base.py`) : `resistance_ecrasement:
   float = 0.5` et `stimulation_ecrasement: float = 0.0`. Valeurs par espèce
   (table `docs/joueur/gestes/conception_ecrasement.md §4`) dans `species.py` + `perennials.py`.
   → **vérif** : golden inchangé (`python3 -m tests.test_golden` =
   `16a1b937…`), traits lus nulle part au tick.
2. **`f_lignification(age)` + constantes** dans `sim/growth.py` : fonction
   croissante bornée (p. ex. `min(1.0, age_weeks / LIGNIFICATION_SCALE)`),
   `INTENSITE_PIED`, `SEUIL_DEGAT`. → **vérif** : fonction pure testée
   (semis ≈ 0, vieux ≈ 1).
3. **`ecraser_plante(game_state, player, plant, eco, segment_id=None,
   urgence=False)`** dans `sim/actions.py` : calcule l'intensité, appelle
   `atteindre_segment` (collet si `segment_id` None), applique `health -= 1` en
   régime NET selon `stimulation`. Coût = celui de `tailler` (MODÉRÉ, geste
   direct, Q6) × urgence éventuelle ; binaire (effet seulement si payé).
   → **vérif** : nouveau bloc de `tests/test_vigueur.py` — déformation (doux :
   structure intacte, auxine baissée), écimage (net : sous-arbre retiré),
   santé entamée en net seulement, basilic épargné (stimulation haute), mort
   après N écrasements d'un semis fragile, coût débité.
4. **Routage pont** (`tools/sim_server.py`) : dans la branche `verb ==
   "ecraser"`, si `target` porte `x_cm/y_cm` (et pas `guilde`) → résoudre la
   plante (`_plant_at`) → `ecraser_plante` (`segment` optionnel, comme
   `tailler` 0.2.1) ; sinon comportement guilde animale actuel. Message :
   `« écrasé {plante} : déformée / écimée / meurt »`. Bump protocole **0.3.1 →
   0.3.2** (ligne d'historique). → **vérif** : `tests/test_sim_server.py` +
   1-2 checks (écraser une plante par position déforme/abat ; déterminisme
   byte-à-byte préservé).
5. **Lancer toute la suite** : `test_golden` (intact), `test_vigueur`,
   `test_croissance` (le seam est partagé avec `tailler` — non-régression),
   `test_sim_server`. `main.py` tourne.

## Critères de succès
- [ ] Golden `16a1b937…` **intact** (geste hors tick, traits neutres au repos).
- [ ] `test_croissance` inchangé (seam partagé avec `tailler` non régressé).
- [ ] Nouveaux tests verts : déformation douce / écimage net / santé en net
      seulement / basilic épargné / mort d'un semis après N passages / coût.
- [ ] `test_sim_server` : écraser une plante par position route bien (vs
      guilde), déterminisme byte-à-byte conservé.
- [ ] `main.py` OK.

## Pièges identifiés (à ne pas réapprendre à chaud)
- **`health` est un `int` 0-3** : `health -= 1` par écrasement NET, pas un
  float. La modulation `stimulation` agit en **seuil** (`(1-stim) ≥ SEUIL_DEGAT`
  → dégât 1, sinon 0), pas en fraction de point. 3 passages tuent un fragile
  sain — calibre `SEUIL_DEGAT` pour que le basilic (stim 0.85) tombe sous le
  seuil et le tournesol (0.05) au-dessus.
- **Collet protégé** : `atteindre_segment` ne retire jamais le segment 0 ; sur
  un semis réduit au collet, l'écimage net ne change pas la structure → c'est
  bien la **santé** (étape 3) qui réalise la mort, pas la structure. Ne pas
  toucher au rejet de souche (option écartée par Nico).
- **Déterminisme byte-à-byte du pont** : `test_sim_server` compare deux runs ;
  l'écrasement d'une plante doit être déterministe (aucun RNG ; intensité et
  dégât sont des fonctions pures de l'état).
- **Ne pas re-figer le golden** : si un test golden bouge, c'est qu'un trait
  est lu DANS le tick par erreur — les traits ne doivent agir que via
  `ecraser_plante` (event-driven).
- **Coût `tailler`** : réutiliser `cout_action(…, "tailler", …)` /
  `_objets_action` pour rester cohérent avec le seam partagé (même famille de
  geste direct), ne pas inventer une entrée `COUTS` neuve sauf besoin avéré.

## Après ce sprint
- Mettre à jour `journal.md` (entrée de clôture du sprint « écraser »,
  volets 1+2), `BACKLOG.md` (retirer « écraser maladroit »), la mémoire projet.
- Le **rendu Godot** du geste (cliquer une plante → écraser, montrer
  déformation/mort) = volet vue ultérieur — le pont est prêt (protocole 0.3.2).
- Reste en suspens : **tranche 7 packaging** (partie VM faite, build Windows
  par Nico) — Nico a choisi de privilégier les features.
