# Tronçon ② — Refroidissement évaporatif (chaleur latente)

> Sprint thermique-microclimat. Conception : `docs/champs/climat/conception_thermique_microclimat.md`
> (§2.1, §3, §5). Kickoff **autosuffisant** (relançable à froid).
> Pré-requis : ① CLOS (champ `temperature_sol` + `tick_thermique` + helper pur
> `fields/ecofields/thermique.py` ; golden re-figé `50a6fd2d…`).

## Objectif

Ajouter le terme **chaleur latente** à la cible thermique : un sol humide reste
frais (l'eau qui s'évapore prend de l'énergie au sol). C'est ce terme qui crée le
**cercle vicieux de la sécheresse** : sec → moins de refroidissement → plus chaud
→ évapore plus → encore plus sec. Émergent recherché du sprint.

## Modèle (ce tronçon — terme ajouté à `cible`)

```
cible[r,c] = T_air + GAIN_SOLAIRE · lumière_sol[r,c] · intensité_saison
           − REFROID_EVAP · humidité_norm[r,c]                         ⟵ ② NOUVEAU
```

- `humidité_norm = humidite.at_plot(r,c) / 3.0` (échelle humidité = [0,3], borner [0,1]).
- `REFROID_EVAP = 6.0` °C (refroidissement max d'un sol saturé) — déjà prévu dans
  la conception §3 mais **pas encore ajouté à `constants.py`** (réservé à ②).

L'inertie lerp (①) reste appliquée APRÈS le calcul de la nouvelle cible.

## Étapes

1. **`fields/ecofields/constants.py`** — ajouter le knob :
   `REFROID_EVAP = 6.0` (dans le bloc « Microclimat de surface T_sol » créé en ①).
   Ne PAS encore ajouter ISOLATION_COUVERT/LITIERE_REF/K_NEBUL (réservés ③④).

2. **`fields/ecofields/thermique.py`** — dans `tick_thermique`, lire l'humidité du
   plot et soustraire le terme latent à `cible` :
   ```python
   hum_norm = min(1.0, eco.humidite.at_plot(r, c) / 3.0)
   cible = (t_air + GAIN_SOLAIRE * lum * intensite
            - REFROID_EVAP * hum_norm)
   ```
   Importer `REFROID_EVAP` depuis `.constants`. Mettre à jour le docstring du module
   (le modèle passe à 2 termes). Rester pur, zéro log.

   ⚠️ **Ordre de lecture** : `tick_thermique` tourne en 2b, AVANT `tick_hydrology`
   (3). Donc `eco.humidite` lue ici = l'humidité de **fin du tick précédent** (pas
   encore évaporée ce tick). C'est cohérent (la T_sol du matin dépend de l'humidité
   accumulée), et déterministe. Ne pas tenter de réordonner.

3. **Golden** — `python3 -m tests.test_golden`. Il échouera (la T_sol baisse sur
   les plots humides → évaporation modifiée → cascade). Vérifier que la dérive est
   **causalement traçable** au terme latent (température/hydro, puis cascade
   croissance/succession comme en ① — c'est ATTENDU, cf. note §REPRISE de `00_etat`).
   Re-figer.

4. **Suites ciblées** : `test_eau`, `test_croissance`, `test_population`,
   `test_genetique` doivent rester **PASS** (elles n'exercent pas la spatialisation
   thermique, comme en ①). Si l'une casse → investiguer avant de re-figer.

## Invariant golden

- **Dérive attendue** : température_sol (plus basse sur sol humide) → évaporation →
  humidité → cascade croissance/succession (traçable, comme ①).
- **Doit rester** : déterminisme (zéro RNG), suites non thermiques PASS, météo
  (tirages `weather_at`) inchangée, T_air (`temperature`) toujours uniforme.

## Validation

- `python3 -m tests.test_golden` re-figé.
- `python3 main.py 3` tourne sans crash (référence comportementale ; le run 30 ans
  par défaut est trop long, 3 ans suffit pour le smoke de non-crash).
- Vérifier de visu (optionnel) que sur la tuile humide la T_sol moyenne a baissé
  vs ① (un `print` jetable, ou comparer `summary`).

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (statut ② ✅ + nouveau hash dans §REPRISE).
- Commit : `feat(thermique) : tronçon ② refroidissement évaporatif (chaleur latente) — golden RE-FIGÉ MAÎTRISÉ (cercle vicieux sécheresse)`.
- Écrire le kickoff `03_isolation_couvert.md` avant le `/clear`.
