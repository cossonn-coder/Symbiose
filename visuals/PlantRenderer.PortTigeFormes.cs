// SYMBIOSE — PlantRenderer.PortTigeFormes.cs (partial, sprint FORMES DES PLANTES ③)
// Feuilles et têtes du port tige. Feuilles à contour (cœur, scie, lancéolée, ovale, lobée),
// main palmée du chanvre, plume ; têtes neuves : soleil du tournesol, étoile de la bourrache et
// du poivron, grappe pendante de l'ortie et de la consoude.
//
// 📖 Pédagogie : pourquoi un LOSANGE aux paliers bas. À ×1 une feuille de 5 cm fait 2 px : ses
// dents n'existeraient pas, mais son contour coûterait 10 triangles. Deux triangles donnent
// exactement les mêmes pixels. Un plancher d'un pixel sur la largeur empêche la feuille de
// disparaître par endroits (une forme plus fine que le pixel en saute).

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		private static readonly Vector2[] ContourCoeur = Symetrique(new(0f, 0f), new(-0.06f, 0.6f), new(0.12f, 1f),
			new(0.45f, 0.85f), new(0.78f, 0.4f), new(1f, 0f));
		private static readonly Vector2[] ContourScie = Symetrique(new(0f, 0f), new(0.15f, 0.7f), new(0.3f, 0.45f),
			new(0.5f, 1f), new(0.62f, 0.55f), new(0.78f, 0.55f), new(1f, 0f));
		private const int DoigtsPalmee = 7;

		private void PoserFeuilleTige(FichePort f, FeuillePosee fe, Color col)
		{
			float pix = PixelInterne;
			Color c = Ton(col, fe.Ton, Orientation(WorldView.WorldToScreenOffset(fe.U.X, fe.U.Y)));
			if (!AuPalier(PaliersHautsMinZoom)) { PoserLosange(fe, c); return; }
			switch (f.Feuille)
			{
				case FormeFeuille.Palmee: PoserPalmee(fe, c); return;
				case FormeFeuille.Plume: PoserPlume(fe, col); return;
			}
			_contourPrairie.Clear();
			foreach (Vector2 q in ContourDe(f.Feuille)) _contourPrairie.Add(PointFeuille(fe, q.X, q.Y));
			bool pres = AuPalier(PalierOrganesZoom);
			if (pres) PoserEventail(_contourPrairie, new Vector2(0f, pix), Ton(col, 0));
			// Armoise : une feuille sur trois montre son dessous argenté, retourné par le vent.
			if (f.Marque == MarqueFeuille.Revers && fe.K % 3 == 0) c = Ton(col, 4);
			PoserEventail(_contourPrairie, Vector2.Zero, c);
			if (f.Marque == MarqueFeuille.Eclat)   // limbe luisant : un éclat franc par feuille, dès ×4
				_lotPrairie.Ligne(PointFeuille(fe, 0.35f, 0.3f), PointFeuille(fe, 0.6f, 0.3f), Ton(col, 4), pix);
			if (!pres) return;
			_lotPrairie.Ligne(PointFeuille(fe, 0.05f, 0f), PointFeuille(fe, 0.9f, 0f), Ton(col, Mathf.Min(fe.Ton + 2, 4)), pix);
			if (f.Marque == MarqueFeuille.Duvet) PoserDuvet(fe, col);
			if (f.Marque == MarqueFeuille.Gaufre) PoserGaufrage(fe, col);
		}

		private void PoserLosange(FeuillePosee fe, Color c)
		{
			fe = fe with { Large = Mathf.Max(fe.Large, PixelInterne / WorldView.PxPerCmX) };
			Vector2 b = PointFeuille(fe, 0f, 0f), p = PointFeuille(fe, 1f, 0f);
			Vector2 g = PointFeuille(fe, 0.5f, 1f), d = PointFeuille(fe, 0.5f, -1f);
			_lotPrairie.Triangle(b, g, p, c);
			_lotPrairie.Triangle(b, p, d, c);
		}

		// Main de chanvre : des doigts étroits en éventail, le médian le plus long.
		private void PoserPalmee(FeuillePosee fe, Color c)
		{
			float a0 = Mathf.Atan2(fe.U.Y, fe.U.X);
			for (int i = 0; i < DoigtsPalmee; i++)
			{
				float e = (i - (DoigtsPalmee - 1) * 0.5f) / ((DoigtsPalmee - 1) * 0.5f);   // -1 → 1
				float a = a0 + e * 1.35f;
				var doigt = fe with
				{
					U = new Vector2(Mathf.Cos(a), Mathf.Sin(a)),
					Long = fe.Long * (1f - 0.45f * Mathf.Abs(e)),
					Large = Mathf.Max(fe.Large, PixelInterne / WorldView.PxPerCmX),
				};
				PoserLosange(doigt, c);
			}
		}

		// Limbe gaufré (ortie, menthe, consoude) : des nervures secondaires creusées.
		private void PoserGaufrage(FeuillePosee fe, Color col)
		{
			Color creux = Ton(col, 1);
			for (int i = 1; i <= 2; i++)
			{
				float t = 0.2f + i * 0.2f;
				Vector2 axe = PointFeuille(fe, t, 0f);
				_lotPrairie.Ligne(axe, PointFeuille(fe, t + 0.18f, 0.6f), creux, PixelInterne);
				_lotPrairie.Ligne(axe, PointFeuille(fe, t + 0.18f, -0.6f), creux, PixelInterne);
			}
		}

		// Tournesol : tête penchée. Loin, un disque jaune à cœur brun, l'icône de ×1. Près, une
		// couronne de rayons. Fanée (autre couleur que la fleur) : le disque de graines seul.
		private void PoserSoleil(Vector2 c, float r, Color col)
		{
			if (!Palettes.TryGetValue(_structure.SpeciesName, out var pal)) pal = DefaultPalette;
			c += new Vector2(r * 0.35f, r * 0.2f);
			float ry = r * 0.8f;
			Color coeur = Ton(pal.FruitRipe, 1);
			if (col != pal.Flower) { PoserEllipse(c, r * 0.75f, ry * 0.75f, coeur); return; }
			PoserEllipse(c, r, ry, Ton(col, PaletteIndexee.TonBase));
			if (AuPalier(PaliersHautsMinZoom))
			{
				const int N = 14;
				for (int k = 0; k < N; k++)
				{
					float a = k * Mathf.Tau / N, e = 0.3f;
					Vector2 Sur(float ang, float d) => c + new Vector2(Mathf.Cos(ang) * r * d, Mathf.Sin(ang) * ry * d);
					_lotPrairie.Triangle(Sur(a - e, 0.75f), Sur(a, 1.3f), Sur(a + e, 0.75f), Ton(col, k % 2 == 0 ? 3 : 4));
				}
			}
			PoserEllipse(c, r * 0.55f, ry * 0.55f, coeur);
			if (AuPalier(PalierOrganesZoom))
				PoserEllipse(c - new Vector2(r * 0.12f, ry * 0.12f), r * 0.3f, ry * 0.3f, Ton(pal.FruitRipe, 3));
		}

		// Étoile à 5 pointes, tournée vers le bas (écrasée) ; un point sombre au cœur dès ×8.
		private void PoserEtoile(Vector2 c, float r, Color col)
		{
			// Hors fleur (organe « fruit » du moteur, poivron non `fruitier`) : une simple marque de
			// stade, ronde. Ni état moteur ni récolte (fiches §Lire).
			if (col != FleurDe()) { PoserDisque(c, r, Ton(col, PaletteIndexee.TonBase)); return; }
			if (!AuPalier(PaliersHautsMinZoom)) { PoserDisque(c, r, Ton(col, 3)); return; }
			Color ton = Ton(col, PaletteIndexee.TonBase), eclat = Ton(col, 3);
			for (int k = 0; k < 5; k++)
			{
				float a = k * Mathf.Tau / 5f - Mathf.Pi * 0.5f;
				var pointe = c + new Vector2(Mathf.Cos(a) * r, Mathf.Sin(a) * r * 0.8f);
				var flanc = new Vector2(-Mathf.Sin(a), Mathf.Cos(a)) * r * 0.35f;
				_lotPrairie.Triangle(c + flanc, pointe, c - flanc, k < 2 ? eclat : ton);
			}
			if (AuPalier(PalierOrganesZoom)) PoserDisque(c, Mathf.Max(r * 0.22f, PixelInterne), Ton(col, 0));
		}

		// Grappe qui pend sous son point d'attache : quelques grains, de plus en plus petits.
		private void PoserPendante(Vector2 c, float r, Color col, int graine)
		{
			const int N = 4;
			float sens = Hash01(371, graine, 0) < 0.5f ? 1f : -1f;
			for (int k = 0; k < N; k++)
			{
				var q = c + new Vector2(sens * r * (0.5f + 0.25f * k), r * 0.9f * k);
				PoserDisque(q, Mathf.Max(r * Mathf.Lerp(0.8f, 0.45f, k / (N - 1f)), PixelInterne), Ton(col, k % 2 == 0 ? 3 : PaletteIndexee.TonBase));
			}
		}
	}
}
