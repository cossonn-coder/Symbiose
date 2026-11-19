# 2026-11-19 — Sprint DÉPART DU JARDIN (D140 A+B+C) — CLOS côté code

Dossier : `sprints/vegetal/genetique/sprint_depart_jardin/` · conception
`docs/vegetal/genetique/conception_depart_jardin.md`.

①②③ faits le 2026-11-18 (pâturin anémophile + gènes muets gratuits, golden `98a050cf…` ;
borne de gel −0,5 °C + tendres + chronique `froid`, golden `25671775…` ; monde `full` ouvert
s10 avec les 52 espèces mûres). Suspendu ensuite pour l'hécatombe d'herbivorie (D140 G),
résolue par `sprint_plante_vivante` + `sprint_stress_au_bilan` (bilan carbone, F5 validé
2026-11-19). Repris par `/sprint-auto` le 2026-11-19 :

- **④** (`848dbd3`) pot DANS la maison (`world/interieur.py` : 17,5 °C, ni gel ni pluie,
  lumière ×0,3) + geste `repiquer` (`sim/repiquage.py`) : même plante pot → pleine terre,
  choc **au bilan** (absorption réduite, repousse du chevelu payée sur les réserves, ∝ racines
  à l'étroit) — mesuré 2-3 sem de stagnation, −2 à −4 cm, aucun mort [seed 42, n=1].
  Monde `full` : 3 godets (tomate, basilic, poivron). Pont 0.6.25.
- **⑤** (`836dfaa`) l'automate repique (règle réactive `tools/jardinier_auto/repiquage.py`) :
  après la fenêtre « gelée tardive », nuit la plus froide (passée + 2 sem prévues) > limite
  + 0,5 °C, plot libre le plus lumineux. Sortie mesurée **s17-s18 (mi-juin)**, pas fin mai :
  les nuits du moteur ne passent 10 °C qu'en s14. Godets de la fabrique = pot posé
  (déblocage). Pont 0.6.26.
- **⑥** (`cc1317b`) vue : `repiquer` (palette semis, icône, curseur, 2 clics), godets sur
  l'appui des fenêtres sud, feuilles tombantes du choc ; banc `depart_jardin` + oracle
  (tomate trop tôt meurt de `froid` en s5). `dotnet build` vert.

**Golden final `bce813af…`** (④⑤⑥ intacts). Refactor auto-léger : rien > 400 LDC ; 🟡
`geste_corpus.py` 360, `serialize.py` 334, `carnet.py` 310, `WorldView.Snapshot.cs` 305,
`WorldView.Hud.cs` 303.

Constats non corrigés : pas d'étiolement à la fenêtre ; choc presque toujours « fort » ; pot
dehors sans gel ni pluie ni arrosage ; plantules des godets non dessinées (pas de
structure) ; godet 2 L lu comme un plateau ; sol à 13-14 °C début avril ; Vigueur LIBRE de
l'automate ramenée au plafond (D81 c). D140 D, E, F restent ouverts. **F5 Nico attendu**
(recette dans `00_etat.md`).
