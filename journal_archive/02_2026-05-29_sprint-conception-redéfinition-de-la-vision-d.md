<!-- Archivé depuis journal.md le 2026-06-03 (Sprint refactor structurel) -->

## 2026-05-29 — Sprint conception : redéfinition de la vision du jeu

### Contexte

Session de challenge constructif à la demande de Nico — « pose-moi des
questions et challenge ma conception ». Format : 12 questions structurantes
posées par Claude, 12 réponses tranchées par Nico, sur la nature même du jeu.

Avant cette session, le `CLAUDE.md` décrivait Symbiose comme un
« roguelike écologique » avec runs, shop inter-run, extinction et reset.
Cette session a montré que **ce cadre n'était plus aligné** avec ce que
Nico imagine vraiment. Tout a été redéfini.

### Les 12 décisions structurantes

**1. Sandbox écologique évolutif, pas roguelike.**
Run éternel. Le mot « roguelike » et son vocabulaire dérivé (shop
inter-run, extinction = fin de run, héritage sol entre runs) sont
obsolètes. Le jardin est unique, persistant, et grandit avec le joueur.

**2. Vigueur unifiée — Mana propre + Qi = champs écologiques.**
Inspiration croisée Qi chinois (énergie circulante) et Mana polynésien
(énergie propre à chaque être). Modèle minimaliste : pas de nouveau
GridField pour le Qi, les champs existants (`microbiome`, `soil_memory`,
`om_*`, `fertilite`) modélisent déjà le territoire énergétique. La
Vigueur (≡ Mana) est ce que chaque être vivant — joueur, plante,
auxiliaire, nuisible — puise dans le territoire et y dépose à sa mort.

**3. Apprentissage par paliers de maîtrise** : découverte → investissement
→ maîtrise → expertise → transcendant. Granularité : **par famille
botanique et par concept écologique transversal** (succession,
polyculture, eau, compost…), pas par espèce individuelle. Évite l'UI
catastrophique (5 paliers × 100 espèces = 500 jauges).

**4. Méthode scientifique préférée** comme levier d'apprentissage.
Observer → formuler hypothèse → expérimenter → conclure. Le jeu
récompense trial & error, prise de risque, diversification d'idées.

**5. Transcendant = non-action existentielle.** Récompense ultime :
un écosystème auto-suffisant qui n'a plus besoin du joueur. Mitigations
contre la fin d'engagement : perturbations (météo extrême, nouvelles
espèces, usure structures) entretiennent le besoin, et la lenteur du jeu
rappelle le joueur par sessions espacées.

**6. 15 minutes d'action ininterrompue par saison**, en temps réel
(1 semaine = 60 secondes). Rythme soutenu au début, s'apaise avec la
maîtrise — ce qui prépare et justifie le palier transcendant.

**7. Découpage phase planification / phase saison clairement délimité :**
- Phase **planification** (entre deux saisons, temps figé) :
  plantation, achat magazine, aménagement de structures lourdes
  (mare, pergola, haie), changement de configuration, consultation
  longue de l'encyclopédie ;
- Phase **saison** (15 min temps réel) : arrosage ciblé, tuteurer,
  écraser un nuisible visible, paillage local, récolte, consultation
  rapide du carnet.

**8. Trois écoles de démarrage au choix** : friche pionnière, sol
modeste, jardin abandonné. Le joueur choisit son ambiance de départ.

**9. Quatre canaux d'acquisition d'espèces :**
- (a) succession spontanée (le sol décide selon `niche_index`) ;
- (b) événements rares (cadeaux du monde — bouture voisin, graine
  d'oiseau, vent…) ;
- (c) exploration de friche périphérique (abstraite au début, monde
  évolutif en backlog lointain) ;
- (d) **magazine de botanique** — déblocage par Vigueur joueur + niveau
  de maîtrise. Remplace le shop sans rompre la philosophie : tu achètes
  du savoir avec ton énergie vitale, et tu ne peux acheter que ce que tu
  es prêt à comprendre.

**10. Encyclopédie + carnet auto, dispositifs distincts :**
- **Encyclopédie** type wiki, se complète aux découvertes selon
  paliers (voir = entrée basique, cycle complet = description biologique,
  plusieurs cycles avec succès = effets écosystémiques).
- **Carnet auto** consultable, indexé, **descriptif au début**
  (faits bruts, le joueur infère) et **interprétatif au seuil de
  maîtrise** (le carnet propose des causes une fois le concept maîtrisé).
  Préserve la méthode scientifique.

**11. Auxiliaires visibles dès le début mais non identifiables sans
maîtrise.** Modèle technique : champ ambiant GridField pour la dynamique
écologique + sprites apparents visibles. Tu vois l'insecte avant de
connaître son nom — posture du naturaliste débutant.

**12. Extension du terrain par maîtrise écologique.** Démarrage à
9 tuiles dont la maison centrale. Maîtriser une famille botanique fait
apparaître une **tuile thématique** (verger, mare, prairie aromatique…)
— pas d'achat, pas de conquête : la connaissance ouvre l'espace.

### Modèle de Vigueur du joueur (à ajuster post-test)

- Montant initial : **100**
- Régénération continue : **+10 par semaine simulée**
- Régénération totale au passage de saison
- Sources extérieures : récolte de plantes mûres, méditation au foyer
- **Vigueur max augmente avec le niveau de maîtrise** — boucle de
  progression : plus on sait, plus on peut, plus on vit le jardin

### La maison normande = hub vivant (5 fonctions actives)

- Atelier (créer/réparer structures persistantes)
- Semis intérieur (germination hors saison)
- Magazine de botanique (déblocage espèces)
- Carnet (consultation centralisée)
- **Foyer** — nouveau lieu, point de récupération de Vigueur

### UX du volume cognitif

432 plots à surveiller × 15 min temps réel = **3 mitigations actives
simultanément** :
- Pause libre à volonté
- Notifications hiérarchisées (seuls les événements importants remontent)
- Zoom contextuel (×4 vue globale → ×32 vue un plot)

### Implications immédiates sur la philosophie

La règle #1 de la philosophie historique (« le joueur agit sur le MILIEU,
jamais directement sur les plantes ») est **partiellement assouplie** :
le joueur peut écraser un nuisible visible, mais l'action coûte de la
Vigueur et augmente `disturbance` localement — donc rappelle des
nuisibles. La permaculture s'enseigne par l'usure de la solution facile.
Voir [[feedback-design]] mémoire mise à jour.

### Zones blanches restantes (à traiter dans la suite de la session)

1. Cycle de sauvegarde (run éternel = persistance critique)
2. « Gérer » les aléas météo : mécanique précise
3. Multiples jardins / multijoueur
4. Lore / narration (qui est le joueur ? la maison normande ?)
5. Conditions de panne sèche (tout meurt)
6. Difficulty / accessibilité

---
