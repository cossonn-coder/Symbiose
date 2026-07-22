# Tronçon 4 — Catalogue clonal ① : fraisier + menthe (+ 5 voix chacune)

> Kickoff autosuffisant. Lis `CLAUDE.md` (règle « toute plante = ses 5 voix ») +
> `00_etat.md` + `docs/vegetal/grimpantes/conception_luxuriance_stratification.md` +
> `docs/narration/voix/conception_voix_narratives.md`.
> **Pré-requis : tronçons 2 (clonal) et 3 (silhouette) faits.**
> **Golden : NEUTRE** (espèces neuves, hors scénario golden).

## Objectif
Ajouter au catalogue **2 espèces clonales** incarnant la densification (absorbe
D62), chacune COMPLÈTE avec ses **5 voix**. Elles exercent la mécanique clonale du
tronçon 2 et la couverture du tronçon 1.

## Espèces
1. **Fraisier** (*Fragaria vesca*, Rosaceae) — couvre-sol **stolonifère** :
   `clonal_mode="stolon"`, strate `sol`/`basse`, `silhouette="rosette"`, portée
   courte, gate lumière au sol. Organe comestible (fruit). Tapisse en plein/mi-soleil.
2. **Menthe** (*Mentha* sp., Lamiaceae — famille existante) — **rhizome
   envahissant** : `clonal_mode="rhizome"`, strate `basse`, `silhouette="touffe"`,
   portée longue, tolère l'ombre → colonise vite. Aromatique. Illustre le revers
   du clonal (envahissement à surveiller).

Suivre le patron d'une espèce existante (`plants/species/cultivees.py` ou
`aromatiques.py` pour la menthe). Renseigner : famille, `growth_stages` (strate par
stade), `clonal_mode`/`clonal_radius_cm`/`clonal_interval`, `silhouette`,
`keywords`, `rarity`, cycle de vie, densité de feuillage.

## Les 5 voix (obligatoires, cf. CONCEPTION_VOIX_NARRATIVES)
1. **Encyclopédie** — `sim/encyclopedie_corpus.py` : fiche 3 niveaux (basique /
   bio / effets écosystémiques). Voix naturaliste.
2. **Carnet** — `sim/carnet.py` (`CONCEPT_DE`) : rattacher chaque espèce aux
   concepts qu'elle illustre (ex. « reproduction clonale », « couvre-sol »,
   « plante envahissante » pour la menthe).
3. **Pages secrètes** — `sim/pages_corpus.py` : une page de lore SI l'espèce en
   porte un (fraisier des bois / menthe des sorcières — optionnel mais bienvenu).
4. **Magazine** — `sim/magazine.py` : rattachement famille + offre de déblocage.
5. **Événements** — `sim/evenements.py` : marqueurs de cycle de vie consignés au
   ledger (floraison, fructification fraisier, émission de stolon/rhizome…).

## Fichiers à toucher
- `plants/species/` (ajout des 2 classes ; menthe → aromatiques, fraisier → potageres
  ou un module cohérent) + réexport `plants/species/__init__.py` + `plants/catalogue.py`.
- Famille Rosaceae : réutiliser l'attribut `family="Rosaceae"` (déjà porté par
  AppleTree). Créer une base herbacée si le patron l'exige, sinon attribut simple.
- Les 5 fichiers de voix ci-dessus.

## Golden — NEUTRE
Ni fraisier ni menthe ne sont semés dans le scénario golden → `test_golden`
**inchangé**. Vérifier. Si dérive → un ajout a fui dans le tick du golden (ex.
`add_species` global) → corriger. Lancer les suites voix/catalogue si présentes.

## Ce qu'il NE faut PAS faire
- Pas de plante « muette » : les 5 voix sont OBLIGATOIRES.
- Pas de modif de la mécanique clonale (elle est figée au tronçon 2).
- Pas de rendu (tronçon 6).

## Fin de tronçon
MAJ `00_etat.md` (§REPRISE, golden inchangé), commit.
