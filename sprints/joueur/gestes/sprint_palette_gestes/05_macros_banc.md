# ⑤ MACROS + PERSISTANCE LAYOUT + BANC F5 — kickoff autosuffisant

> Sprint PALETTE DE GESTES. Lire d'abord : `CLAUDE.md` + `00_etat.md` +
> `docs/joueur/gestes/conception_palette_gestes.md` §3.1/§3.7 (D1/D5/D10).
> Démarre à FROID. Prérequis : ①→④ faits (palette gauche cliquable en place).
> Dernier tronçon = VUE (règle projet). F5 visuel = Nico.

## Objectif
1. **Macros joueur** (D1/D5) : le joueur enregistre une **séquence de gestes**
   rejouée sur la **MÊME cible/point** au clic (ex. planter → pailler → arroser
   ICI). Chaque sous-geste **paie sa Vigueur** (philo #1 : la macro ne gomme pas
   l'usure). Pas de pinceau balayé sur zone (écarté, D5).
2. **Persistance du layout** (D10) : `game_state["palette"][player]` = slots
   curés + macros, par avatar, dans la save JSON (un seul save, règle projet).
3. **Banc d'observation F5** : un banc montable qui met la palette + le déblocage
   + bouture/greffe en évidence pour la recette F5 de Nico.

## Modèle des macros
- Une macro = liste ordonnée de `(verbe, params_fixes?)`. Au clic sur une cible,
  la vue joue la séquence : pour chaque sous-geste, elle envoie l'appel au pont
  avec la MÊME cible (même `(tile, r, c)` / même plante / même point monde), dans
  l'ordre. **Aucun calcul de simulation supplémentaire** : c'est N appels de
  gestes séquencés (le pont les exécute un par un ; chaque `spend` de Vigueur
  s'applique → si la Vigueur s'épuise en cours, les gestes suivants échouent
  proprement, comportement binaire déjà en place côté moteur).
- **Où vit la macro** : la DÉFINITION (séquence) est une DONNÉE persistée côté
  Python (`game_state["palette"][player]["macros"]`), la vue la LIT du snapshot et
  la REJOUE (envoi séquentiel). Pas de logique de sim neuve : le moteur ne
  « connaît » pas les macros, il reçoit juste des gestes normaux.
- **Cohérence des cibles** : une macro n'a de sens que si tous ses sous-gestes
  acceptent la même famille de cible (ex. plot `m` : planter+pailler+arroser).
  Interdis/avertis une macro mêlant des Kinds incompatibles (ex. plante `p` +
  plot `m`) — validation SIMPLE côté enregistrement.
- **Enregistrement** : UI minimale — le joueur entre en « mode enregistrement »,
  sélectionne des gestes dans l'ordre, valide → la macro devient un slot de la
  palette (avec sa propre icône composite ou une puce « macro »).

## Fichiers à toucher
- **Python** :
  - Sérialisation save : ajoute `game_state["palette"][player]` (slots + macros)
    au write/read de la save (miroir de `gestes_debloques` du tronçon ①).
  - Expo snapshot : le bloc `player` porte `palette` (slots curés + macros) pour
    que la vue le relise. Bump `ENGINE_VERSION` (→ 0.5.26) + commentaire (tolérance
    pré-0.5.26 : clé absente → palette par défaut côté vue).
  - Commande pont pour PERSISTER un changement de layout/macro (le joueur cure sa
    palette en jeu → la vue envoie l'état à sauver). Repère le patron des commandes
    read/write existantes (`tools/simserver/commands.py`).
  - **Aucun geste neuf, aucune logique de tick.** Golden NEUTRE.
- **C# / Godot** :
  - `world/WorldView.Actions.cs` (+ éventuel partial dédié `WorldView.Palette.cs`
    si ça déborde la bande de taille — cf. garde-fou CLAUDE.md) : mode
    enregistrement, rejeu séquentiel d'une macro sur la cible cliquée, curation
    des slots, lecture/écriture du layout via le pont.
  - Icône de slot macro dans la palette gauche (④).
- **Banc F5** : ajoute une config de banc montable (cf. les bancs existants,
  `grep -rn "list_bancs\|config=" tools/simserver/ data/code/`) — ex.
  `config="palette_gestes"` : quelques plantes bouturables/greffables matures +
  un avatar avec quelques maîtrises débloquées, pour tester palette+bouture+greffe
  d'un coup. Jamais monté pour smoke/full (golden intact).

## Golden
**INTACT** (`452b5256…`). Rien dans le tick ; macros = rejeu de gestes
event-driven ; layout = donnée persistée. `python3 -m tests.test_golden`.
`dotnet build Symbiose.csproj` compile.

## Ne PAS faire
- Pas de pinceau balayé sur zone (D5, écarté).
- Pas de macro qui esquive la Vigueur (chaque sous-geste paie, philo #1).
- Pas de logique de simulation neuve côté moteur (les macros vivent en
  donnée + rejeu de gestes existants).
- Pas de multi-save (un seul save par profil, règle projet).

## Vérifs de fin
1. Golden inchangé ; `dotnet build` OK.
2. Test ad hoc `tests/` : une macro `[planter, pailler, arroser]` rejouée sur un
   plot déclenche les 3 gestes dans l'ordre, chacun débité en Vigueur ; Vigueur
   insuffisante en cours → les suivants échouent proprement.
3. Persistance : curer la palette + définir une macro → sauver → recharger → le
   layout revient (save JSON contient `palette`).
4. Banc F5 montable ; relève F5 pour Nico (palette gauche + icônes + déblocage +
   bouture/greffe + macro rejouée).
5. **Clôture sprint** : MAJ `journal.md` (entrée sprint PALETTE DE GESTES),
   `DETTE.md` + `BACKLOG.md`, finalise `00_etat.md`. Supprime les HANDOFF obsolètes.
