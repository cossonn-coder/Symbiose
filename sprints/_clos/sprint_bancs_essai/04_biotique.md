# Tronçon ④ — Banc biotique (ravageur / floraison→fruits / semis tempéré)

> Sprint « bancs d'essai ». État : `00_etat.md`. Dernière famille de bancs. Elle
> tranche le plus d'anomalies D47 : C3 (criblage fantôme), C4 (chaîne floraison
> muette), C5 (Solanaceae qui ne lèvent pas). **Golden NEUTRE attendu**.

## Objectif
Trois bancs du vivant (faune + cycle de vie + germination), chacun avec oracle,
et trois diagnostics D47 tranchés.

## Périmètre — `bancs/biotique.py` (3 fabriques ajoutées)

### 1. `infestation_ravageur()` — signe `ravageurs` (criblage) — tranche D47-C3
- 1 tuile où l'on force une densité `ravageur`/`chenille` élevée au plot (via le
  champ de faune `eco.category_density`/`larvae`, cf. `sim/semiologie.py`,
  fonction `ravageurs` l.119-127). Plante hôte posée → limbe criblé/troué (signe
  de FORME, pas de couleur).
- **Diagnostic D47-C3** : au F5, du feuillage criblé apparaissait alors que la
  pression puceron semblait ~0. Ce banc isole le VRAI criblage. Comparer avec le
  rendu NORMAL des feuilles à fort zoom (« petits points » ≠ criblage). Trancher :
  criblage fantôme (autre espèce ravageur ? limace/doryphore ?) vs artefact de
  rendu. NOTER la conclusion.
- Oracle : avec faune forcée, `"ravageurs" in signes(hôte)` ; sans faune (témoin),
  absent.

### 2. `verger_floraison()` — chaîne floraison→pollen→nouaison→fruits — tranche D47-C4
- Verger pré-vieilli : fruitier(s) à `age_years = maturity_years` (même réglage
  que `commands.py:70-73`) pour NOUER dès le 1er début d'été. Démarrer le monde
  en fenêtre de floraison (GDD/photopériode « début d'été »).
- **Diagnostic D47-C4** : au F5 an 4 début été, 0 fruit, 0 butineur, ~3 sprites
  macro — chaîne muette. Ce banc force les conditions idéales et vérifie chaque
  maillon : floraison → émission de pollen → présence de butineurs → nouaison →
  fruits. Si un maillon casse ici (monde idéal), c'est une **régression moteur**
  (pas un artefact carte). Localiser le maillon rompu (GDD/photopériode trop
  tardifs ? registre pollinisateurs ? faune trop basse ?). NOTER précisément.
- Oracle : après la fenêtre de floraison, `nb_fruits > 0` ET `nb_butineurs > 0`.

### 3. `semis_tempere()` — germination Solanaceae (banc ISOLÉ) — tranche D47-C5
- Pourquoi isolé : on neutralise les facteurs qui tuent la tomate/poivron dans
  les autres mondes (froid de démarrage < 5 °C, mildiou familial Solanaceae) pour
  tester la SEULE porte de germination de `planter`.
- 1 tuile `terre` tempérée (humidité/T douces), `planter` tomate + poivron via la
  banque-joueur (geste fidèle, cf. `main.sow_potager`). Conditions de germination
  réunies → les grains lèvent.
- **Diagnostic D47-C5** : trancher si « tomate/poivron ne lèvent pas » au F5 vient
  des portes de germination de `planter` ou de la fragilité Solanaceae
  (froid+mildiou) de la carte `full`. Si elles lèvent ici → c'était la carte.
  NOTER.
- Oracle : après N semaines, au moins 1 plantule tomate ET 1 poivron `is_alive`.

## Registre
`bancs/__init__.py` : ajouter `infestation_ravageur`, `verger_floraison`,
`semis_tempere` à `BANCS`.

## Vérifs
- Golden inchangé `2ab026ad…`.
- `tests/bancs/test_biotique.py` : les 3 oracles verts.
- `init config=<chacun>` répond `ok`.
- Taille `bancs/biotique.py` < ~350 lignes pur.

## Sortie
MAJ `00_etat.md` : ④ clos, golden NEUTRE, **conclusions D47-C3/C4/C5** (bug vs
artefact ; verser correctifs/dette pour les vrais bugs, notamment une éventuelle
régression floraison C4). Commit. `/clear` avant `05_selecteur_godot.md`.
