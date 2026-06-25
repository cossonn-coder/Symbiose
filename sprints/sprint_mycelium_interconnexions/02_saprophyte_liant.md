# ② Saprophyte (décompo `bois`) + liant (`om_stable`)

> Lire d'abord `00_etat.md` + `docs/conception/CONCEPTION_MYCELIUM_INTERCONNEXIONS.md`
> (§2, §2.1). Prérequis : ① FAIT (le champ `mycelium` pousse). On BRANCHE le premier
> rôle : le champignon **digère le bois** et **lie le sol**. **Re-figeage golden
> (décompo) attendu et MAÎTRISÉ.**

## Objectif
Le mycélium **accélère la décompo du tissu `bois`** (terme fongique `×(1+α·mycelium)`)
et **ajoute lentement à `om_stable`** (glomaline / liant du sol). Ferme la boucle du
bois : « le bois nu pourrit mal ; couvert, humide, non bêché, le champignon le digère ».

## À faire

### A. Terme saprophyte (`tick_decomposition`, container.py:531)
- Dans la boucle par parcelle (~L584-595), pour `p.tissu == "bois"` SEULEMENT :
  moduler la masse décomposée `d` (L586) par `×(1 + ALPHA_SAPRO × mycelium_norm)`,
  où `mycelium_norm = self.mycelium.at_plot(r,c)` (déjà ∈ [0,1]).
  ```python
  decay, humif, miner = TISSU[p.tissu]
  d = p.masse * decay * speed
  if p.tissu == "bois":
      d *= 1.0 + ALPHA_SAPRO * self.mycelium.at_plot(r, c)
  ```
- `ALPHA_SAPRO` = knob `const` (placeholder, p.ex. 1.0–2.0) dans `constants.py`.
- Effet émergent : là où le réseau est installé, le bois se minéralise/humifie plus
  vite ; ailleurs, décompo `bois` lente inchangée. Aucun autre tissu touché.

### B. Liant `om_stable` (lent)
- Un petit ajout à `om_stable` ∝ `mycelium` : `self.om_stable.add(r, c, LIANT_K *
  mycelium_norm)`. Placer dans `tick_mycelium` (① — cohérent : c'est le réseau qui
  agrège) OU en fin de `tick_decomposition`. **Très lent** (`LIANT_K` petit) pour
  ne pas exploser l'humus. Borné par le `max_val` du champ.

## Couches
Inchangées (tout dans `fields/ecofields/`). Lecture seule de `mycelium`, écriture
`om_stable` (déjà mutée par la décompo).

## Définition de done
- Terme fongique sur `bois` + liant `om_stable`, knobs `ALPHA_SAPRO`/`LIANT_K`.
- `tests/test_mycelium.py` étendu (ou `test_structures`) : à mycélium FORT, une
  parcelle `bois` décompose plus vite qu'à mycélium nul (même état initial) ;
  `om_stable` monte lentement sous un réseau ; mycélium nul ⇒ décompo `bois`
  bit-identique à AVANT (non-régression du terme). Déterminisme h1==h2.
- **Golden RE-FIGÉ (décompo)** : mesurer le nouveau hash smoke. La dérive doit être
  **localisée à la décompo du bois** là où du mycélium s'est installé. L'ANALYSER
  (cohérente, bornée), puis re-figer. Noter `ancien → nouveau` dans `00_etat.md`
  avec une phrase d'explication. Population : viser inchangé (rien ne touche la faune
  en ②).
- MAJ `00_etat.md` (② → FAIT + hash) puis commit.

## Pièges
- **`bois` UNIQUEMENT** — ne pas accélérer feuille/herbacé/fruit (le champignon
  lignivore est spécialiste). Vérifier la condition `p.tissu == "bois"`.
- Le liant doit rester LENT : un `LIANT_K` trop fort dérive `om_stable` (mémoire du
  sol) et casse le golden bien au-delà du bois. Calibrer petit.
- Ne PAS toucher l'uptake (③) ni la faune (④) ici.
- Garder la décompo des AUTRES tissus strictement inchangée (non-régression).
