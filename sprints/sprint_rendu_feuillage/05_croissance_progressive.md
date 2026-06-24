# ⑤ (T5) — Croissance progressive de la feuille (E1) — B + PONT

> Lis d'abord `docs/conception/CONCEPTION_RENDU_FEUILLAGE.md` **§4**. **Premier tronçon
> qui touche le pont.** Choix acté ①b : croissance ancrée sur l'**âge réel du segment**
> (`age_weeks`), pas un timer de vue.

## But

La feuille naît aujourd'hui à **pleine taille**. E1 veut une feuille qui **grandit sur
1 à 2 semaines**, dérivée de l'âge du segment porteur.

## Travail — pont (couche A → snapshot, doc §4.1)

`Segment` (miroir C# `core/PlantStructure.cs`) **omet** `age_weeks`. L'exposer :
- **Python** : ajouter `age_weeks` du segment au snapshot de structure
  (`data/code/tools/simserver/serialize.py` — c'est de la donnée **déjà calculée** par
  la morphogénèse, on ne fait que la **transporter**, aucun calcul moteur nouveau).
- **C#** : champ ajouté au `record struct Segment` + lecture dans `FromSnapshot`
  (`core/PlantStructure.cs`).
- **Re-bump `ENGINE_VERSION`** (`tools/simserver/version.py`, actuellement **0.5.4** →
  **0.5.5**). ⚠️ **⑥ partage ce geste pont** : si tu pressens faire ⑥ dans la foulée,
  un **seul** saut de version suffit — mais ⑤ et ⑥ étant des tronçons séparés ici,
  bumpe à 0.5.5 pour ⑤ et laisse ⑥ bumper à 0.5.6 (ou regrouper si évident — note ton
  choix dans le rapport).

## Travail — facteur de croissance (couche B, doc §4.2)

```
leafGrowth = clamp(seg.AgeWeeks / LeafMaturityWeeks, 0, 1)   // LeafMaturityWeeks ≈ 1.5
```
- **Multiplie le rayon** du volume de la feuille (`LeafSizeCm * leafGrowth`).
- **Synergie plancher §1** : à l'émergence (`age ≈ 0`) le rayon est sous le plancher →
  1 valeur nue, pas de nervure ; en grandissant il franchit le plancher → volume 2
  valeurs puis nervures (③). La feuille se **construit visuellement**, gratuitement.
- **Pas de pop-in** (doc §4.3) : segments déjà mûrs au chargement (`age ≥ maturity`) →
  `leafGrowth = 1`, feuilles pleines immédiatement. Seules les feuilles **réellement
  jeunes** sont vues en croissance.
- Optionnel : légère courbe ease-out (constante, F5).

## Périmètre — NE PAS déborder

- Le pont ne fait que **transporter** `age_weeks` → **golden inchangé**. Si le golden
  bouge, tu as introduit un calcul moteur = **régression à corriger, pas à figer**.
- Pas la chute (⑥).

## Vérification obligatoire avant de finir

- Golden `cd data/code && python3 -m tests.test_golden` → **INCHANGÉ** (transport pur).
- Smoke pont si présent (`tests/test_sim_server.py`) → doit rester cohérent ;
  bumper l'attendu de version si le test vérifie `ENGINE_VERSION`.
- `dotnet build Symbiose.csproj` → **vert**.
- Maj `00_etat.md` (statut ⑤ + nouveau `ENGINE_VERSION` + §REPRISE → ⑥). **NE COMMIT PAS.**
  Rapport < 200 mots (dont : version pont, golden inchangé confirmé).
- Point **F5** : la jeune feuille grandit visiblement sur ~1-2 sem sans pop-in.
