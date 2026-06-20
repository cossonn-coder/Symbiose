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
| ② | marques événementielles (cause typé + décroissance) | **NEUTRE** (cf. ci-dessous) | **CLOS** (golden `e209e8d8…` inchangé) |
| ③ | vue C# (canal couleur + texture/forme) | — | à faire |

## REPRISE
Prochain = **③** (`03_*.md`, à écrire) : vue C# `PlantRenderer` — canal couleur
(généralise `Chlorotic`/`SetChlorose`) + canaux texture/forme additifs, retrait du
bool chlorose côté C#. ① + ② livrés côté moteur : `leaf_symptoms` (chroniques +
événementiels) est complet au snapshot, pont 0.5.1 (schéma inchangé au ②).

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
- **② (2026-06-20)** — marques ÉVÉNEMENTIELLES (maladie/gel/grêle) mémorisées et
  décroissantes. `ReduceHealth` gagne `cause: str` typé (à côté du `reason` de log,
  mutations.py). `PlantInstance.symptom_marks: dict` + `decay_symptoms(decay)`
  (instance.py). Résolution : une cause non vide fait `marks[c] += amount·GAIN`
  (resolution.py, `SYMPTOM_MARK_GAIN=0.5`) ; décroissance `·DECAY` une fois par tick
  dans `_update_physiology` (croissance.py, `SYMPTOM_DECAY=0.8`, purge sous epsilon
  0.02 ; demi-vie ~3 sem). `semiologie.leaf_symptoms` FUSIONNE marques + chroniques
  avant le tri (causes disjointes, PRIORITE déjà complète). Sites annotés :
  perturbations.py (`maladie`), **mortalite.py `_mediated_damage` + boucle.py
  (`gel`/`grele`)**, aleas.py (mapping `EVENT_CAUSE`, herbivorie→"").
  - **ÉCART au kickoff (assumé)** : le kickoff visait `aleas.py:112` pour gel/grêle,
    mais le dégât réel gel/grêle passe désormais par `_mediated_damage` (refactor
    météo médiée) — la voie `health` d'aleas ne porte plus que l'herbivorie
    (Limaces/Chenilles → cause "", déjà couverte par le détecteur chronique). J'ai
    donc annoté les VRAIS sites (`_mediated_damage`) + gardé un mapping défensif
    dans aleas. Sans ça, gel/grêle n'auraient jamais marqué.
  - **Golden NEUTRE** (et non re-figeage) : `e209e8d8…` inchangé. Raison : les
    marques ne sont PAS dans `_PLANT_ATTRS` (test_golden) et ne rebouclent jamais
    sur santé/croissance → pur affichage. Le re-figeage anticipé n'a pas lieu d'être.
  - Vérifs : gain→décroissance→purge validés en inline (gel 0.5 → demi-vie 3 ticks,
    fusion `leaf_symptoms` OK). `dotnet build` vert. test_golden PASS.
  - NB échecs PRÉ-EXISTANTS (HEAD propre, hors ②) : test_senescence (Pommier mort
    « autre » à 34,3 ans) ; test_sim_server 183/185 (`engine_version` attend 0.5.0
    stale vs 0.5.1 du ① ; nouaison Pommier pré-âgé). À traiter hors sprint.
