## 2026-06-13 — Sprint planter/arroser · Session A : `planter` (germination différée) — golden INTACT

Premier des deux derniers gestes de base. Conception FIGÉE
(`CONCEPTION_PLANTER_ARROSER.md`, Q1–Q12). `planter` ne spawn PAS un semis : il
**dépose une graine** (`GrainEnAttente`) que la **succession ordinaire** lève au
bon moment (plot libre + niche favorable) — on enseigne « le bon moment » par
l'observation (philo #6), aucune écriture directe sur le vivant (philo #2).

**`GrainEnAttente`** (`fields/seedbank.py`, exporté) : structure DISTINCTE de la
banque-sol agrégée — gènes **PROPRES** (non moyennés, ≠ `sample_genes`) pour que
semer une belle graine sélectionnée garde son sens (D17/D22). Porte `cultive`,
`player` (l'avatar planteur — la détection « replanté » est par avatar) et
`semaine_depot`. Stockée **par plot sur `Tile`** (`grains_en_attente[(r,c)]`, FIFO)
— le porteur des plantes ; **vide au repos**.

**`planter(gs, player, tile, eco, species, r, c)`** (`sim/actions.py`) : take
**banque-joueur** (`PlayerSeedBank.take`, source unique Q2) ; **refus si lot vide
EN AMONT de toute dépense** ; coût **`FAIBLE`** binaire tout-ou-rien (graine
conservée si Vigueur insuffisante) ; `cultive=True` posé au dépôt.
**Empilement autorisé (Q4)** : jamais de refus sur plot occupé — la graine
**patiente**. Nouvelles entrées `COUTS["planter"]=FAIBLE` /
`OBJETS_TOUCHES["planter"]=("semis",)` (neutres sans maîtrise → golden Vigueur
intact).

**Levée différée** (`sim/succession.py`, helper `_lever_grains_en_attente`,
appelé dans `succession()` ET `spring_flush()` **avant** le balayage adventices) :
sur plot libre + niche favorable, lève le grain le plus ancien via `add_plant`,
écrit ses **gènes propres** et transmet le tag (`marquer_replante`, import LOCAL
pour éviter tout ordre de chargement fragile). Tirage **déterministe** sur un
**canal de hash distinct** des adventices (`week*7+50` / `week*100+50`) ; une
graine plantée lève à proba = niche (sans l'escompte de densité féral → un semis
délibéré prend plus volontiers). `occupied_roots` muté → le balayage qui suit ne
re-germe pas sur le plot pris.

**Garanties :** golden écolo **INTACT** `16a1b937…` (geste event-driven hors tick,
`grains_en_attente` vide → court-circuit immédiat du helper). `test_planter`
**18/18** (dépôt+coût, refus lot vide sans dépense, levée gènes propres + tag
`replante`, empilement patiente → lève au dégagement). `test_vigueur` 135/135,
`test_croissance` 67/67 (imports non régressés).

**Reste sprint :** Session B (`arroser` + modèle « eau » : drainage par `soil_type`,
asphyxie par paliers — golden RE-FIGÉ T1 maîtrisé) ; Session C (pont
`sim_server.py` route planter/arroser + banque-joueur au snapshot, protocole
0.3.3).
