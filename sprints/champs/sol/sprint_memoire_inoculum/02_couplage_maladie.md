# Tronçon ② — Couplage inoculum → maladie (greffe unique)

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` +
> `docs/champs/sol/conception_memoire_inoculum.md` (§4, §5). Pré-requis : ① fait
> (le champ `eco.inoculum` existe et s'alimente). Lancement depuis `data/code/`.

## Objectif
Faire lire l'inoculum par la maladie, en UN seul point de greffe :
`disease_probability`. La terre chargée d'une famille aggrave la maladie de CETTE
famille (rotation émergente). Le signal SAR reste inoculum-free (anti-runaway).

## Golden ATTENDU : **RE-FIGÉ MAÎTRISÉ** (annoncé)
La probabilité de maladie change dès que l'inoculum > 0 → trajectoire de
mortalité/infection modifiée sur le scénario smoke. **Re-figeage attendu et
prévu.** Exigences :
- prouver que la dérive est **localisée à la voie maladie** : à `INOC_GAIN=0`,
  le golden doit retomber **bit-identique** sur l'ancien hash (sinon tu as touché
  autre chose). Fais ce contrôle explicitement avant de re-figer.
- consigner l'ancien → nouveau hash dans `00_etat.md` avec la cause (« inoculum
  amplifie disease_probability »).

## À implémenter
1. **Signature** — `fields/ecofields/sol.py:108`, ajoute `family=None` :
   ```python
   def disease_probability(self, r, c, base_rate=0.3, family=None):
       ...
       charge = 0.0 if family is None else self.inoculum.at(r, c, family)
       return base_rate * (1.0 + INOC_GAIN * charge) * max(0.02, 1.0 - protection)
   ```
   `INOC_GAIN` dans `constants.py` (placeholder, amplif DOUCE, §10).
2. **Appelants qui passent la family de la plante** :
   - `sim/effects/perturbations.py:198` `fungal_disease` → `family=plant.family` ;
   - `sim/effects/perturbations.py:121` `damping_off` → `family=plant.family` ;
   - `sim/effects/resolution.py:138` mildiou-rondelle → `family=` la plante concernée.
3. **Appelant qui NE passe PAS de family (anti-runaway)** :
   - `sim/engine/croissance.py:316` (signal SAR `infection_sig`) → **laisser
     `family=None`**. Le priming reste piloté par le risque ambiant, pas par la
     mémoire de terre. Ne PAS « améliorer » ça (c'est la garde anti-boucle §4).

## Ce qu'il NE faut PAS faire
- NE PAS amplifier le signal SAR par l'inoculum (romprait l'anti-runaway).
- NE PAS ajouter un second terme de monoculture (la densité même-famille de
  `fungal_disease` reste telle quelle, §5).
- NE PAS re-figer sans le contrôle `INOC_GAIN=0 ⇒ ancien hash`.

## Verrou de test
Étends `tests/test_inoculum.py` : (a) `disease_probability(family=F)` croît avec
`inoculum.at(...,F)` et est INCHANGÉ pour une autre famille G ; (b)
`disease_probability(family=None)` == ancienne formule (bit-identique) ; (c) test
d'invariant `INOC_GAIN=0 ⇒ golden bit-identique à l'ancien`. Re-fige `test_golden`
(hash annoncé). Vérifie `test_senescence`/`test_population` : si rouges, explique
la dérive (elle doit rester cohérente : plus de maladie sur sol chargé).

## À la fin
`00_etat.md` : hash ancien→nouveau + cause, §REPRISE → tronçon ③.
