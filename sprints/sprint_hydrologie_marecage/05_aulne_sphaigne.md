# ⑤ — Aulne (Betulaceae) + Sphaigne (ingénieur) : moteur + niches + voix

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/conception/CONCEPTION_HYDROLOGIE_MARECAGE.md` §5.1/§5.2 + §9. Prérequis :
> ②③ faits. **Golden NEUTRE hors smoke** (espèces absentes du smoke).

## Objectif
Deux espèces de la guilde marécageuse, chacune un FLUX (philo #2) + niche humide/
acide + ses **5 voix** (règle « toute plante = ses 5 voix ») :
- **Aulne** — arbre fixateur d'azote qui pousse les pieds dans l'eau.
- **Sphaigne** — mousse INGÉNIEUR (acidifie + retient l'eau + tourbe).

## Fichiers
- `plants/base/` : famille **Betulaceae** NEUVE (patron des familles existantes) ;
  éventuellement catégorie/famille bryophyte pour la sphaigne (Sphagnaceae).
- `plants/perennials.py` : `class Alder(PerennialWoody)` (strate haute, caduc,
  `family="Betulaceae"`, `archetype="nitrogen_fixer"` ou mécanisme fixation réutilisé,
  gène `tolerance_asphyxie` élevé, anémophile).
- `plants/species/` : `class Sphagnum` (mousse couvre-sol, strate basse, PAS de
  morphogénèse segments — modèle minimal ; niche humide+acide).
- `plants/catalogue.py` : enregistrer les 2 espèces.
- **Fixation N aulne** : réutiliser le mécanisme `nitrogen_fixer` (cf. Medicago) —
  enrichit le N du sol sous l'empreinte. Vérifier le point de greffe existant.
- **Sphaigne ingénieur** (3 flux, sous une sphaigne vivante, sur ses plots) :
  (a) acidification → terme dans `tick_ph` (⚠️ borné AVEC l'acidif. marais §3, pas
  de double-comptage) ; (b) rétention → bump `soil_memory`/rétention ; (c) nécromasse
  → litière `mousse` à `decay` très bas (tourbe). Points de greffe : `sim/effects`
  ou registre d'effets par espèce (patron `basil_companion_check`/family_effects).
- Voix (§9) : encyclopédie 3 niveaux × 2, carnet (`CONCEPT_DE` → `fixation_azote`,
  `asphyxie`, `acidification`), pages (tourbière = lore paysan/poétique), magazine
  (Betulaceae/Sphagnaceae), événements (installation aulne, tapis de sphaigne).
- `data/code/tests/` : germination en niche marais (banc `tourbiere` ③), survie
  aulne en sol gorgé (là où pommier meurt), effets sphaigne (pH ↓, rétention ↑).

## Golden
Espèces **absentes du smoke** → **NEUTRE** (`test_golden` inchangé). Si l'ajout au
catalogue/registre d'effets touche un chemin lu par le smoke (à éviter), re-figeage
MAÎTRISÉ annoncé. Preuves via bancs, pas via le golden.

## Ce qu'il NE faut PAS faire
- Pas de bonus direct : l'aulne ENRICHIT le sol (flux N), il ne « booste » pas les
  voisins ; la sphaigne MODIFIE le milieu, elle ne donne rien aux plantes.
- Double-comptage acidification (marais §3 + sphaigne) : borner ensemble.
- Pas la carnivore (⑥). Pas les gestes (⑦).

## F5
- Aulnes en berge, tapis de sphaigne vert-glauque (⑧). Le marais s'acidifie-t-il
  visiblement sous la sphaigne (overlay pH F6) ?
