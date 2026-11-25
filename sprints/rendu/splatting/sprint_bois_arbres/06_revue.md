# ⑥ Revue des paliers et clôture — kickoff

Lire d'abord : `CLAUDE.md`, `00_etat.md` (comptes rendus ①→⑤), `docs/rendu/splatting/conception_bois_arbres.md`,
la section « F5 consolidé » de `sprints/rendu/splatting/sprint_reliquats_plantes/00_etat.md` (modèle).
Golden attendu : **`bce813af…` INTACT**. Build vert, 0 avertissement.

## Objectif
Tronçon vue Godot final : revue « beau à chaque palier » du bois et des graminées, finitions, F5
consolidé, clôture.

## À faire
1. Planches ×0,5 → ×32 (`-l 2`) avant (`SYMBIOSE_SPLATS=0`) / après : les 12 essences (`houppiers`),
   en ÉTÉ et en HIVER NU (bois seul : c'est là que le tube et l'écorce se jugent), `verger_floraison`,
   graminées (`planche_especes`), un squelette, monde `full`. Lire les montages ; corriger les
   finitions sans recette neuve (seuils, fondus, tri).
2. Mémoire de précuisson et ms par image par palier (VM, n=1, non transposable) ; nombre de plantes
   en repli et lesquelles (ligne du rapport ajoutée au ①).
3. **Section « F5 consolidé S2 »** dans `00_etat.md` (même forme que S1) : général + par essence +
   graminées + portraits ; à jouer au F5 complet APRÈS S3.
4. Clôture : `journal/` (entrée neuve) + `journal.md`, `docs/rendu/splatting/backlog_splatting.md`
   (S2 CLOS, S3 prochain), `DETTE.md` si un reste doit y aller (règle : pas de dette ouverte sans en
   fermer une → sinon le consigner pour l'orchestrateur), `/refactor` auto-léger.

## Ne PAS faire
- Recettes neuves (les signaler pour S3 ou plus tard). `data/code/`, `test_epaisseur_500ans`, DeepSeek.

## Fin
`00_etat.md` §REPRISE → « S2 CLOS côté code ; prochain = `/conception` S3 (lisière sur le bois de S2
— primitive ruban réutilisable —, puis écran de chargement en mycélium) ». Commit.
