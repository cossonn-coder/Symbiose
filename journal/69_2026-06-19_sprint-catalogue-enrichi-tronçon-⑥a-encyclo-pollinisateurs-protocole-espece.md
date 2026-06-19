# 2026-06-19 — Sprint CATALOGUE ENRICHI · tronçon ⑥a (Python)

**Encyclopédie des 5 pollinisateurs + protocole pont `target.espece`.**
Première moitié du tronçon ⑥ (clôture du sprint), volet **Python testable**.
⑥b (vue Godot / sprites par espèce) suit, non-F5-testable par Claude.

## Contexte

Le tronçon ⑥ (esquissé §7.3 du doc, kickoff écrit après) a été scindé avec Nico
en **⑥a (Python : encyclo + protocole)** puis **⑥b (C# : sprites/butineurs/
heatmaps + bascule client `target.espece`)**. Deux natures de travail : ⑥a est
vérifiable de bout en bout (golden + suite + `dotnet build`), ⑥b ne l'est qu'au
`dotnet build`, le rendu visuel restant le F5 de Nico.

## Ce qui est fait (Python pur, golden NEUTRE)

1. **Encyclopédie des 5 pollinisateurs** (`fields/faune_encyclo.py`) : ajout de
   `abeille`, `syrphe`, `papillon`, `bourdon`, `osmie` à `FAUNE_ENCYCLO` (blurb
   naturaliste + graphe d'interconnexions). Jusqu'ici aucun pollinisateur n'avait
   d'entrée — **ni les 2 nouveaux de ⑤ ni les 3 anciens**. Tokens non-trophiques
   du graphe : `fruit` (floraison nouée), `ruche`/`miel` (abeille sociale), `pile`
   (osmie maçonne), `chenille`/`syrphe_larve` (ponts ⑤), `puceron` (proie de la
   larve de syrphe). Hors du sous-graphe trophique symétrique (les pollinisateurs
   pointent vers la floraison/niche, pas vers des proies réciproques).
2. **Splat dans `PollinatorSpec`** : `build_pollinator_specs()` (population.py)
   ajoute `**encyclo_meta(ps.name)` au `TrophicSpec` généré → les 5 pollinisateurs
   portent désormais blurb/interconnexions, comme les trophiques en ④e. DONNÉE
   PURE jamais lue par `tick`.
3. **Protocole `target.espece`** (`tools/simserver/actions.py:ecraser`) : la clé
   canonique de désignation devient `espece` ; `guilde` reste accepté en repli
   (`target.get("espece", target.get("guilde", "puceron"))`) pour ne pas casser le
   client Godot entre ⑥a et ⑥b (bascule coordonnée — le client passe à `espece` en
   ⑥b, le repli pourra alors être retiré). Message et variable renommés
   `guilde`→`espece` ; message d'erreur « espèce inconnue ». Commentaire stub de
   `serialize.py` mis à jour (le pont route désormais par espèce ; reste la TABLE
   sprite côté client = ⑥b).

## Tests & vérifs

- `test_faune_dediee.py` : nouvelle **section 10** (`test_metadata_encyclo_
  pollinisateurs`) — blurb non vide, ≥1 interconnexion, tokens connus, pas de
  prédateur. TOUS verts.
- `tests/simserver/actions.py` : cas `ecraser` bascule sur la clé `espece`
  (inconnue → refus pur ; coccinelle explicite → appliqué/nommé) + nouveau cas de
  **repli compat `guilde`** (encore accepté). Verts.
- **3 goldens INCHANGÉS** (golden NEUTRE prouvé — donnée pure + repli protocole
  sans effet moteur) : golden `f7e1a9b4…`, pop-golden `a39834df…`, vigueur-traj
  `e63b9d7f…`.
- Suite complète verte SAUF les **2 échecs PRÉ-EXISTANTS hors périmètre**
  (re-prouvés depuis ⑤) : `test_senescence` (mort asphyxie ~2.7 ans, modèle eau) ;
  `test_sim_server` pommier nouaison (0 fruit @ S52, pommier meurt « sèche » avant
  fructif) → 184/185.
- `dotnet build Symbiose.csproj` : 0 erreur (⑥a est Python pur).

## Confirmé au passage

Le snapshot `sprites` émet bien **15 clés d'espèce** (10 trophiques + abeille/
bourdon/papillon/syrphe/osmie) — la sérialisation par espèce est prête pour la
table sprite client de ⑥b.

## Reste — ⑥b (vue Godot, C#)

- `MacroLife.cs` mappe encore les 3 anciennes guildes → les 10 espèces nommées
  tombent toutes en point gris `GuildeInconnue`. Étendre la table sprite par
  espèce (placeholders procéduraux : forme/couleur par espèce, pas de PNG).
- `ForagerLayer.cs` : ajouter bourdon/osmie aux butineurs (ou les router) ;
  `FieldOverlay.cs` : heatmaps par catégorie.
- `WorldView.Actions.cs` : émettre `target.espece` (ex-`guilde`) sur `ecraser`.
- Encyclopédie : pas d'UI Godot (n'existe pas → sprint séparé) ; ⑥ porte les
  données seules.
