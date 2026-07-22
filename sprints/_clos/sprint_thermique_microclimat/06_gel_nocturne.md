# Tronçon ⑥ — Gel nocturne localisé

> Sprint thermique-microclimat. Conception : `docs/champs/climat/conception_thermique_microclimat.md`
> (§2.3, §3, ligne 188 du plan). Kickoff **autosuffisant** (relançable à froid).
> Pré-requis : ⑤ CLOS (croissance spatialisée par T ressentie ; knob
> `T_PLANTE_ALPHA=0.5` ; golden re-figé `b1173a78…`).

## Objectif

Aujourd'hui le gel est **global et uniforme** : dans `sim/engine/boucle.py`
(~ligne 99), `if temp_now < TEMP_FROST_DAMAGE` calcule UNE sévérité pour toute
la tuile à partir de `temp_now` (T_air), puis `_mediated_damage` frappe tous les
semis identiquement (seule la rondelle paillage de la tuile module). Ce tronçon
**localise le gel au plot** : un coin découvert sous ciel clair gèle plus fort
qu'un coin paillé ou sous nuages. Premier émergent : **le gel épargne les zones
abritées** (litière) — exactement ce qu'imitent paillage et voiles d'hivernage.

## Modèle (§2.3 — ⚠️ la logique s'INVERSE par rapport au diurne)

```
T_min_nuit[r,c] = T_air − RAYONNEMENT_NOCTURNE · (1 − couvert_norm[r,c]) · (1 − nébulosité)
```

- **La nuit, le soleil ne chauffe plus.** Ce ne sont PAS les zones ensoleillées
  qui gèlent : ce sont les zones **découvertes** qui rayonnent leur chaleur vers
  le ciel **clair**. On NE réutilise donc PAS `temperature_sol` (diurne) — on
  calcule une carte nocturne séparée à partir de T_air.
- `couvert_norm[r,c]` = couvert protecteur local = **litière** :
  `min(1, om_fresh_at(r,c) / LITIERE_REF)` — la MÊME normalisation que l'isolation
  diurne ③ (`ISOLATION_COUVERT`/`LITIERE_REF`). Plus c'est couvert, moins ça
  rayonne, moins ça gèle. (Le **manteau neigeux** s'ajoutera à `couvert_norm` en
  ⑦, quand Neige existera — laisser un commentaire « + neige ⑦ », ne rien câbler.)
- `(1 − nébulosité)` : ciel couvert → peu de gel (les nuages renvoient la chaleur
  IR). C'est pourquoi les gelées arrivent **par nuit claire et calme**. `nebul`
  est déjà calculé une fois/tick dans `boucle.py` (`NEBULOSITE.get(event.kind, 0.10)`).
- `RAYONNEMENT_NOCTURNE = 5.0` °C : refroidissement nocturne max (ciel clair, sol
  nu). Placeholder, calibrage post-test.

## Étapes

1. **`fields/ecofields/constants.py`** — le knob est déjà spécifié en conception
   §3 mais **vérifier qu'il existe** ; sinon l'ajouter dans le bloc « Microclimat
   de surface T_sol », après `T_PLANTE_ALPHA` :
   ```python
   # Gel nocturne (tronçon ⑥) : la nuit le soleil ne chauffe plus ; les zones
   # DÉCOUVERTES rayonnent vers le ciel clair et gèlent le plus. T_min_nuit
   # descend sous T_air d'autant que le sol est nu (1−couvert) et le ciel clair
   # (1−nébulosité). RAYONNEMENT_NOCTURNE = chute max (ciel clair, sol nu).
   RAYONNEMENT_NOCTURNE = 5.0
   ```

2. **`fields/ecofields/thermique.py`** — ajouter un **helper pur** `t_min_nuit_at`
   (à côté du calcul diurne déjà sorti du conteneur en ①), qui prend `(eco, r, c,
   t_air, nebul)` et renvoie `T_min_nuit[r,c]` selon la formule ci-dessus
   (`couvert_norm` réutilise `eco.om_fresh_at(r,c)` + `LITIERE_REF`, comme ③). Pur,
   pas d'effet de bord, pas de RNG (philo #3). Importer `RAYONNEMENT_NOCTURNE`,
   `LITIERE_REF` depuis `.constants`.

3. **`sim/engine/boucle.py`** — remplacer le bloc gel GLOBAL (~ligne 99-105) par
   un gel **localisé**. Au lieu d'une `frost_sev` unique passée à `_mediated_damage`
   pour toute la tuile, calculer la sévérité **par plante** depuis `T_min_nuit` à
   son plot :
   ```
   frost_sev[plant] = max(0, (TEMP_FROST_DAMAGE − T_min_nuit[r_plant,c_plant]) / FROST_SEVERITY_REF)
   ```
   → un coin paillé/sous-nuages peut rester > seuil (sév=0, épargné) pendant qu'un
   coin nu/clair gèle. Conserver le log `❄ gel …` mais il devient **par tuile avec
   une plage** (ex. `sév 0.00→0.42`) plutôt qu'un scalaire global.

4. **`sim/engine/mortalite.py`** — `_mediated_damage` prend aujourd'hui une
   `severity` SCALAIRE pour toute la tuile. Pour localiser, deux options (choisir
   la plus surgicale) :
   - **(a)** ajouter un paramètre optionnel `severity_fn=None` : si fourni,
     `effective` utilise `severity_fn(p)` (sévérité locale au plot de `p`) au lieu
     du scalaire. Les appels grêle/canicule existants restent inchangés (scalaire).
   - **(b)** une méthode jumelle dédiée au gel localisé.
   Préférer **(a)** (un seul chemin de dégât, moins de duplication). Le reste
   (susceptibilité `rusticite_froid`, protection paillage rondelle, `DAMAGE_STEP`,
   `deposer_mort`) **inchangé**.
   ⚠️ Le paillage existe à DEUX échelles maintenant : la **rondelle** `paillage`
   (protection de tuile, déjà dans `_mediated_damage`) ET la **litière** `om_fresh`
   (couvert local, dans `T_min_nuit`). Les deux agissent — c'est voulu (geste
   joueur explicite + état émergent du sol). Ne pas en retirer un.

5. **Golden** — `python3 -m tests.test_golden`. **Échec attendu** : le gel ne
   frappe plus uniformément → les semis sur plots paillés/abrités survivent là où
   ils mouraient → cascade santé/mortalité/succession. Vérifier la traçabilité
   (logs `❄ gel` avec plage de sévérité, et des semis épargnés sur litière) puis
   re-figer (`--capture`).

6. **Suites ciblées** : `test_croissance`, `test_eau`, `test_genetique`,
   `test_population` doivent rester PASS (le gel localisé ne touche ni l'eau ni la
   génétique ni la pop directement). S'il existe un test ciblant le gel/`_mediated_damage`,
   l'inspecter : s'il code en dur l'uniformité du gel, le re-calibrer (raconter la
   dérive à Nico, NE PAS neutraliser).

## Invariant golden

- **Dérive attendue** : gel spatialisé → mortalité des semis hétérogène (abrités
  survivent) → succession décalée (traçable au mécanisme T_min_nuit).
- **Doit rester** : déterminisme (litière + nébulosité déterministes), T_air
  (`temperature`) toujours uniforme, `tick_thermique` DIURNE inchangé (⑥ ajoute
  une carte NOCTURNE séparée, ne touche pas la cible diurne). La croissance
  (⑤) lit toujours la T ressentie — non touchée.

## Note (manteau neigeux + amplitude jour/nuit)

- La **Neige** n'existe pas encore (⑦) : `couvert_norm` n'intègre que la litière
  pour l'instant. Poser le commentaire « + manteau neigeux ⑦ » sans câbler.
- On ne modélise PAS un vrai cycle jour/nuit horaire : `T_min_nuit` est la
  **borne basse nocturne** de la semaine, calculée pour le gel uniquement. La
  croissance reste sur la T ressentie diurne (⑤). Pas de second pas de temps.

## Validation

- `python3 -m tests.test_golden` re-figé.
- `python3 main.py 3` tourne sans crash (exit 0, scores finaux affichés).
- Vérif mécanisme (print jetable, réutiliser `tests.test_golden.build_world` +
  `Engine`, stepper jusqu'à une semaine froide ou forcer `t_air` bas) : pour un
  même `t_air < TEMP_FROST_DAMAGE`, `T_min_nuit` d'un plot paillé (litière haute)
  est > `T_min_nuit` d'un plot nu, et > sous ciel couvert (nébulosité haute) que
  sous ciel clair.

## À faire en fin de tronçon

- Mettre à jour `00_etat.md` (statut ⑥ ✅ + nouveau hash dans §REPRISE + noter si
  un test gel a été re-calibré).
- Commit : `feat(thermique) : tronçon ⑥ gel nocturne localisé (couvert + nébulosité protègent) — golden RE-FIGÉ MAÎTRISÉ`.
- Écrire le kickoff `07_catalogue_neige_orage.md` avant le `/clear` (Neige + Orage
  au catalogue météo + `couvert_norm` qui intègre enfin le manteau neigeux).
