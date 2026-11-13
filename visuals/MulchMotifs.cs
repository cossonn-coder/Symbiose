// SYMBIOSE — MulchMotifs.cs (sprint GESTES LISIBLES ③, conception §3)
// Les TEXTURES du paillis, une par nature de mulch (NATURES_MULCH côté moteur) :
//  · paille     = brins dorés couchés en tous sens (chaume de céréale) ;
//  · brf        = COPEAUX : petits éclats clairs d'aubier cernés d'ombre — le BRF doit
//                 se reconnaître au premier regard (demande Nico) ;
//  · aiguilles  = traits fins et serrés, brun-vert (litière de conifère) ;
//  · feuilles   = taches rousses et rouille (feuilles mortes glanées).
// Le plot entier est COUVERT par un losange de la teinte de base (opaque ∝ profondeur) ;
// la texture se pose dessus, d'autant plus serrée que la couche est épaisse.
//
// 📖 Pédagogie — même découpage que TracesSolMotifs : la couche (MulchLayer) décide
// QUOI dessiner d'après le snapshot, ce fichier décide COMMENT. Dé déterministe par
// plot (même plot = même texture, philo #3), offsets MONDE → la texture tourne avec la
// vue (D35). `pose` ∈ [0,1] : 1 = posé ; en dessous, des brins tombent encore (③).

using Godot;
using static Symbiose.TracesSolMotifs;

namespace Symbiose
{
	internal static class MulchMotifs
	{
		private const float DemiCm = 24f;        // le losange couvre le plot (50 cm) bord à bord
		private const float AlphaFloor = 0.35f, AlphaSpan = 0.55f;
		private const int GrainsFloor = 10, GrainsSpan = 22;
		private const float ChuteCm = 30f;       // hauteur de chute des brins à la pose

		/// <summary>Teinte de base d'une nature (inconnue → teinte neutre).</summary>
		internal static Color Base(string nature) => nature switch
		{
			"paille" => Palette16.PaillePaille,
			"brf" => Palette16.PailleBrf,
			"aiguilles" => Palette16.PailleAiguilles,
			"feuilles" => Palette16.PailleFeuilles,
			_ => Palette16.PailleInconnue,
		};

		private static Color Eclat(string nature) => nature switch
		{
			"paille" => Palette16.PaillePailleEclat,
			"brf" => Palette16.PailleBrfEclat,
			"aiguilles" => Palette16.PailleBrf,
			"feuilles" => Palette16.PailleFeuillesEclat,
			_ => Palette16.PaillePailleEclat,
		};

		private static Vector2 Off(float dx, float dy) => WorldView.WorldToScreenOffset(dx, dy);

		/// <summary>Un plot paillé : couverture + texture de sa nature (+ chute si `pose` &lt; 1).</summary>
		internal static void Plot(LotTriangles lot, string nature, Vector2 c, float depth,
								  uint graine, float pose)
		{
			Color fond = Base(nature);
			fond.A = (AlphaFloor + AlphaSpan * depth) * pose;
			Losange(lot, c, DemiCm, fond);
			var d = new Des(graine);
			int n = GrainsFloor + Mathf.RoundToInt(GrainsSpan * depth);
			Color eclat = Eclat(nature), ombre = Base(nature).Darkened(0.35f);
			for (int i = 0; i < n; i++)
			{
				Vector2 p = c + Off(d.Pm(DemiCm - 3f), d.Pm(DemiCm - 3f));
				float ang = d.Suivant() * Mathf.Tau;
				// Les derniers brins tombent encore : chacun a son retard, puis glisse au sol.
				float chute = Mathf.Clamp(pose * 1.6f - (float)i / n * 0.6f, 0f, 1f);
				if (chute <= 0f) continue;
				p.Y -= (1f - chute) * (1f - chute) * ChuteCm * WorldView.PxPerCmZ;
				Grain(lot, nature, p, ang, i, eclat, ombre);
			}
		}

		private static void Grain(LotTriangles lot, string nature, Vector2 p, float ang, int i,
								  Color eclat, Color ombre)
		{
			Vector2 dir = Off(Mathf.Cos(ang), Mathf.Sin(ang));
			switch (nature)
			{
				case "brf":
					// Copeau : éclat clair 2×2 posé sur son ombre décalée d'un pixel.
					Px(lot, p + new Vector2(1f, 1f), ombre, 2f);
					Px(lot, p, eclat, i % 3 == 0 ? 3f : 2f);
					break;
				case "aiguilles":
					lot.Ligne(p - dir * 4f, p + dir * 4f, i % 2 == 0 ? ombre : eclat, 1f);
					break;
				case "feuilles":
					Px(lot, p, i % 2 == 0 ? eclat : ombre, 2f);
					Px(lot, p + new Vector2(2f, 0f), eclat, 1f);
					break;
				default:   // paille (et nature inconnue) : brin couché, un sur deux au soleil
					lot.Ligne(p - dir * 7f, p + dir * 7f, i % 2 == 0 ? eclat : ombre, 1f);
					break;
			}
		}
	}
}
