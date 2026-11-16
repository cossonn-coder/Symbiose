# ① Températures extrêmes — nuit la plus froide, jour le plus chaud, feuille

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_niche_thermique.md` §1 et §3.
> Golden attendu : **RE-FIGÉ annoncé** — le gel existant (`boucle.py`, `frost_sev`) lit la
> nuit la plus froide, donc il gèle plus souvent.

## Objectif
Donner au moteur les extrêmes de la semaine, sans nouveau champ de grille.

## À faire
1. **Mesure AVANT** (script sous `mesures/` de ce sprint, seed 42, 8 ans) : semaines avec une
   nuit < 0 °C sur sol nu sans vent (référence du 2026-11-16 : 54, min −7,8 °C), et T_air
   hebdo max (24,9 °C). Même calcul que la mesure de conception : `temp_norm` +
   `temperature_delta` + `nebulosite_dynamique`, `RAYONNEMENT_NOCTURNE`.
2. **Nuit la plus froide** dans `t_min_nuit_at` (`fields/ecofields/thermique.py:73`) : un
   terme d'écart à la nuit type, plus grand par ciel clair (`1 − nébulosité`), **pur et
   déterministe** (pas de RNG ; si un hash est nécessaire, `fields/noise.py`). Une
   constante nommée dans `fields/ecofields/constants.py`, avec commentaire pédagogique.
   Garder la signature : tous les lecteurs actuels (gel de `boucle.py`, rosée, glace,
   givre) voient désormais la nuit la plus froide. Si l'un d'eux doit rester sur la nuit
   type (la rosée intègre plutôt la nuit moyenne), garder un helper `nuit_type` et le dire.
   **Cible** : ≈ 12-15 semaines par an avec une nuit < 0 °C sur sol nu, minimum vers −10 °C
   [cible, ordre de grandeur Caen].
3. **`t_max_jour_at(eco, r, c, t_air, nebulosite)`**, même fichier, miroir pur :
   `T_air + AMPLITUDE_DIURNE·(1 − nébulosité) + écart au jour type`. **Cible** : semaine
   de canicule 33-40 °C en plein soleil.
4. **`t_feuille(plant, eco, ...)`** : `t_max_jour + ECHAUFF_FEUILLE·lumière_reçue·soif`,
   `ECHAUFF_FEUILLE ≈ 12`. `soif` ∈ [0,1] lue sur un proxy **existant** (`drought_memory`,
   ou humidité ressentie D111 ④ dans `sim/engine/croissance.py` ≈ l. 294) : choisir après
   lecture et le justifier en commentaire. Place : couche `sim` (elle lit une plante) ou
   `fields` si elle ne lit que des champs ; respecter `plants ← fields ← sim ← engine`.
   Rien ne la lit encore (lecteurs au ③), mais un test la couvre.
5. **Mesure APRÈS** + perf du smoke (cProfile) consignées dans `00_etat.md`.
6. **Re-figeage** : lire le diff du digest (il doit s'expliquer par des gels plus fréquents
   sur les semis, seul stade touché à ce tronçon), puis `--capture`, et consigner les hashes.

## Tests
- Test ciblé : nuit la plus froide ≤ nuit type ; paillage/neige/voile réchauffent toujours ;
  jour le plus chaud ≥ T_air ; T_feuille à l'ombre ≈ t_max_jour ; T_feuille d'une plante
  assoiffée au soleil > celle d'une plante arrosée ; déterminisme.
- Suites existantes : `tests/test_meteo_heterogene.py` et tests de gel/rosée/glace
  (adapter seulement ce qui figeait l'ancienne nuit, en le disant).

## Ne PAS faire
- Lire T_feuille ou les limites des plantes (c'est le ②/③). Toucher au filtre `semis`.
- Changer `temp_norm` (le climat moyen reste le même : on ajoute les extrêmes).
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`00_etat.md` : ① FAIT, mesures, hashes. Commit.
