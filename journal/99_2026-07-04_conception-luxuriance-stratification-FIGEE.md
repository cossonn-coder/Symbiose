# 2026-07-04 — Conception FIGÉE : luxuriance par stratification (D65, absorbe D62)

`/conception` pour **D65** — le vrai objectif « densification » extrait de D64
(« la mort du tournesol cachait une intention : le jardin doit se remplir et se
superposer »). Conception durcie en conversation puis figée.

## Constat de départ
Le socle de stratification existe déjà à ~70 % (vérifié dans le code) : strates
`sol/basse/moyenne/haute/grimpante`, co-occupation permise (`tile.add_plant`),
ombrage vertical asymétrique émergent (`light.py`), empreinte au sol dérivée
(`instance.update_footprint`). D64① a rendu le conflit non-létal → co-occupation
viable. **Manque** : densificateur actif, champ de couverture, empilement visible,
silhouette d'espèce. Aucun clonal n'existait (reproduction 100 % par graine).

## Grands arbitrages (Nico)
- **D65 ABSORBE D62** (rampantes clonales) : une seule mécanique clonale + les
  espèces (fraisier, menthe, framboisier, bambou traçant, violettes), 5 voix chacune.
- **Champ de couverture = 1 scalaire** (strates sol+basse), scatter, lu par 2 flux
  écolo (évaporation réduite + germination adventice supprimée) + gate clonal
  interne (auto-limitation + cap perf).
- **Empreinte = silhouette de rendu + override ciblé** (courge étalée), pas de
  champ écologique concurrent de `canopy_r`.
- **Clonal = 1 mécanique paramétrée** `clonal_mode` (stolon/rhizome/drageon),
  déterministe (hash), coût Vigueur sur la mère, envahissement émergent (pas de flag).

## Découpage (6 tronçons, perf-first)
① champ couverture + hooks [golden RE-FIGÉ, trèfle du golden] → ② mécanique clonale
[golden RE-FIGÉ, trèfle stolonifère] → ③ silhouette + override [NEUTRE] → ④ catalogue
fraisier+menthe [NEUTRE] → ⑤ catalogue framboisier+bambou+violette (+ famille
Violaceae) [NEUTRE] → ⑥ vue Godot (empilement visible + couverture + silhouettes +
banc F5 `luxuriance` + pont 0.5.19) [INTACT].

## Livrables
- `docs/conception/CONCEPTION_LUXURIANCE_STRATIFICATION.md`
- `sprints/sprint_luxuriance_stratification/` (00_etat + 01→06)
- DETTE : D65 conçu/prêt, D62 marquée absorbée (à fermer à la clôture).

Prêt pour `/sprint-auto sprint_luxuriance_stratification`.
