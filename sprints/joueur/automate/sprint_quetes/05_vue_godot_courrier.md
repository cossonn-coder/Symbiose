# Tronçon ⑤ — Vue Godot : panneau « courrier »

> Sprint QUÊTES (D79). Lire d'abord : `CLAUDE.md`, `00_etat.md`,
> `docs/joueur/automate/conception_quetes.md`, tronçons ①→④ (faits).
> Golden : **INCHANGÉ**. Dernier tronçon (règle « vue Godot toujours »).

## Objectif
Rendre les quêtes **jouables et lisibles** : le pont expose les quêtes actives +
progression diégétique, et un **panneau « courrier »** Godot affiche les lettres
(cochées quand comblées). Vue PURE, aucun calcul côté C#.

## Côté pont (Python) — `tools/simserver/`
1. Nouvelle commande read-only, sur le **modèle de `voix.py`** (`cmd_carnet`,
   `cmd_encyclopedie`…) : `cmd_courrier` (ou `cmd_quetes`) qui renvoie la liste
   des quêtes actives : `id`, `donneur`, `texte_lettre`, `avancement_diegetique`,
   `accomplie`. Le **chiffre exact** (progression brute) n'est exposé QUE si un
   flag debug est présent (V2/#5).
2. Bump de version de protocole (`version.py`) — noter le nouveau numéro dans
   `00_etat.md` et le journal.

## Côté Godot (C#) — `visuals/` ou panneau dédié
3. Panneau « courrier » sur le **modèle des panneaux voix narratives** (D13/D14,
   hub-maison cliquable) : une **lettre / fiche par quête**, cochée quand comblée,
   progression en **langage diégétique** (jamais de barre chiffrée en primaire).
   Rattachement au hub-maison si cohérent (une « boîte aux lettres »).
4. `dotnet build Symbiose.csproj` doit passer (filet de compilation VM).
5. **Banc / point F5** : prévoir une petite mise en situation (init + une quête
   active de chaque famille) pour que Nico observe le panneau au F5. Documenter
   la manip exacte dans `00_etat.md`.

## Tests
- `python3 -m tests.test_golden` → **hash INCHANGÉ** (pont read-only).
- `dotnet build` OK.

## Ne PAS faire
- Aucun calcul de progression côté C# (le pont fournit tout). Pas de chiffre en
  primaire (#5). Pas de GDScript (C# only).

## Fin de tronçon — clôture du sprint
- Golden inchangé, build OK → maj `00_etat.md` (sprint CLOS).
- **Maj `DETTE.md`** (D79 → CLOSE), **`BACKLOG.md`**, et **entrée `journal.md`**
  (décision figée + clôture). Rattacher toute dette de vue restante (ex. `outil`
  différé au ④). Supprimer `HANDOFF.md` s'il traîne.
- Points **F5 Nico** à consigner (panneau courrier + une quête de chaque famille).
