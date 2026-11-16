# ④ Sol et expansion — clonalité, portée, azote, allélopathie, mycorhize

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_caracteres_vivants.md` §2.4 et §3.
> Golden attendu : **RE-FIGÉ annoncé** — cinq clés neuves ; les ramets, la dispersion,
> l'azote, l'allélopathie et l'absorption lisent la plante.

## Objectif
Les lignées diffèrent dans leur façon d'occuper le sol et de vivre avec leurs voisines.

## À faire
1. **Cinq caractères en queue** : `vigueur_clonale`, `portee_graine`, `fixation_azote`,
   `allelopathie`, `mycorhization` (§2.4).
2. **Clonalité** (`sim/clonal.py`) : cadence (`clonal_interval`) et portée
   (`clonal_radius_cm`) modulées par le gène. Prix : `reproduction_rate` ÷ gène là où les
   graines sont produites. Un ramet hérite des gènes et du F de sa mère (vérifier).
   Attention : les ramets sont le moteur de l'explosion de population (mémoire « profil de
   perf ») ; mesurer la population à 5 ans avant/après (`data/code/tools/diag_population.py`).
3. **Portée des graines** : distance anémochore × gène (`sim/engine/mortalite.py` ≈ l. 38-47,
   `ANEMOCHORIE_PORTEE_PLOTS`). Prix : levée plus fragile (une lecture dans la germination,
   `sim/succession.py`).
4. **Fixation d'azote** : l'effet de famille des légumineuses (`plants/base/familles.py` ≈
   l. 546, effet `inject_field` azote) est multiplié par le gène **et** freiné quand l'azote
   local est déjà haut (réel : la plante cesse de fixer en sol riche). Lire comment l'effet
   de famille est résolu (`sim/effects/`) avant de choisir le point d'accroche : il faut
   accéder à la plante émettrice.
5. **Allélopathie** : quantité émise (`familles.py` ≈ l. 385, même route `inject_field`) ×
   gène. L'autotoxicité existante (étape 17a de `boucle.py`) suit naturellement.
6. **Mycorhization** : la compensation mycorhizienne de l'absorption
   (`fields/ecofields/uptake.py`) × gène, avec un prix en sucre (`cout_genetique`) qui ne
   paie que si le sol est pauvre (le gain est déjà nul en sol riche si la formule le prévoit ;
   vérifier, sinon le dire).
7. **Re-figeage** : diff lu, `--capture`, hashes, population à 5 ans consignée.

## Tests
- Test ciblé par caractère (cadence de ramets, distance de vol, azote injecté selon le gène et
  freiné en sol riche, émission allélopathique, absorption selon le gène).
- Suites clonal, allélopathie, mycélium, uptake vertes.

## Ne PAS faire
- Créer un champ de grille neuf.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`00_etat.md` : ④ FAIT, hashes. Commit.
