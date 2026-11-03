# Mesure après ① cycle de l'azote

Script : `mesures/mesure_prairie.py`. Monde `full`, seed 42, 5 ans (s260), n=1 graine, VM. « Avant » = commit `5b88d5b`.

## La référence du kickoff n'avait pas d'automate

729 plantes et trèfle 434 sur 274 plots ont été mesurés avec `srv.engine.tick_semaine()`. L'automate joue dans `cmd_step_week` : monté, il n'a jamais joué. Rejoué à l'identique avec `--moteur-seul`, le résultat retombe exactement sur ces trois chiffres. Le tableau §1 de la conception a la même limite, variantes comprises. Avec l'automate réellement actif, le « avant » an 5 est 834 plantes, trèfle 537 sur 345 plots [n=1 graine, VM]. Les deux protocoles figurent ci-dessous.

## Automate curatif réellement actif (`cmd_step_week`)

Toutes les valeurs : [`full`, seed 42, n=1 graine, VM].

| An | Plantes avant → après | Trèfle avant → après | Plots trèfle avant → après | Part avant → après | Plantes/plot occupé après | Morts de trèfle/an avant → après |
|---|---|---|---|---|---|---|
| 1 | 283 → 284 | 118 → 119 | 63 → 64 | 41,7 % → 41,9 % | 1,33 | 46 → 46 |
| 2 | 712 → 710 | 458 → 456 | 236 → 233 | 64,3 % → 64,2 % | 1,61 | 442 → 445 |
| 3 | 861 → 847 | 562 → 547 | 315 → 309 | 65,3 % → 64,6 % | 1,56 | 363 → 386 |
| 4 | 876 → 769 | 557 → 442 | 329 → 275 | 63,6 % → 57,5 % | 1,40 | 242 → 393 |
| 5 | 834 → 628 | 537 → 289 | 345 → 209 | 64,4 % → 46,0 % | 1,22 | 261 → 455 |

N moyen par tuile, an 5 :

| | NO | N | NE | O | E | SO | S | SE |
|---|---|---|---|---|---|---|---|---|
| avant | 0,87 | 0,56 | 0,23 | 0,52 | 0,91 | 0,17 | 0,71 | 0,81 |
| après | 0,67 | 0,50 | 0,19 | 0,46 | 0,66 | 0,17 | 0,59 | 0,76 |

N sous le trèfle, moyenne an 2 : 0,97 avant → 0,52 après. Maximum, tous ans : 2,16 avant → 1,87 après.

Part du trèfle par tuile porteuse, ans 3 / 4 / 5, après : NO 79 / 73 / 61 %, NE 60 / 59 / 51 %, E 79 / 78 / 73 %, S 76 / 65 / 50 %. Avant, ces parts restent stables ou montent entre l'an 3 et l'an 5.

## Les plots se déplacent-ils ?

| An 3 → an 5 | Plots à trèfle | Neufs (parmi ceux de l'an 5) | Perdus (parmi ceux de l'an 3) |
|---|---|---|---|
| avant | 315 → 345 | 17 % | 9 % |
| après | 309 → 209 | 28 % | 51 % |

Sans automate, après : 242 → 181, neufs 35 %, perdus 51 % ; avant : 256 → 274, neufs 20 %, perdus 14 % [n=1 graine, VM].

Le tapis bouge davantage, mais il recule surtout. Il ne fait que baisser de l'an 3 à l'an 5 : aucun retour n'est visible sans graminées, comme le kickoff l'anticipait. Sur 5 ans, on ne peut pas dire où cette baisse s'arrête.

## Sans automate (`--moteur-seul`), pour comparer à la référence

| An 5 | Plantes | Trèfle | Plots | Part |
|---|---|---|---|---|
| avant | 729 | 434 | 274 | 59,5 % |
| après | 588 | 264 | 181 | 44,9 % |

## Critères de la conception §5, à ce stade

- Part sous 40 % : non, 46,0 % [n=1 graine, VM]. Reste à ②.
- Au moins un tiers de plots différents : 28 % avec automate, 35 % sans [n=1 graine, VM]. Non tenu avec l'automate.
- N non effondré ni saturé : tenu, 0,17 à 0,76 par tuile en an 5 [n=1 graine, VM].
- 18 espèces : non, 16 [n=1 graine, VM], inchangé. C'est l'objet de ②.

## Limite observée

4 tuiles sur 8 (N, O, SO, SE) n'ont aucun trèfle pendant les 5 ans, avant comme après [n=1 graine, VM]. Cause non isolée. Le mouvement du tapis ne se joue donc que sur NO, NE, E et S.

## Coût

Tick moyen an 2, automate actif, `tools/banc_cadence` : avant 780 et 790 ms, après 769 et 801 ms [seed 42, n=2 runs par arbre, VM, charge 6,1 au départ]. Écart dans le bruit. Budget +10 % tenu. Les populations de l'an 2 sont presque identiques : ce banc ne voit pas la baisse de population, qui arrive après.
