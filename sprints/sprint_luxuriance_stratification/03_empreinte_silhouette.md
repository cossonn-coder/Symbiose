# Tronçon 3 — Empreinte propre à l'espèce (silhouette + override ciblé)

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` (D3) +
> `docs/conception/CONCEPTION_LUXURIANCE_STRATIFICATION.md §2.4`.
> **Golden : NEUTRE** (overrides limités aux espèces hors scénario golden).

## Objectif
Donner à chaque espèce sa **forme au sol** : un descripteur `silhouette` (lu par
le rendu au tronçon 6) + un **override d'empreinte CIBLÉ** là où le défaut de
strate ment. On NE crée PAS de champ écologique concurrent : `canopy_r` pilote
déjà ombre + uptake.

## Modèle
- **Descripteur silhouette** — nouveau champ data sur `PlantBase` :
  `silhouette ∈ {"touffe", "rosette", "étalée", "dressée", "tapis", "buisson"}`
  (défaut cohérent avec la strate mature). Pur descripteur, aucun effet moteur ici
  (le renderer C# le consommera au tronçon 6, exposé via le pont).
- **Override d'empreinte ciblé** — pour les espèces dont l'étalement au sol dévie
  du défaut de strate, override `canopy_r` (ou un multiplicateur d'empreinte au
  sol) sur la classe/stade. Cas concret : **courge/courgette** = strate `basse`
  mais **s'étale** → `canopy_r` élargi. Rester CIBLÉ (quelques espèces), **ne PAS
  toucher les espèces du golden** (Tomato, Basil, Bean, Sunflower, Pepper, Yarrow,
  Phacelia, Clover, AppleTree) → dérive NEUTRE.

## Fichiers à toucher
- `plants/base/` (champ `silhouette` sur `PlantBase`, défauts par strate).
- `plants/species/potageres.py` (Courgette → override empreinte étalée + silhouette
  `"étalée"`).
- Attribuer `silhouette` aux espèces existantes de façon cohérente (défaut par
  strate mature suffit ; override explicite seulement là où c'est parlant). Rester
  léger.

## Golden — NEUTRE
Aucune espèce du scénario golden n'est modifiée dans son empreinte. `silhouette`
n'a aucun effet moteur. Vérifier `python3 -m tests.test_golden` **inchangé**. Si le
golden bouge → une espèce du scénario a été touchée par erreur → corriger.

## Ce qu'il NE faut PAS faire
- Pas de nouveau champ écologique « empreinte au sol » distinct de `canopy_r` (D3).
- Pas de rendu (tronçon 6 consommera `silhouette`).
- Ne pas toucher l'empreinte des espèces du golden.

## Fin de tronçon
MAJ `00_etat.md` (§REPRISE, golden inchangé confirmé), commit.
