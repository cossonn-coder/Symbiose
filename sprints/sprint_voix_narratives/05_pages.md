# ⑤ Pages secrètes — `pages_trouvees` / `reveler_page` (3 robinets, D18)

> Lire d'abord `00_etat.md` + `docs/narration/voix/conception_voix_narratives.md` (§2.3, §7).
> Tronçon **troisième voix** : lore pur, **ZÉRO effet mécanique**, révélé par 3 robinets.
> État opt-in `gs["pages"][player]=set(ids)`. Dépend de ② (présence joueur), indépendant
> de ③④. Premier geste : RE-MESURER les hashs golden.

## Objectif
Écrire `pages_trouvees(gs, player) -> set[id]` et
`reveler_page(gs, player, robinet, contexte) -> id | None` (doc §2.3), alimentés par le
corpus **20 entrées P01..P20** (doc §7). Révélation **hors tick** (driver), **aucun
champ mécanique touché**. Épuisable → muet quand tout est trouvé.

## À faire

### A. Corpus de données (recopier du doc §7)
- Module de données `PAGES[id] = {id, voix, concept, palier_theme, robinet, texte}` —
  **recopier les 20 entrées P01..P20** du doc §7 (pastiche en STYLE, pas de citation
  réelle). Chaque page : `concept` (thème), `palier_theme` (ordre de due), `robinet`
  (canal d'obtention), `voix` (registre éditorial).

### B. État opt-in + `pages_trouvees` (`sim/pages.py` ou module voix)
- État : `gs["pages"][player] = set(ids)` (sérialisable → convertir set↔list au save).
- `ensure_player(gs, player)` opt-in (miroir journal/maitrise). Pas de joueur = pas de
  clé = no-op golden.
- `pages_trouvees(gs, player) -> set[id]` : renvoie le set (ou `set()` si pas de clé).

### C. `reveler_page(gs, player, robinet, contexte) -> id | None` — 3 robinets
- **récompense** : `contexte` porte le concept du succès → **prochaine page due de ce
  concept** non encore trouvée (ordre par `palier_theme`).
- **hasard** : n'importe quelle page non trouvée ; ancrage déterministe
  `_hash_noise(seed, semaine, "page")` (provisoire, cf. §4 — marqueurs bouture/oiseau/
  vent absents), tiré **au passage de saison**.
- **fouille** : action grenier → **prochaine page due** (ordre global `palier_theme`).
- Ordre de due = tri par `palier_theme`. Ajoute l'id au set, le renvoie. **Corpus épuisé
  pour ce robinet → `None`** (muet).

## Couches
Lecteur/écriveur d'un état joueur **opt-in** au niveau `sim`, **hors tick** (appelé par
le driver, comme `consigner`). **`engine` ne l'importe jamais.** Le seul RNG autorisé
est `_hash_noise` déterministe (robinet hasard) — jamais dans le tick.

## Définition de done
- Corpus `PAGES` recopié du doc §7 (20 entrées), `pages_trouvees` + `reveler_page` (3 robinets).
- `tests/test_pages.py` (NOUVEAU) : robinet **récompense** concept X → page de concept X ;
  corpus épuisé → `None` ; **déterminisme** robinet hasard (même seed/semaine → même
  page) ; **aucune page ne touche un champ mécanique** (asserter qu'aucune clé éco de
  `gs` ne change avant/après `reveler_page`) ; sans joueur → pas de clé `pages`.
- **Golden INTACT** : smoke + population bit-identiques (état opt-in, hors tick).
- MAJ `00_etat.md` (⑤ → FAIT) puis commit.

## Pièges
- **ZÉRO effet mécanique** : une page ne modifie que `gs["pages"][player]`, jamais un
  champ écologique, une plante, une Vigueur. Le test le vérifie explicitement.
- **Sérialisation** : `set` ⇒ convertir en `list` au save JSON (cf. cycle save §CLAUDE).
- Robinet hasard : **uniquement** `_hash_noise` déterministe, **jamais** `random` (sinon
  golden non reproductible et philo déterministe cassée).
- **Corpus éditorial** : recopier le lore du doc fidèlement (pastiche en style).
- Épuisable : ne jamais re-révéler une page déjà dans le set ; tout trouvé → `None`.
