# CONCEPTION — Sémiologie visuelle des signes diégétiques (rendu)

> ## 🅿️ STATUT : PARKÉ le 2026-06-24
> Conception **interrompue volontairement** au profit du doc « Rendu du feuillage et
> des organes végétaux par espèce » (jugé prioritaire par Nico). Ce fichier est une
> **photo fidèle de l'état d'avancement** — un brouillon partiellement décidé, à
> **reprendre tel quel** ensuite. Suivi en dette : voir `DETTE.md` (D48).
> **Aucun dev associé.** Rien n'est figé tant que la reprise n'a pas eu lieu.

Cap : **compléter et unifier la traduction en pixels** des signes de souffrance/réponse
émis par le moteur. Couche **B** (pixellisation, `visuals/PlantRenderer.*`) — la couche
**A** (le modèle moteur : détecteurs, champ `leaf_symptoms`, intensité) est figée par
[`CONCEPTION_SEMIOLOGIE_FOLIAIRE.md`](CONCEPTION_SEMIOLOGIE_FOLIAIRE.md) (D33, clos) et
n'est **pas** retouchée ici.

Postérieur à D33 et couplé au **rendu pixel-art** : les teintes de symptôme cohabitent
désormais avec la palette 16-bit (rampes + hue-shift) introduite au SS② —
cf. [`CONCEPTION_RENDU_PIXELART.md`](CONCEPTION_RENDU_PIXELART.md) §5.

**Golden trivialement préservé** : rendu = vue passive, zéro moteur touché.

## Décisions déjà prises (au moment du parking)

- **Doc distinct** (≠ extension de FOLIAIRE) — FOLIAIRE est clos et décrit le *modèle
  moteur* ; ici on travaille la *complétude du mapping rendu* + la *cohabitation palette*,
  nés **après** D33.
- **Périmètre ÉLARGI** (choix Nico) : revue de TOUS les signes + cohérence palette SS²
  + cadre d'extension futur — pas seulement le trou `ombre`.
- **Concevoir en parallèle** du SS② palette (qui est codé mais attend son F5 + commit).

## Questions ouvertes (à trancher à la reprise)

- **(a)** ~~doc distinct vs extension~~ → **tranché : distinct.**
- **(b)** teinte `ombre` proposée `~b8c8a0` (vert pâle délavé, distinct du jaune chlorose,
  de l'orange sénescence, du glauque acclimatation) — **à valider.**
- **(c)** `ombre` en **couleur seule** (couche B), morpho étirée (entre-nœuds longs) laissée
  à la couche A future — **à valider.**

## §0 — État des lieux (inventaire moteur ↔ vue)

Signes émis par le moteur (`sim/semiologie.py`) — 7 chroniques + 3 événementiels :
`chlorose, secheresse, asphyxie, ravageurs, ombre, senescence, acclimatation`
+ `maladie, gel, grele`.

| Cause (moteur) | Canal couleur (`ColorantTints`) | Canal texture/forme | État vue |
|---|---|---|---|
| chlorose | jaune inter-nervaire ✓ | — | OK |
| asphyxie | brun-vert terne ✓ | — | OK (intensité ? → C2) |
| secheresse | beige flétri ✓ | affaissement (feuille abaissée ∝ intensité) ✓ | OK |
| senescence | jaune-rouge ✓ | — | OK |
| maladie | brun tacheté ✓ | (taches ?) | OK |
| acclimatation | glauque cire ✓ | — | OK |
| ravageurs | — | criblage ✓ | OK (floor bas → C3) |
| gel | — | bords noircis ✓ | OK |
| grele | — | criblage ✓ | OK |
| **ombre** | **— RIEN** | **— RIEN** | **🔴 ignoré silencieusement (dette 0.5.2)** |

## §1 — Principes (hérités de D33)

Deux canaux pour un cumul lisible : **COULEUR** = un seul colorant dominant (plus forte
intensité, pas de mélange boueux) ; **TEXTURE/FORME** = additifs cumulables. Le bois n'est
jamais teinté. Tout déterministe (hash). Philo #5/#6 : voir → hypothèse → cause.

## §2 — `ombre` / étiolement (le trou, dette 0.5.2)

- **Bio** : à l'ombre, la plante s'**étiole** — entre-nœuds allongés, tiges grêles,
  **feuilles pâles et anémiées** (moins de chlorophylle), port tiré vers la lumière.
- **Rendu couche B (C#)** : sans toucher la géométrie, on ne joue que sur la **couleur**.
  → entrée `ColorantTints["ombre"]` = **vert pâle délavé désaturé** (proposé `~b8c8a0`).
- **Morphologie étirée** = couche A Python (entre-nœuds longs) → **hors scope rendu**,
  déjà partiellement émergente via le phototropisme du moteur. Extension future.

## §3 — Affaissement sécheresse (DÉJÀ FAIT)

> Correction 2026-06-24 : contrairement à une 1ʳᵉ lecture, l'affaissement EST implémenté
> — `Organs.cs:134-136` abaisse la feuille (`lz -= _drought * DroughtDroopCm`) ∝ intensité,
> dans la boucle de placement (pas dans `DrawLeafDamage`). Plus un trou. Reste éventuellement
> à affiner l'amplitude au F5.

## §4 — Interaction avec la palette SS² (le point « élargi »)

Ordre actuel : `SymptomTint(albédo)` → puis `HueShift`/`DrawVolume` (lumière + volume).
C'est le bon ordre (symptôme = couleur de base, éclairage par-dessus). **Risque à valider
au F5** : le hue-shift d'ombre tire vers le **bleu froid** → côté nord, un symptôme jaune
pourrait verdir et perdre en lisibilité. Repli : atténuer la force du hue-shift quand
`_colorAmount` est fort.

## §5 — Diagnostic C2/C3 (protocole F5)

Tableau cause → attendu écran → verdict, à instrumenter avec les bancs d'essai (oracle vert
moteur ↔ écran muet = bug rendu). C2 = vérifier l'intensité asphyxie ; C3 = comparer témoin
vs infesté.

## §6 — Cadre d'extension

`carence_n/_k`, `etiolement`, `famine` (D41) : ajout = **une ligne** dans `ColorantTints`
ou un `case` texture, schéma snapshot intact (forward-compat §7 de D33 déjà prévu).

## §7 — Tronçonnage (golden trivialement préservé, rendu pur vue)

- **T1** `ombre` (couleur) — lève la dette 0.5.2.
- **T2** revue maladie (taches ?) — (l'affaissement sécheresse est déjà fait, cf. §3).
- **T3** cohérence palette SS² + diagnostic F5 C2/C3.

## Liens

- Modèle moteur : `CONCEPTION_SEMIOLOGIE_FOLIAIRE.md` (D33, clos).
- Palette : `CONCEPTION_RENDU_PIXELART.md` §5 (SS②).
- Dettes : 0.5.2 (mapping `ombre`), D47 (C2/C3/ombre → rendu C#), D48 (ce doc parké).
