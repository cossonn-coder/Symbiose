# Tronçon ⑥ — Banc multifacteur de germination + oracles

> Kickoff **autosuffisant** (lis CLAUDE.md + 00_etat.md + ce fichier).
> Conception : `docs/vegetal/floraison/conception_germination_thermique.md` §5. Lancement depuis
> `data/code/`. Golden : **NEUTRE** (banc jamais monté au smoke/full).

## Objectif
Outiller le calibrage : un banc qui **balaye chaque facteur de germination toutes
choses égales par ailleurs** (`temperature_sol`, `humidite`, `pH`, `lumiere`) +
un oracle qui asserte le sens des réponses. Sert à régler `t_germ_opt/tol`,
`T_GERM_FLOOR`, `GERM_GENE_SHIFT` et le delta froid pluie du ①.

## Contexte bancs (patron mûr)
- `build_banc_tile(name, soil, rows, cols, ox=0, oy=0, *, humidite=0,
  fertilite=None, microbiome=0.2, **champs)` (`bancs/base.py`) force **uniformément**
  n'importe quel champ éco via `**champs` (p.ex. `temperature_sol=12.0`,
  `humidite=0.5`). `monde(tiles, ecos, house, banque)` emballe.
- Registre `BANCS` dans `bancs/__init__.py`. Oracles dans `data/code/tests/bancs/`.
- Banc germination existant `semis_tempere` (`bancs/biotique.py:113`) : ISOLE
  seulement (neutralise mildiou + froid), ne **balaye rien** → insuffisant.

## À faire
1. **Banc `germination_multifacteur`** (dans `bancs/biotique.py` ou
   `bancs/climatique.py` selon la cohérence thématique) : monte plusieurs tuiles
   identiques sauf **un** facteur balayé (gradient de `temperature_sol`, puis
   `humidite`, puis `pH`, puis `lumiere`), sème un jeu d'espèces frileuse +
   rustique, laisse N ticks, expose les **taux de levée** par tuile.
2. **L'enregistrer** dans `BANCS` (`bancs/__init__.py`).
3. **Oracle** `data/code/tests/bancs/` : asserte les sens attendus —
   - taux de levée **croît** avec T_sol jusqu'à l'optimum d'espèce puis **décroît** ;
   - **nul** sous `T_GERM_FLOOR` ;
   - frileuse lève **plus tard/moins** que rustique à T_sol intermédiaire ;
   - sensibilité pH/lumière cohérente avec les portes existantes.
   Assertions en **tendance/borne**, pas en égalité fragile.

## Golden
**NEUTRE.** Le banc n'est **jamais monté** au smoke/full → `tests/test_golden.py`
**inchangé**. Vérifier que le hash ne bouge pas. Si dérive : le banc fuite dans le
golden (mauvais montage) → corriger.

## Ce qu'il NE faut PAS faire
- Ne PAS modifier le moteur de germination ici (c'est de l'outillage/test).
- Ne PAS monter le banc dans le golden.
- Ne pas dupliquer `semis_tempere` — créer un banc qui **balaye**, pas qui isole.
