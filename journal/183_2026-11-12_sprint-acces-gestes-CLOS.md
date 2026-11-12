# 2026-11-12 — Sprint ACCÈS AUX GESTES — CLOS côté code (①→④)

Premier des trois sprints de la refonte de l'accès aux gestes
(`docs/joueur/gestes/conception_refonte_palette.md`). `/sprint-auto`, quatre
tronçons, golden `b4a921f8…` intact du début à la fin. Pont **0.6.12**.

## Ce qui change
- **① Portes des techniques** : `PORTES_TECHNIQUE` s'ajoute à `GESTE_UNLOCK`.
  Franchir une porte découvre la technique (palier 1). Conditions neuves `stock` et
  `compte`. Test permanent `tests/test_atteignabilite.py` (point fixe sur les tables).
- **② Atelier, courrier, observations** : cinq outils neufs (broyeur, pots, tuteurs,
  greffoir, voile) ; récompense `technique` ; quatre lettres qui enseignent (Amélie,
  Gaston, Augustin, Bertrand) ; le bac d'Odette vaut un bac posé ; marqueurs
  `merle_seme` et `grimpante_sans_appui` posés au-dessus du tick.
- **③ Pressentis, familles, pont** : `gestes_pressentis` (calculé) et ses phrases
  d'ambiance, `FAMILLE_GESTE` (8 familles), routes des supports, de `palisser` et des
  couvertures.
- **④ Vue minimale et banc** : les neuf gestes manquants dans `Gestes[]` (aucun kind
  neuf), un pictogramme provisoire chacun, nature de mulch `feuilles` dans la vue
  (le paillis glané était inutilisable), banc `acces_gestes` et son oracle.

## Preuve de bout en bout
`python3 -m tests.bancs.test_acces_gestes` : 56/56. Partant des seuls gestes de
base, en ne jouant que des commandes du pont et sans jamais envoyer un geste fermé,
les 46 verbes du moteur finissent ouverts (45 entrées de `Gestes[]` + `grelinette`,
qui passe par Maj + bêcher). Les quatre familles de portes sont franchies.

## Constats utiles pour la suite
- **Les dix cases sont pleines dès l'ouverture** (14 gestes de base). Un geste qui
  s'ouvre n'apparaît donc JAMAIS seul dans la barre : il faut un clic droit sur une
  case. C'est le besoin que couvre `sprint_palette_tiroir`.
- **Un haricot semé en fin d'été met 32 semaines à dépasser sa hauteur autoportante**
  [seed 42, n=1 run] : la porte `grimpante_sans_appui` ne s'ouvre pas vite par lui.
  Le banc la montre avec un jasmin de trois ans (1 semaine après le survol).
- Portes qui passent par le temps, au banc : phacélies en fleur ~10 semaines, merle
  ~12 semaines après l'ouverture [seed 42, n=1 run].
- Le pont n'applique toujours aucun refus dur sur un geste fermé (non tranché).

## Reste
F5 de Nico (recette dans `sprints/joueur/gestes/sprint_acces_gestes/00_etat.md`),
puis `sprint_palette_tiroir`.
