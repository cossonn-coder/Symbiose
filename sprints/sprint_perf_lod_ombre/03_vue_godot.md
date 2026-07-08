# Tronçon ③ — Vue Godot : gain perf visible + debug émetteurs/récepteurs

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` (D1-D7) + tronçons ①②
> (LOD actif, seuil calibré). Réf. : `docs/conception/CONCEPTION_PERF_LOD_OMBRE.md`.
> **Golden : INTACT** (vue + snapshot read-only). Dernier tronçon (règle vue Godot).
> Le `dotnet build Symbiose.csproj` est le filet de compil ; le F5 visuel = Nico.

## Objectif
Rendre le LOD **observable** et confirmer que le gain perf remonte à l'écran :
1. L'overlay perf existant (F4, ms/tick — livré à D66④ `perf.py` + `WorldView.Hud`)
   doit refléter la baisse de ms/tick. **Pas de code attendu** ici, juste un point
   F5 : vérifier que le chiffre baisse au fil des années par rapport à avant D67.
2. **Toggle debug « émetteurs vs récepteurs »** : teinter les plantes SOUS-SEUIL
   (non émettrices d'ombre) pour voir qui le LOD écarte — cohérent avec la posture
   « affichage technique, déconseillé en découverte » des autres overlays debug.

## Modèle
Une plante est émettrice ssi `height_cm × canopy_radius × foliage_density ≥
SHADING_POWER_MIN` (même métrique que `fields/light.py`, D1). Le snapshot expose
ce booléen ; le rendu C# teinte les NON-émettrices quand le toggle est actif.

## Fichiers à toucher
- **Python (pont)** :
  - `data/code/tools/simserver/serialize.py` (`_snapshot`) — ajouter au dict
    par plante un champ `"emitteur": bool` (calcul de la métrique via
    `p.current_height`, `cls.canopy_radius_at(p)`, `cls.foliage_density_at(p,
    saison)` et `light.SHADING_POWER_MIN`). Lecture pure → golden NEUTRE.
  - `data/code/tools/simserver/version.py` — bump `ENGINE_VERSION` en **0.5.21**
    (ajout additif : nouveau champ snapshot `emitteur`, aucun verbe cassé ; un
    binaire pré-0.5.21 ignore le champ). Documenter la ligne comme les précédentes.
- **C# (vue)** :
  - `world/WorldView.Snapshot.cs` — lire le champ `emitteur` par plante (défaut
    `true` si absent, pour compat binaire pré-0.5.21).
  - `world/WorldView.Controls.cs` — une touche de toggle debug (choisir une touche
    LIBRE, ex. F7 si non prise ; vérifier les toggles existants F4/F6 avant).
  - Rendu : teinte des plantes non-émettrices quand le toggle est actif (via
    `visuals/PlantRenderer.cs` ou une passe d'overlay analogue à `FieldOverlay`).
    Choisir la voie la moins invasive (un modulate/teinte conditionnel).

## À NE PAS faire
- NE PAS modifier le moteur de simulation (le champ `emitteur` est DÉRIVÉ, pas un
  nouvel état de plante).
- NE PAS re-figer le golden (doit rester le hash du tronçon ②).
- NE PAS casser le protocole (ajout additif seulement, défaut `true` côté C#).
- NE PAS lancer `test_epaisseur_500ans` (interdit).

## Vérification de sortie
1. `python3 -m tests.test_golden` → hash du tronçon ② INTACT.
2. `python3 -m tests.test_sim_server` (ou l'équivalent snapshot) → vert, champ
   `emitteur` présent.
3. `dotnet build Symbiose.csproj` → **vert** (filet de compil).
4. `00_etat.md` : tronçon ③ fait, protocole 0.5.21, **points F5 pour Nico**
   (F4 : ms/tick baisse ; toggle debug : les semis sous-seuil se teintent).
5. Clôture sprint : maj DETTE (D67 → implémenté, gain + dérive + nouveaux hash) +
   BACKLOG + `journal.md` (entrée de clôture). Refactor auto-léger si un fichier
   a franchi la bande.
