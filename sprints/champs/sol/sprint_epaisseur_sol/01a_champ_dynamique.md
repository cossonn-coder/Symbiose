# ①a — Champ `epaisseur_sol` stocké + dynamique de relaxation

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Tu ne sais
> rien d'autre : tout est ici. Conception complète :
> `docs/champs/sol/conception_epaisseur_sol.md`.

## Objectif

Créer un **champ stocké** `epaisseur_sol` (un `GridField` par tuile,
**sauvegardé**) dont la valeur **relaxe** vers une cible bulk-density dérivée des
`om_*`, avec inertie asymétrique. **Aucun effet en retour cette tranche** (les
effets eau/NPK sont pour ①b) : on pose juste le champ et sa dynamique.

## Ce que dit déjà le moteur (vérifié)

- MO d'une tuile dans `fields/ecofields/matiere_organique.py` :
  - `litiere[r][c]` = liste de `Parcelle` typées, chacune avec `age_sem` (déjà
    incrémenté chaque tick, lignes ~178/284).
  - `om_fresh_at(r,c)` = Σ des masses des parcelles (méthode existante ~ligne 27).
  - `self.om_active`, `self.om_stable` = `GridField` (accès `.data[r][c]` ou
    `.at_plot(r,c)`, `.add(r,c,delta)`, `.set(r,c,v)`).
- `GridField` défini `fields/grids.py:20` (constructeur `GridField(rows, cols)`,
  data 2D, `.at_plot`, `.add`, `.set`, `.average`).
- Cascade décompo dans `tick_decomposition` (`matiere_organique.py`) minéralise +
  respire → fait déjà baisser `om_*` (donc la cible baissera → épaisseur suivra).
- Ordre de tick (`sim/engine/boucle.py`, méthode `tick_semaine`) : … hydrologie
  (~l.215) → **décompo (~l.220)** → structures → pH → structure → **mycélium
  (~l.252)** → diffusion → … → **populations (~l.363)**. Tous les consommateurs
  de MO tournent APRÈS l'hydrologie.

## À implémenter

### 1. Le champ (dans le conteneur EcoFields de la tuile)

Trouve où les autres `GridField` de MO sont construits (probablement le
`__init__` du conteneur EcoFields, cf. `fields/ecofields/container.py` et
`matiere_organique.py`). Ajoute `self.epaisseur_sol = GridField(rows, cols)`,
**initialisé au niveau de repos** correspondant au fond hérité : à l'init,
epaisseur = cible calculée sur l'`om_stable` initial (D56, `OM_STABLE_INIT=0.15`
hétérogène), pour partir déjà au repos et éviter un transitoire de montée au tick 0.

### 2. Le tick `tick_epaisseur(self)`

Nouvelle méthode dans le module MO (`matiere_organique.py`) ou un module dédié
`fields/ecofields/epaisseur.py` **si** ça garde MO sous la bande de taille
(vérifie `tools/compte_ldc.py` ; si `matiere_organique.py` dépasse ~300 LDC après
ajout, sors l'épaisseur dans son propre module — un fichier = une responsabilité).

Pour chaque plot `(r,c)` :

```
foisonnement_fresh = Σ_parcelles( masse_p · foisonnement(age_sem_p) )
    # foisonnement(age) décroît avec l'âge : ex. 1/(1 + K_TASSE·age_sem),
    # K_TASSE placeholder calibré F5. Litière jeune foisonne, vieille plaquée.
cible = E_FRESH · foisonnement_fresh
      + E_ACTIVE · om_active[r][c]
      + E_STABLE · om_stable[r][c]
delta = cible − epaisseur[r][c]
taux  = TAUX_MONTEE if delta > 0 else TAUX_DESCENTE   # montée > descente (asym.)
epaisseur[r][c] += delta · taux
epaisseur[r][c] -= EPAISSEUR_EROSION                  # voies naturelles
epaisseur[r][c]  = max(0.0, epaisseur[r][c])          # plancher minéral
```

Constantes (placeholders, dans `fields/ecofields/constants.py`, commentées) :
`E_FRESH > E_ACTIVE > E_STABLE`, `K_TASSE`, `TAUX_MONTEE > TAUX_DESCENTE` (∈]0,1[),
`EPAISSEUR_EROSION` (petit). Choisis des valeurs plausibles ; calibrage réel = F5.

### 3. Brancher le tick dans la boucle

Dans `sim/engine/boucle.py` `tick_semaine`, appelle `eco.tick_epaisseur()`
**APRÈS** `tick_populations` (ou au plus tard après tous les consommateurs de MO
du tick), pour que la cible reflète la consommation de la semaine. Commentaire
pédagogique obligatoire : expliquer le placement (l'hydro lira l'épaisseur du tick
précédent → décalage 1 tick uniforme déterministe, préparé pour ①b).

### 4. Save / engine_version

- Sérialise/désérialise `epaisseur_sol` dans le save JSON (cherche comment les
  autres `GridField` de la tuile sont sauvés — même patron).
- Bump `ENGINE_VERSION` dans `tools/simserver/version.py` (actuellement
  `"0.5.13"` → `"0.5.14"`), avec entrée de changelog en tête de fichier
  (respecte le format existant).

## Golden

**RE-FIGÉ, ANNONCÉ.** Cause unique : un champ tické neuf existe (état + éventuel
micro-impact si un autre système lisait déjà… ici NON, aucun lecteur cette
tranche → la dérive attendue est **nulle sur le comportement**, seul le save
gagne un champ). Lance `python3 -m tests.test_golden` :
- Si le golden est **inchangé** (attendu, car aucun effet en retour) → parfait,
  ne re-fige rien.
- S'il **bouge** (ex. le save round-trip modifie un ordre) → dérive localisée,
  explique-la dans le commit et re-fige. **Toute dérive doit être comprise** —
  si tu ne l'expliques pas, tu as un bug, annule.

## Ce qu'il NE faut PAS faire

- **Aucun effet en retour** (pas de greffe hydro, pas d'accès NPK) — c'est ①b.
- Ne pas retirer de masse aux `om_*` depuis le tick épaisseur (l'épaisseur SUIT,
  elle ne consomme pas — anti-double-comptage).
- Ne pas exposer au snapshot (c'est ②).
- Ne pas modéliser le priming rhizosphérique (dette reportée).
- Pas de RNG (déterminisme #3).

## Perf

O(plots × parcelles) par tuile, un balayage, pas de géométrie. Négligeable
(< 1 % tick). Si `foisonnement_fresh` reparcourt les parcelles déjà parcourues
par `tick_decomposition`, envisage de mémoriser la somme au passage décompo pour
éviter un double balayage — optionnel, mesure d'abord.
