# ③ (T3) — Nervures = 3ᵉ valeur (E2)

> Lis d'abord `docs/rendu/feuillage/conception_rendu_feuillage.md` **§3.2** (et §1, §2 pour
> les archétypes). **Dépend de ② (T2)** : la topologie de nervure est fonction de
> l'archétype `LeafShape`. ② doit être clos avant.

## But

La nervure n'est **jamais** de la couleur du limbe (E2 explicite). On l'ajoute comme
**3ᵉ valeur** posée par-dessus le volume 2 valeurs (`visuals/PlantRenderer.Organs.cs`).

## Travail (règles déterministes, doc §3.2)

- **Teinte** : dérivée du limbe par un `HueShift` léger. **Sens du shift** (plus claire /
  plus sombre) = champ `LeafProfile.VeinLighter` (déclaré en ②). Constante `VeinShift`
  pour l'amplitude (ajustable F5).
- **Tracé** : fines lignes **1 px**, **jamais antialiasées** (cohérent pixel-art),
  posées **APRÈS** le volume → la nervure se lit par-dessus ombre+lumière.
- **Topologie par archétype** :
  - `Elliptique` / `Lanceolee` / `Cordee` → **penninerve** : 1 médiane + 2-4 latérales
    obliques (hash pour l'écartement, zéro `Random`).
  - `Lobee` → **palmée** : une nervure par lobe, rayonnant de la base.
  - `Composee` → une médiane par foliole.
  - `Aciculaire` → **aucune** (trop fin, illisible au pixel).
- **Plancher §1** : sous le rayon plancher, **pas de nervure** (feuille naissante =
  1 valeur nue) ; les nervures n'apparaissent qu'une fois la feuille assez grande
  (sert aussi la croissance progressive ⑤).

## Invariant servi

Avec la nervure, une feuille adulte porte **3 valeurs** (ombre / calotte / nervure) →
E4 doublement garanti. La mini-feuille (1 valeur) reste la seule exception, bornée
par le plancher.

## Périmètre — NE PAS déborder

- Couche **B pure**, zéro Python, zéro pont. Uniquement la **nervure** (réutilise les
  formes de ②).

## Vérification obligatoire avant de finir

- Golden `cd data/code && python3 -m tests.test_golden` → **INCHANGÉ**.
- `dotnet build Symbiose.csproj` → **vert**.
- Maj `00_etat.md` (statut ③ + §REPRISE → ④). **NE COMMIT PAS.** Rapport < 200 mots.
- Point **F5** : lisibilité des nervures 1 px (amplitude `VeinShift`) à valider par Nico.
