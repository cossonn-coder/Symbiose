# Tronçon 04 — Vue Godot : Atelier + menu gestes

> Tu démarres À FROID. Lis `CLAUDE.md`, `00_etat.md`, puis
> `docs/conception/CONCEPTION_ACQUISITION_OUTILS.md` §B/§C. **Tronçon vue
> obligatoire** (règle 2026-07-03 : tout sprint finit par sa vue). Le F5 visuel
> reste à Nico ; toi tu poses le C# + le pont et valides le build
> (`dotnet build Symbiose.csproj`, filet de compilation sur la VM).

## Objectif
Rendre jouables depuis Godot les moyens d'agir ajoutés aux tronçons 01-03 :
1. **Atelier cliquable** dans le hub-maison, exposant **outils** (sécateur) +
   **matériaux** (botte de paille) à acquérir contre Vigueur.
2. **Menu gestes plante** enrichi : `pincer` / `arracher` (toujours), plus
   `couper` / `tailler` (visibles une fois `posseder_secateur` acquis).
3. **Menu milieu** : `glaner` (sur un plot).
4. **Pont** des nouveaux verbes (`acheter_outil`, `acheter_materiau`, `pincer`,
   `arracher`, `glaner`).

## Patron à réutiliser
- **Panneaux du hub-maison (D54)** : les 4 fonctions Carnet/Encyclopédie/Pages/
  Magazine sont déjà des panneaux cliquables ouverts depuis la maison. L'**Atelier**
  est la 5e fonction, non câblée → ajoute son panneau sur le MÊME patron (le
  Magazine, qui présente une offre + bouton d'achat Vigueur, est le modèle le plus
  proche : l'Atelier présente `offre_outils` + `MATERIAUX`).
- **Menu de gestes** : là où `couper`/`tailler`/`bouturer` sont déjà proposés sur
  une plante (côté C#, action menu contextuel) → ajoute `pincer`/`arracher` ; masque
  `couper`/`tailler` tant que le snapshot n'indique pas le sécateur possédé.
- **Pont** : `SimBridge.cs` + protocole côté Python déjà bumpé aux tronçons 02/03.
  Le snapshot doit exposer l'état « sécateur possédé » (dérivable des marqueurs
  d'action du joueur) et l'offre Atelier — ajoute au sérialiseur si absent
  (`tools/simserver/serialize.py`, lecture PURE → golden neutre).

## Fichiers (indicatifs — vérifie les noms réels côté C#)
- `world/WorldView*.cs` (partials) ou le module de hub-maison : ouverture du
  panneau Atelier au clic sur la maison.
- Le panneau C# de l'Atelier (nouveau, calqué sur le panneau Magazine).
- Le menu d'actions plante/plot : entrées `pincer`/`arracher`/`glaner`.
- `SimBridge.cs` : envoi des verbes ; `serialize.py` : exposer possession sécateur
  + offres si besoin.
- `world/WorldView.cs` : mets à jour la constante `Build` (témoin de synchro F5).

## Golden
**INCHANGÉ.** Aucune logique de simulation ici (vue + pont, lecture pure).
`python3 -m tests.test_golden` reste figé. Le C# doit builder :
`dotnet build Symbiose.csproj` (filet VM ; PAS de Godot système).

## Points F5 (pour Nico)
- Ouvrir l'Atelier, acquérir le sécateur (Vigueur débitée), vérifier que
  `couper`/`tailler` apparaissent ensuite sur une plante.
- `pincer` / `arracher` disponibles d'emblée (avant tout outil).
- `glaner` sur un plot avec litière crédite du mulch, puis `pailler` marche.
- Acheter une botte de paille à l'Atelier → `pailler` possible sans avoir rien
  cultivé.

## NE FAIS PAS
- Ne touche pas le moteur (tronçons 01-03 font foi) ni le golden.
- N'invente pas de verbe non prévu par le pont.

## Fin de tronçon
Mets à jour `00_etat.md` (sprint CLOS côté code, reste F5 Nico), commit
(`feat(moyens) ④ : vue Godot Atelier + gestes manuels + glaner`), et signale à Nico
les points F5 ci-dessus. Sprint « acquisition des moyens d'agir » terminé.
