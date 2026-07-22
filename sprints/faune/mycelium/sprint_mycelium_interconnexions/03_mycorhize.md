# ③ Mycorhize — boost borné du phosphore (wood-wide-web)

> Lire d'abord `00_etat.md` + `docs/faune/mycelium/conception_mycelium_interconnexions.md`
> (§2, §2.2). Prérequis : ①② FAITS. Rôle le plus STRUCTURANT : le réseau **relie les
> racines vivantes au sol** et fait passer le **phosphore**. **Re-figeage golden
> (uptake) attendu et MAÎTRISÉ.**

## Objectif
Dans `plant_uptake`, **booster le prélèvement de `p` (phosphore SEULEMENT)** ∝
`mycelium` sous l'empreinte racinaire, plafonné (`MYCO_P_BONUS`). **Miroir** dans la
façade read-only `qi_local`. Réponse partielle à « pourquoi mon phosphore ne passe
pas » (`constants.py:287`). Décision figée (ii) : **`p` seulement**, jamais N/K.

## À faire

### A. Boost `p` dans `plant_uptake` (container.py:701)
- Boucle nutriments (~L783-795), branche `nut == "P"` UNIQUEMENT : multiplier le
  `besoin` (le FLUX prélevable) par `(1 + MYCO_P_BONUS × mycelium_norm)` :
  ```python
  for nut, fld in (("N", self.n), ("P", self.p), ("K", self.k)):
      besoin = (BESOIN[nut].get(stage_index, 0.0) * share * asphyxie_factor
                * (1.0 + micro_norm * UPTAKE_MICRO_BONUS)
                * dispo(ph_local, nut))
      if nut == "P":
          besoin *= 1.0 + MYCO_P_BONUS * self.mycelium.at_plot(r, c)
  ```
- `MYCO_P_BONUS` = knob `const` borné (placeholder, patron `UPTAKE_MICRO_BONUS=0.40`).
  Le `min(besoin, dispo_stock)` qui suit garde le bornage par le stock (Liebig) →
  jamais d'uptake infini. **Philo #2** : on modifie ce que le sol REND DISPONIBLE,
  pas la plante ; un mauvais pH (`dispo(ph,"P")`) reste limitant.

### B. Miroir dans `qi_local` (vigueur_plante.py:55)
- La façade lit `min(eco.n, eco.p, eco.k)` (~L75) pour estimer la nutrition perçue.
  Pour rester COHÉRENT avec l'uptake réel, appliquer le même boost `p` AVANT le min :
  ```python
  p_eff = eco.p.at_plot(r, c) * (1.0 + MYCO_P_BONUS * eco.mycelium.at_plot(r, c))
  nutri = min(eco.n.at_plot(r, c), p_eff, eco.k.at_plot(r, c))
  ```
  Importer `MYCO_P_BONUS` depuis `fields.ecofields` (comme `UPTAKE_MICRO_BONUS` déjà
  importé L33). Lecture seule (la façade ne mute rien).

## Couches
Inchangées. `plant_uptake` (fields) et `qi_local` (sim, lecture seule) lisent
`mycelium`. Vérifier que `MYCO_P_BONUS` est exporté par `fields/ecofields/__init__.py`.

## Définition de done
- Boost `p` dans `plant_uptake` (P seul) + miroir `qi_local`, knob `MYCO_P_BONUS`.
- `tests/test_mycelium.py`/`test_vigueur` étendu : à mycélium FORT sous l'empreinte,
  une plante prélève plus de `p` (et `qi_local` monte) qu'à mycélium nul, MÊME N/K ;
  N et K STRICTEMENT inchangés par le mycélium ; bornage par stock respecté (sol
  pauvre en P ⇒ pas de miracle) ; mycélium nul ⇒ uptake bit-identique à AVANT.
  Déterminisme h1==h2.
- **Golden RE-FIGÉ (uptake)** : nouveau hash smoke. Dérive **localisée au phosphore
  prélevé** là où il y a du mycélium. L'ANALYSER (bornée, P-only), re-figer, noter
  `ancien → nouveau` + explication dans `00_etat.md`. Population : viser inchangé.
- MAJ `00_etat.md` (③ → FAIT + hash) puis commit.

## Pièges
- **P SEULEMENT** : ne JAMAIS booster N ou K (décision figée ii). Un copier-coller qui
  touche les trois casse la pédagogie ET le golden largement.
- Le boost reste BORNÉ et plafonné par le stock — pas de `+= grand nombre`. Calibrer.
- Le miroir `qi_local` DOIT suivre l'uptake (sinon la vigueur perçue ment) — mais
  c'est une lecture, aucune mutation de champ.
- Ne PAS déverrouiller la fenêtre pH : `dispo(ph,"P")` reste un facteur à part.
