# Sprint D12 — Implémentation Python des paliers de maîtrise — état partagé

> État léger partagé entre tronçons (≤ ~25 lignes utiles). Mis à jour en fin de
> chaque sous-sprint. Conception figée : `data/code/CONCEPTION_MAITRISE.md`.

## Ce qu'on construit
Remplir l'interface laissée stubbée par le Sprint Vigueur (`sim/vigueur.py:
palier_bonus()==1.0`). La maîtrise est une **couche gameplay joueur au-dessus du
tick** (miroir de la Vigueur) : `game_state["maitrise"][player]`, **par avatar**,
event-driven. **Golden écolo JAMAIS re-figé** (`c950f06c…` engine / `b005d9ba…`
champ) — comme la Vigueur a gardé son golden intact. Si un hash bouge → bug.

## Découpage (sprint GROS → 4 tronçons autosuffisants ; révisable par Nico)
- **i1 — Cœur : objet de maîtrise + progression intra-objet (strate 0+1).** ✅ **FAIT 2026-06-04.**
  `sim/maitrise.py` (état par avatar, `decouvrir` 0→1, `enregistrer_preuve` →
  franchissement de palier sur courbe log §2.3, monotone §2.4). Catalogue-agnostique
  (un objet = une clé string). Golden joueur `tests/test_maitrise.py` **18/18** (preuves
  **injectées** par API, pas de détection auto). **Golden écolo intact.**
- **i2 — Agrégats + ponts Vigueur (strate 2 + §4.1/§4.3).** ✅ **FAIT 2026-06-04.**
  `maitrise.py` : `accumulation_globale`/`completude_ratio` (§3.2), `palier_bonus
  (game_state, player)` = `1+K·log1p(acc)` (§4.1), spillover intra-famille dans
  `enregistrer_preuve` (lit `plants/catalogue` → famille ; sœur maîtrisée accélère,
  jamais hors famille). `vigueur.py` : `palier_bonus` **délègue** à maitrise (point
  ouvert tranché → **(a)** : signature `(game_state, player)`, 5 sites + A4 maj).
  Sources ponctuelles §4.3 dans `actions.py` (`observer`, `crediter_succes`).
  Golden joueur **maitrise 35/35**, **vigueur 96/96**. **Golden écolo INTACT.**
- **i3 — Seam `cout_action` + table objets-touchés (§4.2/§10.4).** ✅ **FAIT 2026-06-04.**
  `actions.py` : `cout_action(game_state, player, action, objets_touches)` =
  `base × f_globale × f_objets` ; `COUTS` (littéraux d'avant regroupés) ;
  `OBJETS_TOUCHES` (§10.4, objets statiques) ; helpers `_cle_espece` (reverse
  classe→clé catalogue) + `_objets_action` (statique ∪ cible vivante). `f_globale`
  = `1−ATT_GLOBALE_MAX·completude_ratio` ; `f_objets` = moyenne des
  `1−ATT_OBJET_MAX·palier/PALIER_MAX` (inconnu→1.0). Les **6 gestes payants**
  branchés (récolte/déraciner/écraser×urgence-séparée/favoriser/bêcher/grelinette) ;
  `manger` base NUL inchangé. Golden joueur **vigueur 103/103** (96 + section G),
  **maitrise 35/35**. **Golden écolo INTACT.**
- **i4 — Détection de succès branchée (§9).** Lire les signaux du tick (§9.1) depuis
  la couche gameplay, fenêtre d'imputation geste→amélioration, tag provenance
  *féral* vs *replanté* (§9.6), gate d'observation. Le plus délicat → en dernier.

## Décisions déjà actées (conception)
- Unité = **objet de maîtrise générique** (pas les familles), data-driven.
- 2 mesures distinctes : complétude-ratio (seuils) ≠ accumulation-log (Vigueur).
- `palier_bonus` reste scalaire ; coût d'action = **seam séparé** sur `actions.py`.
- Maîtrise stockée **par objet** ; l'action est un **lecteur** (pas de paire
  action×objet). Monotone. Spillover **intra-famille only**.

## Points ouverts (à trancher dans le tronçon concerné, défaut sobre + signaler)
- **i2 (TRANCHÉ 2026-06-04) :** `palier_bonus` → **(a)** signature `(game_state,
  player)`, délégation `vigueur.palier_bonus → maitrise.palier_bonus`. Sens de
  dépendance posé : **Vigueur → Maîtrise** (jamais l'inverse) → `maitrise.py` reste
  pur (importe `plants` seul), et les **gains ponctuels §4.3** vivent dans la couche
  d'orchestration `actions.py` (qui voit les deux), pas dans `maitrise.py` (sinon
  cycle d'import). `vigueur.py` est retouché (assumé : le plan §4.1 « ne pas
  toucher » était inatteignable car le bonus est par-joueur).
- **Calibrage** `K`/`BASE`/`R`/`SPILLOVER_RATE`/`GAIN_DECOUVERTE`/`GAIN_SUCCES`/
  atténuations = **D12.4 post-test** : placeholders nommés posés, pas les bons chiffres.

## État courant
- **2026-06-04 :** **i3 implémenté** (`actions.py` : seam `cout_action` + tables
  `COUTS`/`OBJETS_TOUCHES` + helpers `_cle_espece`/`_objets_action` + `f_globale`/
  `f_objets`, 6 gestes branchés). `actions.py` importe `plants.catalogue` (reverse
  classe→clé) — `maitrise.py` reste pur. **Choix documentés :** `f_globale` lit
  `completude_ratio` (borné [0,1], pas de log) ; `f_objets` = moyenne des atténuations
  (bornée, jamais →0) ; urgence d'`ecraser` = facteur SÉPARÉ par-dessus le seam.
  Atténuations = placeholders `ATT_GLOBALE_MAX`/`ATT_OBJET_MAX = 0.5` → **D12.4**.
  maitrise **35/35**, vigueur **103/103** (96 + section G). **Prochain : i4**
  (détection automatique de succès §9 : signaux du tick, fenêtre d'imputation, tag
  féral, gate d'observation — le plus délicat).
- **2026-06-04 (i2) :** `maitrise.py` agrégats+spillover+`palier_bonus`, `vigueur.py`
  délégation, `actions.py` gains ponctuels. `preuves` flottant quand spillover joue.
- **i1 (rappel)** : module pur, invariant « dans le dict ⇒ palier ≥ 1 », auto-découverte,
  consommation cumulative, placeholders `PREUVES_BASE=2`/`PREUVES_R=2`.
- Golden de référence à préserver : écolo `c950f06c…` / champ `b005d9ba…` /
  joueur Vigueur (hash trajectoire `e63b9d7f…`, inchangé : pont neutre sans maîtrise).
  **Tous VÉRIFIÉS INCHANGÉS après i2** (golden + pop relancés, hash identiques).

## Boucle
Lancer `0N` → coder → vérifier les golden → MAJ ce fichier → commit → `/clear` →
`0N+1`. Mémoire `project_status` à jour en fin de chaque tronçon.
