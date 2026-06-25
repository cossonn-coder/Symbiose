# ⑤ Structures niveau tuile + colonisation fongique + bêchage event-driven

> Lire d'abord `00_etat.md` + `docs/conception/CONCEPTION_MYCELIUM_INTERCONNEXIONS.md`
> (§3.1, §3.3, §3.4, §1.2 perturbation). Prérequis : ①→④ FAITS. Tronçon **structures
> + gestes**, surtout EVENT-DRIVEN → **golden ~intact** (mais refactor `Structure`
> sensible : PROUVER la neutralité). Prolonge `CONCEPTION_DECOMPOSITION_COMPOST.md` §5.

## Objectif
(a) Bac & pile rattachés à la **TUILE** (composter/empiler depuis tout plot de la
tuile) ; (c) maturation lisible **colonisée par le mycélium** ; (d) faune sur le
**bac** aussi ; **bêcher casse le réseau** (`becher` retire un quantum `mycelium`),
grelinette le préserve.

## À faire

### A. (a) `Structure` au niveau tuile (`fields/ecofields/litiere.py:95`, `sim/actions/compost.py`)
- `Structure` est aujourd'hui `plot=(r,c)`. La rattacher à la **tuile** (garder un
  plot d'ancrage pour le rendu, mais l'APPARTENANCE est la tuile). Au plus **un bac
  et une pile par tuile** (lisible).
- `composter`/`empiler_bois` (`compost.py`) acceptent **n'importe quel plot de la
  tuile** et versent dans la structure de CETTE tuile (aujourd'hui ils ne ramassent
  que le plot porteur via `_ramasser_vers_structure`). L'habitat `auxiliaire` de la
  pile est DÉJÀ au niveau tuile (rondelle, `poser_pile`) → aligner le bac dessus.

### B. (c) Colonisation fongique + maturation lisible (`tick_structures`, container.py:628)
- Le tas (bac, pile) porte sa propre **valeur de colonisation fongique** (un champ
  scalaire sur la `Structure`, init 0). Il se colonise au fil des ticks (le tas humide
  riche en bois = habitat fongique de choix), au rythme d'un knob.
- La colonisation **accélère/structure** la maturation (`compost_mur`, `MATUR_BAC`/
  `MATUR_PILE`, `litiere.py`) : phases lisibles **frais → en cours → mûr**. Pile (bois)
  mûrit surtout par voie FONGIQUE ; bac (tendre) par voie microbienne + fongique.

### C. (d) Faune sur le bac
- La colonisation fongique du bac gonfle une fraction **`auxiliaire`/`detritivore`**
  (fongivores) — même patron qu'④. Compost vivant = compost habité.

### D. Bêchage EVENT-DRIVEN (`sim/actions/gestes.py`)
- `becher` (~L422-424, déjà : `lombric -`, `microbiome -`, `structure_sol -`) →
  AJOUTER `eco.mycelium.add(r, c, -BECHAGE_MYCELIUM_MALUS)` (miroir EXACT de son
  malus microbiome/lombric). Knob `BECHAGE_MYCELIUM_MALUS`.
- `grelinette` (~L444-445) → **ne touche PAS** `mycelium` (préserve le réseau). Double
  peine pédagogique de bêcher : casse vers + microbes + STRUCTURE + champignon.

## Couches
`Structure` (fields) ; `compost.py`/`gestes.py` (sim.actions) écrivent `mycelium`
(fields) — sens descendant OK. Refactor `Structure` : vérifier que rien dans `fields/`
ne casse (le plot d'ancrage reste pour le rendu).

## Définition de done
- `Structure` niveau tuile ; composter/empiler depuis tout plot ; colonisation
  fongique + phases de maturation lisibles ; faune sur le bac ; `becher` retire du
  mycélium, `grelinette` non.
- `tests/test_structures.py`/`test_mycelium.py` étendu : composter depuis un plot ≠
  porteur verse dans le bac de la tuile ; tas se colonise puis mûrit plus vite ;
  `becher` fait CHUTER `mycelium` d'un quantum, `grelinette` le laisse INTACT ;
  déterminisme h1==h2.
- **Golden** : surtout EVENT-DRIVEN (gestes hors tick) → **viser ~intact**. La
  colonisation/maturation peut dériver le smoke SI le smoke pose un bac/pile — VÉRIFIER.
  Toute dérive : l'ANALYSER (localisée structures), re-figer si maîtrisée, noter
  `ancien → nouveau` + explication dans `00_etat.md`.
- MAJ `00_etat.md` (⑤ → FAIT + hash + **SPRINT MOTEUR CLOS**) puis commit.

## Pièges
- Le refactor `Structure` plot→tuile est le point délicat : NE PAS casser le rendu ni
  les tests décompo existants. Garder un plot d'ancrage, migrer l'APPARTENANCE.
- `becher` ne doit pas planter si `mycelium` est nul (add d'un négatif clampé à 0 → OK).
- Maturation : garder les knobs existants (`MATUR_BAC`/`MATUR_PILE`) comme socle ; la
  colonisation MODULE, ne remplace pas.
- Un seul bac + une seule pile par tuile (à confirmer ici) — simple et lisible.
