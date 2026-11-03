# Mesure après ② flore spontanée

Script : `mesures/mesure_prairie.py`, automate curatif actif. Monde `full`, seed 42, 5 ans. « Avant » = après ① (commit `4e8482e`). Tous les chiffres : [n=1 graine, VM].

## Résultat retenu (`AZOTE_RICHE` 0,45, dactyle rayon 50)

| An | Plantes avant → après | Trèfle avant → après | Plots trèfle avant → après | Part avant → après |
|---|---|---|---|---|
| 1 | 284 → 293 | 119 → 120 | 64 → 65 | 41,9 % → 41,0 % |
| 2 | 710 → 738 | 456 → 467 | 233 → 239 | 64,2 % → 63,3 % |
| 3 | 847 → 824 | 547 → 494 | 309 → 263 | 64,6 % → 60,0 % |
| 4 | 769 → 747 | 442 → 397 | 275 → 243 | 57,5 % → 53,1 % |
| 5 | 628 → 664 | 289 → 296 | 209 → 202 | 46,0 % → 44,6 % |

An 5 : trèfle 296, bourse-à-pasteur 124, minette 64, pâturin 45, dactyle 42, plantain 15, ortie 13, pissenlit 12, fétuque 12. Avant, pâturin 83 et pissenlit 39 : les neuves prennent surtout leur place, peu celle du trèfle.

Part du trèfle par tuile porteuse, ans 3 / 4 / 5 : NO 77 / 74 / 63 %, NE 63 / 65 / 55 %, E 67 / 64 / 62 %, S 75 / 65 / 53 %.

N moyen par tuile, an 5 : NO 0,63, N 0,56, NE 0,20, O 0,52, E 0,64, SO 0,17, S 0,66, SE 0,80.

Plots à trèfle an 3 → an 5 : 263 → 202, neufs 29 % (parmi ceux de l'an 5), perdus 45 % (parmi ceux de l'an 3).

Tick an 2, chaque arbre lancé seul : 63,97 s → 49,98 s [1 passe par arbre, VM]. Baisse non expliquée, le nombre de plantes monte de 4 % ; retenir seulement que le budget +10 % n'est pas dépassé.

## Critères de la conception §5

| Critère | Verdict | Valeur |
|---|---|---|
| Part du trèfle sous 40 % | **raté** | 44,6 % |
| Part qui varie par tuile d'une année à l'autre | tenu | voir ci-dessus, mais elle baisse presque partout : variation, pas oscillation |
| Au moins un tiers de plots différents an 3 → an 5 | **raté** au sens strict | 29 % de neufs ; 45 % de perdus |
| Au moins 18 espèces en an 5 | tenu | 20 |
| Les 4 ajoutées présentes | tenu | dactyle 42, plantain 15, ortie 13, fétuque 12 |
| N non effondré ni saturé | tenu | 0,17 à 0,80 par tuile |
| Tick an 2 ≤ +10 % | tenu | voir ci-dessus |

## Pourquoi la part reste au-dessus de 40 %

Le dactyle fait de l'ombre, mais il y en a trop peu.

1. **L'ombre marche.** Un pied adulte seul donne 0,25 de lumière sur son plot, sous la porte 0,30 des stolons. Sur un monde réel, 41 plots à dactyle adulte sur 41 sont sous la porte en an 5. Le chemin ombre → stolon bloqué existe.
2. **La quantité manque.** 40 dactyles environ face à 300 trèfles. Sur les 5 ans, avec le seuil 0,6, la sonde compte 537 levées spontanées toutes espèces, dont 37 dactyles. Ces levées passent par `GERM_PRESSION_FERALE` 0,30, le gate de couverture et la banque par archétype : un ramet de trèfle ne passe par aucun des trois.
3. **Les vivaces à archétype ne réalimentent pas leur banque.** `seed_bank.add(arch, …)` n'est appelé qu'à la mort des annuelles et des bisannuelles (`sim/engine/mortalite.py`). Un dactyle mûr dépose dans son pool génétique, jamais dans la densité de `grass`. Il ne peut donc pas s'amplifier par graine comme le trèfle. Vrai aussi du pâturin et du pissenlit.
4. **Aucune cohabitation mesurée** : avec le seuil 0,6, 0 plot porte à la fois trèfle et dactyle aux points de sonde (2 par an).

Sur la part, ② n'apporte que 1,4 point. Le recul vient surtout de ①. Le retour du trèfle n'est pas observé en 5 ans : il baisse encore en an 5.

## Variantes essayées

Réglages d'espèce uniquement. An 5, part / plots neufs :

| Variante | Trèfle | Part | Neufs | Retenue |
|---|---|---|---|---|
| Seuil 0,6, rayon 35 | 327 | 45,9 % | 29 % | non |
| Seuil 0,45, rayon 35 | 316 | 44,8 % | 29 % | non |
| + `archetype=None` (recrutement direct) | 316 | 44,8 % | 29 % | non, sans effet |
| + `archetype=None`, `reproduction_rate` 0,35 (celui du trèfle) | 296 | 42,7 % | 28 % | non, valeur injustifiée pour une graminée en touffe |
| Seuil 0,45, rayon 55 | 279 | 42,9 % | 30 % | non, au-delà du défaut de strate |
| Seuil 0,45, rayon 50 | 296 | 44,6 % | 29 % | **oui** |

Aucune n'atteint 40 % ni un tiers de neufs. `GERM_PRESSION_FERALE` et le gate de couverture n'ont pas été touchés.

**Limite du rayon** : la lumière se lit au centre du plot. À 50, un pied centré couvre aussi les 4 centres voisins (0,25), à 35 aucun. L'effet du rayon dépend donc de ce pas de 50 cm.

## Pistes, à trancher par Nico

- Faire alimenter la banque d'archétype par les vivaces mûres : mécanisme manquant, mais golden re-figé large, hors de ce tronçon.
- Pondérer la sous-sélection par le pool d'espèce du plot (`species_density`), pour que le dactyle se ressème autour de lui. Limité tant que le point précédent reste ouvert.
- Mesurer au-delà de 5 ans : la part baisse de 7 à 9 points par an depuis l'an 3, elle passerait sans doute 40 % en an 6, sans preuve ici.
