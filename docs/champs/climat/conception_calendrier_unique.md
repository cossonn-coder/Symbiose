# Conception — calendrier unique (D122)

> Arbitrée avec Nico le 2026-10-30. Sprint : `sprints/champs/climat/sprint_calendrier_unique/`.
> Origine : F5 MARE VIVANTE, « j'ai l'impression que les saisons sont pas bonnes ».

## 1. Le problème

Le moteur numérote les semaines de 1 à 52 (`week_in_year`, abrégé `wiy`), mais deux
familles de code ne parlent pas du même calendrier :

- **Climat** — année au **1ᵉʳ janvier** : `sim/weather.temp_norm` (minimum wiy 4),
  `sim/weather.humidite_air` et `sim/wind.py` (phase `wiy − 4`),
  `fields/population/constants.daylength` (`W_SOLSTICE_ETE = 25`), fenêtres de
  `fields/fongique.REGISTRE_FONGIQUE`.
- **Étiquettes** — année à l'**équinoxe de printemps** : `sim/engine/calendrier.SAISONS`
  (printemps 1-13, été 14-26, automne 27-39, hiver 40-52), sa copie
  `sim/weather._saison_meteo`, `sim/precroissance.SEMAINE_HIVER`,
  `sim/growth/phases._season_factor`, fenêtres des aléas `sim/weather._CATALOGUE`,
  `ABSCISSION_MIN/MAX`, `bois_chute_semaine` par espèce, transition hivernale,
  remise à zéro des degrés-jours de floraison en wiy 1, déclinaison solaire par
  saison (`fields/light.SOLAR_DECLINATION`, valeur au DÉBUT de saison — déjà cohérente).

Décalage : 11 semaines. Le froid le plus vif tombe au « printemps » s4, le jour le plus
long à la fin de l'« été ». Conséquences constatées : glace de la mare au printemps,
tomate tuée par le froid à w2-3, pollinisateurs (porte photopériodique) qui culminent
après la floraison du pommier (« recouvrement quasi nul », sprint floraison).

## 2. Décisions

| # | Décision | Raison |
|---|---|---|
| C1 | **L'année commence à l'équinoxe de printemps** : wiy 1 ≈ 20 mars. On décale le CLIMAT, on garde les étiquettes. | Les saisons restent contiguës (l'hiver 40-52 ne chevauche pas le nouvel an) ; le jeu démarre au printemps, moment naturel du jardinier ; le soleil est déjà dans cette convention. |
| C2 | **Un seul calendrier, en couche basse** : module racine `data/code/calendrier.py` (à côté de `constants.py`, zéro dépendance), importable par toutes les couches. Les copies locales (`_saison_meteo`, `SEMAINE_HIVER`, `_season_factor`) le lisent. `sim/engine/calendrier.py` le ré-exporte (API inchangée). | La copie dupliquée pour éviter un cycle d'import est la racine structurelle du bug : deux copies peuvent diverger, une seule non. |
| C3 | **Mesurer d'abord, recalibrer après** : banc de mesure figé AVANT tout changement, re-mesure après le décalage, recalibrage uniquement sur les écarts constatés. | Choix de Nico. Plusieurs réglages ont été calibrés sur le climat décalé ; on ne les touche qu'avec un chiffre. |
| C4 | **Soleil hors périmètre** : déclinaison par saison (4 valeurs mises en cache) conservée. | Ce n'est pas le bug, et elle est déjà dans la bonne convention ; passer à la semaine multiplierait le cache de LightField (62 % du tick). |

## 3. Le décalage (une seule constante de phase)

Passage 1ᵉʳ janvier → équinoxe : `wiy_equinoxe = ((wiy_janvier − 1 − 11) mod 52) + 1`.

| Courbe | Avant | Après |
|---|---|---|
| Température normale (minimum) | wiy 4 | wiy 45 |
| Humidité de l'air (maximum) | wiy 4 | wiy 45 |
| Saisonnalité du vent | wiy 4 | wiy 45 |
| Jour le plus long (`W_SOLSTICE_ETE`) | wiy 25 | wiy 14 |

Ces phases deviennent des constantes nommées dans `calendrier.py` (ex. `W_T_MIN = 45`,
`W_SOLSTICE_ETE = 14`) ; plus aucun « 4 » ou « 25 » magique dans les formules.

## 4. Table de référence mois → semaine (convention équinoxe)

wiy ≈ 1 + (jours depuis le 20 mars) / 7.

| 1ᵉʳ avr | 1ᵉʳ mai | 1ᵉʳ juin | 1ᵉʳ juil | 1ᵉʳ août | 1ᵉʳ sept | 1ᵉʳ oct | 1ᵉʳ nov | 1ᵉʳ déc | 1ᵉʳ janv | 1ᵉʳ févr | 1ᵉʳ mars |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 7 | 11 | 16 | 20 | 24 | 29 | 33 | 37 | 42 | 46 | 50 |

Saisons étiquetées : printemps ≈ 20 mars–19 juin · été ≈ 20 juin–18 sept ·
automne ≈ 19 sept–18 déc · hiver ≈ 19 déc–19 mars.

## 5. Fenêtres à réécrire au recalibrage (proposition, Normandie océanique)

Ces fenêtres sont calées sur l'une ou l'autre convention, parfois aucune. Au tronçon ③,
elles se réécrivent **d'après le mois réel** (table §4), puis la mesure tranche.

**Aléas météo** (`sim/weather._CATALOGUE`) :

| Aléa | Actuel | Réalité | Proposé |
|---|---|---|---|
| Gelée tardive | 8-15 (mai–juin) | avril → saints de glace | 2-9 |
| Canicule | 16-26 | juin–août | 12-24 |
| Sécheresse | 18-32 | juin–sept | 12-28 |
| Grêle | 10-26 | mai–août | 7-22 |
| Orage | 16-30 | mai–août | 8-24 |
| Tempête | 27-52 | oct–mars | 28-52 (inchangé à 1 près) |
| Pluie prolongée | 27-52 | oct–mars | inchangé |
| Redoux | 40-52 | hiver | inchangé |
| Neige | 44-52 | déc–fév | 38-49 |

**Champignons** (`fields/fongique.REGISTRE_FONGIQUE`) :

| Espèce | Réalité | Proposé |
|---|---|---|
| Pleurote | oct–fév | 29-48 |
| Hypholome en touffes | août–déc | 20-41 |
| Collybie à pied velouté | nov–mars, après les gels | (34, 52), (1, 2) |
| Coprin chevelu | mai–nov après pluie | 8-37 |
| Rosé des prés | août–oct | 20-33 |
| Clitocybe blanchâtre | juil–nov | 16-37 |
| Psilocybe lancéolé | sept–nov | 25-37 |
| Morille | avril–mai | 3-10 |
| Cèpe | juil–oct | 16-33 |
| Amanite phalloïde | juil–oct | 16-33 |
| Amanite tue-mouches | août–nov | 20-37 |
| Armillaire | sept–nov | 25-37 |
| Polypore du bouleau | fin d'été–automne | 20-37 |

**Phénologie végétale** : `ABSCISSION_MIN/MAX = 34, 39` (6 nov–18 déc) → chute réelle
mi-octobre–novembre ≈ **30-36** ; `bois_chute_semaine` des espèces (38, 46, 48) à
relire avec la même table ; remise à zéro des degrés-jours de floraison en wiy 1
(≈ 20 mars) à confronter à la semaine de floraison mesurée.

## 6. Indicateurs mesurés (banc ①, rejoué en ② et ③)

Par année simulée (3 ans au plus — jamais le test 500 ans), lus sur l'état réel du moteur :

1. Semaines de T min / T max et leur saison étiquetée ; nombre de semaines de gel
   (`T_air < 0`) par saison étiquetée.
2. Semaine du jour le plus long et saison.
3. Semaines de neige / de glace (mare) par saison étiquetée.
4. Pommier : semaine d'ouverture florale (`bloom_week`) et saison ; recouvrement
   floraison × butineurs (part des semaines `floraison ≥ 0,5` où la densité de
   butineurs dépasse un seuil) ; nombre de fruits noués.
5. Tomate : semaine de mort ou survie de la saison.
6. Humidité du sol médiane par saison étiquetée.
7. Carpophores apparus par saison étiquetée (par espèce).
8. Semaine d'abscission effective vs température.

**Critère de recalibrage (③)** : un indicateur se recalibre seulement s'il contredit la
réalité de la table §4-§5 (ex. gel en été, pommier fleuri hors printemps, recouvrement
pollinisateurs nul). Tout le reste reste en l'état et se juge au F5.

## 7. Golden

- ① : intact (outil de mesure seul).
- ② : **re-figé LARGE annoncé** — tout le climat glisse de 11 semaines.
- ③ : **re-figé annoncé** — fenêtres + seuils recalibrés.
- ④ : intact (vue).

Coût perf : ≈ 0 (constantes de phase, aucune boucle ajoutée).
