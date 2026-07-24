# 2026-07-24 — Sprint MÉMOIRE D'INOCULUM DU SOL (D10) — CLOS

`/sprint-auto sprint_memoire_inoculum` (①→④). Solde **D10** en la scindant en
deux : **ménage** du code C# mort (portage Option B purgé) + **idée écologique
neuve** = mémoire d'inoculum de tuile persistante (« terre malade », pédagogie
de rotation, philo #2/#6). Golden de départ et d'arrivée : **`57c166d8…`
INCHANGÉ sur les 4 tronçons**, `dotnet build` VERT.

## ① Champ `InoculumField` dormant — `664d36f`
Champ **sparse** `(r,c)→{famille→charge}` (`fields/ecofields/inoculum.py`, 30 LDC)
indexé par **famille botanique** (D3 : rotation hôte-spécifique émergente).
Alimentation par **CONSÉQUENCE**, 2 canaux : (1) dépôt continu des plantes
vivantes dont `infection_memory > INOC_DEPOT_SEUIL` (passe par-plante de
`apply_disturbances`, zéro nouvelle boucle) ; (2) pulse de résidu à la mort d'une
plante infectée (`deposer_mort`, garde idempotent). Décroissance passive
`×INOC_DECAY` rabattue par le microbiome suppressif (étape 4g de la boucle).
Champ **DORMANT** (personne ne le lit) → **golden INTACT** attendu et obtenu.
7 constantes placeholder (calage F5). `test_inoculum` 15/15.

## ② Couplage `disease_probability(family)` — `a307228`
Point de greffe **UNIQUE** : `disease_probability(r,c,base,family=None)` lit
`inoculum.at(r,c,family)` et amplifie `× (1 + INOC_GAIN·charge)`. Trois appelants
passent la famille : `damping_off`, `fungal_disease` (perturbations.py),
mildiou-rondelle (resolution.py). **Le signal SAR** (`croissance.py:316`,
`family=None`) reste **inoculum-free** → la boucle
inoculum→SAR→infection_memory→inoculum est **CASSÉE** (D5, anti-runaway).

**Golden INTACT alors que le kickoff autorisait un re-figeage maîtrisé** : le
smoke n'accumule que ~0.058 d'inoculum sur 1 plot (`infection_memory` plafonne à
0.284, juste sous le seuil de dépôt 0.3) → l'amplification continue (~+8,7 % sur
ce seul plot) ne flippe aucun tirage discret. Couplage bien **LIVE** (prouvé en
test ; hash retombe à `INOC_GAIN=0`). Un golden inchangé étant plus sûr qu'un
re-figeage, on ne force PAS de dérive artificielle. `test_inoculum` 20/20.

## ③ Molène indicatrice + 5 voix — `7c05366`
Ajoute la **molène** (*Verbascum thapsus*, Scrophulariaceae, bisannuelle
monocarpique) comme indicatrice de sol vicié, **hors gradient de succession**.
Nouvelle porte de RELÂCHE `arch_inoculum` (patron `arch_ph`) : germination
gouvernée par `smoothstep(inoculum.total, INOC_MOLENE_SEUIL, 2×seuil)` sur la
seule molène → colonise les plots durablement infectés. `choisir_archetype` la
priorise sans déplacer les 4 archétypes classiques. **5 voix** : encyclopédie
(fiche 3 niveaux, 46→47), carnet (concept **interne** « maladie » via
`CONCEPT_DE` + cause `sol_vicie`), page secrète P37 (lore médicinal), magazine
(famille auto), événements (ledger). **Golden NEUTRE atteint : INTACT** (inoculum
nul sur le smoke → molène jamais candidate). `test_inoculum` 32/32, `test_pages`
64/64, `test_encyclopedie` 64/68 (4 échecs gestes/outils **préexistants**).
Décision : concept « maladie » gardé **carnet-interne** (pas dans encyclopédie
`CONCEPTS`) — l'y ajouter serait une mécanique de maîtrise neuve hors périmètre.

## ④ Ménage C# (D10 CLOS) + vue Godot — `b42b95e`
**Volet A — ménage** : supprime `PathogenPressure` (champ), `TickPathogen`,
l'entrée `"pathogen"` de `Summary()`, et l'usage `eco.PathogenPressure>0.6f` de
l'indicatrice molène (`PlantCatalogue.Indicatrices.cs`). Vestiges du portage
intégral abandonné (Option B, SS⑦) → **divergence D10 formellement CLOSE**.
Build C# **VERT**. **Volet B — vue** : snapshot inoculum par tuile
(`serialize.py`, liste creuse, lecture pure) ; pont **0.5.38→0.5.39** + 3 checks
`engine_version` alignés (piège D76) ; heatmap **F6** `inoculum` (palette
clair→rouge vicié) via `cmd_fields` dans `FieldOverlay.cs` ; banc F5
**`rotation_inoculum`** (monoculture Solanacées viciée vs planche tournée saine,
molène qui colonise). **Golden INTACT.** `test_sim_server` 269/270 (le seul rouge
= pommier-fruit, **décalage phénologique préexistant**, décorrélé).

## Notes
- **`EvaluateIndicators`** (`PlantCatalogue.cs:112`) reste **orphelin** : dead
  code **préexistant hors périmètre** du kickoff ④ (qui ne nomme que
  `PathogenPressure`/`TickPathogen`) → non touché (règle « mentionner, ne pas
  supprimer le dead code non lié »). Candidat à un futur ménage.
- Refactor auto-léger **no-op** : aucun fichier touché ne dépasse 400 LDC pur
  (max `encyclopedie_corpus.py` à 394, jaune, corpus narratif SRP).
- **DETTE** : D10 → CLOS. **BACKLOG** mis à jour.

## Reste F5 Nico
- Heatmap **F6 `inoculum`** (rouge vicié sur monoculture, sain sur rotation).
- Banc **`rotation_inoculum`** : maladie qui s'aggrave en monoculture, molène qui
  finit par coloniser la planche viciée.
- Calibrage des placeholders au banc : `INOC_DECAY` (demi-vie ~2 saisons),
  `INOC_GAIN`, `INOC_DEPOT_SEUIL`, `INOC_MOLENE_SEUIL=0.4`.
