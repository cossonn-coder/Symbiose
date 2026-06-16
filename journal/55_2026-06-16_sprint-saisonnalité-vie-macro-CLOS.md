## 2026-06-16 — Sprint saisonnalité vie macro — CLOS (golden RE-FIGÉ maîtrisé)

**Origine** : retour F5 t6·B de Nico (gravé 2026-06-12) — *« la vie grouille
encore en hiver et ne se réveille qu'à l'été »*. Diagnostic chiffré
(`docs/conception/CONCEPTION_SAISONNALITE_VIE_MACRO.md` §0) : la seule modulation
saisonnière était `warmth(T)` ; en climat océanique doux elle reste à ~0.42 début
hiver **et** l'inertie 0.85 symétrique fait traîner la décrue ~13 semaines ; le
réveil, purement thermique, est mou et un Redoux le tromperait.

**Conception FIGÉE** (3 décisions Nico, doc d'abord) : **photopériode + inertie
asymétrique**, **une fenêtre par guilde**, doc rédigé puis validé (« je te fais
confiance, tant que ça amène vers un réalisme biologique »).

**Modèle** (carte blanche, cœur dans `fields/population.py`, couche `fields`
intacte — aucun import `sim`) :
- **Deux signaux séparés** dans `survie` : `phenology(wiy)` dit QUAND la guilde
  est active, `warmth(T)` COMBIEN. `survie = phenology · warmth · (1−préd) ·
  (1−perturb)`.
- `daylength(wiy) = 12 + 4·cos(2π(wiy−25)/52)` — longueur du jour PURE (8 h↔16 h,
  pic solstice wiy≈25, qui précède le pic thermique wiy≈30). Photopériode =
  signal anticipateur déterministe, robuste aux redoux (≠ température bruitée).
- `phenology = smoothstep(daylength, daylen_min, daylen_full)` — **fenêtre par
  guilde** data-driven sur `TrophicSpec` : ravageur/auxiliaire 10→13 h (estival),
  pollinisateur 12→14.5 h (étroit, jours longs), vers 8.5→10 h (large, sol
  tamponné → quasi toujours actif). `daylength` non-monotone ⇒ une seule rampe
  donne réveil printanier ET dormance automnale.
- **Inertie asymétrique** : `inertia_decay`=0.55 (décrue, extinction ~4 sem) si
  `cible < pop`, sinon `inertia`=0.85 (montée inchangée). Resserre la dormance
  sans casser les boom-bust estivaux. Knob de recours → 0.70 si bust trop pointus.
- **Threading minimal** du `wiy` : `boucle.py:235` → `tick_populations(…, wiy)` →
  `PopulationField.tick(…, week_in_year)`. `phenology` calculé UNE fois hors de la
  boucle r×c (scalaire global tuile) → **coût perf nul**. Défaut `wiy=25` (plein
  été) pour les appels de test sans saison.

**Décision — golden RE-FIGÉ maîtrisé (annoncé)** : le golden capture
`health`/`growth_factor`/`stress_memory` + résumé éco, **jamais** les champs de
population directement. Unique voie de propagation = `ravageur → herbivorie
(HERBIVORY_GAIN, D31.2) → santé`. La dérive est donc **localisée** : la pression
d'herbivorie baisse hors été (dormance), ce qui change les trajectoires de santé
sur le smoke 2 tuiles × 4 ans. Hashs re-figés : smoke `908f591b…`→`af3bfa8f…`,
population `435e6f72…`→`6dc7004d…`.

**Mesures (intégration 110 sem, 2 tuiles)** — pathologie corrigée :
ravageur pic 0.187 / hiver 0.007, auxiliaire 0.151 / 0.005, pollinisateur 0.250 /
0.001 (dormance franche, plus de traîne) ; **vers** pic 0.156 / hiver 0.070
(~45 % du pic — reste actif, valide la fenêtre par guilde).

**Tests** : `tests/test_population.py` — 3 tests-preuve ajoutés (indépendants du
hash) : `test_saisonnalite_dormance_reveil` (3 guildes décollent puis s'éteignent,
hiver < 0.02), `test_vers_insensibles_photoperiode` (hiver > 25 % du pic),
`test_photoperiode_verrouille_redoux` (un +20 °C en plein hiver wiy=46 ne réveille
pas le ravageur — signature lumière ≠ température). Les **19 suites** passent
(golden, génétique 20, croissance 67, vigueur, sénescence, compétition 14, eau,
fruits, attraction, maîtrise, sim_server, signes, ombre_maison, phototropisme…).

**Hors périmètre (laissé câblable)** : `temperature_sol` (le vers lira le sol
tamponné, pas l'air — sprint physico-chimie), floraison réelle / phénologie
florale (arc pollinisation, s'appuiera sur la même horloge `daylength`), portage
C# / vue Godot (la vue échantillonne déjà le champ → la saisonnalité se voit
gratuitement une fois le moteur recalé).

**Sprint CLOS.** **Suivant pressenti (choix Nico)** : arc **pollinisation & cycle
de vie** (conception d'abord — `daylength` posée exprès comme fondation), puis
tout ce qui rend la vie réaliste (compost/interconnexions, champignons…).

---
