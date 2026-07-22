# ① Substrat data-driven

> Lire d'abord `00_etat.md` + `docs/joueur/outils/conception_pots_bacs_substrats.md`
> (§2). Tronçon **data pur** : aucun conteneur, aucune boucle touchée → golden
> trivialement NEUTRE. Premier geste : mesurer et NOTER les hashs golden dans
> `00_etat.md`.

## Objectif
Créer le **registre des substrats** (6 recettes) et préparer le seul point de
couplage moteur : un `drainage_override` rétrocompatible sur `tick_hydrology`.

## À faire

### A. Registre `world/substrat.py` (nouveau fichier)
- `@dataclass(frozen=True) SubstratRecette` avec les champs du §2 : `nom`,
  `drainage`, `structure_init`, `ph_init`, `npk_init: tuple`, `microbiome_init`,
  `litiere_precharge: tuple = ()`, `herite_tuile: bool = False`.
- `SUBSTRATS: dict[str, SubstratRecette]` = les **6 recettes** du tableau §2
  (`terreau`, `compost`, `drainant_mineral`, `lasagnes`, `terre_jardin`,
  `mycelium_use`). Valeurs EXACTES du tableau. Pour `terre_jardin`, mettre des
  valeurs sentinelles (peu importe, jamais lues) + `herite_tuile=True`.
- Helper `get_substrat(cle) -> SubstratRecette` (KeyError explicite si inconnu).
- Vérifier que les `tissu` de `litiere_precharge` (`feuille`, `herbace`, `bois`,
  `substrat`) sont des clés VALIDES de la table `TISSU` (`fields/ecofields/litiere.py`)
  — sinon la décompo plantera plus tard. (Ajouter un petit garde-fou ou un test.)
- Export dans `world/__init__.py` (`SubstratRecette`, `SUBSTRATS`, `get_substrat`).

### B. `drainage_override` sur `tick_hydrology`
Dans `fields/ecofields/container.py`, `tick_hydrology(self, soil_type="terre")` →
`tick_hydrology(self, soil_type="terre", drainage_override=None)`. Une ligne :
```python
drainage = drainage_override if drainage_override is not None \
           else DRAINAGE_PAR_SOL.get(soil_type, DRAINAGE)
```
Aucun appelant existant ne passe l'override → **tuiles bit-identiques**. (C'est le
seul hook posé pour ② ; les conteneurs s'en serviront.)

## Couches
`world/substrat.py` n'importe rien de lourd (juste `dataclass`). Pas de cycle.

## Définition de done
- `world/substrat.py` créé, 6 recettes, `get_substrat`, exports.
- `tick_hydrology` accepte `drainage_override` (rétrocompatible).
- Nouveau `tests/test_substrat.py` : présence des 6 clés, valeurs du tableau,
  tissus de pré-charge valides, `get_substrat` lève sur clé inconnue,
  `drainage_override` change bien le drainage (mini-test sur un EcoFields jouet :
  override=0.90 → humidité diverge d'un appel sans override).
- **Golden PROUVÉ NEUTRE** : `tests/test_golden.py` + `tests/test_population.py`
  bit-identiques aux hashs notés dans `00_etat.md`. Suites amont vertes (lancer au
  moins golden, population, eau, sim_server).
- MAJ `00_etat.md` (ligne ① → FAIT + acquis) puis commit.

## Pièges
- Ne PAS encore brancher les substrats à quoi que ce soit (pas de conteneur en ①).
- `litiere_precharge` est de la DONNÉE ici ; son injection dans un mini-sol est en ②.
- Garder les valeurs en knobs lisibles (calibrage post-test annoncé).
