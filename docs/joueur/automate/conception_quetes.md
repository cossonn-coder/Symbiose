# Conception — Système de quêtes (D79)

> **FIGÉE le 2026-07-24** (skill `/conception`, amont de `/sprint-auto`).
> Type/thème : `joueur/automate`. Dépend de D78 (fait) ; couple D87 (clos).
> Sprint prêt : `sprints/joueur/automate/sprint_quetes/` (5 tronçons).

## 1. Intention

Donner une **direction** au joueur dans un bac à sable sans direction, **sans
casser la promesse d'apprentissage diffus** (#6). Une quête n'est pas un ordre :
c'est un **désir** posé par une voix (une lettre), et une **lecture passive** de
l'état du monde pour savoir s'il est comblé. La quête **ne pilote rien, elle
regarde**. Le *comment* appartient au joueur et à son écologie (#1) — jamais à la
quête.

## 2. Ce que le code impose (faits vérifiés, source de vérité Python)

Trois découvertes du code recadrent l'amorce :

- **F1 — Le cœur objectif D78 n'est PAS sur le chemin joueur.**
  `tools/jardinier_auto/objectifs.py` est le harnais de l'**automate** ;
  `incrementer()` est appelé par la boucle automate ; `sim/actions/gestes.py`
  (gestes du **joueur humain**) l'ignore ; le pont ne l'expose que derrière
  `automate on`. → **D79 est un système MOTEUR joueur neuf** (`sim/quetes.py`),
  pas un enveloppement de D78. Il **partage la forme** `(geste, quantite, cible)`
  mais possède son propre état (sauvegardé) et son propre point de comptage.
- **F2 — `sim/evenements.py` est un PARSEUR de log texte (regex), pas un bus.**
  → La quête **n'est pas** « le 5ᵉ lecteur du ledger ». Conditions cumulées
  comptées par **hook sur le geste joueur** ; conditions d'état lues sur le
  **snapshot** hors tick. Moins de couplage, pas de coût de parsing.
- **F3 — Le kiwi N'EXISTE PAS** (grimpante différée D26). Le trèfle existe
  (stolonifère). Espèces hautes dispo pour `hauteur_min` : `Sunflower`,
  `AppleTree`. → **Aucune espèce créée dans D79.** Une quête « kiwi 5 m » a une
  cible `inatteignable` (déjà géré par `est_atteignable`) jusqu'à D26.

## 3. Décisions de vision (tranchées par Nico, 2026-07-24)

- **V1 — Donneurs = LETTRES ANONYMES.** Une lettre signée d'un prénom
  (« Ton voisin Marcel »), **sans figure, sans dialogue, sans récurrence
  obligatoire**. Voix épistolaire. Compatible avec l'esprit « pas de PNJ » →
  le garde-fou CLAUDE.md est **ajusté** pour autoriser les voix épistolaires
  (une plume, pas un personnage).
- **V2 — Affichage DIÉGÉTIQUE approximatif.** Progression en langage vivant
  (« de quoi remplir un cageot », « à hauteur d'homme », « ça y est presque »).
  **Chiffre exact réservé au mode debug** (#5 respecté).
- **V3 — Récompenses (catalogue déclaratif ouvert).** Base = **plaisir pur**
  (combler le désir suffit). Variantes : **graine · page secrète · Vigueur
  joueur · maîtrise** (crédit direct). RARE : **outil · structure permanente ·
  plante vivace déjà enracinée de plusieurs années** (= instanciation d'une
  pérenne à âge avancé — un cadeau matériel, **PAS un buff** → #2 respecté).
  **JAMAIS de bonus/malus direct sur une plante existante.**

## 4. Décisions techniques

- **Représentation de la condition** : **mini-catalogue déclaratif fermé** de
  types (pas de langage de prédicats général) :
  - `recolte_cumulee(geste, quantite, cible)` — comptée par hook geste ;
  - `hauteur_min(cible, metres)` · `floraison_min(cible, n)` ·
    `nombre_vivant_min(cible, n)` — lues sur snapshot.
  Chaque type = une fonction pure `(params, monde/compteurs) → (accompli: bool,
  avancement_diegetique: str)`. On étend en **ajoutant un type**.
- **Couplage D87 : one-way et partiel, assumé.** Une quête `recolte_cumulee`
  est le tuple `Objectif` D78/D87 → convertible (l'automate sait la poursuivre,
  utile en banc). Les conditions d'**état** sont **nouvelles** et l'automate ne
  sait pas « pousser jusqu'à 5 m » — **et ce n'est pas requis** (D79 = système
  joueur). On ne demande **rien de neuf à D87** dans ce sprint.
- **Persistance** : quête **ouverte à vie**, accomplissable à tout moment,
  **jamais d'expiration ni de vocabulaire d'échec** (#4). Le joueur peut
  ignorer/archiver une lettre.
- **Garde-fou #6 formel** : optionnelle + ignorable + jamais bloquante +
  **désir-sans-méthode** (la voix ne dit jamais *comment*) + **plafond de N
  quêtes actives simultanées** (les nouvelles n'arrivent pas tant que le plafond
  est plein → tue l'effet « checklist »).
- **Déclenchement déterministe (#3, zéro RNG vivant)** : gaté par **palier de
  maîtrise** (`sim.maitrise.palier`) et/ou **jalon de saison**. Une quête
  « arrive » quand le joueur franchit un seuil ou à un jalon calendaire.
- **Perf** : K conditions actives lues sur snapshot **hors tick**, K borné par le
  plafond → négligeable, aucun O(N²). **Golden intact** (couche `sim`, jamais
  importée par `engine`).

## 5. Respect de la philo (#1–#7)

- **#1/#2** ✅ la quête observe, ne pousse jamais une plante ; aucune récompense
  ne dope une plante existante (V3).
- **#3** ✅ déclenchement et progression déterministes, aucun `random` vivant.
- **#4** ✅ pas d'expiration, pas d'échec terminal.
- **#5** ✅ progression diégétique, chiffre en debug seulement (V2).
- **#6** ✅ garde-fou formel (§4) — désir sans méthode, optionnel, plafonné.
- **#7** neutre ; piste d'élégance : une lettre ne réclame pas une espèce que le
  terrain ne peut pas porter (non exigé).

## 6. Interconnexions

- **D78/④** — forme de données `(geste, quantite, cible)` réutilisée (pas le code).
- **D87** — couplage one-way partiel (§4), non requis ce sprint.
- **Ledger `sim/evenements.py`** — accomplir une quête **émet** un événement
  (→ entrée carnet « j'ai porté les patates au voisin ») ; n'est PAS lu pour
  détecter (F2).
- **Snapshot / pont JSON** — conditions d'état + alimentation du panneau courrier.
- **Maîtrise (D12.2, `sim.maitrise.palier`)** — déclencheur d'apparition.
- **Banque de graines · pages secrètes · Vigueur (D11) · maîtrise · structures ·
  pérennes** — cibles de récompense (V3).

## 7. Voix narratives

Nouveauté : une **catégorie de voix inédite**, le **donneur d'objectif**, sous
forme de **lettre épistolaire anonyme** (V1). Registre chaleureux, jamais
directif — le désir est là, la méthode jamais. Exemples de ton (corpus à écrire
au tronçon ③) :
- voisin : « Dis donc, tes patates ont l'air belles cette année — j'en prendrais
  bien un plein cageot si tu as du rab. » ;
- enfant : « Tonton, il paraît que les kiwis ça monte super haut ? J'aimerais
  trop en voir un géant ! » ;
- oncle : « Ta grand-mère avait un tapis de trèfle en fleur derrière la maison.
  Ça me manque. »

Articulation : accomplir une quête émet un événement au ledger (→ **carnet**) et
peut débloquer une **page secrète** (V3). La voix du donneur parle du **monde
social**, distincte des 4 voix « du jardin » (écologie).

## 8. Découpage (5 tronçons, golden intact partout)

| # | Tronçon | Cœur |
|---|---------|------|
| ① | Module moteur `sim/quetes.py` + conditions **cumulées** | dataclass `Quete`, état `game_state`, hook comptage sur le dispatch des gestes joueur, accomplissement + consignation ledger, tests. Opt-in → golden intact |
| ② | Conditions d'**état** | `hauteur_min` / `floraison_min` / `nombre_vivant_min` sur snapshot hors tick + progression diégétique |
| ③ | Déclenchement + habillage | déclenchement déterministe (palier maîtrise + jalon saison), table déclarative de quêtes, **voix des donneurs** (corpus épistolaire), plafond quêtes actives, récompenses **simples** (graine/page/Vigueur/maîtrise) |
| ④ | Récompenses **matérielles rares** | vivace déjà enracinée (instanciation pérenne à âge avancé), structure permanente posée ; **outil différé en dette** si pas d'inventaire d'outils |
| ⑤ | **Vue Godot** | pont expose quêtes+progression diégétique, panneau « courrier » (lettres cochées quand comblées), banc F5 |

*Fin de la conception figée.*
