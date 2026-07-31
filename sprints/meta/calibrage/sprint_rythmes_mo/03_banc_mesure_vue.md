# Tronçon ③ — Banc de mesure (précondition D41) + vérif vue F5

## Objectif
Mesurer ce que la recalibration a produit, et livrer le **verdict de précondition
D41**. Vérifier au F5 Godot que la nouvelle dynamique est visible et correcte.
Golden INTACT (mesure + observation, pas de changement de moteur).

## Pré-requis
Tronçons ① et ② faits. Lire `docs/meta/calibrage/conception_rythmes_mo.md` §5.

## Partie Python — banc de mesure
Étendre `data/code/tools/banc_calibration.py` (ou créer une sonde sœur
`tools/banc_favorabilite.py`) qui, sur le monde sain du banc (seed 42, ~20 ans),
mesure et imprime **par année** :
1. **Décompo saisonnière** : preuve que D40 vit — vitesse de décompo (ou
   `microbe_clim_factor` × `micro` recalibré) hiver vs été sur un plot riche.
   Attendu : swing ≈ +50 % (vs +13 % avant le sprint).
2. **Chaîne minéralisation** : microbiome moyen → flux N/P/K minéralisés →
   niveaux N/P/K → humus (om_active/om_stable). Montrer que la ligne de base NPK
   d'un jardin sain est REMONTÉE vs l'avant-sprint.
3. **Favorabilité D41 DIRECTE** (le livrable clé) : pour chaque plot vivant,
   `favorabilite = Liebig(min(N,P,K normalisés)) × fenetre_pH`, calculée
   **directement** (PAS via `qi_local`, qui reste épuisé — cf. DETTE.md D41).
   Sortir sa médiane/distribution sur sol sain. **Verdict** : est-elle désormais
   ≈ haute en conditions normales (analogue à `drought_memory ≈ 0`, la condition
   pour qu'une voie « mort chronique » soit SAINE) ? Chercher dans le code la
   fonction Liebig existante (physico-chimie du sol, `nutriments.py`/uptake) et
   la fenêtre pH (`dispo(ph, ...)`) — les réutiliser, ne pas ré-implémenter.

Consigner le verdict chiffré dans `00_etat.md` : **GO** (précondition atteinte →
D41 part en /conception) ou **NO-GO** (favorabilité encore basse → documenter
pourquoi, ce qui manque).

## Partie vue — F5 Godot
La recalibration n'ajoute aucun champ ni signe : la vue lit les mêmes heatmaps.
Vérifier :
1. Que `FieldOverlay` (heatmaps debug F6) expose bien om/npk/microbiome. Si une
   heatmap MO/NPK manque pour observer la nouvelle dynamique, la câbler côté
   `visuals/FieldOverlay.cs` (rendu C#, golden Python intact). Sinon, rien à
   coder.
2. Rédiger un **mémo de checkpoints F5** dans `00_etat.md` (§F5) pour Nico :
   - la litière (couche fraîche) doit s'ACCUMULER visuellement l'hiver et se
     RÉSORBER l'été (D40 enfin visible à l'œil) ;
   - les heatmaps N/P/K d'un sol sain doivent être MOINS uniformément « pauvres »
     qu'avant (cf. D41/C6 du F5 2026-06-22) ;
   - aucune plante ne doit mourir en masse d'un artefact de recalibration.

## Ce qu'il NE faut PAS faire
- Ne PAS modifier le moteur (aucun `data/code/` hors `tools/`). Golden INTACT ;
  si le golden bouge, c'est un bug — annuler.
- Ne PAS implémenter D41 (mort édaphique) — seulement mesurer sa précondition.
- Ne PAS lancer `test_epaisseur_500ans`.

## Fin de sprint
Maj `00_etat.md` (verdict D41 GO/NO-GO, mémo F5) + commit + maj `DETTE.md`
(D40 & D77 → FAITS ; D41 → précondition mesurée + statut) + `journal.md`.
