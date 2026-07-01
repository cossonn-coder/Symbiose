# 2026-07-01 — Sprint UI des VOIX NARRATIVES (①→④) — SPRINT TERMINÉ

> Exécution autonome `/sprint-auto sprint_voix_narratives_ui`. Rend **jouables**
> les 4 voix narratives dont le moteur Python était 100 % fait (sprint VOIX
> ①→⑥, 2026-06-29). Conception figée = `docs/conception/CONCEPTION_VOIX_NARRATIVES_UI.md`.
> **INVARIANT gravé** : l'UI restitue le corpus **verbatim** depuis Python, zéro
> phrase générée côté C# — le C# ne fait que de la mise en page.

## Golden — INTACT bit-identique sur TOUT le sprint : `ae445d3f…`
Le pont vit hors du golden (hors-serveur, opt-in joueur) ; le C# est une couche
vue ; le tick moteur n'est jamais touché. Aucun re-figeage, comme prévu par le
kickoff.

## Tronçons

- **① Pont Python** (`b1ff45c`) — chaîne de maîtrise 3 hooks branchée au driver :
  hook A `observer` (espèces vivantes post-tick + concepts eau/lumière/météo/
  pollinisation lus du log), hook B `detecter` (crédit palier), hook C
  `noter_geste` (dans `cmd_action`) ; révélation page « récompense » au palier 3.
  4 commandes read-only verbatim (`carnet`/`encyclopedie`/`pages`/`magazine`,
  `VoixMixin` dans `tools/simserver/voix.py`) + module dédié
  `tools/simserver/maitrise_pont.py`. Verbe `acheter_magazine` (chemin Vigueur
  unique Q3). Protocole `0.5.10 → 0.5.11`. Suite `sim_server` **219/219**.
  Effet de couplage voulu signalé : la chaîne crédite de VRAIS paliers ⇒
  `vigueur_max` monte et `cout_action` remise les coûts → 5 assertions de coût
  absolu rendues robustes (débit = cost annoncé, ratio urgence 1.5, régen ≥ +10).

- **② Ossature UI Godot** (`9e69e35`) — `core/SimBridge.cs` gagne une méthode par
  commande de pont voix (relais verbatim). Nœud `world/VoicePanel.cs` réutilisable
  (plein écran, **pause-aware** : mémorise/restaure `GetTree().Paused`,
  `ProcessMode=Always`). Hub-maison **cliquable** (`world/WorldView.Hub.cs`) :
  clic maison → menu 5 fonctions, 4 voix actives ouvrent un `VoicePanel` titré,
  Atelier/Semis/Foyer grisés « (à venir) » (D54). Détection clic = rectangle
  d'empreinte au sol (pas d'Area2D). `dotnet build` vert.

- **③ Carnet + Encyclopédie** (`43db11f`) — `CarnetPanel` : sélecteur de concept
  re-appelant le pont (le **filtre est côté Python**), entrées verbatim, registre
  interprétatif en italique BBCode (crochets échappés `[`→`[lb]`). `EncyclopediePanel` :
  index cliquable → fiche niveaux `1..niveau_max` verbatim → retour. `VoicePanel`
  gagne un hook `Remplir()` virtual + injection `Bridge`. Étiquettes de rubrique
  (« N1 — Observation… ») = mise en page structurelle, pas des voix. `dotnet build` vert.

- **④ Pages + Magazine** (`eea3693`) — `PagesPanel` : lecteur pur du coffret grenier
  (pages trouvées verbatim, en-tête voix·concept, corps italique), aucune
  révélation côté C#. `MagazinePanel` : offres → fiche produit verbatim → achat
  bout-en-bout via `acheter_magazine` (Vigueur unique) ; succès retire l'offre +
  rafraîchit le bilan, refus sobre — **le pont gate tout, la vue ne pré-valide
  rien**. `dotnet build` vert.

## Taille des fichiers (fin de sprint)
Aucun fichier en zone rouge (> 400 LDC pur) ⇒ refactor auto-léger = no-op. Le
plus haut : `tools/simserver/actions.py` à **359** (🟡 vigilance, responsabilité
unique = pont d'actions, +49 lignes au ①) — **point de vigilance** pour un futur
sprint (extraire le helper hook-C). `core/SimBridge.cs` = 194 (🟢).

## Reste
- **F5 = Nico** : depuis le hub-maison (5 entrées, 3 grisées) — Carnet (liste +
  filtre concept, interprétatif en italique), Encyclopédie (index → fiche
  N1/N2/N3), Pages (coffret), Magazine (offres → fiche → achat qui débite la
  Vigueur et ajoute la graine à la banque). Affiner éventuellement la zone
  cliquable maison (empreinte au sol vs façades) et le wrap des textes longs.
- **Dette D54** (reliquats hors sprint) : HUD primaire philo #5, page d'accueil
  pictos, notifs temps réel, robinets pages hasard/fouille + marqueurs
  bouture/oiseau/vent, entrées hub Atelier/Semis/Foyer, corpus encyclo paliers 4-5.
