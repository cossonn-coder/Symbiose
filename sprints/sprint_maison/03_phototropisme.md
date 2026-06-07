# Sprint Maison·3 — **Phototropisme branché** (apex se penche vers la lumière)

> **Kickoff autosuffisant.** Démarrage à froid. Lis ce fichier, puis
> `data/code/CONCEPTION_MAISON_OMBRE.md` (§4 phototropisme, §7 golden), puis les
> sources, puis exécute. Carte blanche (conception figée). **Français.** Rigueur
> **déterminisme + golden**. **Prérequis : tronçons 1 & 2 faits** (monde +
> maison + ombre dans le `LightField`).
>
> Tronçon **moyen, RISQUÉ** : modifie la croissance de **toutes** les plantes.
> Touche `sim/growth.py` (le phototropisme y est **stubé neutre**, ~ligne 24).
> Lancement depuis `data/code/`.

## Ce que c'est, en une phrase
On **débranche le stub neutre** du phototropisme : l'apex **biaise sa direction
horizontale vers le gradient de lumière local** (lu dans le `LightField`), de
façon **déterministe, bornée et d'intensité paramétrable**. La plante à l'ombre
ne fait plus que pousser moins : elle **se penche** vers le clair (course à la
lumière, étiolement).

## Principe directeur (à NE PAS contourner)
- **Déterministe, zéro RNG.** Le biais est une fonction du gradient de lumière
  (et du bruit déterministe existant `_hash_noise` pour le jitter latéral, déjà
  là). Pas de nouveau tirage aléatoire.
- **Borné** : un angle d'inclinaison **max par tick** ; l'apex **ne se couche
  jamais à plat**. La verticalité reste l'attracteur par défaut (gravitropisme
  implicite) ; la lumière la **dévie**.
- **Intensité paramétrable** : attribut `phototropism_strength` (sur `PlantBase`,
  défaut **marqué** — décision Q3). Le sous-sprint **rend subtil ET marqué** dans
  la maquette (tronçon 4 consommera ça) → **Nico tranche la valeur finale à
  l'œil**. Donc : rends le paramètre propre, pas une constante en dur.
- **Source du gradient** : échantillonner `LightField.at_plot` dans quelques
  directions autour de l'apex (ou suivre le gradient discret). Coût négligeable
  devant le `LightField` (§5).
- **Risque golden (§7)** : ça change **toutes** les plantes. En lumière ~uniforme
  le biais doit être **≈ 0** (sinon dérive partout). Vérifier que l'apex en plein
  champ reste ~droit.

## Sources à lire (dans l'ordre)
1. `data/code/CONCEPTION_MAISON_OMBRE.md` §4 (phototropisme), §7 (golden).
2. `sim/growth.py` — **le stub neutre ~ligne 24-25** (« apex droit, jitter
   latéral »), `grow_plant`, `_debourrement` (utilise `branch_angle` + jitter),
   `_elongate_emit`. C'est ici qu'on branche.
3. `plants/base.py` — `PlantBase` (où poser `phototropism_strength` + défaut).
4. `fields/light.py` — `at_plot`, repère sol (x=Est, y=Sud).
5. `sim/engine.py` — ordre d'appel (`grow_plant` après physiologie ; le
   `LightField` du tick est-il disponible au moment de la croissance ? threader
   si besoin, en LECTURE seule).

## Plan suggéré (révisable)
1. `phototropism_strength` sur `PlantBase` (défaut marqué), mirroir module si
   besoin (cf. patron `emit_length_cm`/`max_segments` déjà fait en croissance).
2. Fonction `_phototropic_bias(apex, light_field, origin)` → vecteur de déviation
   horizontale borné, ∝ gradient × strength. Zéro RNG.
3. Brancher dans l'allongement/émission d'apex (remplacer le stub neutre).
   S'assurer que `bias ≈ 0` quand la lumière est uniforme.
4. `tests/test_phototropisme.py` (§7) : apex sous gradient se penche vers le
   clair ; apex en lumière uniforme reste ~droit ; angle borné ; déterminisme.

## Critères de succès (vérifier AVANT de clore)
- [ ] Sous un gradient (ex. ombre de maison d'un côté), l'apex **se penche vers le
      clair** de façon visible.
- [ ] En lumière **uniforme**, l'apex reste **~droit** (biais ≈ 0).
- [ ] Inclinaison **bornée** (jamais à plat), **déterministe** (2× = identique).
- [ ] `phototropism_strength` **paramétrable** : 2 valeurs (subtil/marqué)
      produisent 2 allures distinctes (le tronçon 4 les rendra côte à côte).
- [ ] **Golden re-figé maîtrisé** : documenter le nouveau hash + vérifier que la
      dérive est cohérente (pas d'emballement). Suite complète verte.
- [ ] `00_etat.md` mis à jour (tronçon 3 ✅, hash, valeurs subtil/marqué retenues
      pour la maquette).

## Pièges connus
- Si le biais n'est pas nul en lumière uniforme, **tout** le golden dérive sans
  raison → bug. Tester ce cas en premier.
- Le `LightField` du tick doit être prêt **avant** `grow_plant` (vérifier l'ordre
  dans l'engine ; sinon utiliser le champ du tick précédent, en le documentant).
- Garder l'inclinaison dans le **plan horizontal** + composante verticale gérée
  comme avant (ne pas casser la montée en hauteur dérivée de l'empreinte).
