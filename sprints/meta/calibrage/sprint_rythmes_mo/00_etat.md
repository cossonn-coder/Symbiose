# Sprint RYTHMES MO — état

**Sujet** : D77 (calibration des modulateurs de RYTHME microbiome/MO) + D40
(sensibilité T°/humidité Q10 de la décompo). Découverte cardinale : **D40 est
déjà codé (`microbe_clim_factor`, sprint météo→champs ④) mais INERTE, tué par le
même `/3.0` que vise D77 → D40 ≡ D77, un seul problème**. Débloque D41 (mesuré,
pas implémenté ici). Type/thème = `meta/calibrage` (le D-cal différé par
CALIBRATION RÉALISTE §6).

**Conception FIGÉE** : `docs/meta/calibrage/conception_rythmes_mo.md`.
**Phase** : ① FAIT. Reste ② + ③.

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
| ② | `sol.py:81`(+cap), `resources:316`, `allelopathie:43` → RHYTHM_REF ; `perturbations:438`+seuil re-dérivé | **RE-FIGE** (soil_memory→succession ; herbivorie) |
| ③ | Banc mesure favorabilité D41 + vérif heatmaps/litière saisonnière F5 Godot | **INTACT** |

## §REPRISE
① FAIT (non commité — l'orchestrateur commit). Prochain : **tronçon ②**
(`02_*.md` : `sol.py:81`+cap, `resources:316`, `allelopathie:43`,
`perturbations:438`+seuil re-dérivé → `MICROBE_RHYTHM_REF`). Golden courant
après ① = `298d37b376c530ef41b5adcac19e216a029c1077211578c97744c50e5b154667`.
Chaque tronçon lit `CLAUDE.md` + ce fichier + son `0N_*.md`. À la fin du sprint :
maj DETTE.md (D40/D77 → faits ; D41 → statut précondition mesuré) + `journal.md`.
