# Sprint « Vie macro identifiable + encyclopédie multi-règnes » (D60) — état de sprint

> État partagé léger. Reprise à froid : lire `CLAUDE.md` +
> `docs/conception/CONCEPTION_VIE_MACRO_IDENTIFIABLE.md` + ce fichier + le kickoff
> `0N` du tronçon courant. Conception FIGÉE (Nico « oui » 2026-07-02).

## Où on en est
Conception **figée**, 6 kickoffs autosuffisants écrits.
**① CLOS** (2026-07-02) : backend encyclo unifié multi-règnes. Créé
`sim/encyclopedie_types.py` (table de classification string→type, 7 types,
priorité déterministe) + `sim/champignon_encyclo.py` (fiche générique mono-niveau).
`sim/encyclopedie.py` dispatche par `type_de` (plante 3n inchangé, animal/champignon
mono-niveau, registre `CORPUS_PAR_TYPE` VIDE pour concept/technique/outil/geste →
`None` propre d'ici ④⑤) ; `encyclopedie_index` renvoie des dicts `{cle,type,titre}`
+ filtre par type. `cmd_encyclopedie` accepte `msg.type` (filtre) + `msg.cle`
(alias hérité `msg.espece`). Golden INCHANGÉ (`a6c2f651…`). Tests :
`test_encyclopedie` 42/42, `test_sim_server` 235/235.
**COLLISION SIGNALÉE** : `grelinette` est à la fois geste (verbe `COUTS`) et outil
(`OBJETS_TOUCHES`) — priorité déterministe la range en OUTIL (cohérent kickoff). Seule
clé multi-catégories ; documentée dans le test.

**② CLOS** (2026-07-02) : découverte de la vie macro au survol.
`tools/simserver/maitrise_pont.py:observer_espece` rendu MULTI-RÈGNES (plante par
nom de classe inchangé → animal `FAUNE_ENCYCLO` → `CLE_CHAMPIGNON` → None). Côté C# :
`ForagerLayer.SpeciesNear` + `CarpophoreLayer.HasNear` (miroirs de
`MacroLife.SpeciesNear`) ; `WorldView.Observation.cs:ObserveHoveredMacroLife`
(nuage → butineur → carpophore→"champignon", dédup `_especesMacroObservees`, gaté
zoom ≥ ×4), appelée depuis `WorldView._Process`. Golden INCHANGÉ (`a6c2f651…`).
Tests : `test_sim_server` 240/240 (+5 checks vie macro dans `simserver/voix.py`),
`test_encyclopedie` 42/42. **`dotnet build` VERT** (0 err/0 warn) — le risque
`EncyclopediePanel` (index strings→dicts) ne s'est PAS matérialisé, build propre.
**Point F5 Nico** : survoler un puceron/butineur/carpophore au zoom ≥ ×4 →
log `[WorldView] survol → vie macro observée : …` + entrée dans l'encyclo.

**③ CLOS** (2026-07-02) : progression geste/outil/technique combinée usage+succès.
`sim/maitrise.py:enregistrer_preuve` gagne `poids: float = 1.0` (défaut = comportement
historique, golden intact). `sim/maitrise_detection.py` : `noter_geste` mémorise le
`verb` (fenêtre `(sem, zone, verb)`, rétro-compatible None), nouvelle `verbes_imputables`,
`detecter` remplit une sortie optionnelle `zones_creditees` (les zones où un geste a
produit un crédit). Côté PONT (`tools/simserver/maitrise_pont.py`, étendu — LDC pur 61,
🟢) : `decouvrir_a_usage` (canal Q3, découvre geste+technique+outils à la 1ʳᵉ utilisation
réussie, avec petit gain de Vigueur §4.3), `crediter_usage` (preuve LÉGÈRE `PREUVE_USAGE_LEGER=0.34`),
`_crediter_succes_gestes` (preuve FORTE `PREUVE_SUCCES_FORT=1.0` sur le verbe imputé) ;
poids = placeholders calibrage **D12.4**. `cmd_action` appelle découverte+crédit APRÈS un
geste `applied` (hors tick → golden neutre) et rafraîchit `result[vigueur/vigueur_max]`.
**Décision retenue** (kickoff §5 option préférée) : le pont retrouve le verbe via la
fenêtre, pas `detecter` ; pont étendu plutôt que fichier neuf (< 300 LDC). Golden INCHANGÉ
(`a6c2f651…`, NEUTRE). Tests : nouveau `test_progression_geste` 15/15 ; `test_sim_server`
240/240 — **5 checks adaptés** (`actions/planter/taille/conteneurs`) : le gain de découverte
au 1ᵉ usage pollue le delta Vigueur net, on assied désormais l'assertion sur le champ
`cost` (source de vérité du geste) ; orphelins nettoyés. Batterie complète verte.

Reste ④→⑥.

## Sujet (D60, Nico 2026-07-02, F5 — S9, étend D31)
La vie macro est un amas de cercles indistincts. Objectif : **survol → nom + entrée
encyclopédie** (comme les plantes), et **encyclopédie filtrable par règne** en
**7 onglets** : plante · animal · champignon · concept · technique · outil · geste.
Détail complet : `docs/conception/CONCEPTION_VIE_MACRO_IDENTIFIABLE.md`.

## Décisions clés (rappel — détail dans le doc de conception §3)
- Faune = fiche MONO-niveau (blurb + graphe `faune_encyclo.py`), cap palier 1.
- Champignon = UNE fiche générique « réseau mycélien » (pas d'espèces).
- Outils ET gestes reçoivent leurs fiches, découverts à la **1ʳᵉ utilisation réussie**.
- 7 onglets ; profondeur = `min(palier, niveau_max_dispo)` uniforme (plante/concept/
  technique/outil/geste = 3 niv. ; animal/champignon = 1).
- Progression geste/outil/technique = **combinée usage + succès écologique**
  (poids léger à l'usage réussi ; poids fort au succès imputé par `detecter`).
- **Golden NEUTRE partout** (tout hors tick : pont opt-in + état joueur + données).

## Carte des tronçons
| # | Kickoff | Cœur | Golden | F5 |
|---|---------|------|--------|----|
| ✅ ① | `01_backend_encyclo_unifiee.md` | Corpus taggué + `type_de` + dispatch + fiche champignon | NEUTRE ✓ | non |
| ✅ ② | `02_survol_vie_macro.md` | `observer_espece` multi-règnes + survol C# vie macro | NEUTRE ✓ | **oui** |
| ✅ ③ | `03_progression_geste_outil.md` | Progression combinée usage+succès + découverte à l'usage | NEUTRE ✓ | non |
| ④ | `04_corpus_concept_technique.md` | Fiches 3 niv. concept + technique | NEUTRE | non |
| ⑤ | `05_corpus_geste_outil.md` | Fiches 3 niv. geste + outil | NEUTRE | non |
| ⑥ | `06_ui_godot_7_onglets.md` | UI 7 onglets + fiches mono/graphe + hover carpophore | NEUTRE | **oui** |

Dépendances : ② dépend de ① ; ③ dépend de ① ; ④⑤ dépendent de ① (branchent le
registre `CORPUS_PAR_TYPE`) ; ⑤ suppose ③ (rend N2/N3 atteignables) ; ⑥ dépend de
①–⑤. ⚠️ ① change la forme de l'index (strings → dicts taggués) : `EncyclopediePanel`
peut casser à `dotnet build` entre ① et ⑥ — c'est PRÉVU, ⑥ répare la vue.

## Ancrages code vérifiés (pour implémenter à froid)
- Encyclo pont : `tools/simserver/voix.py:cmd_encyclopedie` → `sim/encyclopedie.py`
  (`encyclopedie_index`/`encyclopedie_lire`) ; corpus plantes `sim/encyclopedie_corpus.py`
  (`FICHES`, `NIVEAU_MAX=3`). Faune : `fields/faune_encyclo.py` (`FAUNE_ENCYCLO`
  15 espèces, `encyclo_meta(name)` → `{blurb, interconnexions}`).
- Maîtrise : `sim/maitrise.py` (`decouvrir`, `palier`, `enregistrer_preuve` +
  `_facteur_spillover`, `preuves_requises`, `PALIER_MAX=5`). Progression Vigueur :
  `sim/actions/progression.py` (`observer` = découvre+gain ; `crediter_succes`).
- Détection : `sim/maitrise_detection.py` (`detecter` renvoie `[(objet,palier)]`,
  `noter_geste(gs,player,semaine,zone)`, fenêtre `_detection["gestes"]=[(sem,zone)]`,
  `_crediter` gate palier≥1 + `NATURE_REQUISE` pour espèces, concepts non gatés).
- Survol PLANTE : `world/WorldView.Observation.cs` (`ObserveHoveredPlant`, dédup
  `_especesObservees`) → `SimBridge.Observer` → `maitrise_pont.observer_espece`
  (`_CLE_DE_NOM`, PLANTES only). Picking vie macro : `visuals/MacroLife.cs:SpeciesNear`
  (10 espèces trophiques ; butineurs `NonDessine`→`ForagerLayer` ; `MinZoom=4`).
  Carpophores : `visuals/CarpophoreLayer.cs`, snapshot `sample_carpophores`.
- Gestes : `sim/actions/couts.py` (`COUTS`, `OBJETS_TOUCHES` mêle technique+outil,
  `_objets_action`). Routeur `tools/simserver/actions.py:cmd_action` (`result.applied`,
  `_noter_geste_maitrise`→`noter_geste_pont`). UI `world/EncyclopediePanel.cs`
  (ouvert `WorldView.Hub.cs:176`), `core/SimBridge.cs:Encyclopedie/Observer`.

## §REPRISE (exécution)
Boucle `/sprint-auto` : lancer le kickoff `0N` → implémenter → vérifier
`python3 -m tests.test_golden` (attendu INCHANGÉ, golden NEUTRE) + tests ciblés du
tronçon + `dotnet build Symbiose.csproj` pour les tronçons C# (②⑥) → mettre à jour
CE fichier (cocher le tronçon) → commit → `/clear` → tronçon suivant. **①②③ CLOS** ;
reprendre à **④** (`04_corpus_concept_technique.md` — fiches encyclopédie 3 niveaux
concept + technique, branche le registre `CORPUS_PAR_TYPE` laissé VIDE au ① ; tronçon
Python pur, **pas F5**, golden NEUTRE). F5 groupés à la fin (② faite — à valider ; et ⑥).

## NB git
À l'ouverture de la conception, l'arbre était SALE (`sprint_epaisseur_sol` non
commité + modifs `data/code/`). Le commit de figeage n'ajoute QUE les fichiers D60
(doc + 6 kickoffs + ce fichier + DETTE + journal), jamais `epaisseur_sol` ni les
modifs `data/code/`. Exiger un arbre propre avant d'exécuter les tronçons.
