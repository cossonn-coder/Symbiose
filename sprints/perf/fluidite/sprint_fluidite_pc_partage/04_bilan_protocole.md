# ④ Bilan VM + protocole d'un run PC + clôture

Lire d'abord : `CLAUDE.md`, `00_etat.md` (§① à §③), `docs/perf/fluidite/conception_fluidite_pc_partage.md`.
**Golden intact** (vérifie-le une dernière fois). Pas d'appel DeepSeek.

## À faire
1. Banc VM complet, même protocole que les sprints précédents [n=1 run chacun, charge notée] :
   `tools/perf_vm.sh -3 25,25,20 -P 20 -A 1 -W 90 -S 1521550718` et balayage
   `-Z 4 -S 1521550718 -w 90 -c 1650,950` ; headless `python3 -m tools.banc_cadence --runs 3
   --semaines 104`. Tableau avant → après dans `00_etat.md` (avant = fin du sprint LEVIERS,
   cf. son « Bilan VM du sprint »), chaque chiffre avec sa limite entre crochets.
2. **§F5 — protocole d'UN run PC** dans `00_etat.md` : Main Run Args exacts (banc 3 phases
   + partage), ~durée, quoi copier ; puis aller-retour de zoom ×0,5 → ×32 → ×0,5 + touche Z.
   Questions F5 (au plus 3-4) : 15 FPS en retard gênant ? caméra fluide ? à-coup des hauts
   zooms ? HUD pont 0.6.0 inchangé.
3. Écrire **comment lire** le tableau de partage pour décider (ex. si A3/A4 tiennent
   ≤ 2 s/sem → régulateur gardé ; si A2/A4 ≫ A1/A3 → priorité Normal par défaut, avec le
   coût en images) — la décision finale se prend sur le run PC, pas sur la VM.
4. Clôture : `DETTE.md` D116 (note datée : ce qui est fait, chiffres VM, attend le run PC ;
   l'enchaînement anticipé reste écarté — 2 s de latence jugés trop longs par Nico),
   `BACKLOG.md`, `journal.md` + entrée `journal/` (style des entrées existantes),
   mémoire `project_file_priorisee_20261022.md` si elle cite ce 3ᵉ temps.
5. Commit + push.

## Ne PAS faire
Changer un réglage par défaut sur la foi de la VM ; ouvrir une dette sans en fermer
(feedback Nico) ; lancer `test_epaisseur_500ans`.
