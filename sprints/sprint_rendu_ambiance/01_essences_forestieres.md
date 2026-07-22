# T1 — Essences forestières au catalogue (MOTEUR, golden NEUTRE)

> Kickoff autosuffisant. Lire `CLAUDE.md` + `00_etat.md` + ce fichier suffit.
> Conception complète : `docs/rendu/ambiance/conception_rendu_ambiance.md` §2.

## Objectif
Ajouter **3 essences forestières normandes** au catalogue Python (source de
vérité) — **Hêtre**, **Bouleau**, **Charme** — comme vraies espèces `PerennialWoody`,
chacune avec ses **5 voix** (règle projet « toute plante ajoutée = toutes ses
voix »). Elles serviront de silhouettes au décor (T5) et à l'acquisition future
(canal #3 friche). **Elles ne sont PAS plantées dans le scénario smoke** → le
golden ne doit PAS bouger.

## Fichiers à toucher
- `data/code/plants/perennials.py` — 3 classes (gabarit = `OakTree`, voir §2 doc).
- `data/code/plants/catalogue.py` — les inscrire dans `PERENNIAL_CATALOGUE`.
- `data/code/sim/encyclopedie_corpus.py` — **fiche encyclopédie 3 niveaux** par
  essence (voix OBLIGATOIRE ; suivre l'entrée existante du `chene`/`sapin`).
- `data/code/sim/magazine.py` — rattachement famille/offre (Fagaceae, Betulaceae).
- `data/code/sim/pages.py` + `data/code/sim/carnet.py` — **optionnels** (page de
  lore si l'espèce en porte ; concept illustré). Cf. `docs/narration/voix/conception_voix_narratives.md`.

## Modèle (par espèce)
Copier la structure de `OakTree` (`plants/perennials.py`) et adapter :

- **Hêtre** — `family="Fagaceae"`, `genus="Fagus"`, `name="Hêtre"`,
  `pollination_mode="wind"`, port ovoïde dense, grande stature. `age_curve` de
  grand arbre (adulte ~2500-3000 cm à 100 ans, rayon large mais < chêne).
  `foliage_density` élevée (ombre dense), `longevity_years` ~300.
- **Bouleau** — `family="Betulaceae"` (famille NEUVE, la déclarer à l'espèce comme
  l'a fait `FirTree` pour Pinaceae), `genus="Betula"`, `name="Bouleau"`,
  **pionnier** (`keywords` lisière/pionnière), croissance rapide, stature moyenne
  (~1500-2000 cm), `foliage_density` faible (houppier léger), `longevity_years` ~90.
- **Charme** — `family="Betulaceae"`, `genus="Carpinus"`, `name="Charme"`, bois
  dur du bocage, stature moyenne, `foliage_density` moyenne, `longevity_years` ~150.

Valeurs de gènes/résistances : reprendre les défauts de `PerennialWoody` (ne pas
inventer de mécanique). `archetype=None` (arbres non tirés par la succession,
comme les autres pérennes).

## Golden — NEUTRE (impératif)
- Ces espèces **n'apparaissent pas** dans le scénario smoke (`tests/test_golden.py`,
  2 tuiles × 4 ans). Lancer `python3 -m tests.test_golden` **AVANT** et **APRÈS** :
  le hash doit être **identique**. Si le golden bouge, une espèce a fui dans le
  scénario (succession/seedbank) → corriger, ne JAMAIS re-figer.
- Lancer aussi `python3 -m tests.test_genetique` (ou la suite pérennes si elle
  existe) pour vérifier que les 3 classes s'instancient sans erreur.

## Ne PAS faire
- Ne pas planter ces arbres dans le smoke ni dans un banc.
- Ne pas ajouter de mécanique nouvelle (pas de trait neuf) — que du **contenu**.
- Ne pas toucher au rendu C# (c'est T5 qui lira les noms d'espèces).

## Vérif de sortie
Golden inchangé + suites vertes + les 3 espèces listables via le catalogue
(`PERENNIAL_CATALOGUE`) et pourvues d'une fiche encyclopédie.
