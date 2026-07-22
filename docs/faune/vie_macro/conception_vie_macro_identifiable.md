# Conception — Vie macro identifiable + encyclopédie multi-règnes (D60)

> Sujet D60 (Nico 2026-07-02, F5 — S9, étend D31). Conception FIGÉE (« oui »
> 2026-07-02). Ce doc est la référence de conception ; l'exécution est découpée en
> 6 kickoffs autosuffisants sous `sprints/faune/vie_macro/sprint_vie_macro_identifiable/`.

## 1. Problème

La vie macro (faune trophique + butineurs + carpophores) est rendue à l'écran
comme un **amas de cercles de couleur indistincts**. Le joueur ne peut pas savoir
ce qu'il regarde. Les PLANTES, elles, sont déjà identifiables : survol → nom
(étiquette) et surtout survol → **découverte encyclopédie** (pont 0.5.12,
`WorldView.Observation.cs` → `Observer` → `observer_espece`).

**Objectif** : porter cette posture naturaliste (« on apprend ce qu'on REGARDE »)
à TOUTE la vie macro, et faire de l'encyclopédie un ouvrage **multi-règnes
filtrable** — pas seulement un herbier.

Deux moitiés du chemin sont DÉJÀ posées (voir §7) : le picking de survol de la vie
macro existe (`MacroLife.SpeciesNear`), la découverte est data-driven (accepte
n'importe quelle clé string), la faune a déjà ses métadonnées (`faune_encyclo.py`),
le panneau encyclopédie + son index existent. D60 branche ces morceaux et comble
les trous.

## 2. Les trous à combler

1. Le survol de la vie macro n'appelle jamais `observer` (seul le survol PLANTE le fait).
2. `observer_espece` (pont) ne résout que les clés PLANTES.
3. L'encyclopédie ne sert que le corpus plantes ; la faune (blurb) n'a aucun pont.
4. Pas de filtre par règne/type dans le panneau.
5. Champignon = 1 acteur générique (densité de carpophores), sans fiche ni espèces.
6. Outils / gestes = objets de maîtrise « neutres » sans fiche, non survolables.

## 3. Décisions arrêtées

### 3.1 Périmètre des fiches (Q1/Q2/Q3)
- **Faune = fiche MONO-niveau** (Q1). Survol → découverte → blurb + graphe
  d'interconnexions issus de `faune_encyclo.py`, réutilisé tel quel. PAS de
  progression de palier animal : les règles de détection ne créditent que les
  plantes et les concepts (cf. `maitrise_detection.NATURE_REQUISE`). L'animal
  reste donc naturellement plafonné à palier 1 = 1 fiche.
- **Champignon = UNE entrée générique** (Q2). Survol d'un carpophore → découvre la
  fiche unique « champignons / réseau mycélien ». L'onglet champignon = cette seule
  fiche (pas d'espèces fongiques — cohérent avec `sample_carpophores` qui ne rend
  qu'un acteur `mycelium` générique).
- **Outils ET gestes reçoivent leurs fiches MAINTENANT** (Q3), découverts à la
  **1ʳᵉ utilisation réussie** (canal de découverte NEUF — pas de survol monde, un
  geste ne se survole pas).

### 3.2 Taxonomie de l'encyclopédie (QA)
- **7 ONGLETS** : plante · animal · champignon · **concept · technique** · outil ·
  geste. L'encyclopédie devient un ouvrage **UNIFIÉ multi-règnes**. Les concepts
  (qui vivent déjà dans le carnet interprétatif) entrent AUSSI dans l'encyclo ; les
  techniques ont leur propre onglet, distinct des outils.

### 3.3 Profondeur des fiches (QB)
- **3 NIVEAUX gatés palier** pour geste / outil / technique, comme les plantes.
- Règle UNIFORME : profondeur = `min(palier, niveau_max_disponible)`.
  - plante : 3 niveaux (progresse déjà via détection) ✓
  - concept : 3 niveaux (progresse déjà : crédité à chaque événement lié) ✓
  - **geste / outil / technique : 3 niveaux → EXIGE une progression neuve** (§3.4)
  - animal : cap palier 1 (détection ne les crédite pas) → 1 fiche (blurb + graphe)
  - champignon : 1 fiche générique (pas de progression)

### 3.4 Progression geste/outil/technique = COMBINÉE usage + succès écologique
Sans source de preuves, geste/outil/technique resteraient plafonnés à palier 1 et
les niveaux N2/N3 seraient du contenu MORT (≈ 150 textes jamais vus). On ouvre donc
un robinet de preuves à DEUX volets, tout côté PONT (état joueur, hors tick) :

- **usage répété** : chaque utilisation RÉUSSIE (`cmd_action` renvoie `applied=True`)
  crédite une preuve de **poids léger** sur le geste employé + ses outils + sa
  technique (résolus via la table de classification, §5) ;
- **succès écologique** : quand `detecter` IMPUTE une amélioration écologique au
  geste du joueur (levée de stagnation, reproduction provoquée — infrastructure
  d'imputation DÉJÀ en place via `noter_geste_pont`/`detecter`), crédit d'une preuve
  **BONUS de poids fort** sur ce geste.

Courbe `preuves_requises` géométrique existante (`sim/maitrise.py`) réutilisée.
Poids léger/fort = **placeholders à calibrer (dette D12.4)**. Déterministe, aucun
RNG. Golden NEUTRE (le moteur tourne sans serveur → ces hooks ne sont jamais
appelés).

## 4. Philosophie respectée
- **#5 (indices visuels, pas de chiffres)** : le survol révèle un NOM et alimente
  l'encyclopédie ; aucune barre ni compteur en HUD.
- **#6 (méthode scientifique, apprendre ce qu'on regarde)** : la posture
  naturaliste plantes est étendue à toute la vie macro. La découverte reste
  diffuse (regarder / utiliser), jamais un grind imposé.
- **Interconnexion des acteurs** : la fiche faune expose son graphe
  d'interconnexions (proie/prédateur/plante-hôte) ; la fiche champignon dit le
  réseau mycélien ; concepts/techniques/gestes/outils relient l'action du joueur à
  ses effets. Aucun acteur n'est une fiche isolée.
- **Déterminisme (#3)** : aucun aléa introduit ; tout hook est idempotent/déterministe.

## 5. Modèle unifié (backend)

Interface corpus unique : chaque entrée = `{cle, type, niveaux:{1..k}}`, avec
`type ∈ {plante, animal, champignon, concept, technique, outil, geste}`.

- `encyclopedie_index(gs, player)` renvoie les entrées découvertes (palier ≥ 1)
  **TAGUÉES par type** (→ alimente le filtre 7 onglets côté UI).
- `encyclopedie_lire(gs, player, cle)` **dispatche par type** vers la bonne source
  et tronque à `min(palier, niveau_max_dispo)`.

Sources de corpus :
- `encyclopedie_corpus.py` (plantes, 3 niveaux) — **inchangé** ;
- `faune_encyclo.py` (animaux, mono-niveau : blurb + graphe) — réutilisé ;
- fiche champignon générique (nouvelle, 1 niveau) ;
- nouveaux corpus **concept · technique · outil · geste** (3 niveaux, tronçons ④⑤).

**Table de classification string→type** : nécessaire pour séparer *outil* vs
*technique* dans `OBJETS_TOUCHES` (`sim/actions/couts.py` mélange les deux dans un
même tuple par geste). Cette table est la source de vérité qui range chaque objet
de maîtrise dans son onglet et route les crédits de preuves (§3.4).

## 6. Coût perf
Quasi nul côté moteur : tout est read-only ou état joueur (pont opt-in, hors tick,
golden NEUTRE attendu partout). Le survol de la vie macro **réutilise**
`MacroLife.SpeciesNear` (déjà appelé pour l'écrasement ciblé) — pas de nouveau
balayage de champ. Aucune structure moteur nouvelle.

## 7. Ancrages code vérifiés
- Survol PLANTE : `world/WorldView.Observation.cs` → `SimBridge.Observer(species)`
  → `tools/simserver/maitrise_pont.py:observer_espece` (résout via `_CLE_DE_NOM`,
  PLANTES only).
- Picking vie macro : `visuals/MacroLife.cs:SpeciesNear(wMonde, rayonCm)` (rend 10
  espèces trophiques ; butineurs = `NonDessine`, ForagerLayer).
- Carpophores : `visuals/CarpophoreLayer.cs` ; snapshot bloc `carpophores`
  (`tools/simserver/serialize.py:sample_carpophores`) = densité, UN acteur générique.
- Encyclopédie pont : `tools/simserver/voix.py:cmd_encyclopedie` → `sim/encyclopedie.py`
  (`encyclopedie_index`/`encyclopedie_lire`) ; corpus `sim/encyclopedie_corpus.py`
  (28 plantes, 3 niveaux). Faune : `fields/faune_encyclo.py` (blurb + graphe).
- Découverte data-driven : `sim/maitrise.py:decouvrir/palier` (clé ARBITRAIRE OK) ;
  `sim/actions/progression.py:observer`. Crédit preuves : `sim/maitrise_detection.py`
  (`detecter`, `_crediter`, `NATURE_REQUISE`) — crédite plantes + concepts SEULEMENT.
- Gestes/outils/techniques : `sim/actions/couts.py` (`COUTS`, `OBJETS_TOUCHES`).
  Routeur : `tools/simserver/actions.py:cmd_action` (verbe=geste, `applied` dans
  result) ; imputation `_noter_geste_maitrise` → `noter_geste_pont`.
- UI : `world/EncyclopediePanel.cs` (index cliquable + fiche N1/N2/N3), ouvert via
  `world/WorldView.Hub.cs:176`. Pont C# : `core/SimBridge.cs:Encyclopedie(espece=null)`
  + `Observer(species)`.

## 8. Découpage en 6 tronçons (golden NEUTRE partout)

1. **① backend encyclo unifiée + type** — interface corpus taguée, dispatch par
   type, `cmd_encyclopedie` renvoie index tagué + accepte un filtre ; plantes
   inchangées, animal (mono via `faune_encyclo`), fiche champignon générique.
   Tests Python.
2. **② découverte vie macro au survol** — pont `observer_espece` accepte les clés
   animales + carpophore→champignon ; C# `MacroLife`/`WorldView` survol → `Observer`.
   Point F5.
3. **③ progression geste/outil/technique (combiné usage + succès)** — crédit de
   preuves (pont, hors tick) + découverte à l'usage + table de classification
   outil/technique/geste. Tests joueur. Golden NEUTRE.
4. **④ corpus concept + technique** (3 niveaux) — rédaction des fiches.
5. **⑤ corpus geste + outil** (3 niveaux) — rédaction des fiches.
6. **⑥ UI Godot 7 onglets** — filtre par règne dans `EncyclopediePanel` + hover
   carpophore. Point F5.

Le golden reste **NEUTRE** à chaque tronçon (aucune écriture dans le tick : tout
vit dans le pont opt-in / l'état joueur, ou dans du texte de corpus).
