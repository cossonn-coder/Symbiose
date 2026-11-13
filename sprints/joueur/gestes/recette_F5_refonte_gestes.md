# Recette F5 — refonte de l'accès aux gestes (3 sprints)

> Plan de test unique pour `sprint_acces_gestes`, `sprint_palette_tiroir` et
> `sprint_icones_curseur`, clos côté code du 2026-11-12 au 2026-11-13 (golden
> `b4a921f8…` intact, pont 0.6.13). Il remplace la lecture des trois recettes
> éparses dans leurs `00_etat.md`, qui restent la référence de détail.
>
> **Principe** : tu ne valides que ce que la VM ne peut pas voir — la souris, le
> clavier, le curseur de Windows, et ton ressenti. Tout ce qui se prouve par
> mesure est déjà prouvé (§A). Chaque étape tient en moins d'une minute.

## 0. Préparation (2 min)

1. Sur le PC : `git pull` (dernier commit `351ff2b`), puis F5 dans Godot.
2. Au sélecteur de monde : banc **`acces_gestes`**. La tuile d'essai est au coin
   **sud-est**. Vigueur 3000 au banc : aucun geste ne sera refusé faute de Vigueur.
3. Garde ce fichier ouvert à côté. Note seulement les **KO** et les « bof ».

## A. Déjà prouvé sans toi — NE PAS re-tester

- Tous les gestes sont atteignables en jeu normal : test d'atteignabilité 36/36.
- Le banc joue chaque porte de bout en bout par le pont : oracle 56/56
  (`python3 -m tests.bancs.test_acces_gestes`).
- Les 46 icônes existent, font 16×16, ont un point chaud sur un pixel peint :
  contrôle au démarrage, journal `[Icones] 45 gestes vérifiés, 0 défaut(s).`
- Les icônes et les animations ont été regardées sur planche
  (`sprint_icones_curseur/planche/*.png`).
- Le clic sur un tronc devant la maison a été mesuré au banc (15/15 segments).

Ce qui reste n'a **jamais** été vu avec une vraie souris.

## B. Parcours (≈ 20 min, dans l'ordre)

Coche ✅ / ❌. Le sprint d'origine est entre crochets : [A] accès, [P] palette &
tiroir, [I] icônes & curseur.

### B1. Le curseur (2 min)
- [ ] **1** [I] Sans geste armé : le curseur est la main gantée.
- [ ] **2** [I] Touche `1` : le curseur devient l'icône du geste de la case 1.
      Sous Windows, **c'est bien l'icône, pas une croix système**.
- [ ] **3** [I] Survole la barre, puis un panneau : la main revient. Retour sur
      le jardin : l'icône revient.
- [ ] **4** [I] Clique une petite cible (un plot précis, une plante isolée) :
      l'action part **sous le bout de l'outil**, là où tu vises.
- [ ] **5** [I] À ta résolution, l'icône du curseur se lit (taille ×2).

### B2. Le tiroir (3 min)
- [ ] **6** [P] `Q` ouvre le tiroir, rangé par familles. `Q` ou `Échap` le ferme.
- [ ] **7** [P] Tiroir ouvert, clic sur le jardin : il se ferme **sans rien faire**
      au jardin.
- [ ] **8** [P] Clic gauche sur `glaner` dans le tiroir : il est en main, le
      bouton du bas porte son icône, le HUD le nomme sans numéro, le curseur
      prend son icône.
- [ ] **9** [P] Clic droit sur un geste du tiroir → « case 3 » : il prend la case
      ET devient actif. Pareil par clic droit sur une case de la barre.
- [ ] **10** [P] Ctrl+molette : le geste actif monte et descend dans la barre ; la
      molette seule zoome toujours.
- [ ] **11** [P] `K` et `J` ne font plus rien.

### B3. Les premières portes (3 min)
- [ ] **12** [A] Au départ, le tiroir montre peu de gestes ouverts.
- [ ] **13** [A] `glaner` ×3 sur le coin de feuilles mortes (ouest de la tuile) :
      `poser bac`, `poser pile`, `pailler` apparaissent ; **le bouton du tiroir bat**.
- [ ] **14** [A] Pose un bac et une pile : `composter`, `retourner`, `épandre`,
      `empiler bois` s'ouvrent. `creuser` un plot : `endiguer`, `dériver`.

### B4. Les réglages (2 min)
- [ ] **15** [P] `planter` : des pastilles de graines à côté de la case ; un clic
      choisit la graine.
- [ ] **16** [P] `pailler` : 4 natures, pâles si le stock manque. Feuilles par
      défaut. Le paillis de feuilles posé se voit (roux).
- [ ] **17** [P] `poser pot` (après achat des pots, B5) : 5 substrats.
- [ ] **18** [P] `S`, `B`, `N` ne font plus rien.

### B5. L'Atelier et les silhouettes (4 min)
Hub de la maison → onglet **Atelier**.
- [ ] **19** [A] Achète les **tuteurs** : le bouton du tiroir bat. Dans la rangée
      « structures », une **silhouette sombre** ; la survoler donne une phrase, sans
      consigne ni chiffre.
- [ ] **20** [A] Achète sécateur, broyeur, pots, voile, hache, serpe, pioche : les
      gestes correspondants apparaissent (couper, broyer, poser pot, voile/cloche/
      ombrière, abattre, recéper, entailler).
- [ ] **21** [A] **Clique les 9 gestes neufs** et vérifie que l'objet posé **se
      voit** : tuteur, treillis, pergola ; palisser (le jasmin, au nord de la tuile,
      avec un tuteur à son pied) ; voile, cloche, ombrière ; poser ruche ; récolter
      miel (sur la ruche — seulement si l'essaim est venu, B7).

### B6. Les animations (3 min)
Arme le geste, clique une cible valide, regarde le curseur.
- [ ] **22** [I] `arroser` un plot : l'eau coule et éclabousse.
- [ ] **23** [I] `couper` une plante : la lame mord, éclat au bec.
- [ ] **24** [I] `bêcher` un plot : l'outil se lève, frappe, miettes.
- [ ] **25** [I] `poser bac` : l'objet descend et touche.
- [ ] **26** [I] `récolter` une plante mûre : le panier plonge.
- [ ] **27** [I] `composter` sur un bac : petit cercle.
- [ ] **28** [I] `écraser` un nuisible : la botte se lève et retombe.
- [ ] **29** [I] Un geste refusé par le moteur (ex. `composter` sans litière) :
      courte secousse gauche-droite.
- [ ] **30** [I] Premier clic d'`épandre` sur un tas : l'icône appuie une fois.
- [ ] **31** [I] Au repos, **rien ne bouge**. Pendant une animation, la main
      revient bien si tu passes sur la barre.

### B7. Les portes lentes (optionnel, Turbo, ~5 min réelles)
- [ ] **32** [A] Lance la saison en Turbo. ~10 semaines : phacélies en fleur →
      lettre d'essaim de Bertrand → `poser ruche`.
- [ ] **33** [A] ~12 semaines : le merle prend des cerises → `perchoir`.
- [ ] **34** [A] Greffoir acheté + lettre d'Augustin → `greffer`.

### B8. Le clic sur un tronc (1 min)
- [ ] **35** [P] Banc **`verger_mur`** : clique le tronc d'un arbre devant la
      maison. Le geste part sur l'arbre, le carnet ne s'ouvre pas.

## C. Ressenti — une phrase suffit

- Les icônes dans la barre et le tiroir : lisibles ? Lesquelles hésites-tu à
  reconnaître ? Suspectes connues : `palisser` (une balle ?), `endiguer`,
  `broyer`, `glaner`, `pincer`.
- Les animations : vitesse (80 ms par image), trop discrètes ou trop présentes ?
  Faibles connues : poussière de « poser », miettes de « remuer », éclats
  d'`abattre`, secousse de refus (2 px).
- Trouver un geste : le tiroir suffit-il, ou cherches-tu encore ?

## D. Trois décisions prises sans toi — à garder ou défaire

1. **Pont 0.6.13** : deux clés de lecture ajoutées au pont (`paillis_dispo`,
   `graines_espece`) alors que le sprint palette était « pure vue ». Sans elles :
   plus d'estompage des paillis vides, graines toutes de la même teinte.
2. **Refus dur** : le pont exécute un geste fermé s'il est envoyé à la main
   (seuls les gestes de paysage vérifient). La vue ne l'envoie jamais. Faut-il
   un refus dur ?
3. **Secousse** : elle ne joue qu'au refus du **moteur**. Un clic dans le vide
   (« aucune tuile ici ») garde seulement le message qui clignote.

## E. Me rendre compte

Une ligne par KO : `n° — ce que tu as vu`. Plus tes phrases de §C et tes choix
de §D (garder / défaire). Tout OK → je clos D118 (d)(e) et D133 en entier.
