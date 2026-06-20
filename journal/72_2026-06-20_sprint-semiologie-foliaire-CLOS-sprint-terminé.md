# 2026-06-20 — Sprint « sémiologie foliaire » (D33) — ①②③ TOUS CLOS, sprint terminé

> Conception : `docs/conception/CONCEPTION_SEMIOLOGIE_FOLIAIRE.md` (figée 2026-06-20).
> Généralise la chlorose `bool` du physico-chimie ⑨ à TOUT le vocabulaire de
> symptômes foliaires. Promeut et clôt la dette **D33**.

## Intuition

Une plante qui souffre **le montre** sur son feuillage, et chaque cause a un
**signe distinct** : pas une jauge de santé unique, un **vocabulaire** (philo #5
indices visuels en HUD primaire ; philo #6 observer → hypothèse → cause). Voir le
signe → consulter → trouver la cause. Le symptôme est une **LECTURE** d'un flux /
d'une contrainte (philo #2), jamais un malus direct ; déterministe (philo #3).

## Décisions figées (Nico)

- **Cumul multi-signes** : `leaf_symptoms` = LISTE `{cause, intensity}`, pas un
  signe unique. Plusieurs entrées coexistent.
- **Tri** : intensité décroissante, départage par **priorité fixe**
  (`asphyxie > secheresse > maladie > ravageurs > gel > grele > chlorose > senescence`).
- **Invariant DRY central** : chaque détecteur réutilise le **SEUIL MÊME** de la
  mécanique qui blesse → le signe ne peut jamais mentir vis-à-vis de la simulation.
- **Périmètre complet** : chroniques recalculés (golden NEUTRE) + événementiels
  mémorisés/décroissants.

## Ce qui a été fait

**① Détecteurs CHRONIQUES purs (golden NEUTRE).** `sim/semiologie.py` — 5
détecteurs (`chlorose`/`secheresse`/`asphyxie`/`ravageurs`/`senescence`), chacun
rampant sur le seuil de sa mécanique (CHLOROSE_PH/SEUIL_ACIDOPHILE,
DROUGHT_DAMAGE_THRESHOLD, ASPHYXIE_HEALTH_SEUIL, floor herbivorie,
SENESCENCE_ONSET). Agrégateur `leaf_symptoms` trié `(intensité desc, PRIORITE)`.
`serialize._snapshot` remplace `chlorose: bool` par `leaf_symptoms: list`. Pont
**0.5.1**. Golden NEUTRE `e209e8d8…` (lecture pure dans `_snapshot`).

**② Marques ÉVÉNEMENTIELLES mémorisées et décroissantes (golden NEUTRE).**
`ReduceHealth` gagne un `cause: str` typé (à côté du `reason` de log) ;
`PlantInstance.symptom_marks: dict` + `decay_symptoms` (gain `·0.5` à la
résolution, décroissance `·0.8`/tick, purge sous epsilon, demi-vie ~3 sem).
Sites annotés : `perturbations.py` (maladie), `mortalite._mediated_damage` +
`boucle.py` (gel/grêle — la voie réelle du dégât météo médié, écart assumé au
kickoff qui visait `aleas.py`). `semiologie.leaf_symptoms` fusionne marques +
chroniques avant le tri. Golden NEUTRE (et non re-figeage) : les marques ne sont
pas dans `_PLANT_ATTRS` et ne rebouclent jamais sur santé/croissance → pur
affichage ; le scénario smoke 2 tuiles × 4 ans ne déclenche aucun gel/grêle/maladie.

**③ Vue C# — deux canaux séparés (C# pur, golden NEUTRE par construction).**
`PlantRenderer.cs` : bool `_chlorose`/`SetChlorose`/`Chlorotic` RETIRÉS →
`SetSymptoms(Godot.Collections.Array)` qui lit `leaf_symptoms` et le résout en :
- **Canal COULEUR** : registre `ColorantTints` (chlorose jaune inter-nervaire /
  asphyxie brun-vert terne / sécheresse beige désaturé / sénescence jaune-rouge /
  maladie brun tacheté). Le colorant de plus FORTE intensité gagne (pas de
  mélange boueux) ; `SymptomTint(tissu)` lerp ∝ intensité (×`SymptomTintMax`=0.7),
  appliqué aux feuilles + apex + silhouette LOD, jamais au bois. Généralise
  l'ex-`Chlorotic()`.
- **Canaux TEXTURE/FORME** (additifs, sur les feuilles, `PlantRenderer.Organs.cs`) :
  ravageurs+grêle = criblage (1-4 morsures sombres placées au hash, stables
  inter-frames) ; gel = bords noircis (`DrawEllipseOutline`) ; sécheresse =
  affaissement des feuilles (`DroughtDroopCm`).

`WorldView.Snapshot.cs` pousse `leaf_symptoms` (tolérant : clé absente → null →
plante saine) aux deux sites (plante qui pousse / plante qui naît). Cause inconnue
→ aucun effet (forward-compatible §7 : `carence_n/_k`/`etiolement` s'ajouteront
sans toucher le schéma). `dotnet build` vert, 0 avertissement. **F5 visuel = Nico.**

## Golden

NEUTRE sur tout le sprint : `e209e8d8…` inchangé. ① lecture pure ; ② affichage
hors tick (scénario smoke sans aléa) ; ③ aucun fichier Python touché.

## Reste / liens

- D33 **clôturée** dans `DETTE.md`.
- Échecs PRÉ-EXISTANTS hors sprint (HEAD propre) : `test_senescence` (Pommier mort
  « autre » à 34,3 ans), `test_sim_server` 183/185 (`engine_version` stale 0.5.0 ;
  nouaison Pommier pré-âgé). À traiter hors sprint.
- Extensible : carence azotée/potassique, étiolement (ombre) = nouvelles `cause`.
