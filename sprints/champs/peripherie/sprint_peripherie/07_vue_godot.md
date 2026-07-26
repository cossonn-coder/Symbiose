# ⑦ Vue Godot — le décor cesse de s'inventer, il obéit au moteur

> Sprint **PÉRIPHÉRIE** (D73), **dernier tronçon** (règle permanente : tout sprint finit
> par sa vue Godot). Lis d'abord `CLAUDE.md` + `00_etat.md` + ①→⑥.
> Spec : `docs/champs/peripherie/conception_peripherie.md` §4.1, §11.
>
> **Golden attendu : INCHANGÉ.** Pur C# + sérialisation ; le moteur ne change pas.

## Objectif

Boucler la boucle : `DecorLayer` **cesse d'être générateur** et devient consommateur du
snapshot, comme tout le reste de la vue. C'était l'intention explicite de D58·T4 —
`DecorLayer.cs:18-23` documente la couture et la nomme « dette D73 ».

## A. Pont Python → Godot

`data/code/tools/simserver/serialize.py` : bloc `ceinture` au snapshot — 4 secteurs,
champs du §4.1 (`cote`, `type`, `essence`, `hauteur_canopee`, `densite_ligneuse`,
`souche_memory`, `ligne_eau`, `altitude_relative`).

**Compact** : 4 entrées, volume négligeable (contraste avec les 705 Ko du bloc `sprites`
qui avaient imposé un format tableau en 0.2.3 — ici la question ne se pose pas).

`data/code/tools/simserver/version.py` : bump `ENGINE_VERSION` (0.5.40 → **0.5.41**) avec
son commentaire, patron des bumps précédents. Un binaire antérieur n'envoie pas le bloc
⇒ la vue doit **retomber sur le profil local** (voir C) — tolérance, comme tous les bumps.

Commandes d'action : router `abattre`/`receper`/`eteter`/`endiguer`/`deriver`/`entailler`
via `tools/simserver/actions.py` + `actions_cibles.py`, avec une cible **secteur**
(`{"cote": 0..3}`). Patron des cibles existantes.

## B. `DecorLayer` consomme

`visuals/DecorLayer.cs` — **le point d'entrée unique est `BuildProfile(seed)`**, tout est
prévu pour :

1. Ajouter `BuildFromBridge(ceinture)` qui alimente la **même** `SurroundingsProfile`.
   Le commentaire de tête l'annonce mot pour mot (« il suffira d'un second constructeur
   BuildFromBridge(...) alimentant la MÊME struct, sans toucher au rendu »).
2. `BuildProfile(seed)` reste comme **repli** quand le pont ne fournit rien (binaire
   ancien, banc F10). Ne le supprime pas.
3. La struct `Secteur` gagne `DensiteLigneuse`, `HauteurCanopee`, `Essence` — le rendu
   des arbres (`DecorLayer.Arbres.cs`) doit **refléter la densité** : une clairière se
   **voit** (#5). C'est le retour visuel qui rend le geste lisible.

⚠️ **D92** : une fois branché sur le pont, la distribution vient de Python (tronçon ①) et
le hash mal brassé du C# ne sert plus que de repli. Note-le dans le commentaire — la
dette est refermée par le haut, pas corrigée sur place.

## C. Interaction

Clic sur un secteur du décor → gestes disponibles (selon outils possédés), sur le patron
des actions existantes (`WorldView` partials). Le décor est actuellement **hors picking**
(ZIndex négatif) : il faut lui ouvrir une zone cliquable **sans casser** le picking des
plots du jardin.

Retours visuels : clairière (densité ↓), trogne (hauteur ↓, densité conservée), ligne
d'eau qui monte, entaille et éboulis. **Aucun chiffre, aucune jauge** (#5).

## D. Banc F5

`data/code/bancs/peripherie.py` — patron des bancs existants (`bancs/hydrologie.py`,
`bancs/courrier.py`). Une config qui pose une ceinture **contrastée** : forêt dense au
sud (pour voir l'ombre d'hiver et les rafales), rivière à l'est, falaise au nord, friche
à l'ouest — plus les outils déjà en poche, pour que Nico puisse tester les gestes
immédiatement.

Ajoute-le à la palette de configs du pont (`init config="peripherie"`).

## E. Build

`dotnet build Symbiose.csproj` doit être **vert** — c'est le filet de compilation sur la
VM. **Le F5 visuel reste à Nico** (Godot n'est pas sur la VM) : ne prétends pas avoir
validé le rendu.

## Golden

`python3 -m tests.test_golden` → **INCHANGÉ** (rien de tout cela n'est dans le tick).

## Ce qu'il NE faut PAS faire

- **Ne supprime pas `BuildProfile(seed)`** : c'est le repli, et le banc F10 s'en sert.
- **Ne réécris pas le rendu du décor** (D58/D83 sont clos et validés) : tu ajoutes une
  source de données, tu ne refais pas les tracés.
- **Pas de GDScript** — tout en C#, namespace `Symbiose`.
- **Pas de jauge ni de compteur d'impact** à l'écran (#5).
- **Ne prétends pas avoir validé le F5.**
- **N'exécute JAMAIS** `test_epaisseur_500ans`.

## Fin de sprint

Après ce tronçon : mettre à jour `00_etat.md`, `DETTE.md` (D73 close, D92 absorbée, D93
périmée pour ce périmètre, **D94 ouverte** — porosité des haies du jardin), `BACKLOG.md`
et `journal.md`.
