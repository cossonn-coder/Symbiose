# Sprint GESTES LISIBLES — état

> Conception figée le 2026-11-13 : `docs/joueur/gestes/conception_gestes_lisibles.md`
> (à lire en entier). Reprend **D136 (a)-(f)**. Hors sprint : (g) structures en volume,
> (h) paysage (après la rivière), outils à trouver/fabriquer (`sprint_outils_atelier`),
> automate à intentions (`sprint_automate_intention`), devenir des fruits (D137), autres
> états du sol (D108).

## But
L'outil bouge (curseur, images précuites), le jardin se souvient (sol-canvas : traces de
gestes + pluie + sécheresse), les messages parlent en mots, aucun geste n'est incompris,
et l'automate joue un plan de test sous nos yeux.

## Décisions clés (Nico, 2026-11-13)
- D1 Curseur = l'outil qui agit, images précuites qui décomposent le geste ; monde = la
  conséquence. D2/D8 Sol = canvas (gestes + événements), ce sprint pose le canvas + traces
  de gestes + pluie + sécheresse ; D108 remplira le reste.
- D3 Registre `traces_sol` côté MOTEUR (état joueur, hors tick) : **la vue n'invente rien**.
- D5 Quantités rééquilibrées **à l'excès** pour tester ; aucun chiffre dans les messages.
- Q8 **On ne touche à rien des outils** (arrosoir, sécateur, Atelier) avant leur sprint ;
  `arroser` reste de base.
- D7/D10 Automate : actif fenêtre fermée + mode testeur (plan `(verbe, cible)` déroulé
  par le chemin du clic joueur). L'« âme » de l'automate = sprint à part.
- Décidé seul, à confirmer au F5 : déraciné = cadavre `couchee` au moteur ; volants
  épargnés par `ecraser` via un attribut `vole` ; gestes de l'automate joués en sprite
  monde avec les images du curseur.

## Golden
**INTACT sur tout le sprint** (`b4a921f8…`, `data/code/tests/golden_hash.txt`). Aucun
re-figeage prévu : un rééquilibrage qui le bougerait passe par une constante côté geste.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_moteur_pont.md` — traces, volants, couché, pot, mots, rééquilibrage, pont 0.6.14 | à faire |
| ② | `02_animations_curseur.md` — images précuites, rotation, icônes inversées | à faire |
| ③ | `03_sol_canvas.md` — couche de traces, paillis, cuvette, pile, pluie, craquelé | à faire (après ①) |
| ④ | `04_objet_en_main_ergonomie.md` — objet en main, coccinelle, catalogue, fruit | à faire |
| ⑤ | `05_automate.md` — actif fenêtre fermée, gestes visibles, mode testeur | à faire (après ②) |
| ⑥ | `06_banc_recette.md` — banc `gestes_lisibles`, oracle, recette F5, clôture | à faire (après tous) |

## Interdits communs
Jamais `tests/test_epaisseur_500ans` ; pas de `ps aux` / `pgrep -f` ; GDScript interdit ;
aucune couleur brute (`Palette16`) ; ne supprimer aucun code ; > 300 LDC → scinder
(`tools/compte_ldc.py`) ; `WorldView.cs` est à 300 LDC, n'y rien ajouter ; regarder les
PNG de capture avant de conclure un tronçon de vue.

## Constats d'exécution
(à remplir par chaque tronçon)

## §REPRISE
Conception figée, aucun tronçon lancé. Prochaine étape : `/sprint-auto sprint_gestes_lisibles`.
