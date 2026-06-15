# Sprint Maison·2 — **Ombre de la maison dans le `LightField`**

> **Kickoff autosuffisant.** Démarrage à froid. Lis ce fichier, puis
> `data/code/CONCEPTION_MAISON_OMBRE.md` (§3 modèle d'ombre + albédo, §1 option B,
> §5 coûts), puis les sources, puis exécute. Carte blanche (conception figée).
> **Français.** Rigueur **déterminisme + golden**. **Prérequis : tronçon 1 fait**
> (monde agrandi, `House` inerte, offsets monde par tuile, golden smoke test).
>
> Tronçon **moyen, cœur du sprint**. Touche `fields/light.py` (+ peut-être le
> threading de la config maison jusqu'à `LightField.compute`). Synchro
> multi-fichiers assumée. Lancement depuis `data/code/`.

## Ce que c'est, en une phrase
La maison **projette enfin son ombre** : on injecte dans `LightField.compute` un
**obstacle rectangle balayé** (le footprint carré de la maison glissé le long de
la direction d'ombre, longueur = `hauteur × inv_tan(élévation)`), évalué sur la
**lumière-sol par plot** ET la **lumière reçue par plante**, en tenant compte de
la **position monde de chaque tuile** (offset du tronçon 1). On ajoute aussi
l'**albédo espalier** (point chaud devant la face ensoleillée).

## Principe directeur (à NE PAS contourner)
- **Option B (§1)** : champs lumière **par tuile**. La maison est le **seul**
  obstacle global. Pour chaque tuile, on convertit ses plots en **coordonnées
  monde** (via `origin_*_cm`) avant de tester l'ombre de la maison. Les ombres de
  **plantes** restent locales/inchangées.
- **Modèle d'ombre = rectangle balayé (§3)** : l'ombre au sol est l'union, pour
  `s ∈ [0, height·inv_tan]`, du footprint translaté de `s·(shadow_dx, shadow_dy)`.
  Réutilise la mécanique analytique existante (`solar_slice` donne déjà
  `shadow_dx, shadow_dy, inv_tan, weight`). Maison **opaque** → sous ombre pleine,
  plancher `LIGHT_FLOOR = 0.15`. Repli capsule-disque (rayon ~4-5,6 m) **seulement**
  si la maths du rectangle bloque — signaler si tu y recours.
- **Albédo espalier (§3, Q5)** : pour chaque plot **devant une face de mur
  ACTUELLEMENT éclairée**, dans un **rayon court** (≈ 2-3 m), ajouter
  `+= wall_albedo × intensité_incidente × falloff(distance)`, plafonné à 1.0.
  Hors rayon ou face à l'ombre → rien. **Désactivable** (`wall_albedo = 0.0`). Si
  ça alourdit trop, le sortir en **2b** sans bloquer l'ombre de base — signaler.
- **Déterminisme** : zéro RNG. Tout est analytique/astronomique.

## Sources à lire (dans l'ordre)
1. `data/code/CONCEPTION_MAISON_OMBRE.md` §3 (ombre + albédo), §1, §5.
2. `fields/light.py` — `LightField.compute`, `solar_slice`, `_point_in_capsule`,
   `LIGHT_FLOOR`, `SOLAR_*`, `LATITUDE_DEG`. **C'est le fichier central.**
3. `fields/ecofields.py` — `tick_light(plants, saison)` → `lumiere.compute(...)` :
   c'est là qu'il faut threader la config `House` + l'offset monde de la tuile.
4. `world/building.py` (créé au tronçon 1) — la config `House`.
5. `sim/engine.py` ~ligne 636 — appel `eco.tick_light(tile.plants, saison)`.

## Plan suggéré (révisable)
1. `solar_slice` donne déjà la géométrie d'ombre par tranche — réutiliser tel quel.
2. Écrire `_point_in_swept_rect(px, py, rect, dx, dy, length)` (analytique).
3. Dans `compute` : threader `house` + `tile_origin` ; convertir plots → monde ;
   pour chaque tranche, tester l'ombre maison en plus des capsules plantes
   (cumul multiplicatif des opacités, comme l'existant) sur sol ET reçu-plante.
4. Albédo : passe additive bornée après l'ombrage (plots proches face éclairée).
5. `tests/test_ombre_maison.py` (cf. §7) : N plus sombre que S à saison donnée ;
   ombre s'allonge en hiver ; **albédo** : pied du mur sud > plein champ ;
   déterminisme (2× = identique).

## Critères de succès (vérifier AVANT de clore)
- [ ] Plot au **Nord** de la maison nettement plus sombre qu'au **Sud** (été),
      asymétrie **NE/NO** présente (matin vs soir).
- [ ] Ombre **plus longue en hiver** qu'en été (soleil rasant).
- [ ] **Albédo** : un plot au pied du mur **sud ensoleillé** reçoit *plus* que le
      plein champ équivalent (effet espalier) ; `wall_albedo=0` annule l'effet.
- [ ] `test_ombre_maison` vert + **déterministe**.
- [ ] **Golden re-figé localisé** : seuls les plots ombrés par la maison changent ;
      documenter le nouveau hash. Suite complète verte.
- [ ] Coût : vérifier que le surcoût lumière reste **marginal** (1 obstacle), pas
      d'explosion. Noter l'ordre de grandeur dans `00_etat.md`.
- [ ] `00_etat.md` mis à jour (tronçon 2 ✅, hash, décision albédo 2/2b).

## Pièges connus
- Bien convertir **plots → monde** (offset tuile) AVANT le test maison, sinon
  l'ombre tombe au mauvais endroit.
- Repère sol de `light.py` : **x = Est, y = Sud, Nord = -y** (cf. docstring
  `solar_slice`). Respecter cette convention pour l'orientation des secteurs.
- Ne pas casser l'exclusion d'auto-ombrage des plantes (tri hauteur décroissante).
