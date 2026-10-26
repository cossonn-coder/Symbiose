# ④ Pont : segments en delta (protocole 0.6.0)

**Golden** : intact — vérifié : `tests/test_golden.py` n'importe rien de `tools/simserver/`.
**Build** vert. Suites `tests/simserver` (lancées par `test_sim_server`) vertes.

## Constat
Phase B au PC (rendu suspendu) : tick 1 572 ms, step vu par la vue 2 454 ms → surcoût du
pont ≈ 880 ms/step (réponse 2,2 Mo, parse 192 ms, lecture plantes 173 ms) [n=1 run, PC].
Mesuré VM (sprint FLUIDITÉ PC, constat 5) : plantes = 56 % de la réponse, segments = 70 %
des octets plantes ; dans ~99 % des segments le SEUL champ qui bouge d'une semaine à
l'autre est `age_weeks` (+1) ; `length_cm` bouge dans ~24 % ; `genes` (9 % des octets
plantes) ne bouge jamais. Sérialiseur actuel : `data/code/tools/simserver/segments_pont.py`
(`SegmentsVue`, cache à deux générations par `id(segment)`), appelé par
`serialize.py:821` ; lecteur C# : `core/PlantStructure.cs` `FromSnapshot` (lit `age_weeks`
l.250), `core/PlanteLue.cs`.

## Modèle
- **Opt-in** : la vue demande le mode delta dans sa requête de step / snapshot. Sans la
  demande, le snapshot reste COMPLET et identique (tous les tests et outils existants qui
  lisent `segments`, p. ex. `tests/simserver/taille.py` qui lit `parent`, restent intacts).
- En delta, par plante : segments transmis avec leur **semaine de naissance** (la vue calcule
  `age_weeks = semaine courante − naissance`) ; seuls les segments **changés** depuis le
  dernier envoi à ce client (nouveaux, géométrie / longueur / épaisseur / apex modifiés)
  sont envoyés, plus la liste des segments supprimés et des plantes disparues ; `genes`
  seulement au premier envoi d'une plante.
- Identité d'un segment : à établir AU CODE (indice dans la liste ? un segment peut-il être
  inséré au milieu / retiré par la taille ?). Si l'identité stable n'existe pas, choisir le
  plus simple qui reste exact (p. ex. delta par plante : « structure inchangée sauf âge » vs
  « structure renvoyée »), et le dire au rapport.
- **Resynchronisation** : la vue peut demander un complet (démarrage, chargement de save,
  rotation de monde, incohérence détectée) ; le serveur oublie alors l'état du client.
- La semaine de naissance est-elle connue du moteur ? Sinon la dériver côté pont
  (semaine courante − `age_weeks`) — déterministe, sans toucher `sim/`.

## À faire
1. Python (`tools/simserver/`) : mode delta + état « dernier envoyé » par client, borné au
   monde courant. Version du pont → **0.6.0** (`version.py`) ; mettre à jour les tests qui
   vérifient la version.
2. **Test d'équivalence** neuf (`tests/simserver/…`) : sur plusieurs semaines (dont une
   taille et une mort), état reconstruit en appliquant les deltas = snapshot complet.
3. C# : appliquer les deltas sur la structure gardée par plante (`PlantStructure`,
   `PlanteLue`) ; demander la resynchro aux bons moments.
4. Mesurer VM (banc cadence headless existant ou banc 3 phases B) : octets de réponse,
   sérialisation, parse, lecture plantes — avant / après.

## Ne PAS faire
Toucher `sim/` ni `PlantInstance.structure_to_dict()` (format fidèle des sauvegardes / tests).
Passer en binaire (le JSON lisible est une règle projet).

## F5 Nico
Aucun changement visuel attendu ; le HUD doit afficher « pont 0.6.0 ».
