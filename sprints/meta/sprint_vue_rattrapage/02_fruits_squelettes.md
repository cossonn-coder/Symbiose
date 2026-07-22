# 02 — Cycle de vie visible : fruits réels + squelettes post-mortem

> Lire `00_etat.md`. **Snapshot enrichi en LECTURE seule** (golden neutre) +
> rendu C#. Rend visible ce que la décompo·compost ②③ a apporté au moteur :
> les fruits traçables (maturité, déplétion par `manger`) et les **squelettes**
> de plantes mortes (la mort ne fait plus disparaître la plante). Ampleur : **moyen**.

## Partie A — Python : exposer les morts (read-only, golden NEUTRE)
`tools/simserver/serialize.py`, `_snapshot` : aujourd'hui `if not p.is_alive:
continue` saute les squelettes. Les **inclure** avec un bloc minimal :
- ajouter par plante un champ `dead` (ou `mort`) : `false` pour les vivantes ;
  pour les mortes persistantes (`p.morte and p.bois_restant > 1e-9` OU
  `stade_mort` non vide), exposer `{stade_mort ("seche"/"couchee"), bois_restant,
  semaines_mort}` + la position + les `segments` (la silhouette nue à dessiner).
- **Ne PAS toucher le tick.** C'est de la sérialisation : `serialize.py` lit
  `tile.plants` (qui contient désormais les morts, cf. décompo ②B `_tick_skeletons`
  ne les retire qu'après épuisement du bois). Vérifier `908f591bee…` inchangé.
- Bump `ENGINE_VERSION` 0.3.5 → 0.3.6 + historique (`version.py`). Champs
  toujours optionnels côté vue (tolérance pré-0.3.6, comme les bumps précédents).
- `tests/test_sim_server.py` : +checks (un mort apparaît avec `stade_mort`, les
  vivantes ont `dead=false`, déterminisme byte-à-byte). Garder 123 + N.

## Partie B — C# : fruits réels au lieu du proxy saisonnier
Aujourd'hui `PlantRenderer.Organs.cs` dessine fleurs/fruits depuis le **proxy**
`organ` (`REPRO_BY_SEASON`) aux `OrganSites()`. Le vrai état est `plant.fruits[]`
(`{segment, maturite, masse}`) — déjà au snapshot (③).
- Faire passer la liste `fruits` du snapshot à `PlantRenderer` (comme la structure).
- Dessiner **un fruit par entrée**, ancré à son `segment` (mapper `segment` →
  position 3D via la structure, même `Iso` que le bois), **couleur ∝ `maturite`** :
  vert (`<1.0`) → mûr (`~1.0`) → sur-mûr/fermenté (`>MATURITE_CHUTE 1.3`, teinte
  brune). Taille ∝ `masse`. Garder les **fleurs** sur le proxy `organ` (pas d'état
  moteur de fleur) ; les **fruits** basculent sur l'état réel.
- Conséquence visible : la déplétion par `manger` (un fruit disparaît) et la
  chute des sur-mûrs deviennent observables.

## Partie C — C# : manger un fruit ciblé (`target.fruit`)
- Le geste `manger` (kind `p`) envoie aujourd'hui la plante entière (chemin
  legacy). L'enrichir : si la plante visée a des fruits, **choisir le fruit le
  plus proche du clic** et envoyer `target.fruit = index` (le serveur 0.3.4 le
  consomme, gain ∝ maturité, l'organe disparaît). Pas de fruit sous le clic →
  chemin générique inchangé (plante entière).
- Le picking de fruit réutilise les positions calculées en Partie B.

## Partie D — C# : squelettes
- Dans `ApplySnapshot` (`WorldView.Snapshot.cs`), ne plus ignorer les entrées
  `dead` : créer/garder un `PlantRenderer` en **mode squelette** (silhouette de
  bois nu, pas d'organes ni de feuilles ; `seche` = debout, `couchee` = au sol/
  aplati). Réutiliser `DrawSegments` avec une palette « bois mort » (gris-brun)
  et sans `DrawOrgans`. Le squelette **disparaît** quand le snapshot ne le liste
  plus (bois épuisé, retrait moteur ②B).

## Vérification
- `dotnet build` vert ; golden `908f591bee…` inchangé (Partie A = lecture seule).
- `tests/test_sim_server` : 123 + nouveaux checks verts.
- **F5 Nico** : (a) un pommier mûr montre des fruits qui **verdissent→mûrissent→
  brunissent** au fil des semaines ; (b) `manger` un fruit → il disparaît, gain
  Vigueur ∝ maturité ; (c) une annuelle qui meurt laisse une **silhouette sèche**
  qui se couche puis se fragmente et disparaît (le pommier de sénescence aussi,
  test long). *(Le golden ne fait pas mûrir AppleTree — fenêtre 2 ans < 5 ans de
  maturité ; pour voir des fruits au F5, jouer le scénario potager / saisons.)*

## Définition de fait
- [ ] Snapshot expose les morts (Partie A), golden inchangé, protocole 0.3.6.
- [ ] Fruits rendus depuis l'état réel (maturité visible), `manger`-fruit ciblé.
- [ ] Squelettes rendus (sèche/couchée) et retirés à l'épuisement.
- [ ] Build vert, témoin incrémenté, `00_etat.md` MAJ. Commit.

## Commit suggéré
`feat(vue·rattrapage) : 02 — fruits réels (maturité) + squelettes post-mortem (snapshot 0.3.6 RO, golden intact)`
