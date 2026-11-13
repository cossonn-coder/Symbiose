// SYMBIOSE — TracesSolMotifs.cs (sprint GESTES LISIBLES ③, conception §3.1-§3.2)
// Les MOTIFS PIXEL du sol-canvas : ce qu'un geste laisse au sol (mottes, raies,
// botte, voile de compost, auréole, rebord de cuvette) et le sol CRAQUELÉ d'un plot
// sec. Pur dessin, sans état : TracesSolLayer décide QUOI dessiner (lu au snapshot),
// ce fichier décide COMMENT (une sorte = une méthode).
//
// 📖 Pédagogie — tout est posé en OFFSET MONDE (cm) autour d'un point, projeté par
// WorldView.WorldToScreenOffset : le motif tourne avec la vue (D35) au lieu de rester
// figé à l'écran. Les grains sont des carrés de 1 px canvas arrondis à la grille
// entière (`Px`) : c'est ce qui donne le grain pixel-art au lieu d'un flou vectoriel.
//
// Le hasard est un DÉ déterministe (`Des`, graine = hash de la trace) : la même trace
// a toujours les mêmes mottes, d'une image et d'une session à l'autre (philo #3).

using Godot;

namespace Symbiose
{
	internal static class TracesSolMotifs
	{
		// Demi-côté utile d'un plot (cm) : on reste DANS le losange (plot = 50 cm).
		private const float DemiPlotCm = 22f;

		/// <summary>Dé déterministe (xorshift32) : jamais Random, jamais GetHashCode.</summary>
		internal struct Des
		{
			private uint _s;
			public Des(uint graine) { _s = graine == 0 ? 0x9e3779b9u : graine; }
			public float Suivant()
			{
				_s ^= _s << 13; _s ^= _s >> 17; _s ^= _s << 5;
				return (_s & 0xffffff) / 16777216f;
			}
			/// <summary>Valeur dans [-a, a].</summary>
			public float Pm(float a) => (Suivant() * 2f - 1f) * a;
		}

		/// <summary>Hash djb2-xor d'une clé texte (même choix que MulchLayer/LitterLayer).</summary>
		internal static uint Hash(string s)
		{
			uint h = 5381;
			foreach (char ch in s) h = ((h << 5) + h) ^ ch;
			return h;
		}

		private static Vector2 Off(float dx, float dy) => WorldView.WorldToScreenOffset(dx, dy);

		private static Color A(Color c, float a) { c.A = a; return c; }

		/// <summary>Un grain carré de `taille` px canvas, calé sur la grille entière.</summary>
		internal static void Px(LotTriangles lot, Vector2 p, Color col, float taille = 1f)
		{
			Vector2 o = p.Floor();
			lot.PolygoneConvexe(new[] { o, o + new Vector2(taille, 0f),
				o + new Vector2(taille, taille), o + new Vector2(0f, taille) }, col);
		}

		/// <summary>Losange du plot (demi-côté `demiCm`) autour de `c`.</summary>
		internal static void Losange(LotTriangles lot, Vector2 c, float demiCm, Color col)
		{
			lot.PolygoneConvexe(new[] { c + Off(-demiCm, -demiCm), c + Off(demiCm, -demiCm),
				c + Off(demiCm, demiCm), c + Off(-demiCm, demiCm) }, col);
		}

		/// <summary>Disque MONDE (rayon cm) — une ellipse 2:1 à l'écran, en éventail.</summary>
		private static void Disque(LotTriangles lot, Vector2 c, float rCm, Color col)
		{
			const int n = 12;
			var pts = new Vector2[n];
			for (int i = 0; i < n; i++)
			{
				float a = i * Mathf.Tau / n;
				pts[i] = c + Off(Mathf.Cos(a) * rCm, Mathf.Sin(a) * rCm);
			}
			lot.PolygoneConvexe(pts, col);
		}

		/// <summary>Dessine une trace de geste. `a` = opacité (estompage par l'âge).</summary>
		internal static void Trace(LotTriangles lot, string sorte, Vector2 c, float a, uint graine)
		{
			var d = new Des(graine);
			switch (sorte)
			{
				case "becher": Becher(lot, c, a, ref d); break;
				case "grelinette": Grelinette(lot, c, a); break;
				case "pas": Pas(lot, c, a, ref d); break;
				case "epandre": Epandre(lot, c, a, ref d); break;
				case "arroser": Arroser(lot, c, a); break;
				case "creuser": Creuser(lot, c, a, ref d); break;
				// Sorte inconnue (moteur plus récent que la vue) : rien — on n'invente pas.
			}
		}

		// BÊCHER : terre retournée sombre, semée de mottes (dessous humus, dessus éclairé).
		private static void Becher(LotTriangles lot, Vector2 c, float a, ref Des d)
		{
			Losange(lot, c, DemiPlotCm, A(Palette16.SolSombre, 0.55f * a));
			for (int i = 0; i < 11; i++)
			{
				Vector2 p = c + Off(d.Pm(DemiPlotCm - 4f), d.Pm(DemiPlotCm - 4f));
				Px(lot, p, A(Palette16.SolHumus, a), 2f);
				Px(lot, p + new Vector2(0f, -1f), A(Palette16.SolMotte, a), 2f);
			}
		}

		// GRELINETTE : terre claire ameublie, raies parallèles (sillon sombre + crête claire).
		private static void Grelinette(LotTriangles lot, Vector2 c, float a)
		{
			Losange(lot, c, DemiPlotCm, A(Palette16.SolAmeubli, 0.35f * a));
			for (int k = -2; k <= 2; k++)
			{
				float y = k * 8f;
				lot.Ligne(c + Off(-DemiPlotCm + 3f, y), c + Off(DemiPlotCm - 3f, y),
					A(Palette16.SolSombre, 0.85f * a), 1f);
				lot.Ligne(c + Off(-DemiPlotCm + 3f, y + 2.5f), c + Off(DemiPlotCm - 3f, y + 2.5f),
					A(Palette16.SolAmeubli, 0.8f * a), 1f);
			}
		}

		// PAS (ecraser) : une empreinte de botte au point cliqué — semelle + talon
		// séparés, crampons en travers. Orientation tirée du dé (un pas, pas une grille).
		private static void Pas(LotTriangles lot, Vector2 c, float a, ref Des d)
		{
			float ang = d.Suivant() * Mathf.Tau;
			Vector2 ax = new(Mathf.Cos(ang), Mathf.Sin(ang)), tr = new(-ax.Y, ax.X);
			Vector2 W(float u, float v) => c + Off(ax.X * u + tr.X * v, ax.Y * u + tr.Y * v);
			Color botte = A(Palette16.SolHumus, 0.75f * a);
			// Semelle (avant du pied, arrondie) puis talon, en cm le long de l'axe.
			lot.PolygoneConvexe(new[] { W(2f, -4.5f), W(9f, -4f), W(13f, -2f), W(14f, 0f),
				W(13f, 2f), W(9f, 4f), W(2f, 4.5f), W(1f, 0f) }, botte);
			lot.PolygoneConvexe(new[] { W(-13f, -3.5f), W(-5f, -3.8f), W(-5f, 3.8f),
				W(-13f, 3.5f), W(-14f, 0f) }, botte);
			Color crampon = A(Palette16.SolMotte, 0.8f * a);
			for (int i = 0; i < 3; i++)
				lot.Ligne(W(4f + 3.5f * i, -3f), W(4f + 3.5f * i, 3f), crampon, 1f);
		}

		// ÉPANDRE : un voile de compost brun foncé, bords irréguliers, grumeaux.
		private static void Epandre(LotTriangles lot, Vector2 c, float a, ref Des d)
		{
			const int n = 10;
			var pts = new Vector2[n];
			for (int i = 0; i < n; i++)
			{
				float ang = i * Mathf.Tau / n, r = DemiPlotCm * (0.8f + 0.25f * d.Suivant());
				pts[i] = c + Off(Mathf.Cos(ang) * r, Mathf.Sin(ang) * r);
			}
			lot.PolygoneConvexe(pts, A(Palette16.SolHumus, 0.6f * a));
			for (int i = 0; i < 14; i++)
				Px(lot, c + Off(d.Pm(DemiPlotCm - 3f), d.Pm(DemiPlotCm - 3f)),
					A(i % 3 == 0 ? Palette16.SolMotte : Palette16.SolHumus, a));
		}

		// ARROSER : auréole de terre mouillée — un disque sombre, un cœur plus sombre.
		private static void Arroser(LotTriangles lot, Vector2 c, float a)
		{
			Disque(lot, c, DemiPlotCm, A(Palette16.SolSombre, 0.35f * a));
			Disque(lot, c, DemiPlotCm * 0.6f, A(Palette16.SolHumus, 0.3f * a));
		}

		// CREUSER : le rebord de terre rejetée autour de la cuvette — une couronne
		// serrée de mottes (ombre dessous, dessus clair). Le creux lui-même est le
		// relief du plot (altitude baissée par le moteur), dessiné par le sol.
		private static void Creuser(LotTriangles lot, Vector2 c, float a, ref Des d)
		{
			for (int i = 0; i < 24; i++)
			{
				float ang = i * Mathf.Tau / 24f + d.Pm(0.12f), r = DemiPlotCm * (0.8f + 0.18f * d.Suivant());
				Vector2 p = c + Off(Mathf.Cos(ang) * r, Mathf.Sin(ang) * r);
				Px(lot, p + new Vector2(0f, 1f), A(Palette16.SolHumus, 0.8f * a), 2f);
				Px(lot, p, A(i % 2 == 0 ? Palette16.SolAmeubli : Palette16.SolMotte, a), 2f);
			}
		}

		/// <summary>Sol CRAQUELÉ : croûte claire + réseau de fentes, d'autant plus marqué
		/// que le plot est sec (`sec` ∈ [0,1]).</summary>
		internal static void Craquele(LotTriangles lot, Vector2 c, float sec, uint graine)
		{
			var d = new Des(graine);
			Losange(lot, c, DemiPlotCm + 2f, A(Palette16.SolCroute, 0.25f + 0.35f * sec));
			int fentes = 3 + Mathf.RoundToInt(4f * sec);
			Color fente = A(Palette16.SolSombre, 0.55f + 0.4f * sec);
			for (int i = 0; i < fentes; i++)
			{
				// Une fente = une ligne brisée de 3 tronçons, au hasard du dé.
				Vector2 p = new(d.Pm(DemiPlotCm - 2f), d.Pm(DemiPlotCm - 2f));
				float ang = d.Suivant() * Mathf.Tau;
				for (int k = 0; k < 3; k++)
				{
					ang += d.Pm(1.1f);
					Vector2 q = p + new Vector2(Mathf.Cos(ang), Mathf.Sin(ang)) * 7f;
					q = q.Clamp(new Vector2(-DemiPlotCm, -DemiPlotCm), new Vector2(DemiPlotCm, DemiPlotCm));
					lot.Ligne(c + Off(p.X, p.Y), c + Off(q.X, q.Y), fente, 1f);
					p = q;
				}
			}
		}
	}
}
