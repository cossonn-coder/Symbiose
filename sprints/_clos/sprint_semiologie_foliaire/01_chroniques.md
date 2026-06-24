# Tronçon ① — Détecteurs chroniques + champ `leaf_symptoms`

> Sprint « sémiologie foliaire ». Conception :
> `docs/conception/CONCEPTION_SEMIOLOGIE_FOLIAIRE.md` (§2.1-2.4, §5, §6).
> Lire la conception d'abord. **Golden NEUTRE attendu** (lecture pure).

## Objectif
Remplacer le bool `chlorose` du snapshot par une LISTE `leaf_symptoms`
`[{cause, intensity}]` alimentée par des détecteurs PURS des stresseurs
**chroniques** (état persistant relu à l'instant du snapshot, zéro écriture
moteur — même propriété que le ⑨).

## Périmètre (5 détecteurs chroniques)
- `chlorose` — porter le prédicat existant (`serialize.py:117`, miroir
  `sim/vigueur_plante.qi_local`), passer de bool à intensité (rampe sur
  `CHLOROSE_PH 7.6` / `SEUIL_ACIDOPHILE 5.5`, `fields/ecofields/constants.py`).
- `secheresse` — rampe sur l'humidité basse / `drought_memory` (réutiliser le
  seuil de `perturbations.py` « stress hydrique sévère »). Couvre la canicule.
- `asphyxie` — rampe sur `asphyxie_memory` / excès d'eau (`HUM_EXCES`).
- `ravageurs` — rampe sur `herbivory_pressure` (`perturbations.py:190`, densité
  locale `ravageur + chenille`).
- `senescence` — âge relatif à la longévité + déclin de santé (courbe D27).

## Travail
1. Créer `sim/semiologie.py` : module PUR. Une fonction par détecteur
   `(plant, eco, saison) -> float` (intensité [0,1], 0 = absent) réutilisant le
   SEUIL de la mécanique correspondante (DRY, §2.4). Un agrégateur
   `leaf_symptoms(plant, eco, saison) -> list[dict]` qui collecte les intensités
   > 0, trie par `(intensity desc, PRIORITE[cause])` (ordre §2.3).
   - Respecter la règle de couches : `sim` peut importer `fields`/`plants`.
   - Garde-fou taille : viser < ~350 lignes code pur (commentaires pédago exclus).
2. `tools/simserver/serialize.py:_snapshot` : remplacer le bloc
   `base["chlorose"] = …` par `base["leaf_symptoms"] = semiologie.leaf_symptoms(p, eco, saison)`.
   Retirer l'import devenu inutile s'il n'est plus utilisé ailleurs.
3. `tools/simserver/version.py` : bump `0.5.1`, commentaire de changelog
   (schéma ÉTENDU : `chlorose` bool retiré → `leaf_symptoms` liste ; champ
   optionnel côté vue, tolérance pré-0.5.1).

## Vérifs
- `python3 -m tests.test_golden` depuis `data/code/` → **golden inchangé**
  (`f7e1a9b4…` ou hash courant ; aucune écriture moteur). Si dérive : STOP,
  c'est un bug (un détecteur écrit quelque part).
- Smoke : les espèces neutres (ph_opt ≥ 5.5) ne produisent AUCUN symptôme
  chlorose ; vérifier qu'une liste vide sort bien `[]` (plante saine).
- `dotnet build Symbiose.csproj` reste vert (la vue lit encore `chlorose` mais
  champ optionnel → pas de crash ; le retrait C# se fait au ③).

## Sortie
MAJ `00_etat.md` (statut ① = clos, hash golden, journal). Commit. `/clear`.
