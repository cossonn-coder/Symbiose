# ⑥ Signes côté Python : corpus, observation, carnet, encyclopédie, « appris » — kickoff autosuffisant

## Lire d'abord
`CLAUDE.md` · `00_etat.md` · `docs/rendu/pixelart/conception_plante_assemblee.md` §3 (décision 4)
+ §4.4 · `docs/narration/voix/conception_voix_narratives.md` (voix : carnet « je », encyclopédie
naturaliste) · `docs/narration/semiologie/conception_semiologie_foliaire.md` §2.

## Objectif
Donner au moteur narratif (pont + `sim/`) de quoi : (a) **consigner l'observation d'un signe** au
carnet, (b) **ouvrir une fiche « signe »** dans l'encyclopédie quand il est appris, (c) dire à la vue
**ce que le joueur a appris** (signes, bêtes) pour l'info-bulle à deux niveaux (⑦).

## Existant vérifié (2026-10-19)
- Observation par survol : `world/WorldView.Observation.cs` → commande pont `observer`
  (`tools/simserver/maitrise_cmds.cmd_observer` → `maitrise_pont.observer_espece`).
- Ledger : `sim/journal.py` (`entries` `{semaine, zone, kind, cause, espece}`, `_appender` borné).
- Carnet : `sim/carnet.py` (`CONCEPT_DE[(kind, cause)]`, registre D/I par `_seuil` =
  `SEUIL_CARNET` 3, ou 1 si option « interprétatif anticipé »).
- Encyclopédie : `sim/encyclopedie.py` (registre des corpus 3-niveaux des types neufs
  concept/technique/outil/geste — `_lire_corpus_3n`), `sim/encyclopedie_types.py`.
- Signes (11) : `sim/semiologie.py` `DETECTEURS` (chlorose, secheresse, asphyxie, ravageurs,
  rongeur_racinaire, ombre, senescence, acclimatation) + événementiels maladie, gel, grele.
- Précédent de filtrage par palier au snapshot : `tools/simserver/serialize.py` ~l.644-652
  (`nom_compose` joint seulement si `palier(météo)` suffit).

## Modèle
1. **Corpus** `sim/signes_corpus.py` (DONNÉE éditoriale, français accentué, voix du projet) :
   pour chaque signe : `vu` (ce qu'on voit, sans cause : « liseré brun-noir au bord des feuilles »),
   `concept` (concept de maîtrise **existant** — vérifier au code la liste ; ex. secheresse/asphyxie →
   eau, ravageurs/rongeur_racinaire → ravageurs, ombre → lumière, gel/grele → météo, maladie → maladie,
   senescence → sénescence ; chlorose et acclimatation : choisir le plus juste parmi l'existant, ne pas
   créer de concept sans le signaler), gabarits carnet D et I, fiche encyclopédie 3 niveaux
   (1 : le signe décrit ; 2 : sa cause biologique ; 3 : ce que le jardin peut y faire par le MILIEU —
   philo #1). Pour chaque espèce de la vie macro (`FAUNE_ENCYCLO`) : `vu` descriptif (« petit
   coléoptère rouge à points noirs »).
   Les descriptions `vu` des signes doivent correspondre à ce que dessine `PlantRenderer.PaliersHauts.cs`
   (bord brun-noir = gel ; bord beige-brun = sécheresse ; petits trous sombres = ravageurs ou grêle ;
   taches brun foncé = maladie) — le lire.
2. **Observation d'un signe** : étendre `observer` (champ optionnel `signe` + `species` + plot/zone),
   ou une commande sœur — au choix, rétro-compatible. Effet : une entrée ledger `kind="signe"`,
   `cause=<signe>`, `espece`, `semaine`, `zone` ; **dédup** une note par (espèce, signe, saison) et par
   joueur. `CONCEPT_DE[("signe", cause)]` + gabarits → le carnet la lit sans autre changement.
   Observer un signe **ne crédite pas** de maîtrise (sauf si le mécanisme existant le fait déjà pour
   l'observation d'espèce — vérifier, ne pas inventer).
3. **Appris** : un signe est appris quand `palier(concept) ≥ carnet._seuil(...)` ; une bête quand le
   palier de sa clé de maîtrise ≥ ce même seuil. Exposé à la vue : un petit champ du snapshot (ex.
   `appris: {"signes": [...], "faune": [...]}`) calculé en LECTURE PURE au serialize, comme
   `palier_meteo`. Bumper la version du pont (`tools/simserver/version.py`).
4. **Encyclopédie** : type `signe` au registre des corpus 3-niveaux ; découverte de la fiche = appris.

## Tests
Suite ciblée neuve (`tests/`) : observation → entrée ledger + dédup ; registre D puis I quand le
palier du concept franchit le seuil ; `appris` vide au départ, rempli après palier forcé
(`cmd_debug op=palier3` existe) ; fiche encyclopédie verrouillée puis ouverte ; tous les 11 signes et
toutes les espèces macro ont leur corpus (test d'exhaustivité). Suites existantes vertes.

## Vérifications
Golden `cd data/code && python3 -m tests.test_golden` → `22768f33…` (aucun appel `observer` dans le
golden) ; LDC (`carnet.py` 188, `encyclopedie.py` 72 : rester ≤ 300).

## NE PAS
Écrire dans le tick (`engine`/`fields`/`plants` n'importent jamais `carnet`/`journal`) · consigner les
symptômes au snapshot (non-déterminisme) · toucher au C# (c'est ⑦) · lancer `test_epaisseur_500ans`.
DeepSeek : uniquement pour relire la cohérence du corpus si utile, jamais pour l'écrire.

## Golden
Intact.
