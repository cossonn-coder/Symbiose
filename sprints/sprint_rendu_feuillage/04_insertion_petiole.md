# ④ (T4) — Insertion sur rameau vert + pétiole (E5)

> Lis d'abord `docs/conception/CONCEPTION_RENDU_FEUILLAGE.md` **§5**. C'est l'exigence
> la plus proche de l'acquis : on **verrouille** plutôt qu'on ne construit. Indépendant
> de ②/③ (peut suivre ③ dans l'ordre).

## Acquis (déjà en place, doc §5.1)

- Placement des feuilles déjà ancré aux segments « feuillus » :
  `IsLeafy(s) = s.IsApex || s.ThicknessCm ≤ LeafMaxThickCm` (`Organs.cs`).
- Un segment fin/jeune a une lignification faible → `WoodRamp` le rend en **vert tendre**
  → le rameau porteur d'une feuille **est déjà vert** par construction. E5 cohérent.

## Travail

1. **Verrou (invariant explicite, doc §5.2)** : ériger en règle « **feuille ⟹ segment
   rendu vert** ». Garder `LeafMaxThickCm` **cohérent** avec le point de bascule
   vert→olive de la rampe (`LignifyFullCm`). Si un segment feuillu pouvait devenir
   non-vert, ce serait un bug — documenter/garantir la cohérence des deux seuils.
2. **Pétiole vert (renfort lisibilité, doc §5.3)** : court pétiole de **1-2 px** reliant
   le point d'insertion au limbe :
   - couleur = teinte **verte du rameau local** (rampe au point d'insertion), **jamais
     brune** — réaffirme E5 ;
   - orientation = celle déjà calculée (`LeafOffsetCm`, axe rameau → extérieur) ;
   - soumis au facteur de croissance (le pétiole s'allonge avec la feuille — le facteur
     `leafGrowth` arrive en ⑤ ; ici, prévoir le branchement, ou pétiole pleine taille
     en attendant ⑤ selon ce qui reste cohérent) ;
   - c'est le **point de rupture** de l'abscission (servira ⑥).

## Périmètre — NE PAS déborder

- Couche **B pure**, zéro Python, zéro pont. Ni croissance (⑤), ni chute (⑥).

## Vérification obligatoire avant de finir

- Golden `cd data/code && python3 -m tests.test_golden` → **INCHANGÉ**.
- `dotnet build Symbiose.csproj` → **vert**.
- Maj `00_etat.md` (statut ④ + §REPRISE → ⑤). **NE COMMIT PAS.** Rapport < 200 mots.
- Point **F5** : le pétiole vert rend bien l'émergence (pas de feuille « posée dans le
  vide ») — à valider par Nico.
