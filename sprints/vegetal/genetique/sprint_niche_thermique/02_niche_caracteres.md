# ② Niche d'espèce, caractères thermiques, plasticité, coût

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_niche_thermique.md` §4 et §7 (tableau des espèces).
> Golden attendu : **RE-FIGÉ annoncé** — clés de gènes neuves dans le digest
> (`tests/test_golden.py`, `GENES[...]`) et `rusticite_froid` passe en °C (le gel des semis
> le lit). Pas encore de nouveaux dégâts.

## Objectif
Chaque espèce porte sa plage, chaque plante la décale par ses gènes et par ce qu'elle a vécu.

## À faire
1. **Attributs d'espèce** sur `PlantBase` (`plants/base/familles.py`) : `t_froid_lesion`
   (None par défaut), `t_gel_tendre` (−6), `endurcissement_max` (10), `t_chaud_stress` (32),
   `t_brulure` (45), avec commentaire pédagogique. Surcharger les **52 espèces** selon le
   tableau §7 (fichiers `plants/species/*.py`, `plants/perennials/*.py`). Vérifier la liste
   au code (une espèce absente du tableau garde les défauts, à signaler).
2. **Caractères** (registre du sprint ①) : `rusticite_froid` passe en °C (neutre 0, σ_A 1.5,
   abaisse `t_gel_tendre`) ; `limite_froid` (°C, 0, 1.0) et `limite_chaud` (°C, 0, 1.5)
   ajoutés **en queue**.
3. **Plasticité en °C** (§4.3) : l'expression liée à `cold_memory` reste, mais pour un
   caractère en °C le phénotype est **génotype + plasticité** (`endurci = endurcissement_max
   × (expression−1)/(EXPR_MAX−1)`). Adapter `expressed_gene` ou ajouter un accès dédié, sans
   casser les caractères `facteur`. Nouvelle mémoire `heat_memory` (signal : T_feuille au-dessus
   de `t_chaud_stress − 5`, même dynamique que `cold_memory` dans
   `sim/engine/croissance.py` ≈ l. 286-344) appariée à `limite_chaud` dans
   `ADAPTOGENIC_GENES` ; acclimatation ≤ +3 °C. Le priming maternel s'applique comme aux
   autres.
4. **Limites effectives** (§4.4) : quatre méthodes sur `PlantInstance` (`lim_gel`,
   `lim_froid`, `lim_chaud`, `lim_brul`), source **unique** que liront le ③ (dégâts) et le ④
   (signes).
5. **Gel des semis existant** (`boucle.py` ≈ l. 146-162, `_mediated_damage` avec
   `gene_name="rusticite_froid"`) : la susceptibilité `1/expressed_gene` n'a plus de sens en
   °C. Le gel compare désormais la nuit à `lim_gel` (sévérité ∝ écart). **Garder le filtre
   `semis`** à ce tronçon (il tombe au ③).
6. **Coût** (§4.5) : `K_THERMO = 0.02` par °C de tolérance génétique au-delà du neutre, sur le
   chemin de `cout_defense` (lecteurs `sim/engine/croissance.py:163`,
   `sim/engine/mortalite.py:137`).
7. **Voix** : niveau 2 de l'encyclopédie (`sim/encyclopedie_corpus/`) des espèces
   sensibles (basilic, tomate, poivron, courgette, haricot) et rustiques (mâche, seigle) : la
   frilosité ou la rusticité en **mots**, pas en °C.
8. **Re-figeage** : diff du digest lu, `--capture`, hashes consignés.

## Tests
- Test ciblé : `lim_gel` d'un basilic neutre = −1 °C ; un basilic endurci ne gagne rien
  (`endurcissement_max` 0) ; un seigle endurci descend vers −25 °C ; `limite_chaud` relève
  `lim_brul` ; `heat_memory` monte sous T_feuille chaude ; héritage des trois caractères.
- `test_plasticite`, `test_greffe` (la greffe classe `rusticite_froid` comme aérien) verts.

## Ne PAS faire
- Nouveaux dégâts de froid sans gel, de chaleur, ou gel sur les adultes (c'est le ③).
- Toucher à `_winter_transition` (③).
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`00_etat.md` : ② FAIT, hashes. Commit.
