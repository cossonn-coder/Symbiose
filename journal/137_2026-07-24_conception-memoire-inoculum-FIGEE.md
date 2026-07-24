# 2026-07-24 — Conception MÉMOIRE D'INOCULUM DU SOL (D10) — FIGÉE

`/conception D10`. Point de départ : la dette D10 (« réconcilier `PathogenPressure`
C#→Python »).

## Diagnostic — D10 caduque dans sa lettre
Lecture du code : le `EcoFields` C# (`PathogenPressure`, `TickPathogen`,
`EvaluateIndicators`) est du **code MORT** — rien de vivant ne l'appelle (Option B :
Godot est une vue nourrie par le pont Python ; le portage intégral C# a été purgé
au SS⑦). Le modèle de maladie **Python** est déjà PLUS riche par plante
(`fungal_disease` humidité × densité même-famille × susceptibilité familiale × gène
`resistance_pathogene` × vent séchant/dispersant, `infection_memory` SAR par plante,
`damping_off`). **Unique écart de fond** : `disease_probability` Python n'a pas le
terme d'inoculum accumulé du C# (`base × (1 + PathogenPressure×0.5) × (1−protection)`
vs `base × (1−protection)`).

D10 se scinde donc en **ménage** (supprimer le scalaire C# mort) + **idée
écologique**. Nico a tranché : **concevoir la mémoire d'inoculum**.

## Le trou que ça comble
`infection_memory` meurt AVEC la plante → une tuile ayant porté une monoculture
malade repart **vierge**. Faux pour les pathogènes sol/résidus (mildiou hivernant,
verticillium, fonte) et prive le jeu de la **pédagogie de rotation** (philo #2/#6).

## Décisions figées
- **Champ `InoculumField`** sparse **indexé par famille** (rotation émergente : le
  bucket d'une famille absente décroît → tourner de famille échappe à la charge).
- **Alimentation = CONSÉQUENCE** : dépôt continu ∝ `infection_memory` des plantes
  infectées + pulse de résidu à la mort. PAS de re-dérivation humidité×mono (évite
  le double-comptage avec la densité même-famille de `fungal_disease`).
- **Suppression** = décroissance passive (demi-vie ~2 saisons, hiverne) + microbiome
  (sols suppressifs). PAS de bêchage-réducteur (anti « biner pour guérir »).
- **Greffe UNIQUE** = `disease_probability(r,c,base,family=None)` : `×(1+INOC_GAIN·
  load[family])` si family passée (fungal/damping/mildiou) ; **SAR reste family=None**
  → casse la boucle de rétroaction inoculum→SAR→infection_memory→inoculum (anti-runaway).
- **Molène** (*Verbascum*, Scrophulariaceae) ravivée avec ses **5 voix**, apparition
  via facteur de niche `arch_inoculum` (patron `arch_ph`/`arch_temp` de
  `germinate_candidates`, porte de RELÂCHE : ~0 sain, ~1 sol vicié).

## Tronçonnage (4, vue en dernier)
① champ + alimentation + décroissance DORMANT [golden INTACT] → ② couplage
`disease_probability(family)` [golden RE-FIGÉ maîtrisé annoncé, contrôle
`INOC_GAIN=0 ⇒ ancien hash`] → ③ molène + `arch_inoculum` + 5 voix [NEUTRE visé]
→ ④ ménage C# (`PathogenPressure` mort supprimé) + vue Godot (snapshot inoculum +
heatmap F6 + banc F5 `rotation_inoculum`) [INTACT]. Le ④ clôt la lettre de D10.

Doc : `docs/champs/sol/conception_memoire_inoculum.md`. Sprint :
`sprints/champs/sol/sprint_memoire_inoculum/` (00_etat + 01→04). DETTE D10 mise à
jour (conçu, prêt). **Prêt pour `/sprint-auto sprint_memoire_inoculum`.**
