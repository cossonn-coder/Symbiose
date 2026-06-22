# Tronçon ① — Substrat de plasticité (gène asphyxie + 2 mémoires + expression)

> Sprint « plasticité ». Conception : `docs/conception/CONCEPTION_PLASTICITE_EXPRESSION.md`
> (§2.1-2.3, §2.6, §6). **Lire la conception d'abord.** C'est le tronçon le plus
> chargé, mais **golden NEUTRE attendu** : rien ne LIT encore `expressed_gene`.

## Objectif
Poser toute la tuyauterie de l'expression plastique sans que personne ne la
consomme. À la fin : chaque plante a un état `expression[g]` qui dérive du stress
vécu, mais le calcul de croissance/dégât est inchangé → hash golden identique.

## Périmètre
1. **Nouveau gène `tolerance_asphyxie`** — ajouté **en FIN** de `GENE_NAMES`
   (`plants/genetics.py:30`) pour préserver les canaux de hash des gènes existants
   (`child_genes` indexe par position, `reproduction.py:108`). Docstring du gène
   (modèle : tolérance à l'hypoxie racinaire, neutre 1.0).
2. **Deux mémoires d'exposition** sur `PlantInstance` (`plants/base/instance.py:35-38`,
   à côté de `shade_memory`/`drought_memory`/`asphyxie_memory`) :
   - `cold_memory: float = 0.0` — intègre la sévérité de froid sub-létale. Signal :
     `frost_sev` par plot (`sim/engine/boucle.py:108-111`, `t_min_nuit_at` vs
     `TEMP_FROST_DAMAGE`). Intégrer même hors gel létal (exposition douce).
   - `infection_memory: float = 0.0` — intègre la pression pathogène vécue. Signal :
     `disease_probability` / pression de `fungal_disease` (`perturbations.py:116`).
3. **Intégration des mémoires** dans `_update_physiology` (`sim/engine/croissance.py:175`)
   — lerp lent, MÊME patron que les mémoires existantes (montée sous exposition,
   décroissance sinon, cf. `mortalite.py:239` pour `shade_memory`).
4. **État d'expression** `expression: dict[str, float]` sur `PlantInstance`
   (patron `symptom_marks`, instance.py:119). Défaut 1.0 pour chaque gène de
   `ADAPTOGENIC_GENES`. Init dans le constructeur / factory de plante.
5. **`ADAPTOGENIC_GENES`** (constante) + **`expressed_gene(self, name)`** sur
   `PlantInstance` : `clamp_gene(self.gene(name) * self.expression.get(name, 1.0))`.
   Emplacement de `ADAPTOGENIC_GENES` : `plants/genetics.py` (à côté de `GENE_NAMES`).
6. **Dynamique d'expression** dans `_update_physiology` : pour chaque gène
   adaptogène, `cible = 1.0 + EXPR_GAIN * memoire(g)` ; lerp à **hystérèse**
   (`TAU_UP` si cible > expression, `TAU_DOWN` sinon). Bornes `EXPR_MIN`/`EXPR_MAX`.
   Appariement : sécheresse↔`drought_memory`, ombre↔`shade_memory`,
   froid↔`cold_memory`, pathogène↔`infection_memory`, asphyxie↔`asphyxie_memory`.

## Knobs (constantes, calibrage ultérieur P6 — valeurs de départ raisonnables)
`EXPR_GAIN ≈ 0.3`, `EXPR_MIN = 1.0`, `EXPR_MAX ≈ 1.3`, `TAU_UP ≈ 0.08`,
`TAU_DOWN ≈ 0.04`. Centraliser dans un endroit lisible (genetics.py ou un bloc
dédié), commentés.

## Vérifs (golden NEUTRE)
- `python3 -m tests.test_golden` depuis `data/code/` → **hash inchangé**
  `3f86bf53…`. Si dérive : STOP — un consommateur lit déjà `expressed_gene`, ou
  l'ajout du gène/mémoire a touché un calcul (vérifier que `tolerance_asphyxie`
  défaut 1.0 n'est lu nulle part, que `cold_memory`/`infection_memory` ne
  rebouclent sur rien).
- Test d'unité ciblé (nouveau, ex. `tests/test_plasticite.py`) : sous stress
  forcé (mémoire → 1.0), `expression[g]` monte vers `1+EXPR_GAIN` à vitesse
  `TAU_UP` ; stress levé → redescend à `TAU_DOWN` (plus lent, hystérèse) ;
  `expressed_gene` borné à `EXPR_MAX`/`clamp_gene`.
- Garde-fou taille (`tools/compte_ldc.py` si présent) : modules touchés < ~350
  lignes de code pur.

## Sortie
MAJ `00_etat.md` (statut ① clos, hash golden confirmé, journal détaillé). Commit.
`/clear` avant `02_branchement.md`.
