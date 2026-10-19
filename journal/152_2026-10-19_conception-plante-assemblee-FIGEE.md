# 152 — 2026-10-19 — Conception PLANTE ASSEMBLÉE — FIGÉE

`/conception` à partir de `docs/rendu/pixelart/entree_plante_assemblee.md` (F5 de clôture de PERF VUE).
Doc : `docs/rendu/pixelart/conception_plante_assemblee.md`. Sprint : `sprints/rendu/pixelart/sprint_plante_assemblee/` (7 tronçons, golden intact `22768f33…`).

## Trouvaille
Ventilation des draw calls à ×4 (banc E s45, couches masquées une à une) [VM, n=1] : total 2 013,
**Decor (ceinture) 1 099**, couvre-sol 449, plantes + maison 380. Le regroupement des plantes (D109 d)
n'était pas le levier principal : la ceinture statique émet des centaines de primitives par `_Draw`.

## Décisions (Nico)
- Un seul sprint : perf → silhouettes → légende des signes (+ bug légende F1).
- Paliers bas = plante assemblée : vraies tiges + touffes de pixel-art générées depuis `LeafShape`
  par espèce ; ×4 et au-delà inchangés. « Pixels plus fins » = éléments plus petits, pas de pleine résolution.
- Info-bulle à deux niveaux : descriptive (ce qu'on voit) par défaut, cause / nom de bête une fois
  appris (même seuil que le carnet interprétatif) ; affichage technique sur touche, comme F6.
- Accéléré : instrument + correctifs des suspects ; un seul banc PC en fin de sprint.
- Observation d'un signe = commande pont au survol (carnet « j'ai vu… »), jamais dans le tick.
