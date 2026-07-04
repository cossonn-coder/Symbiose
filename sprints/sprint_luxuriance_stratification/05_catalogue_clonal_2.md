# Tronçon 5 — Catalogue clonal ② : framboisier + bambou traçant + violettes (+ 5 voix)

> Kickoff autosuffisant. Lis `CLAUDE.md` (règle « toute plante = ses 5 voix ») +
> `00_etat.md` + `docs/conception/CONCEPTION_LUXURIANCE_STRATIFICATION.md` +
> `docs/conception/CONCEPTION_VOIX_NARRATIVES.md`.
> **Pré-requis : tronçons 2, 3, 4 faits** (patron d'espèce clonale posé au 4).
> **Golden : NEUTRE.**

## Objectif
Compléter le catalogue clonal (absorbe D62) avec **3 espèces**, chacune COMPLÈTE
avec ses **5 voix**. Elles couvrent les 3 modes clonaux et 2 registres nouveaux
(fruitier ligneux drageonnant, graminée envahissante, couvre-sol d'ombre).

## Espèces
1. **Framboisier** (*Rubus idaeus*, Rosaceae) — **drageon** :
   `clonal_mode="drageon"`, strate `moyenne`/`haute`, `silhouette="buisson"`,
   portée très courte (thicket près de la mère). Fruitier. Illustre le drageon.
2. **Bambou traçant** (*Phyllostachys*, Poaceae — famille existante) — **rhizome
   très envahissant** : `clonal_mode="rhizome"`, strate `haute`, portée LONGUE,
   tolère l'ombre, `silhouette="dressée"`. Le démonstrateur extrême de
   l'envahissement clonal — attention au cap couverture (tronçon 1) qui le borne.
3. **Violette odorante** (*Viola odorata*, **Violaceae — FAMILLE À CRÉER**) —
   couvre-sol d'ombre **stolonifère** : `clonal_mode="stolon"`, strate `sol`,
   `silhouette="tapis"`, sciaphile (prospère sous canopée). Mellifère précoce.
   Créer la classe famille `Violaceae` dans `plants/base/familles.py` (patron des
   familles existantes).

## Les 5 voix (obligatoires — cf. CONCEPTION_VOIX_NARRATIVES)
Pour CHAQUE espèce, comme au tronçon 4 :
1. **Encyclopédie** (`sim/encyclopedie_corpus.py`) — fiche 3 niveaux.
2. **Carnet** (`sim/carnet.py`, `CONCEPT_DE`) — concepts illustrés (drageon,
   graminée rhizomateuse, couvre-sol d'ombre, envahissement…).
3. **Pages secrètes** (`sim/pages_corpus.py`) — lore si porté (violette des bois
   / bambou / ronce — optionnel).
4. **Magazine** (`sim/magazine.py`) — famille + offre de déblocage.
5. **Événements** (`sim/evenements.py`) — marqueurs de cycle de vie (floraison
   violette précoce, fructification framboise, poussée de rhizome bambou…).

## Fichiers à toucher
- `plants/base/familles.py` (nouvelle classe `Violaceae`).
- `plants/species/` (3 classes) + `plants/species/__init__.py` + `plants/catalogue.py`.
- Les 5 fichiers de voix.

## Golden — NEUTRE
Aucune de ces espèces n'est dans le scénario golden → `test_golden` **inchangé**.
Vérifier. La création de la famille `Violaceae` ne doit rien changer aux espèces
existantes.

## Ce qu'il NE faut PAS faire
- Pas de plante muette (5 voix obligatoires).
- Pas de modif de la mécanique clonale ni du champ couverture (figés 1-2).
- Ne pas laisser le bambou exploser le nombre de plantes : c'est le gate couverture
  du tronçon 1 qui le borne — si ça explose, c'est un bug de gate à remonter, pas à
  contourner ici.
- Pas de rendu (tronçon 6).

## Fin de tronçon
MAJ `00_etat.md` (§REPRISE, golden inchangé), commit.
