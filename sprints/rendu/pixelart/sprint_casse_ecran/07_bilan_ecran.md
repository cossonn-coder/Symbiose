# ⑦ Bilan à l'écran — planche complète, mesures, protocole F5

Lire d'abord : `CLAUDE.md`, `00_etat.md` (toutes les §Notes), `docs/rendu/pixelart/conception_casse_ecran.md`.
**Golden intact** (vérifier une dernière fois : `python3 -m tests.test_golden` depuis
`data/code/`). Filet : `dotnet build Symbiose.csproj`. Pas d'appel DeepSeek.
Ne JAMAIS lancer `test_epaisseur_500ans`.

## Objectif
Tronçon vue de clôture (règle permanente). Pas de nouvelle fonctionnalité.
1. **Planche complète** : banc `full`, paliers ×0,5→×32 × 4 rotations × 3 heures (matin,
   midi, soir) × vent calme / fort ; plus la planche L (plantes) et la planche faune ⑤.
   Lire les captures avec Read.
2. **Rapport final du banc ①** comparé à la ligne de base ① : un tableau par critère de la
   checklist du brief (tons, noir, contour, dérive, aplat, voisins, côté de l'éclat,
   continuité ×2→×4). Tout chiffre porte sa limite entre crochets ([n=…], [VM]).
3. **Perf finale** : banc E (`tools/perf_vm.sh`) et outil Z vs l'état de départ du sprint
   (sprint PARTAGE : VM A 2,01 s/sem [n=1 run, VM]) — aucune régression > 10 %.
4. **Taille des fichiers** : `tools/compte_ldc.py` sur les fichiers touchés ; > 400 LDC →
   `/refactor` léger (golden-gaté), comme en fin de `/sprint-auto`.
5. **Protocole F5 de Nico (ressenti seul, court)** dans `00_etat.md` §F5 : 6-8 points max —
   maison opaque + H ; Maj+F3 jauges ; F6 commence par le vent ; psilocybe → vision ;
   zoom ×2→×32 « même plante » ; soleil visible le matin et le soir ; bêtes reconnaissables ;
   lisière animée au vent. Pas de mesure demandée à Nico.
6. Mettre à jour `DETTE.md` (D112 : points fermés côté code, F5 restant ; D117 nuit
   inchangée), `BACKLOG.md`, `journal.md` + entrée `journal/`.

## Ne PAS faire
Corriger en douce un défaut trouvé au bilan : le consigner (dette ou note D112) sauf s'il
est trivial et localisé.

## Fin de tronçon
`00_etat.md` (tableau → tout fait, §F5), commit, push.
