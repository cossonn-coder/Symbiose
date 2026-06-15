## 2026-06-04 — Sprint D12.3 : taxonomie des objets de maîtrise (conception seule)

Troisième sous-sprint de D12 (D12.2 reste bloqué, attend D13/D14/D15). Précédé de
la **lecture des catalogues moteur** (point de vigilance acté) : `plants/`
(17 espèces / 11 familles), `sim/actions.py` (4 gestes codés) + le catalogue
d'actions *conçu* de `CONCEPTION_VIGUEUR.md` §3.2/§3.3. La taxonomie **reflète**
ces catalogues, n'en invente aucun. Aboutit à `CONCEPTION_MAITRISE.md` **§10**.

**Découpage : passage unique** (pas de `00_etat.md`+`0N`). Motif acté : conception
= un seul fichier (pas de fichiers de code couplés), contexte déjà chargé,
livrables couplés (table ↔ taxonomie), sur-découpage déconseillé (CLAUDE.md).

**Taxonomie (§10.1–10.3).** Êtres vivants = les 17 espèces réparties sur 11
familles ; le **spillover §3.1 est data-driven sur la famille réelle** → actif
aujourd'hui pour Solanaceae, Fabaceae, Asteraceae, **Rosaceae** (≥2 espèces), pas
pour les 7 singletons. Les 5 familles « cœur » de `base.py` **ne sont pas
privilégiées** (Rosaceae spille comme Solanaceae) — honore le pivot §0. Concepts =
les 6 de §9.3 → **terme global** de `cout_action`. Outils/structures/techniques =
inventaire dérivé des actions, **déclarés non câblés** (D29/D30/D31).

**Livrable central (§10.4) : table objets-touchés par action.** Précise le modèle
§4.2 — terme 1 = global (concepts + vivants), terme 2 = `{technique, espèce cible
(→famille), outil, structure}` que CE geste manipule.

**Décision :** maîtrise.md §10.4, le succès figé en D12.1 reçoit son support data.
- **Outil ≠ technique** comme deux objets distincts (sécateur vs taille). Honore
  les catégories §1 et **raffine** l'exemple §4.2 (dont l'espèce « framboisier »
  était illustrative, hors catalogue).
- **Concepts hors terme 2** : ils ne nourrissent que le terme global (connaissance
  holistique) — fidèle au texte littéral de §4.2.
- **Milieu sans cible vivante** (philo #2) ; **vivant** ajoute l'espèce →
  spillover famille gratuit. `observer`/`méditer`/`manger` (coût NUL) → terme 2 vide.

**Reste ouvert (différé) :** câblage des objets *en cursive* (outil/structure/
technique + nuisible) → D29/D30/D31 + sprints d'action ; Nᵢ + atténuations → D12.4.

### Hash golden (journal de re-figeage)
`ee79dd66…` → **inchangé** (conception seule, aucun code moteur).

---
