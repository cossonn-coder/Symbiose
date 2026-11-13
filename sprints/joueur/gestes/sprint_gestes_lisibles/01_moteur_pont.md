# ① Moteur + pont — traces, règles, mots, rééquilibrage

> Lire d'abord : `CLAUDE.md`, `00_etat.md` (ce dossier), puis
> `docs/joueur/gestes/conception_gestes_lisibles.md` §3, §5, §6 (en entier).
> Golden attendu : **INTACT** (`data/code/tests/golden_hash.txt`, `b4a921f8…`).

## Objectif
Donner au moteur et au pont tout ce que la vue devra dessiner ou dire, sans que la vue
invente quoi que ce soit. Python seulement (`data/code/`), aucune ligne C#.

## À faire
1. **Registre des traces de gestes** (§3.1) — `game_state["traces_sol"]`, créé
   paresseusement par le premier geste qui écrit (jamais par une lecture : le smoke n'a
   pas de joueur, la clé ne doit pas y apparaître). Entrée = `{tuile, r, c, x_cm, y_cm,
   sorte, semaine}`. Sortes et durées : table §3.1 (constantes data-driven, une table).
   Écriture **quand le geste est appliqué** (payé), au niveau où le pont connaît la tuile
   et le point cliqué — choisir le point d'accroche après lecture de
   `tools/simserver/actions.py` et des routes ; ne pas modifier la signature des gestes
   de `sim/actions/` si l'écriture peut se faire à la route. Purge (expiration + plafond
   FIFO) à l'écriture et à l'export ; **jamais dans le tick**.
   Un module dédié (ex. `sim/traces_sol.py`, couche `sim`) : écriture, purge, lecture.
2. **Export au pont** : clé neuve du snapshot, liste creuse par tuile (patron `paillage`
   dans `tools/simserver/serialize.py`), avec l'âge de la trace en semaines (la vue
   l'estompe). + liste creuse des **plots secs** (`eco.humidite` sous un seuil, valeur
   brute arrondie) pour le craquelé (§3.2). Lecture pure. Clés optionnelles côté vue.
3. **Déraciné = couché** (§3.1) : après `deposer_mort` dans `deraciner`
   (`sim/actions/gestes.py`), le cadavre est en `stade_mort = "couchee"`. Vérifier que
   `couchee` est bien géré partout où `seche` l'est (décompo, export, rendu existant).
4. **`ecraser` épargne les volants** (§6) : attribut de donnée `vole` par espèce dans le
   registre de faune (`fields/population/registry.py` / `spec.py` — lire la structure
   avant). Refus **en amont** de toute dépense quand la guilde visée vole ; message
   diégétique. Le pont exporte `vole` avec les sprites (la vue en aura besoin au ④).
   Garder le code d'alarme abeille tel quel (devenu inatteignable par ce chemin).
5. **Pot posé hors du jardin** : reproduire au pont (`tools/simserver/conteneurs_route.py`)
   avec une cible hors monde / hors tuile. Si le pont accepte → refuser (désignation, ne
   coûte rien). Si le pont refuse déjà → consigner dans `00_etat.md` « bug côté vue, pour ④ ».
6. **Mots au lieu des chiffres** (§5) : toutes les phrases de geste du pont qui affichent
   un nombre (`grep` sur `:.1f`, `:.2f`, `+{` dans `tools/simserver/`) passent en mots, par
   paliers en doses (`PAILLAGE_DOSE`). Une fonction partagée (ex. `quantite_en_mots`) ;
   les champs numériques du bilan (`cost`, `gain`) restent pour la vue, seule la phrase change.
7. **Mesurer puis rééquilibrer À L'EXCÈS** (§5) : écrire une petite mesure reproductible
   (script sous `sprints/joueur/gestes/sprint_gestes_lisibles/mesures/`, seed 42) qui donne
   la masse glanée sur un plot ordinaire, le `compost_mur` d'un bac plein après une saison,
   le miel d'une ruche peuplée après une saison. Consigner les chiffres AVANT. Puis
   calibrer pour atteindre les cibles §5 (glaner ≥ 1 dose ; un épandage franc par saison ;
   un miel qui se sent), **de préférence par une constante côté geste** (rendement au
   moment du geste). Une constante lue dans le tick ne change que si le golden reste
   identique — sinon on revient à une constante côté geste. Consigner AVANT/APRÈS.
8. **Version du pont** : incrémenter `ENGINE_VERSION` (`tools/simserver/version.py`, 0.6.13
   → 0.6.14) avec sa note, comme les entrées précédentes.

## Tests
- Un test ciblé neuf (`data/code/tests/`) : trace écrite au geste payé, pas au refus ;
  expiration ; plafond ; absente du `game_state` sans geste ; `ecraser` sur un volant
  refusé sans dépense ; déraciné couché ; phrases sans chiffre.
- `python3 -m tests.test_golden` → hash identique. Suites des gestes existantes vertes
  (`tests/bancs/test_acces_gestes.py`, tests d'actions touchés).

## Ne PAS faire
- Aucun C#. Aucune trace écrite dans le tick. Aucun re-figeage du golden.
- Ne pas toucher aux outils (arrosoir, sécateur, Atelier) : sprint `outils_atelier`.
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.
- Ne supprimer aucun code. Fichier > 300 LDC (`tools/compte_ldc.py`) → scinder.

## Fin de tronçon
Mettre à jour `00_etat.md` : clés de pont ajoutées (noms exacts, format), constantes et
chiffres AVANT/APRÈS, verdict du bug du pot, écarts au kickoff.
