# Tronçon ③ — Couvertures posables (voile / cloche / ombrière)

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` + ce fichier suffit.
> Spec : `docs/champs/climat/conception_effondrement_meteo.md` (§4, §7).

## Objectif
Finir l'appareil de préparation §6 de `conception_meteo.md`. Trois gestes posables
manquants, chacun un **modificateur de milieu LOCAL** (philo #1 : pose en
planification = Vigueur modérée, vs réaction dans l'urgence = chère). Ils donnent au
joueur le moyen d'**atténuer** l'effondrement (tronçon ①) en amont.

## Modèle d'implémentation
Se modeler sur les gestes posables existants : `poser_bac` / `poser_pile`
(`sim/actions/compost.py`), `poser_pot` (`sim/actions/conteneurs.py`),
`poser_ruche` (`sim/actions/ruche.py`). Enregistrement dans `sim/actions/palette.py`
(cible `"plot"`), coût dans `cout_action`, déblocage par maîtrise dans
`sim/actions/deblocage.py` (comme `poser_tuteur`).

## Les trois gestes
| Geste | Agit sur le milieu LOCAL | Atténue |
|---|---|---|
| **Voile d'hivernage** | relève le `couvert` local lu par `t_min_nuit_at` (`fields/ecofields/thermique.py`) + écran physique | gel + grêle sur une zone |
| **Cloche** | protection par-plante (empreinte 1×1) : couvert + écran | gel + grêle d'un individu |
| **Ombrière** | réduit la lumière / chaleur locale (couplage LightField) → baisse l'évaporation | canicule / sécheresse sur une zone |

**Intention, pas placement imposé** : le sous-agent décide comment chaque structure
injecte son effet dans le champ local (p.ex. voile → terme `couvert` additionnel lu
par `t_min_nuit_at` ; ombrière → occulteur local du LightField, comme la maison).
Respecter : agir par le MILIEU, jamais en multiplicateur direct sur la plante (#1/#2).

## Voix des gestes (obligatoire)
Chaque geste reçoit ses entrées **carnet + encyclopédie** (voix naturaliste,
français accentué) : `sim/geste_corpus.py` (3 niveaux comme `poser_tuteur`) et, si
un outil est impliqué, `sim/outil_corpus.py`. La règle « toute plante = 5 voix » ne
s'applique PAS (ce sont des gestes/structures, pas des espèces) — mais un geste muet
est à éviter.

## Golden
**NEUTRE.** Aucune de ces structures n'est posée dans le golden (2 tuiles × 4 ans,
`main.py`/`test_golden.py`) → sortie inchangée par construction. Vérifier que le
golden ne bouge pas ; s'il bouge, une structure agit alors qu'aucune n'est posée
(bug d'effet par défaut) : corriger jusqu'à neutralité.

## Test ciblé à AJOUTER
Déterministe : sous le collapse connu (seed 12345, an 26), un plot **avec voile**
(ou cloche/ombrière selon l'événement) garde un noyau vivant là où le même plot
**sans** couverture s'effondre. Prouve que la préparation atténue réellement.

## NE PAS faire
- Pas de bonus/malus direct sur la plante — tout par le milieu.
- Pas de RNG vivant.
- Ne pas toucher à la météo (①/②) ni à la vue (④).
- Ne pas lancer `test_epaisseur_500ans`.

## Perf
Modificateurs locaux lus aux points de lecture existants (comme le paillage) ;
aucun nouveau balayage. Négligeable.
