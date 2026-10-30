// SYMBIOSE — FauneIcones.cs (sprint CASSÉ À L'ÉCRAN ⑤ — faune en icônes)
// Cuisson et pose des PORTRAITS de bêtes : chaque silhouette (FauneSilhouettes)
// est rastérisée UNE fois par (espèce, taille en px, cap) dans un atlas de pixels
// INDEXÉS (encodage de la palette indexée ③, cf. PaletteIndexee.cs) ; les couches
// (MacroLife, ForagerLayer) posent ensuite chaque bête comme UN quad texturé dans
// leur lot de triangles → un seul envoi GPU par couche, comme avant.
//
// 📖 Pédagogie — pourquoi précuire par TAILLE plutôt qu'agrandir une image : en
// pixel-art, un portrait de 9 px n'est pas un portrait de 36 px réduit — c'est un
// autre dessin (moins de détails, pas de contour). Les paliers de zoom étant
// discrets (×0,5 … ×32), une bête n'a que quelques tailles possibles : on cuit
// chacune au pixel près, à la demande, et on la garde (mémoïsation, jamais de
// recalcul). Au-delà de 128 px on cuit plus petit et on pose en blocs ENTIERS k×k
// (×2, ×3…) : les pixels restent carrés.
//
// 📖 Le volume vient du SOLEIL, pas de la cuisson : chaque pixel de dôme porte
// l'orientation de sa face (8 directions) ; le shader de la palette indexée monte
// le ton côté soleil (éclat) et le descend à l'opposé. Le contour (1 px, à partir
// de 8 px) = le ton 0 de la rampe de la partie — jamais du noir (règle 7 du brief).
// Cap de la bête : 8 variantes précuites, choisies au hash de la clé (pas de
// rotation de sprite, pas de Random). Vue pure, déterministe : golden non concerné.

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	internal static class FauneIcones
	{
		private const int AtlasPx = 1024;
		/// <summary>Sous cette longueur (px internes), la bête reste un point de sa couleur.</summary>
		public const float IconeMinPx = 3f;
		private const int TailleMaxPx = 128;   // au-delà : cuisson réduite posée en blocs k×k
		private const int DetailMinPx = 8;     // détails « Fin », motifs et contour dès 8 px
		private const int GrainMinPx = 24;     // texture anti-aplat (APLAT_MAX du banc = 24 px)
		private const int Caps = 8;            // orientations précuites (k × 45°)
		private const float AmpSerpent = 0.12f, OndesSerpent = 1.5f;
		// Vue OBLIQUE : le sol iso 2:1 est écrasé de moitié (PxPerCmY / PxPerCmX = 0,5),
		// mais une bête écrasée d'autant devient un bâton (merle de profil = un cigare,
		// vu au banc ⑤) ; 0,7 = un dessus vu de trois-quarts, lisible à tout cap.
		private const float Ecrasement = 0.7f;

		private readonly record struct Portrait(Rect2 Uv, Vector2 Taille, Vector2 Pivot);
		private static readonly Dictionary<(string, int, int), Portrait> _cache = new();
		private static Image _img;
		private static ImageTexture _tex;
		private static bool _sale;
		private static int _x, _y, _hRangee, _gen = -1;

		/// <summary>Atlas des portraits (à passer à LotTriangles.Dessiner).</summary>
		public static Texture2D Texture { get { Assurer(); return _tex; } }

		/// <summary>Pose la bête `espece` centrée en `centre` (px canvas), longue de
		/// `longPx` px INTERNES ; `px1` = 1 px interne en px canvas (1 / zoom). Sous
		/// IconeMinPx : un point `pointPx` (largeur, hauteur canvas) de sa couleur.</summary>
		public static void Poser(LotTriangles lot, string espece, Vector2 centre, float longPx,
								 Vector2 pointPx, float px1, uint phase, float alpha)
		{
			var sil = FauneSilhouettes.De(espece);
			Assurer();
			var mod = new Color(1f, 1f, 1f, alpha);
			if (longPx < IconeMinPx)
			{
				var pt = Obtenir(espece, sil, 1, 0);
				// UV au CENTRE du texel : un point étiré ne bave pas sur le voisin.
				var uv = new Rect2(pt.Uv.Position + pt.Uv.Size * 0.25f, pt.Uv.Size * 0.5f);
				lot.Quad(new Rect2(centre - pointPx * 0.5f, pointPx), uv, mod);
				return;
			}
			int k = Mathf.Max(1, Mathf.CeilToInt(longPx / TailleMaxPx));
			int n = Mathf.Max((int)IconeMinPx, Mathf.RoundToInt(longPx / k));
			var p = Obtenir(espece, sil, n, (int)((phase >> 16) % Caps));
			float e = px1 * k;
			// Calé sur la grille des px internes : texel ↔ pixel, sans demi-pixel.
			Vector2 o = centre - p.Pivot * e;
			o = new Vector2(Mathf.Round(o.X / px1) * px1, Mathf.Round(o.Y / px1) * px1);
			lot.Quad(new Rect2(o, p.Taille * e), p.Uv, mod);
		}

		/// <summary>Envoie l'atlas au GPU si un portrait a été cuit (fin de _Draw).</summary>
		public static void Televerser()
		{
			if (!_sale) return;
			_tex.Update(_img);
			_sale = false;
		}

		private static void Assurer()
		{
			if (_img == null)
			{
				_img = Image.CreateEmpty(AtlasPx, AtlasPx, false, Image.Format.Rgba8);
				_tex = ImageTexture.CreateFromImage(_img);
			}
			// La LUT a été vidée (n° de palette réattribués) → les portraits sont périmés.
			if (_gen != PaletteIndexee.Generation) { Vider(); _gen = PaletteIndexee.Generation; }
		}

		private static void Vider()
		{
			_cache.Clear();
			_img.Fill(new Color(0f, 0f, 0f, 0f));
			_x = _y = _hRangee = 0;
			_sale = true;
		}

		private static Portrait Obtenir(string espece, SilhouetteFaune sil, int n, int cap)
		{
			if (_cache.TryGetValue((espece, n, cap), out var p)) return p;
			var (px, w, h, pivot) = Rasteriser(sil, n, cap);
			if (!Placer(w, h, out int x0, out int y0))
			{
				GD.Print("[FauneIcones] atlas plein → vidé (portraits recuits à la demande).");
				Vider();
				Placer(w, h, out x0, out y0);
			}
			for (int j = 0; j < h; j++)
				for (int i = 0; i < w; i++)
					if (px[j * w + i].A > 0f) _img.SetPixel(x0 + i, y0 + j, px[j * w + i]);
			_sale = true;
			p = new Portrait(new Rect2(x0 / (float)AtlasPx, y0 / (float)AtlasPx, w / (float)AtlasPx, h / (float)AtlasPx),
							 new Vector2(w, h), pivot);
			_cache[(espece, n, cap)] = p;
			return p;
		}

		// Rangement en étagères (1 px d'écart : le filtrage « nearest » ne bave jamais).
		private static bool Placer(int w, int h, out int x0, out int y0)
		{
			if (_x + w > AtlasPx) { _y += _hRangee + 1; _x = 0; _hRangee = 0; }
			x0 = _x; y0 = _y;
			if (_y + h > AtlasPx || w > AtlasPx) return false;
			_x += w + 1;
			_hRangee = Mathf.Max(_hRangee, h);
			return true;
		}

		// ── Rastérisation d'un portrait ─────────────────────────────────────────
		// Pour chaque pixel : centre écran → plan du sol (y désécrasé) → repère du
		// corps (rotation du cap) → dernière partie qui le contient. Renvoie les
		// pixels codés recadrés, leurs dimensions et le pivot (centre du corps).
		private static (Color[] Px, int W, int H, Vector2 Pivot) Rasteriser(SilhouetteFaune sil, int n, int cap)
		{
			if (n <= 1)   // un point : la couleur du corps, ton de base, plat
				return (new[] { PaletteIndexee.Code(PaletteIndexee.Palette(sil.Couleurs[0])) }, 1, 1, new Vector2(0.5f, 0.5f));
			float s = n / 2f;                                  // px par unité du corps
			float rMin = 0.5f / (s * Ecrasement);              // une partie fait ≥ ~1 px
			bool details = n >= DetailMinPx;
			float r = sil.Serpent ? 1f + AmpSerpent : 0f;
			foreach (var q in sil.Parties)
				r = Mathf.Max(r, Mathf.Max(Mathf.Abs(q.U) + q.Ru, Mathf.Abs(q.V) + q.Rv) + rMin);
			int hx = Mathf.CeilToInt(r * s) + 1, hy = Mathf.CeilToInt(r * s * Ecrasement) + 1;
			int w = 2 * hx, h = 2 * hy;
			float ang = cap * Mathf.Pi / 4f, cs = Mathf.Cos(ang), sn = Mathf.Sin(ang);
			var px = new Color[w * h];
			var parti = new int[w * h];                        // n° de partie + 1 (0 = vide)
			for (int y = 0; y < h; y++)
				for (int x = 0; x < w; x++)
				{
					float dx = x + 0.5f - hx, dy = (y + 0.5f - hy) / Ecrasement;
					float u = (dx * cs + dy * sn) / s, v = (-dx * sn + dy * cs) / s;
					if (sil.Serpent) v -= AmpSerpent * Mathf.Sin(u * Mathf.Pi * OndesSerpent);
					int best = -1; float bu = 0f, bv = 0f, bd = 0f;
					for (int i = 0; i < sil.Parties.Length; i++)
					{
						var q = sil.Parties[i];
						if (q.Fin && !details) continue;
						float ru = Mathf.Max(q.Ru, rMin), rv = Mathf.Max(q.Rv, rMin);
						for (int m = 0; m < (q.Miroir ? 2 : 1); m++)
						{
							float du = u - q.U, dv = v - (m == 0 ? q.V : -q.V);
							float d = du * du / (ru * ru) + dv * dv / (rv * rv);
							if (d <= 1f) { best = i; bu = du / ru; bv = dv / rv; bd = d; }
						}
					}
					if (best < 0) continue;
					parti[y * w + x] = best + 1;
					px[y * w + x] = Coder(sil, sil.Parties[best], u, v, bu, bv, bd, cs, sn, s, x, y, cap, n);
				}
			if (details) Contourer(sil, px, parti, w, h);
			return Recadrer(px, w, h, new Vector2(hx, hy));
		}

		// Ton + orientation d'un pixel de la partie `q` (cf. en-tête de FauneSilhouettes).
		// (u, v) = repère du corps ; (du, dv) = écart au centre de la partie NORMALISÉ
		// par ses rayons, d = sa norme² ; s = px par unité du corps.
		private static Color Coder(SilhouetteFaune sil, PartieFaune q, float u, float v, float du, float dv,
								   float d, float cs, float sn, float s, int x, int y, int cap, int n)
		{
			int pal = PaletteIndexee.Palette(sil.Couleurs[q.Couleur]);
			int ton = q.Ton >= 0 ? q.Ton : PaletteIndexee.TonBase, orient = PaletteIndexee.OrientPlat;
			if (q.Ton < 0 && d > 0.25f)   // couronne du dôme : la face regarde vers l'extérieur
			{
				// Normale du corps → plan du sol (rotation inverse du cap), repère écran.
				float nx = du * cs - dv * sn, ny = du * sn + dv * cs;
				orient = Mathf.PosMod(Mathf.RoundToInt(Mathf.Atan2(ny, nx) / (Mathf.Pi / 4f)), 8);
			}
			if (n >= DetailMinPx && q.Ton < 0)
				switch (q.Motif)
				{
					case MotifFaune.Bandes when Mathf.PosMod(Mathf.FloorToInt((u + 1f) * 4f), 2) == 1:
						ton = 0; orient = PaletteIndexee.OrientPlat; break;
					case MotifFaune.Segments when Mathf.PosMod(Mathf.FloorToInt((u + 1f) * 5f), 2) == 1:
						ton = 1; break;
					case MotifFaune.Ecailles when Mathf.PosMod(Mathf.FloorToInt((u + 1f) * 14f), 2) == 1:
						ton = 1; break;
					case MotifFaune.Piquants:
						uint g = (uint)(x * 73856093) ^ (uint)(y * 19349663) ^ (uint)(cap * 83492791);
						if (g % 7u < 3u) ton = 1; else if (g % 7u == 3u) ton = 3;
						break;
				}
			if (n >= GrainMinPx && !q.Fin) ton = Mathf.Clamp(ton + Plumage(u * s, v * s), 0, 4);
			return PaletteIndexee.Code(pal, ton, orient);
		}

		// Texture des GRANDES icônes (dès 24 px) : un pavage de plumes / écailles de
		// 4 × 3 px du corps, décalé d'une rangée à l'autre (appareil de briques) —
		// bord arrière d'une plume un ton plus sombre, bord bas un ton plus clair. Les
		// deux liserés ne se touchent jamais : aucun ton ne forme d'aplat > 6 px (le
		// « motif 3×4 » du brief, comme les limbes ④). Calé sur le corps : il tourne
		// avec la bête. Sur les ailes : des nervures.
		private static int Plumage(float bu, float bv)
		{
			int rang = Mathf.FloorToInt(bv / 3f);
			int col = Mathf.PosMod(Mathf.FloorToInt(bu + (rang % 2 != 0 ? 2f : 0f)), 4);
			if (col == 0) return -1;
			return Mathf.PosMod(Mathf.FloorToInt(bv), 3) == 2 ? 1 : 0;
		}

		// Contour sélectif : tout pixel de bord (un voisin 4-connexe vide) passe au
		// ton 0 de SA rampe, à plat. Lu sur une copie : le contour ne se propage pas.
		private static void Contourer(SilhouetteFaune sil, Color[] px, int[] parti, int w, int h)
		{
			bool Vide(int x, int y) => x < 0 || y < 0 || x >= w || y >= h || parti[y * w + x] == 0;
			for (int y = 0; y < h; y++)
				for (int x = 0; x < w; x++)
				{
					int i = parti[y * w + x];
					if (i == 0 || !(Vide(x - 1, y) || Vide(x + 1, y) || Vide(x, y - 1) || Vide(x, y + 1))) continue;
					px[y * w + x] = PaletteIndexee.Code(PaletteIndexee.Palette(sil.Couleurs[sil.Parties[i - 1].Couleur]), 0);
				}
		}

		private static (Color[], int, int, Vector2) Recadrer(Color[] px, int w, int h, Vector2 pivot)
		{
			int x0 = w, y0 = h, x1 = -1, y1 = -1;
			for (int y = 0; y < h; y++)
				for (int x = 0; x < w; x++)
					if (px[y * w + x].A > 0f)
					{
						x0 = Mathf.Min(x0, x); x1 = Mathf.Max(x1, x);
						y0 = Mathf.Min(y0, y); y1 = Mathf.Max(y1, y);
					}
			if (x1 < 0) return (new Color[1], 1, 1, new Vector2(0.5f, 0.5f));   // rien de visible
			int cw = x1 - x0 + 1, ch = y1 - y0 + 1;
			var r = new Color[cw * ch];
			for (int y = 0; y < ch; y++)
				for (int x = 0; x < cw; x++)
					r[y * cw + x] = px[(y + y0) * w + x + x0];
			return (r, cw, ch, pivot - new Vector2(x0, y0));
		}
	}
}
