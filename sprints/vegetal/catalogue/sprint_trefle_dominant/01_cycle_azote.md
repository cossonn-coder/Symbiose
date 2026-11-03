# ① Cycle de l'azote du trèfle — golden RE-FIGÉ annoncé

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, conception §1 à §3 et §5.

## Objectif

Le trèfle cesse d'être gagnant partout : il fixe moins sur sol riche, et ses pieds se renouvellent.

## À faire

1. **Fixation** : l'effet `inject_field` de `Fabaceae.family_effects` (`plants/base/familles.py`, résolu dans `sim/effects/resolution.py`) devient
   proportionnel au manque d'azote du plot : plein sur sol pauvre, nul à saturation. Clé optionnelle sur l'effet, générique : une espèce sans la clé garde
   exactement son comportement. Vérifier si `Clover` et les autres `Fabaceae` héritent bien de cet effet ou le redéfinissent, et l'effet `add_rondelle` de `Clover` sur `fertilite`
   (`plants/species/cultivees.py`), qui peut aussi nourrir le sol sans frein. Choisir le seuil de saturation sur les valeurs réelles de `eco.n`.
2. **Renouvellement** : longévité courte du pied de trèfle (`longevity_years`, `plants/base/familles.py:72`). Vérifier d'abord qui lit `longevity()` et si un pied en meurt vraiment
   (`sim/semiologie.py`, `sim/engine/mortalite.py`). La mort doit passer par les chemins existants, avec retour au sol.
3. **Tests** `tests/test_trefle_cycle.py` : fixation décroissante avec l'azote ; autre espèce inchangée ; un pied finit par mourir et la colonie survit ; déterminisme.
4. **Mesure** `mesures/apres_cycle.md`, `full`, seed 42, automate curatif `{"op":"on","profil":{"desherbage":"curatif"}}`, 5 ans, chiffres marqués `[n=…, VM]` : trèfle en plantes et plots par an,
   part, N moyen par tuile, plantes par plot, tick an 2 avec `tools/banc_cadence`. Référence an 5 : 729 plantes, trèfle 434 sur 274 plots [`full`, seed 42, n=1 graine, VM].
   Cartographier les plots à trèfle des ans 3 et 5 : se déplacent-ils ? Sans graminées, ce tronçon peut ne faire que baisser le trèfle : le dire.

## Golden

**RE-FIGÉ annoncé** : le smoke porte du trèfle et du haricot. Raison et dérive à consigner dans `00_etat.md`, puis `python3 -m tests.test_golden --capture`. Aucune autre cause de dérive tolérée.

## NE PAS

Poser un plafond de population sur le trèfle. Toucher à `COUVERTURE_SATURATION` ou `GERM_PRESSION_FERALE`. Ajouter une espèce (②). Toucher au C#. Lancer `tests/test_epaisseur_500ans.py`.
