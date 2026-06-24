# Tronçon ④ — Nébulosité (effet thermique de la météo, diurne)

> Sprint thermique-microclimat. Conception : `docs/conception/CONCEPTION_THERMIQUE_MICROCLIMAT.md`
> (§2.1, §3, §5). Kickoff **autosuffisant** (relançable à froid).
> Pré-requis : ③ CLOS (cible thermique à 3 termes dans `tick_thermique` ;
> knobs `ISOLATION_COUVERT=4.0`, `LITIERE_REF=2.0` ; golden re-figé `aab6c60a…`).

## Objectif

Moduler la surchauffe solaire par la **nébulosité** de l'événement météo courant :
un ciel couvert bloque le soleil → le sol chauffe moins. C'est le 4ᵉ et dernier
terme de la cible thermique **diurne** (§2.1). Première fois que la **météo
(événement `weather_at`)** entre dans la carte T_sol — d'où le câblage couche
`sim` → `fields` (table de données pure, pas d'import inverse).

## Modèle (ce tronçon — la nébulosité atténue le gain solaire)

```
cible[r,c] = T_air + GAIN_SOLAIRE · lumière_sol[r,c] · intensité_saison · (1 − K_NEBUL_DIURNE · nébulosité)   ⟵ ④ NOUVEAU
           − REFROID_EVAP · humidité_norm[r,c]                                                                ⟵ ②
           − ISOLATION_COUVERT · litière_norm[r,c]                                                            ⟵ ③
```

- `nébulosité ∈ [0,1]` : 0 = ciel clair, 1 = couvert total. Lue dans la table
  `NEBULOSITE` (clé = `event.kind`), donnée PURE dans `constants.py`.
- `K_NEBUL_DIURNE = 0.8` : part de la surchauffe annulée par un ciel **totalement**
  couvert (à nébulosité=1, il reste 20 % du gain solaire).
- La nébulosité est un **scalaire par tick** (la météo est uniforme sur le monde,
  comme T_air) → passée en argument à `tick_thermique`, PAS un champ par plot.

## Étapes

1. **`fields/ecofields/constants.py`** — dans le bloc « Microclimat de surface
   T_sol », ajouter `K_NEBUL_DIURNE = 0.8` puis la table `NEBULOSITE` (copier §3,
   clés = noms d'événements `weather.py`, y compris `"Orage"`/`"Neige"` réservés
   à ⑦ — inoffensifs tant que ces events n'existent pas) :
   ```python
   K_NEBUL_DIURNE = 0.8
   NEBULOSITE = {
       "Beau temps": 0.10, "Sécheresse": 0.05, "Canicule": 0.10, "Gelée tardive": 0.05,
       "Redoux": 0.60, "Pluie prolongée": 0.90, "Tempête": 0.80, "Grêle": 0.70,
       "Orage": 0.85, "Neige": 0.70,
   }
   ```

2. **`fields/ecofields/thermique.py`** — ajouter un paramètre `nebulosite: float = 0.0`
   à `tick_thermique`, importer `K_NEBUL_DIURNE`, et multiplier le terme solaire :
   ```python
   facteur_nebul = 1.0 - K_NEBUL_DIURNE * nebulosite
   cible = (t_air + GAIN_SOLAIRE * lum * intensite * facteur_nebul
            - REFROID_EVAP * hum_norm
            - ISOLATION_COUVERT * lit_norm)
   ```
   Le défaut `0.0` garde la pureté de l'helper (testable sans météo) et = pas de
   nébulosité. Mettre à jour le docstring (4 termes, modèle diurne COMPLET).

3. **`fields/ecofields/container.py`** — `tick_thermique(self, saison, nebulosite=0.0)`
   délègue `_tick_thermique(self, saison, nebulosite)`. Garder court (container dense).

4. **`sim/engine/boucle.py`** — en 1 (déjà calculé `event = weather_at(...)`), importer
   `NEBULOSITE` depuis `fields.ecofields.constants`, calculer une fois par tick
   `nebul = NEBULOSITE.get(event.kind, 0.10)` (défaut = ciel quasi clair), et passer
   à l'appel **2b** : `eco.tick_thermique(saison, nebul)`. ⚠️ Couche : `sim` importe
   `fields` (sens autorisé), JAMAIS l'inverse — la table reste donnée pure côté `fields`.

5. **Golden** — `python3 -m tests.test_golden`. Échec attendu (la surchauffe diurne
   baisse les semaines à ciel couvert → cascade évaporation/croissance/succession).
   Vérifier la traçabilité (température selon la météo) puis re-figer (`--capture`).

6. **Suites ciblées** : `test_eau`, `test_croissance`, `test_population`,
   `test_genetique` doivent rester **PASS**.

## Invariant golden

- **Dérive attendue** : température_sol modulée par la nébulosité de l'événement
  hebdo → cascade hydro/croissance/succession (traçable, comme ①②③).
- **Doit rester** : déterminisme (la nébulosité vient d'une table déterministe
  indexée par l'event déjà déterministe), suites non thermiques PASS, T_air
  (`temperature`) toujours uniforme, `weather_at` inchangé (④ ne touche PAS les
  tirages — c'est ⑦).

## Validation

- `python3 -m tests.test_golden` re-figé.
- `python3 main.py 3` tourne sans crash.
- Vérif mécanisme (print jetable) : à lum/hum/litière constants, T_sol plus basse
  quand `nebulosite` monte (à nébul=1, surchauffe résiduelle = 20 % de GAIN_SOLAIRE).

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (statut ④ ✅ + nouveau hash dans §REPRISE).
- Commit : `feat(thermique) : tronçon ④ nébulosité (effet thermique météo diurne) — golden RE-FIGÉ MAÎTRISÉ`.
- Écrire le kickoff `05_t_ressentie.md` avant le `/clear`.
