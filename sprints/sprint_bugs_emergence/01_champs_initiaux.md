# ① D56 — Champs initiaux riches & hétérogènes

> Kickoff autosuffisant. Lire AVANT : `CLAUDE.md`, `00_etat.md`,
> `docs/conception/CONCEPTION_BUGS_EMERGENCE.md` (volet S3, fix (c)).
> Source de vérité = Python `data/code/`. Lancement depuis `data/code/`.

## Objectif
Enrichir les conditions initiales des champs écologiques ET leur donner une
hétérogénéité spatiale déterministe par plot. But : (1) monde vivant dès le
départ (F5 S4, dette D56) ; (2) donner à certains secteurs assez d'OM/nutriments
initiaux pour amorcer la succession des tardifs plus tôt → succession hétérogène
(philo #7). C'est la fondation du déverrouillage S3 (tronçon ②).

## Fichiers à toucher
- `fields/ecofields/container.py` — `EcoFields.__post_init__` (init des champs) et
  `init_eco(...)`. Aujourd'hui `om_active`/`om_stable` démarrent à `0.0` partout,
  `humidite`/`microbiome` sont posés uniformes par `init_eco`, n/p/k héritent de
  `NUTRIENT_INIT_PAR_SOL`.
- `fields/ecofields/constants.py` — ajouter les constantes de calibrage (valeurs
  plancher enrichies + amplitude d'hétérogénéité).
- `fields/noise.py` — réutiliser `_hash_noise(seed, week, r, c)` (pas de nouveau
  bruit). Passer `week=0` + un canal dérivé du `tile_id` (hash du nom) pour que
  chaque tuile ait son propre motif spatial, déterministe.

## Modèle
- Enrichir les planchers de départ (calibrage à documenter dans le doc) :
  `microbiome`, un peu d'humus initial `om_stable` (sol jamais parti de zéro
  absolu), `humidite`, NPK — valeurs modestes mais non nulles.
- Hétérogénéité : pour chaque plot, moduler la valeur initiale par
  `(1 + AMPLITUDE · (2·_hash_noise(seed_tuile, 0, r, c) − 1))`, bornée ≥ 0.
  `seed_tuile` = hash déterministe du `tile_id` (le monde reste reproductible à
  seed global fixe — philo #3, #7).
- Garder `init_eco` rétrocompatible : le param `fertilite` de compat continue de
  forcer n=p=k uniformes SI fourni (le golden le fournit) ; l'hétérogénéité
  s'applique aux champs NON forcés explicitement, ou via un nouveau chemin opt-in
  documenté — choisir la voie qui garde le contrôle du re-figeage.

## Golden attendu
**RE-FIGÉ MAÎTRISÉ.** Le golden (`tests/test_golden.py`) construit son monde via
`init_eco(tid, 6, 8, humidite=2.0, fertilite=1.2, microbiome=0.3, …)` (valeurs
explicites). Si l'hétérogénéité s'applique même aux champs explicitement fournis,
le golden dérive → re-figer et CONSIGNER le nouveau hash dans le test + `00_etat.md`,
en expliquant : « conditions initiales enrichies/hétérogènes (D56) ». Si tu choisis
d'appliquer l'hétérogénéité UNIQUEMENT aux champs non forcés (om_stable,
microbiome selon le chemin), vérifier si le golden bouge — re-figer seulement s'il
bouge, sinon golden INTACT. Dans les deux cas : décision explicite, annoncée.

Suites ciblées : relancer `python3 -m tests.test_golden` + toute suite éco
(`test_population`, etc.) ; re-figer en cascade UNIQUEMENT si la dérive est
cohérente (init plus riche) et l'annoncer.

## À NE PAS faire
- Pas de RNG live : tout via `_hash_noise` déterministe (philo #3).
- Ne pas casser la reproductibilité « même seed global → même terrain » (philo #7 :
  seed d'origine persistée). L'hétérogénéité dérive du seed, pas d'un aléa.
- Ne pas toucher à la dynamique de succession (c'est le tronçon ②).

## Clôture
Mettre à jour `00_etat.md` (§REPRISE + hash golden si re-figé), marquer D56 dans
`DETTE.md` comme livré. Commit.
