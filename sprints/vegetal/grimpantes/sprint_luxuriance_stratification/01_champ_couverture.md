# Tronçon 1 — Champ de couverture au sol + hooks écologiques

> Kickoff autosuffisant. Lis d'abord `CLAUDE.md` (philo #1-#7, garde-fous) +
> `00_etat.md` (décisions D1-D4) + `docs/vegetal/grimpantes/conception_luxuriance_stratification.md §2.1`.
> **Golden : RE-FIGÉ maîtrisé et annoncé** (voir §Golden).

## Objectif
Créer le **champ scalaire `couverture_sol`** (0..1 par plot) = fraction du sol
couverte par les strates basses, alimenté par **scatter** depuis les empreintes
des plantes, et le brancher sur **2 flux écologiques** (philo #2, jamais de malus
direct plante) : évaporation réduite + germination d'adventices supprimée.

Ce champ est le **socle** : le tronçon 2 (clonal) s'en sert comme gate
d'établissement. Ne PAS anticiper le clonal ici.

## Modèle
- **Champ** : un `GridField` scalaire par tuile (comme les autres champs éco),
  recalculé chaque tick par **un seul balayage des plantes** (scatter), jamais un
  sweep de grille.
- **Stamp** : pour chaque plante dont le stade courant est de strate `sol` ou
  `basse`, stamper sur `_plots_in_radius(x_cm, y_cm, canopy_r)` une contribution
  = densité de feuillage de la strate (`STRATE_DEFAULTS[strate]["density"]` ou
  `foliage_density` de l'espèce). Accumuler puis **clamp [0,1]** par plot.
  Les strates moyenne/haute/grimpante ne comptent PAS dans la couverture au SOL.
- **Hook (a) évaporation** — `fields/ecofields/hydrologie.py:90` applique
  `evap = EVAPORATION - EVAP_TEMP_COEF*...`. Ajouter un facteur de couverture :
  plus le plot est couvert, moins il évapore (l'eau reste sous le tapis). Ex.
  `evap_effectif = evap + (1-evap)*COUVERTURE_EVAP_FRAC*couverture` (rapproche de
  1.0 = rétention). Constante `COUVERTURE_EVAP_FRAC` dans
  `fields/ecofields/constants.py`, calibrage modéré (~0.3-0.5).
- **Hook (b) germination adventice** — `sim/succession.py::_lever_grains_en_attente`
  décide la levée des grains en attente. Ajouter un gate : si `couverture_sol` du
  plot dépasse un seuil (`COUVERTURE_ADVENTICE_SEUIL` ~0.6), **supprimer/atténuer**
  la levée d'adventices (archétypes pionniers) sur ce plot. Le couvre-sol étouffe
  la concurrence. Déterministe (pas de RNG).

## Fichiers à toucher
- `fields/ecofields/` (nouveau champ `couverture_sol` + constantes) — respecter la
  structure paquet existante (`ecofields/__init__.py` ré-exporte l'API).
- `fields/ecofields/hydrologie.py` (hook évaporation).
- `sim/succession.py` (hook germination adventice).
- Câblage du recalcul du champ dans la boucle de tick (`sim/engine.py`) — placer le
  scatter AVANT les consommateurs (évaporation, germination).
- Réexport dans `fields/__init__.py` si l'API publique le demande.

## Golden — RE-FIGÉ (annoncé)
Le golden porte **Clover** (tuile 2) → couverture > 0 → évaporation modifiée →
humidité dérive → cascade. **Re-figeage LOCALISÉ attendu et légitime.**
Procédure : lancer `python3 -m tests.test_golden`, constater la dérive, **vérifier
qu'elle est cohérente** (humidité un peu plus haute sous couvert, pas d'explosion),
re-figer le hash dans le test, **consigner le nouveau hash + la raison** dans
`00_etat.md`. Lancer aussi les suites ciblées impactées (hydrologie, succession).

## Ce qu'il NE faut PAS faire
- Pas de sweep de grille (scatter uniquement — perf, LightField déjà 53 % CPU).
- Pas de malus direct sur les plantes (couverture agit par flux, pas sur la santé).
- Pas de mécanique clonale (tronçon 2).
- Pas de rendu (tronçon 6).
- Pas de champ par strate (décision D2 : UN scalaire).

## Fin de tronçon
MAJ `00_etat.md` (§REPRISE + nouveau hash golden + raison), commit.
