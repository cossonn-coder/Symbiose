## 2026-11-04 — Sprint TRÈFLE DOMINANT (D126) — CLOS côté code

Kickoffs : `sprints/vegetal/catalogue/sprint_trefle_dominant/`. Bilans et écarts détaillés dans son `00_etat.md`. Golden `ac48b170…` → `a10b7225…`, population `6007f2cd…` → `0556d1c1…`, pont 0.6.5.

- ① `4e8482e` : clé `sature_a` sur `inject_field` (fixation pleine à N=0, nulle à N=1,5), `Clover.longevity_years = 2`. Golden re-figé annoncé `c23f70d9…`. Trèfle an 5 : 537 → 289 plantes [automate actif, `full`, seed 42, n=1 graine, VM].
- ② `b4e9112` : dactyle, fétuque rouge, plantain lancéolé avec leurs voix (page P48), `choisir_espece` selon l'azote puis hash. Golden re-figé annoncé `a10b7225…`. 20 espèces en an 5 [n=1 graine, VM].
- ③ `5228de2` : trèfle à quatre feuilles, statut pur par hash, bonus unique à la récolte, page P49, pont 0.6.5. 1,98 pied à la fois en an 3 [n=1 graine, VM]. Golden intact.
- ④ `bb3ced7` : tapis de trèfle, quatre feuilles en X, dactyle, fétuque, plantain. Draw calls ×4 280 → 170 [n=1 run, VM]. FPS non concluants [n=8 relevés, VM chargée]. Golden intact, build vert.

**Critères §5 ratés** : part du trèfle 44,6 %, cible sous 40 % ; plots neufs entre an 3 et an 5 29 %, cible un tiers [`full`, seed 42, n=1 graine, VM]. Le trèfle recule sans retour observé : le tapis qui bouge n'est pas atteint. L'ombre du dactyle bloque bien les stolons (41 plots sur 41, an 5), mais il y a ~40 dactyles pour ~300 trèfles [n=1 graine, VM], car les vivaces à archétype ne réalimentent pas leur banque (`sim/engine/mortalite.py`). Corriger cela re-figerait largement le golden : arbitrage de Nico attendu.

**Écarts** : `population_hash` re-figé au ① et au ②, non prévu par les kickoffs, même cause que le golden. La référence 729 / 434 de la conception a été mesurée sans automate : le vrai « avant » est 834 / 537 [n=1 graine, VM]. Correctif de l'orchestrateur au ② : borne `% len` dans `choisir_espece` (`_hash_noise` peut valoir 1,0), hash intacts.

Refactor auto-léger : rien à scinder, `serialize.py` est pile à 400 LDC. Attend le F5 de Nico.

## Suite du 2026-11-04 : F5, rapport perf, rejeu

**F5 de Nico** : « ça me convient tel quel pour la prairie ». D126 fermée, correction de la banque des vivaces non retenue, reste versé en D127.

**Rapport PC, an 25** : trèfle 26,5 % des plantes, 18 espèces [n=1 run, PC, automate débranché]. **Rejeu VM jusqu'à s925, sans automate** : le trèfle remonte, 188 → 252 entre an 7 et an 8, 160 → 203 entre an 15 et an 17 ; plots neufs de la dominante 19 à 43 % par an dès l'an 3 [n=1 rejeu, VM]. Le retour manquait à 5 ans : il faut plus longtemps pour le voir.

**Rapport C enrichi** (`606f32e`, pont 0.6.6), à la demande de Nico (« c'est ça qu'il faut changer ») : sonde serveur `perf_tick.py`, bilan par an `perf_annees.py`, RSS Windows.

**Tick de 62 s** : s921 fait 62 568 ms au PC [n=1 run, PC, Python 3.14], 1 820 ms au rejeu [n=1 rejeu, VM, Python 3.13]. Non reproduit, cause ouverte en D127.

**Piège de mesure** : le rejeu montrait des ticks médians de 3,9 à 4,9 s en ans 5 à 7, CPU compris. Rejoué plus tard : 1,1 à 1,6 s, s260 9 763 → 1 101 ms [n=2 rejeux, VM]. Des `stockfish` occupaient la VM (charge relevée jusqu'à 17,9). Mesurer le temps sur cette VM exige de regarder sa charge.
