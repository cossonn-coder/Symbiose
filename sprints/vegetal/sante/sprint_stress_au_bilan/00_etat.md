# Sprint STRESS AU BILAN (D140 G, sprint B) — état

> Conception FIGÉE le 2026-11-18 : `docs/vegetal/sante/conception_plante_vivante.md`
> (§4-§5). **Prérequis : `sprints/vegetal/sante/sprint_plante_vivante/` (A) CLOS** —
> ce sprint suppose le bilan carbone, `feuillage`, `reserves`, `vitalite` dérivée et
> l'adaptateur `erode` = perte de tissus en place. Lire l'`00_etat.md` du sprint A
> (acquis, noms réels des fonctions et constantes) AVANT tout tronçon.

## But
Remplacer l'adaptateur universel du sprint A par le **vrai mécanisme de chaque
stress** : ce qu'il retire (feuilles, sucres, eau, racines, vaisseaux, bourgeons).

## Décisions clés (Nico, 2026-11-18)
- Tout le vivant végétal passe au bilan ; plus de mort au sort.
- Causes de mort : famine, destruction, défaillance hydraulique, racines perdues,
  fin de cycle, vieillesse. Code supplanté commenté et conservé, jamais supprimé.

## Golden
Départ = golden final du sprint A. ①②③④ **RE-FIGÉ annoncé** chacun (dérive
prouvée localisée par neutralisation du seul mécanisme du tronçon) · ⑤ **INTACT**.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_secheresse_embolie.md` — stomates + défaillance hydraulique | à faire |
| ② | `02_froid_gel_brulure.md` — feuilles détruites vs bourgeons/sève gelés | à faire |
| ③ | `03_maladies_racines.md` — mildiou, oïdium, fonte, asphyxie, pourriture, campagnol | à faire |
| ④ | `04_vieillesse_cycle_mycorhize.md` — vieillesse, fin de cycle, paiement fongique | à faire |
| ⑤ | `05_vue.md` — signes, info-bulle, banc, clôture D140 G | à faire |

## Contrôle commun à chaque tronçon
Critères d'ouverture du sprint A toujours tenus (`tests/test_ouverture_vivante.py`) ;
perf tick `full` ≤ +10 % ; suites `tests/` vertes ; jamais `test_epaisseur_500ans`.

## REPRISE
Lire `CLAUDE.md`, ce fichier, l'`00_etat.md` du sprint A, la conception, puis le
kickoff du premier tronçon « à faire ». Lancer : `/sprint-auto sprint_stress_au_bilan`.
