# ⑥ Vue : lisière 4 saisons + signes macro — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/rendu/pixelart/etude_brief_da_16bits.md`, en-têtes de
`visuals/decor_indexe.gdshader` et `visuals/DecorLayer.Indexe.cs`, `world/WorldView.Ciel.cs`, `sim/ciel.py`,
`SIGN_TABLE` de `sim/weather.py`, conception §3.5.

## Objectif

Le paysage dit la saison et le temps. Quatre saisons lisibles d'un coup d'œil sur la lisière, et les signes
macro (canicule d'abord) visibles dans le décor.

## À faire

1. **4 saisons** : aujourd'hui aucun fichier du décor ne lit la saison. Le décor passe par une palette indexée
   et un shader (les canaux du sommet sont un contrat : R valeur, G vent, B phase, A alpha, voir l'en-tête ;
   la vérification du masque végétal/roche/eau reste à faire, G = 0 ne suffit peut-être pas).
   Intention : un uniform de saison issu de `week_in_year`, recoloration dans le shader pour les houppiers et
   la prairie, décalée par pied au hash, **sans reconstruire le décor chaque semaine** et à draw calls constants.
   Si le masque exige de ré-encoder le kit, c'est permis à la construction, jamais par semaine.
   Sapins, roche, eau et rivière inchangés. Couleurs dans la palette 16 bits (F11 ON). Aspect visé : conception §3.5.
2. **Signes macro** : table libellé/état → effet, lue du bloc `ciel` et de la météo du snapshot, sans calcul
   d'écologie côté vue. Priorités : canicule et sécheresse (prairie grillée, brume de chaleur), gelée (brume
   rasante, givre), pluie prolongée (prairie sombre), neige (état `snow` de la lisière, à vérifier ; `SnowLayer`
   ne couvre aujourd'hui que les tuiles). Un libellé inconnu ne fait rien. Lisser les transitions.
3. **Mesure** : captures de la lisière aux 4 saisons et avec météo imposée (`-m Canicule`), ×1 et palier le plus
   dézoomé. Lire le PNG, `tools/mesure_da.py` si utile. `tools/perf_vm.sh` : FPS et draw calls inchangés
   `[n=…, VM]`.
4. `dotnet build Symbiose.csproj` vert.
5. **Clôture** : `00_etat.md` §F5 avec un protocole court « une année » (arbres, chute, tapis, lisière, signes),
   rédigé pour un ressenti, le calibrage étant déjà mesuré.

## Golden

**INTACT** (vue pure).

## NE PAS

Changer la loi de la canicule (D107) ni les probabilités. Annoncer un événement que le moteur n'a pas émis.
Lancer `tests/test_epaisseur_500ans.py`.

## F5

Reconnaître la saison sur une capture sans lire le HUD ; canicule visible sur la lisière.
