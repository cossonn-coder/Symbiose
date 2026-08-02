# Tronçon ① — Impact météo hétérogène (le cœur)

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` + ce fichier suffit.
> Spec complète : `docs/champs/climat/conception_effondrement_meteo.md` (§2, §6, §7).

## Objectif
Un événement météo reste **global** (un seul tirage), mais son **impact devient
spatialement hétérogène** : sous un même hiver catastrophe, un plot bien abrité
survit, un plot nu flanche. Le **plancher de survie émerge** du milieu
`f(abri, paillage, diversité)` — aucune constante gravée.

## Le problème (mesuré, re-vérifié au code)
La météo est un tirage global fanné aux 8 secteurs (`sim/engine/boucle.py:95,115-167`)
→ une semaine composée (gel + double tempête + pluie) effondre le jardin ENTIER.
**Mais l'impact est déjà majoritairement spatialisé** — ce tronçon FINIT la
spatialisation, il n'ajoute pas de système.

## Déjà local (NE PAS retoucher, juste élargir la dispersion si besoin)
- **Gel** : `t_min_nuit_at(eco,r,c,t_air,nébul)` (`fields/ecofields/thermique.py`) —
  couvert litière/neige + nébulosité + wind chill `eco.vent.at_plot`.
- **Tempête / verse** : `_wind_damage` (`sim/effects/perturbations.py:582+`) lit
  `eco.vent.at_plot(*plant.position)` (sillage d'abri / venturi, D73).
- **Fongique / pluie** : `fungal_disease` / `_dampoff` (`perturbations.py`) lisent
  l'humidité locale, le vent local, la dispersion de spores sous le vent.

## À FAIRE — 4 sous-étapes, séquencées, golden re-figé UNE FOIS en fin
Travailler dans cet ordre, vérifier la sim tourne après chaque étape, ne re-figer
`tests/test_golden.py` qu'à la toute fin (dérive localisée, annoncée).

### (a) Spatialiser Sécheresse / Pluie prolongée
Aujourd'hui `appliquer_alea` mode `field` appelle `eco.apply_weather(var, delta)`
(`fields/ecofields/container.py:599`) = **fill uniforme** de la tuile. Rendre le
delta **modulé par le drainage / l'altitude local** : l'eau de pluie s'accumule
dans les creux (altitude basse / `eau_surface` haute) et s'écoule des hauteurs ;
la sécheresse mord plus vite sur les plots bien drainés (haut / `drainage_last`
élevé). Champs existants : `eco.altitude`, `eco.eau_surface`, `eco.drainage_last`
(container hydrologie ~:419-454). **Intention, pas placement imposé** : décider si
la modulation se fait dans `apply_weather` (nouveau paramètre spatial optionnel) ou
en amont dans `appliquer_alea` — au sous-agent de choisir le point propre, en
respectant l'ordre des champs dans le tick (l'apport pluie doit précéder la lecture
hydrologie du même tick — vérifier dans `boucle.py` où `tick_hydrology` tourne).

### (b) Brancher la Canicule sur l'ombre / évaporation locale
La chaleur est stockée uniforme (`temperature.fill`). L'impact hydrique de la
canicule doit varier avec l'**ombre locale** (LightField déjà spatial : un plot
ombragé par la canopée / la maison évapore moins) et le paillage local. Ne PAS
spatialiser le champ température lui-même (coûteux, golden lourd) : agir sur la
voie évaporation → `humidite` locale, déjà le patron du moteur.

### (c) Honorer `event.scope == "local"`
Grêle et Orage portent `scope="local"` dans `WeatherEvent` (`sim/weather.py:100`)
mais **aucun lecteur ne l'utilise** (fan-out identique aux 8 secteurs). Les rendre
**patch** : un masque spatial déterministe (`_hash_noise` sur un canal sentinelle
réservé, hors grille plots — cf. `K_OCC/K_PICK` dans `weather.py`) sélectionne la
sous-zone frappée. Un événement `scope="global"` reste inchangé (toute la tuile).
Effet double : décorrèle grêle/orage dans l'espace ET réduit le travail.

### (d) Médiation complète + dispersion élargie
- **Résorber les voies `health` plates résiduelles** : `appliquer_alea` mode
  `health` (`sim/engine/aleas.py`) fait un `ReduceHealth` binaire sur les semis.
  Router tout impact restant par milieu × gène × protection (le patron `_mediated_damage`
  de `boucle.py` existe déjà pour gel/grêle). C'est la condition pour que la
  **diversité** fasse plancher (les espèces résistantes survivent au composé).
- **Élargir la dispersion** des tampons (amplitude abri / paillage / inertie /
  neige) juste assez pour qu'un plot bien abrité franchisse le seuil de survie
  sous le collapse connu, tandis qu'un plot nu chute. Calibrage : viser la texture
  Q2 (abrité ~0,45 garanti, nu ~0,13), sans coder ces nombres — ils émergent.

## Golden
**RE-FIGÉ une seule fois, en fin de tronçon**, dérive localisée + annoncée dans le
message de commit : « impacts météo (sécheresse/pluie/canicule/grêle) désormais
spatialisés + médiation health résorbée ». Vérifier que la dérive est bien
localisée à ces canaux (lancer le golden, lire le diff, confirmer). Le golden est
un smoke 2 tuiles × 4 ans : le composé catastrophe (an 26) n'y apparaît pas, la
dérive vient des événements NORMAUX de sécheresse/pluie/canicule sur 4 ans.

## Test ciblé à AJOUTER
Un test déterministe : sous le collapse connu (seed 12345, an 26, tuile 16×11), la
**variance spatiale de survie est > 0** (avant : ~0 pour les canaux uniformes) ET
un plot abrité (fort abri/paillage) garde un noyau vivant quand un plot nu s'effondre.
Le plancher doit corréler avec l'abri (∝), pas être une constante.

## NE PAS faire
- Ne pas décorréler la météo par secteur (événement reste global — signes intacts).
- Ne pas spatialiser le champ température stocké.
- Ne pas introduire de RNG vivant (tout via `_hash_noise`, philo #3).
- Ne pas lancer `test_epaisseur_500ans` (interdit).
- Ne pas toucher au pont / à la vue (tronçon ④).

## Perf
Quasi-neutre : lectures locales déjà en place ; honorer le scope réduit le travail ;
aucun nouveau balayage O(N²). Rester ≤ +10 % de tick.
