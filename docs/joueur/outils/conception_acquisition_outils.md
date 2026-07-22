# Conception — Acquisition des moyens d'agir (SYMBIOSE)

> **Document de conception FIGÉ (2026-07-19).** Spec de référence du sprint
> d'implémentation (MOTEUR + vue). Découpe = **4 tronçons** (§L). Kickoffs :
> `sprints/joueur/outils/sprint_acquisition_outils/0N_*.md`. Carnet d'état : `00_etat.md`.
> Origine : **dette D82** (chaîne « taille » inatteignable) + impasse
> `RAVITAILLEMENT_MANQUANT` de `tools/jardinier_auto/` (pailler sans mulch ni moyen
> d'en produire). Deux instances d'un MÊME bug : un geste bloqué faute d'un
> **moyen** que rien ne provisionne. D'où le sprint « acquisition des MOYENS
> d'agir » = **outils** (sécateur) + **matière** (mulch).

---

## 0. Constat & périmètre

**D82** — `couper` est gated derrière le marqueur `posseder_secateur`
(`sim/actions/deblocage.py:55`), `tailler`/`bouturer` en dépendent, mais **aucun
flux ne pose ce marqueur** → toute la famille taille est morte (F5 Nico : « pas
d'option couper »).

**Impasse ravitaillement** — `jardinier_auto` (automate qui joue le jardin pour
débusquer les trous de gameplay) veut `pailler` (stress hydrique / `sol_nu`) mais
`mulch_stock` est vide ET aucun canal n'est amorçable tôt (pas de squelette de
bois à `broyer`, pas de plante à paille cultivée à `recolter_paille`) → impasse
`RAVITAILLEMENT_MANQUANT` (`tools/jardinier_auto/impasses.py`). L'automate
distingue déjà ce cas d'un `GESTE_VERROUILLE` (maîtrise) → c'est bien la
**matière** qui manque, pas la maîtrise.

**Garde-fous** : philo **#1** (action directe sur le vivant permise mais coûteuse
et perturbatrice — l'outil raffine, il n'est pas un prérequis binaire) ; **#2**
(réponse émergente — le seam structurel, pas de +X codé) ; **#3** déterminisme,
zéro RNG ; **#6** apprentissage diffus (la main déchire / l'outil coupe net =
enseignement par l'usage). **« Tout coexiste »** : le mulch VIENT de quelque part.
**Golden INTACT sur tout le sprint** : tous les gestes et acquisitions sont
**opt-in joueur, hors tick** ; le smoke est une succession sans joueur.

---

## A. Gradient de gestes structurels — FIGÉ

Un seul continuum, du plus doux au plus net. L'outil n'est PAS un prérequis : à
mains nues on pince ou on arrache déjà. Le sécateur débloque la coupe **sans
blessure**, pas « couper » tout court.

| Geste | Régime seam (`intensite`) | Outil | Vigueur | Effet propre | Déblocage |
|---|---|---|---|---|---|
| `pincer` | DOUX (`< COUPE_NETTE`) | main | FAIBLE | baisse auxine locale → débourrement ÉMERGENT au tick, **aucun retrait** | **BASE** |
| `arracher` | NET (`≥ COUPE_NETTE`) | main | ÉLEVÉ | écimage + dépôt litière `bois` + **`erode()` vitalité** (stress cicatriciel de la déchirure) | **BASE** |
| `couper` | NET (`intensite=1.0`) | sécateur | MODÉRÉ | écimage + litière `bois`, **PAS d'erode** (coupe nette) | `posseder_secateur` |
| `tailler` | NET + segment au clic | sécateur | MODÉRÉ | idem `couper`, branche désignée à la souris | `couper` |

- **`couper`/`tailler` sont DÉJÀ implémentés** (`tools/simserver/actions.py:176`,
  `sim/actions/gestes.py:260`) : écimage NET via `atteindre_segment(intensite=1.0)`
  + dépôt `bois`. Ils N'érodent PAS la vitalité aujourd'hui → **on ne les touche
  pas**. Ce sont les gestes-outil du gradient.
- **Le différenciateur main/outil = `erode()`** : `arracher` (déchirure) appelle
  `plant.erode(VITALITE_STEP)` — le MÊME `erode` que `ecraser_plante`
  (`gestes.py:396`) ; `couper`/`tailler` (net) ne l'appellent pas. **Pas de champ
  « propreté » neuf** — le différenciateur est purement comportemental.
- **`pincer`** réutilise le régime DOUX du seam (`atteindre_segment` avec
  `intensite < COUPE_NETTE`) : baisse d'auxine, aucun segment retiré, débourrement
  émergent au `grow_plant` suivant (philo #2). Rien déposé au sol.
- **Bouture viable réservée à l'outil, GRATUITEMENT** : `bouturer`
  (`sim/actions/bouture.py`) est déjà en aval du sécateur dans la chaîne
  (`("et", taille≥2 & semis≥2)`) → quand on peut bouturer, on possède le sécateur.
  `bouturer` **n'est pas touché**.

### A.1 Plomberie moteur
- `sim/actions/gestes.py` : ajouter `pincer` et `arracher` (façades, sur le modèle
  de `tailler` : gate coût → seam → dépôt litière pour `arracher`).
- `sim/actions/couts.py` : `COUTS["pincer"]=FAIBLE`, `COUTS["arracher"]=ELEVE` ;
  `OBJETS_TOUCHES["pincer"]=("taille",)`, `["arracher"]=("taille",)` (famille
  taille, **sans outil** → la maîtrise taille atténue, aucun outil requis).
- `sim/actions/palette.py` : `"pincer":"plante"`, `"arracher":"plante"`.
- `tools/simserver/actions.py` : dispatch `pincer`/`arracher` (patron `couper`),
  messages diégétiques ; bump protocole.

---

## B. Acquisition du sécateur — Atelier + registre `OUTILS` — FIGÉ

- **Canal = Atelier** (hub-maison, seule des 5 fonctions non câblée). Commande
  Vigueur-seule, **miroir d'`acheter_au_magazine`** (`sim/magazine.py`) : gate une
  offre + débite la Vigueur + **pose un marqueur d'outil** (au lieu de déposer une
  graine).
- **Nouveau module `sim/outils.py`** (jumeau de `sim/magazine.py`) :
  - Registre **`OUTILS`** data-driven : `{"secateur": {"marqueur":
    "posseder_secateur", "cout_vigueur": <placeholder calibrage F5>, "offre":
    True}}`. Extensible (greffoir/bêche plus tard) — **sécateur seul pour l'instant**.
  - `acquerir_outil(game_state, player, outil) -> bool` : gate offre + fonds ;
    `spend` Vigueur ; `marquer_action(gs, player, marqueur)` +
    `evaluer_deblocages(gs, player)` (`sim/actions/deblocage.py`). Bool, jamais
    d'exception (refus si offre fermée / fonds insuffisants). Déverrouille
    `couper` → `tailler`.
- `tools/simserver/actions.py` : verbe **`acheter_outil`** (patron
  `acheter_magazine`, chemin Vigueur UNIQUE, sans tuile) ; bump protocole.
- **Porte** : Vigueur seule, **tôt** (aucune maîtrise — évite le poule-œuf `taille`).
  Le sécateur est de l'outillage d'entrée de gamme.

---

## C. Ravitaillement en mulch — 3 canaux — FIGÉ

Gradient d'approvisionnement parallèle à l'acquisition d'espèce (succession /
événement / magazine). Lève l'impasse `RAVITAILLEMENT_MANQUANT`.

1. **`glaner` — geste BASE, cycle INTERNE** (lève l'impasse à la racine).
   Ramasse la `litiere` de surface tendre d'un plot → crédite `mulch_stock` nature
   **« feuilles »** (nouvelle nature dans `NATURES_MULCH`,
   `fields/ecofields/constants.py:1050`). Réutilise le patron
   `_ramasser_vers_structure` (`sim/actions/compost.py:44`) mais vers le STOCK, pas
   une structure. Amorçable dès qu'il y a des feuilles tombées (la décompo en
   produit toujours un peu). Coût FAIBLE (geste rustique). Façade dans
   `sim/actions/paillage.py` (là où vit déjà le stock) ; `COUTS`/`palette`/dispatch
   serveur ; bump protocole.
2. **Graine de paille au départ — cycle INTERNE cultivé.** `"ble"`/`"chanvre"`
   (`plants/catalogue.py:60`, `mulch_source` déjà posé) accessibles tôt → cultiver
   → `recolter_paille` alimente le stock `paille`. Ajout à `BANQUE_DEPART`
   (`tools/simserver/commands.py:37`) **et** vérifier la config par défaut (la
   banque de départ n'est peuplée qu'en config `full` — s'assurer que blé/chanvre
   est réellement accessible tôt, sinon les verser à l'offre magazine amorce). Pas
   de code neuf, données seulement.
3. **Import Atelier (Vigueur) — cycle EXTERNE.** L'Atelier fournit une botte
   paille/BRF contre Vigueur. Cadré comme **import externe parallèle au magazine
   de graines** (le magazine importe déjà des espèces « de l'extérieur ») → PAS
   « mulch abstrait », le principe de `paillage.py` (cycle interne sourcé) tient.
   Réutilise l'infra d'acquisition Atelier du §B : registre **`MATERIAUX`**
   data-driven `{"botte_paille": {"nature":"paille", "dose":<X>, "cout_vigueur":
   <Y>}}` + verbe **`acheter_materiau`** (crédite `mulch_stock[nature] += dose`).

---

## D. Philo & interconnexions

- **#1** : `arracher`/`ecraser_plante` — l'action directe sur le vivant est permise
  mais coûte (Vigueur ÉLEVÉE) et perturbe (`erode`). L'outil raffine la solution.
- **#2** : `pincer` ne code aucun débourrement ; il baisse l'auxine, le tick
  PRODUIT la réponse.
- **#3** : zéro RNG — gestes et acquisitions déterministes.
- **#6** : la différence déchiré/net s'apprend à l'usage (la plante arrachée
  souffre, la coupe nette non).
- **Interconnexions** : `glaner` relie décompo (`litiere`) → paillage → germination/
  humidité/champignons ; `arracher`/`couper` → litière `bois` → décompo ; sécateur
  → chaîne taille → `bouturer` (multiplication) ; Vigueur ↔ Atelier ↔ maîtrise.

## E. Voix narratives

Pas de nouvelle espèce → **pas de fiche 5-voix**. Couverture légère : messages
diégétiques de chaque geste (déjà le patron des façades serveur) + marqueur au
ledger joueur (acquisition sécateur, premiers pincer/arracher/glaner). Le **carnet
interprétatif « la coupe déchirée a stressé la plante »** (révélé au seuil de
maîtrise taille) est REPORTÉ en **dette D54** (là où vit l'interprétation) — pas
ouvert ici.

## F. Perf & golden

**Aucun coût de tick** : tout est opt-in joueur, hors boucle de simulation. Le
smoke golden est une succession **sans joueur** → aucun de ces gestes/acquisitions
n'est exercé → **golden INTACT sur les 4 tronçons, zéro re-figeage**. Ajout de la
nature `feuilles` : les lecteurs nature-aware du tick ne la voient que si un
paillage `feuilles` existe → jamais dans le smoke (paillage=0) → NEUTRE.

---

## L. Découpage — 4 tronçons (perf-first, golden INTACT partout)

- **① Gestes manuels** (`gestes.py`, `couts.py`, `palette.py`, dispatch serveur,
  tests ciblés) — `pincer` + `arracher`. Répond au F5 « pas d'option couper »
  (un geste structurel d'emblée). Golden inchangé.
- **② Acquisition Atelier + registre `OUTILS`** (`sim/outils.py` neuf, verbe
  `acheter_outil`, `marquer_action`+`evaluer_deblocages`, tests : avant = couper
  refusé, après acquisition = couper/tailler déverrouillés) — **CŒUR D82**. Golden
  inchangé.
- **③ Ravitaillement mulch** — `glaner` (base, litière→stock, nature `feuilles`) +
  graine paille au départ (données) + import Atelier (`MATERIAUX`,
  `acheter_materiau`). Lève l'impasse `RAVITAILLEMENT_MANQUANT` (vérifier via
  `jardinier_auto`). Golden inchangé (NEUTRE).
- **④ Vue Godot** (F5 Nico) — Atelier cliquable (patron panneau D54) exposant
  **outils + matériaux** ; menu gestes plante enrichi (`pincer`/`arracher` +
  `couper`/`tailler` une fois le sécateur acquis) ; menu milieu `glaner` ; pont des
  nouveaux verbes. Tronçon vue obligatoire (règle 2026-07-03), golden intact.

**Calibrage F5 (placeholders)** : coûts Vigueur `pincer`/`arracher`/`glaner`, coût
d'acquisition sécateur, dose/coût botte de paille. À affiner après observation.
