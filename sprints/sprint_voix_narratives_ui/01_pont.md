# ① Pont : chaîne de maîtrise + 4 commandes voix + achat magazine

> Lire d'abord `00_etat.md` + `docs/conception/CONCEPTION_VOIX_NARRATIVES_UI.md`
> (§1 invariant, §2 hooks, §3 signatures, §4 pont). Tronçon **Python pur** (dossier
> `data/code/tools/simserver/`). Premier geste : `python3 -m tests.test_golden` →
> doit afficher `ae445d3f…`. **INVARIANT** : aucune phrase générée ici, on relaie le
> corpus verbatim.

## Objectif
Rendre les 4 voix **interrogeables depuis le pont** et **alimentées** par la
maîtrise. Trois blocs : (A) chaîne de maîtrise 3 hooks + révélation page ; (B) 4
commandes read-only ; (C) verbe d'achat `acheter_magazine`. Golden **intact**
(moteur non touché), `ENGINE_VERSION` bumpé.

## À faire

### A. Chaîne de maîtrise (`tools/simserver/commands.py` + `actions.py`)
Imports à ajouter dans `CommandsMixin` : `from sim import carnet, encyclopedie,
magazine, pages`, `from sim.actions import observer`, `from sim import
maitrise_detection`.

1. **`observer`** (découverte) — dans le chemin `cmd_step_week`, APRÈS le tick,
   pour le `current_player` :
   - espèces : `observer(gs, player, <clé espèce>)` pour chaque espèce d'une plante
     VIVANTE du monde post-tick (dédup) ;
   - concepts : à la 1ʳᵉ occurrence dans le `log` du tick — stagnation `sec`→`eau`,
     `ombre`→`lumière`, `froid`→`météo` (mapping `CONCEPT_PAR_STAGNATION` de
     `maitrise_detection`), repro `biparental`→`pollinisation`.
2. **`detecter`** — juste à côté de `consigner()` (`commands.py:143`), **après le
   tick, avant `log.clear()`** : `promos = detecter(gs, player, log, semaine)` avec
   `semaine = gs["week"] - 1`. Lecture seule du même `log` → ordre indifférent vs
   `consigner`.
3. **`noter_geste`** — dans `cmd_action` (`actions.py`), quand le geste porte sur un
   plot : `noter_geste(gs, player, gs["week"]-1, (tile_id, r, c))` AVANT le tick de
   résolution du geste (fenêtre d'imputation).
4. **Révélation page au palier** : pour chaque `(objet, palier)` de `promos` avec
   `palier == 3`, `reveler_page(gs, player, robinet="récompense",
   contexte={"concept": objet})`.

**NE PAS refaire** : `marquer_replante` (tick, `succession.py:158`), `consigner()`.

### B. 4 commandes read-only (`server.py` dispatch + `commands.py`)
Ajouter au dict `dispatch` (`server.py:25`) : `"carnet"`, `"encyclopedie"`,
`"pages"`, `"magazine"` → méthodes `cmd_*` dans `CommandsMixin`. Chacune lit
`player = gs["current_player"]`, appelle la voix, sérialise le retour JSON, 1 ligne
+ `flush`.
- `cmd_carnet(msg)` → `carnet_lire(gs, player, filtre=msg.get("filtre"))`.
- `cmd_encyclopedie(msg)` → si `msg.get("espece")` : `encyclopedie_lire(gs, player,
  espece)` ; sinon `encyclopedie_index(gs, player)`.
- `cmd_pages(msg)` → `sorted(pages_trouvees(gs, player))` + le texte de chaque page
  trouvée (lire `pages_corpus.PAGES[id]`, respecter `ORDRE`).
- `cmd_magazine(msg)` → si `msg.get("espece")` : `magazine_fiche(espece)` (PAS de
  gs/player) ; sinon `magazine_offres(gs, player)`.

### C. Verbe d'achat (`actions.py cmd_action`)
Brancher `verb == "acheter_magazine"` (chemin Vigueur unique, Q3) :
`ok = acheter_au_magazine(gs, player, params["espece"])` → renvoyer `{ok, result:
{achete: ok}, snapshot: bilan(...)}` (le `bilan` porte déjà `vigueur`/`vigueur_max`
+ banque rafraîchie). Refus si offre non ouverte ou Vigueur insuffisante (bool
`False`, pas d'exception).

### D. Version protocole
Bump `ENGINE_VERSION` (`tools/simserver/version.py`) — commandes neuves.

## Test (script pont JSON)
`data/code/tests/simserver/test_voix_pont.py` (ou section dans le smoke pont
existant) : `init config="full"` → quelques `step_week` → vérifier que
`encyclopedie` renvoie un index NON vide (des espèces vivantes ont été observées),
`carnet` renvoie des entrées, `pages`/`magazine` répondent (même vides), et un
`acheter_magazine` sur une offre ouverte débite la Vigueur + ajoute la graine.

## Definition of done
- 4 commandes répondent en JSON 1-ligne ; les 3 hooks tournent après tick/action.
- `python3 -m tests.test_golden` → **`ae445d3f…` INCHANGÉ** (moteur non touché).
- Script pont vert. `ENGINE_VERSION` bumpé. MAJ `00_etat.md` (①) + commit.
- LDC : garder chaque fichier pont sous le seuil (`tools/compte_ldc.py`) ; scinder
  si `commands.py`/`actions.py` gonflent.
