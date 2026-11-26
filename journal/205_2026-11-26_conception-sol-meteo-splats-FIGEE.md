## 2026-11-26 — Conception SOL, LITIÈRE, EAU, NEIGE, MÉTÉO en splats (famille (e)) FIGÉE

`/conception` avec Nico (lot 1 arbitré, puis « carte blanche »). Doc :
`docs/rendu/splatting/conception_sol_meteo_splats.md` ; sprint :
`sprints/rendu/splatting/sprint_sol_meteo_splats/` (9 tronçons, golden `bce813af…` intact partout,
`data/code/` et pont jamais modifiés).

**Décisions :**
- E1 (Nico) sol = tapis de matériaux pavables (fond continu) + kit de pièces (objets épars) + eau au shader.
  Rejetés : tout en grains posés (CPU ∝ surface), une texture par plot (mémoire à ×32).
- E2 (Nico) météo en pièces cuites, taille par palier plafonnée à ×8.
- E3 (Nico) reliquat « écorce sous ×4 » joint (⑦).
- E4 (carte blanche) POC chanvre ×64 au ⑧ : jamais fait après S3 alors qu'il était prévu — oubli relevé
  par Nico (« où est l'image en x64 ? »).
- E6 seuil par hauteur : le ton du dessous sert de hauteur → l'eau et la neige mince remplissent les creux.
- E7 jamais réduire une cuisson fine (question de Nico « pourquoi pas ×32 partout ? ») : réduire au plus
  proche = sel, moyenner des codes de palette = faux, cache GPU.

**Limite connue :** le pont n'envoie l'humidité que des plots secs → pas de « sol mouillé plus sombre ».
