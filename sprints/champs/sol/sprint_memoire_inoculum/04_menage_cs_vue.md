# Tronçon ④ — Ménage C# + Vue Godot (banc rotation)

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` +
> `docs/champs/sol/conception_memoire_inoculum.md` (§8, §11). Pré-requis : ①②③
> faits. Deux volets : ménage C# (clôt la lettre de D10) + vue Godot (règle : tout
> sprint finit par sa vue). Build C# : `dotnet build Symbiose.csproj` sur la VM.

## Golden ATTENDU : **INTACT**
Pur-vue C# + suppression de code mort C# + ajout de champs snapshot (hors math du
tick). Aucun re-figeage. `python3 -m tests.test_golden` inchangé.

## Volet A — Ménage C# (§8)
Supprimer le code **MORT** de `core/EcoFields.cs` (rien de vivant ne l'appelle,
vestige du portage intégral abandonné SS⑦, Option B) :
- champ `public float PathogenPressure` ;
- méthode `TickPathogen(...)` ;
- l'entrée `{ "pathogen", PathogenPressure }` de `Summary()` ;
- l'usage `eco.PathogenPressure > 0.6f` de l'indicatrice molène dans
  `core/PlantCatalogue.Indicatrices.cs` (retire la lambda `Check` ou l'entrée si
  elle devient vide — reste chirurgical, ne casse pas le registre voisin).
`dotnet build` doit rester **vert**. C'est ce volet qui **clôt formellement D10**.

## Volet B — Vue Godot
1. **Snapshot** — expose l'inoculum au pont. Dans `tools/simserver/serialize.py`,
   ajoute au snapshot de tuile un bloc `inoculum` (par plot chargé : famille
   dominante + charge totale, ou map compacte — reste sobre, lecture pure du champ
   déjà calculé, AUCUN recalcul). Bump `ENGINE_VERSION` (actuel `0.5.38` →
   `0.5.39`) dans `tools/simserver/version.py` et **aligne les 3 checks de test**
   qui lisent la version en dur (cf. D76 : `tests/simserver/conteneurs.py`,
   `voix.py`, `structures.py`) sinon `test_sim_server` casse.
2. **Heatmap F6** — `visuals/FieldOverlay.cs` : ajoute une palette `["inoculum"]`
   (langage visuel « charge pathogène » : clair sain → rouge/brun vicié, bornes
   fixes) au dictionnaire `Palettes` et intègre `inoculum` au cycle F6 (comme
   ph/microbiome). C# lit le bloc snapshot ; défaut absent ⇒ 0 (rétro-compat).
3. **Banc F5 `rotation_inoculum`** — un banc d'observation (patron des bancs
   existants, ex. `luxuriance`/`floraison_saisons`, hook `BANC_POST_INIT`) qui
   met en scène : une planche en **monoculture de Solanacées** répétée (inoculum
   monte, maladie s'aggrave) vs une planche **tournée** (familles alternées, sol
   sain) → démontre §11. Molène doit finir par coloniser la planche viciée.

## Ce qu'il NE faut PAS faire
- NE PAS toucher la math du tick (golden intact).
- NE PAS recalculer l'inoculum côté C# (Godot est une vue ; lecture du snapshot).
- NE PAS oublier l'alignement des 3 checks `engine_version` (piège D76).

## À la fin
`00_etat.md` : sprint CLOS, hash golden final, points F5 restants (§11). Mets à
jour `DETTE.md` (D10 → CLOS) et `BACKLOG.md`. Message F5 pour Nico.
