# 2026-07-02 — Conception VIE MACRO IDENTIFIABLE + encyclopédie multi-règnes (D60) — FIGÉE

> `/conception d60`, phase B (conception SEULE, aucun code moteur écrit).
> Doc : `docs/conception/CONCEPTION_VIE_MACRO_IDENTIFIABLE.md`. Sprint prêt :
> `sprints/sprint_vie_macro_identifiable/` (00_etat + 01…06). Prêt pour `/sprint-auto`.

## Sujet

D60 (Nico 2026-07-02, F5 — S9, étend D31) : la vie macro est un amas de cercles de
couleur indistincts. Objectif : **survol → nom + entrée encyclopédie** (comme les
plantes, pont 0.5.12) et **encyclopédie filtrable par règne**.

## Constat d'entrée : ≈ moitié du chemin déjà posée

Picking survol vie macro DÉJÀ là (`MacroLife.SpeciesNear`) ; découverte data-driven
(accepte n'importe quelle clé) ; faune a ses métadonnées (`faune_encyclo.py`, 15
espèces blurb+graphe, branchée à AUCUN pont) ; panneau encyclopédie + index
existent (plantes only). D60 branche ces morceaux et comble les trous.

## Décisions arbitrées

- **Q1 = fiche faune MONO-niveau** : survol → blurb + graphe d'interconnexions de
  `faune_encyclo.py`, PAS de progression palier animal (détection ne crédite que
  plantes+concepts → cap palier 1 naturel).
- **Q2 = UNE entrée générique champignon** : survol carpophore → fiche « réseau
  mycélien » unique, pas d'espèces fongiques.
- **Q3 = TOUT FAIRE MAINTENANT** : outils ET gestes reçoivent leurs fiches,
  découverts à la **1ʳᵉ utilisation réussie** (canal de découverte neuf).
- **QA = 7 ONGLETS** : plante · animal · champignon · concept · technique · outil ·
  geste. Encyclopédie UNIFIÉE multi-règnes (les concepts entrent en plus du carnet).
- **QB = 3 NIVEAUX gatés palier** pour geste/outil/technique. Profondeur uniforme
  `min(palier, niveau_max_dispo)`.
- **Progression geste/outil/technique = COMBINÉE usage + succès écologique** (Nico) :
  usage réussi (`cmd_action` applied=True) → preuve poids LÉGER sur geste+outils+
  technique ; succès imputé par `detecter` (levée stagnation / repro provoquée,
  infra `noter_geste_pont` déjà là) → preuve BONUS poids FORT. Courbe géométrique
  existante ; poids = placeholders D12.4. **Tout hors tick → golden NEUTRE.**

## Modèle unifié (backend)

Corpus tagué : chaque entrée `{cle, type, niveaux}`, `type` ∈ 7 valeurs.
`encyclopedie_index` renvoie les découverts (palier≥1) taggués (filtre 7 onglets) ;
`encyclopedie_lire` dispatche par type et tronque à `min(palier, niveau_max)`.
Table de classification string→type (`sim/encyclopedie_types.py`) sépare
outil/technique/geste dans `OBJETS_TOUCHES`/`COUTS`. Sources : `encyclopedie_corpus`
(plantes, inchangé) + `faune_encyclo` (animaux mono) + fiche champignon générique +
nouveaux corpus concept/technique/outil/geste (3 niv.).

## Découpage — 6 tronçons, golden NEUTRE partout

① backend encyclo unifiée + type + dispatch ; ② survol vie macro → observer
(`observer_espece` multi-règnes + C# MacroLife/WorldView, F5) ; ③ progression
geste/outil/technique combinée + découverte à l'usage ; ④ corpus concept+technique ;
⑤ corpus geste+outil ; ⑥ UI Godot 7 onglets + hover carpophore (F5). ⚠️ ① change la
forme de l'index (strings→dicts taggués) → `EncyclopediePanel` peut casser au build
entre ① et ⑥ (prévu, ⑥ répare).

## Coût perf

Quasi nul : tout read-only ou état joueur (pont opt-in, hors tick). Survol vie macro
réutilise `SpeciesNear` (déjà appelé) — aucun nouveau balayage de champ.

Conception seule, rien implémenté. Prêt pour `/sprint-auto sprint_vie_macro_identifiable`.
