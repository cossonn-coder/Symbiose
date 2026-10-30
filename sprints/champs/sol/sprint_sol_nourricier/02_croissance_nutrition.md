# ② La plante carencée pousse plus lentement

**Moteur Python. Golden RE-FIGÉ annoncé** (la croissance du smoke dépend désormais de
N/P/K). Conception : `docs/champs/sol/conception_sol_nourricier.md` §3.2.

## Objectif
Donner une conséquence biologique réelle à la carence (philo #2 : flux → contrainte →
réponse) : un facteur de nutrition ∈ [plancher, 1] escompte la croissance.

## Faits vérifiés au code (2026-10-30)
- Précédent exact : `sim/engine/croissance.py` ~l.425-448 — l'allélopathie multiplie
  `target_g` (cible du `growth_factor`) par `_f_croissance_allelo(...)` sur
  l'empreinte racinaire `plant.root_plots` déjà dérivée, puis lerp 0,10 et clamp
  [0,3 ; 1]. Le `growth_factor` module la vitesse des segments
  (`sim/growth/phases.py:255`) et la hauteur (`familles.py:367`).
- `_avancer_stades` (croissance.py:131) ne lit pas N/P/K — ne PAS y ajouter de porte
  binaire.
- Liebig lu aujourd'hui en lecture seule dans `sim/vigueur_plante.qi_local`
  (min N/P/K + bonus mycorhize sur P, carnivore sans N) — s'en inspirer, pas dupliquer
  à l'aveugle.
- Besoin par stade : `BESOIN` (`fields/ecofields/constants.py` ~l.755).
- Équilibre par sol : celui défini au tronçon ① (lire `00_etat.md`).

## Modèle (intention)
- `facteur_nutrition(plant, eco)` : helper PUR (fichier/couche à choisir en respectant
  `plants ← fields ← sim ← engine`). Pour chaque nutriment, ratio
  `stock_moyen_sous_racines / équilibre_du_sol`, pondéré par le besoin relatif du
  stade (une plante en fructification ressent K d'abord) ; le minimum (Liebig) passe
  dans une rampe continue → [PLANCHER, 1]. Carnivore : N ignoré.
- `target_g *= facteur_nutrition` à côté de l'escompte allélopathique (mémoïser :
  aucune relecture d'empreinte en double dans le tick).
- Le helper sera RELU par la voix (③) : expose-le proprement.

## Critères mesurés (OBLIGATOIRES, dans 00_etat.md)
- Banc ou sonde : même espèce sur sol riche vs sol carencé → hauteur/segments à
  26 semaines nettement inférieurs en carence, jamais nuls (plancher).
- `mesure_faim.py` (seeds 42, 1, 2 ; 156 sem.) : la population reste viable (pas
  d'effondrement : nombre de plantes en an 2 ≥ 50 % de l'avant-②) ; noter
  vitalité et nombre de plantes.
- Perf : tick moyen avant/après sur `full` [n≥2 runs] ≤ +3 %.

## Golden
Re-figé (dérive attendue = croissance). Ancien/nouveau hash + raison dans 00_etat.md.

## Ne PAS faire
Mort par carence (D41) ; toucher la vitalité/santé directement (philo #2 : pas de
malus direct, on escompte un gain) ; voix (③) ; monde `full` (④).
