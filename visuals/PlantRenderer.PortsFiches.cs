// SYMBIOSE — PlantRenderer.PortsFiches.cs (partial, sprint FORMES DES PLANTES ②)
// La TABLE des ports : une ligne par espèce, clé = nom de classe Python. Chaque ligne traduit
// sa fiche de docs/vegetal/croissance/fiches_herbacees.md ; les chiffres y sont `[choix]`.
// Aucune fonction par espèce : une espèce qui en réclamerait une serait un 8ᵉ port à justifier.
// Les palettes absentes de PlantRenderer.Organs.cs sont ici, pour ne pas faire grossir ce fichier.
//
// 📖 Pédagogie (C# pour un œil C) : un `sealed record` à paramètres nommés se lit comme un
// initialiseur désigné de struct en C (`.rayon = 20`), la table reste lisible en colonnes.
// Le constructeur `static` s'exécute une fois, après TOUS les champs statiques des partials :
// il complète donc sans risque le dictionnaire `Palettes`, déclaré dans un autre fichier.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private enum FormePort { Rosette }   // ③ tiges, ④ chaumes, tapis, buissons, rampante, ⑥ volubile
		private enum FormeFeuille { Dentee, Spatule, Lobee, Ovale, Cuillere, Plume, Ruban }
		private enum FormeTete { Capitule, Bouquet, Chapelet, Epi, Ombelle, Boule, Grappe }
		private enum MarqueFeuille { Aucune, Duvet, Gouttes, Pli }

		/// <summary>Une ligne de table : ce qu'il faut pour dessiner un port. Hauteurs en cm ;
		/// `HauteurAdulteCm` = `height_cm` moteur du stade feuillé adulte (taille du pied) ;
		/// `Dressee` 0 plaquée → 1 dressée ; `LargeurFeuille` = demi-largeur / longueur ;
		/// `StadesHampe` null = la hampe suit la floraison seule ; `MelangeFruit` tire le
		/// limbe vers le fruit mûr de la palette (drosera) ; `Pied` = couleur vue au collet.</summary>
		private sealed record FichePort(
			FormePort Forme, float RayonCm, float HautFeuillesCm, float HauteurAdulteCm, int Feuilles,
			FormeFeuille Feuille, float LargeurFeuille, float Dressee, FormeTete Tete, float TeteCm,
			int Hampes, float EpaisseurTigeCm, string[] StadesHampe = null, int FeuillesHampe = 0,
			float MelangeFruit = 0f, MarqueFeuille Marque = MarqueFeuille.Aucune, string Pied = null);

		private static readonly Dictionary<string, FichePort> FichesPort = new()
		{
			// --- Rosettes ② ---------------------------------------------------------------
			["Taraxacum"] = new(FormePort.Rosette, RayonCm: 20f, HautFeuillesCm: 5f, HauteurAdulteCm: 30f, Feuilles: 14,
				FormeFeuille.Dentee, LargeurFeuille: 0.2f, Dressee: 0f, FormeTete.Capitule, TeteCm: 3f, Hampes: 4, EpaisseurTigeCm: 0.5f),
			["CornSalad"] = new(FormePort.Rosette, RayonCm: 10f, HautFeuillesCm: 9f, HauteurAdulteCm: 12f, Feuilles: 13,
				FormeFeuille.Spatule, LargeurFeuille: 0.34f, Dressee: 0.4f, FormeTete.Bouquet, TeteCm: 1.6f, Hampes: 3, EpaisseurTigeCm: 0.3f,
				StadesHampe: new[] { "mature" }),
			["BursaPastoris"] = new(FormePort.Rosette, RayonCm: 8f, HautFeuillesCm: 2f, HauteurAdulteCm: 25f, Feuilles: 10,
				FormeFeuille.Lobee, LargeurFeuille: 0.26f, Dressee: 0f, FormeTete.Chapelet, TeteCm: 1.2f, Hampes: 2, EpaisseurTigeCm: 0.3f,
				StadesHampe: new[] { "adulte", "mature" }),
			["Molene"] = new(FormePort.Rosette, RayonCm: 30f, HautFeuillesCm: 8f, HauteurAdulteCm: 20f, Feuilles: 11,
				FormeFeuille.Ovale, LargeurFeuille: 0.34f, Dressee: 0f, FormeTete.Epi, TeteCm: 3.5f, Hampes: 1, EpaisseurTigeCm: 3f,
				StadesHampe: new[] { "hampe", "mature" }, FeuillesHampe: 8, Marque: MarqueFeuille.Duvet),
			["Drosera"] = new(FormePort.Rosette, RayonCm: 6f, HautFeuillesCm: 1.5f, HauteurAdulteCm: 10f, Feuilles: 9,
				FormeFeuille.Cuillere, LargeurFeuille: 0.26f, Dressee: 0f, FormeTete.Grappe, TeteCm: 0.8f, Hampes: 1, EpaisseurTigeCm: 0.2f,
				MelangeFruit: 0.8f, Marque: MarqueFeuille.Gouttes),
			["Carrot"] = new(FormePort.Rosette, RayonCm: 14f, HautFeuillesCm: 18f, HauteurAdulteCm: 18f, Feuilles: 13,
				FormeFeuille.Plume, LargeurFeuille: 0.22f, Dressee: 0.7f, FormeTete.Ombelle, TeteCm: 6f, Hampes: 1, EpaisseurTigeCm: 0.6f,
				StadesHampe: new[] { "ombelle", "mature" }, Pied: "d8782a"),
			["Garlic"] = new(FormePort.Rosette, RayonCm: 12f, HautFeuillesCm: 25f, HauteurAdulteCm: 25f, Feuilles: 8,
				FormeFeuille.Ruban, LargeurFeuille: 1.5f, Dressee: 1f, FormeTete.Boule, TeteCm: 2.8f, Hampes: 1, EpaisseurTigeCm: 0.6f,
				StadesHampe: new[] { "hampe", "mature" }, Marque: MarqueFeuille.Pli, Pied: "ece6d8"),
		};

		// Espèces du catalogue sans palette (limbe, fleur, fruit vert, fruit mûr).
		static PlantRenderer()
		{
			Palettes["Taraxacum"] = new OrganPalette("4f9a3c", "f0c21e", "8aa858", "f2f0e8");       // pissenlit : vert franc, capitule d'or, aigrette blanche
			Palettes["Molene"] = new OrganPalette("9aa88c", "e8c82e", "8a9a70", "6a5236");          // molène : gris-vert argenté, épi jaune, capsule brune
			Palettes["BursaPastoris"] = new OrganPalette("5f8a48", "f0efe6", "9aa860", "a89a58");   // bourse-à-pasteur : vert terne, fleur blanche, silicule
			Palettes["Basil"] = new OrganPalette("4a9c3e", "f2efe6", "6fae45", "6a7a40");           // basilic : vert franc luisant
			Palettes["Mint"] = new OrganPalette("3f8f55", "c8a8d8", "6fa864", "7a8a60");            // menthe : vert bleuté, épi lilas
			Palettes["Raspberry"] = new OrganPalette("4a8540", "f0ece0", "c0a060", "c0283e");       // framboisier : fruit rouge
			Palettes["RunningBamboo"] = new OrganPalette("5a9a48", "c8c888", "8aa858", "a89a58");   // bambou : vert clair
			Palettes["Wheat"] = new OrganPalette("6a9a48", "c8b878", "a8b060", "d0b050");           // blé : épi doré
			Palettes["Rye"] = new OrganPalette("5f9458", "a89a78", "a8b070", "c8a860");             // seigle : vert bleuté, épi paille
			Palettes["Hemp"] = new OrganPalette("4a8a3c", "b8c070", "7a9a50", "7a7a48");            // chanvre : vert franc, fleurs ternes
			Palettes["PoaAnnua"] = new OrganPalette("62a850", "c8c8a0", "9ab070", "b0a870");        // pâturin : vert tendre
			Palettes["MedicagoLupulina"] = new OrganPalette("4f8f40", "e8d030", "5a8a40", "2a2a24"); // minette : fleur jaune, gousse noire
			Palettes["Ivy"] = new OrganPalette("2f6a3a", "c0c060", "3a5a3a", "22263a");             // lierre : vert sombre, baie noire
			Palettes["Jasmine"] = new OrganPalette("3f8a48", "f6f2ea", "7a9a50", "3a3a40");         // jasmin : vert franc, fleur blanche
		}
	}
}
