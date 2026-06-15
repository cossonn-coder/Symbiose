# Dette D18 — Pages secrètes (savoirs épars, ésotériques)

> **Kickoff autosuffisant.** Lis ce fichier en entier, puis les sources, puis
> exécute. Français + pédagogie. **Conception SEULE d'abord** (`CONCEPTION_PAGES_
> SECRETES.md`, valider avec Nico, puis impl.). Ampleur **moyenne**.

## Ce que c'est, en une phrase
Concevoir les **pages secrètes** : la 3ᵉ voix narrative — **connaissances perdues,
éparses, ésotériques**, trouvées **par hasard**, gagnées **après une belle
réalisation**, ou découvertes **en fouillant**. Voix **multiples** (extraits
poétiques, savoirs paysans, herbiers anciens, citations type Fukuoka /
Sackville-West / sorcières médicinales). Consultation **au coffret du grenier**.

## Le contexte (CLAUDE.md)
- **CLAUDE.md, « Trois voix narratives »** : pages secrètes = la voix la plus libre,
  **non systématique**, par opposition à l'encyclopédie (déterministe, complétée aux
  découvertes) et au carnet (auto, première personne). Elle porte le **lore** et la
  **poésie**, pas l'information de jeu opérationnelle.
- **Source d'histoire émergente** : CLAUDE.md « Histoire émergente via les événements
  rares (bouture, oiseau, vent). » Les pages secrètes sont **un des butins** de ces
  événements rares — pas une quête, pas un PNJ, pas un narrateur omniscient (interdits
  explicites).
- **Lieu** : « coffret au grenier de la maison » (la maison normande = hub, 5
  fonctions ; le grenier/coffret = 6ᵉ recoin, consultation des pages).

## Ce qui est déjà tranché (ne pas re-débattre)
- **Pas de quête, pas de PNJ, pas de narrateur externe.** Les pages se *trouvent*,
  elles ne sont pas *données par* quelqu'un.
- **Trois voies d'obtention** : hasard / récompense d'une belle réalisation / fouille.
- **Voix multiples**, registre poétique/ésotérique/paysan. Ce n'est **pas** de
  l'information de gameplay (≠ encyclopédie) — c'est de l'**ambiance et du sens**.
- Consultation **au coffret du grenier**.

## 🔵 Choix de design à trancher
### Choix 1 — Le « contenu » est-il pré-écrit ou génératif ?
- **(A) ⭐ Corpus pré-écrit, fini, débloqué par fragments.** Une collection de N
  pages (citations, extraits, recettes de grand-mère, notes d'herbier) **rédigées à la
  main**, révélées une à une. **Pour** : qualité littéraire maîtrisée (c'est le but —
  de la *belle* écriture), déterministe, traduisible, golden-neutre. **Contre** :
  volume éditorial à produire (mais c'est *le* livrable de valeur, pas la mécanique).
- **(B) Génération procédurale** (assemblage de fragments) : volume infini, mais
  qualité littéraire fragile — un texte « ésotérique » généré sonne vite creux. Va à
  l'encontre de la promesse (« belle réalisation → belle page »). **Déconseillé** pour
  cette voix précise.

> Reco : **(A)** — corpus fini, soigné. C'est la voix où la **main** se sent. Le
> volume cible v1.0 est un point ouvert (DETTE.md) : commencer petit (~15-25 pages)
> et enrichir. **Sujet hors expertise technique** : produire le corpus comme
> **livrable éditorial** à relire, pas du code.

### Choix 2 — Comment se déclenche une trouvaille ? (déterminisme vs surprise)
Le jeu est **déterministe** (seed global) mais les pages doivent *sembler* fortuites.
- **(A) ⭐ Déterministe-mais-imprévisible** : la trouvaille est ancrée sur un événement
  rare déjà émis par le moteur (`_hash_noise(seed, …)` → bouture/oiseau/vent) ou sur un
  **succès de maîtrise marquant** (palier franchi, naturalisation férale §9.4). Le
  joueur ne peut pas la *prévoir*, mais elle est **reproductible** (même seed → même
  page au même moment). **Pour** : respecte la philo #3 (déterminisme) **et** la
  promesse de hasard. **Contre** : aucun vrai — c'est le bon modèle.
- **(B) RNG live** : casse le déterminisme (interdit, philo #3). **Exclu.**

> Reco : **(A)**. Trois robinets : **hasard** = adossé aux événements rares déjà
> déterministes ; **récompense** = adossé aux succès de maîtrise (réutilise
> `maitrise_detection.py`) ; **fouille** = action joueur au grenier/jardin qui
> *révèle* une page déjà « due ».

### Choix 3 — Y a-t-il un lien mécanique avec le gameplay, ou pur lore ?
- **(A) ⭐ Pur lore, zéro effet mécanique.** Une page ne donne **aucun** bonus (ni
  Vigueur, ni déblocage). Elle existe pour le sens, l'ambiance, la curiosité. **Pour** :
  fidèle à CLAUDE.md (les pages ne sont pas un canal d'acquisition — ça, c'est le
  magazine D13) ; aucune pression d'optimisation sur une voix qui doit rester
  contemplative ; golden trivialement intact. **Contre** : aucun (c'est le but).
- **(B) Indices voilés** : une page *suggère* une technique sans la débloquer
  (l'apprentissage reste au joueur). Tentant, mais brouille la frontière avec
  l'encyclopédie/carnet. Reportable.

> Reco : **(A)** — pur lore. Le plaisir est la **trouvaille** et la **lecture**, pas
> un gain. (Si plus tard tu veux des indices, ce sera un raffinement, pas la v1.)

## Périmètre — phase CONCEPTION (livrable)
`docs/conception/CONCEPTION_PAGES_SECRETES.md` actant : les 3 choix ; les **3 robinets**
d'obtention (hasard ↔ événements rares ; récompense ↔ succès de maîtrise ; fouille ↔
action grenier) ancrés sur des signaux **déterministes existants** ; l'**interface**
(`pages_trouvees(game_state, player)`, `reveler_page(...)` appelée par le driver,
**hors tick**) ; le **bornage** (corpus fini, état = ensemble d'IDs révélés, trivial à
sauver) ; et le **corpus initial** (~15-25 entrées rédigées, livrable éditorial à
relire).

## Hors périmètre
L'**UI Godot** du coffret/grenier (frontend). Le **rendu** des pages (typographie,
parchemin). Tout **effet mécanique** (Option B, backlog). Le **magazine** D13 (canal
d'acquisition — voix et rôle différents). Portage C# (D24).

## Golden / vérification
Conception = zéro code. À l'impl. : pages = event-driven hors tick, **pur read-only**
→ **golden intact**. Tests : une page se révèle sur le bon déclencheur, l'ensemble
des IDs révélés persiste, aucune page ne donne d'effet mécanique. MAJ `DETTE.md` D18
(volume cible v1.0 fixé) + `BACKLOG.md`.
