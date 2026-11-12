# 2026-11-12 — Conception REFONTE DE L'ACCÈS AUX GESTES — FIGÉE

`/conception` « palette de gestes — refonte de l'accès aux gestes (inclure D133) ».

## Constat (audit au code)
- Point fixe sur `GESTE_UNLOCK`, `GESTES_BASE`, `OUTILS`, `OBJETS_TOUCHES` : **20
  gestes gatés sur 32 ne s'ouvrent jamais en jeu normal**. Une technique n'est
  découverte qu'en utilisant un geste qui la touche, or ce geste exige la
  technique. D133 (perchoir) en est un cas ; seul le sécateur avait sa porte.
- Le bac offert par la lettre d'Odette n'ouvre pas `composter`.
- 10 gestes du moteur absents de la vue (supports, couvertures, ruche).

## Décisions de Nico (R1→R9)
Refonte complète en trois sprints ; quatre portes par technique (Atelier, geste de
base voisin, observation, courrier) ; gestes pressentis (silhouette + phrase
d'ambiance, jamais la piste) ; barre de favoris + tiroir par familles + réglages
visibles + Ctrl+molette ; icônes dessinées par le code dans la DA ; curseur à
l'icône du geste, animé à l'exécution ; macros débranchées de l'interface (code
gardé).

## Choix de conception
On garde `GESTE_UNLOCK` et on ajoute `PORTES_TECHNIQUE` : franchir une porte
découvre la technique (palier 1), ce qui rend vraies les conditions existantes. Un
test d'atteignabilité permanent empêche le retour de l'impasse.

## Livré
- `docs/joueur/gestes/conception_refonte_palette.md`
- `sprints/joueur/gestes/sprint_acces_gestes/` (4 tronçons, ferme D133)
- `sprints/joueur/gestes/sprint_palette_tiroir/` (3 tronçons)
- `sprints/joueur/gestes/sprint_icones_curseur/` (4 tronçons)

Golden intact prévu sur les trois sprints.
