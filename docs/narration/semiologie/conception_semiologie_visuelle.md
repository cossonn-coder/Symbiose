# CONCEPTION — Sémiologie visuelle des signes diégétiques (rendu)

> **STATUT : repris et figé le 2026-06-24** (après parking du même jour). Toutes
> les questions ouvertes sont tranchées, le doc est prêt à implémenter
> (tronçonnage §8). Suivi : `DETTE.md` (D48).

Cap : **compléter et unifier la traduction en pixels** des signes de souffrance/
réponse émis par le moteur. Couche **B** (pixellisation, `visuals/PlantRenderer.*`)
— la couche **A** (le modèle moteur : détecteurs, champ `leaf_symptoms`, intensité)
est figée par [`CONCEPTION_SEMIOLOGIE_FOLIAIRE.md`](CONCEPTION_SEMIOLOGIE_FOLIAIRE.md)
(D33, clos) et n'est **pas** retouchée ici.

Postérieur à D33 et couplé au **rendu pixel-art** : les teintes de symptôme
cohabitent désormais avec la palette 16-bit (rampes + hue-shift) introduite au
SS② — cf. [`CONCEPTION_RENDU_PIXELART.md`](CONCEPTION_RENDU_PIXELART.md) §5.

**Golden trivialement préservé** : rendu = vue passive, zéro moteur touché.

## Décisions (figées)

- **Doc distinct** (≠ extension de FOLIAIRE) — FOLIAIRE est clos et décrit le
  *modèle moteur* ; ici on travaille la *complétude du mapping rendu* + la
  *cohabitation palette*, nés **après** D33.
- **Périmètre ÉLARGI** (choix Nico) : revue de TOUS les signes + cohérence palette
  SS² + cadre d'extension futur — pas seulement le trou `ombre`.
- **Conçu en parallèle** du SS② palette (désormais committé, `23b5613`).
- **(b)** teinte `ombre` = **`b8c8a0`** (vert pâle délavé désaturé, distinct du
  jaune chlorose, de l'orange sénescence, du glauque acclimatation) — **validé**.
- **(c)** `ombre` = **couleur + texture** : teinte `b8c8a0` (canal couleur) **+**
  texture « limbe chétif » (canal texture) — **validé**. La morpho étirée
  (entre-nœuds longs) reste couche A future, hors scope.
- **T2** : `maladie` gagne une **texture « taches »** (cryptogamie ponctuée),
  en plus de sa teinte brune — **validé**.

## §0 — État des lieux (inventaire moteur ↔ vue)

Signes émis par le moteur (`sim/semiologie.py`) — 7 chroniques + 3 événementiels :
`chlorose, secheresse, asphyxie, ravageurs, ombre, senescence, acclimatation`
+ `maladie, gel, grele`.

| Cause (moteur) | Canal couleur (`ColorantTints`) | Canal texture/forme | État vue |
|---|---|---|---|
| chlorose | jaune inter-nervaire ✓ | — | OK |
| asphyxie | brun-vert terne ✓ | — | OK (intensité ? → §6 C2) |
| secheresse | beige flétri ✓ | affaissement (feuille abaissée ∝ intensité) ✓ | OK |
| senescence | jaune-rouge ✓ | — | OK |
| maladie | brun tacheté ✓ | **taches (à ajouter, §3/T2)** | 🟠 couleur OK, texture à faire |
| acclimatation | glauque cire ✓ | — | OK |
| ravageurs | — | criblage ✓ | OK (floor bas → §6 C3) |
| gel | — | bords noircis ✓ | OK |
| grele | — | criblage ✓ | OK |
| **ombre** | **`b8c8a0` (à ajouter, §2/T1)** | **limbe chétif (à ajouter, §2/T1)** | 🟠 conçu, à coder (dette 0.5.2) |

## §1 — Principes (hérités de D33)

Deux canaux pour un cumul lisible : **COULEUR** = un seul colorant dominant (plus
forte intensité, pas de mélange boueux) ; **TEXTURE/FORME** = additifs cumulables.
Le bois n'est jamais teinté. Tout déterministe (hash). Philo #5/#6 : voir →
hypothèse → cause.

## §2 — `ombre` / étiolement (trou, dette 0.5.2)

- **Bio** : à l'ombre, la plante s'**étiole** — entre-nœuds allongés, tiges grêles,
  **feuilles pâles et anémiées** (moins de chlorophylle), port tiré vers la lumière.
- **Canal COULEUR** : entrée `ColorantTints["ombre"]` = **`b8c8a0`** (vert pâle
  délavé désaturé). Partage le canal couleur (colorant dominant) avec les autres
  symptômes — une chlorose plus intense le masque, mais sur une plante seulement
  ombragée le délavé révèle l'étiolement.
- **Canal TEXTURE — « limbe chétif »** : nouveau canal `_ombre`, additif, qui
  **réduit le rayon de la calotte éclairée** du volume de la feuille
  ∝ intensité (render-only, **aucune géométrie moteur touchée**). La feuille paraît
  amincie/affaiblie. **Borne E4** : la réduction est plancher­née pour conserver
  ≥ 2 valeurs (ombre + calotte) — jamais d'aplat, même à intensité maximale.
- **Morphologie étirée** (entre-nœuds longs) = couche A Python → **hors scope
  rendu**, déjà partiellement émergente via le phototropisme du moteur. Extension
  future.

## §3 — `maladie` / taches cryptogamiques (T2)

- **Bio** : les maladies cryptogamiques sont **ponctuées** (taches, pustules) —
  un lavis brun uni ne le rend pas, et se confond avec le brun-vert de l'asphyxie.
- **Canal COULEUR (déjà là)** : `ColorantTints["maladie"]` = `8a6a4a` (brun),
  inchangé.
- **Canal TEXTURE — « taches »** : nouveau canal `_maladie`, additif, posé dans
  `DrawLeafDamage` à côté du criblage : un **semis de petites taches brun foncé**
  par **hash** ∝ intensité. Rend le « tacheté » littéral et **distingue
  visuellement** `maladie` (ponctué) de `asphyxie` (uniforme) — lisibilité
  philo #5/#6.
- Cumulable avec les autres textures (criblage, bords gelés) sans conflit (additif).

## §4 — Affaissement sécheresse (DÉJÀ FAIT)

> L'affaissement EST implémenté — `Organs.cs:134-136` abaisse la feuille
> (`lz -= _drought * DroughtDroopCm`) ∝ intensité, dans la boucle de placement
> (pas dans `DrawLeafDamage`). Pas un trou. Reste éventuellement à affiner
> l'amplitude au F5.

## §5 — Interaction avec la palette SS² (le point « élargi »)

Ordre actuel : `SymptomTint(albédo)` → puis `HueShift`/`DrawVolume` (lumière +
volume). C'est le bon ordre (symptôme = couleur de base, éclairage par-dessus).
**Risque à valider au F5** : le hue-shift d'ombre tire vers le **bleu froid** →
côté nord, un symptôme jaune pourrait verdir et perdre en lisibilité. Repli :
atténuer la force du hue-shift quand `_colorAmount` est fort.

> Note `ombre` × SS² : le délavé `b8c8a0` est proche du froid du hue-shift d'ombre
> — au F5, vérifier qu'il reste distinct côté nord (sinon relever légèrement sa
> valeur/chaleur). C'est exactement le risque générique ci-dessus appliqué à `ombre`.

## §6 — Diagnostic C2/C3 (protocole F5)

Tableau cause → attendu écran → verdict, à instrumenter avec les bancs d'essai
(oracle vert moteur ↔ écran muet = bug rendu). C2 = vérifier l'intensité asphyxie ;
C3 = comparer témoin vs infesté.

## §7 — Cadre d'extension

`carence_n/_k`, `etiolement`, `famine` (D41) : ajout = **une ligne** dans
`ColorantTints` ou un `case` texture, schéma snapshot intact (forward-compat §7 de
D33 déjà prévu).

## §8 — Tronçonnage (golden trivialement préservé, rendu pur vue)

| Tr | Contenu | § | Couche | Exigence |
|----|---------|---|--------|----------|
| **T1** | `ombre` — teinte `b8c8a0` (`ColorantTints`) + canal texture `_ombre` (limbe chétif, calotte réduite plancherée) | §2 | B pure | lève dette 0.5.2 |
| **T2** | `maladie` — canal texture `_maladie` (semis de taches par hash) | §3 | B pure | distingue de l'asphyxie |
| **T3** | cohérence palette SS² + diagnostic F5 C2/C3 | §5, §6 | B pure | lisibilité |

(L'affaissement sécheresse est déjà fait, cf. §4 — pas de tronçon.)

## Liens

- Modèle moteur : `CONCEPTION_SEMIOLOGIE_FOLIAIRE.md` (D33, clos).
- Palette : `CONCEPTION_RENDU_PIXELART.md` §5 (SS②, committé `23b5613`).
- Rendu feuillage (forme/couleur/nervures par espèce) :
  [`CONCEPTION_RENDU_FEUILLAGE.md`](CONCEPTION_RENDU_FEUILLAGE.md).
- Dettes : 0.5.2 (mapping `ombre`), D47 (C2/C3/ombre → rendu C#), D48 (ce doc).
