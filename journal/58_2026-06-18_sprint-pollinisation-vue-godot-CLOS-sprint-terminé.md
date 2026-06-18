# 2026-06-18 — Sprint POLLINISATION & CYCLE DE VIE · vue Godot — SPRINT TERMINÉ

> Suite directe de l'entrée [#57](57_2026-06-18_sprint-pollinisation-implémentation-①-⑦-CLOS-moteur.md)
> (moteur ①→⑦ clos). Conception figée :
> `docs/conception/CONCEPTION_POLLINISATION_CYCLE_VIE.md` (§F/§H/§I/§J).
> Mémoire : [[design_pollinisation_cycle_vie]].

Le §Reste du moteur (« vue Godot, hors VM, F5 Nico ») est livré et **confirmé F5
le 2026-06-18**. Aucune ligne Python touchée → **golden INTACT** `4f9fad91…1260`,
`population_hash` inchangé `71f7ddda…`. Commit `9b534ee` (682 insertions, 10 fichiers
C#/état, 0 Python).

## Livré (vue pure, lit le snapshot)

- **`visuals/ForagerLayer.cs` NEUF** — butineurs abeille/syrphe/papillon dessinés en
  AGENTS fleur-en-fleur (bloc snapshot `foragers`, pont 0.3.9). Saut entre fleurs
  conspécifiques voisines via index `_plantsByName` (clé = `name` FR, **≠** `species`
  anglais — piège évité). Point de pollen sur le dos quand l'agent porte ; **dépôt de
  pollen sur les fleurs butinées** par atterrissage, accumulé/capé par saison, vidé à
  `OnSeasonEnd`. LOD ×4 + culling.
- **`visuals/MacroLife.cs`** — abeille/syrphe/papillon RETIRÉS du nuage de densité
  (`NonDessine`) : ils vivent désormais dans `ForagerLayer` (pas de double affichage).
- **`visuals/PiqureFlash.cs` + `world/WorldView.Piqure.cs` NEUFS** — **piqûre temps
  réel « vue pure »** (§J.2 délégué à Godot) : accumulateur déterministe
  `taux × alarme × densité abeille` (alarme lue au snapshot 0.4.1, densité dans
  `ForagerLayer`), **coût Vigueur LOCAL** (écrasé au prochain snapshot, pas de retour
  moteur), éclat éphémère. Câblé chaque frame en phase Saison.
- **`world/WorldView.Compost.cs` + `visuals/CompostStructure.cs`** — ruche dessinée
  (3 hausses iso, remplissage miel + abeilles au trou de vol ; `essaim`/`miel` du pont
  0.4.0). `WorldView.Snapshot.cs` désérialise les blocs `foragers`/`alarme`/`structures`.
- Calibrages exposés si retouche : `HopSec` (par guilde), `MaxPollenPerFlower`,
  `TauxPiqure` / `CoutPiqure` / `RayonPiqureCm`.

## Assumé NON fait

Sprites larves/chenilles : `eco.larvae` n'est pas exposé au snapshot (décision de
périmètre — hook futur si besoin).

## Clôture

**SPRINT POLLINISATION & CYCLE DE VIE TERMINÉ** (moteur ①→⑦ + vue Godot). Sprint
déplacé sous `sprints/_clos/sprint_pollinisation_cycle_vie/`.
