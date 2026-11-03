# Conception : le trèfle dominant (D126), une prairie qui bouge

Figée le 2026-11-02, accord de Nico (« on va suivre tous tes conseils »). Sprint : `sprints/vegetal/catalogue/sprint_trefle_dominant/`.

## 1. Constat

Mesures `full`, seed 42, automate curatif, 5 ans, VM, n=1 graine par variante :

| Variante | Plantes an 5 | Trèfle | Espèces an 5 |
|---|---|---|---|
| Référence | 729 | 434, sur 274 plots sur 1 188 | 15 |
| `reproduction_rate` 0,35 → 0,08 | 723 | 419 | 15 |
| Sans stolons | 365 | 2 | 15 |

Le trèfle n'exclut pas les autres espèces sur 5 ans. Trois causes :

1. `WEED_CATALOGUE` ne compte que 5 espèces spontanées. C'est le plafond de diversité.
2. Un ramet ne passe que couverture < 0,85 et lumière ≥ 0,30 (`sim/clonal.py`) ; une graine passe `niche` × `GERM_PRESSION_FERALE` 0,30.
3. Rien ne le fait reculer : fixation constante par pied (+0,03 N/sem., `Fabaceae.family_effects`), et aucune plante ne profite assez de cet azote pour l'ombrer.

## 2. Écologie retenue

- Fixation freinée sur sol riche en azote : forte baisse de nodulation et de fixation chez le trèfle blanc à nitrate élevé.
- Oscillations trèfle-graminées pilotées par l'azote du sol, période d'environ 2 ans dans un modèle ; à l'échelle des taches, elles s'amortissent sur le champ.
- Stolons renouvelés : les vieux segments meurent pendant que les nouveaux avancent.

## 3. Conception

Aucun plafond sur le trèfle (philo #2 ; D71 reste dormante). La boucle attendue : trèfle → azote du sol → fixation freinée et graminées nitrophiles → ombre → stolons bloqués par la porte de lumière existante → vieux pieds qui meurent → sol qui s'appauvrit → trèfle qui revient.

- **Fixation** : proportionnelle au manque d'azote du plot, pour toute `Fabaceae`.
- **Renouvellement** : le pied de trèfle a une longévité courte ; la colonie se déplace.
- **Flore spontanée** : `dactyle` et `fétuque rouge` (neuves) avec le pâturin, `plantain lancéolé` (neuf) et `ortie` (existante) avec le pissenlit. Les archétypes et leur banque de graines ne changent pas. Une fois l'archétype choisi, l'espèce se décide par l'azote du plot puis par hash : dactyle et ortie sur sol riche. Chaque neuve reçoit ses 5 voix.
- **Trèfle à quatre feuilles** (demande de Nico) : fonction pure du pied, rare, déterministe. Le récolter rend toute la Vigueur du joueur, une fois par pied, ouvre la prochaine page secrète due et écrit au carnet. Bonus au joueur, jamais à la plante (philo #2). Rien en HUD : on le trouve en regardant (philo #5).
- **Vue** : tapis de feuilles à trois folioles, trèfle à quatre lisible de près, formes des trois neuves.

## 4. Coût et garde-fous

Budget : tick an 2 ≤ +10 % par tronçon. Le coût suit le nombre de plantes : moins de ramets attendus, mais des espèces en plus. Si le budget saute, réduire et le signaler.

## 5. Critères d'effet (`full`, seed 42, 5 ans)

- Part du trèfle en plantes sous 40 %, et elle varie d'une année à l'autre par tuile.
- Les taches se déplacent : plots à trèfle en an 5 différents de l'an 3 pour au moins un tiers.
- Au moins 18 espèces en an 5, dont les 4 ajoutées présentes.
- N moyen par tuile non effondré ni saturé.

## 6. Hors périmètre

Forme des autres plantes (D118). Faune (D119). Eau de neige et montée de l'humidité (D126, limites).

## Sources

- [Modèle spatial de légumineuses stolonifères et de graminées (Rothamsted)](https://repository.rothamsted.ac.uk/item/84zq8/a-spatially-explicit-population-model-of-stoloniferous-n-fixing-legumes-in-mixed-pasture-with-grass)
- [Fluctuations du trèfle blanc en prairie pâturée (Aberystwyth)](https://research.aber.ac.uk/en/publications/fluctuations-in-white-clover-content-of-sheep-grazed-swards/)
- [Revue sur le trèfle (Teagasc)](https://t-stor.teagasc.ie/server/api/core/bitstreams/1d3956a6-1e3f-42f2-9713-a5187bfc6f3c/content)
- [Azote et nodulation du trèfle blanc (Massey)](https://mro.massey.ac.nz/handle/10179/10211)
- [Nitrate et fixation chez le trèfle blanc (Aberystwyth)](https://research.aber.ac.uk/en/publications/relationships-between-nitrate-and-oxygen-supply-in-symbiotic-nitr/)
