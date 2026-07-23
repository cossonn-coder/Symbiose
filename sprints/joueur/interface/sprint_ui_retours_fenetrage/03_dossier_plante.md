# T3 — Dossier de plante au clic (outil de test) — VUE + PONT

**Sprint :** `sprint_ui_retours_fenetrage` (dernier tronçon).
**Nature :** VUE C#/Godot + petit ajout de SÉRIALISATION (pont).
**Golden : NEUTRE** (le snapshot n'est pas figé par `test_golden` ; on n'ajoute AUCUN
état moteur, seulement de la lecture sérialisée). À vérifier explicitement (voir §Golden).
**Doc de conception :** `docs/joueur/interface/conception_retours_ui_fenetrage.md` §4.
**Prérequis de lecture :** `CLAUDE.md` + `00_etat.md` + ce fichier.

## Objectif
Clic sur une plante → panneau **debug read-only** affichant son **état physiologique
courant** (pas une chronologie — il n'en existe pas côté moteur). C'est un instrument
de test, du même rang que les overlays F6/F7, hors HUD de découverte.

## Pourquoi « dossier » et pas « historique »
Aucun journal chronologique par instance n'existe. `plants/base/instance.py` porte des
**mémoires scalaires intégrées** qui SONT l'histoire compressée de la plante. On les
expose telles quelles (honnête, gratuit) plutôt que de fabriquer un log moteur.

## Partie PONT — `data/code/tools/simserver/serialize.py`
Dans la sérialisation par plante VIVANTE (le bloc après `base["dead"] = False`, là où
sont déjà posés `vitalite`, `etat`, `genes`, `leaf_symptoms`), AJOUTER :
- Les **8 mémoires** de l'instance : `shade_memory`, `drought_memory`, `asphyxie_memory`,
  `cold_memory`, `infection_memory`, `wind_memory`, `root_herbivory_memory`,
  `stress_memory` (arrondies, ex. 3 déc.). Les regrouper sous une clé `"memoires"`
  (dict) pour ne pas polluer le socle.
- `"expression"` : `{gène: round(f, 3)}` pour les facteurs ≠ 1.0 (dict, éventuellement
  vide) — lu depuis `p.expression`.
- `"age_weeks"` : `p.age_weeks` ; `"age_years"` : `round(p.age_years, 2)`.

Ces champs sont de la **pure lecture** d'un état déjà porté par l'instance → hors
`_PLANT_ATTRS` du golden → golden NEUTRE. **Bump de version du pont** (incrémenter la
version dans `version.py` avec une ligne de changelog, comme les tronçons précédents).

Vérifier le nom EXACT des attributs dans `plants/base/instance.py` avant d'écrire (ils
sont tous présents dans le `@dataclass PlantInstance` ; ne rien inventer). Tolérer une
plante neutre (`expression` par défaut = tous 1.0 → dict filtré vide ; `genes` = {}).

## Partie VUE — C#
- **Picking** : réutiliser `FindPlant(worldPos, radius)` (déjà employé par
  `WorldView.Etiquettes.cs`, `WorldView.Genes.cs`, `WorldView.Actions.cs`). Décider du
  déclencheur : soit un **mode d'inspection** dédié (touche debug, ex. réutiliser l'esprit
  du survol gènes F7/G), soit un clic gauche quand aucun geste n'est actif. Choisir le
  plus simple qui n'entre pas en conflit avec les gestes (recommandé : une touche debug
  qui, tant qu'active, fait du clic un « inspecter » ; cohérent avec le registre F6/F7).
- **Source des données** : lire le **dict du dernier snapshot** correspondant à la plante
  pointée — NE PAS relancer d'appel pont. Les nœuds plante sont indexés par clé
  `tile|species|x|y` (`WorldView.Snapshot.cs:25`, `_plantNodes`) et portent les metas
  tile/lx/ly/species. Conserver, au moment où `ApplyPlants`/la synchro traite le snapshot,
  un dictionnaire `clé → payload plante` (le `GDict` de la plante), lu par le panneau.
  (Si un tel cache n'existe pas, l'ajouter dans `WorldView.Snapshot.cs` : peu coûteux,
  une entrée par plante vivante déjà itérée.)
- **Panneau** : un `Control`/`Panel` debug read-only (nouveau fichier, ex.
  `world/DossierPlantePanel.cs`), affichant en texte : espèce · plot(x,y) · stade + âge ·
  vitalité/état · symptômes (cause : intensité) · mémoires (mot ou valeur) · expression
  (gène ×facteur) · gènes. Fermable (clic ailleurs / Échap — attention à la précédence
  Échap posée en T2 : ce panneau doit être « fermé par Échap » AVANT le retour accueil).
  Chiffres tolérés (registre debug, #5). Un fichier = une responsabilité ; viser < 300 LDC.

## Golden
- `python3 -m tests.test_golden` depuis `data/code/` : **INCHANGÉ** (hash identique
  avant/après). Si le hash bouge, c'est une FUITE (un attribut a été ajouté à
  `_PLANT_ATTRS` ou une écriture moteur a glissé) → corriger, ne jamais re-figer.
- Build C# `dotnet build Symbiose.csproj` VERT.

## Ne PAS faire
- Ne PAS ajouter d'état moteur (pas de nouveau champ persistant sur `PlantInstance`, pas
  de log par instance). Uniquement de la sérialisation en lecture.
- Ne PAS en faire une voix narrative / une fiche encyclopédie / le carnet — c'est un
  outil de test distinct (#5/#6).
- Ne PAS ré-interroger le pont au clic (lire le dernier snapshot en mémoire).

## Points F5 (Nico)
- Clic (mode inspection) sur une plante → panneau avec son état physiologique complet.
- Une plante stressée montre des mémoires élevées (ombre/soif/…) cohérentes avec ce
  qu'on observe → diagnostic F5.
- Le panneau se ferme proprement ; Échap le ferme avant de revenir à l'accueil.

## En fin de tronçon
MAJ `00_etat.md` (Avancement T3 : champs pont ajoutés, nouvelle version pont, golden
inchangé, build). Phase C (clôture) gérée par l'orchestrateur `/sprint-auto` : MAJ
`DETTE.md` (D54-a avancé, D55 complété) + `BACKLOG.md` + `journal.md`, commit final.
