# Conception — reliquats des plantes en splats (S1 du style homogène)

> Conçue en `/conception` le 2026-11-25 avec Nico. Suite du sprint (a) plantes
> (`conception_precuisson_splats.md`, sprint `sprint_precuisson_splats`, clos côté code
> le 2026-11-25). Sprint : `sprints/rendu/splatting/sprint_reliquats_plantes/`.
> **Vue + outillage seulement : `data/code/` n'est jamais modifié, golden `bce813af…` intact.**

## 1. Pourquoi

Au retour F5 partiel du sprint (a), Nico a trouvé les splats « beaux, globalement
positif », mais le style n'est pas homogène :
- à ×32, les grandes plantes reviennent à l'ancien dessin ;
- des organes restent dessinés (feuilles du trèfle, masses du buisson…) ;
- les pièces sont trop grandes chez certaines espèces ;
- les détails fins des feuilles (duvet, nervures, gouttes…) disparaissent dès que la feuille devient une pièce ;
- une douzaine de portraits sont ratés.

Nico ne fera son F5 complet qu'une fois le style homogène partout (mémoire
`feedback_f5_splats_differe`).

## 2. Séquence de trois sprints (décision E1)

| Sprint | Contenu | Conception |
|---|---|---|
| **S1 `sprint_reliquats_plantes`** | ×32, tailles, détails cuits, recettes manquantes, portraits non-arbres, revue | **ce document** |
| S2 arbres | arborescence **rendue** lissée (aucun angle abrupt, fourches arrondies), écorce cuite en splats par essence et plaquée le long du tube, brins et rubans des graminées (même technique), portraits d'arbres (sapin, bouleau, cerisier, figuier), masses ×4 des arbres | `/conception` à venir |
| S3 lisière + chargement | (b) kit du décor et arbres de lisière en splats (sur le bois de S2), puis (g) écran de chargement : filament de **mycélium qui s'arborise en splats et sert de barre de progression**, puis liste F5 exhaustive pour Nico | `/conception` à venir |

Pas de F5 entre les sprints. Des sprints séparés plutôt qu'un seul : le contexte de
l'orchestrateur reste court, et les arbres demandent leur propre conception, que la
lisière consomme.

## 3. Décisions

- **E4 S2 = rendu seul** : la forme produite par le moteur (`sim/growth.py`) ne change pas.
- **E5 Précuisson maximale** : on préfère cuire (variantes, tailles, couches) plutôt que dessiner, quitte à étaler le travail sur plusieurs sprints.
- **E6 Budget mémoire de précuisson : 1 Go** (images cuites des plantes et planches splat chargées).
- **E7 ×32** : on relève les plafonds de cuisson par plante sous ce budget global, avec éviction. On ne dessine pas de codes en direct.
- **E8 Trois classes de taille précuites par recette**, et l'échelle √2 des organes ronds est corrigée.
- **E9 Les brins et rubans des graminées passent en S2.**
- **E10 « Tous les détails des feuilles présents quand on zoome, beau à chaque palier »** : chaque détail vectoriel est cuit en couche, visible dès le palier où il se lit.
- **×64** : hors de S1. Une sonde de mesure est prévue au ③. Un **proof of concept sur une plante entière (chanvre) à ×64**, avec mesure du coût, vient **après S1-S3** (au BACKLOG). Le palier ×64 n'a de sens que lorsque le sol, la faune, le paillage, etc. seront eux aussi cuits par palier (familles c-e du programme D7).

## 4. Constat ×32 (vérifié par capture VM le 2026-11-25)

Banc `planche_especes`, `-z 32 -w 0`, n=1 image par cas :
- **tomate** : pièces splat présentes (`feuille_composee_x32` chargée) ;
- **tournesol** : aucune ligne `[Splats]` ni `[Cuisson]` au journal, feuille vectorielle plate à l'écran.

Cause :
- `PlantBaker.Begin` renonce (une pose dépasse `MaxSidePx` 2048, ou l'atlas dépasse `MaxAtlasPx` 4096, `visuals/PlantBaker.cs:114,120`).
- La plante passe alors en dessin direct, donc `Indexe` est faux, donc `SplatsIci` est faux (`PlantRenderer.Splats.cs:59`).
- Les pièces sont des CODES de palette : elles ne s'affichent qu'au travers de `PaletteIndexee.Materiau`, que seule une image cuite porte (`PlantRenderer.Bake.cs:151`).

## 5. Les six tronçons

1. **Mémoire et ×32** : budget global de 1 Go, plafonds par plante relevés (limite GPU de 16 384 px), éviction hors champ ; mesures sur un tournesol ×32 et un arbre ×16/×32.
2. **Classes de taille** : 3 classes par recette, calées sur les tailles réelles des fiches de la vue ; la vue choisit la classe la plus proche ; correction du √2 ; recuisson complète, poids mesuré.
3. **Détails cuits** : inventaire au grep de tout détail vectoriel posé sur les feuilles et organes, puis chacun devient une COUCHE cuite (palette propre), posée dès son palier de lisibilité. Fin du tronçon : sonde ×64.
4. **Recettes neuves** :
   - trèfle à 3 folioles, avec une variante rare à 4 (tirée au hash) ;
   - rameau de thym ;
   - lames de lavande ;
   - panicule fine de la fétuque ;
   - anthères du blé ;
   - cœur des fleurons aux petites tailles.
5. **Portraits non-arbres ratés**, recuits avec ②③④, plus les baies de la myrtille absentes de sa fiche de vue.
6. **Revue « beau à chaque palier »** : échelles ×0,5 → ×32 sur un échantillon d'espèces couvrant tous les ports et toutes les marques ; finitions ; section F5.

Ordre :
- ① d'abord : c'est un défaut, et le budget conditionne le reste.
- ② avant ③④ : on cuit une seule fois, directement dans les bonnes tailles.
- ⑤ après ④ : les portraits utilisent les recettes définitives.
- ⑥ : la revue finale.

## 6. Coût et garde-fous

- Recuisson complète au ② : au sprint (a), il fallait 49 min de mur pour les feuilles et 30 min pour les organes, pour UNE taille → ×3 [estimation]. Elle tourne en arrière-plan sur la VM ; vérifier la charge (`uptime`) avant de mesurer.
- Poids : `assets/splats/` 26 Mo → ~80 Mo [estimation] après ②, plus les couches au ③. **Alerte au-delà de 200 Mo** (D2 : images versionnées dans git).
- Déterminisme : deux cuissons donnent les mêmes octets (acquis au sprint (a)).
- Interdits : `test_epaisseur_500ans` ; DeepSeek dans les sous-agents ; modifier `data/code/` ; modifier les sources copiées d'ink-studio (`tools/splat/vendor/`).
- Interrupteur conservé : Maj+F11 ou `SYMBIOSE_SPLATS=0` → l'ancien dessin, intact derrière chaque crochet.
