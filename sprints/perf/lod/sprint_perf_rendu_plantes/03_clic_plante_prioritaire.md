# Tronçon ③ — Priorité de clic plante > maison

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` +
> `docs/perf/lod/conception_perf_rendu_plantes.md` (§3.5). Indépendant des
> tronçons ①/② (picking, pas perf), mais après eux dans l'ordre. Rendu/vue **C#
> pur** : AUCUNE touche `data/code/`, **golden INTACT**. Filet :
> `dotnet build Symbiose.csproj`. Validation = **F5 Nico**.

## Problème

La maison a une silhouette écran **généreuse** (murs + toit + avant-toits,
`ClicSurMaison` dans `world/WorldView.Hub.cs`). Le routage du clic gauche la
teste AVANT toute plante (`world/WorldView.Controls.cs`, ~ligne 91) :
```csharp
if (ClicSurMaison(canvas)) OuvrirHubMaison();
else TryAction(canvas, mb.ShiftPressed);
```
→ une plante plantée **devant OU derrière** la maison voit son clic « volé » par
le hub. Nico veut : **cliquer sur une plante ne doit jamais ouvrir le hub**.

## Règle (conception §3.5)

Résoudre la plante **d'abord**. Le hub ne s'ouvre que si **aucune** plante n'est
sous le curseur :
```csharp
if (mb.ButtonIndex == MouseButton.Left)
{
    var canvas = WorldMouseCanvas();
    // Priorité de clic plante > maison : cliquer le corps visible d'une plante
    // exécute le geste, jamais le hub — même si la maison est devant/derrière.
    if (!PointeUnePlante(canvas) && ClicSurMaison(canvas))
        OuvrirHubMaison();
    else
        TryAction(canvas, mb.ShiftPressed);
}
```

## À faire

### A. `visuals/PlantRenderer.cs` — prédicat de containment par plante
Ajouter une méthode publique qui répond « le curseur touche-t-il le CORPS
VISIBLE de cette plante ? ». On teste la **silhouette de couronne projetée**
(l'ellipse de `DrawCanopySilhouette`) : forgiving, indépendante du zoom, = ce que
le joueur voit. En repère LOCAL (`Position` = collet), donc `ToLocal`.
```csharp
/// <summary>Le curseur (canvas) touche-t-il le corps visible de la plante ?
/// Test de l'ellipse de silhouette de couronne (même géométrie que
/// DrawCanopySilhouette) → forgiving, cohérent à tout zoom. Sert la priorité
/// de clic plante > maison (WorldView.PointeUnePlante).</summary>
public bool ContientCurseur(Vector2 canvasPos)
{
    if (_structure == null) return false;
    Vector2 local = ToLocal(canvasPos);
    (float wf, float hf, float yf) = SilhouetteShape(_silhouette);
    Vector2 center = Iso(0f, 0f, _structure.HeightCm * yf);
    float rx = _structure.CanopyRadiusCm * WorldView.PxPerCmX * wf;
    float ry = _structure.CanopyRadiusCm * WorldView.PxPerCmX * hf;
    if (rx <= 0f || ry <= 0f) return false;
    Vector2 d = local - center;
    return d.X * d.X / (rx * rx) + d.Y * d.Y / (ry * ry) <= 1f;  // dans l'ellipse
}
```
- `SilhouetteShape`, `Iso`, `_structure.CanopyRadiusCm`, `_structure.HeightCm`,
  `_silhouette` sont déjà présents dans `PlantRenderer` (utilisés par
  `DrawCanopySilhouette`) → réutilisation directe, aucune nouvelle géométrie.
- Un jeune semis a un rayon de couronne minuscule → cliquable seulement de près,
  acceptable (c'est le comportement du corps visible).

### B. `world/WorldView` — prédicat global
Ajouter dans **`world/WorldView.Controls.cs`** (le fichier du routage du clic —
`_plantNodes` est accessible depuis n'importe quel partial de `WorldView`).
⚠️ **NE PAS** le mettre dans `WorldView.Actions.cs` : ce fichier est déjà à
**468 LDC 🔴** (dette préexistante) — ne pas l'aggraver.
```csharp
/// <summary>Une plante est-elle sous le curseur (corps visible) ? Sert la
/// priorité de clic plante > maison. ~500 nœuds, balayage linéaire.</summary>
private bool PointeUnePlante(Vector2 canvasMouse)
{
    foreach (var node in _plantNodes.Values)
        if (IsInstanceValid(node) && node.Visible
            && node.ContientCurseur(canvasMouse))
            return true;
    return false;
}
```
- Le `node.Visible` respecte le culling du tronçon ② (une plante hors champ ne
  compte pas ; de toute façon elle n'est pas sous le curseur).

### C. `world/WorldView.Controls.cs` — ré-ordonnancement du routage
Remplacer les 2 lignes du clic gauche (~ligne 95) par le bloc de la §Règle
ci-dessus. **Ne rien changer d'autre** dans le handler (molette, phase…).

## Ce qu'il NE faut PAS faire

- Pas de `data/code/`, pas de pont, pas de Python, pas de test moteur.
- Ne PAS modifier `ClicSurMaison`, `OuvrirHubMaison`, ni `TryAction` : on ne
  change QUE l'ordre de résolution.
- Ne pas toucher au picking existant (`FindSegmentGlobal`, `FindPlant`,
  surbrillance de taille) : `ContientCurseur` est un test SÉPARÉ pour le routage.
- Ne PAS lancer `test_epaisseur_500ans` (interdit).

## Vérification / definition of done

- `dotnet build Symbiose.csproj` compile.
- Relire : le hub ne s'ouvre QUE si `!PointeUnePlante && ClicSurMaison` ; sinon
  `TryAction`. `ContientCurseur` teste bien l'ellipse en repère local.
- **Golden** : inchangé (rendu/UI pur).
- **F5 Nico** : planter une plante contre la maison (devant ET derrière) →
  cliquer la plante exécute le geste courant ; cliquer la maison hors de toute
  plante ouvre bien le hub (aucune régression du hub-maison).

## Golden attendu

**INCHANGÉ.** Sprint terminé après ce tronçon → mettre à jour `00_etat.md`
(§REPRISE : sprint clos, reste F5 Nico), `BACKLOG.md`, `journal.md`.
