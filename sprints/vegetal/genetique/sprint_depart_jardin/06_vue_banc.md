# ⑥ Vue Godot + banc `depart_jardin` (D140 C)

Lire d'abord `docs/vegetal/genetique/conception_depart_jardin.md`, puis les bilans ①-⑤
dans `00_etat.md` (clés de pont ajoutées, nom du geste).

## Objectif
1. **Geste `repiquer`** dans la palette (famille des pots), avec icône dans la palette
   maître (voir les icônes de gestes existantes, `sprint_icones_curseur`) et curseur.
2. **Pots dans la maison** : visibles (ex. au rebord d'une fenêtre de la maison ou par
   un indicateur sur la maison), cliquables pour `repiquer`/`deplacer_pot`. Choisir la
   solution la plus simple et lisible ; pas de refonte de la maison.
3. **Choc de repiquage** : signe visible discret (feuilles un peu tombantes quelques
   semaines) s'il est exporté par le pont ; sinon le signaler.
4. **Banc F5 `depart_jardin`** (`data/code/bancs/`, patron des bancs existants, warmup
   si utile) : à ×8, un pot de tomate dans la maison, un pot dehors, une tomate
   repiquée trop tôt (gèle), une repiquée après la fenêtre, une graine semée qui lève
   sur sol chaud.
5. `dotnet build Symbiose.csproj` vert. Planche PNG si le banc de capture Xvfb est
   utilisable (cf. `sprint_caracteres_vivants/planche/`).
6. **Clôture** : recette F5 complète dans `00_etat.md` ; `DETTE.md` D140 → A, B, C
   « faits côté code, F5 attendu » (D, E, F restent ouverts) ; `BACKLOG.md` si besoin.
   Ne pas écrire `journal.md` (l'orchestrateur s'en charge).

## Golden
**INTACT**.

## Ne PAS faire
- Les éclaboussures de pluie et Ctrl+molette des graines (D140 E-F, hors sprint).
- Peaufiner le rendu (refonte gaussian splatting à venir) : le minimum lisible.

## F5
Monde `full` : ouverture fin mai, 52 espèces adultes, arbres mûrs ; pots dans la maison,
`repiquer` à la main ; automate branché qui repique ; chronique « froid »/« gel » au
lieu de `non_consignee` ; banc `depart_jardin`.
