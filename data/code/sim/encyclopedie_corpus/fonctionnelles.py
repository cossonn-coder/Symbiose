"""
SYMBIOSE — sim/encyclopedie_corpus/fonctionnelles.py
Fiches des espèces ajoutées pour INCARNER une mécanique : trio clonal
(LUXURIANCE ⑤), émetteurs allélopathiques (ALLÉLOPATHIE ⑤), sources de mulch
(équilibre invasion ⑤), grimpantes (Grimpantes ⑤).
DONNÉE éditoriale pure — aucune logique, aucun import moteur. Éclaté de
l'ex-monolithe `sim/encyclopedie_corpus.py` (402 LDC, zone rouge) au refactor de
clôture du sprint PÉRIPHÉRIE ; `__init__.py` réassemble `FICHES` dans le MÊME
ordre, l'API publique lue par les appelants est inchangée.

Voix « naturaliste qui observe » (3ᵉ personne, descriptive et factuelle), 3 niveaux
par entrée — cf. le docstring du paquet pour le contrat complet.
"""
from __future__ import annotations

FICHES_FONCTIONNELLES: dict[str, dict[int, str]] = {
    # === Trio clonal (sprint LUXURIANCE ⑤) ===
    "framboisier": {
        1: "Touffe de cannes dressées épineuses, feuilles composées vert clair, "
           "fleurs blanches puis framboises rouges.",
        2: "Sous-arbrisseau vivace qui s'étend par DRAGEONS : de courts rejets "
           "percent le sol tout près de la souche mère et forment peu à peu un "
           "fourré serré. Le rejet ne prend qu'à la lumière du sol — la touffe "
           "s'épaissit sur place sans coloniser tout le terrain. Fleurs mellifères, "
           "fruits fondants appréciés de la faune.",
        3: "Fourré nourricier qui se densifie de lui-même par drageonnage tant que "
           "la lumière atteint son pied : un massif fruitier qui s'entretient seul, "
           "resserré autour de la mère (≠ le rhizome qui file loin). Ses fleurs "
           "nourrissent les butineurs, ses framboises oiseaux et petits mammifères "
           "qui dispersent ses graines. Bon brise-vue caduc en lisière ; à contenir "
           "en bordure pour l'empêcher de gagner la planche voisine.",
    },
    "bambou": {
        1: "Chaumes verts dressés et cannelés en bosquet dense, feuillage léger "
           "bruissant, persistant l'hiver.",
        2: "Graminée géante vivace qui gagne du terrain par RHIZOMES TRAÇANTS : sous "
           "terre, des tiges courent VITE et LOIN, hors de la touffe, et relèvent des "
           "chaumes à distance — y compris sous l'ombre, car le rhizome porte sa "
           "réserve. Il ne fait presque jamais de graine : tout se joue sous la "
           "surface. C'est le champion de l'expansion clonale.",
        3: "Brise-vent et écran persistants remarquables, mais colonisateur "
           "REDOUTABLE : ses rhizomes traversent une planche en une saison, sous "
           "l'ombre comme au soleil, là où les autres traçantes caleraient. Rien ne "
           "l'arrête sinon la place elle-même — un sol déjà couvert le freine. À "
           "cloisonner absolument (barrière anti-rhizome enterrée, bac) sous peine de "
           "voir le bosquet avaler le jardin. Ses racines fibreuses assèchent le sol "
           "au voisinage (compétition hydrique des graminées).",
    },
    "violette": {
        1: "Tapis ras de petites feuilles en cœur, fleurs violettes parfumées "
           "portées bas, très précoces au printemps.",
        2: "Couvre-sol vivace de sous-bois, SCIAPHILE — elle prospère à l'ombre où "
           "les héliophiles calent. Elle tapisse par courts STOLONS, mais le stolon "
           "réclame un peu de lumière au sol pour enraciner sa fille : elle garnit "
           "surtout les clairières et lisières, moins le cœur le plus sombre. "
           "Floraison mellifère parmi les toutes premières de l'année.",
        3: "Tapis d'ombre précieux : il habille le pied des arbres et des haies, "
           "limite le sol nu là où peu de plantes tiennent, et offre l'une des "
           "premières tables de nectar au sortir de l'hiver (bourdons fondateurs, "
           "abeilles précoces). Son tapissage stolonifère s'auto-limite aux zones "
           "assez claires — un couvre-sol discret qui ne verrouille jamais tout. "
           "Comestible et médicinale (fleurs).",
    },

    # === Émetteurs allélopathiques (sprint ALLÉLOPATHIE ⑤) ===
    "armoise": {
        1: "Grande touffe dressée aux feuilles découpées vert sombre dessus, "
           "argentées dessous, dégageant une odeur camphrée quand on les froisse.",
        2: "Vivace rustique presque increvable des friches et bords de chemin, "
           "anémophile (capitules verdâtres discrets, pollen au vent — aucun nectar). "
           "Aromatique et médicinale ancienne. Elle repart chaque printemps d'une "
           "souche ligneuse et supporte tout : sécheresse, sols pauvres, piétinement.",
        3: "PUISSAMMENT ALLÉLOPATHE : ses racines et son feuillage libèrent des "
           "composés qui inhibent la levée et la croissance des plantes autour d'elle "
           "— elle « fait le vide » et règne seule sur sa tache. À tenir à distance du "
           "potager (peu de voisines la supportent) ; utile en revanche pour tenir "
           "propre une bordure ou décourager une adventice tenace. Elle-même y est "
           "insensible. Le sol garde longtemps sa mémoire chimique là où elle a régné.",
    },
    "seigle": {
        1: "Touffe d'herbe dressée aux longues feuilles bleutées, puis épis fins "
           "barbus portés haut sur des chaumes souples.",
        2: "Céréale annuelle LA PLUS RUSTIQUE : semée dense à l'automne, sa graine "
           "lève au froid quand rien d'autre ne démarre, et le couvert protège le sol "
           "nu tout l'hiver. Anémophile (pollen au vent). Racines fibreuses "
           "assoiffées, comme toutes les graminées — mais tolérante à l'allélopathie.",
        3: "ENGRAIS VERT ALLÉLOPATHIQUE — le couvert nettoyant du permaculteur : ses "
           "racines exsudent des composés qui ÉTOUFFENT chimiquement la levée des "
           "adventices dicotylédones, SANS le gêner lui-même (les graminées "
           "encaissent). On le FAUCHE au printemps : sa paille couvre le sol et "
           "l'effet résiduel garde la planche nette quelques semaines — on plante "
           "DANS le mulch de seigle. Cultivé non pour la table mais pour la terre.",
    },

    # === Sources de mulch (sprint équilibre invasion ⑤) ===
    "ble": {
        1: "Touffe d'herbe dressée aux longues feuilles rubanées, puis épis barbus "
           "qui dorent et se courbent à maturité.",
        2: "Céréale annuelle rustique : sa graine lève dès que le sol s'est un peu "
           "radouci, sans attendre la chaleur. Elle talle (se multiplie en tiges), "
           "monte en chaume puis en épi. Anémophile — son pollen voyage au vent, "
           "elle ne nourrit aucun butineur. Racines fibreuses assoiffées (graminée).",
        3: "Après la moisson du grain, sa PAILLE — le chaume sec — est le paillis de "
           "référence du maraîcher : léger, aéré, il couvre le sol nu, étouffe les "
           "levées d'adventices, garde l'humidité et se décompose vite en humus. La "
           "cultiver, c'est produire sa propre couverture de sol pour l'an prochain.",
    },
    "chanvre": {
        1: "Grande tige unique dressée, feuilles palmées à folioles dentées, "
           "silhouette élancée qui dépasse tout le potager en une saison.",
        2: "Annuelle à croissance fulgurante et fibre très robuste ; dioïque et "
           "anémophile (pieds mâles et femelles séparés, pollen au vent). Son "
           "feuillage dense ombre fortement le sol sous lui. Levée au mitan du "
           "printemps, sur sol réchauffé.",
        3: "Plante-service étouffe-adventices : par sa vitesse et son ombrage dense, "
           "elle couvre le sol nu et prive de lumière les herbes indésirables — un "
           "couvert vivant avant d'être un couvert mort. Sa tige rouie donne une "
           "PAILLE de fibre durable, plus lente à se décomposer que celle des "
           "céréales — un paillis de longue tenue.",
    },
    "sapin": {
        1: "Conifère au houppier conique sombre, aiguilles plates persistantes, "
           "cônes dressés ; vert en toute saison, même sous la neige.",
        2: "Pérenne PERSISTANT (jamais nu) à croissance lente et longévité "
           "séculaire ; anémophile (cônes). Contrairement aux fruitiers caducs, il "
           "projette son ombre TOUTE l'année — utile au nord, gênant au sud. Aime "
           "les sols plutôt ACIDES ; sa litière d'aiguilles acidifie le sol sous lui.",
        3: "Deux ressources pour le sol : ses AIGUILLES tombées font un paillis "
           "ACIDIFIANT, légèrement allélopathique — à réserver au pied des "
           "acidophiles (myrtille), à éviter ailleurs ; ses rameaux ligneux broyés "
           "donnent un BRF qui nourrit les champignons du sol. Brise-vent persistant "
           "et abri hivernal pour la faune quand tout le reste est nu.",
    },

    # === Grimpantes (sprint Grimpantes ⑤) ===
    "lierre": {
        1: "Liane à feuilles luisantes palmées, tiges hérissées de crampons, baies "
           "noires en boules.",
        2: "Vivace ligneuse sempervirente, sciaphile — prospère à l'ombre où les "
           "autres calent. Ses crampons adhésifs lui font escalader murs et troncs "
           "sans qu'on l'y aide. Floraison très tardive, à l'automne. Sans appui, "
           "elle rampe au sol.",
        3: "Tapisse le sol nu et les parois au nord ; son feuillage d'hiver et son "
           "ombre dense abritent oiseaux et insectes. Sa floraison d'arrière-saison "
           "est l'une des dernières tables des abeilles ; ses baies nourrissent la "
           "faune quand tout est fané.",
    },
    "jasmin": {
        1: "Grimpante aux tiges souples arquées, feuilles composées, fleurs blanches "
           "étoilées très parfumées.",
        2: "Vivace sarmenteuse : ses tiges ne s'agrippent pas seules — il faut les "
           "palisser sur un support, sinon elles s'étalent sans monter. Floraison "
           "estivale abondante, embaumant surtout le soir. Semi-caduque, elle dort "
           "l'hiver.",
        3: "Sur un treillis ou une pergola, elle habille et parfume l'espace ; son "
           "nectar nourrit abeilles et papillons, en particulier au crépuscule. Se "
           "conduit par palissage — c'est la main du jardinier qui l'élève.",
    },
}
