## 2026-06-04 — Sprint conception Vie macroscopique : D31 (conception seule)

Conception de la **vie macroscopique observable** (auxiliaires, ravageurs,
pollinisateurs, vers de terre). Le moteur ne tenait jusqu'ici que des **flux
abstraits** (`herbivory_pressure` scalaire, terme `predator` reconstruit de
proxies, `ALEAS_RAVAGEURS` événementiels) — aucune entité à vitalité propre.
Modèle technique **hybride** déjà tranché le 2026-06-04 après profilage (D32).
Aboutit à `docs/conception/CONCEPTION_VIE_MACRO.md`.

**Découpage : passage unique** (conception, un seul fichier, contexte chargé).

**Décision structurante (golden) :** la dynamique vit **DANS le tick écologique**
(les champs nourrissent herbivorie/prédation/`pollinator_reach`/aération et
remplacent la reconstruction `predator`) → **re-figeage golden assumé**, unique,
journalisé (comme météo). Motif : la boucle d'apprentissage *vois → agis →
observe* ne se referme que si **le champ qui dessine est le champ qui agit** ;
un découplage « décoratif » créerait une dérive visuel↔santé. Contraste assumé
avec la Vigueur (qui, elle, ne re-figeait jamais).

**Pivot (réponse de Nico sur les champs) :** pas 4 dynamiques au cas par cas mais
**un `PopulationField` générique** (ressource trophique / prédateurs / habitat)
instancié **4 fois** — chaque guilde attirée par la ressource dont elle se nourrit
(ravageur ← feuillage ; auxiliaire ← ravageur + nectar ; pollinisateur ← fleurs ;
vers_de_terre ← microbiome/OM, part fongique incluse). Même esprit data-driven que
l'objet de maîtrise générique (D12.3). L'**inertie** crée le **décalage
proie-prédateur** → boom-bust visible (la pédagogie).

**Perception (§3) :** sprites échantillonnés, **1 sprite = 1 quantum** de densité,
position `_hash_noise(seed,r,c,slot)` **indépendante de la semaine** (pas de
téléportation), **activité** = vitesse d'anim (pur rendu), **cap + marge** (coût
borné — le seul point hors budget au profilage). **Golden-neutre** (lecture pure).

**Façades `vigueur_*` (§4) :** patron `CONCEPTION_VIGUEUR.md` §1 mais `qi_local`
**trophique** (= la ressource du champ) ; **populations, pas individus** (les
sprites ne portent pas de Vigueur).

**Gestes (§5) :** « favoriser un auxiliaire » (↑ plancher habitat), « écraser »
devient **réel** (retire **un quantum**, la pression revient), « fourche-bêche →
**vers morts visibles** » (feedback viscéral *avant* la dette microbiome — visuel
avant santé ; grelinette = pas de vers morts). Granularité **individu** (Nico).

**Découpe impl. proposée :** D31.1 champs+perception (golden intact) → D31.2
câblage écolo (**re-fige**) → D31.3 façades+gestes (golden intact).

**Décisions annexes :**
- Le **gain signé de « manger un individu »** (limace `−`, etc.) → **renvoyé en
  dette côté D19** (« option rigolote, pas prioritaire », Nico) ; D31 fournit le
  **prérequis** (entité ciblable / sprite cliquable). `DETTE.md` D19+D31 mis à jour.
- Recoupe **D27** (« champ auxiliaire dédié » = ce sprint), **D30** (vers =
  support possible de l'aération), **D32** (champ gratuit vs agents ∝ population).

### Hash golden (journal de re-figeage)
`ee79dd66…` → **inchangé** (conception seule). Le re-figeage interviendra à
**l'implémentation D31.2** (câblage écologique), pas avant.

---
