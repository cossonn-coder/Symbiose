# SPRINT RENDU FEUILLAGE — état partagé

> Conception figée : `docs/conception/CONCEPTION_RENDU_FEUILLAGE.md`.
> Lancement Python depuis `data/code/`. Build C# : `dotnet build Symbiose.csproj`
> (filet de compilation ; F5 visuel = Nico).

## Objectif

Combler les trous du **rendu des feuilles** par espèce (forme, couleur, nervures,
croissance, insertion, chute) dans la continuité du pixel-art 16-bit (SS④). Couche
**B** (`visuals/PlantRenderer.*`) sauf T5/T6 qui *transportent* une donnée déjà
calculée par le moteur via le pont. **Rendu = vue passive → golden trivialement
préservé sur TOUS les tronçons** (T5/T6 inclus : transport, pas calcul).

## Périmètre — 6 exigences Nico (cf. doc §Périmètre)

- **E1** croissance progressive des feuilles (1-2 sem) · **E2** nervures couleur ≠ limbe ·
  **E3** forme **et** couleur par espèce · **E4** jamais d'aplat (≥ 2 valeurs) ·
  **E5** feuille émerge d'une branche verte (+ **E5bis** chute au pétiole, reste au sol) ·
  **E6** vrilles grimpantes → **DIFFÉRÉ, gated dette D49** (hors sprint).

## Verrous tranchés (Nico, 2026-06-24)

- **①b** croissance ancrée sur l'**âge réel du segment** (`age_weeks`), exposé au pont.
- **②b** mécanique de grimpe des vrilles = sprint moteur séparé (**D49**), hors ce sprint
  (seul le contrat de rendu est pré-cadré, §7 du doc).
- **③** forme de feuille codée **directement en C#** (dérogation assumée à D10).

## Invariants transverses (vérifiés à CHAQUE tronçon, doc §1/§8)

1. **Jamais d'aplat (E4)** : tout organe ≥ 2 valeurs (`DrawVolumeEllipse`), sauf
   mini-feuille naissante sous le **plancher de rayon** (~2-3 px, exception transitoire).
2. **Déterminisme total** : zéro `Random`, toute variation dérive d'un **hash** stable
   de l'identité du segment/organe (philo #3, condition du golden).
3. **Le bois n'est jamais teinté par le feuillage** : `WoodRamp` reste maîtresse du rendu
   des segments ; une feuille colore le limbe, pas le rameau.

## Tronçons (doc §8 — couche B pure d'abord, pont ensuite)

| # | Tronçon | § doc | Couche | Pont | Exigence | Golden | Statut |
|---|---------|-------|--------|------|----------|--------|--------|
| ① (T1) | Couleur du limbe par espèce — étendre la table `Palettes` aux cultivées | §3.1 | B pure | — | E3-couleur | NEUTRE | ⏳ |
| ② (T2) | Forme par espèce — `enum LeafShape`, `LeafProfile`, tracé des 6 archétypes (jitter par hash) | §2 | B pure | — | E3-forme | NEUTRE | ⏳ |
| ③ (T3) | Nervures = 3ᵉ valeur — topologie par archétype, sens du shift par espèce | §3.2 | B pure | — | E2 | NEUTRE | ⏳ |
| ④ (T4) | Insertion — verrou « feuille ⟹ vert » + pétiole vert | §5 | B pure | — | E5 | NEUTRE | ⏳ |
| ⑤ (T5) | Croissance progressive — `age_weeks` au segment (pont), facteur `leafGrowth` | §4 | B + pont | `ENGINE_VERSION`↑ | E1 | NEUTRE (transport) | ⏳ |
| ⑥ (T6) | Chute + litière — abscission au pétiole, semis de litière typée au sol | §6 | B + pont | `ENGINE_VERSION`↑ | E5bis | NEUTRE (transport) | ⏳ |

**Dépendances** : ③ dépend de ② (topologie de nervure ∝ archétype). ⑤ et ⑥ partagent
le geste « champ au snapshot + re-bump » → **regrouper le re-bump** (un seul saut de
version si faits dans la foulée). ①, ②, ④ indépendants.

**Contrat pont au départ** : `ENGINE_VERSION = "0.5.4"`. ⑤/⑥ le bumpent.

## §REPRISE

**Rien de fait.** Prochain tronçon = **① (T1)** — `sprints/sprint_rendu_feuillage/01_couleur_limbe.md`.
