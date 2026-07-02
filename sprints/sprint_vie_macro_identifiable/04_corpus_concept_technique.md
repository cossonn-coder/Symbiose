# ④ Corpus concept + technique (3 niveaux) (D60)

> Kickoff autosuffisant. Reprise à froid : `CLAUDE.md` + `00_etat.md` + ce fichier.
> Dépend de ① (dispatch + registre `CORPUS_PAR_TYPE`). Golden **NEUTRE** (données
> pures). Tronçon de RÉDACTION.

## Objectif
Écrire les fiches d'encyclopédie **3 niveaux** pour les onglets **concept** et
**technique**, et les brancher au dispatch de ①. Registre naturaliste (3ᵉ personne,
factuel), progression : N1 observation → N2 biologie/mécanisme → N3 rôle
écosystémique (mêmes titres que les plantes : Observation / Biologie / Écosystème,
cf. `EncyclopediePanel.TitresNiveau`).

## Périmètre — clés à couvrir
- **Concepts** (source de vérité = `sim/encyclopedie_types.CONCEPTS`, dérivée de
  `maitrise_detection.CONCEPT_PAR_STAGNATION` + pollinisation) :
  `eau`, `lumière`, `météo`, `pollinisation`. ⚠️ Vérifier la liste EXACTE au
  moment de l'implémentation (elle peut avoir grandi) ; couvrir TOUTES les clés
  concept que `type_de` classe `"concept"`, sinon fiche manquante = trou.
- **Techniques** (set `TECHNIQUES` de ①, dérivé de `OBJETS_TOUCHES`) :
  `semis`, `arrosage`, `récolte`, `arrachage`, `bêchage`, `ameublissement`,
  `taille`, `compostage`, `apiculture`, `jardinage_hors_sol`, `aménagement-habitat`.
  Même vigilance : couvrir tout ce que `type_de` classe `"technique"`.

## Fichiers à créer
- **CRÉER `sim/concept_corpus.py`** — `FICHES_CONCEPT: dict[str, dict[int, str]]`,
  chaque entrée `{1: "…N1…", 2: "…N2…", 3: "…N3…"}`. Miroir structurel de
  `sim/encyclopedie_corpus.py` (plantes) mais pour les concepts transversaux.
- **CRÉER `sim/technique_corpus.py`** — `FICHES_TECHNIQUE` idem.
- **BRANCHER au dispatch** : enregistrer ces corpus dans le registre
  `CORPUS_PAR_TYPE` de `sim/encyclopedie.py` (posé vide en ①) pour les types
  `concept` et `technique`. `encyclopedie_lire` tronque à `min(palier, 3)`
  (uniforme, comme les plantes) ; l'index les liste taggués.

## Registre & style
- 3 niveaux, palier-gatés : N1 dès découverte, N2 à palier 2, N3 à palier ≥ 3.
  Les concepts progressent déjà (crédités à chaque événement lié). Les techniques
  progressent via ③ (usage + succès).
- Voix « naturaliste qui observe » — factuelle, pas de tutoriel impératif (philo
  #6). Pas de chiffres de gameplay (philo #5). Interconnexions implicites dans le
  texte (relier l'idée aux acteurs : eau↔stagnation sèche, pollinisation↔butineurs
  + floraison↔fruits, compostage↔litière↔humus↔faune détritivore).
- Respecter la taille fichier (garde-fou ~300-400 LDC ; commentaires pédagogiques
  centraux exclus du décompte). Si un corpus gonfle, le scinder proprement.

## Ce qu'il NE faut PAS faire
- Ne PAS toucher le tick / moteur / golden.
- Ne PAS inventer de clés hors des ensembles de ① (une fiche sans clé de maîtrise
  correspondante est morte). Aligner sur `encyclopedie_types`.
- Ne PAS traiter geste/outil ici (c'est ⑤).
- Ne PAS re-styler l'UI (⑥).

## Golden
NEUTRE (données pures). Test : chaque clé concept/technique de `encyclopedie_types`
a une fiche à 3 niveaux ; `encyclopedie_lire` tronque correctement au palier ;
alignement clés corpus ↔ classification (aucun trou, aucun surplus).

## Points F5
Aucun (données). Le rendu est ⑥.
