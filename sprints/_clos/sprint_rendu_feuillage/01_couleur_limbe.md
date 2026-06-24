# ① (T1) — Couleur du limbe par espèce (E3-couleur)

> Lis d'abord `docs/conception/CONCEPTION_RENDU_FEUILLAGE.md` **§3.1** (et §1 pour les
> invariants). Ce kickoff ne fait que cadrer l'exécution ; le doc est la source.

## But

La table `Palettes[species]` (dans `visuals/PlantRenderer.Palette.cs`) n'a aujourd'hui
que **2 entrées** (Tomato, AppleTree) + un défaut. **Étendre la table** aux espèces
**cultivées** du catalogue, chacune avec sa teinte de base verte d'espèce.

## Travail

- **Aucun mécanisme nouveau** — juste du **contenu** : ajouter des entrées `Palettes`.
- La teinte de base reste passée à `DrawVolumeEllipse`, qui applique déjà le volume
  2 valeurs (ombre froide / calotte sud) via `HueShift` (SS②) → **E4 garanti par
  construction**, ne rien casser de ce chemin.
- La modulation saisonnière (`LeafColor`, SS②) reste appliquée **par-dessus** la teinte
  d'espèce (vérifier que l'ordre est préservé : automne = jaune-roux **à partir de** la
  teinte d'espèce, pas d'un vert générique).
- Espèce non mappée → `DefaultPalette` (statu quo, jamais bloquant).
- Liste des espèces : les **cultivées** du catalogue (`core/PlantCatalogue.*.cs`,
  partial `.Cultivees`). Choisis une teinte plausible par espèce ; pas besoin de couvrir
  les 27 d'un coup, mais couvre au moins les cultivées principales. Espèces restantes →
  défaut, enrichies plus tard.

## Périmètre — NE PAS déborder

- Couche **B pure**, **zéro fichier Python**, **zéro pont**.
- Pas de forme (c'est ②), pas de nervure (③) — uniquement la **couleur du limbe**.

## Vérification obligatoire avant de finir

- Golden : `cd data/code && python3 -m tests.test_golden` → doit être **INCHANGÉ**
  (vue pure, aucun moteur touché). S'il bouge = régression à corriger (tu as touché
  autre chose), **pas** à figer.
- `dotnet build Symbiose.csproj` → **vert** attendu (sinon résous).
- Mets à jour `sprints/sprint_rendu_feuillage/00_etat.md` (statut ① + §REPRISE → ②).
- **NE COMMIT PAS.** Rapport < 200 mots (fait / golden inchangé / build vert / fichiers /
  points F5 / blocages).
