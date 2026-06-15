# Dette D13 — Magazine de botanique (canal d'acquisition d'espèces)

> **Kickoff autosuffisant.** Lis ce fichier en entier, puis les sources, puis
> exécute. Français + pédagogie. **Conception SEULE d'abord** (produire un
> `CONCEPTION_MAGAZINE.md`, valider avec Nico, puis seulement impl.). Ampleur
> **moyenne**. Aucun code golden touché en phase conception.

## Ce que c'est, en une phrase
Concevoir le **magazine de botanique** : le **4ᵉ canal d'acquisition d'espèces** (cf.
CLAUDE.md « Acquisition d'espèces »), débloqué par **Vigueur joueur + maîtrise**, qui
permet au joueur d'**introduire volontairement** une nouvelle espèce dans son jardin
— par opposition aux 3 canaux *subis* (succession spontanée, événements rares,
exploration de friche).

## Le contexte (CLAUDE.md + conception déjà faite)
- **Les 4 canaux d'acquisition** (CLAUDE.md) : 1. succession spontanée (`niche_index`),
  2. événements rares (bouture/oiseau/vent), 3. friche périphérique, **4. magazine**
  (déblocage par Vigueur + maîtrise). D13 = le canal 4.
- **La maîtrise est prête à l'alimenter** (`CONCEPTION_MAITRISE.md`) :
  - **§7** : « D13 (magazine) — consomme la **complétude-ratio** + paliers pour
    débloquer des espèces ».
  - **§3.2** : deux mesures globales distinctes — la **complétude-ratio** (→ seuils
    de déblocage) ≠ l'**accumulation-log** (→ Vigueur max/régen). Le magazine lit la
    **complétude-ratio**, fonction déjà implémentée (`maitrise.completude_ratio`).
  - **§8 point 2** : la **table palier→déblocage** est un sous-sprint séparé (**D12.2**)
    qui *coordonne* magazine/carnet/terrain. D13 doit donc s'arrêter **au bord** de la
    table (définir CE QUE le magazine fait), pas la remplir (← D12.2).
- **Banque de graines joueur** déjà en place : `sim/seeds.py::PlayerSeedBank` (lots par
  espèce, transportable, suit l'avatar, JSON). Le magazine **dépose un lot** dans cette
  banque — l'infrastructure de réception existe.
- **Vigueur joueur** : `sim/vigueur.py` (état event-driven, `spend`/`gain`,
  `palier_bonus`). Le coût du magazine se paie via `spend`, comme une action.

## Ce qui est déjà tranché (ne pas re-débattre)
- Magazine = **dans la maison normande** (hub, fonction « Magazine de botanique »,
  CLAUDE.md). Pas un menu hors-monde.
- Déblocage = **Vigueur + maîtrise** (les deux), pas de monnaie, pas d'achat (philo :
  « la connaissance ouvre l'espace », pas la conquête).
- Run éternel : pas de catalogue « premium », pas de rareté artificielle de boutique.

## 🔵 Choix de design à trancher
### Choix 1 — Qu'est-ce qui « débloque » une espèce dans le magazine ?
- **(A) ⭐ Maîtrise = condition d'apparition, Vigueur = coût d'obtention.** Une espèce
  apparaît dans le magazine quand un **seuil de complétude-ratio** (global ou de
  famille) est franchi ; l'**obtenir** (déposer un lot dans la `PlayerSeedBank`) coûte
  de la **Vigueur**. Deux leviers séparés = pédagogie claire (« je comprends assez
  pour que ce savoir s'ouvre ; il me coûte de l'énergie de le concrétiser »).
- **(B) Vigueur seule** (maîtrise ignorée) : simple, mais casse le lien « savoir →
  accès » qui est tout le sel du jeu.
- **(C) Maîtrise seule** (gratuit une fois débloqué) : élégant mais retire le rôle de
  la Vigueur que CLAUDE.md lui donne explicitement ici.

> Reco : **(A)** — c'est la lecture littérale de CLAUDE.md (« Vigueur **+** maîtrise »).

### Choix 2 — Quelles espèces le magazine propose-t-il, et liées à quelle maîtrise ?
- **(A) ⭐ Espèces de familles déjà maîtrisées** : maîtriser les Solanaceae ouvre
  d'autres Solanaceae (parenté botanique = fil pédagogique). Cohérent avec le
  **spillover intra-famille** déjà codé (`enregistrer_preuve`).
- **(B) Espèces « voisines écologiques »** (même strate/niche, pas même famille) :
  plus riche écologiquement, mais demande une notion de proximité de niche non encore
  modélisée.
- **(C) Catalogue plat débloqué par complétude globale** : simple, mais perd le lien
  « ce que tu connais ouvre ce qui lui ressemble ».

> Reco : **(A)** pour la v1 (réutilise le spillover famille), **(B)** en backlog quand
> les niches seront formalisées (lié à D26 diversification).

### Choix 3 — Forme diégétique : un magazine qui se « complète » ?
CLAUDE.md veut des **dispositifs informationnels diégétiques** (encyclopédie, carnet).
Le magazine devrait suivre : pages qui **se remplissent** à mesure que la maîtrise
monte (offres qui apparaissent), pas une liste plate.
- **(A) ⭐ Numéros mensuels** (saisonniers) : à chaque saison, un « numéro » propose
  quelques espèces de saison parmi les débloquées. Rythme le gameplay, évite le
  catalogue-supermarché, colle au cycle.
- **(B) Catalogue permanent filtré** par maîtrise : plus simple, moins vivant.

> Reco : **(A)** si tu veux du caractère, **(B)** pour un MVP. À toi selon l'effort.

## Périmètre — phase CONCEPTION (livrable de ce sprint)
Produire `docs/conception/CONCEPTION_MAGAZINE.md` qui acte : les 3 choix ci-dessus ; la
**signature de l'interface** côté moteur (`magazine_offres(game_state, player) ->
list[espèce]` lisant `completude_ratio` ; `acheter_au_magazine(game_state, player,
espèce) -> bool` qui `spend` la Vigueur puis dépose un lot dans `PlayerSeedBank`) ;
et **explicitement ce qui est renvoyé à D12.2** (les *seuils* exacts palier→offre).
**Ne pas** coder le tick (le magazine est hors tick, comme toutes les actions joueur).

## Hors périmètre
La **table de seuils** palier→déblocage (← D12.2, qui coordonne magazine+carnet+
terrain). L'**UI Godot** du magazine (sprint frontend). Le **contenu encyclopédique**
des fiches (← encyclopédie, voix narrative séparée). Portage C# (D24).

## Golden / vérification
Phase conception = **zéro code**, golden intact par construction. À l'impl. (sprint
suivant) : magazine = event-driven hors tick → golden écolo **INTACT** ; tests sur
`PlayerSeedBank` (un lot déposé après `acheter`, Vigueur débitée, offre gated par
maîtrise). MAJ `DETTE.md` D13 (conçu) + `BACKLOG.md`.
