# Tronçon ④ — Matériau du paillage : `broyer`→BRF + récolte paille → stock + 3 natures

**Prérequis** : `CLAUDE.md`, `00_etat.md`, `CONCEPTION_EQUILIBRE_INVASION.md` §3.
Patrons : `sim/actions/compost.py` (`epandre`/`composter`, jauges de structure),
`sim/actions/gestes.py::recolter`, `bois_restant` des squelettes (décompo·compost
②B), `sim/actions/couts.py`.

## Objectif
Donner une SOURCE au mulch (interconnexion) et **trois natures** aux propriétés
distinctes. `pailler` (③) consomme désormais un **stock** alimenté par :
- **`broyer`** : transforme du **bois** (`bois_restant` d'un squelette au sol, ou
  une pile de bois) en **BRF** ;
- **récolte** de plantes à paille (blé/chanvre → paille ; sapin → aiguilles/BRF,
  cf. ⑤).

## Fichiers à toucher
1. **`sim/actions/gestes.py`** (ou nouveau `sim/actions/paillage.py` si la taille
   l'exige) — `broyer(game_state, player, eco, r, c, ...)` : consomme du
   `bois_restant`/pile → incrémente le **stock BRF** ; coût Vigueur (`couts.py`).
   Brancher `recolter` : une plante à paille récoltée alimente le stock paille.
2. **Stock de mulch** — jauge par nature (`{"brf":.., "paille":.., "aiguilles":..}`),
   rangée dans `game_state` (patron `player_seed_bank`/`compost_mur`). `pailler`
   (③) décrémente la nature demandée ; refus en amont si stock vide (aucune
   Vigueur dépensée, patron `epandre`).
3. **Natures data-driven** — un dict `NATURES_MULCH` (module `sim/paillage.py` ou
   `fields/ecofields/paillage.py`) : par nature, les propriétés
   `{decay, om_w, humidite_w, n_hunger, ph_shift, allelo, abri_w, fongique}` :
   - **BRF** : decay lent, `n_hunger>0` (faim d'azote → retire un peu de `n` en
     surface via le couplage NPK `nutriments.py`), `fongique=True` (hook mycélium :
     marquer le plot riche en bois pour `fields/ecofields/mycelium.py`).
   - **Paille** : decay moyen, `humidite_w` fort, reste neutre.
   - **Aiguilles** : decay lent, `ph_shift<0` (acidifie via `ph.py`), `allelo>0`
     (petit frein germination en plus).
   Le tick de décompo (③) et les lectures (germination/ET/pH/NPK) lisent ces
   propriétés selon la nature DOMINANTE du plot (stocker la nature par plot, ou un
   champ léger `paillage_nature`).

## Golden
**INTACT**. Gestes event-driven, natures inertes tant que `paillage=0` au repos ;
le smoke n'appelle ni `broyer` ni `pailler`. Vérifier `test_golden`/`test_population`
inchangés. Étendre `tests/test_paillage.py` : BRF crée une faim d'azote locale,
aiguilles baissent le pH, paille retient l'humidité.

## NE PAS
- Pas de dépendance DURE au mycélium (simple hook/marqueur, il peut ne pas être
  branché). Pas de RNG. Respecter les couches (`plants ← fields ← sim`).

## Vérif / F5
Test : broyer du bois donne du BRF ; pailler en BRF crée `n_hunger` ; en aiguilles
baisse le pH ; le stock se vide. F5 = ⑧.
