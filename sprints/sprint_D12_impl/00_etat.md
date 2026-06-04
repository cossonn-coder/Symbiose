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
- **i2 — Agrégats + ponts Vigueur (strate 2 + §4.1/§4.3).** complétude-ratio,
  accumulation-log, spillover famille (lit `plants/`), **remplir `palier_bonus`**,
  sources ponctuelles (découverte/succès → `gain`). ⚠ point ouvert : `palier_bonus
  (player)` n'a pas `game_state` (voir §Points ouverts).
- **i3 — Seam `cout_action` + table objets-touchés (§4.2/§10.4).** `cout_action
  (player, action, objets_touches)` = terme global × terme objets ; table §10.4
  data-driven ; objets non câblés = atténuation neutre 1.0. Brancher sur les
  actions de `sim/actions.py`.
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
- **i2 :** `palier_bonus(player)` ne reçoit pas `game_state` (appelée ainsi dans
  `vigueur_max`/`regen_rate`/`gain`/`tick_player_vigueur`/`refill_saison`). Or
  l'accumulation-log vit dans `game_state["maitrise"]`. Choisir : (a) changer la
  signature `palier_bonus(game_state, player)` partout (retouche la couche Vigueur,
  ce que §4.1 voulait éviter) ; (b) registre par-joueur mis à jour par la couche
  maîtrise et lu par `palier_bonus`. **Défaut proposé : (a)** — explicite,
  déterministe, sans état caché module-level ; à confirmer au tronçon i2.
- **Calibrage** `K`/`BASE`/`R`/atténuations/gains ponctuels = **D12.4 post-test** :
  poser des placeholders nommés, ne pas chercher les bons chiffres.

## État courant
- **2026-06-04 :** **i1 implémenté** (`sim/maitrise.py` + `tests/test_maitrise.py`
  18/18). Module pur (lib std `math` seule), purement additif, zéro hook tick.
  Décisions i1 prises : invariant « objet dans le dict ⇒ palier ≥ 1 » (absence = 0),
  auto-découverte sur `enregistrer_preuve`, consommation cumulative (reliquat reporté),
  placeholders `PREUVES_BASE=2`/`PREUVES_R=2` (courbe 2,4,8,16 — calibrage D12.4).
  **Prochain : i2** (agrégats + ponts Vigueur).
- Golden de référence à préserver : écolo `c950f06c…` / champ `b005d9ba…` /
  joueur Vigueur 87/87 (`tests/test_vigueur.py`, hash trajectoire `e63b9d7f…`).
  **Tous VÉRIFIÉS INCHANGÉS après i1.**

## Boucle
Lancer `0N` → coder → vérifier les golden → MAJ ce fichier → commit → `/clear` →
`0N+1`. Mémoire `project_status` à jour en fin de chaque tronçon.
