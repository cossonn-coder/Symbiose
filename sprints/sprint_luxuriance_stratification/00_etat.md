# Sprint « Luxuriance par stratification » (D65) — état vivant

> Carnet de bord de la `/conception` (skill `conception`, §0bis). Reconstructible
> à froid : lire `CLAUDE.md` + ce fichier suffit à reprendre. PHASE A (challenge)
> en cours — RIEN n'est figé tant que Nico n'a pas dit « OK ».

## Sujet
D65 « luxuriance par stratification / densification » — extrait de D64. Un plot
n'est pas limité à une plante : plusieurs strates coexistent (couvre-sol +
potagère + grimpante + traçante), la **compétition émerge de la densification**,
pas d'un conflit discret. Détail source : `CONCEPTION_USURE_LETALITE.md §6`.

## 4 briques D65 (toutes prioritaires Nico)
1. Densification clonale des couvre-sols/traçantes (stolons trèfle/fraisier/menthe).
2. Champ de couverture au sol par strate (« sol couvert à X % »), lu par écologie + rendu.
3. Empilement multi-strates VISIBLE (superposition / ordre de dessin).
4. Empreinte graphique propre à l'espèce — taille au sol ET silhouette.

## Fondations VÉRIFIÉES dans le code (ne pas réinventer)
- Strates par stade : `plants/base/empreintes.py::STRATE_DEFAULTS` (canopy_r/root_r/height/density)
  + `STRATE_SHADE_TOLERANCE`. Strates : sol/basse/moyenne/haute/grimpante.
- Co-occupation DÉJÀ permise : `world/tile.py::add_plant` ne teste pas l'occupation.
- Ombrage vertical asymétrique émergent : `fields/light.py` (seuls les voisins PLUS HAUTS ombrent).
- Empreinte au sol dérivée de la structure : `instance.update_footprint()` → `footprint{height,canopy_r,root_r}`.
- Conflit rendu NON-LÉTAL par D64① (co-occupation viable = blocage amont levé).
- Reproduction 100 % par graine (`sim/reproduction.py`) — AUCUN clonal existant.
- Évaporation modélisée (`fields` : `EVAPORATION`, `SOIL_RETENTION`) → hook couverture→humidité dispo.
- Catalogue : Trèfle (Clover) OUI ; Courgette OUI ; fraisier/menthe NON (prévus D62).

## COUPLAGE MAJEUR — D62
Brique 1 (clonal stolons/rhizomes) = frontalement **D62** (rampantes clonales,
🟡 non conçue : fraisier/menthe/framboisier/bambou + violettes, chacune 5 voix,
touche `reproduction.py`/`seedbank.py`). À trancher avec Nico : D65 absorbe D62 /
D65 sans clonal (renvoyé à D62) / clonal MINIMAL ici + espèces à D62. → Q1.

## Décisions ARRÊTÉES (Nico, lot 1 — 2026-07-04)
- **D1 — D65 ABSORBE D62.** Mécanique clonale complète + espèces (fraisier,
  menthe, framboisier, bambou traçant, violettes odorantes), chacune ses 5 voix.
  D62 sera fermée/fusionnée à la clôture. Sprint gros → 6 tronçons.
- **D2 — champ de couverture = 1 SCALAIRE par plot** (fraction couverte, strates
  sol+basse), scatter depuis les empreintes. Lu par 2 flux écolo (philo #2) :
  évaporation réduite + germination d'adventices supprimée. + 3ᵉ rôle interne :
  **gate d'établissement du clonal** (couverture saturée = pas de nouveau ramet)
  → auto-limitation émergente ET **cap perf** du nombre de plantes.
- **D3 — empreinte espèce = silhouette de rendu + override CIBLÉ.** Pas de
  nouveau champ écologique (canopy_r pilote déjà ombre+uptake). On ajoute un
  descripteur `silhouette` (data) + un override d'empreinte au sol seulement là
  où le défaut de strate ment (courge basse-mais-étalée). Overrides limités aux
  espèces HORS golden → neutre.
- **D4 — clonal = UNE mécanique paramétrée** (pas 3 chemins de code). `clonal_mode`
  ∈ {none, stolon, rhizome, drageon} module 3 axes : portée (radius), gate
  (stolon = besoin lumière sol / rhizome = tolère l'ombre, réserve / drageon =
  courte portée près de la mère), agressivité (intervalle). Ramet = COPIE
  génétique (pas de brassage), déterministe (hash), coût Vigueur sur la mère.

## Golden — re-figeages prévus
- **T1** (couverture→évaporation) : RE-FIGÉ maîtrisé (humidité dérive sur tout
  plot couvert). Le golden porte Clover sur tuile 2.
- **T2** (clonal sur trèfle du golden) : RE-FIGÉ maîtrisé (ramets de trèfle).
- T3/T4/T5 : NEUTRE (overrides + espèces hors scénario golden). T6 : INTACT.

## Coût perf (à surveiller)
LightField = déjà 53 % du CPU. Champ de couverture = 1 scatter (stamp empreinte,
réutilise `_plots_in_radius`), jamais un balayage. Le gate de couverture BORNE le
nombre de ramets → protège le LightField d'une explosion de plantes. Budget ≤ +10 %.

## Carte des tronçons (perf-first, golden discipliné)
1. Champ de couverture `couverture_sol` + hooks évaporation & adventices — RE-FIGÉ.
2. Mécanique clonale (ramets déterministes, gate couverture, coût Vigueur) — RE-FIGÉ.
3. Empreinte/silhouette par espèce (descripteur `silhouette` + override ciblé) — NEUTRE.
4. Catalogue clonal ①  : fraisier + menthe (+ trèfle stolonifère) + 5 voix — NEUTRE.
5. Catalogue clonal ② : framboisier + bambou traçant + violettes + 5 voix — NEUTRE.
6. Vue Godot : empilement multi-strates visible + couverture rendue + silhouettes
   + colonies clonales + pont + banc F5 `luxuriance` — INTACT.

## §REPRISE
**Conception FIGÉE (2026-07-04).** Doc `docs/conception/CONCEPTION_LUXURIANCE_STRATIFICATION.md`
écrit, kickoffs 01→06 écrits, prêt pour `/sprint-auto sprint_luxuriance_stratification`.
Exécuter les tronçons dans l'ordre (T1 socle couverture → T2 clonal → T3 empreinte
→ T4/T5 catalogue → T6 vue). Golden : RE-FIGÉ à T1 et T2 (annoncé), NEUTRE T3-T5,
INTACT T6. À la clôture : fermer D62 (absorbée), MAJ DETTE/BACKLOG/journal/mémoire.
