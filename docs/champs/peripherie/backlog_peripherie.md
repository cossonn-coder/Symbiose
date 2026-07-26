# Backlog — peripherie

> Fragment de [`BACKLOG.md`](../../../BACKLOG.md) — les entrées de sprint qui
> concernent ce thème, reprises **verbatim**. L'index global des thèmes et
> les kickoffs de dette dormante restent à la racine.

| Sprint | Fichier kickoff |
|---|---|
| **Sprint PÉRIPHÉRIE — le jardin n'est pas une île (D73)** — ✅ **CONCEPTION FIGÉE 2026-07-26** (`/conception`, à partir de l'amorce de Nico du même jour) → spec `docs/champs/peripherie/conception_peripherie.md`. Fait passer le décor d'ambiance (D58, cosmétique) au statut de **matière écologique** : la périphérie agit sur le jardin, puis le joueur agit sur la périphérie. **Ceinture = 4 secteurs cardinaux en vérité Python** (`fields/peripherie.py`), la vue devient consommatrice du snapshot (la couture `SurroundingsProfile` de D58·T4 était écrite pour ça). Flux entrants : **ombre de lisière** (obstacle en coordonnées MONDE, patron de la maison — à 49°N une forêt au sud donne 47 m d'ombre en hiver, 7 m en été, gratuitement via `solar_slice`), **abri + turbulence** (`fields/abri.py`, porosité φ : réduction linéaire du vent moyen, **rafale quadratique** — une lisière trop dense abrite du vent constant mais fait tomber des rafales, la leçon centrale), **pluie de graines** (support enfin donné au canal d'acquisition #3), **nappe de berge** (condition aux limites, PAS une rivière simulée), **corridor** (`eco.lisiere` + `lisiere_w` par spec, jamais un bonus d'habitat). Gestes : `abattre` / `receper` / `eteter` (le hêtre et le bouleau **ne rejettent pas** de souche — charme, aulne, saule oui) / `endiguer` / `deriver` / `entailler` / `creuser` étendu, gatés par **hache/serpe/pioche** sur le registre `sim/outils.py` **existant** (D82). Asymétrie de réversibilité : trogne 5 ans · recépage 10 ans · canopée 30 ans · entaille **jamais** · barrage rompt vers 8 ans. « Comptabilisé » = ledger + trace dans le milieu + matière (`mulch_stock`), **aucun indicateur cumulé** (#5). Une espèce ajoutée : le **saule** (trogne + bouture) avec ses 5 voix. **7 tronçons** (①ceinture+D92→②exposition/abri→③graines/eau/corridor→④gestes forestiers→⑤eau/roche/érosion→⑥voix→⑦vue Godot). **Golden INCHANGÉ partout** — aucun re-figeage autorisé (le golden ne pose ni maison ni ceinture ; `poro=None` garde la branche historique). Budget perf **< +2 % de tick** (caches `geom_key`/`_signature` existants). Absorbe **D92**, périme **D93** pour ce périmètre, ouvre **D94**. | `docs/champs/peripherie/conception_peripherie.md` + `sprints/champs/peripherie/sprint_peripherie/` (00_etat + 01→07) |

## Idées écartées, gardées au chaud

- **Noisetier** et **prunellier / ronce** — proposés par l'amorce D73 comme incarnations
  du taillis et de la friche pionnière. **Écartés du sprint** : côté périphérie la
  végétation est un **agrégat** (le charme et le bouleau suffisent à porter les deux
  camps « rejette / ne rejette pas »), et chaque espèce ajoutée coûte ses 5 voix. À
  reprendre le jour où la friche périphérique devient jouable *à l'intérieur* du terrain
  (extension par maîtrise, D15) — c'est là qu'elles auraient un rôle propre.
- **Lisière vivante** (vraies `PlantInstance` sur la première rangée) — plus belle et
  plus juste écologiquement, mais rouvre le poste `LightField` (D32) pour un gain
  d'observation faible. Le champ agrégé rend le même service à coût ≈ 0.
