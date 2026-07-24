# Tronçon ③ — Molène : indicatrice de terre malade + 5 voix

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` +
> `docs/champs/sol/conception_memoire_inoculum.md` (§6) + la règle « toute plante
> = ses 5 voix » (`docs/narration/voix/conception_voix_narratives.md`).
> Pré-requis : ①② faits. Lancement depuis `data/code/`.

## Objectif
Ajouter *Verbascum thapsus* (bouillon-blanc, Scrophulariaceae, bisannuelle
pionnière indicatrice) qui **apparaît sur terre malade persistante**, via un
facteur de niche `arch_inoculum`, avec ses **5 voix** complètes.

## Golden ATTENDU : **NEUTRE visé** (re-figeage localisé annoncé si besoin)
`arch_inoculum` est une **porte de RELÂCHE** : molène gatée à ~0 sur sol sain,
≈1 seulement au-dessus de `INOC_MOLENE_SEUIL` ; tous les autres archétypes = 1.0
neutre. Sur le smoke (sol sain, inoculum nul), molène ne lève pas → golden
INTACT. **Si** l'ajout au catalogue de succession déplace malgré tout un tirage,
re-figeage **localisé + annoncé** (prouve la cause). Vise NEUTRE d'abord.

## À implémenter
1. **Espèce** — `plants/species/adventices.py` (ou le module d'indicatrices
   adéquat) : classe `Verbascum`/`Molene(PlantBase)`, `family="Scrophulariaceae"`,
   `life_cycle="biennial"`, archétype pionnier/indicateur, `fungal_susceptibility`
   basse (elle prospère où d'autres tombent), `keywords=["Indicatrice","Médicinale",
   "Bisannuelle"]`, stades rosette→hampe florale. Aligne-toi sur une indicatrice
   existante (ex. la minette `MedicagoLupulina`) pour tous les champs requis.
2. **Facteur de niche** `arch_inoculum` — patron strict de `arch_ph`/`arch_temp`
   (`fields/seedbank.py:germinate_candidates`, ~ligne 410) :
   - l'appelant (le chemin qui bâtit `arch_temp`/`arch_ph` avant d'appeler
     `germinate_candidates`) construit un dict `{archétype -> facteur}` où **seul**
     l'archétype de la molène porte `smoothstep(inoculum.total(r,c), INOC_MOLENE_SEUIL)`
     et tous les autres valent `1.0` ;
   - dans `germinate_candidates`, ajoute le paramètre `arch_inoculum=None` et
     `if arch_inoculum: niche_eff *= arch_inoculum.get(archetype, 1.0)` (comme
     `arch_ph`). Absent ⇒ comportement historique (golden intact).
   - `INOC_MOLENE_SEUIL` dans `constants.py` (placeholder §10).
3. **Les 5 voix** (§6, obligatoire — une plante muette est à proscrire) :
   - **encyclopédie** 3 niveaux (`sim/encyclopedie_corpus.py`) ;
   - **carnet** `CONCEPT_DE` concept « maladie / sol vicié » (`sim/…` du carnet) ;
   - **pages secrètes** 1 entrée lore médicinal bouillon-blanc (`sim/pages_corpus.py`) ;
   - **magazine** rattachement famille Scrophulariaceae (registre magazine) ;
   - **événements** marqueurs cycle bisannuel (rosette→hampe) au ledger si le
     patron d'événements de cycle de vie l'exige.

## Ce qu'il NE faut PAS faire
- NE PAS faire de molène une porte qui REFERME la niche des autres (elle ne
  module QUE son propre archétype ; les autres restent à 1.0).
- NE PAS livrer l'espèce sans ses 5 voix.

## Verrou de test
Étends `tests/test_inoculum.py` : (a) molène ne germe PAS à inoculum nul ;
(b) germe quand `total > INOC_MOLENE_SEUIL` (niche ouverte) ; (c) les 5 voix
existent (assert de présence des entrées molène dans chaque corpus). Golden :
NEUTRE visé (sinon hash annoncé + cause).

## À la fin
`00_etat.md` : statut golden (neutre / re-figé localisé), §REPRISE → tronçon ④.
