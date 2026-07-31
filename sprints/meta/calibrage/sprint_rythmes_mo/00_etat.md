# Sprint RYTHMES MO — état

**Sujet** : D77 (calibration des modulateurs de RYTHME microbiome/MO) + D40
(sensibilité T°/humidité Q10 de la décompo). Découverte cardinale : **D40 est
déjà codé (`microbe_clim_factor`, sprint météo→champs ④) mais INERTE, tué par le
même `/3.0` que vise D77 → D40 ≡ D77, un seul problème**. Débloque D41 (mesuré,
pas implémenté ici). Type/thème = `meta/calibrage` (le D-cal différé par
CALIBRATION RÉALISTE §6).

**Conception FIGÉE** : `docs/meta/calibrage/conception_rythmes_mo.md`.
**Phase** : ① + ② FAITS. Reste ③.

## Avancement
- **① Décompo cœur — FAIT.** `MICROBE_RHYTHM_REF = 0.6` ajoutée dans
  `fields/ecofields/constants.py` (près de `MICROBE_EFFECT_REF`, exportée par
  `import *`, aucun `__all__`). Les deux sites `/3.0` de
  `fields/ecofields/matiere_organique.py` (`decomp_speed:96`, `tick_decomposition:133`)
  passent à `min(1.0, microbiome / MICROBE_RHYTHM_REF)` — cap structurel OK.
  Commentaire « jusqu'à 2× plus vite » (:149) redevenu VRAI, laissé tel quel.
  Aucune ligne B/om_stable touchée. Sites ② intacts.
  - **Golden RE-FIGÉ LARGE** (attendu) : `57c166d8…` → **`298d37b376c530ef41b5adcac19e216a029c1077211578c97744c50e5b154667`**.
    Dérive = cascade MO→NPK→humus→vitalité (décompo plus rapide/saisonnière) ;
    pas de crash, pas de NaN/inf/négatif (vérif 4 ans × 2 tuiles sur
    om_active/om_stable/n/p/k/microbiome). Suites décompo (microbiome_clim,
    conteneur, lessivage, marais, stress_chronique, structures, paillage,
    mycelium) toutes VERTES.

- **② Readers périphériques + herbivorie — FAIT.** 4 sites migrés vers
  `MICROBE_RHYTHM_REF` :
  - `fields/ecofields/sol.py:81` (`tick_soil_memory`) : `/3.0` → `min(1.0, …/RHYTHM_REF)`
    — **cap AJOUTÉ** (piège `max_val=3.0`). Dispo via `from .constants import *`.
  - `fields/population/resources.py:316` (`_soil_food_grid`, ressource lombric) :
    `/3.0` → `/RHYTHM_REF`, cap déjà présent. **Import PARESSEUX** au point d'appel
    (`from fields.ecofields.constants import MICROBE_RHYTHM_REF` dans la fonction) —
    la couche `fields/population` n'importe JAMAIS `ecofields` au top-level (cycle :
    `ecofields/container.py` importe `fields.population`). Voir écart §Écart.
  - `fields/ecofields/allelopathie.py:43` (détox) : `/3.0` → `/RHYTHM_REF`, cap déjà
    présent ; constante ajoutée à l'import `from .constants import (…)` + formule du
    docstring corrigée. Champ `allelopathie` nul au repos → NEUTRE.
  - `sim/effects/perturbations.py:438` (bascule létale herbivorie) : `/3.0` →
    `/RHYTHM_REF`. Import `from fields.ecofields import MICROBE_RHYTHM_REF` (couche
    `sim`→`fields.ecofields`, comme `vigueur_plante.py` pour `MICROBE_EFFECT_REF` ;
    `fields/__init__` ne ré-exporte PAS `RHYTHM_REF`). `if eco else 0.3` par défaut
    CONSERVÉ (0.3 = sol moyennement vivant, bien au-dessus du nouveau seuil).
  - Ancre B (`croissance.py:245`) et `om_stable/5.0` NON touchés. Décompo ① NON re-touchée.
  - **Seuil `HERBIVORY_LETHAL_MICRO` re-dérivé 0.20 → 0.05** (perturbations.py:377).
    MESURE au banc `full` (seed 1234, 3 ans), micro_norm sur échelle `/0.6` :
    - Sol vivant d'équilibre : médian **0.18**, moy 0.21, plage typique 0.08–0.40 (p10 0.008).
    - Sol BÊCHÉ (−0.5) / stérile (bêchages répétés) : médian **0.0**, moy 0.002–0.014.
    - 0.05 siège dans le creux stérile(~0)↔sain(≥0.08) → seul un sol réellement
      dégradé (post-bêchage) fait sauter le doublement létal ; l'ancien 0.20 sur `/3.0`
      lisait ~0.017 partout → « sol mort » TOUJOURS vrai (calibration cassée).
  - **Golden RE-FIGÉ** (attendu) : `298d37b376…` → **`9ad035f18916813dbd194f0d7b76c11178229c63203dccd832bdf4ea3175411c`**.
    Dérive = soil_memory (nouvelle échelle micro, poids 40 % de la target) → succession/
    seedbank ; herbivorie exercée par le smoke. Cohérente : `main.py` exit 0 sans
    NaN/traceback ; sanity 4 ans × champs clefs (microbiome/om/soil_memory/npk/allelo) =
    **0 anomalie** (aucun NaN/inf/négatif).
  - **2ᵉ golden re-figé : `tests/population_hash.txt`** `cc886bdd…` →
    **`c59e0ddb94cab1d25bd212e4590229ec87d5cc7ba0f2ba1c963f754253c8f1b7`**.
    Cause = `resources.py:316` (ressource lombric) est dans le tick population →
    densité vers modifiée. Toutes les assertions comportementales de `test_population`
    VERTES ; seul le hash de déterminisme bouge (re-capturé `--capture`). ① l'avait
    laissé vert (① ne touchait pas `resources.py`).
  - Suites VERTES : microbiome_clim, stress_chronique, lessivage, marais, structures,
    paillage, mycelium, senescence, croissance, genetique, signes, vigueur, competition,
    planter, eau, inoculum, population (assertions). `test_automate_determinisme` non
    lancé (trop long ; self-consistency externe au tick, non impacté par un golden stocké).

### §Écart de prescription (②)
Le kickoff dit pour `resources.py`/`allelopathie` « ils importent déjà d'autres
constantes — ajouter au besoin ». VRAI pour `allelopathie` (importe déjà de `.constants`).
**FAUX pour `resources.py`** : il importe de `fields.population.constants`, PAS d'`ecofields`,
et la couche `fields/population` n'importe VOLONTAIREMENT jamais `ecofields` (cycle avéré,
documenté dans constants.py:254 et resources.py:104/120). Corrigé d'emblée par un import
paresseux au point d'appel (runtime, `sys.modules` cache → coût nul), conforme à la NOTE
du kickoff. Aucune fouille DeepSeek nécessaire.

### Vérif D40 (preuve que D40 s'est allumé)
Swing saisonnier de la décompo, microbiome ~0.5, sol humide, hiver (T_sol 4 °C)
vs été (22 °C) :
- **Nouveau régime** (`/MICROBE_RHYTHM_REF` + cap) : hiver 0.566 → été 0.878 =
  **swing +55.2 %** (≈ cible +50/+56 %).
- Ancien régime `/3.0` : hiver 0.513 → été 0.576 = swing +12.2 %.
- ⇒ Le Q10 de `microbe_clim_factor` (D40, déjà codé, inerte) est ENFIN actif.

## Décisions arrêtées
- **D40 ≡ D77** : le levier unique est le dénominateur `/3.0`. Chiffré : à denom
  0,6, la décompo d'un plot riche swingue +56 %/saison (vs +13 % aujourd'hui) et
  le Q10 (×5) s'allume enfin. Perf neutre.
- **Constante neuve `MICROBE_RHYTHM_REF = 0.6`** (≠ `MICROBE_EFFECT_REF`, même
  valeur) : découple la dynamique MO de la lisibilité vue.
- **Catégories** (Nico) : A migre (décompo :96/:133, soil_memory :81, lombric
  :316, détox :43) ; **B inchangée** (exsudats `croissance.py:245`, ancre de
  saturation) ; **om_stable /5.0 inchangé** (centennal, philo #7) ; **C**
  (herbivorie `perturbations.py:438`) migre + seuil `HERBIVORY_LETHAL_MICRO`
  re-dérivé.
- **Piège vérifié** : microbiome `max_val = 3.0` → `/0.6` atteint 5,0 → cap
  `min(1.0,·)` OBLIGATOIRE aux 3 sites A qui ne l'ont pas (:96, :133, :81).
- **D41** : ce sprint débloque + MESURE la précondition (favorabilité directe
  Liebig×pH sur sol sain), ne l'implémente pas. D41 = /conception de suivi.

## Carte des tronçons
| # | Objet | Golden |
|---|---|---|
| ① | Décompo cœur `matiere_organique.py:96`+`:133` → `MICROBE_RHYTHM_REF`+cap ; site D40 | **RE-FIGE LARGE** (cascade MO→NPK→humus→vitalité) |
| ② | `sol.py:81`(+cap), `resources:316`, `allelopathie:43` → RHYTHM_REF ; `perturbations:438`+seuil 0.20→0.05 | **RE-FIGÉ** `9ad035f18…` (+ population_hash `c59e0ddb…`) — FAIT |
| ③ | Banc mesure favorabilité D41 + vérif heatmaps/litière saisonnière F5 Godot | **INTACT** attendu |

## §REPRISE
① + ② FAITS (② non commité — l'orchestrateur commit). Prochain : **tronçon ③**
(`03_*.md` : banc de mesure favorabilité D41 sur jardin sain post-recalibration +
vérif F5 Godot heatmaps F6 om/npk/microbiome + accumulation saisonnière de litière ;
**golden INTACT attendu** — mesure/observation, aucun champ/rendu neuf). Golden courant
après ② = `9ad035f18916813dbd194f0d7b76c11178229c63203dccd832bdf4ea3175411c`
(+ `tests/population_hash.txt` = `c59e0ddb94cab1d25bd212e4590229ec87d5cc7ba0f2ba1c963f754253c8f1b7`).
Chaque tronçon lit `CLAUDE.md` + ce fichier + son `0N_*.md`. À la fin du sprint :
maj DETTE.md (D40/D77 → faits ; D41 → statut précondition mesuré) + `journal.md`.
