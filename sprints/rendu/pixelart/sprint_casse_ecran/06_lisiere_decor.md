# ⑥ Lisière et décor : dialecte forêt, animé au vent et à la lumière

Lire d'abord : `CLAUDE.md`, `00_etat.md` (§Notes ① ③ ④), `docs/rendu/pixelart/etude_brief_da_16bits.md`
(dialecte 2 ; masse buissonnante ; rochers), `docs/rendu/pixelart/conception_casse_ecran.md`
§1 (résidus) et §4. **Golden intact.** Filet : `dotnet build Symbiose.csproj`.
Pas d'appel DeepSeek. Ne JAMAIS lancer `test_epaisseur_500ans`.

## Contexte
Décor = atlas de pièces pixel-art en 1 draw call (`visuals/DecorLayer*.cs`, sprint
FLUIDITÉ PC ③) + couche `DecorDevant` (z 30, `DecorLayer.Devant.cs`) ; géométrie de vérité
`data/code/fields/peripherie.py` (lecture seule ici). `DecorLayer.MaxZoom = 4` (au-delà, la
lisière sort du cadre : voulu).

## Objectif
1. **Dialecte 2 (Chrono Trigger forêt)** sur la lisière : couvert olive en grain en chevrons
   (2×3 px), rampes du brief (`#302806 … #aab164`), pas de contour, bord haut le plus clair ;
   forêt en rideau, berges, falaise et éboulis repassés dans la même grammaire (rochers :
   3 tons + éclat, ombre sous le bord, jamais de contour noir).
2. **Même pipeline indexé que ③** pour le décor → l'éclat suit le soleil réel, comme les
   plantes (D112 k « à la lumière »).
3. **Animé au vent** (D112 k) : déformation dans le shader du décor, pilotée par le bloc
   `weather.wind` du snapshot (force, direction, risées — `tools/simserver/vent_pont.py`),
   amplitude par type de pièce (houppiers > sous-bois > roseaux ; roche = 0), phase au hash
   de position — **aucun redessin CPU**. Cohérent avec l'onde de vent des plantes
   (`visuals/WindWave.cs`) : mêmes fronts si possible.
4. **Résidus de lisière** : (a) le **vert uni au-delà de la bande de 9 m** → texture en
   dialecte 2 jusqu'au bord du cadre ; (b) la **face de falaise en grands blocs unis à ×2**
   → strates/blocs à l'échelle du palier ; (c) le **pic de redessin du décor au changement
   de palier ×4** (165 ms [n=1 run, VM chargée]) → mesurer à l'outil Z, réduire (cuisson
   préalable par palier, déjà le principe « décor prêt par palier » du sprint LEVIERS).

## Validation
Captures 4 rotations × ×0,5/×1/×2/×4, vent calme et fort (`tools/capture_vm.sh -v`) ; banc ① ;
à-coup ×2↔×4 avant/après (touche Z) ; draw calls du décor inchangés (1 + 1 devant).

## Ne PAS faire
Changer la géométrie de la ceinture (moteur) ; afficher le décor au-delà de ×4 ; animer en
continu ce qui ne bouge pas sous le vent (DA : l'animation est un signal — ici le signal
est le vent).

## Fin de tronçon
`00_etat.md` §Notes ⑥ ; commit. F5 Nico : lisière par vent calme puis fort, au fil de la
journée.
