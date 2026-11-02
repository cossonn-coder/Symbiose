# Mesure du tronçon ① : colonies de fleurs au moteur

Monde `full`, seed 42, 3 ans, VM. Scripts : `mesures/mesure_butineurs_bord.py`, `tools/banc_cadence`, `bancs/mesure_calendrier`.
« Avant » = arbre `HEAD` 2c79791 extrait à part. Le monde est déterministe : les plantes ne varient pas d'un run à l'autre.

## Pommier × butineurs en an 1 : D119 (c) N'EST PAS fermée

Seuil de `mesure_calendrier` : densité moyenne de la tuile ≥ 0,05.

| Monde | Sem. de floraison ≥ 0,5 | Tuile avant → après | Plots du pommier avant → après | Croise, avant → après |
|---|---|---|---|---|
| `full` | s4 | 0,014 → 0,016 | 0,058 → 0,058 | non → non |
| `full` | s5 | 0,039 → 0,052 [marge 0,002 sur le seuil, n=1 graine] | 0,167 → 0,170 | non → oui |
| `floraison_saisons` + ceinture | s6 | 0,033 → 0,033 | 0,161 → 0,161 | non → non |
| `floraison_saisons` + ceinture | s7 | 0,052 → 0,082 | 0,283 → 0,309 | oui → oui |

- Bilan `full` : 0/2 → 1/2 semaines [n=1 graine, VM], mais pollen reçu toujours 0 pendant ces deux semaines : aucun agent butineur ne vient.
- `bancs/mesure_calendrier` lit `floraison_saisons` SANS ceinture : il reste à 0/2 par construction, il ne peut pas voir les colonies. D'où le script dédié.
- **Cause** : le pommier fleurit en s4-s5 ; le bouton d'or commence à s4 et nourrit peu (goût 0,30, famille absente des tables), la marguerite à s7. La population monte de 15 %/semaine vers une cible bridée par le froid (T 5 à 10 °C).
- **Sensibilité** [`full`, n=1 run par variante, code de géométrie antérieur] : nourriture ×2, bouton d'or dès s1 et goût 0,7 cumulés : 0 agent en s5, premier agent en s7, floraison déjà à 0,18. Nourrir davantage ne règle pas le rendez-vous. Valeurs non retenues.

## Effet réel : présent, surtout hors floraison du pommier

| Indicateur | Avant | Après | Limite |
|---|---|---|---|
| Densité moyenne, tout le monde, an 1 | 0,374 | 0,431 | [n=1 graine, VM] |
| Densité moyenne, an 2 | 0,539 | 0,590 | [n=1 graine, VM] |
| Densité moyenne, an 3 | 0,515 | 0,563 | [n=1 graine, VM] |
| Pic tuile O, an 1 | 0,862 | 1,183 | [n=1 graine, VM] |
| Pic tuile SO, an 1 | 0,849 | 1,207 | [n=1 graine, VM] |
| Pic tuile SE, an 1 (bord sud : bouton d'or) | 0,846 | 0,895 | [n=1 graine, VM] |
| Banc sans jardin fleuri, densité moyenne an 1 | 0,029 | 0,096 | [`floraison_saisons` + ceinture, n=1 graine, VM] |

## Cadence : budget tenu

| Indicateur | Avant | Après | Limite |
|---|---|---|---|
| Tick an 2 moyen, 1ʳᵉ paire | 1074 ms | 1103 ms | +2,7 % [n=1 paire, VM] |
| Tick an 2 moyen, 2ᵉ paire | 1103 ms | 1176 ms | +6,6 % [n=1 paire, charge VM 7,13 au départ de « après » : peu fiable] |
| Tick an 2 moyen, les deux paires | 1088 ms | 1140 ms | +4,7 % [n=2 par côté, VM, budget ≤ +10 %] |
| Plantes an 2, moyenne / max | 498 / 620 | 519 / 654 | [seed 42, n=1 graine] |
| Plantes an 3, moyenne / max | 660 / 711 | 690 / 747 | [seed 42, n=1 graine] |
| Réponse an 2, moyenne | 1257 Ko | 1289 Ko | [n=1 graine, VM] |

Le coût suit les plantes en plus (+4 à +5 % [seed 42, n=1 graine]), l'effet indirect annoncé en conception §4. Nourriture non réduite.

## Non mesuré

Une seule graine, à 2 prairies et 2 friches. Rien sur un monde à forêts ou falaises, où les colonies sont rares ou absentes.
