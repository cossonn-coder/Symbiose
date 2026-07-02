# 2026-07-03 — Sprint VIE MACRO IDENTIFIABLE + encyclopédie multi-règnes (D60, ①→⑥) — SPRINT TERMINÉ

`/sprint-auto sprint_vie_macro_identifiable`. La vie macro cesse d'être un amas
de cercles indistincts : **survol → nom + entrée encyclopédie** (comme les
plantes) et **encyclopédie filtrable en 7 onglets** (plante · animal ·
champignon · concept · technique · outil · geste). Étend D31, brique D24.
Conception figée le 2026-07-02 (`docs/conception/CONCEPTION_VIE_MACRO_IDENTIFIABLE.md`).

## Golden — NEUTRE de bout en bout
**Golden INCHANGÉ `a6c2f651…` sur les 6 tronçons.** Tout le sprint vit hors
tick : corpus de données pures, pont opt-in, état joueur, couche vue C#. Aucun
re-figeage — conforme à la carte de conception (« golden NEUTRE partout »).

## Tronçons (①②③ clos la veille, ④⑤⑥ ce jour)
- **① backend encyclo unifié** (`a6c2f651…`) — `sim/encyclopedie_types.py` (table
  classif string→type, 7 types, priorité déterministe) + `sim/champignon_encyclo.py`
  (fiche générique mono-niveau) ; `sim/encyclopedie.py` dispatche par `type_de`,
  index → dicts `{cle,type,titre}` filtrables. **Collision signalée** : `grelinette`
  = geste ET outil → priorité déterministe le range en OUTIL.
- **② survol vie macro** (`a6c2f651…`, **F5**) — `observer_espece` multi-règnes
  (plante→animal→champignon→None) ; C# `ForagerLayer.SpeciesNear` +
  `CarpophoreLayer.HasNear` + `WorldView.Observation.cs:ObserveHoveredMacroLife`
  (gaté zoom ≥ ×4, dédup). `dotnet build` vert.
- **③ progression geste/outil/technique combinée** (`a6c2f651…`) — `enregistrer_preuve`
  gagne `poids` ; `maitrise_detection` mémorise le `verb` ; pont : `decouvrir_a_usage`
  (canal Q3, découverte à la 1ʳᵉ utilisation réussie) + `crediter_usage`
  (`PREUVE_USAGE_LEGER=0.34`) + `_crediter_succes_gestes` (`PREUVE_SUCCES_FORT=1.0`) ;
  poids = placeholders calibrage **D12.4**. Nouveau `test_progression_geste` 15/15.
- **④ corpus concept + technique** (`a6c2f651…`) — `sim/concept_corpus.py`
  (4 concepts) + `sim/technique_corpus.py` (11 techniques), fiches 3 niveaux
  (observation → mécanisme → rôle écosystémique) branchées dans `CORPUS_PAR_TYPE`.
  Voix naturaliste, contreparties nommées (philo #1/#5/#6).
- **⑤ corpus geste + outil** (`a6c2f651…`) — `sim/geste_corpus.py` (20 gestes) +
  `sim/outil_corpus.py` (12 outils), fiches 3 niveaux (geste : acte→mécanique→rôle+
  effets de bord ; outil : objet→usage juste→quand s'en passer). Test K = complétude
  GLOBALE (tout objet classé a une source de fiche). `test_encyclopedie` 68/68.
- **⑥ UI Godot 7 onglets** (`a6c2f651…`, **F5**, `dotnet build` vert) — réécrit
  `EncyclopediePanel` (barre 7 onglets, index filtré au pont par type, fiche
  dispatchée 3-niveaux vs mono-niveau blurb+interconnexions) ; param `type` ajouté
  à `SimBridge.Encyclopedie`. **Répare la casse ①** (index strings→dicts) dans
  `CarnetPanel` (bug runtime silencieux, lecture du champ `cle` au lieu de `AsString`).
  Hover carpophore déjà couvert par ②.

## Clôture
- **Refactor auto-léger = no-op** : aucun fichier créé/touché ne dépasse la bande
  (max LDC pur = `SimBridge.cs` 209, `geste_corpus.py` 161 ; tous 🟢). Le sprint
  n'a créé aucune dette de taille.
- Tests finaux : `test_golden` PASS `a6c2f651…`, `test_encyclopedie` 68/68,
  `test_sim_server` 240/240, `test_progression_geste` 15/15. `dotnet build` vert (0/0).

## Reste F5 = Nico
1. Ouvrir l'encyclo (hub maison) → **7 onglets** présents.
2. Survoler puceron/coccinelle/abeille au zoom ≥ ×4 → onglet **Animaux** (blurb +
   interconnexions) ; survoler un **carpophore** → onglet Champignons.
3. Gestes répétés (arroser/planter…) → onglets Gestes/Outils/Techniques apparaissent,
   fiches N2/N3 progressives à mesure de la maîtrise.
4. Onglet non découvert → message neutre « (rien de découvert dans cette catégorie) ».

Calibrage des poids de progression = **D12.4** (placeholders posés). Python source
de vérité ; C# = couche vue.
