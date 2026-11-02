// SYMBIOSE — PlantRenderer.Arbres.cs (partial, sprint AUTOMNE VISIBLE ④)
// RECETTES DES 11 ARBRES : ce que docs/vegetal/croissance/fiches_arbres.md demande au
// rendu et qui n'est ni une couleur d'organe (`Palettes`, Organs.cs, couleurs d'automne
// comprises) ni une forme de limbe (`LeafProfiles`, Leaf.cs).
//
// 📖 Pédagogie : le PORT d'un arbre (hauteur, largeur, étages) vient des vrais segments du
// moteur (tronçon ②). Depuis PLANTE ASSEMBLÉE ⑤, les paliers bas dessinent ces segments :
// la vue n'invente donc aucune couronne. La recette ne règle que ce que le moteur ne porte
// pas : le grain du feuillage, ce qui pend, la matière du tronc. `Couronne()` (Paliers.cs)
// ne dessine plus rien : elle sert au picking et à la boîte de cuisson, d'où ses ratios ici.
//
// Valeurs de jeu, à confirmer au F5 ; purement visuel, golden non concerné.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer : Node2D
	{
		/// <summary>Recette d'un arbre. Couronne (ratios de la hauteur / du rayon réels) :
		/// CentreZ, Largeur, DemiHaut. TailleFeuille : limbe ∝ fiche (1 = feuille de 5-10 cm).
		/// CranTouffe : grain du feuillage aux paliers bas, en crans de `KitTailles`.
		/// RetombeeCm : ce qui pend (rameaux pleureurs). Ecorce : tronc et charpentières.</summary>
		private readonly record struct RecetteArbre(
			float CentreZ, float Largeur, float DemiHaut,
			float TailleFeuille, int CranTouffe, float RetombeeCm, Color Ecorce);

		private static readonly Dictionary<string, RecetteArbre> RecettesArbres = new()
		{
			["AppleTree"]    = new(0.62f, 1.00f, 0.40f, 1.0f,  0,  0f, new Color("7a6a58")), // étalé ; gris-brun écailleux
			["CherryTree"]   = new(0.62f, 0.90f, 0.38f, 1.2f,  0,  0f, new Color("7a3f34")), // ovoïde étagé ; brun-rouge luisant
			["WalnutTree"]   = new(0.66f, 1.05f, 0.34f, 1.6f,  1,  0f, new Color("a09c90")), // arrondi large ; gris argent
			["OakTree"]      = new(0.66f, 1.10f, 0.32f, 1.15f, 0,  0f, new Color("6a5e4e")), // étalé tortueux ; gris-brun crevassé
			["BeechTree"]    = new(0.60f, 0.90f, 0.42f, 1.0f,  0,  0f, new Color("a8a8a0")), // ovoïde dense ; gris clair lisse
			["BirchTree"]    = new(0.58f, 0.75f, 0.42f, 0.7f, -1, 18f, new Color("e4e2d8")), // dressé pleureur ; blanc
			["HornbeamTree"] = new(0.60f, 0.90f, 0.40f, 1.0f,  0,  0f, new Color("8a8a80")), // ovoïde ; gris lisse
			["Alder"]        = new(0.52f, 0.70f, 0.48f, 0.9f,  0,  0f, new Color("4f3f30")), // conique ; brun sombre
			["Willow"]       = new(0.62f, 1.00f, 0.38f, 1.0f, -1, 12f, new Color("7a6e5c")), // arrondi souple ; gris-brun
			["Fig"]          = new(0.50f, 1.05f, 0.50f, 1.7f,  1,  0f, new Color("a09e90")), // buissonnant ; gris clair
			["FirTree"]      = new(0.50f, 0.70f, 0.50f, 0.6f, -1,  0f, new Color("8e9088")), // conique étroit ; gris argent
		};

		// Épaisseur au-delà du rameau feuillu où le bois a pris toute son écorce (cm).
		private const float EcorcePleineCm = 2.5f;

		private bool RecetteDeLaPlante(out RecetteArbre r)
		{
			r = default;
			return _structure != null && RecettesArbres.TryGetValue(_structure.SpeciesName, out r);
		}

		private float TailleFeuilleEspece => RecetteDeLaPlante(out var r) ? r.TailleFeuille : 1f;
		private float RetombeeCm => RecetteDeLaPlante(out var r) ? r.RetombeeCm : 0f;

		/// <summary>Le bois `bois` tiré vers l'écorce de l'espèce selon l'épaisseur du
		/// segment : brindilles inchangées, tronc pleinement écorcé (le bouleau est blanc
		/// au tronc, sombre aux rameaux, comme la fiche).</summary>
		private Color AvecEcorce(Color bois, Segment s)
		{
			if (!RecetteDeLaPlante(out var r)) return bois;
			float t = Mathf.Clamp((s.ThicknessCm - LeafMaxThickCm) / EcorcePleineCm, 0f, 1f);
			return bois.Lerp(r.Ecorce, t * Lignification(s));
		}
	}
}
