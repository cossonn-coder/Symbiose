# Tronçon ② — Marques événementielles (mémorisation décroissante)

> Sprint « sémiologie foliaire ». Conception :
> `docs/conception/CONCEPTION_SEMIOLOGIE_FOLIAIRE.md` (§2.5, §5).
> Lire la conception + faire ① d'abord. **Re-figeage golden maîtrisé ANNONCÉ.**

## Objectif
Exposer les symptômes ÉVÉNEMENTIELS — `maladie`, `gel`, `grele` — qui n'ont pas
d'état persistant relisible. Les MÉMORISER sur la plante sous forme de marque
décroissante (option A), puis les fusionner dans `leaf_symptoms`.

## Travail
1. `sim/effects/mutations.py` : `ReduceHealth` gagne un champ `cause: str = ""`
   (enum canonique), à côté du `reason` humain de log (inchangé).
2. Annoter les sites qui produisent un symptôme événementiel :
   - `perturbations.py:139` « maladie fongique » → `cause="maladie"`.
   - `aleas.py:112` (aléas de type `health`) : mapper `alea.nom` → cause
     (« Gelée tardive » → `gel`, « Grêle » → `grele`). Les autres aléas santé
     sans signe foliaire (mortalité de fond, fonte) → `cause=""` (pas de marque).
   - NE PAS annoter « stress hydrique sévère » ni « herbivorie » : déjà couverts
     par les détecteurs CHRONIQUES du ① (pas de double comptage).
3. `plants/base.py` (`PlantInstance`) : champ `symptom_marks: dict[str, float]`
   (init `{}`). Méthode de décroissance `decay_symptoms(DECAY)` (purge sous epsilon).
4. `sim/effects/resolution.py:232` (branche `ReduceHealth`) : si `m.cause`, faire
   `marks[m.cause] = min(1.0, marks.get(m.cause,0) + m.amount * GAIN)`.
   Knobs : `GAIN ≈ 0.5`, `DECAY ≈ 0.8`, epsilon `≈ 0.02` (calibrage, commentés).
5. Appeler `decay_symptoms` une fois par tick de plante (placer dans la boucle
   de tick existante, à côté des autres mémoires — chercher où `drought_memory`/
   `asphyxie_memory` décroissent pour cohérence).
6. `sim/semiologie.py` : l'agrégateur `leaf_symptoms` lit AUSSI `plant.symptom_marks`
   (événementiels) et les fusionne avec les détecteurs chroniques avant le tri.
   Pas de bump pont (schéma `leaf_symptoms` inchangé, seul le CONTENU s'enrichit).

## Vérifs
- `python3 -m tests.test_golden` : un re-figeage est attendu SI le scénario smoke
  déclenche gel/grêle/maladie. **Procédure** : lancer, constater la dérive,
  l'EXPLIQUER (quel événement, quelle plante, quelle marque), re-figer le hash
  de façon ANNONCÉE dans le commit + `00_etat.md`. Si AUCUN événement déclenché →
  golden NEUTRE (l'annoncer aussi). Toute dérive doit être localisée et comprise.
- Vérifier qu'une plante touchée puis épargnée voit sa marque décroître à 0 sur
  quelques ticks (test ciblé recommandé si un fichier de test thématique existe).
- `dotnet build Symbiose.csproj` reste vert.

## Sortie
MAJ `00_etat.md` (statut ② = clos, NOUVEAU hash golden + justification, journal).
Commit. `/clear`.
