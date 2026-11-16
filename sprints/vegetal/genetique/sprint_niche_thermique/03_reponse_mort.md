# ③ La plante répond et meurt d'elle-même

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_niche_thermique.md` §2 (T1) et §5 (en entier).
> Golden attendu : **RE-FIGÉ annoncé, dérive large** — gel sur tous les stades, froid sans
> gel, chaleur, et les annuelles ne meurent plus au calendrier.

## Objectif
Brancher les limites du ② sur la vie de la plante, et retirer la mort par le calendrier.

## À faire
1. **Gel, tous stades** : retirer le filtre `p.stage.name != "semis"` du chemin gel
   (`sim/engine/mortalite.py`, `_mediated_damage` ≈ l. 424, appelé par `boucle.py` ≈ l. 146).
   **Attention** : la grêle passe aussi par `_mediated_damage`. Le filtre `semis` de la grêle
   reste tel quel (décision hors périmètre) : séparer proprement, par exemple un paramètre
   de stades. Le docstring dit pourquoi le stade perpétuel des ligneux était exclu : la
   limite `lim_gel` endurcie des ligneux (≈ −30 °C) remplace cette exclusion. La sévérité
   reste médiée par le couvert local (paillage, voile).
2. **Froid sans gel** : pour les espèces à `t_froid_lesion` défini, si la nuit la plus froide
   < `lim_froid`, érosion **cumulative** ∝ écart (`erode`, cause `froid`, marque de
   symptôme). Calibrer : un basilic neutre exposé à des nuits à 6-8 °C décline en 3-5
   semaines et meurt (cible ; mesurer au banc headless).
3. **Chaleur** : T_feuille > `lim_chaud` → pas de croissance cette semaine (même endroit que
   `ok_temp`, `sim/engine/croissance.py` ≈ l. 157) et **nouaison bloquée** cette semaine
   (trouver le point d'accroche dans `_tick_fruits`, `sim/engine/decompo.py:264`, ou dans la
   voie de pollinisation ; une seule condition, lue sur `lim_chaud`). T_feuille > `lim_brul` →
   `erode` ∝ excès, cause `brulure`. Mettre à jour `heat_memory`.
4. **Fin de la mort calendaire** (`_winter_transition`, `sim/engine/mortalite.py:319` ;
   déclencheur `boucle.py` ≈ l. 698-701) : la branche `die` ne tue plus. La dormance et le
   ralentissement des persistantes se déclenchent à l'entrée en hiver réelle
   (`SEMAINE_HIVER`, `calendrier.py`) ou à un seuil de `cold_memory`, plus à la semaine 49.
   Corriger le docstring (« semaines 48-52 »). Garder le code de la branche (ne rien jeter)
   s'il sert encore, sinon le commenter comme historique.
5. **Sénescence de fin de cycle** (annuelles, puis bisannuelles si possible) : déclin interne
   à partir de `bloom_week + bloom_duration + maturation` (`PlantInstance.bloom_week`,
   `fruit_semaines_maturation` de l'espèce ou un défaut de 6 semaines), décrément direct
   comme la sénescence d'âge (`_tick_senescence_health`, `mortalite.py` ≈ l. 51). Lire
   comment `bloom_week` se réinitialise d'une année à l'autre avant d'écrire la condition.
   Bisannuelles : si leur floraison de l'an 2 passe par `bloom_week`, même mécanisme et
   retrait de la règle `age_years >= 2` ; sinon garder la règle et le consigner.
6. **Graines** : la mort calendaire déposait `seed_bank.add(...)`. **Mesurer** si les
   annuelles fructifient et réensemencent sans ce dépôt (banc headless, 3 ans, basilic,
   phacélie, moutarde) ; sinon, déposer à la mort par fin de cycle.
7. **Banc headless** (`mesures/`) : date de mort du basilic sur sol nu vs paillé vs voilé ;
   la mâche et le seigle passent l'hiver ; une plante assoiffée en plein soleil en canicule
   brûle, la même arrosée ou ombragée tient (forcer une canicule au banc). Consigner.
8. **Perf** : smoke avant/après, budget ≤ +2 %. **Re-figeage** : diff lu, `--capture`,
   hashes et explication de la dérive.

## Tests
- Test ciblé : un basilic adulte gèle ; une mâche non ; un basilic à 6 °C décline ; une plante
  au-dessus de `lim_chaud` ne pousse pas ; une annuelle ne meurt plus en semaine 49 ; elle
  sénesce après sa floraison ; la grêle épargne toujours les adultes.
- `tests/test_evergreen.py` et les tests de mortalité/hiver : adapter seulement ce qui
  figeait la mort calendaire, en le disant.

## Ne PAS faire
- Perte de rameaux des ligneux (D131). Fréquence des canicules (D107).
- Un « filet » de vieillesse arbitraire (décision T1 de Nico).
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`00_etat.md` : ③ FAIT, mesures, hashes. Commit.
