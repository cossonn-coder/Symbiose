# Tronçon ④ — Vue Godot : encart « état du ciel » + couvertures + banc F5

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` + ce fichier suffit.
> Spec : `docs/champs/climat/conception_effondrement_meteo.md` (§5, §7).
> Tronçon vue OBLIGATOIRE de clôture (règle CLAUDE.md : tout sprint finit par la vue).

## Objectif (exigence Nico)
Un **petit encart affichant l'état du ciel**, qui permet d'**anticiper la météo de
la semaine suivante**. + rendu des couvertures (③) + banc d'observation F5 du
collapse. Le pont exporte, Godot affiche — la vue ne calcule rien.

## Contrainte philo #5 / §4 — l'encart est DIÉGÉTIQUE
**PAS un widget de prévision chiffrée** (« Semaine +1 : 🌧 70 % » = interdit). C'est
une **fenêtre rapprochée sur le ciel** : couleur, nuages, halo lunaire, brume,
lumière. Le joueur **lit le ciel** comme un vrai jardinier. L'encart **condense** les
signes de `ciel_semaine` (helper Python du tronçon ②) et **s'assombrit visiblement
à l'approche du composé catastrophe** (niveau de convergence de ②) — le préavis
dramatique rendu perceptible AVANT que le jardin soit frappé.

- **Masque de maîtrise** (§4.2) : l'encart montre TOUJOURS le ciel (signal parfait) ;
  ce qui dépend du palier, c'est si le carnet/l'encart **nomme** ce qu'il annonce
  (« ciel blanc laiteux → canicule probable » à la maîtrise ; brut avant). Le flag
  de nommage vient du palier maîtrise climat (D12), déjà exposé côté pont — vérifier.

## À FAIRE
### (a) Pont — exporter `ciel_semaine`
`tools/simserver/serialize.py` : sérialiser la structure `ciel_semaine` (② l'a
rendue prête). Read-only. Bumper la version de protocole du pont (cf. historique des
versions dans `serialize.py` / `SimBridge.cs`).

### (b) Godot — encart « état du ciel »
Scène/nœud C# (namespace `Symbiose`, `res://`) : un petit panneau qui rend le ciel
depuis les données du pont (couleur de fond, sur-couche nuages/halo/brume, teinte
qui s'assombrit avec la convergence). Nommage conditionné au palier. **Un fichier =
une responsabilité** (garde-fou taille CLAUDE.md). Se rattacher à l'UI existante
(hub-maison / panneaux carnet du sprint voix narratives) plutôt que réinventer.

### (c) Rendu des couvertures
Placeholders procéduraux pour voile / cloche / ombrière (③), comme les placeholders
tuiles/maison de `WorldView` — pas besoin d'assets, juste une silhouette lisible.

### (d) Banc d'observation F5
Un scénario reproductible du collapse connu (seed 12345, an 26, tuile 16×11) où Nico
voit, à l'écran : l'encart **virer au plomb** à l'approche, puis la **zone abritée
survivre** pendant que l'exposée meurt. C'est la preuve visuelle de l'hétérogénéité
(①) + du préavis (②) + de l'utilité des couvertures (③).

## Golden
**INTACT.** Pure vue + pont read-only ; aucune règle de simulation touchée. Le
`dotnet build Symbiose.csproj` sur la VM est le filet de compilation (le F5 visuel
reste à Nico).

## NE PAS faire
- Pas de chiffre / barre / icône calendrier dans l'encart (philo #5) — diégétique.
- Ne pas recalculer côté Godot ce que `ciel_semaine` fournit déjà (pont → affichage).
- Ne pas modifier la simulation (①/②/③ l'ont fait) ni re-figer le golden.
- Pas de GDScript (C# uniquement). Ne pas lancer `test_epaisseur_500ans`.

## Points F5 (pour Nico, après le tronçon)
- L'encart se lit-il d'un regard ? S'assombrit-il assez tôt / assez nettement ?
- La zone abritée survit-elle visiblement au banc collapse ?
- Le nommage au palier maîtrise arrive-t-il au bon moment ?
