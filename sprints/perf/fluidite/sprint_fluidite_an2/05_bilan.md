# ⑤ Bilan — mesure finale, protocole PC, clôture D114

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (toutes les mesures ①→④), le doc de conception.
**Golden** : intact `fecccded…`.

## À faire
1. **Banc final VM** (n ≥ 3 runs par cas, en série, charge < 4) :
   `tools/banc_cadence.py` sans/avec automate (156 sem.) et `tools/perf_vm.sh -E 30 -A 1 -W 90`
   OFF / automate onglet fermé / onglet ouvert. Tableau avant (HEAD `5c69ac6`) / après dans
   `00_etat.md` et dans le doc de conception (§ bilan à ajouter), limites entre crochets.
2. **Protocole PC pour Nico** (court, dans `00_etat.md` §F5) : commandes exactes — touche E
   en an 2 à 1 s/semaine, sans puis avec automate (touche A) — et ce qu'il doit coller
   (rapport du presse-papier). Rappeler : `git pull` avant (le F5 teste souvent du code non
   poussé). Conversion VM → PC : ratio CPU ~1,3 [mesure 2026-07-09] pour le moteur ; pour la
   vue, seul le rapport PC fait foi.
3. **Verdict cible** (≤ 1,5 s/sem effectives, aucune image > 100 ms, PC an 2) : tenue / non
   tenue côté VM, à confirmer PC. Si non tenue : nommer le poste restant **mesuré** et ouvrir
   UNE dette seulement en fermant D114 (règle : pas de dette ouverte sans en fermer une).
4. **Docs** : `DETTE.md` (D114 → close ou réduite au poste restant), `BACKLOG.md`, `journal.md`
   + entrée `journal/`, mémoire de file priorisée (prochain = D112 sprint B vue), rappel
   « Vigueur infinie ON » à repasser OFF avant packaging.

## Ne PAS faire
- Optimiser encore ici (le bilan mesure, il ne corrige pas).
- Lancer `test_epaisseur_500ans`.

## Fin de tronçon
Golden intact ; `dotnet build` vert ; docs à jour ; commit + push.
