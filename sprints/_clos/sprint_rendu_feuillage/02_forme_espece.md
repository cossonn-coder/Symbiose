# ② (T2) — Forme de feuille par espèce (E3-forme)

> Lis d'abord `docs/conception/CONCEPTION_RENDU_FEUILLAGE.md` **§2** (et §1 invariants).
> Source de vérité du design. Ce kickoff cadre l'exécution.

## But

Aujourd'hui toute feuille est une **ellipse générique unique** (`DrawVolumeEllipse`,
`LeafSizeCm`, dans `visuals/PlantRenderer.Organs.cs`) — c'est le vrai trou de E3.
On le comble par un **catalogue fermé d'archétypes de silhouette**, choisi par espèce,
dessiné **directement en C#** (dérogation D10 actée ③, doc §1).

## Travail

1. **`enum LeafShape`** — 6 archétypes (doc §2.1) :
   `Elliptique` (défaut), `Lanceolee`, `Cordee`, `Lobee`, `Composee`, `Aciculaire`.
2. **`readonly record struct LeafProfile`** (doc §2.2) :
   `LeafShape Shape, float Aspect, int Count, bool VeinLighter`
   (`VeinLighter` sert ③ — le déclarer ici, ne pas l'exploiter encore).
3. **Table `LeafProfiles[species]`** en regard de `Palettes` (même fichier `.Palette.cs`
   ou un partial dédié, au choix cohérent). Mappage initial pour les espèces déjà
   peintes ; **défaut `Elliptique`** partout ailleurs (comme la palette, jamais bloquant).
4. **Tracé déterministe** (doc §2.3) — chaque archétype = **composition de primitives
   volumées**, chaque sous-élément passe par `DrawVolumeEllipse` (garde l'invariant
   2 valeurs §1) :
   - `Lobee`/`Composee` placent leurs N sous-ellipses par un **hash** du segment
     (jitter d'angle/longueur **stable**, philo #3 — zéro `Random`).
   - L'orientation générale suit l'axe du rameau porteur (placement existant `Organs.cs`).
   - **Plancher de rayon** (§1) : sous le seuil, on retombe sur **une seule ellipse
     1 valeur** quelle que soit la forme (mini-feuille naissante illisible en lobes).
5. **LOD / coût** (doc §2.3 encadré) : `Lobee`/`Composee` multiplient les `DrawEllipse`
   (3-5×). Prévoir un repli LOD : au **dézoom**, toute forme retombe sur `Elliptique`.

## Périmètre — NE PAS déborder

- Couche **B pure**, zéro Python, zéro pont. Uniquement la **forme** (pas la nervure ③,
  pas le pétiole ④).
- Catalogue **fermé** : 6 formes, pas d'explosion combinatoire.

## Vérification obligatoire avant de finir

- Golden `cd data/code && python3 -m tests.test_golden` → **INCHANGÉ**.
- `dotnet build Symbiose.csproj` → **vert**.
- Maj `00_etat.md` (statut ② + §REPRISE → ③). **NE COMMIT PAS.** Rapport < 200 mots.
- Signale en point **F5** : la lisibilité des silhouettes lobées/composées au pixel
  (à valider par Nico en vue).
