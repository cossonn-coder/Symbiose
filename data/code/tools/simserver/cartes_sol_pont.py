"""
SYMBIOSE — tools/simserver/cartes_sol_pont.py
Les CARTES DE SOL d'une tuile au snapshot : litière, alarme, température,
condensation, épaisseur, altitude, eau de surface, marais, couverture, paillage,
allélopathie, inoculum, couvertures posées. Extrait tel quel de `serialize.py`
(passe /refactor du 2026-11-13, découpage pur) : une carte = une clé du snapshot,
indexée ensuite par tuile. Lecture seule de champs déjà tickés → golden NEUTRE.
"""
from __future__ import annotations

# Seuil de perception d'une flaque (sprint hydrologie & marécages ②) : la liste
# creuse `eau_surface` ne consigne que les plots dont la lame le dépasse.
from fields.ecofields.constants import SEUIL_FLAQUE, COUVERTURE_RENDU_SEUIL, MARAIS_OFF, ALLELO_FLOOR

# Clés produites par `cartes_sol`, dans l'ordre du snapshot.
CLES_CARTES_SOL = ("litiere", "alarme", "temperature", "condensation", "epaisseur",
                   "altitude", "eau_surface", "marais", "couverture", "paillage",
                   "allelopathie", "inoculum", "couvert_pose", "ombre_pose")


def cartes_sol(eco) -> dict:
    """Les cartes de sol d'UNE tuile, `{clé snapshot: valeur}` (cf. CLES_CARTES_SOL)."""
    out = {}
    # Litière typée par plot (décompo·compost ①, rendue par la vue en
    # 03·B) : la couche fraîche de nécromasse au sol. On n'expose QUE ce
    # qui se dessine — la parcelle `diffus` (exsudats racinaires, humus
    # permanent, masse souvent > 0 via croissance) n'est PAS de la litière
    # de surface : on l'écarte du tissu dominant ET du total. Format
    # COMPACT (cf. `sprites`) : par plot non vide `[r, c, tissu_dominant,
    # masse, age_sem]` — dominant = parcelle de plus grande masse hors
    # `diffus`, masse = Σ des parcelles de surface (densité ∝ masse côté
    # vue). Les plots sans litière de surface sont OMIS (liste creuse).
    # 0.5.51 : + `bois_masse, bois_age_sem` (index 5-6, 0.0 sans bois).
    # 0.5.55 (⑦bis) : + `bois_diam_cm` (index 7, 0.0 sans bois) — la vue ⑧
    # dessine brindille / branche / souche selon la grosseur.
    # `age_sem` (rendu feuillage ⑥, 0.5.6) = ÂGE MOYEN pondéré par la masse
    # des parcelles de surface : proxy d'ÉTAT DE DÉCOMPO déjà calculé par le
    # moteur (`Parcelle.age_sem`, semaines depuis dépôt) — la vue assombrit/
    # désature la litière de feuilles à mesure qu'elle vieillit (dérive vers
    # l'humus, §6.3). TRANSPORT pur (donnée existante, aucun calcul moteur
    # nouveau) → golden NEUTRE. PURE lecture (`eco.litiere` déjà rempli par
    # le tick).
    plots = []
    for r in range(eco.rows):
        for c in range(eco.cols):
            surface = [p for p in eco.litiere[r][c]
                       if p.tissu != "diffus" and p.masse > 0.0]
            if not surface:
                continue
            dominant = max(surface, key=lambda p: p.masse)
            total = sum(p.masse for p in surface)
            # Âge moyen pondéré par la masse (total > 0 garanti : surface
            # ne retient que les parcelles masse > 0). Litière fraîche
            # (age ≈ 0) = brun-roux vif ; vieillie, elle fond dans le sol.
            age_moy = sum(p.age_sem * p.masse for p in surface) / total
            # Bois mort (D111 ②, 0.5.51) : masse + âge de la parcelle `bois`
            # MÊME sous des feuilles dominantes → la vue (⑧) dessine la branche
            # et son stade de décompo. Fusion par tissu ⇒ ≤ 1 parcelle `bois`.
            bois = next((p for p in surface if p.tissu == "bois"), None)
            # Masse de feuilles (AUTOMNE VISIBLE ③, 0.6.3) MÊME sous un autre
            # tissu dominant : le tapis de ⑤ ne dépend plus du tissu dominant.
            feuille = next((p for p in surface if p.tissu == "feuille"), None)
            plots.append([r, c, dominant.tissu,
                          round(total, 4), round(age_moy, 3),
                          round(bois.masse, 4) if bois else 0.0,
                          round(bois.age_sem, 3) if bois else 0.0,
                          round(bois.diam_cm, 2) if bois else 0.0,
                          round(feuille.masse, 4) if feuille else 0.0])
    out["litiere"] = plots
    # Phéromone d'alarme apienne (⑦, §J, 0.4.1) : liste CREUSE des plots en
    # alarme `[r, c, intensite]` (foyers > 0 seulement). Godot lit l'intensité
    # au curseur → les abeilles présentes piquent (réaction temps réel, coût
    # Vigueur côté vue). PURE lecture (`eco.alarme` rempli par les déclencheurs
    # + décru par le tick) → golden NEUTRE (vide tant qu'aucune abeille écrasée
    # / aucun miel récolté nu). Champ optionnel côté vue (tolérance pré-0.4.1).
    af = getattr(eco, "alarme", None)
    foyers = []
    if af is not None:
        for r in range(eco.rows):
            for c in range(eco.cols):
                v = af.data[r][c]
                if v > 0.0:
                    foyers.append([r, c, round(v, 4)])
    out["alarme"] = foyers
    # Carte température par tuile (sprint thermique ⑧, §B) : ÉTATS
    # persistants déjà calculés par le tick → lecture DIRECTE (≠ météo
    # scalaire, recalculée par fonction pure plus bas). `snow` = manteau
    # neigeux scalaire (⑦, voile blanc ∝ snow côté vue). `t_sol` = grille 2D
    # rows×cols de la température de surface spatialisée (heatmap ⑩) ;
    # T_air uniforme N'EST PAS dupliquée par plot (elle vit dans `weather`).
    # PURE lecture (`eco.snow`/`eco.temperature_sol` remplis par le tick)
    # → golden NEUTRE. Champ optionnel côté vue (tolérance pré-0.5.0).
    out["temperature"] = {
        "snow": round(eco.snow, 3),
        "t_sol": [[round(eco.temperature_sol.data[r][c], 2)
                   for c in range(eco.cols)] for r in range(eco.rows)],
    }
    # Carte de CONDENSATION par tuile (sprint météo→champs ⑤, §6, 0.5.10) :
    # liste CREUSE des plots `[r, c, rosee, givre]` où il y a eu rosée
    # liquide ce matin (`eco.rosee_last`, écrite par `tick_rosee`) ou du givre
    # accumulé (`eco.givre`, gelée blanche non encore fondue). La vue Godot en
    # tire les GOUTTES scintillantes (rosee > 0, été/printemps) et le GIVRE
    # blanc (givre > 0, hiver) — rendu C# = dette D24, ⑤ n'expose que la donnée.
    # Plots secs/sans dépôt OMIS (liste creuse, comme `litiere`/`alarme`).
    # PURE lecture (champs remplis par le tick) → golden NEUTRE pour le pont ;
    # le smoke en pose (nuits claires) mais le pont ne RÉINJECTE rien. Champ
    # optionnel côté vue (tolérance pré-0.5.10).
    rl = getattr(eco, "rosee_last", None)
    gv = getattr(eco, "givre", None)
    condensation = []
    if rl is not None and gv is not None:
        for r in range(eco.rows):
            for c in range(eco.cols):
                rosee = rl.data[r][c]
                givre = gv.data[r][c]
                if rosee > 0.0 or givre > 0.0:
                    condensation.append(
                        [r, c, round(rosee, 4), round(givre, 4)])
    out["condensation"] = condensation
    # Carte d'ÉPAISSEUR de sol par tuile (D57 ②, §4) : grille 2D dense
    # rows×cols de `eco.epaisseur_sol` en cm (relaxation vers la cible
    # bulk-density, remplie par `tick_epaisseur` ①a). La vue en extrude un
    # RELIEF iso (dessus du plot remonté de `epaisseur_cm × PxPerCmZ`) → on
    # voit le sol monter (humus qui s'accumule) et descendre (décompo/
    # tassement/érosion). PURE lecture (champ déjà tické) → golden NEUTRE.
    # Champ optionnel côté vue (tolérance pré-0.5.16).
    out["epaisseur"] = [
        [round(eco.epaisseur_sol.data[r][c], 2)
         for c in range(eco.cols)] for r in range(eco.rows)]
    # Carte d'ALTITUDE par tuile (sprint hydrologie & marécages ①, §1) :
    # grille 2D dense rows×cols du MICRO-RELIEF topographique `eco.altitude`
    # en cm (socle géométrique FIXE, initialisé hétérogène par `init_eco`,
    # DÉCORRÉLÉ de l'humus). La vue en tire le relief du terrain (⑧) et
    # portera l'écoulement visible (②). À NE PAS confondre avec `epaisseur`
    # (humus foisonnant). PURE lecture (champ jamais tické) → golden NEUTRE.
    # Champ optionnel côté vue (tolérance pré-0.5.17 → terrain plat).
    out["altitude"] = [
        [round(eco.altitude.data[r][c], 2)
         for c in range(eco.cols)] for r in range(eco.rows)]
    # Lame d'EAU DE SURFACE par tuile (sprint hydrologie & marécages ②, §2) :
    # liste CREUSE `[[r, c, lame], …]` des plots portant une lame > SEUIL_FLAQUE
    # (la plupart des plots sont SECS → liste courte, patron `litiere`/`alarme`).
    # La vue en tire les FLAQUES (lame translucide bleutée ∝ profondeur, ⑧).
    # PURE lecture (champ déjà tické par `tick_ruissellement`) → aucun impact
    # golden. Champ optionnel côté vue (tolérance pré-0.5.18 → pas de flaque).
    out["eau_surface"] = [
        [r, c, round(eco.eau_surface.data[r][c], 3)]
        for r in range(eco.rows) for c in range(eco.cols)
        if eco.eau_surface.data[r][c] > SEUIL_FLAQUE]
    # Carte de MARÉCAGE par tuile (sprint hydrologie & marécages ③) : liste
    # CREUSE `[[r, c, marais, etat], …]` des plots où `marais_memory > MARAIS_OFF`
    # (marais naissant ou installé). `marais` ∈ [0,1] = intensité (la vue
    # « noircit » le sol ∝ mémoire, philo #5) ; `etat` = booléen d'hystérèse
    # (`est_marais`). La plupart des plots sont SECS → liste courte (patron
    # `eau_surface`). PURE lecture (champ déjà tické par `tick_marais`) → aucun
    # impact golden. Champ optionnel côté vue (tolérance pré-0.5.27 → pas de marais).
    # MARE VIVANTE ① (0.6.2) : + `lame` (5ᵉ, `eau_surface` BRUTE, même sous
    # SEUIL_FLAQUE → la vue dessine le marnage progressif : vase luisante sous
    # une lame mince) et `glace` (6ᵉ, ∈ [0,1], `tick_glace`). Pré-0.6.2 : 4 champs.
    mmem = getattr(eco, "marais_memory", None)
    out["marais"] = [
        [r, c, round(mmem.data[r][c], 3), eco.est_marais(r, c),
         round(eco.eau_surface.data[r][c], 3), round(eco.glace.data[r][c], 3)]
        for r in range(eco.rows) for c in range(eco.cols)
        if mmem is not None and mmem.data[r][c] > MARAIS_OFF]
    # Carte de COUVERTURE DU SOL par tuile (sprint LUXURIANCE ①, D65 §2.1,
    # exposée au pont au ⑥) : liste CREUSE `[[r, c, cov], …]` des plots
    # tapissés (cov > SEUIL) — fraction du sol couverte par les strates
    # basses (sol+basse), scattée par `tick_couverture`. La vue en tire le
    # TAPIS (densité de rendu au sol ∝ cov, indice diégétique philo #5) : sol
    # nu ↔ sol tapissé se distingue à l'œil, sans chiffre. Liste creuse (patron
    # `litiere`/`eau_surface`) : la plupart des plots sont nus au démarrage.
    # PURE lecture (champ déjà tické par la boucle) → golden NEUTRE (le pont ne
    # réinjecte rien). Champ optionnel côté vue (tolérance pré-0.5.19 → pas de
    # tapis). `couverture_sol` peut être None sur un vieil eco (défaut lazy) →
    # garde-fou getattr.
    cov = getattr(eco, "couverture_sol", None)
    out["couverture"] = [
        [r, c, round(cov.data[r][c], 3)]
        for r in range(eco.rows) for c in range(eco.cols)
        if cov is not None and cov.data[r][c] > COUVERTURE_RENDU_SEUIL]
    # Carte de PAILLAGE par tuile (sprint équilibre invasion ⑧, D69) : liste
    # CREUSE `[[r, c, profondeur, nature], …]` des plots mulchés (profondeur
    # > 0). `profondeur` ∈ [0,1] = densité du mulch au sol (champ `eco.paillage`,
    # posé par le geste `pailler`, décru par `tick_paillage`) ; `nature` ∈
    # {paille, brf, aiguilles} = matériau du mulch (`nature_at`, ④) → la vue
    # teinte/texture par matériau ET module l'opacité par profondeur. Liste
    # creuse (patron `litiere`/`couverture`) : la plupart des plots sont NUS.
    # PURE lecture (champ déjà tické par `tick_paillage`) → golden NEUTRE : le
    # smoke ne paille jamais → paillage=0 partout → liste vide. Champ optionnel
    # côté vue (tolérance pré-0.5.20 → pas de mulch dessiné). `paillage` peut
    # être None sur un vieil eco (défaut lazy) → garde-fou getattr.
    pai = getattr(eco, "paillage", None)
    nat = getattr(eco, "paillage_nature", None)
    out["paillage"] = [
        [r, c, round(pai.data[r][c], 3), (nat[r][c] or "paille")]
        for r in range(eco.rows) for c in range(eco.cols)
        if pai is not None and pai.data[r][c] > 0.0]
    # Carte d'ALLÉLOPATHIE par tuile (sprint ALLÉLOPATHIE ⑥, kickoff §Pont) :
    # liste CREUSE `[[r, c, concentration], …]` des plots chargés en
    # allélochimiques (au-dessus du plancher de snap-à-0 ALLELO_FLOOR — la
    # plupart des plots sont propres → liste courte, patron `alarme`/
    # `couverture`). On expose `allelo_effectif` (allélopathie AMBIANTE +
    # autotoxicité du plot), MAIS sans espèce de référence → seul le champ
    # ambiant sort ici (l'autotox ④ est spécifique-espèce ; la vue F6 la lit
    # via son propre registre `get_field` "autotox"). Concrètement =
    # `allelopathie.at_plot`. La vue en tire l'indice DIÉGÉTIQUE de sol
    # PELÉ/nu sous un émetteur fort (halo sans levée autour du noyer/armoise,
    # philo #5 : pas de chiffre) et l'overlay F6 double la lecture technique.
    # PURE lecture (`eco.allelopathie` déjà tické par `tick_allelopathie` ①)
    # → golden NEUTRE : le pont ne réinjecte rien. Champ optionnel côté vue
    # (tolérance pré-0.5.29 → pas de halo). `allelopathie` peut être None sur
    # un vieil eco (défaut lazy) → garde-fou getattr.
    al = getattr(eco, "allelopathie", None)
    out["allelopathie"] = [
        [r, c, round(al.data[r][c], 4)]
        for r in range(eco.rows) for c in range(eco.cols)
        if al is not None and al.data[r][c] > ALLELO_FLOOR]
    # Carte de MÉMOIRE D'INOCULUM par tuile (sprint mémoire d'inoculum ④) :
    # liste CREUSE `[[r, c, famille_dominante, charge_totale], …]` des SEULS
    # plots viciés (`eco.inoculum.load` est un dict SPARSE indexé par plot →
    # un plot resté sain n'a AUCUNE entrée, la liste reste courte, patron
    # `marais`/`eau_surface`). Par plot chargé : la famille dominante (bucket
    # de plus forte charge — la maladie qui hiverne le plus) + la charge
    # totale toutes familles confondues (`inoculum.total`, sert la niche
    # molène ③ et la heatmap). La vue F6 en tire l'overlay « charge pathogène »
    # (sain → rouge/brun vicié). PURE lecture d'un champ déjà tické par
    # `tick_decay` → golden NEUTRE (le smoke ne vicie aucun plot → dict vide →
    # liste vide). Champ optionnel côté vue (tolérance pré-0.5.39 → pas
    # d'overlay). `inoculum` peut être absent d'un vieil eco → garde-fou getattr.
    ino = getattr(eco, "inoculum", None)
    plots_ino = []
    if ino is not None:
        for (r, c), bucket in ino.load.items():
            if not bucket:
                continue
            dominante = max(bucket, key=bucket.get)
            total = sum(bucket.values())
            plots_ino.append([r, c, dominante, round(total, 4)])
    out["inoculum"] = plots_ino
    # Couvertures POSÉES par le joueur (effondrement météo ③, tronçon ④ au
    # pont) : deux listes CREUSES par tuile `[[r, c, dose], …]` des plots
    # abrités — `couvert_pose` (écran physique du VOILE/CLOCHE, protège gel/
    # grêle) et `ombre_pose` (occultation de l'OMBRIÈRE, rafraîchit contre
    # canicule/sécheresse). Champs alloués PARESSEUSEMENT (None au repos → la
    # plupart des mondes n'ont RIEN de posé, liste vide, patron `paillage`).
    # La vue en tire les placeholders procéduraux (voile translucide / filet
    # d'ombre, CoverLayer). PURE lecture (aucun tick propre, cf.
    # couvertures_posees.py) → golden NEUTRE : le smoke ne pose aucune
    # couverture → champs None → listes vides. Champ optionnel côté vue
    # (tolérance pré-0.5.43). Garde-fou getattr (vieil eco sans le mixin).
    cvp = getattr(eco, "couvert_pose", None)
    out["couvert_pose"] = [
        [r, c, round(cvp.data[r][c], 3)]
        for r in range(eco.rows) for c in range(eco.cols)
        if cvp is not None and cvp.data[r][c] > 0.0]
    omp = getattr(eco, "ombre_pose", None)
    out["ombre_pose"] = [
        [r, c, round(omp.data[r][c], 3)]
        for r in range(eco.rows) for c in range(eco.cols)
        if omp is not None and omp.data[r][c] > 0.0]
    return out

