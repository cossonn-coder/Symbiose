# Conception — Allélopathie racinaire (SYMBIOSE)

> **Document de conception FIGÉ (2026-07-13).** Spec de référence du sprint
> d'implémentation (MOTEUR + vue). Découpe = **6 tronçons** (§L). Kickoffs :
> `sprints/vegetal/allelopathie/sprint_allelopathie/0N_*.md`. Carnet d'état : `00_etat.md`.
> Origine : sujet choisi par Nico le 2026-07-13 (parmi allélopathie / zoochorie /
> climat pluriannuel / épidémie spatiale). Comble le trou pointé par le TODO
> `plants/base/familles.py:440` (« faute d'action moteur qui injecte du NÉGATIF
> dans le champ, on triche avec un adjacency_bonus »).

---

## 0. Constat & périmètre

L'**allélopathie** = interférence chimique entre plantes. Une plante libère par ses
racines (exsudats) des composés qui **inhibent** la germination et la croissance des
voisines. Aujourd'hui le concept n'existe qu'en **narration** (blurbs encyclopédie) ;
aucune mécanique. Pourtant la plomberie est là :

- `family_effects` data-driven (`plants/base/familles.py`) sait déjà **injecter dans
  un champ de sol au voisinage** : l'ortie fait `inject_field variable="n"
  amount=+0.03 cible="local"`. L'allélopathie = injecter dans un champ NÉGATIF pour
  la levée/croissance des voisines.
- ~20 champs de sol (`fields/ecofields/container.py`) : un champ neuf `allelopathie`
  s'insère comme `microbiome`/`ph`.
- Germination : `fields/seedbank.py` (`niche_index`, `germination_candidates`) +
  `sim/succession.py` = point d'insertion NATUREL de l'inhibition.
- `microbiome`/`mycelium` : un sol vivant **détoxifie** → décroissance modulée =
  interconnexion (règle « tout coexiste »).

**Garde-fous** : **philo #2** (jamais de malus direct sur la plante — tout passe par
le champ : flux exsudat → contrainte champ → réponse émergente) ; **#3** déterminisme ;
**#5** indices visuels ; **#7** hétérogénéité. Re-figeage golden **maîtrisé et
annoncé**, isolé par tronçon.

---

## A. Champ `allelopathie` & injection — FIGÉ

### A.1 État moteur
- Nouveau `GridField` **`allelopathie`** dans `EcoFields` (`container.py`), `max_val`
  borné (ex. 3.0 comme n/p/k), `initial=0.0`. Concentration d'allélochimiques par
  plot.
- **Champ UNIQUE** (décision D4) : une seule concentration agrégée par plot, pas un
  dict par molécule. L'auto-tolérance et la sensibilité se gèrent à la **lecture**
  (§B/§C), pas par étiquetage du champ. L'autotoxicité par espèce (§D) trace
  l'identité **séparément** (soil_memory ne trace PAS l'espèce — mémoire de
  fertilité fast/deep, vérifié `sol.py`).

### A.2 Injection (émetteurs)
- Nouvelle **action `family_effects`** `inject_allelopathie` (ou réutilise
  `inject_field` avec `variable="allelopathie"` — à trancher à l'impl., préférence :
  réutiliser `inject_field` pour ne pas dupliquer le routeur d'effets).
- Un émetteur dépose `amount` (par espèce, placeholder) dans `allelopathie` sur son
  **empreinte racinaire** (`cible="local"`, rayon racinaire déjà dérivé → scatter
  borné, pas de balayage O(N²)).
- Trait espèce **`allelopathie_emission: float = 0.0`** (défaut = non-émetteur,
  neutre). Renseigné au §E.

### A.3 Décroissance (labile, modulée microbiome)
- Chaque tick : `allelopathie[r,c] *= (1 − DECAY_BASE − DECAY_MICROBE ·
  microbiome[r,c])` (borné ≥ 0, snap à 0 sous un plancher). Sol vivant → décroissance
  plus rapide (détoxification). Régime **labile** par défaut ; l'accumulation
  autotoxique est le mode §D (traceur séparé), pas ce champ.
- Le mycélium peut renforcer la détox (option §D/§E, interconnexion).

### A.4 Golden
Ajout d'un champ neutre + injection + décroissance, **lu par personne à ce tronçon**
→ **golden NEUTRE visé** (à confirmer ①). Émetteurs pas encore dotés du trait (§E).

---

## B. Lecture à la GERMINATION — FIGÉ

**Décision D1 (part 1) + D2 + D6.**

### B.1 Inhibition de la niche
- `niche_index` (ou `germination_candidates`) **escompte** la niche d'un candidat par
  un facteur `f_allelo(conc, sensibilité) ∈ [0,1]` : forte concentration + forte
  sensibilité → niche se referme → pas de levée. **Rampe douce continue** (D6), pas
  de seuil dur : `f_allelo = 1 − SENS_esp · rampe(allelopathie[r,c])` (rampe
  saturante type Monod/`x/(x+K)`), borné [0,1].

### B.2 Sélectivité (D2)
- Trait espèce **`allelopathie_sensibilite: float = 1.0`** (défaut : sensible
  standard ; 0 = insensible/tolérant). Une graine tolérante lève malgré le champ.
- **Auto-tolérance** : l'émetteur ne s'inhibe pas lui-même. Mécanisme = l'émetteur
  a une `allelopathie_sensibilite` faible/nulle à sa propre molécule ; comme le champ
  est unique, on approxime par **auto-exclusion** (une graine de l'espèce émettrice
  E ignore la fraction du champ qu'elle-même produirait) OU plus simplement
  `sensibilite` propre basse. Trancher à l'impl. (préférence : sensibilité propre
  basse, plus simple, champ unique préservé).

### B.3 Golden
Probable **NEUTRE** sur le smoke (peu d'émetteurs matures : noyer maturity 5 > 2 ans ;
adventices non émettrices par défaut). À confirmer ②. Invariant : `allelopathie=0`
partout ⇒ `f_allelo=1` ⇒ germination **strictement inchangée**.

---

## C. Escompte CROISSANCE / vigueur — FIGÉ

**Décision D1 (part 2).**

### C.1 Effet sur les plantes établies
- Une plante déjà levée, sur un plot chargé en `allelopathie` et **sensible**, subit
  un **escompte de croissance/vigueur** : facteur multiplicatif borné appliqué là où
  la croissance lit déjà les contraintes de milieu (pas un décrément direct de santé
  — philo #2 ; l'escompte réduit le gain, l'écosystème fait le reste).
- `f_croissance = 1 − ESC_MAX · SENS_esp · rampe(allelopathie_racinaire)`, où
  `allelopathie_racinaire` = concentration moyenne sur les plots explorés par les
  racines (empreinte racinaire, comme l'uptake). Borné.

### C.2 Interconnexion
Une plante affaiblie chimiquement devient plus vulnérable au reste (ombre,
ravageurs, sécheresse) → dépérissement émergent, jamais scripté. Relie
allélopathie ↔ vigueur ↔ santé continue (`vitalite`, sprint D75).

### C.3 Golden
Re-figeage **à évaluer** ③ : si un émetteur mature charge le champ près d'une plante
sensible du smoke. Invariant : `allelopathie=0` ⇒ `f_croissance=1` ⇒ inchangé.
Isoler ; si dérive, annoncer.

---

## D. AUTOTOXICITÉ / fatigue du sol — FIGÉ (tronçon isolé)

**Décision D3 + D4.** La pépite pédagogique permaculture : une monoculture répétée
s'empoisonne.

### D.1 Traceur d'espèce récurrente
- `soil_memory` ne trace pas l'espèce → **traceur léger neuf** : par plot, l'identité
  (clé espèce/famille) de l'occupant récurrent + un compteur/accumulateur
  `autotox[r,c]` qui **monte** quand la même espèce émettrice occupe le plot saison
  après saison, et **redescend** à la rotation (autre espèce) ou en sol nu.
  Implémentation légère (un champ `autotox` + une clé d'espèce par plot, ou un petit
  dict). À dimensionner au tronçon ④ (garde-fou RAM).

### D.2 Effet
- `autotox` **alimente `allelopathie`** (ou un terme additionnel lu par B/C) pour la
  **même espèce** : la graine/plante de l'espèce fatigante voit sa niche/croissance
  escomptée sur ce plot. Rotation ⇒ `autotox` retombe ⇒ le sol « se repose ».
- Le microbiome/mycélium accélère la résorption (détox, cohérent §A.3).

### D.3 Golden
**RE-FIGÉ MAÎTRISÉ annoncé** : le smoke porte des successions/monocultures locales
→ l'autotox peut modifier la levée sur plots ré-occupés. **Invariant** : à
`autotox=0` partout (rotation parfaite / traceur neutralisé), germination et
croissance **strictement identiques** au pré-④ → toute dérive est attribuable au
seul traceur d'autotoxicité. Isoler, mesurer, annoncer le nouveau golden.

---

## E. Espèces émettrices & voix narratives — FIGÉ

**Décision D5.** Le catalogue grandit avec l'idée ; toute plante ajoutée reçoit ses
5 voix (règle projet).

### E.1 Traits sur espèces EXISTANTES (data pur)
- **Noyer** (`WalnutTree`/Juglans, `perennials.py`) : `allelopathie_emission` FORT
  (juglone), auto-tolérant. Emblème.
- **Tournesol** (`Sunflower`, `cultivees.py`) : émission MODÉRÉE.
- **Aromatiques (Lamiaceae) / aulx (Amaryllidaceae)** : émission LÉGÈRE — **résout le
  TODO `familles.py:440`** (remplace la triche `adjacency_bonus` par une vraie
  injection négative). Migration douce : conserver l'effet répulsif existant OU le
  reformuler en émission allélopathique (trancher à l'impl., surgical).

### E.2 Espèces NEUVES (avec 5 voix chacune)
- **Armoise** (Artemisia, Asteraceae) : vivace inhibitrice **puissante** — fait le
  vide autour d'elle. Facette « vivace toxique ».
- **Seigle** (Secale, Poaceae) : annuel, **engrais vert allélopathique** — couvert
  qui étouffe chimiquement les adventices puis se fauche. Facette « couvert
  stratégique permaculture » (geste joueur : semer un couvert nettoyant).
- Pour chacune : encyclopédie (fiche 3 niveaux), carnet (concept `allelopathie` /
  cause), pages secrètes (lore optionnel), magazine (famille/offre), événements
  (marqueurs de cycle) — cf. `docs/narration/voix/conception_voix_narratives.md`.

### E.3 Sensibilités
- Renseigner `allelopathie_sensibilite` sur quelques espèces cibles marquantes
  (ex. tomate très sensible à la juglone ; graminées tolérantes) pour rendre la
  stratégie lisible. Défaut 1.0 ailleurs.

### E.4 Golden
Data pur (traits + espèces absentes du smoke sauf noyer/tournesol déjà présents mais
non matures) → **golden NEUTRE visé** ⑤. Si un émetteur déjà au smoke gagne le trait
et charge le champ, mesurer.

---

## F. Vue Godot — FIGÉ

**Règle projet : tout sprint finit par son tronçon vue, golden intact.**
- **Overlay debug F6** : le champ `allelopathie` rendu en heatmap (`FieldOverlay.cs`,
  comme les autres champs) — zone d'inhibition visible en mode technique.
- **Indices diégétiques** (philo #5, pas de chiffres) : sol nu/pelé sous un émetteur
  fort (halo de terre sans levée autour du noyer/armoise), graines qui ne lèvent pas.
  Le rendu réutilise la sémiologie existante ; profondeur laissée au F5.
- Pont : exposer `allelopathie` au snapshot par tuile (liste creuse des foyers > 0,
  comme `alarme`). Golden **intact** (aucune ligne moteur touchée).

---

## L. Découpe en sous-sprints

1. **① Champ + injection + décroissance** (A) : `GridField allelopathie`, trait
   `allelopathie_emission`, `inject_field`/action, décroissance modulée microbiome.
   Lu par personne → **golden NEUTRE visé**.
2. **② Lecture germination** (B) : `niche_index`/`succession` escomptent la niche
   (rampe douce), trait `allelopathie_sensibilite`, auto-tolérance. **Golden probable
   neutre** (à confirmer, invariant champ=0).
3. **③ Escompte croissance/vigueur** (C) : facteur borné sur la croissance des
   établies. **Re-figeage à évaluer**, isolé.
4. **④ Autotoxicité / fatigue du sol** (D) : traceur d'espèce récurrente + `autotox`
   → alimente l'inhibition de la même espèce. **Golden RE-FIGÉ MAÎTRISÉ annoncé**
   (invariant : autotox=0 ⇒ identique au pré-④).
5. **⑤ Espèces émettrices + voix** (E) : traits sur noyer/tournesol/aromatiques/aulx
   + ajout **armoise** & **seigle** avec leurs **5 voix**. **Golden neutre visé**.
6. **⑥ Vue Godot** (F) : overlay F6 `allelopathie` + indices diégétiques + pont
   snapshot. **Golden intact.**

Ordre ①→⑥ (neutre d'abord, re-figeage isolé au ④). Chaque tronçon préserve le
golden OU le re-fige de façon annoncée et isolée.

## M. Invariants transverses
Déterminisme (`seed`/`_hash_noise`, jamais de RNG vivant) ; **philo #2** (aucun
malus direct sur la plante — flux exsudat → champ → réponse émergente) ; couches
`plants ← fields ← sim` ; interconnexion (allélopathie ↔ microbiome/mycélium ↔
germination ↔ croissance ↔ vigueur/santé ↔ rotation) ; re-figeages annoncés/isolés ;
garde-fou taille (~300 l code pur, scinder si dépassement — `container.py`/
`population.py` déjà signalés proches du seuil).
