# Tronçon ① — Bras fidélité + découplage émetteur/récepteur (dormant)

> Kickoff autosuffisant. Lire d'abord `CLAUDE.md` + `00_etat.md` (décisions
> D1-D7). Réf. conception : `docs/perf/lod/conception_perf_lod_ombre.md`.
> **Golden attendu : INTACT** (`33c0ea6f…`). Ce tronçon livre le mécanisme
> DORMANT (seuil défaut 0.0) + l'instrument de mesure. Il n'active RIEN.

## Objectif
1. Découpler récepteurs/émetteurs dans `fields/light.py:LightField.compute`,
   sous un seuil global `SHADING_POWER_MIN` (défaut **0.0** = dormant).
2. Livrer le bras fidélité `tools/diag_lod_ombre.py` (5 critères D6).
3. Verrouiller l'invariant seuil=0 (D3) par un test dédié + golden intact.

## Fichiers à toucher
- `data/code/fields/light.py` (compute) — SEUL fichier moteur modifié.
- `data/code/tools/diag_lod_ombre.py` — NOUVEAU (banc fidélité).
- `data/code/tests/test_lod_ombre.py` — NOUVEAU (invariant + mécanisme).

## Modèle (D1/D2/D3)
- Constante module dans `light.py` : `SHADING_POWER_MIN = 0.0`. Métrique de
  pouvoir ombrageant d'un `info = (p, x, y, h, radius, density)` :
  `pouvoir = h * radius * density` (= `info[3] * info[4] * info[5]`).
- Dans `compute`, après avoir bâti `infos` (plantes vivantes + squelettes debout,
  l.207-219, INCHANGÉ) :
  - `receivers = infos` (TOUTES — la réception ne change jamais) ;
  - `emitters = [t for t in infos if t[3] * t[4] * t[5] >= SHADING_POWER_MIN]`
    (préserve l'ordre de `infos`).
- **Boucle lumière reçue** (l.260-289) : `order = sorted(emitters, ...)`,
  `index = ObstacleIndex(order)` ; la boucle `for p, px, py, ph, pr, pd in …`
  itère désormais **`receivers`** (chaque récepteur reçoit toujours une valeur).
- **Scatter lumière-sol** (l.307) : `for q, qx, qy, qh, qr, qd in emitters`.
- **Cache géométrique** (`geom_key`, l.236-237) : le laisser sur `infos`
  (sur-ensemble correct — invalide dès qu'une géométrie bouge). NE PAS le
  restreindre à `emitters`.
- Référencer `SHADING_POWER_MIN` comme **global de module** (résolu à l'exécution)
  pour que le banc puisse le monkeypatcher (`light.SHADING_POWER_MIN = …`).

**Invariant D3** : à `SHADING_POWER_MIN = 0.0`, `emitters == infos` dans l'ordre
exact → `order`, l'index, le scatter et la boucle reçue voient exactement la même
séquence qu'aujourd'hui → produit multiplicatif bit-identique → golden inchangé.

## Banc `tools/diag_lod_ombre.py` (D6, 5 critères)
S'inspirer de `tools/profile_monde.py` (montage `config="full"` via
`SimServer.cmd_init`, `_build_engine_full`, `_grandir`, `_ms_tick_absolu`). Le
banc compare **LOD off** (`light.SHADING_POWER_MIN = 0.0`) vs **LOD on**
(`--seuil S`, défaut à choisir plus tard, ex. 0 pour la première exécution),
**même seed**, an 0→6 (`--week`, défaut 262). Il monte DEUX moteurs frais (un par
régime), en fixant `light.SHADING_POWER_MIN` AVANT chaque run.

Sortie (texte lisible, copiable dans un rapport) :
1. **Trajectoire N** — N vivant par saison (ou toutes les 13 sem) off vs on, +
   onset (1re bascule) + plateau an 6.
2. **Dérive `light_received`** — sur UNE scène FIGÉE (le monde an 6 d'un seul
   run) : recompute `eco.lumiere.compute` avec seuil 0 puis seuil S sur le MÊME
   monde, comparer `received` plante par plante (écart moyen + max). ⚠ NE PAS
   comparer deux runs divergents plante à plante (ils divergent en 6 ans) — la
   dérive du MODÈLE se mesure à monde figé.
3. **Self-thinning vis B** — compter les morts « carence lumineuse » (message de
   `shade_stress_damage` / journal, ou instrumenter un compteur) sur chaque run.
4. **Gain ms/tick** — `_ms_tick_absolu` an 6, off vs on.
5. **Coût germination surnuméraire** — germinations/saison (comptage) + ms/tick
   NET mesuré à l'équilibre PROPRE de chaque run (pas à N figé) : le gain
   reporté = ms/tick(on) − ms/tick(off) à leurs équilibres respectifs.

Le banc est **hors-ligne, lecture seule** (ne fige jamais rien), comme
`profile_monde`. Régime headless, quelques minutes.

## Test `tests/test_lod_ombre.py`
- **Invariant dormant** : sur une petite scène (2-3 plantes de tailles variées +
  quelques semis), `SHADING_POWER_MIN = 0.0` → snapshot `received` + grille sol ;
  fixer un seuil MINUSCULE qui ne coupe personne → identique bit à bit.
- **Mécanisme actif** : fixer un seuil ÉLEVÉ qui coupe les semis → `emitters` <
  `receivers`, ET la lumière reçue/sol des petits récepteurs AUGMENTE (ombre
  retirée) → valeurs DIFFÉRENTES (prouve que le LOD agit vraiment).
- Restaurer `SHADING_POWER_MIN` à sa valeur module en fin de test (pas de fuite
  d'état entre tests).

## À NE PAS faire
- NE PAS activer le seuil par défaut (>0) — c'est le tronçon ②.
- NE PAS toucher la maison (hors `infos`, toujours émettrice).
- NE PAS re-figer le golden ici : il doit rester `33c0ea6f…`.
- NE PAS lancer `test_epaisseur_500ans` (interdit, cf. CLAUDE.md).
- NE PAS ajouter d'état par plante ni de RNG (métrique = géométrie existante).

## Vérification de sortie
1. `python3 -m tests.test_golden` → hash **`33c0ea6f…` INTACT**.
2. `python3 -m tests.test_lod_ombre` → vert.
3. `python3 -m tools.diag_lod_ombre --seuil 0` tourne et sort les 5 blocs (à
   seuil 0, off ≡ on → dérive nulle, gain nul : sanity check du banc lui-même).
4. Golden général + suites ciblées inchangés.
5. Mettre à jour `00_etat.md` (tronçon ① fait, banc prêt, invariant vert).
