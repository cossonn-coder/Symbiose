# ④ Voix narratives + bancs d'acceptation

> Kickoff autosuffisant. Lire AVANT : `CLAUDE.md`, `00_etat.md`,
> `docs/conception/CONCEPTION_BUGS_EMERGENCE.md`,
> `docs/conception/CONCEPTION_VOIX_NARRATIVES.md`.
> Source de vérité = Python `data/code/`. Lancement depuis `data/code/`.

## Objectif
Donner leur voix aux deux mécaniques corrigées et poser les bancs d'acceptation
qui garantissent que les fixes tiennent. Tronçon **NEUTRE** pour le golden
(corpus read-only hors tick + bancs hors sim golden).

## Volet voix (patron : concept transversal `germination_thermique`, journal 88 ⑦)
- **Encyclopédie** (`sim/encyclopedie_corpus.py`, `CONCEPTS`) : enrichir/ajouter
  le concept **succession** (bascule pionnier→prairie : la description passe de
  descriptive à interprétative au seuil de maîtrise) et un concept
  **phénologie / floraison** (pourquoi les fleurs ne s'ouvrent pas toutes en même
  temps — étalement, mémoire de lignée). 3 niveaux chacun.
- **Carnet** (gabarits interprétatifs) : brancher le gène `phenologie_florale` et
  la reprise de succession sur les concepts existants si pertinent (cf.
  `CONCEPT_DE`). Rester sobre : pas de nouvelle espèce → pas de « 5 voix » à
  créer, seulement les concepts transversaux touchés.
- Vérifier la cohérence de vocabulaire (pas de lexique roguelike proscrit).

## Volet bancs d'acceptation (patron `bancs/climatique.py`, oracle en tendance)
1. **Étalement de floraison** : monde mono-espèce dense, simulé une saison,
   oracle vérifiant que les dates de franchissement de `floraison > 0.5` sont
   RÉPARTIES sur plusieurs semaines (variance non nulle), pas un créneau unique.
2. Confirmer que le banc « succession_bascule » du tronçon ② passe toujours (ne
   pas le dupliquer — juste l'exécuter dans la CI locale).

Oracles en tendance/borne, jamais de hash figé (un banc décrit un monde ;
l'oracle décide quoi observer). Référence comportementale : `/tmp/diag_symbiose.py`.

## Golden attendu
**NEUTRE / INCHANGÉ.** Le corpus est read-only (consulté hors tick) et les bancs
ne montent pas dans la sim golden. Relancer `python3 -m tests.test_golden` pour
CONFIRMER l'invariance (aucun re-figeage ici). Si le golden bouge, c'est un bug
introduit → annuler, ne pas figer.

## À NE PAS faire
- Ne pas introduire de nouvelle espèce ni toucher au moteur de sim.
- Ne pas re-figer le golden (ce tronçon est neutre par construction).

## Clôture
`00_etat.md` (sprint CLOS, bilan + hashes golden de la cascade ①→③),
`journal.md` + entrée `journal/` (décisions du sprint), `DETTE.md`
(D56 livré ; noter S2/S3 résolus). Commit final.
