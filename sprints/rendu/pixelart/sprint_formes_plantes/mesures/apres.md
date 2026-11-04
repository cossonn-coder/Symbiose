# Mesures APRÈS — sprint FORMES DES PLANTES ⑥

En regard de `avant.md`. Rejouer : mêmes commandes. PNG non committés.

## Bilan chiffré

| | Avant | Après | Cible |
|---|---|---|---|
| Paires confondues ×4 | 28 [seed 42, n=1 capture, VM] | **0** [seed 42, n=1 capture, VM] | 0 : tenue |
| Paires confondues ×1 | 14 [seed 42, n=1 capture, VM] | **1**, fraisier / violette [seed 42, n=1 capture, VM] | ≤ 3 : tenue |
| Hauteur hors tolérance ×4 | 30 sur 40 [seed 42, n=1 capture, VM] | **9 sur 40** [seed 42, n=1 capture, VM] | aucune chiffrée |
| Hauteur hors tolérance ×1 | 28 sur 40 [seed 42, n=1 capture, VM] | **10 sur 40** [seed 42, n=1 capture, VM] | aucune chiffrée |

**Ce qui reste hors tolérance, sans arrondir.** Masses plus larges que hautes, la boîte compte l'emprise au sol (consoude, courgette, fraisier, lavande, myrtille, sphaigne, thym, violette, selon le palier). Dactyle : validé au F5 (D126). **Haricot** : 50 cm dessinés pour 200 [×4, n=1 capture], volontaire : le banc n'a pas de support, c'est le tas de la fiche. La hauteur du haricot accroché n'est pas dans cette mesure, vue seulement au banc `accroches_adultes`. Moutarde et poivron à ×1 : 1 à 2 cm d'arrondi au pixel (bilan ③).

## Perf : avant sprint (`3aa436b`) contre après ⑥, même machine, en alternance

`tools/perf_vm.sh -E 20 -z 4 --no-build`, `full`, 3 runs par côté, charge de départ 3,9 à 8,3 (un autre processus tourne sur la VM).

| | Avant | Après |
|---|---|---|
| FPS | 11,4 ; 10,7 ; 9,2 [n=3 runs, VM chargée] | 9,7 ; 10,7 ; 10,9 [n=3 runs, VM chargée, dans le bruit] |
| Image médiane (ms) | 86,3 ; 92,8 ; 106,2 [n=3 runs] | 93,7 ; 91,4 ; 90,4 [n=3 runs] |
| Draw calls | 98 ; 104 ; 90 [n=3 runs] | 81 ; 82 ; 82 [n=3 runs] |
| Pinceau, ms/plante | 0,12 [n=1 run] | 0,24 [n=1 run, charge 7] |
| Cache, pages | 93,4 Mo, 5 [n=1 run, lu en début de run] | 77,4 Mo, 4 [n=1 run, lu en début de run] |

**Garde-fou de cuisson NON TENU**, seuil non modifié, à arbitrer par Nico : pinceau de +60 % au ③ [n=3 runs par côté en alternance, charge de départ 1,8 à 4,9], ×2 sur ce seul couple [n=1 run par côté, charge 7]. Le reste ne se dégrade pas. **Haricot, feuilles et fleurs des paliers ×16 et ×32 ne sont pas couverts par ce banc** (`-z 4`) : coût à ×32 non mesuré, D118 (D).

## `mesure_da`, ×4, banc `planche_especes`, `t.png --ref r.png`

| | tons lus méd. [n=1 capture, VM, plusieurs sprites par image] | noir [idem] | dérive méd. [idem] |
|---|---|---|---|
| Haricot (tas) | 3 | 0 % | 8,0° |
| Tomate | 4 | 0 % | 10,4° |
| Lierre | 4 | 0 % | 6,1° |
| Jasmin | 4 | 0 % | 22,5° |

## Effet en jeu

`mesures/effet_ports.py`, `full`, seed 42, sans automate [n=1 run, VM]. Fin d'an 2 : 627 pieds, 21 espèces. **16 espèces sur 21 passent par un port** (12 à fiche, 4 de prairie, soit 621 pieds sur 627) ; 5 arbres, 6 pieds. Aucune liane vivante à cette date : la tomate meurt avant (1 pied en fin d'an 1, 0 après), lierre et jasmin absents de `full`. Le haricot y vit, mais **aucun haricot accroché vu** dans `full`, ses spires ne sont vues qu'au banc.

## Lecture des PNG, ce qui reste faible

`full`, seed 42, centre (1625, 125), 20 captures s9, s20, s34, s45 à ×1 à ×32 [n=1 run par capture, VM, palette `-F`]. Lues : s20 ×1, ×8, ×32 ; s34 ×4 ; s45 ×4 ; s9 ×16. Les 14 autres non lues une à une.

- **Tuile à ×4 où on les distingue** : s34 ×4. Tomate à fruits rouges et tournesol se nomment d'un coup d'œil ; les ports diffèrent nettement entre eux, mais je ne nomme pas les autres pieds sans info-bulle (basilic, haricot, minette, achillée sont présents dans ce coin à cette date, attribution à l'image non vérifiée).
- **Arbres à ×4 et ×8 : encore des masses ovales en pompon sur rameaux verts**, ils dominent l'image. Le sprint ne les touche pas, mais l'œil voit d'abord ça.
- **Disques verts translucides au sol** à ×8 et ×16 (« clones », D118) : toujours là, origine non vérifiée.
- **×32 dans `full` : le cadre tombe sur le sol nu**, aucune plante à s20 ; feuilles ×32 lues seulement sur le verger (limbe à motifs, nervures fines) et le haricot du banc (moitié d'ombre, nervures). Une moitié de limbe reste presque unie à ×32.
- **Hiver** s45 : tournesol et autres tiges restent feuillus, faute de signal moteur (bilan ③).
- **Fleurs d'arbre** : plus petites qu'avant, 3 cm au lieu de 20 ; un arbre fleuri se remarque moins à ×8, à juger au F5. Seul le pommier jeune est lu ; chatons écrits, jamais vus en capture.
- **Jasmin sur treillis** : reste au sol sur le banc, l'accroche y est posée après la pousse ; palissage réel non vu.

Silhouettes et perf mesurées avant le dernier réglage (nervures tenues dans le limbe), qui n'agit que dès ×16.

## Descripteurs


## Palier ×1

| espèce | boîte l×h px [seed 42, n=1 capture, VM, ×1] | hauteur dessinée cm [seed 42, n=1 capture, VM, ×1] | height_cm | dessinée / height_cm [seed 42, n=1 capture, VM, ×1] | couleur moyenne [seed 42, n=1 capture, VM, ×1] |
| --- | --- | --- | --- | --- | --- |
| achillee | 10×19 | 49 | 40 | 1.22 | #85a37f |
| ail | 10×21 | 54 | 50 | 1.08 | #62a470 |
| armoise | 17×43 | 110 | 110 | 1.00 | #706254 |
| bambou | 31×98 | 251 | 250 | 1.01 | #8bad53 |
| basilic | 14×20 | 51 | 40 | 1.28 | #68ac5d |
| ble | 16×40 | 103 | 100 | 1.03 | #bbac4e |
| bourrache | 24×32 | 82 | 70 | 1.17 | #5d8f6c |
| bourse_pasteur | 8×18 | 46 | 40 | 1.15 | #8ba465 |
| carotte | 7×26 | 67 | 60 | 1.11 | #6faf71 |
| chanvre | 18×118 | 303 | 300 | 1.01 | #4e8242 |
| consoude | 31×30 | 77 | 50 | 1.54 | #5a874d |
| courgette | 54×31 | 79 | 45 | 1.77 | #2d783a |
| dactyle | 29×33 | 85 | 90 | 0.94 | #528f5c |
| drosera | 6×7 | 18 | 10 | 1.79 | #a99480 |
| fetuque | 13×14 | 36 | 25 | 1.44 | #5d9561 |
| fraisier | 14×12 | 31 | 15 | 2.05 | #536842 |
| framboisier | 29×64 | 164 | 150 | 1.09 | #6b613d |
| haricot | 24×20 | 51 | 200 | 0.26 | #70b75e |
| jasmin | 21×16 | 41 | 43 | 0.97 | #79ae7a |
| lavande | 38×34 | 87 | 50 | 1.74 | #6b7d6b |
| lierre | 35×14 | 36 | 42 | 0.85 | #366739 |
| mache | 6×10 | 26 | 18 | 1.42 | #89c28d |
| menthe | 14×16 | 41 | 30 | 1.37 | #5a746f |
| minette | 21×11 | 28 | 30 | 0.94 | #9ab748 |
| molene | 26×66 | 169 | 160 | 1.06 | #9da883 |
| moutarde | 20×30 | 77 | 60 | 1.28 | #aac455 |
| myrtille | 21×21 | 54 | 40 | 1.35 | #92ab85 |
| ortie | 22×35 | 90 | 90 | 1.00 | #4e7942 |
| paturin | 11×13 | 33 | 30 | 1.11 | #99bd77 |
| phacelie | 28×34 | 87 | 80 | 1.09 | #7a9785 |
| pissenlit | 19×15 | 38 | 30 | 1.28 | #519230 |
| plantain | 12×8 | 21 | 25 | 0.82 | #326c36 |
| poivron | 30×38 | 97 | 80 | 1.22 | #559047 |
| seigle | 20×70 | 179 | 160 | 1.12 | #b3a462 |
| sphaigne | 23×14 | 36 | 6 | 5.98 | #8fbd75 |
| thym | 22×18 | 46 | 25 | 1.85 | #5f7655 |
| tomate | 19×37 | 95 | 84 | 1.12 | #4b973f |
| tournesol | 27×101 | 259 | 250 | 1.04 | #588737 |
| trefle | 21×11 | 28 | 15 | 1.88 | #2b8d40 |
| violette | 13×11 | 28 | 12 | 2.35 | #4e7b57 |

**Hauteur hors tolérance [seed 42, n=1 capture, VM, ×1] : 10 sur 40** (consoude, courgette, fraisier, haricot, lavande, moutarde, poivron, sphaigne, thym, violette).

**Paires confondues [seed 42, n=1 capture, VM, ×1] : 1 sur 780.** Seuils : gabarit ≤ 0.15, proportions ≤ 0.15, recouvrement > 0.7, ΔE < 0.05. Espèces dans au moins une paire : 2.

Paires passant chaque critère seul [seed 42, n=1 capture, VM, ×1] : gabarit 24, proportions 104, recouvrement 16, ΔE 94.

| paire | gabarit [seed 42, n=1 capture, VM, ×1] | proportions | recouvrement | ΔE | confondue |
| --- | --- | --- | --- | --- | --- |
| fraisier / violette | 0.08 | 0.01 | 0.72 | 0.048 | oui |
| armoise / ortie | 0.23 | 0.37 | 0.77 | 0.092 | non |
| haricot / trefle | 0.45 | 0.37 | 0.75 | 0.145 | non |
| bourrache / fetuque | 0.56 | 0.19 | 0.74 | 0.029 | non |
| bambou / framboisier | 0.35 | 0.30 | 0.74 | 0.215 | non |
| courgette / thym | 0.59 | 0.30 | 0.73 | 0.065 | non |
| courgette / trefle | 0.65 | 0.09 | 0.73 | 0.068 | non |
| sphaigne / thym | 0.22 | 0.26 | 0.71 | 0.215 | non |
| fetuque / trefle | 0.38 | 0.51 | 0.71 | 0.064 | non |
| sphaigne / trefle | 0.21 | 0.14 | 0.71 | 0.180 | non |
| lavande / sphaigne | 0.59 | 0.32 | 0.71 | 0.193 | non |
| bourse_pasteur / moutarde | 0.60 | 0.33 | 0.70 | 0.108 | non |

## Palier ×4

| espèce | boîte l×h px [seed 42, n=1 capture, VM, ×4] | hauteur dessinée cm [seed 42, n=1 capture, VM, ×4] | height_cm | dessinée / height_cm [seed 42, n=1 capture, VM, ×4] | couleur moyenne [seed 42, n=1 capture, VM, ×4] |
| --- | --- | --- | --- | --- | --- |
| achillee | 47×74 | 47 | 40 | 1.19 | #91ad8b |
| ail | 46×83 | 53 | 50 | 1.06 | #6ca87b |
| armoise | 78×172 | 110 | 110 | 1.00 | #747d66 |
| bambou | 130×391 | 251 | 250 | 1.00 | #88a951 |
| basilic | 61×80 | 51 | 40 | 1.28 | #60ac4f |
| ble | 67×163 | 104 | 100 | 1.04 | #bbaa4c |
| bourrache | 102×132 | 85 | 70 | 1.21 | #518b5a |
| bourse_pasteur | 28×67 | 43 | 40 | 1.07 | #759856 |
| carotte | 31×100 | 64 | 60 | 1.07 | #61a56e |
| chanvre | 89×470 | 301 | 300 | 1.00 | #3a7938 |
| consoude | 126×122 | 78 | 50 | 1.56 | #4a8244 |
| courgette | 222×127 | 81 | 45 | 1.81 | #2c783b |
| dactyle | 128×177 | 113 | 90 | 1.26 | #5b905f |
| drosera | 22×22 | 14 | 10 | 1.41 | #92503d |
| fetuque | 49×62 | 40 | 25 | 1.59 | #628756 |
| fraisier | 65×47 | 30 | 15 | 2.01 | #408747 |
| framboisier | 113×257 | 165 | 150 | 1.10 | #667f45 |
| haricot | 97×78 | 50 | 200 | 0.25 | #64b855 |
| jasmin | 88×59 | 38 | 43 | 0.89 | #569855 |
| lavande | 149×134 | 86 | 50 | 1.72 | #596e63 |
| lierre | 141×58 | 37 | 42 | 0.88 | #255f32 |
| mache | 26×35 | 22 | 18 | 1.25 | #54a559 |
| menthe | 58×65 | 42 | 30 | 1.39 | #477e5f |
| minette | 100×54 | 35 | 30 | 1.15 | #759b49 |
| molene | 109×266 | 171 | 160 | 1.07 | #9ea97e |
| moutarde | 78×115 | 74 | 60 | 1.23 | #99b943 |
| myrtille | 81×88 | 56 | 40 | 1.41 | #528a4f |
| ortie | 90×141 | 90 | 90 | 1.00 | #356f3a |
| paturin | 43×52 | 33 | 30 | 1.11 | #8db76e |
| phacelie | 115×134 | 86 | 80 | 1.07 | #849799 |
| pissenlit | 76×60 | 38 | 30 | 1.28 | #539638 |
| plantain | 52×60 | 38 | 25 | 1.54 | #477b43 |
| poivron | 121×146 | 94 | 80 | 1.17 | #4c8c41 |
| seigle | 97×291 | 187 | 160 | 1.17 | #b3a463 |
| sphaigne | 98×55 | 35 | 6 | 5.88 | #8cbb73 |
| thym | 83×71 | 46 | 25 | 1.82 | #4c6c41 |
| tomate | 90×147 | 94 | 84 | 1.12 | #4b9b3d |
| tournesol | 109×406 | 260 | 250 | 1.04 | #4d8137 |
| trefle | 85×45 | 29 | 15 | 1.92 | #388e4b |
| violette | 53×42 | 27 | 12 | 2.24 | #497b4f |

**Hauteur hors tolérance [seed 42, n=1 capture, VM, ×4] : 9 sur 40** (consoude, courgette, dactyle, fraisier, haricot, lavande, myrtille, sphaigne, thym).

**Paires confondues [seed 42, n=1 capture, VM, ×4] : 0 sur 780.** Seuils : gabarit ≤ 0.15, proportions ≤ 0.15, recouvrement > 0.7, ΔE < 0.05. Espèces dans au moins une paire : 0.

Paires passant chaque critère seul [seed 42, n=1 capture, VM, ×4] : gabarit 19, proportions 111, recouvrement 4, ΔE 119.

| paire | gabarit [seed 42, n=1 capture, VM, ×4] | proportions | recouvrement | ΔE | confondue |
| --- | --- | --- | --- | --- | --- |
| sphaigne / thym | 0.23 | 0.34 | 0.76 | 0.249 | non |
| thym / trefle | 0.37 | 0.38 | 0.76 | 0.100 | non |
| sphaigne / trefle | 0.18 | 0.06 | 0.75 | 0.163 | non |
| fraisier / lavande | 0.65 | 0.20 | 0.72 | 0.107 | non |
| lavande / violette | 0.69 | 0.12 | 0.65 | 0.058 | non |
| courgette / thym | 0.63 | 0.33 | 0.62 | 0.044 | non |
| lavande / mache | 0.83 | 0.33 | 0.62 | 0.170 | non |
| lavande / trefle | 0.66 | 0.41 | 0.61 | 0.114 | non |
| lavande / thym | 0.47 | 0.05 | 0.61 | 0.056 | non |
| lavande / sphaigne | 0.59 | 0.38 | 0.61 | 0.237 | non |
| trefle / violette | 0.38 | 0.33 | 0.61 | 0.059 | non |
| mache / sphaigne | 0.73 | 0.58 | 0.60 | 0.089 | non |
