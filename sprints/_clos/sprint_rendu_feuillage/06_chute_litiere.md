# ⑥ (T6) — Chute (abscission) + litière au sol (E5bis) — B + PONT

> Lis d'abord `docs/rendu/feuillage/conception_rendu_feuillage.md` **§6**. **Dernier tronçon
> du sprint.** Suppose la litière typée par espèce dans le snapshot (vérifier §6.4).

## But (E5bis, ajout Nico 2026-06-24)

Quand une feuille tombe, elle **casse au pétiole** et la **feuille tombée reste apparente
au sol** (litière). Pas d'animation de chute (sim par ticks) : la feuille **cesse d'être
peinte sur la plante** et **apparaît dans la litière au sol** de la même parcelle au tick
suivant. Continuité assurée par la **conservation de matière du moteur**, pas une
trajectoire.

## Travail

1. **Déclenchement (couche A, déjà émis, doc §6.1)** : le moteur fait déjà décroître le
   feuillage **et** alimente la litière de la parcelle (sprint Décompo & compost). Côté
   rendu : « feuille tombée » = feuillage baissé **et** litière montée. On **traduit**,
   on ne décide pas.
2. **Cassure au pétiole (couche B, doc §6.2)** : le pétiole vert (④) est le point de
   rupture ; une feuille qui disparaît ne laisse **pas** de moignon brun proéminent.
3. **Litière au sol (couche B procédurale, doc §6.3)** — semis déterministe de
   silhouettes de feuilles au sol, à la manière de `MacroLife`/`LitterLayer`
   (échantillonnage **stable par hash**, zéro `Random`) :
   - **Forme** : la même `LeafProfile` que l'espèce (②) — litière de pommier = feuilles
     de pommier. Repli `Elliptique` si l'origine n'est pas traçable.
   - **Couleur** : teinte **morte/sèche** (brun-roux désaturé) qui **dérive vers le sol**
     au fil de la décompo (le moteur connaît l'état de décompo → assombrir/désaturer
     progressivement jusqu'à fondre dans l'humus).
   - **Quantité** : nb de feuilles ∝ quantité de litière de la parcelle (**bornée**,
     comme la pop macro).
   - **Pose** : à plat, **volume aplati** (calotte réduite) mais reste **≥ 2 valeurs**
     (invariant §1).
4. **Pont (doc §6.4)** — **À VÉRIFIER D'ABORD** : la litière par parcelle (quantité +
   type/espèce + état de décompo) est-elle **déjà** dans le snapshot ? Inspecte
   `data/code/tools/simserver/serialize.py`.
   - **Si oui** → couche B pure, pas de re-bump.
   - **Si non/incomplet** (manque le type/espèce ou l'état décompo) → 2ᵉ entorse pont
     comme ⑤ : exposer la litière **typée par espèce** + état décompo au snapshot,
     **re-bump `ENGINE_VERSION`** (suite logique de ⑤). Donnée déjà calculée → simple
     **transport**, golden inchangé.

## Périmètre — NE PAS déborder

- Le rendu ne décide jamais d'une chute (c'est le moteur). Pont = **transport pur** →
  **golden inchangé** (toute dérive golden = régression à corriger).

## Vérification obligatoire avant de finir

- Golden `cd data/code && python3 -m tests.test_golden` → **INCHANGÉ**.
- Smoke pont (`tests/test_sim_server.py`) cohérent ; ajuster l'attendu version si bump.
- `dotnet build Symbiose.csproj` → **vert**.
- Maj `00_etat.md` (statut ⑥ + version pont finale + §REPRISE → **SPRINT CLOS**).
  **NE COMMIT PAS.** Rapport < 200 mots (dont : litière déjà au pont ou non + version finale).
- Point **F5** : feuilles mortes typées au sol par espèce, dérive vers l'humus avec la
  décompo, cassure nette au pétiole (pas de moignon brun).
