# ③ Vue Godot & validation F5 — l'usure se VOIT, l'hôte survit

> Kickoff AUTOSUFFISANT. Lis `CLAUDE.md` + `00_etat.md` + ce fichier. Prérequis :
> ① et ② faits. Tronçon vue (règle projet : tout sprint finit par sa vue Godot).
> Le **F5 visuel reste à Nico** (Godot n'est pas sur la VM) ; le sous-agent
> prépare, vérifie la chaîne de données, et écrit le protocole d'observation.

## Objectif
Rendre l'**usure lisible** et **valider** que le correctif tient à l'écran : sur
le banc `grimpantes`, le tournesol-hôte **survit** (plus de mort-éclair w12) et le
dominé **dépérit progressivement** par l'ombre (« usure, pas punition » visible).

## Contexte — le rendu de l'ombre est DÉJÀ en place
`visuals/PlantRenderer.Organs.cs:214-222` mappe déjà le signe `ombre`
(`_litFactor = Lerp(...)` → feuillage dépérissant). Et `tools/simserver/
serialize.py:120` envoie `leaf_symptoms` (dont `ombre`, `senescence`). La chaîne
existe : ce tronçon la **vérifie de bout en bout** et n'ajoute du C# **que si**
l'usure n'est pas assez lisible.

## Ce qu'il faut faire
1. **Vérifier la chaîne données** (Python, sans Godot) : sur `bancs.grimpantes()`,
   `Engine(week=9)`, avancer ~40 semaines et sérialiser le snapshot (via le
   serializer existant) → confirmer que le **haricot** (dominé) porte bien un
   `leaf_symptoms` avec `cause="ombre"` d'intensité croissante, et que le
   **tournesol** reste `dead=false`. C'est la preuve testable côté VM.
2. **Vérifier le mapping C#** (lecture) : que `PlantRenderer.Organs.cs` consomme
   bien la cause `ombre` (et `senescence`) depuis `leaf_symptoms`. Si une cause de
   dépérissement lent (`senescence`, `secheresse`) n'est pas mappée alors que
   `ombre` l'est, harmoniser **a minima** (petit ajout de teinte/flétrissement),
   sans refonte. **Aucun** changement si tout est déjà mappé.
3. **Protocole F5 pour Nico** (écrire dans `00_etat.md` §F5) : monter le banc
   (`init config="grimpantes"`), laisser tourner ~1 an, observer que
   l'hôte tournesol (2,2) **reste vivant** et que le haricot voisin **jaunit/
   flétrit lentement** sous son ombre (aucune disparition brutale).

## Rattachements (NE PAS fonder ici)
- **Volet (b) de D64** — lisibilité des auxiliaires (amas de cercles indistincts,
  survol→nom) : c'est **D60** (déjà CONÇU, extension de D31). NE PAS l'implémenter
  dans ce sprint ; juste **noter** dans DETTE que le volet (b) de D64 est
  **subsumé par D60**.

## Ce qu'il NE faut PAS faire
- Pas de refonte du `PlantRenderer` ni du protocole snapshot.
- Pas de travail sur les auxiliaires (→ D60).
- Ne rien changer au moteur (① ② l'ont fait).

## Golden attendu — INTACT
Vue C# / lecture pure. `python3 -m tests.test_golden` doit PASSER au hash de fin de
② (inchangé par ce tronçon).

## Vérifications
- `python3 -m tests.test_golden` PASS (hash de fin ②).
- La vérif #1 (snapshot : hôte vivant + symptôme `ombre` croissant sur le dominé)
  passe.
- Build C# filet si du C# a été touché : `dotnet build Symbiose.csproj` (depuis la
  racine Godot). Sinon inutile.

## Mise à jour de fin de tronçon / clôture sprint
`00_etat.md` : ③ fait, §F5 renseigné, **SPRINT CLOS**. Commit. Rappeler à Nico le
F5 de validation.
