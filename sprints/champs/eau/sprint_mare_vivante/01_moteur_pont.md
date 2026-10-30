# ① Moteur + pont — glace, lame des plots de marais, dit = peint

**Golden INCHANGÉ obligatoire** (`4c696821…`). Pont 0.6.1 → **0.6.2** (rétro-compatible,
historique dans `data/code/tools/simserver/version.py`). Lire `00_etat.md` d'abord.

## (d) Glace — état Python
- Nouveau champ d'état `glace` ∈ [0,1] par plot dans `EcoFields` (patron `snow`/`givre`,
  helper PUR dans un module dédié `fields/ecofields/glace.py`). Ne concerne que les plots
  qui portent une lame (> `SEUIL_FLAQUE`) : elle **prend** par nuits de gel successives
  (lire `thermique.t_min_nuit_at` ou la température du tick — vérifie ce qui est dispo au
  point d'appel), **fond** au dégel ; une lame disparue emporte sa glace.
- Tick près de `tick_snow` dans `sim/engine/boucle.py` (vérifie l'ordre réel).
- **Aucun effet en retour** sur hydrologie, populations ou plantes dans ce sprint →
  golden neutre. Si le digest du golden lisait tous les attributs d'`eco`, exclure `glace`
  et le signaler.
- Mesure : `full` seed 42 sur 2 ans → semaines où la mare est prise (centre `glace` ≥ 0,5) ;
  attendu : hiver seulement, jamais en été. Placeholders commentés (pédagogie).

## (b) Lame des plots de marais
- Le bloc `marais` exporte aussi la **lame** du plot (5ᵉ champ, arrondi 3 déc.) ET la
  `glace` (6ᵉ champ). Le bloc `eau_surface` reste tel quel. Un binaire 0.6.1 ne les
  émet pas → la vue prendra lame = absente (documenter).
- Mesure du marnage : lame des 9 plots de `MARE_FOND` sur 104 sem. [seeds 42/1/2] —
  le centre (8,5) ne descend jamais sous `SEUIL_FLAQUE` (sinon : renforcer la source au
  centre, chiffré, sans toucher aux paramètres d'hydrologie globaux) ; noter si les bords
  se découvrent surtout l'été (marnage saisonnier) ou au hasard des semaines.

## (a) Dit = peint
- Repérer **toutes** les surfaces textuelles qui nomment une bête : voix des bêtes
  (`sim/voix_etres.py` + corpus : prédateur / proie cités), info-bulle du vivant, et ce
  qui alimente « il y a des libellules au-dessus de la mare » côté hover. Une espèce
  n'est nommée que si elle est **peinte** à cet endroit (même critère que
  `perception.SEUIL_PRESENCE`, une seule source — pas un 2ᵉ seuil copié).
- Corriger la majuscule « J'ai senti La libellule » (le nom est inséré tel quel en tête
  de groupe nominal → article en minuscule).
- Test ciblé : hors saison (densité < seuil), aucune phrase ne cite moustique/libellule.

Fin : golden, `test_sim_server` (+ checks du nouveau champ), suites voix/infobulle vertes,
`00_etat.md` mis à jour (mesures + écarts). Pas de C# ici.
