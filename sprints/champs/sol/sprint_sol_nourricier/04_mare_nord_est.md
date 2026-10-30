# ④ Une mare remplie et peuplée au nord-est du monde `full`

**Python, init du monde `full` seulement. Golden INCHANGÉ obligatoire** (le smoke
utilise `tests/test_golden.build_world`, pas `main.build_world_full`).
Conception : `docs/champs/sol/conception_sol_nourricier.md` §3.4.

## Faits vérifiés au code (2026-10-30)
- Monde `full` : `main.py build_world_full` (SECTORS l.47 ; tuile **NE** = sable,
  11×11 plots, origine (1450, 0) cm). Appelé par `tools/simserver/commands.py cmd_init`
  (config `full`, et `propre` qui le réutilise — la mare y sera aussi, c'est voulu).
- Patron d'un marais installé : `bancs/hydrologie.py` `tourbiere()` → `build_banc_tile`
  avec `altitude=2.0`, `humidite=3.0` (saturé), `eau_surface=1.2`,
  `marais_memory=0.85` (> `MARAIS_ON`). Ici il faut l'appliquer à UN GROUPE de plots
  d'une tuile existante (pas à toute une tuile) : poser les valeurs plot par plot
  après `build_tile`.
- Hydrologie : `tick_ruissellement` (l'eau converge vers les minima d'altitude),
  `tick_marais` (hystérèse) ; geste `creuser` (`sim/actions/gestes.py:567`) =
  référence de ce qu'est une cuvette.
- Plantes de mare au catalogue : `Alder` (aulne, `plants/perennials.py:583`),
  `Sphagnum`, `Drosera` (`plants/species/sauvages.py`). Semis : `semer_fondateur`.
- Faune de mare : `moustique` (catégorie aquatique) + `libellule` (son prédateur),
  `fields/population/registry.py` ~l.236-246. Vérifier ce qui gouverne leur présence
  (habitat lu sur l'eau ?) et, si elles partent de zéro, amorcer leur densité sur la
  mare à l'init.

## Modèle (intention)
- Mare d'environ 3×3 à 4×4 plots dans le coin nord-est de la tuile NE, bords
  en pente douce (altitude progressive) pour qu'elle reste un minimum hydraulique
  et ne se vide pas en une saison ; berge saturée autour.
- Semis : aulne en berge (1-2), sphaigne + rossolis en bordure tourbeuse ; ne pas
  étouffer les cultures existantes de la tuile (`plant_garden` occupe colonnes 0..6).
- Faune de mare présente dès la semaine 1.
- Code dans un helper dédié (ex. `world/` ou à côté de `main.py`), commenté.

## Critères mesurés (dans 00_etat.md)
Sur `full` seed 42, 104 semaines : la mare garde une lame d'eau et `est_marais` vrai
au moins 80 % des semaines (sécheresses d'été tolérées) ; aulne vivant en an 2 ;
moustique ET libellule présents sur la mare en été an 1 et an 2.

## Golden
INCHANGÉ (vérifier).

## Ne PAS faire
Modifier l'hydrologie ou les populations (paramètres) ; toucher le smoke.
