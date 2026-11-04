# Mesures AVANT — sprint FORMES DES PLANTES ①

Référence à rejouer après chaque tronçon de rendu. PNG non committés (`/tmp/planche_avant`, 160 images).

```
dotnet build Symbiose.csproj
python3 tools/mesure_silhouettes.py capturer /tmp/planche --zoom 1 4 --jobs 5
python3 tools/mesure_silhouettes.py mesurer  /tmp/planche --paires 30
```

Capture : banc `planche_especes`, `-w 0` (état posé, aucun tick), vent 0, ombres coupées, couches `Weather,MacroLife,House` masquées, référence avec `Objects` en plus, 3 images. Une paire de PNG par espèce et par palier. Déterminisme : descripteurs identiques à une seconde capture [tournesol et lavande à ×4, n=2 espèces].

## Lecture

- **L'effet générique se mesure** : 34 espèces sur 40 dessinent le même gabarit, 88 à 91 cm de haut à ×4 [seed 42, n=1 capture, VM], quelle que soit leur `height_cm`, de 6 cm (sphaigne, rapport 14,6) à 300 cm (chanvre, rapport 0,29). Seules dactyle, fétuque, plantain, trèfle (ports de prairie), lierre et jasmin (3 ans de structure, au sol) y échappent.
- **Les paires confondues sous-estiment l'œil** : 28 paires à ×4 pour 20 espèces [seed 42, n=1 capture, VM]. Ce squelette a des variantes au hash de l'individu (branche à gauche ou à droite), et le recouvrement les sépare, alors que l'œil voit la même plante. Les deux mesures se lisent ensemble : la hauteur est le signal le plus net, la paire le critère de sortie.
- **Lecture des PNG** (`dactyle`, `lavande` à ×4, `thym` à ×1) : concorde. À ×4, tige brune et 3 ou 4 touffes en bonsaï pour chaque voisine, l'espèce ne se reconnaît qu'à la teinte de ses touffes et à la couleur du disque de fleur. À ×1, une rangée de bâtonnets égaux. Le dactyle se lit tout de suite comme une graminée.

## Recalibrage des seuils (reporté en conception §6)

- **Recouvrement à ×1 sur une grille 4×4** au lieu de 16×16. Avec 16×16 : 3 paires [seed 42, n=1 capture, VM], soit la cible déjà atteinte avant tout travail, parce qu'un sprite de 8 px de large décalé d'un pixel ne se recouvre plus. Avec 4×4 : 14 paires. La cible (au plus 3) redevient un vrai critère.
- **Seuils inchangés à ×4** : gabarit 15 %, proportions 15 %, recouvrement 0,7, ΔE 0,05 donnent 28 paires. Cible 0 atteignable : aucune des 4 espèces de prairie n'est dans une paire à ×4 ni à ×1 [seed 42, n=1 capture, VM].
- **Hauteur** : ±20 % ou ±15 cm, le plus large. Au-dessous de 75 cm, la boîte compte aussi la nappe au sol (fétuque 40 cm dessinés pour 25, trèfle 29 pour 15 à ×4 [seed 42, n=1 capture, VM]) ; ±20 % seul refuserait ces ports déjà validés au F5.
- **Dactyle hors tolérance à ×4** : 113 cm pour 90 [seed 42, n=1 capture, VM] (85 à ×1) : ses panicules dépassent. Validé au F5 (D126), laissé tel quel.

## Palier ×1

| espèce | boîte l×h px [seed 42, n=1 capture, VM, ×1] | hauteur dessinée cm [seed 42, n=1 capture, VM, ×1] | height_cm | dessinée / height_cm [seed 42, n=1 capture, VM, ×1] | couleur moyenne [seed 42, n=1 capture, VM, ×1] |
| --- | --- | --- | --- | --- | --- |
| achillee | 12×35 | 90 | 40 | 2.24 | #637746 |
| ail | 15×35 | 90 | 50 | 1.79 | #5d643b |
| armoise | 8×36 | 92 | 110 | 0.84 | #747653 |
| bambou | 11×36 | 92 | 250 | 0.37 | #538037 |
| basilic | 8×36 | 92 | 40 | 2.31 | #4e8337 |
| ble | 13×35 | 90 | 100 | 0.90 | #46722d |
| bourrache | 11×35 | 90 | 70 | 1.28 | #577141 |
| bourse_pasteur | 9×35 | 90 | 40 | 2.24 | #496c2d |
| carotte | 7×34 | 87 | 60 | 1.45 | #5d8246 |
| chanvre | 13×36 | 92 | 300 | 0.31 | #4c8638 |
| consoude | 11×34 | 87 | 50 | 1.74 | #3e5c29 |
| courgette | 9×34 | 87 | 45 | 1.94 | #518540 |
| dactyle | 29×33 | 85 | 90 | 0.94 | #528f5c |
| drosera | 9×34 | 87 | 10 | 8.72 | #5f6a3d |
| fetuque | 13×14 | 36 | 25 | 1.44 | #5c9560 |
| fraisier | 9×35 | 90 | 15 | 5.98 | #52783b |
| framboisier | 12×36 | 92 | 150 | 0.62 | #547a36 |
| haricot | 9×36 | 92 | 200 | 0.46 | #568a3c |
| jasmin | 24×19 | 49 | 43 | 1.15 | #4f7934 |
| lavande | 9×35 | 90 | 50 | 1.79 | #72765a |
| lierre | 38×17 | 44 | 42 | 1.04 | #487f35 |
| mache | 7×35 | 90 | 18 | 4.99 | #627d3d |
| menthe | 7×36 | 92 | 30 | 3.08 | #537e37 |
| minette | 8×35 | 90 | 30 | 2.99 | #597c38 |
| molene | 8×34 | 87 | 160 | 0.54 | #577736 |
| moutarde | 9×34 | 87 | 60 | 1.45 | #6c843c |
| myrtille | 15×34 | 87 | 40 | 2.18 | #506638 |
| ortie | 12×34 | 87 | 90 | 0.97 | #38582b |
| paturin | 11×35 | 90 | 30 | 2.99 | #547534 |
| phacelie | 9×35 | 90 | 80 | 1.12 | #4e6e40 |
| pissenlit | 11×34 | 87 | 30 | 2.91 | #538038 |
| plantain | 12×8 | 21 | 25 | 0.82 | #326b36 |
| poivron | 12×35 | 90 | 80 | 1.12 | #376327 |
| seigle | 10×36 | 92 | 160 | 0.58 | #518037 |
| sphaigne | 14×34 | 87 | 6 | 14.53 | #707745 |
| thym | 12×35 | 90 | 25 | 3.59 | #716a3e |
| tomate | 5×35 | 90 | 84 | 1.06 | #4e7f36 |
| tournesol | 11×37 | 95 | 250 | 0.38 | #487233 |
| trefle | 21×11 | 28 | 15 | 1.88 | #2b8c40 |
| violette | 11×35 | 90 | 12 | 7.48 | #526537 |

**Hauteur hors tolérance [seed 42, n=1 capture, VM, ×1] : 28 sur 40** (achillee, ail, bambou, basilic, bourrache, bourse_pasteur, carotte, chanvre, consoude, courgette, drosera, fraisier, framboisier, haricot, lavande, mache, menthe, minette, molene, moutarde, myrtille, paturin, pissenlit, seigle, sphaigne, thym, tournesol, violette).

**Paires confondues [seed 42, n=1 capture, VM, ×1] : 14 sur 780.** Seuils : gabarit ≤ 0.15, proportions ≤ 0.15, recouvrement > 0.7, ΔE < 0.05. Espèces dans au moins une paire : 17.

Paires passant chaque critère seul [seed 42, n=1 capture, VM, ×1] : gabarit 187, proportions 191, recouvrement 37, ΔE 322.

| paire | gabarit [seed 42, n=1 capture, VM, ×1] | proportions | recouvrement | ΔE | confondue |
| --- | --- | --- | --- | --- | --- |
| bourse_pasteur / fraisier | 0.00 | 0.00 | 0.89 | 0.039 | oui |
| ortie / poivron | 0.03 | 0.03 | 0.86 | 0.037 | oui |
| basilic / menthe | 0.12 | 0.13 | 0.83 | 0.016 | oui |
| bambou / tournesol | 0.03 | 0.03 | 0.82 | 0.046 | oui |
| bambou / paturin | 0.03 | 0.03 | 0.81 | 0.032 | oui |
| tournesol / violette | 0.05 | 0.05 | 0.79 | 0.045 | oui |
| achillee / pissenlit | 0.08 | 0.06 | 0.77 | 0.043 | oui |
| fraisier / molene | 0.11 | 0.08 | 0.74 | 0.008 | oui |
| mache / molene | 0.12 | 0.15 | 0.72 | 0.021 | oui |
| carotte / minette | 0.12 | 0.10 | 0.72 | 0.021 | oui |
| basilic / carotte | 0.12 | 0.07 | 0.71 | 0.027 | oui |
| paturin / tournesol | 0.05 | 0.05 | 0.71 | 0.020 | oui |
| armoise / mache | 0.12 | 0.10 | 0.71 | 0.049 | oui |
| menthe / minette | 0.12 | 0.15 | 0.71 | 0.009 | oui |
| minette / phacelie | 0.11 | 0.11 | 0.87 | 0.050 | non |
| minette / seigle | 0.20 | 0.18 | 0.87 | 0.015 | non |
| bambou / violette | 0.03 | 0.03 | 0.87 | 0.084 | non |
| framboisier / ortie | 0.06 | 0.06 | 0.85 | 0.116 | non |
| chanvre / tournesol | 0.15 | 0.18 | 0.83 | 0.060 | non |
| bourrache / pissenlit | 0.03 | 0.03 | 0.83 | 0.052 | non |
| framboisier / poivron | 0.03 | 0.03 | 0.81 | 0.083 | non |
| bambou / chanvre | 0.15 | 0.15 | 0.80 | 0.019 | non |
| armoise / fraisier | 0.11 | 0.14 | 0.80 | 0.060 | non |
| haricot / mache | 0.22 | 0.20 | 0.80 | 0.040 | non |
| phacelie / seigle | 0.10 | 0.07 | 0.79 | 0.060 | non |
| chanvre / violette | 0.15 | 0.13 | 0.79 | 0.101 | non |
| paturin / violette | 0.00 | 0.00 | 0.79 | 0.052 | non |
| ble / haricot | 0.31 | 0.33 | 0.76 | 0.077 | non |
| courgette / lavande | 0.03 | 0.03 | 0.75 | 0.079 | non |
| armoise / molene | 0.06 | 0.06 | 0.74 | 0.057 | non |

## Palier ×4

| espèce | boîte l×h px [seed 42, n=1 capture, VM, ×4] | hauteur dessinée cm [seed 42, n=1 capture, VM, ×4] | height_cm | dessinée / height_cm [seed 42, n=1 capture, VM, ×4] | couleur moyenne [seed 42, n=1 capture, VM, ×4] |
| --- | --- | --- | --- | --- | --- |
| achillee | 73×137 | 88 | 40 | 2.20 | #4c7751 |
| ail | 57×137 | 88 | 50 | 1.76 | #718062 |
| armoise | 68×137 | 88 | 110 | 0.80 | #797657 |
| bambou | 69×137 | 88 | 250 | 0.35 | #467f38 |
| basilic | 56×137 | 88 | 40 | 2.20 | #467e38 |
| ble | 74×137 | 88 | 100 | 0.88 | #447f38 |
| bourrache | 67×137 | 88 | 70 | 1.25 | #386a4a |
| bourse_pasteur | 48×137 | 88 | 40 | 2.20 | #477d37 |
| carotte | 56×137 | 88 | 60 | 1.46 | #468254 |
| chanvre | 78×137 | 88 | 300 | 0.29 | #3f7f38 |
| consoude | 65×137 | 88 | 50 | 1.76 | #3f623d |
| courgette | 62×142 | 91 | 45 | 2.02 | #2b6c34 |
| dactyle | 128×177 | 113 | 90 | 1.26 | #5c905f |
| drosera | 60×137 | 88 | 10 | 8.78 | #677856 |
| fetuque | 49×62 | 40 | 25 | 1.59 | #638656 |
| fraisier | 48×142 | 91 | 15 | 6.07 | #695733 |
| framboisier | 74×142 | 91 | 150 | 0.61 | #625b32 |
| haricot | 50×137 | 88 | 200 | 0.44 | #478e4f |
| jasmin | 87×69 | 44 | 43 | 1.04 | #4d8638 |
| lavande | 71×137 | 88 | 50 | 1.76 | #59665e |
| lierre | 159×75 | 48 | 42 | 1.14 | #448239 |
| mache | 51×137 | 88 | 18 | 4.88 | #578b54 |
| menthe | 52×137 | 88 | 30 | 2.93 | #447e37 |
| minette | 56×137 | 88 | 30 | 2.93 | #458038 |
| molene | 50×137 | 88 | 160 | 0.55 | #467f37 |
| moutarde | 64×137 | 88 | 60 | 1.46 | #508533 |
| myrtille | 69×137 | 88 | 40 | 2.20 | #406845 |
| ortie | 74×137 | 88 | 90 | 0.98 | #335a31 |
| paturin | 50×137 | 88 | 30 | 2.93 | #487b36 |
| phacelie | 71×137 | 88 | 80 | 1.10 | #3e6d51 |
| pissenlit | 49×137 | 88 | 30 | 2.93 | #458038 |
| plantain | 52×60 | 38 | 25 | 1.54 | #497c44 |
| poivron | 62×137 | 88 | 80 | 1.10 | #406d3e |
| seigle | 62×137 | 88 | 160 | 0.55 | #478038 |
| sphaigne | 65×137 | 88 | 6 | 14.64 | #64874f |
| thym | 68×137 | 88 | 25 | 3.51 | #526442 |
| tomate | 48×142 | 91 | 84 | 1.08 | #476d32 |
| tournesol | 67×137 | 88 | 250 | 0.35 | #3f6629 |
| trefle | 85×45 | 29 | 15 | 1.92 | #398f4c |
| violette | 68×137 | 88 | 12 | 7.32 | #395840 |

**Hauteur hors tolérance [seed 42, n=1 capture, VM, ×4] : 30 sur 40** (achillee, ail, armoise, bambou, basilic, bourrache, bourse_pasteur, carotte, chanvre, consoude, courgette, dactyle, drosera, fraisier, framboisier, haricot, lavande, mache, menthe, minette, molene, moutarde, myrtille, paturin, pissenlit, seigle, sphaigne, thym, tournesol, violette).

**Paires confondues [seed 42, n=1 capture, VM, ×4] : 28 sur 780.** Seuils : gabarit ≤ 0.15, proportions ≤ 0.15, recouvrement > 0.7, ΔE < 0.05. Espèces dans au moins une paire : 20.

Paires passant chaque critère seul [seed 42, n=1 capture, VM, ×4] : gabarit 293, proportions 291, recouvrement 48, ΔE 278.

| paire | gabarit [seed 42, n=1 capture, VM, ×4] | proportions | recouvrement | ΔE | confondue |
| --- | --- | --- | --- | --- | --- |
| basilic / carotte | 0.00 | 0.00 | 1.00 | 0.030 | oui |
| haricot / molene | 0.00 | 0.00 | 1.00 | 0.046 | oui |
| basilic / minette | 0.00 | 0.00 | 0.93 | 0.003 | oui |
| carotte / minette | 0.00 | 0.00 | 0.93 | 0.030 | oui |
| lavande / phacelie | 0.00 | 0.00 | 0.90 | 0.042 | oui |
| bourrache / thym | 0.01 | 0.01 | 0.83 | 0.030 | oui |
| bourrache / consoude | 0.03 | 0.03 | 0.82 | 0.025 | oui |
| paturin / pissenlit | 0.02 | 0.02 | 0.81 | 0.013 | oui |
| consoude / myrtille | 0.06 | 0.06 | 0.79 | 0.014 | oui |
| bourrache / myrtille | 0.03 | 0.03 | 0.79 | 0.014 | oui |
| menthe / pissenlit | 0.06 | 0.06 | 0.79 | 0.006 | oui |
| consoude / thym | 0.04 | 0.04 | 0.78 | 0.019 | oui |
| moutarde / seigle | 0.03 | 0.03 | 0.78 | 0.019 | oui |
| achillee / phacelie | 0.03 | 0.03 | 0.78 | 0.034 | oui |
| myrtille / thym | 0.01 | 0.01 | 0.78 | 0.018 | oui |
| bourse_pasteur / molene | 0.04 | 0.04 | 0.76 | 0.006 | oui |
| menthe / minette | 0.07 | 0.07 | 0.75 | 0.005 | oui |
| haricot / pissenlit | 0.02 | 0.02 | 0.75 | 0.044 | oui |
| molene / pissenlit | 0.02 | 0.02 | 0.75 | 0.002 | oui |
| bambou / moutarde | 0.07 | 0.07 | 0.75 | 0.023 | oui |
| achillee / ble | 0.01 | 0.01 | 0.75 | 0.044 | oui |
| molene / paturin | 0.00 | 0.00 | 0.75 | 0.011 | oui |
| basilic / menthe | 0.07 | 0.07 | 0.74 | 0.003 | oui |
| carotte / menthe | 0.07 | 0.07 | 0.74 | 0.031 | oui |
| bourse_pasteur / paturin | 0.04 | 0.04 | 0.74 | 0.005 | oui |
| bambou / seigle | 0.10 | 0.10 | 0.73 | 0.004 | oui |
| menthe / paturin | 0.04 | 0.04 | 0.72 | 0.008 | oui |
| bourse_pasteur / pissenlit | 0.02 | 0.02 | 0.72 | 0.008 | oui |
| armoise / violette | 0.00 | 0.00 | 0.87 | 0.124 | non |
| consoude / moutarde | 0.02 | 0.02 | 0.81 | 0.115 | non |
