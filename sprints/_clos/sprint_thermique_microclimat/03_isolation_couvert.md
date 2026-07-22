# Tronçon ③ — Isolation par le couvert (litière)

> Sprint thermique-microclimat. Conception : `docs/champs/climat/conception_thermique_microclimat.md`
> (§2.1, §3). Kickoff **autosuffisant** (relançable à froid).
> Pré-requis : ② CLOS (terme chaleur latente dans `tick_thermique` ; knob
> `REFROID_EVAP=6.0` ; golden re-figé `7cfef331…`).

## Objectif

Ajouter le terme **isolation par le couvert** à la cible thermique : une litière
dense (paillis naturel) tamponne le sol — elle l'isole de la surchauffe solaire
diurne. C'est le pendant thermique du paillage permacole et illustre
l'**interconnexion des acteurs** : la litière issue de la décompo agit sur la
thermique (conception §1, règle d'interconnexion).

## Modèle (ce tronçon — terme ajouté à `cible`)

```
cible[r,c] = T_air + GAIN_SOLAIRE · lumière_sol[r,c] · intensité_saison
           − REFROID_EVAP · humidité_norm[r,c]                          ⟵ ②
           − ISOLATION_COUVERT · litière_norm[r,c]                      ⟵ ③ NOUVEAU
```

- `litière_norm = min(1.0, eco.om_fresh_at(r,c) / LITIERE_REF)` — `om_fresh_at`
  somme les masses des parcelles de litière du plot (déjà existant, container.py:152).
- `ISOLATION_COUVERT = 4.0` °C (tampon max d'une litière dense saturée).
- `LITIERE_REF = 2.0` (masse de litière au-dessus de laquelle le couvert sature).

Les deux knobs sont **prévus dans la conception §3 mais pas encore dans
`constants.py`** (réservés à ③). L'inertie lerp (①) reste appliquée APRÈS le calcul
de la cible.

## Étapes

1. **`fields/ecofields/constants.py`** — ajouter dans le bloc « Microclimat de
   surface T_sol » :
   `ISOLATION_COUVERT = 4.0` et `LITIERE_REF = 2.0`.
   Ne PAS encore ajouter K_NEBUL/nébulosité (réservés ④).

2. **`fields/ecofields/thermique.py`** — dans `tick_thermique`, lire la masse de
   litière et soustraire le terme isolation à `cible` :
   ```python
   lit_norm = min(1.0, eco.om_fresh_at(r, c) / LITIERE_REF)
   cible = (t_air + GAIN_SOLAIRE * lum * intensite
            - REFROID_EVAP * hum_norm
            - ISOLATION_COUVERT * lit_norm)
   ```
   Importer `ISOLATION_COUVERT, LITIERE_REF` depuis `.constants`. Mettre à jour le
   docstring du module (le modèle passe à 3 termes). Rester pur, zéro log.

   ⚠️ **Ordre de lecture** : `tick_thermique` tourne en 2b, AVANT la décompo du
   tick. La litière lue = état de fin du tick précédent — cohérent et déterministe.

3. **Golden** — `python3 -m tests.test_golden`. Il échouera (la T_sol baisse sur
   les plots couverts de litière → cascade évaporation/croissance/succession, comme
   ①②). Vérifier que la dérive est **causalement traçable** au terme isolation
   (température/hydro légère, puis cascade). Re-figer (`--capture`).

4. **Suites ciblées** : `test_eau`, `test_croissance`, `test_population`,
   `test_genetique` doivent rester **PASS** (elles n'exercent pas la spatialisation
   thermique). Si l'une casse → investiguer avant de re-figer.

## Invariant golden

- **Dérive attendue** : température_sol (plus basse sous litière dense) → évaporation
  → humidité → cascade croissance/succession (traçable, comme ①②).
- **Doit rester** : déterminisme (zéro RNG), suites non thermiques PASS, météo
  (`weather_at`) inchangée, T_air (`temperature`) toujours uniforme.

## Validation

- `python3 -m tests.test_golden` re-figé.
- `python3 main.py 3` tourne sans crash.
- Vérif de visu (optionnel) : sur un plot à `lum` égale, plus de litière ⇒ T_sol
  plus basse (print jetable corrélant `om_fresh_at` et `temperature_sol`).

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (statut ③ ✅ + nouveau hash dans §REPRISE).
- Commit : `feat(thermique) : tronçon ③ isolation par le couvert (litière) — golden RE-FIGÉ MAÎTRISÉ`.
- Écrire le kickoff `04_nebulosite.md` avant le `/clear`.
