# ④ Microbiome climatique — cloche de température + facteur humidité

> Lire d'abord `00_etat.md` + `docs/conception/CONCEPTION_METEO_CHAMPS.md` (§5).
> Dépend de ① (humidité médiée). Indépendant de ②③. Premier geste : RE-MESURER les
> hashs golden.

## Objectif
Le microbiome évolue aujourd'hui par **famine** (litière épuisée) + **lockout pH**
(cloche autour du neutre), dans `tick_decomposition` (`container.py` ~L580-648). Il
manque le couplage **climatique** : l'activité microbienne suit une **cloche de
température** (optimum doux, dormance au gel, stress au chaud) et chute au **sec**.
Golden re-figé annoncé.

## À faire

### A. Facteur climatique (`container.py`, dans la boucle décompo ou un helper pur)
- `f_temp = cloche(T_sol[r,c], MICROBE_T_OPT, MICROBE_T_TOL)` ∈ [0,1] : 1 à l'optimum
  (~20 °C), → 0 au gel et à la canicule. Forme simple (gaussienne ou triangle borné).
- `f_hum = facteur_humidite(hum_norm)` ∈ [0,1] : ~0 au sec (dormance), max en sol frais,
  **légèrement réduit en saturation** (anoxie → c'est le « léger ↓ » de la Pluie prolongée).
- `f_clim = f_temp · f_hum`.

### B. Brancher sur la dynamique microbienne EXISTANTE
- Le microbiome a déjà un **puits de famine** (`microbiome *= (1 − MICROBE_DECAY_MAX·famine)`,
  ~L648). Ajouter `f_clim` comme **modulateur** : aux conditions climatiques défavorables,
  l'activité ralentit (le microbiome décline davantage / croît moins).
- Décision à trancher en codant (NOTER) : (i) moduler la `speed` de décompo par `f_clim`
  (le climat ralentit le recyclage — effet direct, simple) ; et/ou (ii) ajouter un terme
  de déclin climatique au puits microbien (le froid/sec tue des microbes). Préférer le
  plus sobre qui produit l'effet émergent recherché sans champ neuf.
- `f_clim = 1` (conditions idéales) → comportement actuel strictement inchangé.

### C. Constantes (`constants.py`, tête, calibrage post-test)
`MICROBE_T_OPT` (~20 °C) · `MICROBE_T_TOL` (largeur de la cloche) · éventuels seuils
humidité (réutiliser une échelle existante si possible).

## Couches
Tout dans `fields/ecofields/container.py` (+ helper pur si ça aère). Lit `temperature_sol`
et `humidite` déjà calculés ce tick. Pas de nouvel import, zéro RNG.

## Définition de done
- `f_clim` calculé (cloche T × facteur humidité), branché sur la dynamique microbienne.
- Constantes nommées en tête de `constants.py`.
- `tests/test_microbiome_clim.py` (NOUVEAU) : sol chaud+humide → microbiome/décompo
  actifs ; sol gelé → activité quasi nulle (litière s'accumule) ; sol desséché → ralenti ;
  saturation → léger ↓ vs frais optimal ; conditions idéales → identique à l'existant ;
  déterminisme.
- **Golden re-figé MAÎTRISÉ** : dérive = vitesse de décompo modulée par T_sol/humidité du
  smoke (recyclage plus lent l'hiver). Recapturer, **noter hash + justification** dans
  `00_etat.md`.
- MAJ `00_etat.md` (④ → FAIT) puis commit.

## Pièges
- **Ne pas casser le couplage pH/famine existant** : `f_clim` se COMBINE avec eux, ne les
  remplace pas (le lockout pH et la famine restent).
- **Effet émergent voulu** : litière qui s'accumule l'hiver/en sécheresse = correct, pas
  un bug. Le cycle redémarre au réchauffement/à la pluie.
- Vérifier l'interaction avec ③ : sol pluvieux = lessivage ↑ ET microbiome (saturation)
  légèrement ↓ — cohérent, mais surveiller que ça ne s'emballe pas (azote qui s'effondre).
