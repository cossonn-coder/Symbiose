# Mesures APRÈS feuilles — sprint AUTOMNE VISIBLE ③

Rejouer : `cd data/code && python3 -m bancs.mesure_feuilles 3`. Tous les chiffres ci-dessous : monde `full`,
seed 42, un seul run sur la VM. La semaine lue est la prochaine à simuler : à « s36 », le tick de s35 est le dernier joué.

## Lecture

- **Calibrage** : `FEUILLE_PAR_PLOT = 0,30` retenu. À 0,10, la feuille pesait peu face à l'herbacé : médiane 0,048
  contre 0,113 par plot en s37 [n=1 run, VM], feuille dominante sur 33 plots [n=1 run, VM]. À 0,30 : médiane 0,145
  contre 0,113 [n=1 run, VM], dominante sur 178 plots [n=1 run, VM].
- **Critère s36 du kickoff, partiellement tenu** : 4 arbres sur 6 ont un tapis sur tous leurs plots de couronne ;
  un aulne a 28 plots sur 47, grâce à une couronne voisine, et le bouleau 0 plot sur 70 [n=1 run, VM]. En s37,
  les 6 sur 6 ont leur couronne couverte [n=1 run, VM]. Cause : `semaine_abscission` n'a pas de composante par espèce
  (pivot s34, bornes s30-36, seul le gène décale). Le bouleau et un aulne de ce run ont `w` = s36, leur premier dépôt
  est donc au tick de s36. Limite consignée, non corrigée sur consigne de l'orchestrateur.
- **Sol, pas de dérive aberrante sur 3 ans** : N sous couronne de −12 % à +27 % par rapport aux témoins en an 3
  [5 tuiles, n=1 run, VM]. Matière organique active sous couronne souvent inférieure aux témoins dès l'an 2, déjà sous
  le calibrage 0,10 [n=1 run, VM] : l'écart ne vient donc pas d'un excès de feuilles. Cause non isolée (hypothèse :
  moins d'herbacées sous l'ombre). Témoin non contrôlé : autres plantes et faune varient d'un plot à l'autre.
- **Taille du snapshot** : s39, 489 262 → 497 857 octets, soit +1,8 % [n=1 run, VM], sous le seuil de signalement de +20 %.
  Peu de plots en plus : 677 → 701 plots de litière [s40, n=1 run, VM]. L'herbacé et le bois couvrent déjà la plupart.
- **Limites** : les dates ne diffèrent pas par espèce (voir ci-dessus) ; la part de couronne qui déborde de la tuile n'est
  ni déposée ni reportée ; `foliage_density_at` inchangée (conception §3.3). Masse par arbre multipliée par 13 par
  rapport à l'ancienne formule [1 pommier isolé de 11 ans, plot (8,5), sans lumière, VM] : effet voulu par la conception §3.2.

## Tableaux bruts

### Par arbre, an 1

| arbre | tuile | sem. | plots couronne | plots avec feuilles | masse sous couronne | feuillage |
|---|---|---|---|---|---|---|
| Aulne | NE | s30 | 44 | 0 | 0.000 | 1.0 |
| Aulne | NE | s30 | 44 | 0 | 0.000 | 1.0 |
| Cerisier | O | s30 | 102 | 0 | 0.000 | 1.0 |
| Bouleau | SO | s30 | 70 | 0 | 0.000 | 1.0 |
| Pommier | S | s30 | 39 | 0 | 0.000 | 1.0 |
| Charme | SE | s30 | 78 | 0 | 0.000 | 1.0 |
| Aulne | NE | s32 | 44 | 0 | 0.000 | 1.0 |
| Aulne | NE | s32 | 44 | 0 | 0.000 | 1.0 |
| Cerisier | O | s32 | 102 | 0 | 0.000 | 1.0 |
| Bouleau | SO | s32 | 70 | 0 | 0.000 | 1.0 |
| Pommier | S | s32 | 46 | 46 | 3.369 | 0.75 |
| Charme | SE | s32 | 82 | 82 | 11.077 | 0.5 |
| Aulne | NE | s34 | 47 | 0 | 0.000 | 1.0 |
| Aulne | NE | s34 | 44 | 0 | 0.000 | 1.0 |
| Cerisier | O | s34 | 102 | 102 | 13.575 | 0.5 |
| Bouleau | SO | s34 | 70 | 0 | 0.000 | 1.0 |
| Pommier | S | s34 | 46 | 46 | 8.484 | 0.25 |
| Charme | SE | s34 | 82 | 82 | 19.001 | 0.0 |
| Aulne | NE | s36 | 47 | 28 | 2.083 | 1.0 |
| Aulne | NE | s36 | 44 | 44 | 3.265 | 0.75 |
| Cerisier | O | s36 | 102 | 102 | 23.618 | 0.0 |
| Bouleau | SO | s36 | 70 | 0 | 0.000 | 1.0 |
| Pommier | S | s36 | 46 | 46 | 8.828 | 0.0 |
| Charme | SE | s36 | 82 | 82 | 13.600 | 0.0 |
| Aulne | NE | s37 | 47 | 47 | 7.414 | 0.75 |
| Aulne | NE | s37 | 44 | 44 | 8.237 | 0.5 |
| Cerisier | O | s37 | 102 | 102 | 20.275 | 0.0 |
| Bouleau | SO | s37 | 70 | 70 | 5.083 | 0.75 |
| Pommier | S | s37 | 46 | 46 | 7.486 | 0.0 |
| Charme | SE | s37 | 82 | 82 | 11.635 | 0.0 |
| Aulne | NE | s38 | 47 | 47 | 12.166 | 0.5 |
| Aulne | NE | s38 | 44 | 44 | 12.698 | 0.25 |
| Cerisier | O | s38 | 102 | 102 | 17.462 | 0.0 |
| Bouleau | SO | s38 | 70 | 70 | 9.504 | 0.5 |
| Pommier | S | s38 | 46 | 46 | 6.383 | 0.0 |
| Charme | SE | s38 | 82 | 82 | 9.989 | 0.0 |
| Aulne | NE | s40 | 47 | 47 | 18.117 | 0.0 |
| Aulne | NE | s40 | 47 | 46 | 17.438 | 0.0 |
| Cerisier | O | s40 | 102 | 102 | 13.040 | 0.0 |
| Bouleau | SO | s40 | 70 | 70 | 16.743 | 0.0 |
| Pommier | S | s40 | 50 | 47 | 4.696 | 0.0 |
| Charme | SE | s40 | 83 | 82 | 7.420 | 0.0 |
| Aulne | NE | s42 | 47 | 47 | 14.284 | 0.0 |
| Aulne | NE | s42 | 47 | 46 | 13.796 | 0.0 |
| Cerisier | O | s42 | 102 | 102 | 9.844 | 0.0 |
| Bouleau | SO | s42 | 70 | 70 | 12.736 | 0.0 |
| Pommier | S | s42 | 50 | 47 | 3.515 | 0.0 |
| Charme | SE | s42 | 83 | 82 | 5.593 | 0.0 |
| Aulne | NE | s45 | 47 | 47 | 10.110 | 0.0 |
| Aulne | NE | s45 | 47 | 46 | 9.813 | 0.0 |
| Cerisier | O | s45 | 102 | 102 | 6.481 | 0.0 |
| Bouleau | SO | s45 | 70 | 70 | 8.465 | 0.0 |
| Pommier | S | s45 | 50 | 46 | 2.289 | 0.0 |
| Charme | SE | s45 | 83 | 82 | 3.679 | 0.0 |

### Sol, fin de chaque année

| an | tuile | plots sous couronne | N couronne | N témoin | om_active couronne | om_active témoin | om_stable couronne | om_stable témoin |
|---|---|---|---|---|---|---|---|---|
| 1 | NE | 53 | 0.137 | 0.132 | 0.194 | 0.156 | 0.155 | 0.157 |
| 1 | O | 102 | 0.535 | 0.520 | 0.105 | 0.101 | 0.154 | 0.147 |
| 1 | SO | 70 | 0.168 | 0.149 | 0.136 | 0.094 | 0.156 | 0.156 |
| 1 | S | 50 | 0.532 | 0.575 | 0.295 | 0.240 | 0.170 | 0.170 |
| 1 | SE | 83 | 0.849 | 0.788 | 0.134 | 0.122 | 0.156 | 0.158 |
| 2 | NE | 64 | 0.138 | 0.126 | 0.319 | 0.351 | 0.182 | 0.189 |
| 2 | O | 104 | 0.503 | 0.477 | 0.162 | 0.272 | 0.168 | 0.172 |
| 2 | SO | 76 | 0.181 | 0.153 | 0.243 | 0.316 | 0.176 | 0.181 |
| 2 | S | 56 | 0.532 | 0.610 | 0.583 | 0.624 | 0.243 | 0.224 |
| 2 | SE | 78 | 0.821 | 0.749 | 0.212 | 0.314 | 0.178 | 0.189 |
| 3 | NE | 72 | 0.139 | 0.114 | 0.461 | 0.372 | 0.233 | 0.220 |
| 3 | O | 85 | 0.404 | 0.381 | 0.200 | 0.358 | 0.186 | 0.211 |
| 3 | SO | 70 | 0.137 | 0.108 | 0.318 | 0.468 | 0.210 | 0.221 |
| 3 | S | 67 | 0.459 | 0.523 | 0.780 | 0.973 | 0.343 | 0.318 |
| 3 | SE | 78 | 0.755 | 0.656 | 0.250 | 0.422 | 0.205 | 0.237 |

### Taille du snapshot

s39, an 1 : 497857 octets.
