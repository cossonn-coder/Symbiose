# ⑥ Vue Godot — automate en F5 + journal/impasses + onglet objectifs

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` +
> `docs/conception/CONCEPTION_JARDINIER_AUTOMATE.md` (§2 H3, §6, §8). Prérequis :
> ①→⑤ faits. **RÈGLE PERMANENTE** : tout sprint se termine par un tronçon vue Godot.

## Objectif
Rendre l'automate **observable en F5** : le brancher dans la boucle de `sim_server`
(option opt-in), exposer sa **trace** et ses **objectifs** au snapshot, et les
afficher côté Godot (retour visuel des gestes joués + journal/impasses + onglet
objectifs). **Golden neutre** (aucune écriture de tick).

## Partie Python (pont) — `data/code/tools/`
- Lire d'abord `tools/sim_server.py`, `tools/simserver/server.py`,
  `tools/simserver/actions.py` (dispatch `cmd_action`) et `tools/simserver/serialize.py`
  (snapshot) pour le protocole réel.
- **Brancher l'automate** dans `cmd_step_week` (ou l'équivalent qui appelle
  `engine.tick_semaine()`) : APRÈS le tick, SI un automate est actif pour la session,
  appeler `automate.jouer_tick(engine)`. Opt-in strict (aucun automate par défaut →
  comportement F5 actuel inchangé).
- **Commande de contrôle** : ajouter une commande pont (ex. `cmd_automate`) pour
  activer/désactiver l'automate et régler son profil (`ProfilAutomate`) + ajouter un
  objectif en phase de planification. Versionner le protocole du pont (bump mineur,
  cf. `tools/simserver/version.py`).
- **Expo au snapshot** (`serialize.py`) : ajouter au snapshot, opt-in, la **trace**
  récente (`game_state["automate_journal"]`) et les **objectifs actifs** +
  progression + l'**onglet** courant. Ne rien exposer si l'automate est inactif
  (snapshot inchangé → pas de casse pour la vue existante).

## Partie Godot (vue) — `Symbiose/` (C#, namespace `Symbiose`)
- Lire `world/WorldView.cs` (+ ses partials) et `core/SimBridge.cs` pour le point
  d'insertion (réception du snapshot).
- **Retour visuel des gestes** : à chaque geste consigné dans la trace du snapshot,
  un marqueur/surbrillance éphémère au plot/plante concerné (ligne de log défilante
  suffit pour une v1 — confort de débogage, pas un chef-d'œuvre).
- **Panneau journal/impasses** : un panneau texte listant les dernières entrées de
  trace + les impasses (les « trous de gameplay » sautent aux yeux).
- **Onglet objectifs** : un onglet listant les objectifs actifs, leur progression
  (n/quantité), et le journal filtré de l'objectif sélectionné.
- Respecter : GDScript INTERDIT (tout C#), un fichier = une classe/concept, ≤ 300
  LDC (scinder en partials si besoin). **`dotnet build Symbiose.csproj`** doit passer
  (filet de compilation VM). Le **F5 visuel reste à Nico**.

## Golden attendu
**NEUTRE / INCHANGÉ.** L'automate reste hors tick ; le snapshot n'expose que du
read-only opt-in. `python3 -m tests.test_golden` inchangé.

## Ce qu'il NE faut PAS faire
- NE PAS faire jouer l'automate depuis le tick moteur. NE PAS créer de geste.
- NE PAS implémenter le panneau de QUÊTES diégétiques (D79) — ici c'est l'onglet
  objectifs MÉCANIQUE (geste+quantité+cible) seulement.
- NE PAS casser le snapshot existant (tout ajout est opt-in). NE PAS lancer
  `test_epaisseur_500ans`.

## Points F5 (à valider par Nico)
- L'automate tient-il visiblement le jardin (arrosage/paillage/récolte visibles) ?
- Le journal et les impasses sont-ils lisibles ? L'onglet objectifs progresse-t-il ?
- Perf F5 acceptable en régime tenu (lien avec le verdict Q9 du banc ⑤) ?

## Vérif de sortie
`dotnet build Symbiose.csproj` OK + `python3 -m tests.test_golden` inchangé + pont
versionné. Marquer dans `00_etat.md` les points à valider en F5 par Nico. Ce tronçon
CLÔT la chaîne obligatoire (⑦ semiologique reste optionnel).
