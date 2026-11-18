# ⑥ Vue Godot + banc `plante_vivante` + clôture (golden INTACT)

Lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/vegetal/sante/conception_plante_vivante.md`
§3-§5 et §9 (philo #5 : pas de jauge).

## Objectif
Rendre le bilan **visible sans chiffres** : une plante défeuillée paraît
défeuillée, une plante à bout de réserves paraît épuisée, l'info-bulle le dit en
mots, et un banc F5 met côte à côte les cas.

## À faire
1. Pont (`data/code/tools/simserver/serialize.py`, sites qui exportent déjà
   `vitalite` ~l. 217 et ~l. 644) : exporter `feuillage` et `reserves` (arrondis à
   3 décimales) par plante ; bump `ENGINE_VERSION` (`tools/simserver/version.py`,
   0.6.20 au départ du sprint → mineur suivant) ; adapter `tests/simserver/`.
   Le golden ne voit pas le pont : comparer le snapshot JSON avant/après (mémoire
   « refactor du pont : golden aveugle »).
2. C# : `core/PlanteLue.cs` lit les deux clés ; `visuals/PlantRenderer.cs`
   (+ partials) : la **densité de feuillage** dessinée suit `feuillage` (moins de
   feuilles, pas une teinte de « dégât ») ; `reserves` basses → posture/teinte
   d'épuisement via le canal existant de vitalité (ne pas créer de jauge).
   `world/WorldView.InfoBulle.cs` / `world/DossierPlantePanel.cs` : phrases
   diégétiques (« broutée par les limaces », « à bout de forces », « refait ses
   feuilles ») — au 1ᵉʳ niveau d'info-bulle, sans chiffres hors mode debug.
   Noms d'espèces en français (D141, mémoire `feedback_noms_francais`).
3. Banc `data/code/bancs/plante_vivante.py` (enregistré comme les autres bancs,
   `bancs/__init__.py`) : côte à côte un semis et un chêne sous les mêmes limaces,
   une plante à l'ombre dense qui s'affame, une laitue rongée qui refait ses
   feuilles, un arbre mort et ses rejets.
4. `dotnet build Symbiose.csproj` vert ; capture VM si le banc capture existe
   (mémoire `project_rendu_pixelart`), sinon F5 à Nico.
5. Clôture : `00_etat.md` (recette F5 pour Nico), `DETTE.md` D140 (G) → « sprint A
   clos côté code, F5 attendu, sprint B prêt », `BACKLOG.md`, `journal.md` (+ entrée
   `journal/`), puis indiquer la reprise de `sprint_depart_jardin` ④.

## Golden
**INTACT** (vue + pont uniquement).

## Ne PAS faire
- Afficher des nombres de réserves ou de feuillage hors mode debug (philo #5).
- GDScript (interdit).
