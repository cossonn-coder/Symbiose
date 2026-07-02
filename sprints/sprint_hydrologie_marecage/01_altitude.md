# ① — Champ `altitude` (micro-relief topographique déterministe)

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/conception/CONCEPTION_HYDROLOGIE_MARECAGE.md` §1. **Golden NEUTRE.**

## Objectif
Poser le champ `altitude` (cm de micro-relief du terrain), FIXE, initialisé
déterministe. Personne ne le lit encore ce tronçon → golden inchangé. C'est le
support de l'écoulement (②) et de la surface hydraulique visible (⑦).

## Fichiers
- `fields/ecofields/container.py` : déclarer `altitude: GridField = field(default=None)`
  (avec les autres, ~l.185) ; l'initialiser dans `__post_init__` ; le poser
  hétérogène dans `init_eco` sur un **canal de hash décorrélé** de l'humus.
- `fields/ecofields/constants.py` : `ALT_BASE`, `ALT_AMPLITUDE` (micro-relief de
  jardin, dénivelé ~0–40 cm, placeholder calibrage).
- `fields/ecofields/container.py` (`get_field`/registre) : exposer `altitude` à
  l'overlay debug (introspection, comme `epaisseur_sol`).
- `tools/simserver/serialize.py` : bloc `altitude` par tuile (grille 2D dense cm,
  patron `epaisseur`/`temperature.t_sol`). `tools/simserver/version.py` : bump
  ENGINE_VERSION + changelog. Tests `simserver/*` : recaler l'assert de version +
  1 check présence.

## Modèle
Patron D56 (`_init_heterogene`) mais **canal distinct** pour ne pas corréler relief
et humus :
```
seed_alt = stable_str_hash(tile_id + "_alt")
altitude[r][c] = ALT_BASE + ALT_AMPLITUDE * (2*_hash_noise(seed_alt, 0, r, c) - 1)   # borné ≥ 0
```
FIXE : aucun tick ne l'écrit (seuls les gestes ⑦ le modifieront). Les mini-sols de
conteneur (qui appellent `EcoFields(...)` direct sans `init_eco`) restent à
`altitude=0` (plats) → déterminisme préservé, aucun effet.

## Golden
**NEUTRE.** Le champ n'entre dans AUCUNE grandeur du digest (rien ne le lit).
`python3 -m tests.test_golden` doit rester **inchangé** (`a6c2f651…`). S'il bouge,
un tick lit `altitude` par erreur → annule.

## Ce qu'il NE faut PAS faire
- Ne pas brancher l'écoulement (c'est ②).
- Ne pas confondre avec `epaisseur_sol` (humus ≠ topographie — cf. §1).
- Ne pas toucher les mini-sols de conteneur (restent plats).

## F5
- L'altitude s'affiche-t-elle au relief (⑦) de façon crédible (cuvettes/bosses) ?
  Calibrage `ALT_AMPLITUDE` à l'œil (ici on ne fait que le champ + l'expo).
