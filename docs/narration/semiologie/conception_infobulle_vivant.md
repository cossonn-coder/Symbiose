# Conception — Info-bulle du vivant (D110 a·b·g)

> **FIGÉE le 2026-10-22** (`/conception`, arbitrages Nico). Sprint :
> `sprints/narration/semiologie/sprint_infobulle_vivant/` (3 tronçons, golden jamais re-figé).
> Prolonge la légende des signes du sprint PLANTE ASSEMBLÉE
> (`docs/rendu/pixelart/conception_plante_assemblee.md` §3 décision 4, §4.4).

## 1. Problème

Retour F5 du 2026-10-20 et arbitrages du 2026-10-21 :

- **(g) Info-bulle pessimiste** — « souvent négative, pas souvent : la plante est en bonne
  santé ». Cause vérifiée : `SigneDominant` (`world/WorldView.InfoBulle.cs`) retient le
  1er symptôme d'intensité **> 0**, alors que la teinte dessinée vaut intensité × 0,7
  (`PlantRenderer.SymptomTintMax`) puis passe par la palette 34 couleurs : une intensité
  faible ne change souvent **aucun pixel**. Le texte annonce ce que le dessin ne montre pas.
  Et sans signe, la ligne disparaît : aucune voix ne dit « saine ».
- **(a) Bête jamais nommée** — le nom exige `palier(espèce) ≥ carnet._seuil` (3), or rien
  ne crédite la faune au-delà du palier 1 (`encyclopedie._lire_mono`, `maitrise_detection`).
- **(b) Champignon muet** — la clé générique `champignon` n'a pas de `vu` dans le corpus.
- Nico : nommer animaux ET champignons comme les plantes, avec en très peu de mots ce
  qu'ils font + leur état.

## 2. Décisions (Nico, 2026-10-22)

1. **Nom révélé par observation répétée** : chaque survol d'une bête / d'un carpophore dans
   une **saison neuve** (indice absolu `année × 4 + saison`) crédite **+1 palier** à sa clé
   de maîtrise, **plafond 3** (= `SEUIL_CARNET`). Vue en 3 saisons distinctes → nommée (≈ un
   an pour la faune ; **3 automnes pour le champignon**, assumé : il ne fructifie qu'en
   automne). La règle CLAUDE.md « auxiliaires visibles dès le début, non identifiables sans
   maîtrise » est **conservée**. L'option « interprétatif anticipé » (seuil 1) nomme dès le
   1er survol, comme pour les signes.
2. **Affichage technique / debug** (Maj+F3, comme F6) : nomme tout dès le 1er survol, avec
   les chiffres (abondance, nourriture, densité, vitalité, intensités).
3. **État d'une bête = ce que les données disent déjà**, golden neutre : **abondance**
   (combien de bêtes de l'espèce on VOIT dans le plot) + **nourriture** (`activite` =
   ressource locale du sprite). **Pas de maladie animale** : elle n'existe pas au moteur,
   et un signe ne ment jamais par rapport à la simulation.
4. **Champignon = rôle lu sur place** : bois frais au plot (`eco.bois_fresh_at`) →
   « décompose le bois mort » ; sinon racines vivantes au plot → « relie les racines » ;
   sinon « lie l'humus ». État = densité du réseau (déjà au snapshot du carpophore).
5. **Seuil de visibilité mesuré, pas choisi** : un signe colorant n'est « visible » qu'à
   partir de l'intensité qui change réellement un pixel au rendu (mesure par capture VM) ;
   une marque fine (ravageurs/gel/grêle) qu'à partir de l'intensité qui dessine au moins
   une marque. Même règle pour le carnet : on n'observe que ce qui se voit.
6. **Voix « plante saine »** : sans signe visible, l'info-bulle décrit tout de même le
   feuillage — vert franc (vitalité haute), couleurs d'automne (phénophase `automne`), ou
   terne sans signe distinct (vitalité basse : honnête, sans inventer de cause). La
   sénescence reste dite comme un programme, pas un mal.

## 3. Ce que montre l'info-bulle

| Survol | Avant apprentissage | Appris | Technique (Maj+F3) |
|---|---|---|---|
| Plante sans signe visible | « feuillage ferme, d'un vert franc » / « prend ses couleurs d'automne » / « feuillage terne, sans signe distinct » | idem | vitalité, automne, symptômes bruts |
| Plante avec signe visible | `vu` du signe | `vu` — cause | cause + intensité |
| Bête | `vu` · abondance | **Nom** — rôle · abondance, nourriture | clé · abondance n · activite |
| Carpophore | `vu` champignon · réseau (dense / clairsemé) | **Champignon** — rôle local · réseau | clé · rôle · densité |

- **Abondance** (bête) : 1 = « seule », 2-3 = « quelques-unes », ≥ 4 = « nombreuses ». Le
  compte est celui que la vue affiche dans le plot (cap par plot = 4 au moteur).
- **Nourriture** (bête apprise) : 3 bandes « nourriture rare / suffisante / abondante »,
  bornes **mesurées** sur la distribution réelle de `activite` (quantiles d'un run
  témoin), pas devinées. Révélée seulement avec le nom : savoir que la coccinelle a de quoi
  manger suppose de savoir ce qu'elle mange.
- **Rôle** : ≤ 6 mots par espèce, voix naturaliste (« suce la sève des jeunes pousses »,
  « mange les pucerons »), corpus éditorial Python.

## 4. Modèle

### 4.1 Python (source de vérité, hors tick)
- **Corpus** (`sim/signes_corpus.py`, donnée pure) : `FAUNE_ROLE` (20 espèces),
  `CHAMPIGNON_VU`, `CHAMPIGNON_ROLE` (3 rôles), `VOIX_SAINE` (vert franc / automne / terne),
  libellés d'abondance, de nourriture et de réseau. La vue n'a **aucun texte en dur**.
- **Crédit par observation saisonnière** : au survol (`observer_espece`, faune et
  champignon seulement, jamais les plantes), si la saison absolue est neuve pour cette clé
  et que son palier < 3 → +1 palier (`maitrise.enregistrer_preuve` avec exactement
  `preuves_requises(palier)`). Mémoire « dernière saison créditée » par clé dans la tranche
  joueur de maîtrise (sérialisable, survit au save). Effet de bord assumé : Σ paliers ↑ →
  `palier_bonus` (Vigueur max) ↑ un peu — connaître la faune est un savoir.
- `appris` (`sim/signes.py`) inclut `champignon` ; l'encyclopédie faune/champignon reste
  une fiche mono-niveau (son commentaire « plafonnée à palier 1 » devient faux → corrigé).
- **Snapshot** : rôle local de chaque carpophore (code court) ; nourriture des butineurs si
  `ForagerLayer` n'en reçoit pas encore (à vérifier). Légende (`cmd_legende`) étendue au
  nouveau corpus. Pont bumpé.

### 4.2 Vue (lit, ne décide pas)
- `SigneDominant` : premier symptôme **visible au palier ET au-dessus du seuil mesuré**.
- Voix saine quand aucun signe ne passe.
- Lignes bête / carpophore selon le tableau §3 ; observation de la vie macro dédupliquée par
  **(clé, saison)** au lieu de « une fois par session » (sinon le crédit saisonnier n'arrive
  jamais après le 1er survol).

## 5. Philosophie
- #1/#2 : rien n'agit sur la simulation. #3 : golden intact, crédit = geste du joueur hors
  tick, dédup par saison déterministe. #5 : mots, pas de chiffres hors technique ; le texte
  ne dit que ce que le dessin montre. #6 : le nom se mérite en regardant au fil des saisons.
- Interconnexion : le rôle relie chaque bête / champignon à ce qu'il touche (proies, sève,
  bois, racines) ; l'état relie la bête à sa ressource dans le milieu.

## 6. Coût
Tick : **0**. Snapshot : rôle carpophore = quelques lectures par carpophore (automne
seulement, ≤ 3 par plot). Vue : recalcul au changement de survol seulement.

## 7. Tronçons
| # | Contenu | Golden |
|---|---|---|
| ① | Python : corpus, crédit saisonnier, `appris` champignon, snapshot (rôle carpophore, nourriture butineurs), légende, bandes de nourriture mesurées, pont bumpé | intact |
| ② | Vue plante : seuil de visibilité mesuré (capture VM) + voix saine + technique | intact |
| ③ | Vue faune/champignon : lignes nom/rôle/état, dédup (clé, saison), technique, bilan + F5 | intact |
