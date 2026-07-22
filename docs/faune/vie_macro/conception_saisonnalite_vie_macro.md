# Conception — Saisonnalité de la vie macroscopique (SYMBIOSE)

> **Document de conception. Aucun code moteur écrit.** Spec de référence pour le
> sprint de calibrage de la **saisonnalité** des 4 guildes de vie macro
> (ravageur, auxiliaire, pollinisateur, vers de terre). Touche `fields/population.py`
> (le cœur écolo) → **re-figeage golden maîtrisé annoncé** (l'herbivorie lit le
> champ `ravageur` depuis D31.2).
>
> Issu du retour F5 t6·B de Nico (gravé 2026-06-12, BACKLOG.md) : *« la vie
> grouille encore en hiver et ne se réveille qu'à l'été »*. Décisions de cadrage
> (2026-06-16) : **photopériode + inertie asymétrique**, **une fenêtre par guilde**,
> **doc d'abord**. Prépare l'arc **pollinisation & cycle de vie** (la floraison
> réelle et la phénologie florale viendront s'appuyer sur la même horloge
> saisonnière). S'appuie sur `docs/faune/vie_macro/conception_vie_macro.md` (le modèle hybride d'origine)
> et `docs/champs/climat/conception_meteo.md` §1.1 (la normale de température `temp_norm`).

---

## 0. Le constat de départ (diagnostic chiffré)

Le tick d'une guilde (`PopulationField.tick`, `fields/population.py`) calcule :

```
capacité = clamp(resource_w·ressource + habitat_w·habitat + signal_fruit, 0, 1)
survie   = warmth · (1 − pred_w·prédation) · (1 − disturb_w·perturbation)
cible    = capacité · survie
champ'   = clamp(champ·INERTIE + cible·(1−INERTIE), 0, POP_MAX)
```

La **seule** modulation saisonnière aujourd'hui est `warmth`, une rampe sur la
température instantanée de l'air :

```
warmth = clamp01((T − T_COLD_ZERO) / (T_WARM_FULL − T_COLD_ZERO))   # T_COLD_ZERO=6, T_WARM_FULL=24
```

Avec la normale océanique normande `T = T_MOY − T_AMP·cos(2π(w−4)/52)`
(`T_MOY=11`, `T_AMP=7`, min wiy≈4, max wiy≈30) on obtient :

| Moment | wiy | T (°C) | warmth | Effet observé |
|---|---|---|---|---|
| Début hiver | 40 | ~13.5 | **0.42** | la pop reste nourrie |
| Cœur hiver | 4 | ~4.5 | **0** | dormance OK |
| Début printemps | 1 | ~4.5 | **0** | mort |
| Fin printemps | 14 | ~8.5 | **0.14** | réveil très mou |
| Pic été | 30 | ~18 | 0.67 | plein régime |

**Deux pathologies, exactement celles pointées par Nico :**

1. **Décrue automnale traînante.** `warmth ≈ 0.42` début hiver **et** l'inertie
   `POP_INERTIA = 0.85` est **symétrique** → `0.85¹³ ≈ 0.12` : ~13 semaines pour
   s'éteindre. La vie grouille jusqu'en plein hiver.
2. **Réveil purement thermique et tardif.** `warmth` ne dépend que de la
   température *instantanée*. En climat doux elle monte lentement → réveil mou.
   Pire : un **Redoux** (event météo `+5 °C`, `weather.py`) ferait *remonter* la
   pop en novembre — ce qui est biologiquement faux.

---

## 1. La brique manquante : la photopériode

En écologie, la **diapause / dormance** de la plupart des insectes et de la
petite faune est déclenchée par la **longueur du jour** (photopériode) qui
raccourcit en automne — **pas** par la température seule.

> **Pourquoi (pédagogie domaine).** La longueur du jour est un signal
> *anticipateur* parfaitement fiable et déterministe : le 21 septembre dure le
> même nombre d'heures chaque année, quelle que soit la météo. La température,
> elle, est bruitée (un redoux, une vague de froid). Les organismes qui se
> préparent à l'hiver (entrée en diapause, accumulation de réserves) se fient
> donc à la lumière, pas à la chaleur du jour. Au printemps, le réveil combine
> **jours qui rallongent** (le signal) **+ seuil thermique franchi** (la
> permission). C'est le « pas seulement la température » demandé.

Conséquence de modèle : on sépare **deux signaux complémentaires** :

- **`phenology(wiy)`** = *QUAND* la guilde est active dans l'année (porte
  saisonnière, photopériodique, robuste aux redoux) ;
- **`warmth(T)`** = *COMBIEN* elle prospère quand elle est active (intensité,
  sensible aux coups de chaud/froid ponctuels).

`warmth` reste **inchangé** (il gère l'intensité estivale et la pénalité des
gelées/canicules). On lui adjoint `phenology` comme **porte** :

```
survie = phenology · warmth · (1 − pred_w·prédation) · (1 − disturb_w·perturbation)
```

Pas de double comptage problématique : en hiver les deux tombent à 0 (dormance
franche, renforcée) ; au **printemps frais mais lumineux**, `phenology` monte
*avant* `warmth` → léger réveil anticipé piloté par la lumière, confirmé ensuite
par la chaleur. C'est le réalisme visé.

---

## 2. Longueur du jour analytique `daylength(wiy)`

Photopériode à ~49°N (Normandie), sinusoïde simple bornée 8 h ↔ 16 h :

```
daylength(wiy) = 12 + 4·cos( 2π·(wiy − W_SOLSTICE_ETE) / 52 )      # en heures
```

avec `W_SOLSTICE_ETE = 25` (jour le plus long ≈ fin juin dans le calendrier du
jeu — il **précède** le pic thermique wiy≈30 d'environ 5 semaines, le déphasage
saisonnier réel). Vérification :

| wiy | 1 | 14 | 25 | 30 | 40 | 51 |
|---|---|---|---|---|---|---|
| daylength (h) | ~8.2 | ~14.9 | **16.0** | ~15.2 | ~10.5 | **~8.0** |

- Fonction **PURE** de `wiy` (aucun RNG, philo #3) → déterministe.
- Bornes 8/16 h = placeholders calibrage, alignés sur la latitude visée.
- Réutilisable plus tard par l'arc pollinisation (phénologie florale) et par les
  signes diégétiques météo.

> **Pourquoi `cos` et pas la vraie formule astronomique ?** Le déclinaison
> solaire exacte (arccos d'un produit de sin/tan de latitude) est plus précise
> mais illisible et superflue : à l'échelle du jeu, une sinusoïde de bonne
> amplitude/phase est indiscernable et reste calibrable d'un coup d'œil.

---

## 3. Facteur phénologie par guilde `phenology(wiy)`

`daylength` est convertie en activité `[0,1]` par une **rampe douce** (smoothstep)
entre deux seuils **propres à chaque guilde** (décision « une fenêtre par
guilde ») :

```
phenology = smoothstep( daylength(wiy), DAYLEN_MIN, DAYLEN_FULL )
# = 0 si daylength ≤ DAYLEN_MIN ; 1 si ≥ DAYLEN_FULL ; transition lisse entre
```

Comme `daylength` est **non-monotone** (monte au printemps, redescend en
automne), une seule rampe sur cette grandeur produit **automatiquement** le
réveil printanier ET la dormance automnale, sans calendrier en dur : la guilde
s'éteint quand les jours repassent sous son seuil, des deux côtés du solstice.

Seuils par guilde (placeholders calibrage post-test, §6) :

| Guilde | `DAYLEN_MIN` (h) | `DAYLEN_FULL` (h) | Fenêtre d'activité |
|---|---|---|---|
| `ravageur` | 10.0 | 13.0 | printemps tardif → début automne |
| `auxiliaire` | 10.0 | 13.0 | suit le ravageur (sa proie) |
| `pollinisateur` | 12.0 | 14.5 | **étroite** : seulement les jours longs |
| `vers_de_terre` | 8.5 | 10.0 | **large** : sol tamponné, quasi toute l'année |

> **Lecture écologique.** Le pollinisateur a la fenêtre la plus tardive/étroite
> (il lui faut des jours longs ET des fleurs). Le ver de terre est presque
> insensible à la photopériode (il vit dans le sol, tamponné — il ralentira
> surtout par le futur champ `temperature_sol`, sprint physico-chimie) : ses
> seuils bas le rendent quasi toujours « ouvert », sa saisonnalité résiduelle
> passant par `warmth`. Ravageur et auxiliaire partagent la fenêtre estivale,
> l'auxiliaire suivant le ravageur via le couplage trophique existant.

**Paramétrage data-driven** : deux nouveaux champs sur `TrophicSpec`
(`daylen_min`, `daylen_full`) avec défauts de module, surchargés par guilde dans
`build_population_specs()` — exactement le patron déjà utilisé pour
`resource_w`, `pred_w`, `inertia`, etc.

---

## 4. Inertie asymétrique (décrue rapide / montée lente)

Pour resserrer la dormance automnale sans casser les cycles boom-bust estivaux,
l'inertie devient **asymétrique** selon le sens du mouvement vers la cible :

```
inertie_eff = INERTIA_DECAY  si  cible < pop     (la pop DÉCLINE → relaxation rapide)
            = INERTIA         sinon              (la pop CROÎT  → rythme actuel inchangé)
champ' = clamp(champ·inertie_eff + cible·(1−inertie_eff), 0, POP_MAX)
```

- `INERTIA = 0.85` (montée — **inchangé**, préserve le rythme de colonisation
  observé au calibrage D31).
- `INERTIA_DECAY ≈ 0.55` (décrue — `0.55⁴ ≈ 0.09` : extinction en ~4 semaines).
- Paramétrable par spec (`inertia_decay`), défaut module.

> **Lecture écologique.** « Meurt vite quand les conditions se dégradent,
> recolonise lentement quand elles s'améliorent » — asymétrie classique des
> populations (un gel tue en une nuit, un repeuplement prend des générations).

**Effet de bord à surveiller au calibrage** : la décrue rapide accentue aussi
les *bust* estivaux (effondrement de proie quand un prédateur la rabote) → cycles
plus « pointus » (chute brutale, remontée lente). C'est plausible
écologiquement ; à confirmer que les sprites n'en *clignotent* pas. Knob de
recours : remonter `INERTIA_DECAY` vers 0.70.

---

## 5. Intégration au tick

`phenology` dépend de `wiy`, que `PopulationField.tick` ne reçoit pas encore. Le
threading est minimal et **strictement le long de la chaîne d'appel existante** :

1. `boucle.py:235` appelle `eco.tick_populations(tile, tile.plants)` **dans** un
   contexte où `week_in_year` est déjà calculé (`wiy = ((week-1) % 52) + 1`,
   ligne ~119) → passer `week_in_year` :
   `eco.tick_populations(tile, tile.plants, week_in_year)`.
2. `container.tick_populations(self, tile, plants, week_in_year)` le transmet à
   chaque `popfield.tick(self, tile, plants, predator_fields, week_in_year)`.
3. `PopulationField.tick` calcule `daylength(week_in_year)` **une fois** (hors
   double boucle r×c — c'est un scalaire global à la tuile), en déduit
   `phenology` via ses seuils, puis l'applique dans `survie`.

> **Coût perf nul** : `daylength`/`phenology` sont deux scalaires par tick et par
> guilde, calculés hors de la boucle sur les plots. Aucun impact sur le profil
> (`perf_profile_simulation` : la couche biotique pèse ~13 % et n'est pas le goulot).

Rétro-compat : `week_in_year` peut prendre un **défaut** (ex. `25`, plein été →
phenology≈1) pour que d'anciens appels de test sans saison restent neutres, mais
la voie golden (l'engine) passera toujours la vraie valeur.

---

## 6. Re-figeage golden + tests

**Re-figeage assumé et annoncé** (règle de design #3 — dérive localisée,
expliquée) :

- **Golden écolo** (`tests/test_golden.py`, smoke 2 tuiles × 4 ans) : il traverse
  les 4 saisons et l'herbivorie lit `ravageur` (câblage D31.2) → les densités
  hivernales chutent → **hash re-figé**. Dérive localisée à la pression
  d'herbivorie saisonnière.
- **Golden de champ** (`tests/test_population.py`, `population_hash.txt`) :
  re-figé (c'est l'objet même du sprint).

**Assertions de non-régression à ajouter** (`test_population.py`) — elles
*prouvent* le comportement voulu, indépendamment du hash :

1. `pop_hiver(cœur, wiy≈4) << pop_été(pic, wiy≈30)` pour les 4 guildes.
2. **Dormance automnale resserrée** : à `wiy≈46` (mi-hiver), la pop ravageur est
   < X % de son pic — vérifie que la décrue ne traîne plus 13 semaines.
3. **Réveil printanier** : la pop pollinisateur commence à remonter *avant* le
   pic thermique (montée pilotée par la photopériode).
4. **Robustesse au redoux** : injecter un `+8 °C` en plein hiver (wiy≈46) ne
   réveille **pas** la guilde (phenology=0 verrouille la porte malgré warmth>0).
   ← test signature de la valeur ajoutée du modèle.
5. **Vers de terre** quasi insensibles à la photopériode (fenêtre large) : leur
   creux hivernal vient de `warmth`, pas d'un effondrement photopériodique.

`main.py 30` (banc d'essai) doit rester propre.

---

## 7. Paramètres (récapitulatif — tous placeholders calibrage post-test)

| Constante | Valeur proposée | Rôle |
|---|---|---|
| `W_SOLSTICE_ETE` | 25 | semaine du jour le plus long |
| `DAYLEN_MIN_H` / `DAYLEN_MAX_H` | 8.0 / 16.0 | amplitude photopériode (h) |
| `INERTIA` | 0.85 (inchangé) | inertie de **montée** |
| `INERTIA_DECAY` | 0.55 | inertie de **décrue** |
| `daylen_min`/`daylen_full` par guilde | cf. table §3 | fenêtre phénologique |

Aucune de ces valeurs n'est gravée : le sprint les pose, le **calibrage jeu en
main** (analogue à D12.4) les ajuste sur l'observation des sprites au fil des
saisons.

---

## 8. Hors périmètre (ne PAS faire dans ce sprint)

- **`temperature_sol`** (sprint physico-chimie du sol) : le ver de terre devrait
  à terme lire le sol tamponné, pas l'air. Ici il reste sur `warmth(air)` + sa
  fenêtre large. Hook laissé, pas câblé.
- **Floraison réelle / phénologie florale** (arc pollinisation) : ici le
  pollinisateur garde sa ressource `_flower_grid` actuelle (proxy stade ≥ 2). La
  vraie floraison branchera plus tard sur la même horloge `daylength`.
- **Portage C# / vue Godot** : la vue échantillonne déjà le champ
  (`sample_sprites`) → la saisonnalité se voit *gratuitement* côté Godot une fois
  le moteur recalé, sans toucher au rendu.
- **Saisonnalité de la météo elle-même** (`weather.py`) : déjà saisonnière, hors
  sujet.

---

## 9. Découpe d'implémentation

Sprint **petit/moyen, un seul fichier moteur** (`fields/population.py`) + le
threading `wiy` (2 signatures) + tests. **Un seul tronçon** suffit (pas de
sur-découpage) :

1. `daylength` + `phenology` + champs `TrophicSpec` + seuils par guilde +
   inertie asymétrique → **golden re-figé** (écolo + champ) + assertions §6.
   Vérifier `main.py 30`, mettre à jour `journal.md`, commit.

Si le re-figeage golden écolo s'avère plus large que prévu (interaction
herbivorie ↔ saisons), scinder en `01` (champ + tests de champ, golden écolo
re-figé en bloc annoncé) — mais a priori inutile.
