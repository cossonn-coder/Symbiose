# Tronçon ③ — Banc climatique (acclimatation / ombre dense)

> Sprint « bancs d'essai ». État : `00_etat.md`. `secheresse_sable` a été livré
> au ① (cette famille y a démarré). Ce tronçon ajoute les deux stress
> climatiques restants. **Golden NEUTRE attendu**.

## Objectif
Deux bancs (+ l'existant `secheresse_sable`) couvrant la famille climatique,
chacun avec oracle. Point d'attention RENDU sur le signe `ombre`.

## Périmètre — `bancs/climatique.py` (2 fabriques ajoutées)

### 1. `acclimatation()` — durcissement plastique visible (teinte glauque)
- 1 plante soumise à un stress DOUX mais PROLONGÉ (sécheresse légère ou ombre
  partielle sub-létale), assez pour que l'expression plastique monte vers
  `EXPR_MAX` sans dégât franc. La fabrique peut pré-charger une mémoire de stress
  modérée (`force_memoire`) pour atteindre la sur-expression en peu de semaines.
- Le signe `acclimatation` est GÉNÉRIQUE (un seul, intensité = plus forte
  sur-expression — `sim/semiologie.py`, fonction `acclimatation`, priorité 9 :
  s'efface derrière un signe de DÉGÂT). Donc viser un stress qui durcit SANS
  blesser, sinon `secheresse`/`ombre` masque `acclimatation`. C'est le point
  délicat du banc.
- Oracle : après N semaines, `"acclimatation" in signes(plante)` ET aucun signe
  de dégât concurrent au même plot.

### 2. `ombre_dense()` — signe `ombre` (banc ISOLÉ)
- Pourquoi isolé : une ombre installée dense étouffe toute la végétation autour
  → impossible à mêler aux autres bancs sans tout fausser (décision « mixte »).
- 1 tuile collée au flanc nord de la maison, `House(height_cm=…)` haute / proche
  pour projeter une ombre INSTALLÉE (pas un nuage passager). Plante non sciaphile
  posée dessous → `shade_memory` monte → dégât → signe `ombre`
  (`sim/semiologie.py`, fonction `ombre`, seuil `SHADE_DAMAGE_THRESHOLD`).
- ⚠️ **RENDU C# MANQUANT (dette 0.5.2)** : le moteur ÉMET le signe `ombre`, mais
  `PlantRenderer` (C#) n'a pas encore le mapping couleur/texture `ombre`. Donc au
  F5, ce banc sera **muet à l'écran** tant que la dette n'est pas levée — et c'est
  précisément ce que le banc DÉMONTRE : oracle vert + écran muet = bug rendu
  confirmé. Le NOTER dans `00_etat.md` et rappeler la dette 0.5.2 au bilan ⑤.
- Oracle : après N semaines, `"ombre" in signes(plante)`.

## Registre
`bancs/__init__.py` : ajouter `acclimatation`, `ombre_dense` à `BANCS`.

## Vérifs
- Golden inchangé `2ab026ad…`.
- `tests/bancs/test_climatique.py` : `secheresse_sable` (①) + 2 nouveaux oracles
  verts.
- `init config="acclimatation"` / `"ombre_dense"` répondent `ok`.
- Taille `bancs/climatique.py` < ~350 lignes pur.

## Sortie
MAJ `00_etat.md` : ③ clos, golden NEUTRE, **rappel dette 0.5.2** (rendu `ombre`
C# à faire pour que le banc soit visible). Commit. `/clear` avant `04_biotique.md`.
