# Tranche 5 — Taille au segment près, à la souris (demande Nico, F5 t4·B)

> **Kickoff autosuffisant** (démarrage à froid : lire `00_etat.md` d'abord).
> Demande Nico (2026-06-11) : « pouvoir décider quelle branche je taille et
> où je fais la coupe avec la souris ». Aujourd'hui `tailler` ne propose que
> `cible="apex"|"branche"` (sélecteur déterministe moteur) — Maj+clic côté
> vue. Cette tranche donne le **choix du segment exact au clic**, avec
> surbrillance de la branche sous la souris. Ampleur : **moyen**.
> Golden écolo `16a1b937…` **intact** (couche joueur seule).

## 📖 Pédagogie — pourquoi c'est déjà presque prêt

Le seam moteur `sim/growth.py:atteindre_segment(plant, segment_id, intensite)`
cible N'IMPORTE QUEL segment depuis le sprint Croissance (« depuis Godot
tronçon 4+ il viendra du clic » — anticipé). Seule la façade joueur
`sim/actions.py:tailler` impose apex/branche via `_segment_cible`. Il faut
donc étendre LA FAÇADE (couche joueur, PAS le tick → golden écolo intact par
construction), le protocole, et le picking de la vue.

## Volet Python (`sim/actions.py` + `tools/sim_server.py` + tests)

1. **`tailler` accepte un segment explicite** : paramètre keyword
   `segment_id: int | None = None` — si fourni ET valide (existe, pas le
   collet `parent is None`), il REMPLACE le sélecteur `_segment_cible` ;
   sinon comportement actuel inchangé (compat : `test_vigueur` et
   `test_croissance` doivent passer SANS modification). Coût/gain inchangés.
2. **Protocole** : `target` de `tailler` gagne un champ optionnel
   `"segment": i` (l'index dans `segments` du snapshot — c'est déjà l'ordre
   de `structure_to_dict()`, stable et déterministe). `params.cible` reste
   le repli si `segment` absent.
3. **`tests/test_sim_server.py`** : tailler un segment précis d'une plante à
   ≥ 3 segments → le snapshot joint perd le sous-arbre ciblé ; segment
   invalide (hors bornes, collet) → `applied:false` + serveur survivant.

## Volet C# (`world/WorldView.cs` + `visuals/PlantRenderer.cs`)

4. **Hit-test de segment** : en mode geste `tailler`, le clic (et le survol)
   résolvent d'abord la plante (FindPlant, rayon 30 cm), puis le SEGMENT le
   plus proche du curseur en distance point-segment ÉCRAN (px) : projeter
   chaque segment (base→tip via `Iso`/`WorldToScreenOffset` + Position du
   renderer), garder le plus proche sous ~8 px écran. ~50 segments max par
   plante : linéaire, trivial.
5. **Surbrillance** : le segment sous la souris en mode tailler se dessine
   surligné (couleur claire par-dessus, `QueueRedraw` du renderer concerné
   seulement au CHANGEMENT de segment survolé — pas par frame). Prévoir un
   champ `HighlightSegment` (int, −1 = aucun) sur `PlantRenderer`, lu par
   `DrawSegments`.
6. **Clic** : envoie `target.segment` = index survolé (s'il y en a un, sinon
   repli `params.cible` comme aujourd'hui). Le flash jaune t4 reste.
7. **Légende** : « 7 tailler (survolez la branche, Maj = latéral auto) ».

## Critères de succès (F5 Nico)

- [ ] Mode tailler : la branche sous la souris se surligne ; clic → CETTE
      branche disparaît (+ sous-arbre) dans la foulée ; flash jaune.
- [ ] Sans survol précis (clic au pied) : comportement t4 (apex / Maj
      branche) inchangé.
- [ ] Segment invalide/disparu entre temps → refus propre, pas de crash.
- [ ] `test_sim_server` + `test_vigueur` + `test_croissance` verts ;
      golden écolo `16a1b937…` intact.

## Contraintes & rappels

- **GDScript interdit, namespace `Symbiose`** ; un volet committable à la
  fois (Python+tests d'abord, C# ensuite).
- `sim/actions.py` est COUCHE JOUEUR : la modifier ne touche pas le golden
  écolo, mais reste du code moteur Python → tests joueur d'abord.
- Témoin de build : incrémenter `WorldView.Build` (« t5·… ») pour le F5.
- Ne PAS entamer en passant : organes (t6/D33), observer/crediter_succes
  (tranche maîtrise), heatmaps. Backlog intact.
