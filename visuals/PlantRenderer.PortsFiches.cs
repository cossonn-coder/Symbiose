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
		private enum FormePort { Rosette, Tige }   // ④ chaumes, tapis, buissons, rampante, ⑥ volubile
		private enum FormeFeuille { Dentee, Spatule, Lobee, Ovale, Cuillere, Plume, Ruban, Coeur, Scie, Lanceolee, Palmee }
		private enum FormeTete { Capitule, Bouquet, Chapelet, Epi, Ombelle, Boule, Grappe, Soleil, Etoile, Pendante }
		private enum MarqueFeuille { Aucune, Duvet, Gouttes, Pli, Eclat, Gaufre, Revers }

		/// <summary>La grammaire du port tige (PlantRenderer.PortTige.cs). `Axes` tiges partent du
		/// pied, sur `EcartPied` du rayon, et s'écartent en montant de `Evase` du rayon. Feuilles
		/// entre `BasNu` et 1-`HautNu` de l'axe, de `FeuilleBasCm` à `FeuilleHautCm` de long,
		/// `Penche` &lt; 0 elles retombent, en paires ou alternes. `Rameaux` par axe dès `RameauDes`,
		/// `RameauLong` du rayon, multipliés par `RameauFin` au sommet, montant de `RameauMonte`
		/// cm par cm. `TetesAisselle` : têtes aussi aux nœuds du haut. `EpiCm` : longueur de ce
		/// qui porte une tête allongée. Le nombre de nœuds par axe est `Feuilles` de la fiche.</summary>
		private sealed record FicheTige(
			int Axes, float EcartPied, float Evase, float BasNu, float HautNu, bool Opposees,
			float FeuilleBasCm, float FeuilleHautCm, float Penche, Color Tige, float EpiCm = 0f,
			int Rameaux = 0, float RameauDes = 0.5f, float RameauLong = 0.8f, float RameauFin = 1f,
			float RameauMonte = 0.8f, int FeuillesRameau = 0, int TetesAisselle = 0);

		/// <summary>Une ligne de table : ce qu'il faut pour dessiner un port. Hauteurs en cm ;
		/// `HauteurAdulteCm` = `height_cm` moteur du stade feuillé adulte (taille du pied) ;
		/// `Dressee` 0 plaquée → 1 dressée ; `LargeurFeuille` = demi-largeur / longueur ;
		/// `StadesHampe` null = la hampe suit la floraison seule ; `MelangeFruit` tire le
		/// limbe vers le fruit mûr de la palette (drosera) ; `Pied` = couleur vue au collet.</summary>
		private sealed record FichePort(
			FormePort Forme, float RayonCm, float HautFeuillesCm, float HauteurAdulteCm, int Feuilles,
			FormeFeuille Feuille, float LargeurFeuille, float Dressee, FormeTete Tete, float TeteCm,
			int Hampes, float EpaisseurTigeCm, string[] StadesHampe = null, int FeuillesHampe = 0,
			float MelangeFruit = 0f, MarqueFeuille Marque = MarqueFeuille.Aucune, string Pied = null,
			FicheTige Tige = null);

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
			// --- Tiges ③ : Hampes 0, la hauteur vient de l'axe. Dressee 1 : le vent les couche. -
			["Sunflower"] = new(FormePort.Tige, RayonCm: 30f, HautFeuillesCm: 250f, HauteurAdulteCm: 250f, Feuilles: 13,
				FormeFeuille.Coeur, LargeurFeuille: 0.42f, Dressee: 1f, FormeTete.Soleil, TeteCm: 12.5f, Hampes: 0, EpaisseurTigeCm: 3f,
				Tige: new(1, 0f, 0f, 0.15f, 0.04f, false, 28f, 8f, -0.35f, new Color("6a9a48"))),
			["Nettle"] = new(FormePort.Tige, RayonCm: 26f, HautFeuillesCm: 90f, HauteurAdulteCm: 90f, Feuilles: 6,
				FormeFeuille.Scie, LargeurFeuille: 0.42f, Dressee: 1f, FormeTete.Pendante, TeteCm: 1.3f, Hampes: 0, EpaisseurTigeCm: 0.6f, Marque: MarqueFeuille.Gaufre,
				Tige: new(4, 0.55f, 0.05f, 0.08f, 0.02f, true, 13f, 5f, -0.15f, new Color("4f6e3a"), TetesAisselle: 1)),
			["Basil"] = new(FormePort.Tige, RayonCm: 20f, HautFeuillesCm: 40f, HauteurAdulteCm: 40f, Feuilles: 4,
				FormeFeuille.Ovale, LargeurFeuille: 0.62f, Dressee: 1f, FormeTete.Epi, TeteCm: 1.1f, Hampes: 0, EpaisseurTigeCm: 0.4f, Marque: MarqueFeuille.Eclat,
				Tige: new(2, 0.2f, 0.25f, 0f, 0.05f, true, 9f, 6f, 0.05f, new Color("7ab060"), EpiCm: 10f,
					Rameaux: 4, RameauDes: 0.08f, RameauLong: 0.85f, RameauFin: 0.55f, RameauMonte: 0.6f, FeuillesRameau: 3)),
			["Pepper"] = new(FormePort.Tige, RayonCm: 32f, HautFeuillesCm: 80f, HauteurAdulteCm: 80f, Feuilles: 3,
				FormeFeuille.Ovale, LargeurFeuille: 0.5f, Dressee: 1f, FormeTete.Etoile, TeteCm: 2f, Hampes: 0, EpaisseurTigeCm: 0.9f, Marque: MarqueFeuille.Eclat,
				Tige: new(1, 0f, 0f, 0.3f, 0f, false, 15f, 11f, -0.15f, new Color("5a8f42"),
					Rameaux: 7, RameauDes: 0.3f, RameauLong: 0.85f, RameauFin: 0.8f, RameauMonte: 0.9f, FeuillesRameau: 4)),
			["Phacelia"] = new(FormePort.Tige, RayonCm: 24f, HautFeuillesCm: 80f, HauteurAdulteCm: 80f, Feuilles: 6,
				FormeFeuille.Plume, LargeurFeuille: 0.4f, Dressee: 1f, FormeTete.Grappe, TeteCm: 3f, Hampes: 0, EpaisseurTigeCm: 0.5f,
				Tige: new(4, 0.3f, 0.5f, 0.05f, 0.08f, false, 12f, 6f, 0.1f, new Color("6a9460"),
					Rameaux: 1, RameauDes: 0.65f, RameauLong: 0.4f, RameauMonte: 1.2f)),
			["Borage"] = new(FormePort.Tige, RayonCm: 24f, HautFeuillesCm: 70f, HauteurAdulteCm: 70f, Feuilles: 4,
				FormeFeuille.Ovale, LargeurFeuille: 0.58f, Dressee: 1f, FormeTete.Etoile, TeteCm: 3f, Hampes: 0, EpaisseurTigeCm: 1.2f, Marque: MarqueFeuille.Duvet,
				Tige: new(3, 0.3f, 0.35f, 0f, 0.1f, false, 20f, 8f, -0.35f, new Color("8a9a80"),
					Rameaux: 3, RameauDes: 0.55f, RameauLong: 0.5f, RameauMonte: 0.7f, FeuillesRameau: 2, TetesAisselle: 1)),
			["Mustard"] = new(FormePort.Tige, RayonCm: 20f, HautFeuillesCm: 60f, HauteurAdulteCm: 60f, Feuilles: 5,
				FormeFeuille.Lobee, LargeurFeuille: 0.42f, Dressee: 1f, FormeTete.Bouquet, TeteCm: 3.8f, Hampes: 0, EpaisseurTigeCm: 0.5f,
				Tige: new(1, 0f, 0f, 0.03f, 0.42f, false, 20f, 7f, -0.1f, new Color("7aa858"),
					Rameaux: 9, RameauDes: 0.42f, RameauLong: 0.85f, RameauMonte: 1.1f)),
			["Mugwort"] = new(FormePort.Tige, RayonCm: 20f, HautFeuillesCm: 110f, HauteurAdulteCm: 110f, Feuilles: 9,
				FormeFeuille.Lobee, LargeurFeuille: 0.48f, Dressee: 1f, FormeTete.Epi, TeteCm: 1.4f, Hampes: 0, EpaisseurTigeCm: 0.7f, Marque: MarqueFeuille.Revers,
				Tige: new(4, 0.45f, 0.08f, 0.15f, 0.12f, false, 13f, 5f, -0.05f, new Color("7a3f4a"), EpiCm: 55f)),
			["Hemp"] = new(FormePort.Tige, RayonCm: 24f, HautFeuillesCm: 300f, HauteurAdulteCm: 300f, Feuilles: 8,
				FormeFeuille.Palmee, LargeurFeuille: 0.07f, Dressee: 1f, FormeTete.Epi, TeteCm: 1.6f, Hampes: 0, EpaisseurTigeCm: 1f,
				Tige: new(1, 0f, 0f, 0.25f, 0.02f, true, 22f, 7f, -0.2f, new Color("5a8a48"), EpiCm: 50f)),
			["Yarrow"] = new(FormePort.Tige, RayonCm: 16f, HautFeuillesCm: 40f, HauteurAdulteCm: 40f, Feuilles: 4,
				FormeFeuille.Plume, LargeurFeuille: 0.36f, Dressee: 1f, FormeTete.Ombelle, TeteCm: 4.5f, Hampes: 0, EpaisseurTigeCm: 0.5f,
				Tige: new(3, 0.4f, 0.2f, 0f, 0.25f, false, 12f, 3f, 0.15f, new Color("8a9a70"), EpiCm: 8f)),
			["Comfrey"] = new(FormePort.Tige, RayonCm: 32f, HautFeuillesCm: 50f, HauteurAdulteCm: 50f, Feuilles: 5,
				FormeFeuille.Lanceolee, LargeurFeuille: 0.36f, Dressee: 1f, FormeTete.Pendante, TeteCm: 2.2f, Hampes: 0, EpaisseurTigeCm: 1.5f, Marque: MarqueFeuille.Gaufre,
				Tige: new(4, 0.3f, 0.3f, 0f, 0.1f, false, 30f, 10f, -0.25f, new Color("4f7a42"))),
			["Mint"] = new(FormePort.Tige, RayonCm: 18f, HautFeuillesCm: 30f, HauteurAdulteCm: 30f, Feuilles: 4,
				FormeFeuille.Scie, LargeurFeuille: 0.5f, Dressee: 1f, FormeTete.Epi, TeteCm: 1.1f, Hampes: 0, EpaisseurTigeCm: 0.4f, Marque: MarqueFeuille.Gaufre,
				Tige: new(6, 0.75f, 0.05f, 0.1f, 0.05f, true, 7f, 4f, -0.05f, new Color("6a4f78"), EpiCm: 12f)),
		};

		// Espèces du catalogue sans palette (limbe, fleur, fruit vert, fruit mûr).
		static PlantRenderer()
		{
			Palettes["Taraxacum"] = new OrganPalette("4f9a3c", "f0c21e", "8aa858", "f2f0e8");       // pissenlit : vert franc, capitule d'or, aigrette blanche
			Palettes["Molene"] = new OrganPalette("9aa88c", "e8c82e", "8a9a70", "6a5236");          // molène : gris-vert argenté, épi jaune, capsule brune
			Palettes["BursaPastoris"] = new OrganPalette("5f8a48", "f0efe6", "9aa860", "a89a58");   // bourse-à-pasteur : vert terne, fleur blanche, silicule
			Palettes["Mugwort"] = new OrganPalette("5a6e5a", "b7b06a", "8a9a66", "7a7a4a");         // armoise (remplace Organs.cs) : colonne sombre, dessous clair au ton 4
			Palettes["Basil"] = new OrganPalette("4a9c3e", "f2efe6", "6fae45", "6a7a40");           // basilic : vert franc luisant
			Palettes["Mint"] = new OrganPalette("3a7a50", "c8a8d8", "6fa864", "7a8a60");            // menthe : vert bleuté, épi lilas
			Palettes["Raspberry"] = new OrganPalette("4a8540", "f0ece0", "c0a060", "c0283e");       // framboisier : fruit rouge
			Palettes["RunningBamboo"] = new OrganPalette("5a9a48", "c8c888", "8aa858", "a89a58");   // bambou : vert clair
			Palettes["Wheat"] = new OrganPalette("6a9a48", "c8b878", "a8b060", "d0b050");           // blé : épi doré
			Palettes["Rye"] = new OrganPalette("5f9458", "a89a78", "a8b070", "c8a860");             // seigle : vert bleuté, épi paille
			Palettes["Hemp"] = new OrganPalette("3a7436", "a8b468", "7a9a50", "7a7a48");            // chanvre : vert sombre, fleurs ternes
			Palettes["PoaAnnua"] = new OrganPalette("62a850", "c8c8a0", "9ab070", "b0a870");        // pâturin : vert tendre
			Palettes["MedicagoLupulina"] = new OrganPalette("4f8f40", "e8d030", "5a8a40", "2a2a24"); // minette : fleur jaune, gousse noire
			Palettes["Ivy"] = new OrganPalette("2f6a3a", "c0c060", "3a5a3a", "22263a");             // lierre : vert sombre, baie noire
			Palettes["Jasmine"] = new OrganPalette("3f8a48", "f6f2ea", "7a9a50", "3a3a40");         // jasmin : vert franc, fleur blanche
		}
	}
}
