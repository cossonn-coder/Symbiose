// SYMBIOSE — PlantRenderer.SplatsDetails.cs (partial, sprint RELIQUATS DES PLANTES ③)
// Les DÉTAILS des feuilles et des organes en SUR-COUCHES cuites (consigne E10 de Nico : « tous les
// détails des feuilles présents quand on zoome, beaux à chaque palier »).
//
// Avant : nervures, duvet, gouttes, éclat, revers, poils, pruine, étamines étaient tracés en
// vecteurs PAR-DESSUS l'ancien dessin ; dès qu'une feuille devenait une pièce splat, ils
// disparaissaient. Désormais chaque détail est cuit (tools/splat/lib/details.js) dans
// `<recette>_details` : MÊMES vues, MÊMES classes de taille, MÊME point d'attache que la pièce de
// base, une couche par détail. Après la pièce, on pose les couches que porte l'espèce, chacune
// avec sa palette, à partir de son palier (table SeuilsDetails, ci-dessous).
//
// Qui porte quoi : la MARQUE de la fiche de port (Duvet, Gouttes, Éclat, Revers, Nervures) et la
// SURFACE de l'espèce (Poils, Pruine, Glandes, PaliersHauts.cs). Les nervures, toutes les feuilles.
// Les étamines, toute corolle ouverte. Les couleurs de SANTÉ (nécrose, taches, givre) restent
// peintes par-dessus (D5 du sprint (a)) : ce ne sont pas des détails de forme.
//
// SEUILS : le palier où le détail se LIT sur les planches de contrôle (mesures/03_controle_*),
// un cran plus tôt que l'ancien dessin quand la pièce le porte proprement, jamais avant qu'il ne
// fasse un pixel entier (sinon il « grésille » d'une vue à l'autre).
//
// 📖 Pédagogie : un calque par détail, aligné au pixel sur la feuille (même attache). Comme les
// couches d'un circuit imprimé (cuivre, vernis, sérigraphie) : chacune a sa couleur, on n'imprime
// que celles que la carte demande.
//
// Déterministe (tables, hash de la pièce de base), purement visuel : golden non concerné.

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Palier d'apparition de chaque détail — LA table unique (00_etat.md ③, compte rendu).
		private static readonly Dictionary<string, float> SeuilsDetails = new()
		{
			["nervures"] = 16f,   // ancien dessin : ×16 (DetaillerLimbe, DrawLeafVeins)
			["duvet"] = 8f,       // molène, bourrache : ×8 (PoserDuvet)
			["poils"] = 32f,      // Surface.Poils : ×32 (DrawSurfaceFeuille)
			["eclat"] = 4f,       // basilic, poivron : ×4
			["revers"] = 4f,      // armoise, framboisier : ×4
			["pruine"] = 32f,     // ail, baie de la myrtille : ×32
			["glandes"] = 16f,    // drosera : tentacules (ancien : ×32)
			["gouttes"] = 8f,     // drosera : perles de glu, ×8
			["etamines"] = 32f,   // corolle : ×32 (DrawEtamines)
		};
		// Nervures pâles du lierre (marque de fiche) : ×8, comme PoserNervuresLierre.
		private const float SeuilNervuresMarque = 8f;

		// Marque de la fiche de l'espèce (port ou liane) ; Aucune ailleurs (arbres, générique).
		private MarqueFeuille MarqueEspece()
		{
			string n = _structure.SpeciesName;
			if (FichesPort.TryGetValue(n, out var f)) return f.Marque;
			return FichesLiane.TryGetValue(n, out var l) ? l.Organes.Marque : MarqueFeuille.Aucune;
		}

		// Revers (armoise, framboisier) : une feuille sur trois, retournée par le vent, montre son
		// dessous clair dès ×4 — la pièce de base prend alors la teinte du revers (ancien : Ton 4).
		private bool Retournee(int k) =>
			k % 3 == 0 && AuPalier(PaliersHautsMinZoom) && MarqueEspece() == MarqueFeuille.Revers;

		// Ton le plus clair de la rampe d'une couleur (l'ancien `Ton(col, 4)`), opaque.
		private static Color Clair(Color col) => RampeLitterale(col)[4];

		private static Color Opaque(Color c) => new(c.R, c.G, c.B);

		// Recettes qui ont des sur-couches (`<recette>_details.json` présent) : vérifié une fois, en
		// silence — une recette sans détail (plume, palmée…) n'est pas une erreur.
		private static readonly Dictionary<string, bool> _aDesDetails = new();
		private static bool ADesDetails(string rd)
		{
			if (!_aDesDetails.TryGetValue(rd, out bool oui))
				_aDesDetails[rd] = oui = FileAccess.FileExists(SplatPlanches.Dossier + rd + ".json");
			return oui;
		}

		/// <summary>Sur-couches de détail d'une feuille-pièce saine, posées sur la pièce de base
		/// (même attache `ancre`, même vue, classe `e` réellement posée).</summary>
		private void PoserDetailsFeuille(string recette, Vector2 ancre, float z, int e, int inc, int lacet, int v, Color col)
		{
			string rd = recette + "_details";
			if (!ADesDetails(rd)) return;
			string[] couches = SplatPlanches.Couches(rd);
			if (couches == null) return;
			MarqueFeuille m = MarqueEspece();
			Surface s = SurfaceDe();
			for (int k = 0; k < couches.Length; k++)
			{
				string d = couches[k];
				if (!SeuilsDetails.TryGetValue(d, out float seuil)) continue;
				if (d == "nervures" && m == MarqueFeuille.Nervures) seuil = SeuilNervuresMarque;
				if (z < seuil || !Porte(d, m, s)) continue;
				if (!SplatPlanches.Trouver(rd, z, e, k, inc, lacet, v, 0, out var p, out _, exacte: true)) continue;
				PoserPieceSplat(p, ancre, PaletteIndexee.Palette(CouleurDetail(d, col, m)));
			}
		}

		/// <summary>Sur-couches d'un organe : étamines d'une corolle ouverte, pruine d'un fruit.</summary>
		private void PoserDetailsOrgane(string recette, Vector2 ancre, float z, int e, int inc, int lacet, int v, bool fleur)
		{
			string rd = recette + "_details";
			if (!fleur || !ADesDetails(rd) || !SplatPlanches.Vues(rd, out _, out _, out _)) return;
			string[] couches = SplatPlanches.Couches(rd);
			Surface s = SurfaceDe();
			for (int k = 0; k < couches.Length; k++)
			{
				string d = couches[k];
				if (!SeuilsDetails.TryGetValue(d, out float seuil) || z < seuil || (d == "pruine" && s != Surface.Pruine)) continue;
				if (!SplatPlanches.Trouver(rd, z, e, k, inc, lacet, v, 0, out var p, out _, exacte: true)) continue;
				PoserPieceSplat(p, ancre, PaletteIndexee.Palette(CouleurDetail(d, default, MarqueFeuille.Aucune)));
			}
		}

		// L'espèce porte-t-elle ce détail ? (marque de fiche, surface de l'espèce)
		private static bool Porte(string d, MarqueFeuille m, Surface s) => d switch
		{
			"nervures" => true,
			"duvet" => m == MarqueFeuille.Duvet,
			"eclat" => m == MarqueFeuille.Eclat,
			"revers" => m == MarqueFeuille.Revers,
			"gouttes" => m == MarqueFeuille.Gouttes,
			"poils" => s == Surface.Poils,
			"pruine" => s == Surface.Pruine,
			"glandes" => s == Surface.Glandes,
			_ => false,
		};

		// Teinte d'un détail : celle de l'ancien dessin (nervure = limbe décalé, duvet / éclat /
		// revers = ton clair du limbe, poils / pruine / glu = leurs couleurs, glandes = rouge du fruit).
		private Color CouleurDetail(string d, Color col, MarqueFeuille m) => d switch
		{
			"nervures" => m == MarqueFeuille.Nervures ? Clair(col) : HueShift(col, NervureShift),
			"duvet" or "eclat" or "revers" => Clair(col),
			"poils" => Opaque(PoilColor),
			"pruine" => Opaque(PruineColor),
			"gouttes" => Opaque(GluColor),
			"glandes" => PaletteIndividu().FruitRipe,
			"etamines" => FruitRotten.Darkened(0.35f),
			_ => col,
		};
	}
}
