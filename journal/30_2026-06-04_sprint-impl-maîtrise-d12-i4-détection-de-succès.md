## 2026-06-04 — Sprint impl. maîtrise D12·i4 : détection de succès branchée (Python) — impl. D12 COMPLÈTE

**Dernier des 4 tronçons**, le plus délicat (`sprints/sprint_D12_impl/`). Jusqu'ici
les preuves de maîtrise arrivaient **par injection** (`crediter_succes`/
`enregistrer_preuve` appelés à la main). i4 **branche la détection automatique** :
une couche **lit les signaux que le tick émet déjà** (§9.1) et en déduit, toute
seule, quand un **succès** a eu lieu (§9.0 : *une action joueur dont l'effet
émergent améliore le résultat au-delà du cours spontané, et qui est observée*).

**Nouveau module `sim/maitrise_detection.py`.** Logement **(a)** (point ouvert
majeur tranché) : module dédié appelé par le **driver** APRÈS chaque
`tick_semaine` — symétrique de `tick_player_vigueur`. Il importe `maitrise` +
`plants` ; `engine` ne l'importe **jamais** (pas d'inversion de couche). Pur au
sens golden : il **observe** le résultat d'un tick, ne le fait jamais avancer.

**A. Lecture des signaux.** Parsing du `log` retourné par le tick (marqueurs
`🌱` advance / `⏸🌑❄` stagnation / `🌰` reproduction avec tag) via regex, en
suivant la tuile courante (`[T0]`) — l'identité d'un plot = `zone=(tile_id,r,c)`.
Le **nom** de la ligne → clé catalogue (`_CLE_DE_NOM`, dérivé, non dupliqué). La
**santé** et la **naturalisation** se lisent dans l'état post-tick (`tiles[].plants`).

**B. État gameplay neuf (§9.6), au-dessus du tick.** Logé dans
`maitrise[player]["_detection"]` (maitrise.py possède `objets`, la détection
possède `_detection` → maitrise.py **reste pur**, il ignore cette clé). Contient :
*fenêtre d'imputation* (journal des gestes récents `(semaine, zone)`, largeur
`FENETRE_IMPUTATION=4`), *stagnations en attente de levée*, *tag de provenance*
(ensemble `replante` ; tout le reste **féral** par défaut — pas encore de geste
`planter`), flags `naturalise`/`experte` pour la conjonction palier 5.

**C. Règles de crédit.**
- **Lever une stagnation** (§9.2, 1→2) : `⏸/🌑/❄` en *t*, puis `🌱` de la **même
  zone** dans la fenêtre, **après un geste joueur imputable** → preuve sur
  l'espèce + le **concept lié à la cause** (sec→eau, ombre→lumière, froid→météo).
- **Amener à reproduction** (§9.2, 2→3 / 3→4) : `🌰` avec geste imputable → preuve
  espèce ; tag **biparental** → preuve **pollinisation** (§9.3).
- **Naturalisation férale** (§9.4(b)) : recrue **non `replante`** atteignant le
  stade `STAGE_NATURALISATION=2` en **pleine santé** → flag. Palier **4→5** =
  **conjonction** (`experte ∩ naturalise`).

**Garde-fous d'architecture (décisions posées, signalées).**
- **Gate d'observation** (§9.6, minimal) : on ne crédite qu'un objet **découvert**
  (`palier ≥ 1`) — jamais d'auto-découverte par la détection.
- **Nature croissante** (§9.2) : un succès ne crédite l'espèce que si sa nature
  correspond au **palier courant** (`NATURE_REQUISE`) — impossible de sauter une
  marche ; les concepts ont une nature uniforme.
- **Négatif §9.0** : une amélioration **sans geste imputable** (émergent pur, « ça
  pousse tout seul ») ne crédite **rien**.
- **Détection pure maîtrise** : elle crédite des preuves, **pas** de Vigueur (sens
  Vigueur→Maîtrise). Le pont Vigueur §4.3 d'un succès **auto** reste au driver.
- **`actions.py` inchangé** : la détection est event-driven *par tick*, les gestes
  *par clic* → le **driver** relie geste→`noter_geste` et tick→`detecter`.

**D. Golden joueur** — nouveau `tests/test_maitrise_detection.py` **20/20** :
positif (stagnation levée → espèce + concept, palier 1→2 sans appel manuel),
négatif (émergent sans geste → rien), concept par cause, gate d'observation,
nature croissante, pollinisation (biparental + geste vs autofécondation),
tag féral / naturalisation, **intégration sur un vrai `Engine`** (le parser
reconnaît le format réel du log). `test_maitrise.py` **35/35**, `test_vigueur.py`
**103/103** (injection i1–i3 intacte).

**Placeholders → calibrage D12.4** : `FENETRE_IMPUTATION`, `STAGE_NATURALISATION`,
et les Nᵢ (répétitions/palier) hérités de la courbe log d'i1.

### Hash golden (journal — AUCUN re-figeage)
Golden engine **`c950f06c…`**, golden de champ **`b005d9ba…`** : **VÉRIFIÉS
INCHANGÉS** avant *et* après (la détection lit, le tick est inchangé ; le golden =
succession pure sans joueur, ne touche jamais ce module). `main.py` tourne
(`import main OK`). **Impl. Python de D12 COMPLÈTE** — reste D12.2 (conception
bloquée), D12.4 (calibrage post-test) et D12.5 (portage C#, D24).

---
