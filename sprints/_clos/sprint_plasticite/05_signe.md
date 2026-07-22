# Tronçon ⑤ — Signe diégétique d'acclimatation + dette

> Sprint « plasticité ». Conception : `docs/vegetal/genetique/conception_plasticite_expression.md`
> (§3-P3, §3-P4, §4, §7). **Lire la conception + relire le journal `00_etat.md`.**
> **Golden NEUTRE attendu** (détecteur = lecture pure, comme la sémiologie ①).

## Objectif
Rendre la plasticité APPRENABLE, pas magique (philo #5/#6) : une plante fortement
acclimatée le MONTRE. Le joueur voit le signe → formule une hypothèse → consulte →
comprend l'acclimatation.

## Périmètre
1. **Détecteur d'acclimatation** dans `sim/semiologie.py` (patron des détecteurs
   chroniques existants : fonction pure `(plant, eco, saison) -> float`, intensité
   [0,1], rampe sur la SUR-expression). Nouvelle (ou nouvelles) `cause` —
   p.ex. `acclimatation` générique, ou par stress dominant (`acclim_secheresse`…).
   **Trancher dans le journal** : un signe générique ou un par stress. Intensité ∝
   `max_g(expression[g] − 1)` (le stress le plus fortement compensé).
   - L'ajouter au registre de priorité/tri de `leaf_symptoms` (cause distincte,
     forward-compatible : la vue ignore une cause inconnue).
2. **Snapshot** : la cause sort déjà via `leaf_symptoms` (pas de nouveau champ).
   Bump pont (`tools/simserver/version.py`) si une nouvelle `cause` = extension de
   schéma (champ optionnel côté vue). Version de départ actuelle : 0.5.2.
3. **Vue C# (`visuals/PlantRenderer*.cs`)** : consommer la nouvelle `cause`. Forme
   bio (§4) : feuillage plus **coriace / glauque (cire)** pour une forte
   acclimatation sécheresse → canal couleur/texture (réutiliser le mécanisme
   `SetSymptoms` / `ColorantTints` / canaux texture posé au sprint sémiologie ③).
   **F5 visuel = Nico.**
4. **Dette + journal** : inscrire dans `DETTE.md` le **lien Maîtrise → carnet
   interprétatif** (P4 : au palier « adaptation/génétique », le carnet passe de
   descriptif à interprétatif). Entrée `journal/` du sprint (décisions, golden,
   knobs de calibrage retenus). Clôturer le sprint dans `BACKLOG.md` / mémoire.

## Vérifs
- `python3 -m tests.test_golden` → **NEUTRE** (détecteur = lecture pure dans
  `_snapshot`, zéro écriture moteur). Si dérive : un détecteur écrit → bug.
- Smoke : une plante acclimatée forcée sort bien la cause `acclim…` dans
  `leaf_symptoms`, triée correctement ; plante neutre → pas de signe.
- `dotnet build` vert, aucune réf résiduelle cassée.

## Sortie
MAJ `00_etat.md` (statut ⑤ clos = SPRINT TERMINÉ, golden final, journal). MAJ
`journal.md` (index) + `DETTE.md` (dette P4) + `BACKLOG.md`. Commit final.
