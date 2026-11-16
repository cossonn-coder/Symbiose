# ② Fruits et comestibilité — taille ↔ nombre, goût, toxicité

> Lire d'abord : `CLAUDE.md`, `00_etat.md`, puis
> `docs/vegetal/genetique/conception_caracteres_vivants.md` §2.2 et §3.
> Golden attendu : **RE-FIGÉ annoncé** — trois clés neuves ; la taille des fruits change
> la masse déposée en litière ; l'appétence des feuilles change la pression des ravageurs.

## Objectif
Gros fruits ou nombreux petits ; feuilles et fruits savoureux ou toxiques, organe par
organe ; le joueur apprend en goûtant.

## À faire
1. **Trois caractères en queue** : `taille_fruit`, `appetence_fruit`, `appetence_feuille`
   (unités, neutres d'espèce : tableau §2.2 ; défaut feuille 0, fruit +0.3 ; bornes [−1, 1]
   pour l'appétence).
2. **Taille ↔ nombre** : `sim/engine/decompo.py` ≈ l. 88-110 (`fruits_par_site`,
   `fruit_masse`, `FRUIT_MASSE`) : masse × gène, nombre ÷ gène (arrondi déterministe
   existant). Herbacées sans `fruits_par_site` : seule la masse change. Vérifier
   `sim/zoochorie.py:89` (même source) et le geste `manger` en mode fruit ciblé.
3. **Manger** (`sim/actions/gestes.py:58`) : le gain est modulé par l'appétence de l'organe
   (fruit ciblé → `appetence_fruit` ; générique → `appetence_feuille`). Sous −0.3, le gain
   devient une **perte** de Vigueur ∝ |appétence| (dette D31 : lire son entrée dans
   `DETTE.md` et la façade `sim/vigueur_plante.py` avant ; respecter le « coût nul » du
   geste lui-même, seule la valeur de l'organe devient négative). Le carnet note
   « c'était amer » / « j'ai eu mal au ventre » (événement neuf ou existant, voix interne).
4. **Herbivores** : pression des ravageurs × `(1 + appetence_feuille)`, plancher 0.2
   (`herbivory_pressure`, `sim/effects/perturbations.py`). Mulots et fruits : si un lecteur
   de fruits par la faune existe (`sim/mulot.py`), il lit `appetence_fruit` ; sinon rien.
5. **Zoochorie** : ne lit **pas** la toxicité pour l'homme (les oiseaux tolèrent les baies,
   conception §2.2) ; elle lit la taille du fruit si elle lit déjà sa masse.
6. **Re-figeage** : diff lu, `--capture`, hashes consignés.

## Tests
- Test ciblé : gros fruit → moins de fruits, masse totale ≈ conservée ; manger une feuille de
  tomate coûte de la Vigueur, une feuille de basilic en rend ; un fruit de lierre coûte ; la
  pression des ravageurs croît avec `appetence_feuille`.
- Tests des gestes et de la Vigueur existants verts (adapter seulement ce qui figeait un gain
  sans appétence, en le disant).

## Ne PAS faire
- Toucher au « coût nul » de `manger` (le geste ne dépense rien).
- Ne jamais lancer `tests/test_epaisseur_500ans`. Pas de `ps aux` / `pgrep -f`.

## Fin de tronçon
`00_etat.md` : ② FAIT, hashes. Commit.
