# Tranche 3 — Saison animée (le monde se met à vivre)

> **Kickoff autosuffisant.** Lire d'abord `00_etat.md` (Option B actée ;
> tranches 1-2 CLOSES : le pont `sim_server.py` ↔ `SimBridge.cs` fonctionne et
> `WorldView` affiche le monde complet — 1188 plots placeholder, maison,
> ~152 plantes, confirmé F5). But de la tranche : implémenter la **boucle
> hybride** côté vue — phase **planification** (temps figé) ↔ phase **saison**
> (temps réel, 1 semaine = 60 s), le visuel se met à jour à chaque snapshot
> hebdomadaire **sans geler l'affichage**. Pas d'actions joueur (tranche 4),
> pas d'organes/overlays (tranche 5). Ampleur : **moyen** — en principe
> **1 seul fichier modifié** (`world/WorldView.cs`) + docs ; **zéro Python**
> (le protocole v0 suffit : `step_week` existe déjà).

## 📖 Pédagogie — les deux problèmes de la tranche

**1. Le tick bloque, l'écran non.** `SimBridge.StepWeek()` est SYNCHRONE et
prend ~150 ms (VM) à ~290 ms (poste Nico, mesuré t2 : 3451 ms / 12 sem). Sur
le thread principal, ça gèle l'affichage le temps du tick — un hoquet visible
à chaque semaine. Solution = **déporter la requête hors du thread d'affichage**
(analogie embarqué : on ne fait pas une transaction UART bloquante dans l'ISR
d'affichage ; on la lance, on continue, on récupère le résultat au prochain
tour de boucle). En C#/Godot :

```csharp
_pendingStep = System.Threading.Tasks.Task.Run(() => _bridge.StepWeek());
// ... et dans _Process(delta) :
if (_pendingStep != null && _pendingStep.IsCompleted)
{ ApplySnapshot(_pendingStep.Result); _pendingStep = null; }
```

Règles de sécurité absolues : **(a)** ne JAMAIS toucher l'arbre de scène
depuis la Task (le résultat est consommé dans `_Process`, sur le thread
principal) ; **(b)** UNE seule requête en vol à la fois (le protocole du pont
est maître/esclave 1↔1 — deux écritures concurrentes sur le pipe le
corrompraient). Le pattern « une Task à la fois, pollée dans `_Process` »
garantit les deux par construction.

**2. La sim est discrète, le temps est continu.** Le moteur avance par pas
d'UNE semaine ; le joueur voit un horloge continue. La vue tient donc un
**accumulateur de temps** : `t += delta` chaque frame ; quand `t ≥
SecondsPerWeek` ET qu'aucun step n'est en vol → lancer le step suivant.
L'interpolation FINE entre deux snapshots (faire « pousser » les segments en
continu par tweens) est **différée** : à 60 s par semaine le changement est
lent, un swap sec suffit largement en t3 — on se contente d'un **fondu**
d'apparition/disparition des plantes (naissances/morts visibles sans pop).

## État de départ (acquis t1-t2)

- `core/SimBridge.cs` : `Init/StepWeek/GetSnapshot/Quit` synchrones, snapshot
  = horloge (`week`, `week_in_year`, `year`, `season`) + plantes (`tile`,
  `species`, `name`, `x_cm`/`y_cm` locaux, `stage`, `height_cm`, `segments`).
- `world/WorldView.cs` (scène principale) : `_Ready` = Init("full") →
  StepWeek×`WarmupWeeks` → `BuildGround` (statique, ne bouge jamais) /
  `BuildHouse` (statique) / `SpawnPlants(world, snap)` (à re-générer chaque
  semaine) ; process Python laissé ouvert, `Quit()` sur `_ExitTree`.
- Calendrier moteur : 52 semaines/an, saisons de 13 semaines
  (`saison_de`, sim/engine.py) — le **passage de saison** se détecte quand
  `season` du snapshot change.

## Livrables (tout en C#, `WorldView.cs`)

1. **Machine à deux états** : `Planification` (défaut au lancement, temps
   figé, rien ne tourne) ↔ `Saison` (temps réel). Bascule au clavier :
   **Espace** = lancer la saison / pause / reprise (`_UnhandledInput` ;
   les vrais boutons UI viendront avec le sprint UI).
2. **Avancement temps réel** : accumulateur dans `_Process` ;
   `[Export] SecondsPerWeek = 60` (réglage design 30-180 s) +
   `[Export] DebugSecondsPerWeek` (ex. 3 s, utilisé si > 0) — sans ça, tester
   une saison = 13 min de patience.
3. **Step en arrière-plan** : `Task.Run(StepWeek)` + poll `IsCompleted` dans
   `_Process` (cf. pédagogie). Une seule requête en vol. Si la Task échoue
   (moteur mort), retour en `Planification` + erreur console.
4. **`ApplySnapshot(snap)`** : régénère le conteneur des plantes (détruire/
   recréer les `PlantRenderer` — ~150 nœuds, trivial à 1 fois/60 s) ; **fondu**
   d'apparition pour les nouvelles plantes et de disparition pour les
   disparues (Tween sur `Modulate.A`, comparaison par clé
   `tile+species+x_cm+y_cm`). Sol et maison ne bougent pas.
5. **Fin de saison** : après la 13ᵉ semaine de la saison (le `season` du
   snapshot change), retour **automatique** en `Planification` +
   `GD.Print` du passage (« été, an 1 ») + **hook `OnSeasonEnd()` vide avec
   TODO auto-save** (l'auto-save réel = sprint save global ; le protocole v0
   n'a pas de commande `save`, on ne l'invente pas ici).
6. **Affichage d'horloge provisoire** : un `Label` discret (coin d'écran,
   `CanvasLayer`) « printemps · an 1 — semaine 5/13 » + état (« — saison en
   cours / ⏸ pause / planification »). Étiqueté provisoire : le HUD définitif
   (philo #5, pas de chiffres) viendra au sprint UI ; ici c'est l'instrument
   de validation de la tranche.

## Critères de succès (vérifiables, F5 Nico)

- [ ] Au lancement : monde t2 affiché, état `Planification`, rien ne bouge.
- [ ] **Espace** → la saison démarre : la semaine avance toutes les
      `DebugSecondsPerWeek` s, l'horloge se met à jour, les plantes
      évoluent (pousses qui apparaissent en fondu, mortes qui s'effacent).
- [ ] **Aucun gel perceptible** au moment des ticks (step en arrière-plan).
- [ ] **Espace** pendant la saison → pause (l'horloge s'arrête) ; re-Espace
      → reprise.
- [ ] Au changement de saison : retour automatique en `Planification`,
      message console, hook `OnSeasonEnd` appelé.
- [ ] `python3 -m tests.test_golden` **inchangé** (`16a1b937…`) — aucun
      fichier Python touché, vérification de principe.

## Points ouverts (défaut sobre + signaler)

- **Interpolation fine de croissance** (tweens sur les segments) : différée —
  fondu naissance/mort seulement en t3. À réévaluer en t5 (organes).
- **Warmup au `_Ready`** : conservé (12 semaines) pour démarrer sur un monde
  visible. Quand le vrai « démarrage du jardin » (3 écoles) arrivera, il
  sautera.
- **`WarmupWeeks` vs phase saison** : le warmup consomme des semaines du
  calendrier (on démarre semaine 13) — assumé en t3, le vrai flux de partie
  viendra avec le save global.
- **Vitesse pendant la pause Python** : en `Planification` le process Python
  est au repos (aucune commande) — c'est le mapping prévu de la boucle
  hybride, rien à faire.

## Dette / liens

- Ne touche PAS à **D35** (contrôles caméra : déplacement, zoom paliers,
  rotation par quarts de tour) — tranche/sprint dédié après t4.
- Prépare la **t4 (actions joueur)** : la machine à états Planification/Saison
  est exactement la structure qui distinguera actions « préparation »
  (planification, coût modéré) et « réaction » (saison, coût élevé).
- L'auto-save reste au **sprint save global** (hook posé ici).

## Boucle de travail (rappel)

Travailler (`WorldView.cs` seul en principe) → golden vérifié par principe →
F5 Nico (critères ci-dessus, avec `DebugSecondsPerWeek`≈3) → mettre à jour
`00_etat.md` (tranche 3 ✅ + décisions) → entrée `journal.md` → commit →
`/clear` → tranche 4 (kickoff `04_actions_joueur.md` à écrire avant).
