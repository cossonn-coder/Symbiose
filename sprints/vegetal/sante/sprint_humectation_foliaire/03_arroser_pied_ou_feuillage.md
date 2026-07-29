# ③ `arroser` — au pied ou au feuillage, le geste qui rend le dilemme jouable

**Sprint** : `sprint_humectation_foliaire` · **Golden attendu : NEUTRE (inchangé)**
**Conception** : `docs/vegetal/sante/conception_humectation_foliaire.md` §2.5, §2.3
**Prérequis** : ① et ② livrés.

## Objectif

Donner au joueur le **levier** que le ② vient de rendre signifiant : arroser au pied
(neutre pour le feuillage) ou asperger le feuillage (mouille → mildiou ↑, oïdium ↓).

Sans ce tronçon, la correction du ② est juste mais **muette** : le joueur n'a aucun
moyen d'exprimer le bon geste.

## Fichiers à toucher

1. `data/code/fields/ecofields/container.py` — la carte transiente `aspersion_last`
   (patron `rosee_last`, ~lignes 173 et 413)
2. `data/code/sim/actions/gestes.py` — `arroser` (~ligne 162)
3. `data/code/sim/engine/croissance.py` — le terme `ASPERSION_WET_GAIN` dans l'humectation
4. `data/code/sim/engine/boucle.py` — remise à plat de la carte transiente
5. `data/code/tools/simserver/actions.py` — le pont (~ligne 247)
6. `data/code/tools/simserver/version.py` — bump `ENGINE_VERSION` (0.5.41 → **0.5.42**)

## Modèle

### La carte transiente

Sur le patron **exact** de `rosee_last` (`container.py:173` pour la déclaration, `:413`
pour l'init paresseuse) :

```python
aspersion_last:   GridField = field(default=None)
```

**Transiente** : remise à plat **chaque tick**, comme `rosee_last` l'est en tête de
`tick_rosee`. Choisis un point de remise à plat **déterministe et unique** dans la boucle
(avant `_update_physiology`, après l'application des gestes du tick) et **documente-le en
commentaire** : c'est un piège de décalage d'un tick si on se trompe.

### Le geste

```python
def arroser(game_state: dict, player: str, eco, r: int, c: int,
            urgence: bool = False, feuillage: bool = False) -> bool:
```

- `feuillage=False` (**défaut**) — comportement **strictement inchangé** : écrit
  `eco.humidite` seul. Tous les appelants existants restent bit-identiques.
- `feuillage=True` — écrit `eco.humidite` **et** `eco.aspersion_last.set(r, c, DOSE_ARROSAGE)`.

**Coût Vigueur identique dans les deux modes.** Décision de conception §2.5 : le choix est
écologique, pas économique. On ne punit pas le mauvais geste par le prix — on le laisse
produire sa conséquence (philo #6, apprentissage diffus). Ne rajoute **pas** de
multiplicateur de coût.

Le geste reste binaire tout-ou-rien (si la Vigueur ne couvre pas, **rien** n'est écrit —
ni `humidite`, ni `aspersion_last`).

### Le terme d'humectation

Dans `_update_physiology`, complète le `mouillage` du ① :

```python
asp = getattr(eco, "aspersion_last", None)
aspersion = 0.0
if asp is not None and plant.foliar_plots:
    aspersion = sum(asp.at_plot(fr, fc) for (fr, fc) in plant.foliar_plots
                    if 0 <= fr < eco.rows and 0 <= fc < eco.cols)
    aspersion /= len(plant.foliar_plots)
mouillage += ASPERSION_WET_GAIN * min(1.0, aspersion / DOSE_ARROSAGE)
```

Même patron que la rosée : moyenne sur l'empreinte foliaire (on asperge une canopée, pas
un point). `getattr` défensif → un `eco` sans la carte (pots/bacs, outils) reste inerte.

### Le pont

`tools/simserver/actions.py:247` appelle `A.arroser(gs, player, eco, r, c, urgence=urgence)`.
Ajoute le mode, **par défaut au pied** :

```python
feuillage = bool(payload.get("feuillage", False))
ok = A.arroser(gs, player, eco, r, c, urgence=urgence, feuillage=feuillage)
```

Bump `ENGINE_VERSION` → `"0.5.42"` et documente le champ neuf dans l'en-tête de
`version.py` (le fichier tient l'historique du protocole — respecte sa forme).

## Golden

**NEUTRE, bit-identique.** Le smoke test ne joue **aucun** geste `arroser` : la carte
`aspersion_last` reste nulle partout, le terme `ASPERSION_WET_GAIN` est donc nul, et le
défaut `feuillage=False` préserve tous les appelants.

Vérifie que la **remise à plat** de la carte n'a pas d'effet de bord (elle écrit des 0
dans un champ que personne d'autre ne lit).

## Ce qu'il ne faut PAS faire

- ❌ Changer le coût Vigueur selon le mode (§2.5 — décision explicite).
- ❌ Faire de `feuillage` le défaut : le geste par défaut reste le bon geste.
- ❌ Écrire `aspersion_last` quand la Vigueur est insuffisante (tout-ou-rien).
- ❌ Rendre `aspersion_last` persistante (c'est une transiente du tick, patron `rosee_last`).
- ❌ Toucher `tick_hydrology` (§1.2, D39).
- ❌ Lancer `test_epaisseur_500ans` (interdit).

## Vérification

1. `python3 -m tests.test_golden` → hash **inchangé** (celui re-figé au ②).
2. Étends `tests/test_humectation.py` : (a) `arroser(feuillage=False)` laisse
   `wetness_memory` **inchangée** au tick suivant ; (b) `arroser(feuillage=True)` la fait
   monter ; (c) les deux montent `eco.humidite` **pareil** ; (d) Vigueur insuffisante →
   ni `humidite` ni `aspersion_last` touchés.
3. `python3 main.py` tourne sans crash.
4. `python3 tools/compte_ldc.py` sur les fichiers touchés.
