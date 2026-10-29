// SYMBIOSE — PlantRenderer.Motifs.cs (partial, sprint CASSÉ À L'ÉCRAN ④ — paliers hauts)
// La MÊME grammaire aux paliers hauts (×4 → ×32) qu'aux paliers bas : une matière
// n'est plus un aplat volumé (2 valeurs) mais un MOTIF estampillé (feuille ≈ 3×4 px,
// 4 orientations au hash) sur une rampe de 5 tons, lu en palette indexée (③) → l'éclat
// se pose côté soleil réel. Le squelette (segments, feuilles, organes) reste celui du
// moteur : seules les TEXTURES de remplissage changent.
//
//  • FEUILLAGE : chaque limbe (et chaque masse ×4) est rempli par la texture de motifs,
//    calée 1 texel = 1 px INTERNE. Le motif garde donc sa taille à l'écran : en zoomant,
//    la feuille grandit et porte PLUS de motifs, plus petits relativement à elle
//    (« partir du complet, retirer en dézoomant »). La masse de valeur vient d'un DÔME :
//    un cœur (orientations mêlées) + une couronne de quartiers, chacun orienté vers
//    l'extérieur — le bord tourné vers le soleil s'éclaire, l'autre s'assombrit.
//  • BOIS : stries le long de l'axe sur 2-3 tons, flancs orientés (cylindre).
//  • ANCRAGE (arbres) : racines en éventail + halo de sol dithéré au pied (brief).
//  • PETITS OBJETS (fleurs, fruits) : tache de couleur pure en dôme, contour = ton le
//    plus sombre de LEUR rampe.
//
// 📖 Pédagogie (perf-first) : le nombre de motifs ne coûte RIEN en tracés. Un limbe =
// un polygone texturé (cœur) + une dizaine de quads (couronne), quel que soit le palier :
// c'est la TEXTURE (générée une fois, ~5 Mo) qui porte les milliers de motifs. Une
// boucle « un tracé par motif » aurait coûté ∝ zoom² (×32 = 1 000× le ×1).
//
// Deux sorties pour une même recette : dans le PINCEAU de cuisson (palette ON), des
// CODES (ton + orientation, PaletteIndexee.cs) ; en dessin DIRECT (plante trop grande
// pour l'atlas, F11 OFF), des couleurs littérales de la même rampe éclairées par un
// soleil fixe haut-gauche (comme le brief). Déterministe (hash), golden non concerné.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Texture des motifs : 10 bandes de B×B (8 orientations de dôme, 1 cœur mêlé,
		// 1 trame dithérée), deux moitiés : codes indexés (haut) / gris littéral (bas).
		private const int MotifB = 256, MotifBandes = 10, BandeCoeur = 8, BandeTrame = 9;
		private const float CoeurPart = 0.55f;    // rayon relatif du cœur du dôme
		private const int MotifPas = 3;           // pas de la grille d'estampille (px)
		private static ImageTexture _motifTex;
		// Vrai pendant la fenêtre « feuilles » de DrawOrgans : les volumes deviennent motifs.
		private bool _motifs;
		// Teinte du dernier limbe rempli : ses trous (morsures, grêle) prennent SON
		// creux — jamais le quasi-noir LeafHoleColor en palette indexée (brief).
		private Color _limbeCourant = new Color("3f8e3a");
		// Tampons du quad de couronne (DrawPrimitive copie ses tableaux).
		private static readonly Vector2[] _quad = new Vector2[4], _quadUv = new Vector2[4];
		private static readonly Color[] _quadCol = new Color[4];
		// Soleil du rendu LITTÉRAL (dessin direct) : haut-gauche, repère écran.
		private static readonly Vector2 SoleilLitteral = new Vector2(-1f, -1f).Normalized();
		private static readonly Color HaloSol = new Color("2c3c1e");   // brief : halo d'ancrage
		private static readonly Dictionary<Color, Color[]> _rampesLit = new();

		// 4 formes de feuille (brief : ovale pointu ~3×4, ≥ 4 orientations) ; '1' = ton
		// ombre (le pli bas du motif), 'X' = ton de base.
		private static readonly string[][] Formes =
		{
			new[] { ".X.", "XXX", "XXX", ".1." },   // verticale
			new[] { ".XX", "XXX", "11." },          // ↗
			new[] { ".XX.", "XXXX", ".11." },       // →
			new[] { "XX.", "XXX", ".11" },          // ↘
		};

		// ---------------------------------------------------------------------------
		// TON — une couleur de rampe, code au pinceau indexé, littérale sinon
		// ---------------------------------------------------------------------------

		/// <summary>Ton `ton` (0 creux … 4 éclat) de la rampe de `col`, face `orient`.</summary>
		private Color Ton(Color col, int ton, int orient = PaletteIndexee.OrientPlat)
		{
			if (Indexe) return PaletteIndexee.Code(PaletteIndexee.Palette(col), ton, orient);
			Color c = RampeLitterale(col)[Mathf.Clamp(ton + Bosse(orient), 0, 4)];
			c.A = col.A;
			return c;
		}

		private static Color[] RampeLitterale(Color col)
		{
			col.A = 1f;
			if (!_rampesLit.TryGetValue(col, out var r)) _rampesLit[col] = r = RampesDa.Deriver(col);
			return r;
		}

		// Même seuils que le shader de lecture, soleil fixe (rendu littéral).
		private static int Bosse(int orient)
		{
			if (orient >= PaletteIndexee.OrientPlat) return 0;
			float a = orient * Mathf.Pi * 0.25f;
			float d = new Vector2(Mathf.Cos(a), Mathf.Sin(a)).Dot(SoleilLitteral);
			return d > 0.8f ? 2 : d > 0.3f ? 1 : d < -0.3f ? -1 : 0;
		}

		// ---------------------------------------------------------------------------
		// FEUILLAGE — remplissage par motifs en dôme
		// ---------------------------------------------------------------------------

		/// <summary>Remplit le contour `pts` (autour de `c`) de motifs de feuille de la
		/// rampe de `col` : cœur mêlé + couronne de quartiers orientés.</summary>
		private void RemplirMotif(Vector2 c, Vector2[] pts, Color col)
		{
			AssurerMotifs();
			_limbeCourant = col;
			float z = WorldView.CurrentZoom;
			bool idx = Indexe;
			Color mod = idx ? PaletteIndexee.ModulatePiece(PaletteIndexee.Palette(col)) : TeinteLitterale(col);
			// Calage : 1 texel = 1 px interne ; décalage au hash de la position (deux
			// feuilles voisines ne montrent pas le même morceau de motif).
			Vector2 mn = pts[0], mx = pts[0];
			foreach (var p in pts) { mn = mn.Min(p); mx = mx.Max(p); }
			Vector2 o = (mn * z).Floor();
			Vector2 taille = (mx * z).Ceil() - o;
			var dec = new Vector2(
				taille.X < MotifB ? Mathf.Floor(Hash01(131, (int)o.X, (int)o.Y) * (MotifB - taille.X)) : 0f,
				taille.Y < MotifB ? Mathf.Floor(Hash01(137, (int)o.X, (int)o.Y) * (MotifB - taille.Y)) : 0f);
			float moitie = idx ? 0f : MotifB;
			Vector2 Uv(Vector2 q, int bande) => new(
				(bande * MotifB + q.X * z - o.X + dec.X) / (MotifB * MotifBandes),
				(moitie + q.Y * z - o.Y + dec.Y) / (2f * MotifB));

			int n = pts.Length;
			var coeur = new Vector2[n];
			var uvc = new Vector2[n];
			for (int k = 0; k < n; k++) { coeur[k] = c + (pts[k] - c) * CoeurPart; uvc[k] = Uv(coeur[k], BandeCoeur); }
			DrawColoredPolygon(coeur, mod, uvc, _motifTex);
			System.Array.Fill(_quadCol, mod);
			for (int k = 0; k < n; k++)
			{
				int k1 = (k + 1) % n;
				Vector2 nrm = (pts[k] + pts[k1]) * 0.5f - c;
				int b = nrm.LengthSquared() < 1e-8f ? BandeCoeur : Orientation(nrm);
				_quad[0] = coeur[k]; _quad[1] = pts[k]; _quad[2] = pts[k1]; _quad[3] = coeur[k1];
				for (int q = 0; q < 4; q++) _quadUv[q] = Uv(_quad[q], b);
				DrawPrimitive(_quad, _quadCol, _quadUv, _motifTex);
			}
		}

		/// <summary>Couleur d'un trou du limbe : au pinceau indexé, le creux de la
		/// rampe du limbe ; en littéral, la couleur d'avant (sombre translucide).</summary>
		private Color Trou(Color litterale) => Indexe ? Ton(_limbeCourant, 0) : litterale;

		// Littéral : le gris de la texture (ton éclairé ÷ éclat) × l'éclat de la rampe.
		private static Color TeinteLitterale(Color col)
		{
			Color c = RampeLitterale(col)[4];
			c.A = col.A;
			return c;
		}

		/// <summary>Dôme PLEIN (petits objets : fleurs, fruits) : cœur plat + quartiers
		/// orientés, tous au ton de base de la palette de `col` ; contour optionnel.</summary>
		private void RemplirDome(Vector2 c, float rx, float ry, Color col, bool contour)
		{
			if (contour)
				DrawColoredPolygon(EllipsePoints(c, rx + PixelInterne, ry + PixelInterne, 12), Ton(col, 0));
			var pts = EllipsePoints(c, rx, ry, 10);
			var coeur = new Vector2[pts.Length];
			for (int k = 0; k < pts.Length; k++) coeur[k] = c + (pts[k] - c) * CoeurPart;
			DrawColoredPolygon(coeur, Ton(col, PaletteIndexee.TonBase));
			for (int k = 0; k < pts.Length; k++)
			{
				int k1 = (k + 1) % pts.Length;
				Color t = Ton(col, PaletteIndexee.TonBase, Orientation((pts[k] + pts[k1]) * 0.5f - c));
				DrawPrimitive(new[] { coeur[k], pts[k], pts[k1], coeur[k1] }, new[] { t, t, t, t }, null);
			}
		}

		// ---------------------------------------------------------------------------
		// BOIS — stries le long de l'axe, flancs orientés
		// ---------------------------------------------------------------------------

		private const float StrieMinPx = 6f;   // largeur interne à partir de laquelle on strie
		private const int StriesMax = 5, StrieRunsMax = 12;

		/// <summary>Un segment de bois (paliers hauts) : âme plate, flancs orientés vers
		/// l'extérieur (le côté soleil s'éclaire), stries de 2-3 tons au hash.</summary>
		private void DrawEcorce(Vector2 p1, Vector2 p2, Color col, float w)
		{
			Vector2 d = p2 - p1;
			float len = d.Length();
			if (len < 1e-4f) return;
			d /= len;
			var nrm = new Vector2(-d.Y, d.X);
			float z = WorldView.CurrentZoom, wi = w * z;
			DrawLine(p1, p2, Ton(col, PaletteIndexee.TonBase), w, antialiased: false);
			if (wi < 3f) return;
			int oA = Orientation(nrm), oB = Orientation(-nrm);
			float tiers = w / 3f;
			DrawLine(p1 + nrm * tiers, p2 + nrm * tiers, Ton(col, PaletteIndexee.TonBase, oA), tiers, antialiased: false);
			DrawLine(p1 - nrm * tiers, p2 - nrm * tiers, Ton(col, PaletteIndexee.TonBase, oB), tiers, antialiased: false);
			if (wi < StrieMinPx) return;
			int nb = Mathf.Min(StriesMax, (int)(wi / 3f));
			int runs = Mathf.Clamp((int)(len * z / 4f), 1, StrieRunsMax);
			int gx = (int)(p1.X * 16f), gy = (int)(p1.Y * 16f);   // graine : le pied du segment
			for (int s = 0; s < nb; s++)
			{
				float off = ((s + 0.5f) / nb - 0.5f) * w * 0.85f;
				int o = off > w * 0.15f ? oA : off < -w * 0.15f ? oB : PaletteIndexee.OrientPlat;
				for (int r = 0; r < runs; r++)
				{
					if (Hash01(141, gx + s, gy + r) >= 0.55f) continue;
					float t0 = (r + 0.2f * Hash01(143, gx + s, gy + r)) / runs;
					float t1 = (r + 0.6f + 0.4f * Hash01(147, gx + s, gy + r)) / runs;
					int ton = Hash01(149, gx + s, gy + r) < 0.6f ? 1 : 3;
					Vector2 a = p1 + (p2 - p1) * t0 + nrm * off, b = p1 + (p2 - p1) * Mathf.Min(t1, 1f) + nrm * off;
					DrawLine(a, b, Ton(col, ton, o), PixelInterne, antialiased: false);
				}
			}
		}

		// ---------------------------------------------------------------------------
		// ANCRAGE — racines en éventail + halo de sol dithéré (arbres, paliers hauts)
		// ---------------------------------------------------------------------------

		private const float AncrageMaxPx = 12f;   // tient dans la marge de cuisson (BakePadPx)

		private void DrawAncrage()
		{
			if (Port() != "arbre") return;
			float tronc = Mathf.Max(PixelInterne,
				Mathf.Round(_epaisseurMaxCm * WorldView.PxPerCmX * WoodWidthFactor));
			// Halo : couronne en trame (dither) puis disque plein, au ton ombre du sol.
			float rx = Mathf.Min(tronc * 1.6f, AncrageMaxPx), ry = rx * 0.5f;
			RemplirTrame(EllipsePoints(Vector2.Zero, rx, ry, 16), HaloSol);
			DrawColoredPolygon(EllipsePoints(Vector2.Zero, rx * 0.65f, ry * 0.65f, 16), Ton(HaloSol, 1));
			// Racines : 4-5 doigts en éventail au sol, orientés vers l'extérieur et le haut.
			int g = GraineIndividu, nR = 4 + (Hash01(151, g, 0) < 0.5f ? 1 : 0);
			float a0 = Hash01(153, g, 0) * Mathf.Tau;
			float pxCm = WorldView.PxPerCmX;
			for (int k = 0; k < nR; k++)
			{
				float a = a0 + Mathf.Tau * (k + 0.3f * Hash01(155, g, k)) / nR;
				var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
				var perp = new Vector2(-dir.Y, dir.X);
				float lCm = Mathf.Min(_epaisseurMaxCm * (1f + 0.6f * Hash01(157, g, k)), AncrageMaxPx / pxCm);
				float bw = _epaisseurMaxCm * 0.22f;
				Vector2 bout = Iso(dir.X * lCm, dir.Y * lCm, 0f);
				var tri = new[] { Iso(perp.X * bw, perp.Y * bw, 0f), bout, Iso(-perp.X * bw, -perp.Y * bw, 0f) };
				int o = Orientation(bout.Normalized() + new Vector2(0f, -0.6f));
				DrawColoredPolygon(tri, Ton(WoodColor, PaletteIndexee.TonBase, o));
			}
		}

		// Trame : la bande dithérée de la texture (un pixel sur deux) sur le contour.
		private void RemplirTrame(Vector2[] pts, Color col)
		{
			AssurerMotifs();
			float z = WorldView.CurrentZoom;
			bool idx = Indexe;
			Color mod = idx ? PaletteIndexee.ModulatePiece(PaletteIndexee.Palette(col)) : RampeLitterale(col)[1];
			// Calé sur le coin du contour (petit : ≤ 2 × AncrageMaxPx × zoom ≤ 768 px
			// à ×32 — la trame est périodique de 2 px, un débord de bande reste juste).
			var uv = new Vector2[pts.Length];
			Vector2 o = (pts[0] * z).Floor();
			for (int k = 0; k < pts.Length; k++)
				uv[k] = new Vector2((BandeTrame * MotifB + 128f + pts[k].X * z - o.X) / (MotifB * MotifBandes),
									((idx ? 0f : MotifB) + 128f + pts[k].Y * z - o.Y) / (2f * MotifB));
			DrawColoredPolygon(pts, mod, uv, _motifTex);
		}

		// ---------------------------------------------------------------------------
		// TEXTURE — générée une fois (octets bruts, pas de SetPixel par texel)
		// ---------------------------------------------------------------------------

		private static void AssurerMotifs()
		{
			if (_motifTex != null) return;
			int l = MotifB * MotifBandes, h = 2 * MotifB;
			var octets = new byte[l * h * 4];
			// Estampille commune à toutes les bandes (mêmes formes : pas de couture
			// entre quartiers d'un limbe, seule l'orientation change).
			var motif = new int[MotifB * MotifB];   // n° de motif, −1 = creux
			var ton = new byte[MotifB * MotifB];
			System.Array.Fill(motif, -1);
			int id = 0;
			for (int cy = 0; cy < MotifB; cy += MotifPas)
				for (int cx = 0; cx < MotifB; cx += MotifPas, id++)
				{
					if (Hash01(161, cx, cy) >= 0.9f) continue;
					var f = Formes[(int)(Hash01(163, cx, cy) * Formes.Length) % Formes.Length];
					int jx = cx + (int)(Hash01(165, cx, cy) * 2f), jy = cy + (int)(Hash01(167, cx, cy) * 2f);
					for (int y = 0; y < f.Length; y++)
						for (int x = 0; x < f[y].Length; x++)
						{
							if (f[y][x] == '.') continue;
							int px = (jx + x) % MotifB, py = (jy + y) % MotifB;
							motif[py * MotifB + px] = id;
							ton[py * MotifB + px] = (byte)(f[y][x] == '1' ? 1 : PaletteIndexee.TonBase);
						}
				}
			for (int b = 0; b < MotifBandes; b++)
				for (int y = 0; y < MotifB; y++)
					for (int x = 0; x < MotifB; x++)
					{
						int i = y * MotifB + x;
						byte code; bool plein = true;
						if (b == BandeTrame)
						{
							plein = ((x + y) & 1) == 0;
							code = PaletteIndexee.OctetB(1, PaletteIndexee.OrientPlat);
						}
						else if (motif[i] < 0 || (b is 1 or 2 or 3 && Hash01(169, motif[i], b) < 0.25f))
							code = PaletteIndexee.OctetB(0, PaletteIndexee.OrientPlat);   // creux (plus nombreux en bas)
						else
							code = PaletteIndexee.OctetB(ton[i], OrientMotif(b, motif[i]));
						if (!plein) continue;
						int t = (code >> 4) & 7, o = code & 15;
						byte gris = (byte)(255f * GrisTon[Mathf.Clamp(t + Bosse(o), 0, 4)]);
						Poser(octets, l, b * MotifB + x, y, 255, 255, code);              // codes
						Poser(octets, l, b * MotifB + x, MotifB + y, gris, gris, gris);   // littéral
					}
			_motifTex = ImageTexture.CreateFromImage(Image.CreateFromData(l, h, false, Image.Format.Rgba8, octets));
		}

		// Littéral : part de l'éclat de la rampe par ton (creux … éclat).
		private static readonly float[] GrisTon = { 0.4f, 0.62f, 0.8f, 0.92f, 1f };

		// Orientation d'un motif dans la bande `b` : celle du quartier (dôme), parfois
		// voisine (±45°) ; au cœur, mêlée au hash (dont « plat »).
		private static int OrientMotif(int b, int m)
		{
			float h = Hash01(171, m, b);
			if (b == BandeCoeur) return h < 0.3f ? PaletteIndexee.OrientPlat : (int)(Hash01(173, m, 0) * 8f) & 7;
			return h < 0.15f ? (b + 7) & 7 : h < 0.3f ? (b + 1) & 7 : b;
		}

		private static void Poser(byte[] o, int l, int x, int y, byte r, byte g, byte b)
		{
			int i = (y * l + x) * 4;
			o[i] = r; o[i + 1] = g; o[i + 2] = b; o[i + 3] = 255;
		}
	}
}
