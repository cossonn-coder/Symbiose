# ⑥ Magazine de botanique — `magazine_offres` / `acheter_au_magazine` (D13)

> Lire d'abord `00_etat.md` + `docs/narration/voix/conception_voix_narratives.md` (§2.4).
> Tronçon **quatrième voix** + 4ᵉ canal d'acquisition d'espèces. Offre = espèces SŒURS
> au **palier 3 de famille** ; achat = Vigueur → banque de graines. Event-driven hors
> tick. Dépend de ② (joueur/maîtrise) et réutilise ④ (fiche). Premier geste : RE-MESURER
> les hashs golden.

## Objectif
Écrire `magazine_offres(gs, player, saison) -> list[espèce]` (sœurs catalogue d'une
famille dont un membre est au palier 3, filtrées par fenêtre de semis) et
`acheter_au_magazine(gs, player, espèce) -> bool` (gate offre → dépense Vigueur → ajoute
le lot en banque). Doc §2.4. **Event-driven hors tick.**

## À faire

### A. `magazine_offres(gs, player, saison)` (`sim/magazine.py` ou module voix)
- Pour chaque famille dont **un membre a `maitrise.palier(gs, player, membre) >= 3`** :
  proposer ses **espèces sœurs** = membres de la famille **présents au catalogue maître**
  mais **absents de `PlayerSeedBank`** du joueur.
- Familles via `maitrise.famille_de` / `plants.catalogue` (`plants/catalogue.py`).
- **Filtrer par fenêtre de semis de la `saison`** (chaque espèce porte sa fenêtre au
  catalogue ; si l'info n'existe pas → TODO nommé, ne pas inventer).
- Sans maîtrise palier 3 → liste **vide**.

### B. `acheter_au_magazine(gs, player, espèce) -> bool`
- **Gate** : `espèce` doit être dans `magazine_offres(gs, player, saison_courante)`
  (sinon `False`, aucun effet).
- `vigueur.spend(gs, player, COUT_MAGAZINE)` (`sim/vigueur.py`) ; si fonds insuffisants
  → `False`.
- Succès → `PlayerSeedBank.add(Seed(species=espèce))` (`sim/seeds.py`) → `True`.

### C. Constantes + couplage encyclopédie
- `COUT_MAGAZINE` placeholder D12.4 (élevé, ponctuel), knob en tête de module.
- Couplage ④ : la **fiche niveau ≥ 2** est ce que le magazine montre du produit →
  réutiliser `encyclopedie_lire` (ne pas dupliquer le corpus).

## Couches
Lecteur/écriveur **event-driven hors tick** au niveau `sim`. Lit `maitrise` (D12),
`plants.catalogue`, écrit via `vigueur.spend` + `PlayerSeedBank.add` (APIs existantes).
**`engine` ne l'importe jamais.** Aucun RNG.

## Définition de done
- `magazine_offres` + `acheter_au_magazine` + `COUT_MAGAZINE`, fiche réutilisée de ④.
- `tests/test_magazine.py` (NOUVEAU) : membre famille **palier 3** → sœurs offertes ;
  achat valide → **Vigueur débitée** + **lot en banque** ; offre **filtrée par saison** ;
  **pas de palier 3 → offre vide** ; achat hors offre ou fonds insuffisants → `False`
  sans effet.
- **Golden INTACT** : smoke + population bit-identiques (hors tick, opt-in joueur).
- MAJ `00_etat.md` (⑥ → FAIT + **clôture sprint** : carte toute verte) puis commit.

## Pièges
- **Sœurs = catalogue MAÎTRE moins banque joueur** : ne propose pas une espèce déjà en
  banque. Ne propose pas le membre déjà maîtrisé lui-même (c'est l'ancrage, pas l'offre).
- Gate strict : `acheter` doit **re-vérifier** l'offre (ne pas faire confiance à l'appelant).
- Fenêtre de semis absente du catalogue → TODO nommé, ne pas fabriquer un calendrier.
- Réutiliser `encyclopedie_lire` pour la fiche produit (pas de second corpus).
- Event-driven : appelé par le driver/UI, **jamais** dans le tick — sinon golden bouge.
