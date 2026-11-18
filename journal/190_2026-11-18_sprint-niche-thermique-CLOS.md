# 2026-11-18 — Sprint NICHE THERMIQUE (D139, sprint ② sur 3) — CLOS côté code

Tronçons ①→⑤ faits (`sprints/vegetal/genetique/sprint_niche_thermique/`).

## Ce qui change
- ① Nuit la plus froide et jour le plus chaud ; température de feuille (soleil × soif).
  Golden re-figé `72896cbd…`.
- ② Niches thermiques des 52 espèces ; `rusticite_froid` en °C, `limite_froid`,
  `limite_chaud` ; plasticité et coût. Golden re-figé `9e83a0cb…`.
- ③ Dégâts gradués (gel tous stades, froid sans gel, brûlure), fin de la mort calendaire,
  fin de cycle propre à la plante. Golden re-figé `88cca899…`.
- ④ Posture thermique et paliers (pendant → effondré, replié → brûlé), marques `froid` et
  `brulure`, voix. Pont 0.6.18. Golden INTACT.
- ⑤ Vue : port (feuilles qui pendent / repliées) et teinte du palier, marques fines,
  survol G « plage vivable » en °C, banc F5 `niche_thermique` (canicule : mâches sèche /
  arrosée / ombre ; automne : basilics nu / paillé / voilé, mâche, seigle), warmup F5
  par banc. Pont 0.6.19. Golden INTACT.

## Constats
- La canicule n'est pas forcée (pas de drapeau moteur) : le banc vit celle du seed 42 (s24).
- La vue envoie toujours son seed (42) : `BANC_SEED` n'atteint jamais le F5 (préexistant).
- Basilics : nu mort s31, paillé s33, voilé s36 [seed 42] ; mâche sèche brûlée à la canicule.
- Réponse à la sélection (③) sous la cible ≥ +1 °C sur les semis.

## Suite
F5 de Nico (recette dans `00_etat.md`), puis `sprint_caracteres_vivants`.
