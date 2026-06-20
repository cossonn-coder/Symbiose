# Sprint « sémiologie foliaire » (D33) — état partagé

> Généralise l'indice foliaire (bool `chlorose` du physico-chimie ⑨) à TOUS les
> stresseurs. Conception figée : `docs/conception/CONCEPTION_SEMIOLOGIE_FOLIAIRE.md`.
> Lire la conception AVANT tout tronçon.

## Décisions figées (Nico, 2026-06-20)
- **Cumul multi-signes** : `leaf_symptoms` = LISTE (cause, intensity), pas un signe unique.
- **Tri** : intensité décroissante, départage par priorité fixe (§2.3 conception).
- **Périmètre complet** : chroniques recalculés (golden NEUTRE) + événementiels
  mémorisés (re-figeage golden maîtrisé annoncé).
- **Invariant** : chaque détecteur réutilise le SEUIL de la mécanique qui blesse.

## Tronçons
| # | Titre | Golden | Statut |
|---|---|---|---|
| ① | détecteurs chroniques + champ `leaf_symptoms` | NEUTRE | **CLOS** (golden `e209e8d8…` inchangé) |
| ② | marques événementielles (cause typé + décroissance) | re-figeage annoncé | à faire |
| ③ | vue C# (canal couleur + texture/forme) | — | à faire |

## REPRISE
Prochain = **②** (`02_*.md`, à écrire). ① livré : `sim/semiologie.py` (détecteurs
CHRONIQUES purs) + `leaf_symptoms` au snapshot, bool `chlorose` retiré, pont 0.5.1.

## Journal de bord (MAJ en fin de chaque tronçon)
- **① (2026-06-20)** — `sim/semiologie.py` créé : 5 détecteurs chroniques PURS
  (chlorose/sécheresse/asphyxie/ravageurs/sénescence), chacun rampe sur le SEUIL
  MÊME de la mécanique qui blesse (DRY §2.4 : CHLOROSE_PH/SEUIL_ACIDOPHILE,
  DROUGHT_DAMAGE_THRESHOLD, ASPHYXIE_HEALTH_SEUIL, floor herbivory, SENESCENCE_ONSET).
  `leaf_symptoms` = liste triée `(intensité desc, PRIORITE fixe)`. `serialize._snapshot`
  remplace `base["chlorose"]=bool` par `base["leaf_symptoms"]=…` ; import des seuils
  chlorose retiré au profit de `from sim import semiologie`. Pont bump **0.5.1**
  (schéma étendu, champ optionnel côté vue).
  - **Golden NEUTRE confirmé** : `e209e8d8…` inchangé (recalcul lecture pure).
  - Smoke : 25 plantes vivantes du monde golden → toutes `leaf_symptoms == []`,
    0 chlorose (espèces neutres), clé `chlorose` disparue. Détecteurs vérifiés
    actifs sous stress forcé (rampes + tri + cumul OK, annuelle → sénescence 0).
  - `dotnet build` vert (la vue lit encore `chlorose`, champ optionnel → pas de
    crash ; retrait C# au ③).
  - NB : `tools/compte_ldc.py` (cité par CLAUDE.md) est ABSENT du dépôt ; module
    158 lignes brutes, ~⅔ commentaires pédago → code pur largement < 350.
