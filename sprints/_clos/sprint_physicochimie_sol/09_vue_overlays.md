# Tronçon ⑨ — Vue Godot : overlays des nouveaux champs + indice visuel chlorose

> Sprint physico-chimie du sol. **Dernier tronçon (VUE, pas moteur).** Conception :
> `docs/champs/sol/conception_sol_{ph,nutriments_npk,structure}.md`. Kickoff
> **autosuffisant** (relançable à froid). C# depuis la racine repo ; build filet
> `dotnet build Symbiose.csproj` sur la VM (**F5 visuel = Nico**, Godot pas sur la VM).
> Tronçons ①→⑧ **moteur CLOS** : champs `ph`, `n`, `p`, `k`, `structure_sol` posés et
> couplés, golden figé `e209e8d854300aa8…`, pop `cd21704baa2e9f50…`.

## Objectif

Le moteur expose désormais **5 nouveaux champs** par plot (`ph`, `n`, `p`, `k`,
`structure_sol`) qui pilotent toute la chimie du sol. Côté vue ils traversent DÉJÀ
le pont (le serveur `cmd_fields` découvre les `GridField` d'`EcoFields` par
introspection — `tools/simserver/commands.py:129`) et s'affichent DÉJÀ en heatmap
debug F6, mais avec la **palette générique** bleu→rouge (`DefaultPalette`,
`visuals/FieldOverlay.cs:95`) : illisible, pas de libellés, pas de bornes physiques.

⑨ leur donne une **palette dédiée** (couleurs + libellés + bornes figées comparables
semaine à semaine, philo #5 : instrument de debug, jamais une règle) et ajoute un
**indice visuel diégétique de chlorose** sur la plante (jaunissement du feuillage)
— le seul effet ⑤ qui n'a PAS encore de traduction visuelle.

## Partie A — Palettes overlay (debug F6) · `visuals/FieldOverlay.cs`

Ajouter dans le dict `Palettes` (forme : `(Low, High, LowLabel, HighLabel, FixMin, FixMax)`,
NaN sur les bornes = repli auto min/max) :

```csharp
["ph"]            = (new Color("d83a3a"), new Color("9b59b6"), "acide", "alcalin", 4.0f, 8.5f),
["n"]             = (new Color("d8cfa8"), new Color("2f8f4f"), "pauvre", "riche N", 0f, 3f),
["p"]             = (new Color("d8cfa8"), new Color("8f6f2f"), "pauvre", "riche P", 0f, 3f),
["k"]             = (new Color("d8cfa8"), new Color("8f2f6f"), "pauvre", "riche K", 0f, 3f),
["structure_sol"] = (new Color("a8744a"), new Color("4f8f4f"), "compacté", "grumeleux", 0f, 1f),
```

Bornes : `ph` ∈ [4, 8.5] (héritage roche-mère 5.8→7.6 + dérive/amendements, cf.
`PH_PAR_SOL`/`AMEND_PUSH`) ; `n`/`p`/`k` `max_val=3.0` côté moteur (ex-`fertilite`,
`NUTRIENT_INIT_PAR_SOL`) ; `structure_sol` ∈ [0,1] (`GridField max_val=1.0`).
Choix de teintes = suggestion, à ajuster au F5 (rouge=acide est la convention papier pH).

**Ménage** : l'entrée `["fertilite"]` (`FieldOverlay.cs:57`) est **MORTE** — `fertilite`
a été supprimé net au tronçon ③ (loi de Liebig, remplacé par n/p/k). Le pont ne
l'expose plus → la supprimer du dict (sinon code mort qui ment sur le modèle).

## Partie B — Indice visuel chlorose (diégétique) · `visuals/PlantRenderer*.cs`

La **chlorose alcaline** (⑤) frappe une plante acidophile (`ph_opt < SEUIL_ACIDOPHILE`)
en sol trop alcalin (`ph_local > CHLOROSE_PH=7.6`) : malus de vigueur `CHLOROSE_MALUS`.
Aujourd'hui INVISIBLE. La rendre lisible par **jaunissement du feuillage** (philo #5 :
indice biologique, pas un chiffre).

**Décision à prendre à l'implémentation** (le moteur ne pousse pas encore de flag
chlorose dans le snapshot) :
- **Option 1 (sobre, recommandée)** : ajouter un champ au snapshot plante (ex.
  `chlorose: bool` ou un `health_tint ∈ [0,1]`) calculé côté Python dans
  `_snapshot()` (lit `eco.ph` + `ph_opt`/`ph_tol` de l'espèce, même prédicat que
  `vigueur_plante`). PlantRenderer lerp la couleur des feuilles vert→jaune selon ce
  signal. ⚠️ **un champ snapshot neuf = vérifier que le pont reste rétrocompatible**
  et que le golden moteur n'est PAS touché (le snapshot n'entre pas dans le hash, mais
  re-vérifier).
- **Option 2 (zéro moteur)** : Godot recalcule le prédicat côté C# à partir du champ
  `ph` (déjà disponible via overlay) + `ph_opt` de l'espèce (à exposer dans
  `PlantCatalogue.cs`). Plus de duplication de logique, mais aucun champ snapshot neuf.

Trancher avec Nico au lancement (pédagogie : exposer le compromis duplication-logique
vs champ-snapshot). **Défaut = Option 1** (source de vérité = moteur, cf. CLAUDE.md).

## Greffes (repères, à re-vérifier au grep)
1. `visuals/FieldOverlay.cs` — dict `Palettes` : +5 entrées, −1 (`fertilite`).
2. Légende overlay : `WorldView` lit `PaletteOf` pour afficher libellés/bornes —
   vérifier que les nouveaux libellés s'affichent (devrait être gratuit).
3. Indice chlorose : `_snapshot()` (`tools/simserver/`) si Option 1 ; `PlantRenderer`
   + `PlantRenderer.Organs.cs` pour le tint feuillage ; `PlantCatalogue.cs` si Option 2.

## À faire en fin de tronçon
- Palettes des 5 champs + suppression de `fertilite` mort.
- Indice chlorose (option tranchée avec Nico).
- `dotnet build Symbiose.csproj` PASS (filet compilation).
- **F5 par Nico** : overlay F6 cycle bien sur ph/n/p/k/structure_sol avec couleurs
  lisibles + légende ; une myrtille (acidophile) en sol alcalin jaunit visiblement.
- Golden moteur **INCHANGÉ** `e209e8d8…` (⑨ = vue, zéro moteur — si Option 1 ajoute
  un champ snapshot, re-confirmer que le hash ne bouge pas).
- MàJ `00_etat.md` (⑨ ✅) ; **SPRINT PHYSICO-CHIMIE DU SOL CLOS** → `journal.md`
  + déplacer le sprint sous `sprints/_clos/`.
- Commit : `feat(vue) : tronçon ⑨ overlays ph/npk/structure + indice chlorose`.
