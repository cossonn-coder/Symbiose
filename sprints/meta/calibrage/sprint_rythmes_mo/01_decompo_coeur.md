# Tronçon ① — Décompo cœur : allumer D40 via le rescaling D77

## Objectif
Recalibrer les deux modulateurs de vitesse de décompo pour qu'ils lisent le
microbiome sur sa plage d'opération RÉELLE (~0,05 équilibre, ~0,5 riche) au lieu
de l'écraser par `/3.0`. C'est **le site D40** : la sensibilité Q10 (déjà codée,
`microbe_clim_factor`, mais inerte) s'allume enfin, la décompo devient
saisonnière et proportionnelle au sol vivant.

## Contexte (lire d'abord)
`docs/meta/calibrage/conception_rythmes_mo.md` §1, §3.A, §4. En bref : D40 est
déjà câblé mais mort-né, tué par le `/3.0` que vise D77 — un seul levier, le
dénominateur.

## Fichiers à toucher
1. `data/code/fields/ecofields/constants.py` — **ajouter** la constante :
   ```python
   MICROBE_RHYTHM_REF = 0.6   # microbiome « plein RYTHME » (décompo/mémoire/lombric/détox).
   # Distinct de MICROBE_EFFECT_REF (lecture VUE/uptake) : découple le réglage de la
   # DYNAMIQUE MO de celui de la lisibilité — cf. conception_rythmes_mo.md §3. Même
   # valeur au départ ; le banc ③ peut nudger l'un sans toucher l'autre.
   ```
   La placer près de `MICROBE_EFFECT_REF` (~ligne 456).
2. `data/code/fields/ecofields/matiere_organique.py` :
   - **`decomp_speed` (ligne ~96)** : remplacer
     `micro = self.microbiome.at_plot(r, c) / 3.0`
     par `micro = min(1.0, self.microbiome.at_plot(r, c) / MICROBE_RHYTHM_REF)`.
   - **`tick_decomposition` (ligne ~133)** : remplacer
     `micro = self.microbiome.at_plot(r, c) / 3.0`
     par `micro = min(1.0, self.microbiome.at_plot(r, c) / MICROBE_RHYTHM_REF)`.
     Les multiplications qui suivent (`*= dispo(ph)`, `*= microbe_clim_factor(...)`)
     restent INCHANGÉES et derrière le cap (elles sont ≤ 1, `micro` reste ≤ 1).
   - Importer `MICROBE_RHYTHM_REF` (le module fait `from .constants import *` en
     tête — vérifier que `MICROBE_RHYTHM_REF` est bien exporté ; il l'est par le
     `import *`. Sinon l'ajouter nommément).
   - Ajuster le commentaire trompeur ligne ~149 (« jusqu'à 2× plus vite ») : il
     redevient VRAI, le laisser ou le préciser.

## ⚠ Piège vérifié — cap OBLIGATOIRE
Le champ microbiome a `max_val = 3.0` (`fields/grids.py`). À `/3.0` le quotient
restait ≤ 1 (cap superflu, absent aujourd'hui). À `/0.6` un pic de plot (jusqu'à
~2,3, plafond 3,0) donne un quotient jusqu'à **5,0** → **sans `min(1.0,·)` la
décompo divergerait** (masses négatives, oscillation). Le `min(1.0,·)` n'est pas
cosmétique, il est structurel. Le patron existe déjà pour les readers d'effet :
`sol.py:140` fait `min(1.0, self.microbiome.at_plot(r, c) / MICROBE_EFFECT_REF)`.

## Ce qu'il NE faut PAS faire
- Ne PAS toucher `croissance.py:245` (ancre de saturation B, fixe l'équilibre).
- Ne PAS toucher `om_stable / 5.0` (ligne 223 de ce fichier, et ailleurs).
- Ne PAS toucher les autres sites `/3.0` (sol.py:81, resources:316,
  allelopathie:43, perturbations:438) — ils sont au tronçon ②.
- Ne PAS lancer `test_epaisseur_500ans`.

## Golden
**RE-FIGE LARGE, prévu et assumé.** La vitesse de décompo pilote toute la cascade
fresh → active → stable → minéralisation N/P/K → humus → vitalité : le digest
d'état final se déplace largement. Procédure :
1. Lancer `python3 -m tests.test_golden` → il ÉCHOUE (attendu).
2. Vérifier que l'échec est bien une dérive de champs MO/NPK cohérente (pas un
   crash, pas de NaN). Sanity : `python3 main.py` tourne sans crash (référence
   comportementale).
3. Re-capturer : `python3 -m tests.test_golden --capture`.
4. Consigner le nouveau hash dans `00_etat.md` et la nature de la dérive.

## Vérif D40 (à consigner dans 00_etat.md)
Mesurer que le swing saisonnier de décompo est désormais réel. Vite fait : dans
un `python3 -c`, comparer `decomp_speed`-équivalent (ou `microbe_clim_factor`
appliqué au nouveau `micro`) hiver vs été pour un microbiome ~0,5. Attendu :
swing ≈ +50 % (vs +13 % avant). C'est la preuve que D40 s'est allumé.

## Fin de tronçon
Maj `00_etat.md` (hash, dérive, preuve D40) + commit.
