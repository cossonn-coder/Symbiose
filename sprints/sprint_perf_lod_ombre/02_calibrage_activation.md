# Tronçon ② — Calibrage du seuil + activation

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` (D1-D7) + le tronçon ①
> (déjà livré : découplage dormant + banc `diag_lod_ombre` + invariant seuil=0).
> Réf. : `docs/conception/CONCEPTION_PERF_LOD_OMBRE.md`.
> **Golden : RE-FIGÉ maîtrisé et annoncé** (dérive localisée, cf. §6 conception).

## Objectif
Choisir `SHADING_POWER_MIN` dans la zone « ombre coupée individuellement
négligeable » qui tient la trajectoire N dans la bande **±15 %** de ~613/an6
(D5), l'activer par défaut, puis consigner gain net + dérive.

## Méthode (piloter par le banc, pas à l'aveugle)
1. Lancer `python3 -m tools.diag_lod_ombre --seuil S` pour plusieurs S croissants
   (balayage : commencer bas, ex. quelques unités, monter). Pour chaque S,
   relever les 5 critères (trajectoire N off/on, dérive `light_received`, morts
   vis B, ms/tick net, germination/saison).
2. **Critère de choix** : le plus GRAND S tel que —
   - le plateau N an 6 (on) reste dans **[≈520, ≈705]** (±15 % de 613) ;
   - la dérive `light_received` (scène figée) reste faible (ombres coupées
     individuellement négligeables — c'est la garantie de fidélité) ;
   - la vis B ne s'effondre pas (morts « carence lumineuse » du même ordre) ;
   - le gain ms/tick NET (à l'équilibre propre) est franc.
   Un S plus grand gagne plus de perf mais dérive plus → prendre le point où le
   gain marginal ne vaut plus la dérive. Rester du côté conservateur si doute.
3. Fixer `SHADING_POWER_MIN = <valeur choisie>` par défaut dans `fields/light.py`.

## Re-figeage golden (maîtrisé, annoncé)
Activer le seuil change la lumière reçue/sol de quelques plantes/plots (ombres
sous-seuil disparues) → **le golden bouge**. C'est prévu (D3/§6). Procédure :
1. Lancer `python3 -m tests.test_golden`, récupérer le NOUVEAU hash.
2. Le figer dans le test (comme les re-figeages précédents), avec un commentaire
   pédagogique : « re-figé au sprint LOD ombre D67 — dérive localisée (ombres
   sous-seuil retirées), seuil `SHADING_POWER_MIN=<S>`, N tenu dans ±15 % ».
3. Re-figer aussi le digest satellite **`population_hash`** (même cause).
4. Vérifier que les **invariants structurels** du golden (non-hash : nb de suites,
   assertions de forme) restent verts — seule la valeur de hash change.

## Consignation
- `00_etat.md` : valeur `SHADING_POWER_MIN` retenue, nouveaux hash (golden +
  population), gain ms/tick net mesuré, dérive N mesurée (off→on), dérive
  `light_received` moy/max.
- Reporter le gain + la dérive dans la conception (§4) et préparer la mise à jour
  DETTE D67 (faite en clôture de sprint).

## À NE PAS faire
- NE PAS toucher le calibrage férale D69 (`GERM_PRESSION_FERALE`) — sauf si N
  DÉPASSE FRANCHEMENT la bande, auquel cas S'ARRÊTER et remonter à Nico (ne pas
  décider seul de rouvrir D69).
- NE PAS re-figer d'autres hash que golden + population_hash.
- NE PAS lancer `test_epaisseur_500ans` (interdit).

## Vérification de sortie
1. `python3 -m tests.test_golden` → NOUVEAU hash figé, vert.
2. Test invariant `tests/test_lod_ombre` (mécanisme) → toujours vert.
3. `diag_lod_ombre --seuil <S>` → N dans la bande, gain net franc consigné.
4. `00_etat.md` mis à jour (valeur seuil, hash, gain, dérive).
