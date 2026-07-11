# 2026-07-11 — Sprint SOMMET TROPHIQUE (T1+T7) — CLOS (`/sprint-auto`)

Exécution des 3 tronçons figés par la conception du même jour (entrée 114).
Comble les 2 trous couplés du référentiel D61 : **super-prédateur (T1/D1)** +
**herbivore vertébré (T7/B4)**. Golden re-figé maîtrisé ①②, vue Godot ③ intacte.

## ① campagnol proie + dégât racinaire dédié (`10c4a09`)
- **`campagnol`** : catégorie NEUVE `herbivore_vertebre` (canal distinct de
  `ravageur` foliaire), TrophicSpec `resource_fn=_racine_grid` (biomasse
  `root_plots` pondérée par palatabilité familiale + bonus ligneux jeune),
  habitat = galeries (sol non remué), `predators=()` encore (puits reportés à ②),
  salt dédié.
- **Perturbation `root_herbivory`** : morsure **probabiliste −1**
  (`_hash_noise(seed, week·43, …)`, LÉTAL −2 pour ligneux jeune annelé, cappée
  `_cap_chronique`). Calibrage : passée de binaire à probabiliste pour éviter une
  hécatombe du pommier.
- **Signe `rongeur_racinaire`** (sémiologie + carnet) + les 5 voix (encyclopédie
  faune, interconnexions rapace/couleuvre).
- **Golden RE-FIGÉ #1** `817cd77298678302516e0632ac97d8145482bd6d239b47de2ef824a784dd0f09`.
  **Dérive prouvée localisée** : neutraliser `root_herbivory` retombe EXACTEMENT
  sur l'ancien golden → la dérive vient uniquement du dégât voulu (pic densité
  0.136, pommier survit). `population_hash` re-capturé.

## ② rapace + couleuvre ferment le sommet (`b8f8a78`)
- **`rapace`** (0x2B0001) + **`couleuvre`** (0x2B1001) : catégorie
  `super_predateur`, insérées **EN DERNIER** dans l'ordre de tick (lisent leurs
  proies fraîches → décalage d'inertie = boom-bust).
- **Puits top-down câblés** : campagnol←(rapace,couleuvre), merle←rapace,
  limace←(+couleuvre). Sous-graphe trophique **symétrique** (invariant testé :
  tout `predators` ⊂ `interconnexions`). 5 voix, blurbs + interconnexions
  réciproques.
- **Décision de design (dans le périmètre, philo #2)** : le modèle générique fait
  `capacité = res + hab` (additif) — un habitat de super-prédateur (terrain
  ouvert ≈ 1.0 sans plantes) l'aurait fait décoller SANS proie (anti-écologique).
  Corrigé : terrain = **modulateur MULTIPLICATIF** de la proie
  (`_proies_grid(noms, habitat_fn)`, `habitat_w=0`) → sommet strictement piloté
  par le bas.
- **Golden RE-FIGÉ #2** `eb46b49deef4590f0b5f44ce0309c0c09bbbd3d9f536aa039ba80108bc25dd5c`.
  **Dérive prouvée** : ôter les seuls puits fait retomber EXACTEMENT sur le golden
  ① `817cd772…` → dérive = uniquement la régulation top-down. `population_hash`
  re-capturé `2431b6b153…`.

## ③ vue Godot sprites par espèce + signe racinaire (`47f2c0a`)
- **`MacroLife.cs`** + **`FieldOverlay.cs`** : `campagnol`/`rapace`/`couleuvre`
  ajoutés à la table sprite par espèce (patron ⑥b). Rongeur brun-roux au sol
  (errance courte), rapace fauve aérien (errance large), couleuvre olive ondulée
  lente. Le pont émet déjà ces espèces → **0 modif Python**.
- **Signe `rongeur_racinaire`** mappé : colorant `Palette16.SymRongeurRacinaire`
  (`b39244`, jaune-brun « flétri par le collet ») + entrée `ColorantTints` de
  `PlantRenderer`. **Canal COULEUR** (colorant), distinct du criblage foliaire du
  ravageur (canal texture) — la cause souterraine s'infère (philo #5/#6).
- **Encyclopédie** : aucun code C# neuf (`EncyclopediePanel` data-driven → les 3
  fiches apparaissent automatiquement).
- **Golden INTACT** `eb46b49d…` (tronçon C# pur, pont inchangé 0.5.26),
  `dotnet build` **vert**.

## Bilan
- **T1 + T7 → ✅** dans le référentiel D61 (`CONCEPTION_COMPLETUDE_ECOSYSTEME.md`
  §B4/§D1 + tableau des trous). D61 marqué FAIT (reste F5).
- **Golden final** `eb46b49deef4590f0b5f44ce0309c0c09bbbd3d9f536aa039ba80108bc25dd5c`.
- **Refactor auto-léger no-op** : `resources.py` 349 LDC pur = 🟡 vigilance mais
  sous le seuil rouge 400 (responsabilité unique, signalé, pas de split).
- **Reste F5 Nico** : sprites campagnol (au sol sur monticules à racines) / rapace
  (en vol) / couleuvre (près des piles au soleil) ; plante rongée au collet
  lisible et distincte du criblage foliaire ; boom-bust top-down visible dans la
  durée.
