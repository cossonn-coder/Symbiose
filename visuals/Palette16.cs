// SYMBIOSE — Palette16.cs (SS² Palette, tronçon T1)
// PALETTE CENTRALE 16-bit (cap docs/rendu/pixelart/conception_rendu_pixelart.md §5).
//
// POURQUOI ce fichier : avant T1, les teintes de base du rendu étaient des
// littéraux `new Color("…")` ÉPARS dans PlantRenderer(.cs/.Palette/.Organs) et
// WorldView.Monde. Une palette SNES tient son cachet de sa CONTRAINTE : peu de
// couleurs, partagées, cohérentes. On les regroupe donc ici, NOMMÉES PAR RÔLE
// et rangées en rampes. C'est du PUR RANGEMENT : aucun hex ne change → apparence
// strictement identique (le golden est moteur-pur, non concerné ; le F5 doit voir
// la même image, hors le raffinage lignification-sur-l'âge du volet B).
//
// CE QUI N'EST PAS ICI (volontaire) : les constantes d'ÉCLAIRAGE (forces de
// hue-shift, teintes cibles chaud/froid, planchers de calotte) restent dans
// PlantRenderer.Palette.cs — ce sont des PARAMÈTRES d'ombrage, pas des couleurs
// de la palette. De même, les palettes PAR ESPÈCE (Organs.Palettes) et les autres
// acteurs (litière, vie macro, compost, butineurs) restent chez eux : T1 ne
// touche QUE les teintes listées au kickoff (bois/plante, symptômes, sol/maison).
//
// DÉCOMPTE : ~27 couleurs de base + le vocabulaire MATÉRIAU de la maison normande
// (granite/ardoise/brique, T3 RENDU AMBIANCE). Ce dernier est un bloc à part,
// justifié : le rendu détaillé pierre+ardoise exige ses propres 2-valeurs par
// matériau (moellon clair/médian, ardoise claire/médiane/sombre, brique cuite/
// ombre). L'éclairement par mur-monde (D35) MODULE ces teintes à l'usage plutôt
// que de les dupliquer par orientation. Les paires historiques proches
// (FondPierre↔FacadeEst d≈13 ; ToitEst↔ToitOuest d≈11) restent des DISTINCTIONS
// VOULUES (lisibilité de la rotation D35 du décor) : fusionner casserait
// l'apparence, ce que le kickoff interdit sans signalement.
//
// Tout est statique/déterministe (zéro Random, philo #3). Déclaratif : aucune
// logique — un fichier = une responsabilité (le vocabulaire chromatique).

using Godot;

namespace Symbiose
{
	internal static class Palette16
	{
		// === RAMPE BOIS (lignification vert-tendre → olive → brun) ============
		// Index par l'ÂGE du segment (cf. Lignification, PlantRenderer.Palette.cs).
		// Apex = pointe tendre, encore verte ; le bois mûr brunit.
		public static readonly Color BoisApex  = new Color("5ec46a"); // vert vif (apex tendre)
		public static readonly Color BoisOlive = new Color("8a7a38"); // stop intermédiaire (évite le gris-kaki mort)
		public static readonly Color BoisMur   = new Color("7a5230"); // brun ligneux plein
		public static readonly Color BoisMort  = new Color("6b5d4f"); // gris-brun éteint (squelette post-mortem)

		// === FEUILLAGE — silhouette & accents =================================
		public static readonly Color Couronne  = new Color("3f7a4e"); // masse de couronne (LOD silhouette)
		public static readonly Color Surbrillance = new Color("ffe66b"); // jaune clair (segment sous la souris)

		// === SYMPTÔMES COLORANTS (canal couleur, sémiologie D33) ==============
		// Une teinte par cause ; le moteur ne pose qu'un colorant dominant à la fois.
		public static readonly Color SymChlorose    = new Color("d8d24a"); // jaune inter-nervaire (carence ferrique)
		public static readonly Color SymAsphyxie    = new Color("6e6a4a"); // brun-vert terne (anoxie racinaire)
		public static readonly Color SymSecheresse  = new Color("b9a87a"); // beige désaturé, flétri
		public static readonly Color SymSenescence  = new Color("c4702a"); // jaune-rouge de fin de vie
		public static readonly Color SymMaladie     = new Color("8a6a4a"); // brun tacheté (cryptogamique)
		public static readonly Color SymOmbre       = new Color("c2c8a0"); // vert pâle délavé (étiolement)
		public static readonly Color SymAcclimatation = new Color("9db8b0"); // glauque bleu-gris (durcissement)
		// Herbivorie RACINAIRE (campagnol, sommet trophique ③) : flétrissure par la
		// BASE — la plante jaunit-brunit d'un jaune SALE, cause souterraine (collet
		// rongé/écorcé). Distinct du beige sec de la sécheresse (plus chaud, teinté de
		// brun de collet blessé) et du jaune franc de la chlorose : le tissu se meurt
		// par manque de sève montante, pas par carence assimilable.
		public static readonly Color SymRongeurRacinaire = new Color("b39244"); // jaune-brun sale (flétri par le collet)

		// === TEXTURE FOLIAIRE =================================================
		public static readonly Color PustuleMaladie = new Color("4a3320"); // tache brun foncé (semis cryptogamique)

		// === SOL (placeholders, teintes dominantes mesurées sur les PNG) ======
		public static readonly Color SolTerre    = new Color("967a64");
		public static readonly Color SolArgile   = new Color("cd7434");
		public static readonly Color SolSable    = new Color("f1e9bb");
		public static readonly Color SolInconnu  = new Color("777777");
		public static readonly Color FondPierre  = new Color("8d8881"); // chemins (fond de fenêtre)

		// === MAISON — façades (cycle horaire monde : nord, est, sud, ouest) ===
		// Sud = plein soleil (la plus claire), nord = jamais éclairée (la plus sombre).
		public static readonly Color[] Facades =
		{
			new Color("837c6f"), // 0 nord
			new Color("978f7d"), // 1 est
			new Color("b5ac99"), // 2 sud (plein soleil)
			new Color("a49b88"), // 3 ouest
		};
		// === MAISON — pans de toit (même éclairement monde, 4 pans) ===========
		public static readonly Color[] Toits =
		{
			new Color("a8a294"), // pan nord
			new Color("c2bcab"), // pan est
			new Color("d6cfbe"), // pan sud
			new Color("c9c2b1"), // pan ouest
		};
		// Ombre portée (maison) : vert-noir #071010 translucide (CASSÉ À L'ÉCRAN ③, ex-noir
		// α 0,16 ; brief DA : jamais de noir) — α 0,18 ≈ même assombrissement du sol.
		public static readonly Color Ombre = new Color(0.027f, 0.063f, 0.063f, 0.18f);

		// === MAISON NORMANDE — granite + ardoise (T3 RENDU AMBIANCE) ==========
		// Réf. Nico (maçon-couvreur, Cotentin/Montmartin-sur-Mer). PAS de
		// colombages/chaume : maison de PIERRE et d'ARDOISE. Chaque teinte est
		// une COULEUR DE MATÉRIAU en plein jour (référence sud) ; l'éclairement
		// par mur-monde (D35) est appliqué à l'usage par un facteur de valeur —
		// on ne dédouble donc pas la rampe par orientation, on la module.
		// Granite gris-bleu à reflets roux : 2 valeurs de moellon + joint chaux.
		public static readonly Color GraniteMur      = new Color("7d8188"); // moellon gris-bleu (valeur médiane)
		public static readonly Color GraniteMurClair = new Color("969aa0"); // moellon éclairé (facette au soleil)
		public static readonly Color GraniteRoux     = new Color("8a7d70"); // moellon à reflet roux (variété)
		public static readonly Color GraniteClair    = new Color("b8b2a4"); // granite clair : chaînages, encadrements de baies
		public static readonly Color JointChaux      = new Color("cec7b6"); // joints de chaux clairs beurrés
		// Ardoise gris-bleu foncé : 2 valeurs d'écaille + le rang de recouvrement.
		public static readonly Color Ardoise         = new Color("454b55"); // écaille d'ardoise (valeur médiane)
		public static readonly Color ArdoiseClair    = new Color("5c636e"); // écaille éclairée (reflet bleuté)
		public static readonly Color ArdoiseSombre   = new Color("353a42"); // recouvrement / rang d'ombre
		// Brique orangée de la souche de cheminée + menuiseries sombres.
		public static readonly Color BriqueOrange    = new Color("a85f3c"); // brique cuite (souche cheminée)
		public static readonly Color BriqueSombre    = new Color("7c4529"); // joint / ombre de brique
		public static readonly Color MenuiserieSombre = new Color("3a2f26"); // dormant sombre (portes, fenêtres)
		public static readonly Color VitreSombre     = new Color("2b3238"); // verre à petits carreaux (fond)

		// === DÉCOR D'AMBIANCE — ossature (T4 RENDU AMBIANCE) ==================
		// Teintes de BASE des zones hors-jardin (backdrop cosmétique, §5.1).
		// Chaque motif = 2 valeurs (lisière claire / fond) pour le volume pixel-
		// art ; le DÉTAIL (arbres, reflets, redans) est peint par-dessus en T5.
		public static readonly Color DecorPrairie       = new Color("6e9a4a"); // prairie fleurie (fond)
		public static readonly Color DecorPrairieClair  = new Color("83af58"); // prairie éclairée (lisière)
		// T1 lisibilité décor : fond poussé PLUS SOMBRE/FROID pour que les cimes
		// éclairées (calotte + accent de cime) tranchent — avant, hêtre ≈ fond =
		// tache verte plate. Le fond est désormais sous TOUS les feuillages, même
		// leur masse d'ombre (feuillage ×0.75, cf. DrawVolumeBlob).
		public static readonly Color DecorForetFond     = new Color("223a2b"); // forêt profonde (vert sombre-froid)
		public static readonly Color DecorForetLisiere  = new Color("46764a"); // lisière (vert moyen)
		public static readonly Color DecorEau           = new Color("3f6f8e"); // rivière (bleu-gris)
		public static readonly Color DecorEauBerge      = new Color("6f9a86"); // berge herbeuse (vert-eau)
		public static readonly Color DecorRoche         = new Color("8a8073"); // falaise (gris-brun)
		// T3 lisibilité décor : le SOMMET de la falaise est un plateau HERBEUX (le
		// surplomb rocheux se lit à la face verticale, pas au sommet) → teinte
		// poussée vers un vert-gris sec d'herbe rase, distincte de la roche grise.
		public static readonly Color DecorRocheHaut     = new Color("8a9668"); // plateau végétalisé (herbe rase sèche)
		// === CHEMINS ENHERBÉS (gazon inter-tuiles, T4) =======================
		// Le gris pierre FondPierre du fond de fenêtre bascule en vert gazon.
		public static readonly Color GazonChemin        = new Color("6f9350"); // gazon des chemins (grain léger)

		// === DÉCOR D'AMBIANCE — motifs détaillés (T5 RENDU AMBIANCE) ==========
		// Silhouettes d'arbres adultes par essence, eau + reflets, roche étagée,
		// prairie fleurie. Chaque feuillage a SA valeur médiane ; le volume 2
		// valeurs (calotte éclairée) est fabriqué à l'usage par hue-shift, pas
		// dupliqué ici (cohérent avec le rendu des plantes, philo pixel-art).
		// -- Feuillages par essence (houppiers du décor) --
		public static readonly Color FeuillageChene    = new Color("44703f"); // chêne : vert moyen dense
		public static readonly Color FeuillageHetre    = new Color("35603a"); // hêtre : vert profond de hêtraie
		public static readonly Color FeuillageBouleau  = new Color("74a250"); // bouleau : vert clair léger
		public static readonly Color FeuillageCharme   = new Color("4f7d47"); // charme : vert moyen bocager
		public static readonly Color FeuillageSapin    = new Color("2c4d47"); // sapin : vert-bleu sombre
			// Accent de CIME (T1) : vert eclaire chaud du sommet des houppiers
			// (soleil SO). Distinct des feuillages car la calotte du volume plafonne
			// a x1.25 (Assombrir borne) -> il faut une VRAIE couleur claire pour que
			// la skyline foret bosselee tranche contre le jardin.
			public static readonly Color DecorForetCime    = new Color("a6c56e"); // cime au soleil
		// -- Écorces (troncs du décor) --
		public static readonly Color EcorceBrune       = new Color("5a4632"); // tronc brun (chêne/hêtre/charme/sapin)
		public static readonly Color EcorceBouleau     = new Color("d3d0c6"); // écorce blanche du bouleau
		public static readonly Color EcorceLenticelle  = new Color("35322c"); // chevrons sombres du bouleau
		// -- Eau de rivière (T2 : berge franche + 2 valeurs d'eau + reflet) --
		public static readonly Color EauProfonde       = new Color("35617f"); // eau profonde (bleu-gris sombre)
		public static readonly Color EauSurface        = new Color("4a7d9c"); // eau de surface (valeur claire, damier)
		public static readonly Color EauReflet         = new Color("6fa6bf"); // reflet de ciel (bleu clair, streak courant)
		public static readonly Color BergeGalet        = new Color("9a8f76"); // berge de galets/limon (bord franc du lit)
		// -- Roche de falaise (3 valeurs de redans étagés) --
		public static readonly Color RocheClair        = new Color("aca291"); // strate éclairée / éboulis (contraste creusé T3)
		public static readonly Color RocheMedian        = new Color("7c7264"); // pan médian
		public static readonly Color RocheOmbre        = new Color("4c453a"); // strate d'ombre / pied de face (assombri T3)
		// -- Petites fleurs de la prairie (semis déterministe) --
		public static readonly Color FleurPrairieBlanc = new Color("e7e3d2"); // marguerites (points clairs)
		public static readonly Color FleurPrairieJaune = new Color("e6c24a"); // boutons-d'or (points jaunes)

		// === PALETTE MAÎTRE SNES — 34 couleurs (jardin vivant T1) =============
		// LA contrainte finale de l'écran : le shader `palette_snes.gdshader`
		// ramène CHAQUE pixel du SubViewport monde à l'une de ces 32 couleurs (la
		// plus proche en OKLab), avec un tramage Bayer 4×4 entre les deux plus
		// proches. Les teintes ci-dessus restent les couleurs « d'intention » des
		// dessinateurs ; celles-ci sont le NUANCIER réellement affiché.
		// 📖 Pourquoi des rampes à hue-shift : une rampe SNES ne va pas du vert au
		// noir, elle glisse vers le FROID (bleu) dans l'ombre et vers le CHAUD
		// (jaune) dans la lumière — le relief se lit sans noircir. Rampes
		// partagées par tous les acteurs (feuillage = herbe = décor) → cohérence.
		// Calées sur les couleurs dominantes mesurées (k-means sur captures VM T0).
		// Entrées NOMMÉES de la palette maître (curseur, losange de survol) —
		// déclarées AVANT le tableau (ordre d'initialisation statique C#).
		public static readonly Color MaitreSombre  = new Color("2e3038"); // contour (ardoise nuit)
		public static readonly Color MaitreGranite = new Color("b5b0a2"); // ombre claire (granite chaud)
		public static readonly Color MaitreBlanc   = new Color("f2efe6"); // blanc chaux
		public static readonly Color MaitreJaune   = new Color("e6c24a"); // jaune fleur
		// Nombre d'ACCENTS en fin de Maitre (fleurs/fruits) : couleurs franches,
		// jamais partenaires de tramage (évite la moucheture rouge sur l'argile).
		public const int MaitreAccents = 4;
		public static readonly Color[] Maitre =
		{
			// Verts (8) : forêt profonde froide → pousse tendre chaude → crème verdi (sable herbu)
			new Color("1c3328"), new Color("2f5139"), new Color("44703f"), new Color("5f8a47"),
			new Color("709354"), new Color("82ac5a"), new Color("a6c56e"), new Color("d2d3a0"),
			// Terre / bois (5) : humus froid → terre sèche
			new Color("33261f"), new Color("5a4030"), new Color("836556"), new Color("967961"),
			new Color("b39d85"),
			// Argile / brique (4)
			new Color("8a3f26"), new Color("a8462c"), new Color("c77137"), new Color("e8a060"),
			// Sable / crème (3)
			new Color("c9c29a"), new Color("e3dbb3"), new Color("f5edc6"),
			// Pierre / ardoise (6) : gris bleutés (ombre) → gris-beige (flancs de sol) → granite chaud
			MaitreSombre, new Color("3f4550"), new Color("5a616c"), new Color("8a8e93"),
			new Color("918a72"), MaitreGranite,
			// Blanc (1) : écorce de bouleau, chaux, reflets
			MaitreBlanc,
			// Eau / ciel (3)
			new Color("35617f"), new Color("5f94b8"), new Color("a8cfe6"),
			// Fleurs / fruits (4) : rouge, jaune, rose, violet — ACCENTS, toujours en
			// FIN de tableau (le shader ne les trame jamais, cf. MaitreAccents).
			new Color("b8323a"), MaitreJaune, new Color("de8ab0"), new Color("7c5cb0"),
		};
	}
}
