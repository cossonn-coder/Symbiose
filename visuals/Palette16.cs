// SYMBIOSE — Palette16.cs (SS² Palette, tronçon T1)
// PALETTE CENTRALE 16-bit (cap docs/conception/CONCEPTION_RENDU_PIXELART.md §5).
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
// DÉCOMPTE : 27 couleurs nommées (cible « ~24 SNES »). Aucune fusion appliquée —
// les deux seules paires proches (FondPierre↔FacadeEst d≈13 ; ToitEst↔ToitOuest
// d≈11) sont des DISTINCTIONS VOULUES (lisibilité de la rotation D35 du décor,
// cf. commentaires d'origine) : fusionner casserait l'apparence, ce que le
// kickoff interdit sans signalement. On reste donc à 27, proche de la cible.
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
		// Ombre portée (maison) : noir translucide, non opaque (assombrit le sol).
		public static readonly Color Ombre = new Color(0f, 0f, 0f, 0.16f);
	}
}
