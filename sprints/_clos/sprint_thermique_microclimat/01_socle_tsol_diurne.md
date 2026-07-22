# Tronçon ① — Socle T_sol diurne (surchauffe solaire + inertie) + évaporation

> Sprint thermique-microclimat. Conception : `docs/champs/climat/conception_thermique_microclimat.md`
> (§2.1, §2.2, §3, §4, §5). Kickoff **autosuffisant** (relançable à froid).

## Objectif

Introduire le microclimat de surface `temperature_sol` (champ par plot), calculé
depuis la lumière-sol (soleil/ombre déjà connu) avec **inertie temporelle**, et
brancher l'**évaporation** dessus. C'est la fondation : un coin ensoleillé chauffe
et s'assèche, un coin ombragé reste frais.

**Périmètre strict** : seule l'**hydrologie** doit dériver. Croissance et gel
continuent de lire `eco.temperature` (= T_air, uniforme, inchangé).

## Modèle (ce tronçon)

```
cible[r,c]            = T_air + GAIN_SOLAIRE · lumière_sol[r,c] · intensité_saison
temperature_sol[r,c] += (cible[r,c] − temperature_sol[r,c]) · THERMAL_INERTIA
```

(Les termes refroidissement évaporatif ②, couvert ③ et nébulosité ④ s'ajouteront
à `cible` aux tronçons suivants — ici, surchauffe solaire seule.)

## Étapes

1. **`fields/ecofields/constants.py`** — ajouter les knobs de ① (cf. conception §3) :
   `GAIN_SOLAIRE = 15.0`, `THERMAL_INERTIA = 0.5`, et la table
   `INTENSITE_SAISON = {"hiver":0.35,"printemps":0.70,"automne":0.60,"ete":1.0}`.
   (Ne pas encore ajouter REFROID_EVAP / ISOLATION / NEBULOSITE — réservés ②③④.)

2. **`fields/ecofields/container.py`** :
   - Ajouter le champ `temperature_sol: GridField` (init `T_AMBIENT_INIT`, mêmes
     bornes `TEMP_MIN/TEMP_MAX` que `temperature`) dans le dataclass + `__post_init__`
     + l'exposer dans `get_field`.
   - Nouvelle méthode `tick_thermique(self, saison: str)` : pour chaque plot,
     lire `T_air = self.temperature.at_plot(r,c)` (uniforme), `lum =
     self.lumiere.at_plot(r,c)`, calculer `cible = T_air + GAIN_SOLAIRE · lum ·
     INTENSITE_SAISON[saison]`, puis lerp vers `temperature_sol`. Pure, aucun log.
   - **`tick_hydrology`** : remplacer la lecture `temp = self.temperature.data[r][c]`
     par `temp = self.temperature_sol.data[r][c]`. C'est LE changement qui fait
     dériver le golden (l'évaporation devient spatiale).

   ⚠️ Si `container.py` dépasse le seuil de taille (337 ldc actuel sur `ecofields`),
   sortir le calcul dans un helper pur `fields/ecofields/thermique.py` appelé par
   `tick_thermique`. Vérifier avec `python3 tools/compte_ldc.py`.

3. **`sim/engine/boucle.py`** — dans la boucle par tuile, insérer l'appel
   **entre l'étape 2 (`tick_light`) et l'étape 3 (`tick_hydrology`)** :
   ```python
   eco.tick_thermique(saison)
   ```
   Le `fill(temp_now)` en tête de `tick_semaine` reste **inchangé** (il alimente
   `temperature` = T_air, lue par `tick_thermique` comme base et toujours par le
   gel/la croissance).

4. **Golden** — lancer `python3 -m tests.test_golden`. Il échouera (l'humidité
   dérive). **Vérifier que SEULE l'hydrologie bouge** (humidité/champs dérivés ;
   la croissance, les stades, le `population_hash` ne doivent PAS changer). Si
   d'autres mécaniques dérivent → bug d'isolation, corriger avant de re-figer.
   Puis re-figer le golden (mettre à jour le hash de référence).

## Invariant golden

- **Dérive attendue** : humidité (évaporation désormais ∝ soleil reçu) et tout ce
  qui en dépend directement.
- **Doit rester identique** : trajectoires de croissance/stades, `population_hash`,
  météo. Si la tuile était partout à `lum=1` la dérive serait nulle ; elle vient
  des plots ombragés (maison/canopée) qui évaporent moins.

## Validation

- `python3 -m tests.test_golden` re-figé, dérive localisée hydrologie **vérifiée**.
- `python3 main.py` tourne sans crash (référence comportementale).
- Suites ciblées non thermiques inchangées (génétique, population…).

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (statut ① ✅ + nouveau hash golden dans §REPRISE).
- Commit : `feat(thermique) : tronçon ① socle T_sol diurne + évaporation spatialisée — golden RE-FIGÉ MAÎTRISÉ (hydrologie)`.
- Écrire le kickoff `02_refroidissement_evaporatif.md` avant le `/clear`.
