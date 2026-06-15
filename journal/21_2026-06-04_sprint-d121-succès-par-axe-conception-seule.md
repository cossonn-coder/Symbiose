## 2026-06-04 — Sprint D12.1 : succès par axe (conception seule)

Premier sous-sprint de D12. Précédé de la **lecture moteur** actée comme point de
vigilance : inventaire des signaux discrets que le tick émet déjà (stade,
`advance_stage`, santé, mort par cause, reproduction + tag `biparental`, météo +
`_mediated_damage` vide=zéro perte, stagnation `⏸/🌑/❄`, succession férale, champs
`eco.summary()`, actions joueur). Constat : tous les signaux existent pour les
**êtres vivants** et **concepts** ; **outils/structures/techniques absents du
moteur** → fixés comme **patron** (câblage → D12.3). Aboutit à
`CONCEPTION_MAITRISE.md` **§9**.

**Pivot acté (Nico).** Un succès = **une action joueur dont l'effet émergent
améliore le résultat au-delà du cours spontané, observée**. Ni un événement
émergent (*tomate qui pousse seule = bonnes conditions, pas maîtrise*), ni une
action simplement payée. Opérationnalisé sans contrefactuel : *stress présent
levé* ou *stress prévenu chez les protégés*. La couche maîtrise **lit** ces
signaux, n'écrit rien dans le tick → golden intact.

**Nature de preuve croissante par palier (Nico, Q2).** Espèce : observer → lever
une stagnation → reproduction → optimisation répétée saine → **palier 5**.

**Palier 5 = conjonction (Nico).** Transcendance très dure : **(a)** action
experte/extraordinaire réussie (le ~20 % météo imprévisible, un sauvetage) **ET**
**(b)** naturalisation — génération **férale** non replantée qui boucle son cycle
en pleine santé dans le sol façonné, « accueillie comme native ». Réconcilie les
deux principes CLAUDE.md : l'action est la **preuve**, l'auto-suffisance l'**état**.

**État gameplay minimal induit** (au-dessus du tick, par avatar) : tag de
provenance *féral*/*replanté* (pour 5b) + fenêtre d'imputation geste→amélioration ;
gate d'observation (succès registré quand observé). Aucun état tick nouveau.

**Reste ouvert (différé) :** les **Nᵢ** (répétitions/palier, courbe log §2.3) →
calibrage D12.4 ; le **câblage par objet** (objets touchés par action) → D12.3.

### Hash golden (journal de re-figeage)
`ee79dd66…` → **inchangé** (conception seule, aucun code moteur).

---
