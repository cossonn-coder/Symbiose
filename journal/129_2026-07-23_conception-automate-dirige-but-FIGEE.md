# 2026-07-23 — Conception AUTOMATE DIRIGÉ PAR LE BUT (D87) — FIGÉE

`/conception` (sur repo, code lu — l'amorce `brief_amorce_automate_but_D87.md`
avait été écrite SANS accès au dépôt et est ici **recadrée** par la lecture du
code réel de l'automate).

## Ce que D87 ajoute

Un **étage de planification moyens-fins** DÉTERMINISTE (chaînage arrière borné,
pas d'IA/RNG — philo #3) **au-dessus** du jardinier automate réactif (D78) : à
partir d'un objectif `recolter <espèce> ×N`, l'automate comprend la **chaîne
d'étapes** et la **planifie à rebours** pour faire ADVENIR la cible même si elle
n'est pas plantée — et s'arrête sur une **impasse honnête** si un chaînon manque
sans source. Vit hors tick (invariant H2) → **golden intact par construction**.

## Recadrage majeur (apport de la lecture du code vs amorce aveugle)

Le cœur réactif Liebig **couvre déjà tout le « MAINTENIR »** (arroser, pailler,
désherber, grelinette, tailler, récolter) pour les cultivées. Le planificateur ne
comble que le **« FAIRE ADVENIR »** = **3 gestes créatifs** que la boucle réactive
ne joue jamais : `planter`, `acheter_au_magazine`, `favoriser_auxiliaire`. La
chaîne de l'exemple tomate est **quasi-linéaire, profondeur ≤ 3**
(`recolter ← cultivée présente ← planter ← graine ← magazine`). → **archi B**
(régresser le modèle biologique) **REJETÉE** = sur-ingénierie (rien à régresser,
Liebig sert déjà la biologie) ; retenu **archi A/C** = petit catalogue
d'opérateurs dont les pré/post sont **sondées sur l'état vivant** (patron
`objectifs.est_atteignable`/`proposition.proposer` étendu). Aucun geste neuf,
aucun seuil bio recopié.

## Décisions figées

- **Préemption survie** (Q3) : gestes créatifs (advenir) en priorité MODÉRÉE SOUS
  les facteurs de survie du vivant existant. Advenir ralenti, jamais au prix du
  vivant. En coût-0 l'ordre reste requis pour ORDONNER déterministement.
- **Veille + re-sonde** (Q7) : objectif en veille reste ACTIF, impasse tracée 1×,
  re-plan **sur déclencheur** seulement (palier 3 ouvre le magazine / plot libéré /
  fenêtre favorable), jamais par tick. État persistant `automate_plans`.
- **« Récoltable » typé organe** (C2/Q10) : signal = `plant_class.fruitier` (lu,
  pas dupliqué). `fruitier=True` → but = fruit mûr (`plant.fruits`) + sous-chaîne
  pollinisation (`favoriser_auxiliaire`) ; `fruitier=False` → maturité végétative,
  pas de pollinisation. C'est la différence de longueur de chaîne que le banc
  multi-espèces exhibe.
- **Suffisance N** (C1/Q9) : culture permanente `nb_plants_cible=min(N,3)`
  (réglable), rendement non forcé (comptage réel `incrementer`).
- **Re-semis armé sur changement de condition** (C3/Q11) : re-semer la même espèce
  au même plot dans les mêmes conditions redonne la même mort (déterminisme) → le
  re-semis n'est armé que si `(saison, plot)` diffère ; sinon impasse
  `niche_defavorable` directe. Garde-fou `tentatives ≤ 2`.
- **Timing `favoriser_auxiliaire`** (C4) : habitat auxiliaire posé AU PLUS TÔT
  (dès qu'une cultivée `fruitier` sans rondelle existe), one-shot, avant floraison.
- **Log exhaustif structuré** (Q13) : **enrichissement du canal `automate_journal`
  existant** (`trace.py`), PAS un canal neuf. Technique/debug, JAMAIS diégétique —
  frontière stricte avec le carnet D14 (`sim/journal.py`, voix « je », gate
  `ecrit_carnet`). Champs structurés (`categorie`/`semaine`/`niveau`/`objectif_id`/
  `espece`/`zone`/`detail`), log TOUJOURS complet, filtre + verbosité = vues LECTURE
  SEULE (`filtre.py`), ordre total stable. Sert d'**oracle de déterminisme**.
- **Coût Vigueur réglable à 0** (exigence B) : **déjà présent** via
  `paie_vigueur=False` (preset LIBRE) → `assurer_solde_libre`. RÉUTILISÉ (pas de
  flag neuf `cout_vigueur_actif`).
- **Banc « X depuis rien » paramétré** (exigence A) : `banc_culture_depuis_rien(
  espece, quantite, source_graine ∈ {auto,banque,magazine,aucune}, cout_vigueur)`
  = matrice de test multi-espèces + révélateur de bugs bio (Q8).

## Découpage — 5 tronçons (golden `57c166d8…` INTACT partout, opt-in hors tick)

① log structuré (fondation — schéma précède ses écrivains) · ② opérateurs +
moteur de régression · ③ articulation boucle Liebig + préemption survie · ④ veille
+ re-sonde + impasses honnêtes · ⑤ banc paramétré + vue Godot (log filtrable,
DERNIER = vue, règle permanente). Aucun geste neuf, aucun re-figeage.

Suppose D84 (floraison) / D86 (survie tomate, `tomate-mort-precoce`) corrects mais
ne les MASQUE pas : un planificateur parfait échoue si la biologie ne suit pas, et
l'impasse honnête le RÉVÈLE (Q8).

Doc : `docs/joueur/automate/conception_automate_but.md`. Sprint :
`sprints/joueur/automate/sprint_automate_but/` (00_etat + 01→05). DETTE D87 → 🟢.
Prêt pour `/sprint-auto sprint_automate_but`.
