# ③ Feuille et gestes — coriacité, repousse, bouture, dormance, dominance

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_caracteres_vivants.md` §2.3 et §3.
> Golden attendu : **RE-FIGÉ annoncé** — cinq clés neuves ; grêle, litière, banque de
> graines et architecture lisent la plante.

## Objectif
Les gestes du joueur et les coups du ciel rencontrent des lignées différentes.

## À faire
1. **Cinq caractères en queue** : `coriacite_feuille`, `repousse`, `aptitude_bouture`,
   `dormance_graine`, `dominance_apicale` (§2.3).
2. **Coriacité** : (a) grêle, `species_base="hail_resistance_base"` dans
   `_mediated_damage` → la susceptibilité lit aussi le gène de la plante ; (b) pression des
   herbivores ÷ coriacité, bornée ; (c) **litière** : la décomposition dépend du tissu
   (`TISSU[p.tissu]`, `fields/ecofields/matiere_organique.py` ≈ l. 186). Porter un facteur de
   lenteur **sur la parcelle déposée** (là où la plante dépose sa litière ; lire `Parcelle`
   dans `fields/ecofields/litiere.py`) plutôt que de rechercher la plante au tick. La boucle
   de maturation est chaude : O(1) de plus par parcelle, mesurer.
3. **Repousse** : vitesse de reprise après `tailler`/`pincer` (`sim/actions/gestes.py` ≈
   l. 296-380), rabattage (`sim/actions/taille_herbacee.py`) et convalescence après
   herbivorie. Prix : la floraison qui suit est réduite d'autant (point d'accroche dans la
   floraison, une seule lecture).
4. **Aptitude au bouturage** : probabilité de reprise lue par `sim/actions/bouture.py`
   (`peut_bouturer`, `bouturer`), tirage **déterministe** (hash). Neutre d'espèce : reprendre
   le comportement actuel comme neutre (lire le code : si la reprise est certaine aujourd'hui,
   neutre = 1.0 et σ_A rogne vers le bas).
5. **Dormance des graines** : dans `tick_species_aging` (`fields/seedbank.py:491`, boucle
   chaude ≈ 60 000 stats/tick), la perte de densité d'un pool est modulée par la **moyenne**
   du gène de ce pool (une lecture par enregistrement, pas par stat). Prix : la germination
   (`sim/succession.py`) lève une fraction plus faible chaque semaine pour un pool dormant.
   Mesurer la perf.
6. **Dominance apicale** : multiplie `apical_dominance_base` de l'espèce là où la croissance
   des segments la lit (`sim/growth/`, auxine). `pincer` lève déjà la dominance.
7. **Re-figeage** : diff lu, `--capture`, hashes consignés. Perf du smoke consignée.

## Tests
- Test ciblé par caractère : une feuille coriace encaisse moins de grêle et sa litière dure
  plus ; une plante à forte repousse repart plus vite après une taille et fleurit moins ; la
  bouture prend selon le gène, de façon déterministe ; un pool dormant persiste plus
  longtemps ; une dominance forte donne une tige plus haute et moins de latérales.
- Suites gestes, bouture, banque de graines, croissance vertes.

## Ne PAS faire
- Faire remonter des graines au bêchage (aucune mécanique aujourd'hui : BACKLOG si utile).
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`00_etat.md` : ③ FAIT, hashes, perf. Commit.
