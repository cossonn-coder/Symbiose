# Kickoffs de dette — index

> **Écrit pendant ton absence (2026-06-06).** Tu m'avais demandé : « regarde tous
> les sujets de dette et écris pour chacun un kickoff autosuffisant ». Ce dossier
> rassemble **un kickoff par dette dormante** (celle qui n'avait pas déjà son
> fichier). Chaque kickoff est **autosuffisant** : une session démarrée à froid sur
> `lis sprints/dette_kickoffs/DNN_*.md` peut le traiter sans contexte préalable.
>
> Là où **un choix de design t'attend**, le kickoff a une section dédiée
> **« 🔵 Choix de design à trancher »** : options, conséquences, et un **défaut
> recommandé** que je ne pose pas en silence — tu décides. Rien n'a été codé ; ce
> sont des plans à valider.

## Ce qui était déjà fait (vérifié ce 2026-06-06)
- **Tronçon Croissance·3** (`sprint_croissance/03_seam_tailler.md`) : **déjà
  exécuté et commité** (`0997c1b`). Vérifié vert : golden `6369c30b…` PASS,
  `test_croissance` 43/43, `test_vigueur` 110/110. Rien à refaire.
- Nettoyé : `sprint_croissance/03bis_pommier.md` se terminait par deux lignes
  parasites (`</content>`/`</invoke>`, résidu d'écriture) — retirées.

## ⚠️ Incohérence doc repérée
**D16 (météo)** : `DETTE.md` la marque « reste : implémentation », mais
`BACKLOG.md` (l.21) atteste que le **Sprint implémentation météo est TERMINÉ le
2026-06-04** (golden `63bfdac4…`, `sprint_meteo_impl/`). La ligne `DETTE.md` D16
est **périmée** — météo est faite côté Python. Je ne l'ai pas réécrite (à toi de
confirmer), mais **ne lui écris pas de kickoff** : il n'en faut pas.

## Les dettes qui ont DÉJÀ un kickoff (ne pas dupliquer)
Tout le **portage C# / frontend Godot** est déjà couvert par les kickoffs
historiques — et **non prioritaire** par ta décision (mémoire : « attend que la
conception soit satisfaisante », dette D24) :

| Dette | Kickoff existant |
|---|---|
| D2, D3, D4 (dims tuiles, noms sprites, sprite maison) | `sprints/sprint_1_recalibrage_visuel.md` |
| D7, D8, D9 (namespace, `Main.tscn`, conflit `PlantInstance`) | `sprints/sprint_2_orchestration.md` |
| D5, D6, D10, D24, et les ports C# de D11/D12.5/D17/D20/D21/D22/D27 | `sprints/sprint_3_portage_simulation.md` |
| Affichage écologique C# | `sprints/sprint_4_mecaniques_conception.md` |
| D29 (croissance procédurale) | **sprint ACTIF** : `sprints/sprint_croissance/` (tronçons 3bis→6 restants) |

## Les kickoffs neufs de ce dossier
Tous sont des **conceptions** (sauf D32, pur perf, et D23, surtout data) — donc le
livrable est d'abord **un doc de design + des choix tranchés avec toi**, pas du
code. C'est le mode « conception avant code » du projet.

| Fichier | Dette | Ampleur | Choix de design pour toi ? |
|---|---|---|---|
| `D19_organes_comestibles.md` | D19 — modèle d'organes feuille/fleur/fruit + déplétion/repousse + valeur nutritive signée | moyen | **oui** (3 choix) — couplé au tronçon Croissance·5 |
| `D30_structure_compaction_sol.md` | D30 — champ support de l'aération (bonus grelinette) | petit | **oui** (1 choix clé : `vers_de_terre` vs champ dédié) |
| `D13_magazine_botanique.md` | D13 — magazine = canal d'acquisition d'espèces (Vigueur + maîtrise) | moyen | **oui** (3 choix) |
| `D14_carnet_auto.md` | D14 — carnet auto, bascule descriptif → interprétatif | moyen | **oui** (3 choix) |
| `D15_extension_terrain.md` | D15 — tuile thématique qui apparaît au palier de maîtrise | moyen | **oui** (3 choix) |
| `D18_pages_secretes.md` | D18 — pages secrètes (savoirs ésotériques épars) | moyen | **oui** (3 choix) |
| `D12_2_table_deblocage.md` | D12.2 — table palier→déblocage (coordonne D13/D14/D15) | petit | dépend de D13/D14/D15 |
| `D23_catalogue_arbres.md` | D23 — étendre le catalogue d'arbres pérennes | petit | un (liste d'espèces + rôles de strate) |
| `D26_diversification_ecologique.md` | D26 — diversifier le catalogue ; décision class-based vs data-driven | gros | **oui** (1 choix structurant) |
| `D32_optim_lightfield.md` | D32 — perf du `LightField` (cache d'ombres) | moyen | non (approche claire ; à faire « si la perf serre ») |

## Ordre recommandé (et pourquoi)
La logique : **finir les boucles de conception qui se débloquent l'une l'autre**,
en commençant par celles qui ont le moins de dépendances et le plus de valeur de
gameplay immédiate.

1. **D30** (structure/compaction) — petit, **un seul choix**, débloque le couple
   pédagogique bêcher/grelinette déjà à moitié en place. Quick win.
2. **D19** (organes comestibles) — **se conçoit AVEC le tronçon Croissance·5**
   (organes procéduraux) : les deux parlent des mêmes feuille/fleur/fruit. À cadrer
   avant ou pendant t5 pour ne pas dessiner deux fois le modèle d'organe.
3. **D13 → D14 → D15** (magazine, carnet, extension terrain) — les **trois
   consommateurs de la maîtrise** (`docs/joueur/maitrise/conception_maitrise.md` §7). À concevoir dans
   cet ordre car ils partagent la même question « quel palier débloque quoi ».
4. **D12.2** (table palier→déblocage) — **APRÈS** D13/D14/D15 : elle ne fait que
   les **coordonner** (elle est explicitement bloquée tant qu'ils n'existent pas).
5. **D18** (pages secrètes) — la 3ᵉ voix narrative, indépendante ; quand tu veux.
6. **D26** (diversification) — **gros**, et son choix class-based vs data-driven
   conditionne D23. À faire quand la croissance procédurale (D29) est stabilisée,
   car elle ajoute des profils de croissance par espèce.
7. **D23** (catalogue arbres) — après D26 (hérite de sa décision de structure) ou
   en parallèle si tu restes class-based.
8. **D32** (perf LightField) — **seulement si la perf serre** (aujourd'hui ×339 de
   marge). À garder sous le coude pour la sim offline / le portage C#.

## Rappel des garde-fous (CLAUDE.md)
- **Conception avant code** : pour les dettes de design, le sprint produit d'abord
  un `CONCEPTION_*.md`, validé avec toi, **avant** toute ligne de moteur.
- **Golden sacré** : tout ce qui touche le tick doit préserver (ou re-figer de
  façon **maîtrisée et annoncée**) `tests/test_golden.py`. Les couches « au-dessus
  du tick » (Vigueur, maîtrise, actions joueur) ne le re-figent jamais.
- **Pédagogie** : tu viens du C/Python embarqué + simulation (expert), débutant
  Godot/C# ; les sujets bio/éco te sont produits comme **doc à étudier**, pas comme
  questions à trancher dans le vide.
