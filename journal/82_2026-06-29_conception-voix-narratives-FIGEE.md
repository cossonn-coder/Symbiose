# 2026-06-29 — Bloc VOIX NARRATIVES (D13/D14/D18/D43 + encyclopédie + D12.2) — CONCEPTION FIGÉE

> Conception EN CONVERSATION (mode « conversation à trancher » : Claude structure,
> Nico décide, le résultat est gravé dans un doc). **Conception SEULE, zéro code
> moteur.** Livrable unique : `docs/conception/CONCEPTION_VOIX_NARRATIVES.md` (§0→§8).

## En une phrase
Les **quatre voix diégétiques** du jeu (carnet auto, encyclopédie, pages secrètes,
magazine de botanique) sont conçues comme des **lecteurs read-only par-dessus un
substrat unique** — un **ledger d'événements partagé** (`sim/journal.py`) alimenté
par le DRIVER **hors tick** (golden écologique INTACT) — et la **table D12.2**
(palier de maîtrise → déblocage) est enfin remplie car ses consommateurs sont
désormais conçus.

## Le verrou levé : un substrat partagé, pas quatre tuyaux
Les kickoffs isolés (D13/D14/D18, écrits le 2026-06-06) auraient produit quatre
systèmes qui re-parsent chacun l'état du jeu. Décision de cadrage : **un seul
journal d'événements** ; les 4 voix sont des **vues** dessus.
- À l'impl. : extraire `_evenements()` de `maitrise_detection.py` vers un module
  commun `sim/evenements.py` (refactor pur, `Evenement` namedtuple unifié), puis
  `sim/journal.py` avec `journal.consigner(gs, player, log, semaine)` appelé par le
  DRIVER après le tick — **jamais dans le tick** → golden jamais re-figé.
- État : `gs["journal"][player] = {"entries":[...], "resume":{...}}`, opt-in (pas de
  joueur enregistré ⇒ pas de clé ⇒ no-op golden strict, miroir de `maitrise`).

## Décisions tranchées par Nico
- **① substrat = ledger partagé** ; **② encyclopédie incluse** dans la passe
  (4ᵉ voix, sans dette code propre) ; **③ table D12.2 remplie** maintenant.
- **A** encyclopédie = **3 niveaux** révélés sur paliers **1/2/3** (basique /
  biologique / écosystémique) — **pas d'état neuf** : une espèce a une fiche ssi
  `palier ≥ 1`, le niveau = `min(palier, 3)`.
- **B** carnet = bascule **descriptif → interprétatif au palier 3 du CONCEPT** de
  l'entrée (pas de l'espèce) ; réglage d'aide « interprétatif anticipé » → palier 1.
  **D43** (acclimatation) = simple cas de cette règle (concept `adaptation`, aucun
  câblage neuf).
- **C** magazine = espèces **sœurs offertes dès le palier 3** d'un membre de la
  famille (réutilise le spillover famille déjà codé) ; numéros saisonniers.
- **Doc unifié** + **corpus complet** (pas seulement la mécanique).

## Contenu du doc (§0→§8)
- **§0** cadrage (décisions ci-dessus) · **§1** ledger partagé (extraction,
  interface, point d'entrée driver) · **§2** les 4 voix (rôles + interfaces
  read-only) · **§3** table D12.2 qualitative (encyclopédie/carnet/magazine/terrain
  D15/pages × paliers 0→5 ; seuils numériques = D12.4) · **§4** frontières & golden.
- **§5 corpus CARNET** : table `CONCEPT_DE[(kind, cause)]` + gabarits **2 registres**
  (descriptif / interprétatif) pour les types d'événements.
- **§6 corpus ENCYCLOPÉDIE** : **28 fiches × 3 niveaux** de botanique réelle (à
  relire/corriger — sujet hors expertise de Nico).
- **§7 corpus PAGES SECRÈTES** : **20 entrées, 5 voix** (maraîcher de la non-action /
  jardinière des allées / savoirs paysans / herbiers anciens / cahiers de sorcières),
  **pastiche en STYLE** (textes originaux, pas de citation réelle longue → copyright),
  **zéro effet mécanique**, révélées par 3 robinets (hasard / récompense / fouille).
- **§8 roadmap d'impl.** : **6 tronçons** golden-neutres
  ①`evenements.py` → ②`journal.py` → ③carnet → ④encyclopédie → ⑤pages → ⑥magazine,
  + tests visés par tronçon (golden `tests/test_golden.py` doit rester identique).

## Frontières / golden
Tout vit **hors tick** (driver + maison-hub) ⇒ le golden écologique n'est **jamais
re-figé** par ce bloc. Le seul état neuf est joueur (`journal`, `pages`) et opt-in.

## Reste (hors de ce bloc)
- **Implémentation** Python (6 tronçons) — **PAS lancée** : conception figée ≠ dev
  immédiat, et le portage n'est pas prioritaire (attente d'une conception jugée
  satisfaisante).
- **UI Godot** des 4 voix (carnet, encyclopédie, coffret grenier, kiosque magazine)
  → dette **D24** (vue C#).
- **Calibrage D12.4** (`COUT_MAGAZINE`, `JOURNAL_MAX`, seuils `completude_ratio`…).
- **Terrain D15** (tuile thématique au palier 3) : mécanique propre, hors bloc.
- **Marqueurs `bouture`/`oiseau`/`vent`** pour le robinet *hasard* des pages
  (fallback `_hash_noise` en attendant).

## Suivis mis à jour
`DETTE.md` (D13/D14/D18/D43 → 🟢 conçus + D12.2 ✅), `BACKLOG.md` (entrée bloc),
ce journal + index `journal.md`, mémoire `design_voix_narratives.md`.
