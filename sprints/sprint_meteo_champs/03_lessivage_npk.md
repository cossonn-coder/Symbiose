# ③ Lessivage NPK par la pluie — amplifier le lessivage existant par l'eau drainée

> Lire d'abord `00_etat.md` + `docs/conception/CONCEPTION_METEO_CHAMPS.md` (§4).
> Dépend de ① (apport de pluie médié → drainage réel). Indépendant de ②. Premier geste :
> RE-MESURER les hashs golden.

## Objectif
La pluie qui **draine** emporte les ions mobiles. Le lessivage existe DÉJÀ (passif,
`container.py::tick_decomposition` ~L650 : `leach_factor("N"/"P"/"K", cec)`). Ce tronçon
ne le recrée pas : il l'**amplifie ∝ l'eau drainée ce tick** (N≫K, P quasi épargné).
Golden re-figé annoncé.

## À faire

### A. Récupérer le flux d'eau drainée
- `tick_hydrology` RETOURNE déjà la perte de drainage par cellule (`pertes =
  [(r,c, h·(1−drainage))]`, `container.py:392`), aujourd'hui jetée par la tuile.
- Deux options (trancher en codant, **ne pas dupliquer** la boucle hydrologique) :
  - (a) mémoriser la dernière `pertes` dans un petit état `eco._drainage_last` (carte ou
    liste) écrit par `tick_hydrology`, lu par le lessivage ;
  - (b) recalculer un `drainage_norm` simple côté lessivage (h × (1−drainage)) — risque de
    re-coder l'hydrologie, **éviter**.
- Préférer (a) : `tick_hydrology` écrit la perte normalisée par plot, le lessivage la lit.

### B. Amplifier le lessivage (`tick_decomposition` ~L650, ou un pas dédié)
- `drainage_norm[r,c]` = perte d'eau normalisée (∈ ~[0,1]) du tick.
- `facteur_pluie = 1 + LESSIVAGE_PLUIE_K · drainage_norm[r,c]`.
- Appliquer plus fort à N (mobile), un peu à K, **épargner P** :
  `n[r,c] *= leach_factor("N", cec) ** facteur_pluie` (ou forme bornée équivalente).
  P inchangé (`leach_factor("P", cec)` seul). K = intermédiaire.
- Borner pour éviter une chute aberrante en un tick (cap sur `facteur_pluie`).

### C. Constante (`constants.py`)
`LESSIVAGE_PLUIE_K` en tête (calibrage post-test). À 0 → comportement ① strictement
inchangé (utile pour isoler la dérive golden).

## Couches
Tout dans `fields/ecofields/container.py` (calcul pur). Le lessivage reste où vit déjà
le lessivage passif (cohérence). Pas de nouvel import.

## Définition de done
- `tick_hydrology` expose la perte de drainage par plot (état `_drainage_last` ou équiv).
- Lessivage N (et K) amplifié ∝ drainage ; P épargné ; borné.
- `LESSIVAGE_PLUIE_K` nommé en tête de `constants.py`.
- `tests/test_lessivage.py` (NOUVEAU) : sol drainant + forte pluie → N chute plus que sur
  sol retenteur (CEC haute) ; P quasi inchangé ; `LESSIVAGE_PLUIE_K=0` → identique à ① ;
  déterminisme. Vérifier que la **structure** (battance ↓ infiltration → ↑ ruissellement)
  et l'**humus** (CEC ↑) modulent bien qui garde son azote (interconnexion attendue).
- **Golden re-figé MAÎTRISÉ** : dérive = N/K en baisse les semaines pluvieuses du smoke.
  Recapturer, **noter hash + justification** dans `00_etat.md`.
- MAJ `00_etat.md` (③ → FAIT) puis commit.

## Pièges
- **Ne pas dupliquer la boucle hydrologique** (piège connu, cf. sprint pots/bacs) : lire
  la perte déjà retournée, ne pas la re-calculer ailleurs.
- **Ordre** : `tick_hydrology` (3) tourne AVANT `tick_decomposition` (4) → la perte du
  tick est disponible quand le lessivage la lit. Cohérent, ne pas réordonner.
- Respecter la hiérarchie de mobilité N≫K>P (§2.4 du sol) : ne pas lessiver P comme N.
- Cap obligatoire sur `facteur_pluie` : un orage ne doit pas vider l'azote en un tick.
