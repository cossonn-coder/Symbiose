# ① Humidité médiée — retrait des deltas plats + apport de pluie ∝ intensité

> Lire d'abord `00_etat.md` + `docs/champs/climat/conception_meteo_champs.md` (§0, §1, §2).
> Tronçon **fondation** : on rend l'humidité météo conforme à la philo #2 (flux, pas
> delta plat). Premier geste : MESURER les hashs golden actuels (référence avant/après).

## Objectif
Supprimer les deltas plats humidité de `WEATHER_ALEA` et les remplacer par deux flux
médiés : (a) assèchement Canicule/Sécheresse **émergent de l'évaporation∝T_sol déjà en
place** ; (b) apport de pluie **∝ intensité** via une table `PLUIE_APPORT`, infiltré
∝ structure du sol. **Le golden VA bouger** → re-figeage maîtrisé annoncé.

## À faire

### A. Table `PLUIE_APPORT` (PURE, `fields/ecofields/constants.py`)
- Miroir de `PRECIP_NORM` (~L419). Apport d'humidité par événement, calibrage post-test :
  `{"Pluie prolongée": +X, "Orage": +Y, "Tempête": +z, "Grêle": +w, "Sécheresse": −s}`.
- Négatif pour Sécheresse = **pluie de fond tarie** (état sec prolongé), borné pour ne
  jamais rendre l'apport total `BASE_RAIN + PLUIE_APPORT` négatif (on ne « retire » pas
  d'eau arbitrairement — on réduit l'apport, l'évaporation fait le reste).
- Knob `PLUIE_INTENSITE` optionnel si tu veux moduler par `event.intensity` (σ).

### B. Apport infiltré dans `tick_hydrology` (`fields/ecofields/container.py:343`)
- Ajouter un paramètre `pluie_event: float = 0.0` (défaut 0 → appelants existants/golden
  pots-bacs strictement inchangés tant qu'on ne le passe pas).
- Étape 2 « pluie de fond » (~L390) : `h += (BASE_RAIN + pluie_event) · structure_sol.at_plot(r,c)`
  (l'apport météo est infiltré ∝ structure, **comme** `BASE_RAIN`). Borner `BASE_RAIN +
  pluie_event ≥ 0`.

### C. Câblage boucle (`sim/engine/boucle.py`)
- Calculer `pluie_event = PLUIE_APPORT.get(event.kind, 0.0)` (event déjà tiré, L88).
- Le passer à `eco.tick_hydrology(tile.soil_type, pluie_event=pluie_event)` (~L179).
- **Retirer les entrées humidité de `WEATHER_ALEA`** (`sim/engine/aleas.py`) : Canicule,
  Sécheresse, Pluie prolongée, Orage passent en `mode="none"` (ou sont retirées de la
  branche `appliquer_alea`). **Garder** : Tempête/Orage vent (paillage), Gelée (→ gel),
  Grêle (→ médié). Conserver les entrées en commentaire (CLAUDE.md « ne jamais jeter »).
- ⚠ Orage = composite : il garde son VENT (`ORAGE_VENT`, L139-141) ; seule sa part
  humidité plate part vers `PLUIE_APPORT`.

## Couches
`PLUIE_APPORT` PUR côté `fields` (pas d'import `sim`). `tick_hydrology` reste pur (calcul).
Le câblage d'ordre est dans `boucle.py` (couche `engine`).

## Définition de done
- `PLUIE_APPORT` en tête de `constants.py` (knob nommé, commentaire calibrage).
- `tick_hydrology(pluie_event=…)` infiltre l'apport ∝ structure ; défaut 0 = rétrocompat.
- `WEATHER_ALEA` : entrées humidité neutralisées (commentées), vent/gel/grêle intacts.
- `tests/test_hydrologie*.py` (s'il existe) + suites voisines : vertes ou dérive expliquée.
- **Golden re-figé MAÎTRISÉ** : vérifier que la dérive vient bien de l'humidité (les
  semaines à pluie/sécheresse du smoke), recapturer `--capture`, **noter le hash +
  justification dans `00_etat.md`**. Idem population si elle bouge.
- MAJ `00_etat.md` (① → FAIT, hash, dérive expliquée) puis commit.

## Pièges
- **Double-comptage** : ne PAS garder le delta plat ET l'apport médié. On REMPLACE.
- **Ne pas casser les pots/bacs** : `tick_hydrology` a déjà `drainage_override` et
  retourne `pertes` ; ajouter `pluie_event` sans toucher à ces deux-là (défaut 0).
- **Sécheresse** : ne jamais rendre l'humidité négative ; on réduit l'apport, point.
- Vérifier que l'assèchement Canicule fonctionne SANS le delta plat (l'évaporation∝T_sol
  doit suffire) — sinon ajuster `PLUIE_APPORT["Canicule"]`/le coef évaporation, et le NOTER.
