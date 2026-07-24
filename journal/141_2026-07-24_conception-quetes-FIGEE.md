# 2026-07-24 — Conception SYSTÈME DE QUÊTES (D79) — FIGÉE

**Type :** conception (`/conception`) · **Thème :** `joueur/automate` ·
**Statut :** FIGÉE, prête pour `/sprint-auto`. Dépend de D78 (fait) ; couple D87 (clos).

## Intention
Donner une **direction** au joueur (bac à sable sans direction) sans casser #6.
Une quête = un **désir** posé par une lettre + une **lecture passive** de l'état
du monde. Elle **ne pilote rien, elle regarde** ; le *comment* reste au joueur (#1).

## 3 recadrages du code (source de vérité, vérifiés au grep)
- **F1** — le cœur objectif D78 vit dans `tools/jardinier_auto/` (harnais
  AUTOMATE) ; `sim/actions/gestes.py` (gestes JOUEUR) l'ignore. → **D79 = module
  MOTEUR joueur neuf `sim/quetes.py`**, pas un enveloppement de D78 ; partage la
  forme `(geste, quantite, cible)`, pas le code.
- **F2** — `sim/evenements.py` est un **parseur de log texte**, pas un bus. →
  quêtes cumulées comptées par **hook geste** ; quêtes d'état lues sur
  **snapshot** hors tick. Le ledger n'est PAS le substrat (moins de couplage).
- **F3** — **kiwi absent** (grimpante différée D26) ; trèfle existe. → aucune
  espèce créée dans D79 ; cible « kiwi » = `inatteignable` (géré) ; démo sur
  trèfle (floraison) + pommier/tournesol (hauteur).

## Décisions de vision (Nico)
- **V1** donneurs = **lettres ANONYMES** (prénom, sans figure/dialogue/récurrence)
  → garde-fou CLAUDE.md « pas de PNJ » **ajusté** pour autoriser les voix
  épistolaires.
- **V2** progression **diégétique** approx. (« un cageot », « à hauteur d'homme ») ;
  chiffre exact = debug seulement (#5).
- **V3** récompenses (catalogue ouvert) : plaisir pur / graine / page / Vigueur /
  maîtrise ; RARE : outil / structure / **vivace déjà enracinée** (instanciation
  d'une pérenne à âge avancé — cadeau matériel, **PAS un buff**, #2 respecté).

## Décisions techniques
- Condition = **mini-catalogue déclaratif fermé** (`recolte_cumulee`,
  `hauteur_min`, `floraison_min`, `nombre_vivant_min`), fonctions pures.
- Couplage D87 **one-way partiel assumé** (seul `recolte_cumulee` convertible en
  `Objectif` automate ; conditions d'état non requises côté automate).
- Quête **ouverte à vie**, pas d'expiration ni d'échec (#4).
- Garde-fou #6 formel : optionnelle + ignorable + jamais bloquante +
  désir-sans-méthode + **plafond de N quêtes actives** (anti-checklist).
- Déclenchement **déterministe** (palier maîtrise + jalon saison, zéro RNG, #3).
- Perf négligeable (K conditions hors tick), **golden INTACT** partout.

## Découpage (5 tronçons, golden inchangé)
① `sim/quetes.py` + `recolte_cumulee` (hook geste + consignation ledger) ·
② conditions d'état (snapshot) + progression diégétique ·
③ déclenchement déterministe + table `quetes_corpus.py` + voix lettres + plafond
+ récompenses simples · ④ récompenses matérielles rares (vivace enracinée,
structure ; outil différé en dette si pas d'inventaire) · ⑤ vue Godot panneau
« courrier » + pont `cmd_courrier` + banc F5.

Doc `docs/joueur/automate/conception_quetes.md` +
`sprints/joueur/automate/sprint_quetes/` (00_etat + 01→05). DETTE **D79 → 🟢**.
Prêt pour `/sprint-auto sprint_quetes`.
