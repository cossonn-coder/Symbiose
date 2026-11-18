# CONCEPTION — La plante vivante : un bilan, pas des points de vie

> Figé le 2026-11-18 (`/conception`, D140 G). Remplace la **vitalité-jauge** de
> `conception_sante_resilience.md` (D75) par un **bilan carbone** : la plante vit de
> ce qu'elle produit, puise dans ses réserves quand elle produit moins qu'elle ne
> dépense, et meurt quand elles sont vides ou que ses organes vitaux sont détruits.
> Deux sprints : `sprints/vegetal/sante/sprint_plante_vivante/` (A, socle +
> herbivorie + souches + ouverture + vue) puis
> `sprints/vegetal/sante/sprint_stress_au_bilan/` (B, chaque stress à son vrai
> mécanisme). Débloque `sprints/vegetal/genetique/sprint_depart_jardin/` (④→⑥).

## 0. Motivation (mesures du 2026-11-18, monde `full`, seed 42, n=1 par cas)

Ouverture du monde `full` en semaine 10 : 121 des 136 plantes posées meurent
« d'herbivorie » avant la semaine 21, chênes de 25 ans compris.

| Essai (ouverture s10) | Morts posées à s21 |
|---|---|
| tel quel | 121/136 |
| faune pré-roulée s1→s9 (ravageurs + prédateurs) | 130/136 |
| prédateurs seuls pré-roulés | 97/136 |
| `stress_memory` amorcée à 0,12 | 49/136 |

- Les prédateurs existent et régulent (ravageurs à s14 ≈ jardin parti en s1).
- La règle de dégât est la cause : `herbivory_pressure` lit le ravageur du
  plot-foyer, et au-delà d'un seuil (ravageur ≈ 0,075, sous l'équilibre normal
  0,10-0,14) retire **1/3 de vitalité par semaine, même coup pour un semis et un
  chêne**. Seul rempart : une porte sur `stress_memory`. La limace « mange » la cime.
- Semis de chêne (D140 g2) : cascade de **rejets de souche** — un rejet qui meurt
  devient une souche neuve qui rejette à son tour (9 → 27 → 75 → 153 chênes par
  vague, tous à < 1,5 m d'un arbre mort, s20-s32).
- Chronique (g1) : « chêne, 5 sem d'âge » = `age_weeks`, qui compte les semaines
  **dans le stade courant** (remis à 0 par `advance_stage`) — l'âge vrai est `age_years`.

Décisions de Nico : la règle est aberrante ; **les plantes n'ont pas de PV**, elles
vivent d'un bilan (nutriments du sol, échange avec les champignons, photosynthèse ;
eau, lumière, chaleur dans une plage par espèce) ; tout le vivant végétal passe au
bilan ; `vitalite` devient une lecture ; plus de mort tirée au sort.

## 1. Le bilan hebdomadaire

**Unité : la semaine d'entretien** de la plante (ce qu'elle respire pour rester en
vie à 15 °C, actif). Aucune biomasse absolue : tout flux s'exprime relativement à
l'entretien de la plante elle-même, ce qui rend un chêne et un radis comparables.

Deux états neufs par plante :
- `feuillage` ∈ [0,1] — part **intacte** du feuillage attendu à ce moment de sa vie
  (un caduc en hiver a 1,0 : rien ne manque). Les feuilles mangées, gelées, malades
  le font baisser ; la refeuillaison le remonte.
- `reserves` ∈ [0,1] — fraction de la **capacité de réserve** `C` (en semaines
  d'entretien). `C = reserve_semaines(espèce) × facteur_stade` (plantule ≪ adulte).
  Défaut 1,0 à la naissance (la graine apporte ses réserves, l'albumen) et à la pose.

Chaque semaine :

```
P   = photo_max × feuillage × présence_phéno × f_lum × f_eau × f_T × f_nut × f_allelo
E   = entretien(T) = Q10^((T − 15)/10) × (DORMANCE si dormante)        # Q10 = 2
X   = part racinaire (exsudats + paiement mycorhizien) = K_EXSUD × P × mycorhization
net = P − E − X                                     # en semaines d'entretien
```

- `net ≥ 0` : remplit d'abord les réserves (`reserves += net / C`, plafond 1), puis
  le **surplus** alloue la croissance (cible du `growth_factor`, avancement de stade).
- `net < 0` : la plante puise (`reserves += net / C`).
- Refeuillaison : si `feuillage < 1` et en saison de végétation, la plante refait
  jusqu'à `REFEUIL_MAX`·`repousse` de feuillage par semaine, payé
  `cout_feuillage × Δfeuillage / C` en réserves (pas de refeuillaison à réserves vides).

Facteurs (tous ∈ [0,1], **réutilisent l'existant**, aucun doublon) :
- `f_lum` : lumière reçue (`eco.lumiere.light_received`) × tolérance d'ombre
  (`shade_tolerance_base` × gène `tolerance_ombre`), saturante — même lecture que
  l'actuel `light_eff` de `_update_physiology`.
- `f_eau` : eau perçue (`eau_percue`) vs seuils `0,15/tolerance_secheresse` et
  `HUM_NOYE` — même lecture que `ok_hum`, en rampe au lieu d'un booléen.
- `f_T` : rampe sur la plage thermique D139 (`temp_min_growth` → optimum →
  `lim_chaud` via `t_feuille`) — en rampe au lieu de `ok_temp`/`trop_chaud`.
- `f_nut` = `facteur_nutrition` (Liebig, D120) ; `f_allelo` = `_f_croissance_allelo`.

## 2. Paramètres d'espèce

Trois **neufs**, data-driven, défauts par forme de vie (strate du stade mature +
`life_cycle` + `winter_strategy`) surchargés par espèce dans un module unique
`plants/physiologie.py` :

| Paramètre | Sens | Ordres de grandeur (défauts) |
|---|---|---|
| `reserve_semaines` | capacité de réserve à l'âge adulte | arbre 40, arbuste 20, vivace à racine charnue (consoude, pissenlit, ail) 15, vivace 8, bisannuelle 6, annuelle 3 |
| `photo_max` | production à plein régime / entretien | annuelle héliophile 4, vivace 3, arbre 2,5, sciaphile 2 |
| `cout_feuillage` | coût d'un feuillage complet (semaines d'entretien) | caduc 6, persistant 10, herbacée 2 |

Réutilisés : plage thermique D139, `shade_tolerance_base`, `tolerance_secheresse`,
`tolerance_asphyxie`, gènes `coriacite_feuille`, `appetence_feuille`, `parfum`,
`mycorhization`, `repousse`, `resilience_base` (D75 : divise désormais une **perte de
tissus**, plus une perte de vitalité).

## 3. Vitalité = lecture

`vitalite = min(1, reserves / R_CONFORT) × (0,5 + 0,5 × feuillage)`, `R_CONFORT = 0,5`.
Un chêne défeuillé à réserves pleines lit 0,5 (« malade » à l'œil : il est nu) mais
vit ; il meurt seulement à `reserves = 0`. `is_alive`, `etat`, la sémiologie, le
rendu et l'info-bulle continuent de lire `vitalite`. Toute écriture directe
`vitalite = 0` (geste, greffe, régression) = **destruction** → `reserves = 0`.

## 4. Les dégâts retirent ce qu'ils retirent vraiment

- **Adaptateur universel (sprint A)** : `erode(a)` = perte de **tissus** :
  `feuillage −= a / resilience_base` ; un coup ≥ toute la vitalité restante
  (fonte des semis) = destruction. La plante meurt ensuite **par le bilan** si elle
  ne peut pas refaire ses feuilles. Ce n'est qu'une étape : le sprint B donne à
  chaque stress son vrai mécanisme.
- **Herbivorie par atteinte (sprint A)** — chaque ravageur ne mange que ce qu'il
  atteint ; la consommation d'un plot se partage entre les feuillages présents :
  - limace : feuillage **bas** (part du feuillage sous `LIMACE_HAUTEUR_CM ≈ 40 cm`) ;
  - puceron : pousses tendres de toute plante, en saison de croissance → **vole des
    sucres** (retire au bilan), défolie peu ;
  - doryphore : solanacées seulement ;
  - chenille (larve) : feuillage, comme aujourd'hui.
  Perte de feuillage = `K_HERB × moyenne sur les plots foliaires de la plante de
  (densité atteignante × part de la plante dans le feuillage du plot)` × parfum ×
  appétence / coriacité. Un arbre aux dizaines de plots ne perd presque rien ; un
  semis seul sur un plot à limaces peut tout perdre. La porte `stress_memory` est
  retirée de l'herbivorie ; la bascule létale « foyer non régulé sur sol mort » double
  la consommation (la population n'est pas régulée).

## 5. Causes de mort

| Cause | Mécanisme | Sprint |
|---|---|---|
| Famine carbonée | `reserves = 0` (ombre, défoliation répétée, pucerons, sécheresse longue) | A |
| Destruction | coup total, sève gelée (sous `lim_gel`), fonte au collet, annélation, chablis, arrachage | A (adaptateur), B (vrais mécanismes) |
| Défaillance hydraulique | `embolie` ∈ [0,1] : sécheresse extrême, gel-dégel des ligneux ; ne se répare que par du bois neuf ; ≥ seuil = mort | B |
| Racines perdues | asphyxie, pourriture, campagnol → eau et nutriments perçus en baisse → famine/soif | B |
| Fin de cycle | annuelle/bisannuelle : remobilise tout vers ses graines, puis meurt | B (A garde l'existant) |
| Vieillesse | `photo_max` décline et l'entretien croît après l'onset → famine émergente | B (A garde l'existant) |

Supprimés : `background_mortality` (sort), la convalescence au sort (`heal`) — remplacée
par la refeuillaison payée — et `shade_stress_damage` (l'ombre tue par famine). Le
code supplanté est **commenté et conservé** (patron « SUPPLANTÉ — conservé pour
mémoire »), jamais supprimé.

## 6. Souches et rejets

À la mort d'un ligneux à souche vivante, la souche garde une **réserve**
(`reserve_souche` = ses réserves au moment de la mort × `C`). Une vague de rejets
coûte de la réserve ; **un rejet n'a pas de souche propre** tant qu'il n'est pas
établi (âge < `AGE_SOUCHE_PROPRE`) : s'il meurt, il ne rejette pas. Critère : au plus
`N_REJETS_MAX` (4) rejets au total par arbre mort.

## 7. Ouverture du monde `full`

Les plantes posées naissent à réserves et feuillage pleins (défaut). Critère
d'acceptation (Nico, 2026-11-18), monde `full`, seed 42, semaines 10 → 30 :
- **aucun arbre posé mort** la première année ;
- **≤ 25 % des herbacées posées mortes** hors fin de cycle ;
- **≤ 4 rejets par arbre mort**, au total.
La chronique affiche l'âge vrai (`age_years`), pas `age_weeks`.

## 8. Coût perf

Un calcul scalaire par plante et par semaine + l'herbivorie sur les plots foliaires
(déjà en cache). Estimé +3 à +6 % de tick [estimation, à mesurer au A⑤] ; budget
≤ +10 % par tronçon.

## 9. Philo

#1/#2 : aucun bonus/malus — les stress sont des flux (feuilles mangées, sucres volés,
eau manquante) et la mort est la réponse biologique. #3 : zéro RNG (la mort au sort
disparaît). #5 : ce qui se voit = feuillage, teinte, posture ; pas de jauge.
#6 : une plante fragile meurt, un chêne encaisse — l'apprentissage vient du milieu.
