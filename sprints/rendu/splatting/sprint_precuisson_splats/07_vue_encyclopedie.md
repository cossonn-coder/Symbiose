# ⑦ Vue Godot : portraits dans l'encyclopédie et le magazine (dernier tronçon)

Lire d'abord `docs/rendu/splatting/conception_precuisson_splats.md` (D6) et
`00_etat.md` (manifeste des portraits du ⑥, chargement choisi au ④).

## Existant (vérifié 2026-11-20)
- `world/EncyclopediePanel.cs` : fiche lue du pont (`Bridge.Encyclopedie(cle)` →
  `{cle, type, niveau_max, niveaux, …}`, en-tête l. 18-23) ; plantes = fiches à 3
  niveaux (titres `TitresNiveau`) ; animaux/champignons = mono-niveau.
- `world/MagazinePanel.cs` (offres d'achat), `world/CarnetPanel.cs`.

## Objectif
1. **Encyclopédie** : la fiche d'une plante affiche le portrait du niveau atteint
   (D6) — niveau 1 : jeune ; niveau 2 : mûre ; niveau 3 : fin de cycle (les
   trois visibles au niveau 3, ou le plus avancé — choisir le plus lisible et le
   dire). Une espèce jamais vue n'a pas de portrait. Le niveau atteint vient du
   pont existant : **aucune clé de pont nouvelle** sauf nécessité démontrée (alors
   bump `data/code/tools/simserver/version.py`, snapshot comparé avant/après).
2. **Magazine** : une offre d'espèce montre son portrait mûr.
3. Pixel-art respecté : affichage à échelle entière, filtre Nearest.
4. Captures VM des panneaux (si `tools/capture_vm.sh` sait ouvrir un panneau ;
   sinon le dire et laisser le contrôle au F5).
5. Clôture du sprint : `00_etat.md` (§F5 complète pour ④⑤⑦), `DETTE.md` /
   `BACKLOG.md` (fragment `docs/rendu/splatting/backlog_splatting.md`), entrée de
   `journal/` + ligne dans `journal.md`.

## Golden
**INTACT**. `dotnet build` vert.

## Ne PAS faire
Changer le contenu textuel des fiches ; toucher au moteur ; refaire les portraits.

## F5
Ouvrir l'encyclopédie sur une espèce à chaque niveau, et le magazine : le portrait
apparaît, change avec le niveau, reste net.
