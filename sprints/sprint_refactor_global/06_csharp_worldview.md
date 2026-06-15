# SS⑥ — C# : décomposer WorldView (1759 l)

> Lire `00_etat.md`. Le god-class de la VUE Godot. Risque **moyen** :
> filet = la compilation (`dotnet build`) + lancement F5. On NE change
> aucun comportement de rendu, on réorganise.

## Cible

`world/WorldView.cs` — **1759 lignes**, scène principale (`WorldView.tscn`).
Concentre : projection monde→écran, placeholders tuiles/maison, caméra
(D35), gestion des actions joueur, ombre solaire animée, orchestration du
snapshot du pont, etc.

## Méthode : `partial class` (idiomatique C#/Godot)

`WorldView` est déjà une `partial class` (générateurs Godot). On peut donc
l'étaler sur **plusieurs fichiers** sans rien casser : la scène `.tscn`
référence toujours la même classe.

> **Pédagogie (Nico vient du C/Python)** : `partial` autorise une classe à
> être déclarée dans plusieurs fichiers ; le compilateur les recolle. C'est
> le moyen propre de découper une grosse classe sans extraire de sous-objet.
> Quand un bloc a un état/des données qui lui sont propres (ex. la caméra),
> préférer en faire une **vraie classe/composant séparé** plutôt qu'un
> simple `partial` — meilleure responsabilité unique.

Découpe pressentie (à confirmer en lisant) :
```
world/WorldView.cs            # cycle de vie : _Ready, _Process, état central
world/WorldView.Projection.cs # WorldToScreen + calibrage px/plot
world/WorldView.Camera.cs     # caméra D35 (ou classe Camera dédiée)
world/WorldView.Input.cs      # actions joueur → protocole pont
world/WorldView.Soleil.cs     # ombre solaire animée
world/WorldView.Monde.cs      # placeholders tuiles + maison
```
Arbitrage : si un bloc est cohésif et sans dépendance forte au reste,
**extraire une classe** (`CameraController`, `SoleilAnimateur`) plutôt qu'un
`partial`. Chaque fichier < 500 l code, commentaires pédagogiques conservés.

## Vérification

```
dotnet build Symbiose.csproj      # compile sans erreur ni warning nouveau
```
Puis **F5 dans Godot** (ou demander à Nico) : le monde s'affiche, caméra,
ombre solaire, actions joueur fonctionnent comme avant. Comparaison
visuelle = critère (refactor pur).

## Définition de fait

- [ ] `WorldView` réparti en fichiers < 500 l chacun (partial + classes
      extraites le cas échéant).
- [ ] `dotnet build` OK ; scène `WorldView.tscn` toujours liée à la classe.
- [ ] F5 : comportement de rendu identique (validé par Nico si besoin).
- [ ] `00_etat.md` mis à jour → commit → `/clear`.

## Commit suggéré

`refactor(sprint·global) : SS⑥ — WorldView (1759 l) décomposé en partials/composants, rendu inchangé`
