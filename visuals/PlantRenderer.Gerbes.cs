// SYMBIOSE — PlantRenderer.Gerbes.cs (partial, sprint HOUPPIER ④)
// L'ATLAS DE GERBES : une gerbe est un petit rameau garni, brindilles et feuilles déjà montées,
// en une seule pièce. Le ⑤ en couvrira le houppier d'un arbre à bas prix : poser une gerbe = un
// seul tracé, là où les mêmes feuilles posées une à une en coûteraient des dizaines.
// Ce tronçon la génère sans encore la poser : aucun arbre ne change d'aspect.
//
//  • UNE GERBE par forme de feuille × palier (×0,5, ×1, ×2, ×4) × variante au hash.
//    À ×8 et au-delà, pas de gerbe : la feuille se dessine vraiment, sur rameaux dérivés.
//  • DEUX COUCHES par gerbe, bois et feuilles, deux rectangles de même taille : l'hiver ne pose
//    que le bois, et la dentelle se lit.
//  • MÊMES CODES que le kit (canal G, PaletteIndexee) : la teinte vient du `modulate` à la pose,
//    la lumière du shader. Le canal R (niveaux) ne sert qu'à la planche de contrôle.
//  • ANCRAGE : le pied du rameau est le milieu du bas de la pièce (GerbePied).
//
// Tailles : une gerbe couvre ~30 cm, soit 6, 12, 23 et 47 px internes à PxPerCmX (0,39 × zoom),
// arrondis à 8, 14, 24, 48 pour que les touffes (3 à 9 px) y tiennent. RAM : calcul ci-dessous,
// 6 formes × 4 variantes × 2 couches × 3 140 px² = 150 720 px utiles. Une fois rangés sur une
// texture de 1024×221, 0,86 Mo en RGBA8 ; le cache de cuisson de `houppiers_25` en prend 64.
//
// 📖 Pédagogie : un tableau d'octets plutôt que `Image.SetPixel`. SetPixel traverse la frontière
// C#→moteur à chaque pixel ; ici on écrit dans un `byte[]` puis on le donne d'un coup à
// `Image.CreateFromData`. Comme remplir un buffer puis lancer un seul transfert DMA.
//
// Déterministe (canaux 501-513 au hash, zéro Random, philo #3).

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		internal enum CoucheGerbe { Bois, Feuilles }

		// Par palier (×0,5, ×1, ×2, ×4) : côté de la pièce, taille de touffe, brindilles, largeur du rameau.
		private static readonly int[] GerbeCotes = { 8, 14, 24, 48 };
		private static readonly int[] GerbeTouffes = { 3, 3, 5, 9 };
		private static readonly int[] GerbeBrindilles = { 1, 2, 3, 4 };
		private static readonly int[] GerbeLargeurs = { 1, 1, 1, 2 };
		internal const int GerbeVariantes = 4;
		private const int GerbeAtlasLargeur = 1024;

		private static Image _gerbesNiveaux;
		private static ImageTexture _gerbesCodes;
		private static readonly Dictionary<(LeafShape, int, int, CoucheGerbe), Rect2I> _gerbes = new();

		/// <summary>Atlas des niveaux (R) et des codes (G), généré une seule fois.</summary>
		internal static Image GerbesNiveaux { get { AssurerGerbes(); return _gerbesNiveaux; } }

		/// <summary>Le palier de gerbes du zoom, ou −1 : à ×8 et au-delà, pas de gerbe.</summary>
		internal static int PalierGerbe(float zoom) =>
			zoom < 1f ? 0 : zoom < 2f ? 1 : zoom < 4f ? 2 : zoom < 8f ? 3 : -1;

		/// <summary>Position du pied du rameau dans une pièce de côté `n`.</summary>
		private static Vector2I GerbePied(int n) => new(n / 2, n - 1);

		private static Rect2I GerbeRect(LeafShape s, int palier, int variante, CoucheGerbe couche)
		{
			AssurerGerbes();
			return _gerbes[(s, palier, variante, couche)];
		}

		/// <summary>Pose indexée d'une gerbe, pied en `pied` (px canvas locaux), calée sur la grille
		/// des px internes, comme DrawPieceIndexee.</summary>
		private void DrawGerbeIndexee(LeafShape s, int palier, int variante, CoucheGerbe couche, Vector2 pied, float z, int palette)
		{
			Rect2I r = GerbeRect(s, palier, variante, couche);
			Vector2 coin = ((pied * z) - (Vector2)GerbePied(r.Size.X)).Round() / z;
			DrawTextureRectRegion(_gerbesCodes, new Rect2(coin, (Vector2)r.Size / z), (Rect2)r, PaletteIndexee.ModulatePiece(palette));
		}

		/// <summary>La pièce de l'écran de chargement : une touffe du kit, teintée.</summary>
		internal static Image TouffeChargement() =>
			TeindreKit(KitTouffe(LeafShape.Elliptique, KitTailles[^1], 0), RampeKit(new Color("3f9e3a")));

		// --- Construction -----------------------------------------------------

		/// <summary>Génère l'atlas et l'envoie au GPU, une fois. Appelé par l'écran de chargement ;
		/// à la 1ʳᵉ demande sinon (bancs de capture).</summary>
		internal static void AssurerGerbes()
		{
			if (_gerbesNiveaux != null) return;
			ulong t0 = Time.GetTicksUsec();
			var formes = (LeafShape[])System.Enum.GetValues(typeof(LeafShape));
			int hauteur = RangerGerbes(formes);
			var rg = new byte[GerbeAtlasLargeur * hauteur * 2];
			var touffes = new Dictionary<(LeafShape, int, int), (byte[] Niv, byte[] Codes)>();
			foreach (var forme in formes)
				for (int p = 0; p < GerbeCotes.Length; p++)
					for (int v = 0; v < GerbeVariantes; v++)
						PeindreGerbe(rg, hauteur, forme, p, v, touffes);
			_gerbesNiveaux = Image.CreateFromData(GerbeAtlasLargeur, hauteur, false, Image.Format.Rg8, rg);
			// Texel = (1, 1, code, 1) : × modulate (palette, palette, 1, 1) = pixel encodé, comme _kitCodes.
			var rgba = new byte[GerbeAtlasLargeur * hauteur * 4];
			for (int i = 0; i < GerbeAtlasLargeur * hauteur; i++)
			{
				byte code = rg[i * 2 + 1];
				if (code == 0) continue;
				rgba[i * 4] = 255; rgba[i * 4 + 1] = 255; rgba[i * 4 + 2] = code; rgba[i * 4 + 3] = 255;
			}
			_gerbesCodes = ImageTexture.CreateFromImage(Image.CreateFromData(GerbeAtlasLargeur, hauteur, false, Image.Format.Rgba8, rgba));
			GD.Print($"[Chargement] atlas de gerbes : {GerbeAtlasLargeur}×{hauteur} px, {rgba.Length / 1048576.0:F2} Mo, "
				+ $"{_gerbes.Count} pièces, {(Time.GetTicksUsec() - t0) / 1000.0:F1} ms.");
		}

		// Rangement en étagères, du plus petit au plus grand côté. Rend la hauteur totale.
		private static int RangerGerbes(LeafShape[] formes)
		{
			int x = 0, y = 0;
			for (int p = 0; p < GerbeCotes.Length; p++)
			{
				int n = GerbeCotes[p];
				foreach (var forme in formes)
					for (int v = 0; v < GerbeVariantes; v++)
						foreach (var couche in new[] { CoucheGerbe.Bois, CoucheGerbe.Feuilles })
						{
							if (x + n > GerbeAtlasLargeur) { x = 0; y += n + 1; }
							_gerbes[(forme, p, v, couche)] = new Rect2I(x, y, n, n);
							x += n + 1;
						}
				x = 0; y += n + 1;
			}
			return y;
		}

		// Un rameau qui monte depuis le pied, des brindilles alternées, une touffe au bout de chacune
		// et le long de la moitié haute du rameau. Le bois est tracé en entier dans sa couche, même
		// sous les feuilles : l'hiver, il est seul à l'écran.
		private static void PeindreGerbe(byte[] rg, int h, LeafShape forme, int p, int v,
			Dictionary<(LeafShape, int, int), (byte[] Niv, byte[] Codes)> touffes)
		{
			int n = GerbeCotes[p], graine = (int)forme * 16 + p, t = GerbeTouffes[p];
			float hg(int canal, int k) => Hash01(canal, graine, v * 64 + k);
			Rect2I bois = _gerbes[(forme, p, v, CoucheGerbe.Bois)], feuilles = _gerbes[(forme, p, v, CoucheGerbe.Feuilles)];
			Vector2 pied = (Vector2)GerbePied(n) + new Vector2(0.5f, 0.5f);
			float axe = -Mathf.Pi * 0.5f + (hg(501, 0) - 0.5f) * 0.7f;
			Vector2 bout = Dans(pied + new Vector2(Mathf.Cos(axe), Mathf.Sin(axe)) * n * 0.82f, n, t);
			TracerBois(rg, h, bois, pied, bout, GerbeLargeurs[p], KitOmbre);
			var sites = new List<Vector2> { bout };
			int nb = GerbeBrindilles[p];
			for (int k = 0; k < nb; k++)
			{
				float u = 0.3f + 0.6f * (k + hg(503, k) * 0.6f) / nb;
				float cote = k % 2 == 0 ? 1f : -1f;
				if (hg(505, 0) < 0.5f) cote = -cote;
				float a = axe + cote * (0.6f + 0.5f * hg(507, k));
				Vector2 depart = pied.Lerp(bout, u);
				Vector2 fin = Dans(depart + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * n * (0.32f + 0.2f * hg(509, k)), n, t);
				TracerBois(rg, h, bois, depart, fin, 1, KitBase);
				sites.Add(fin);
				sites.Add(depart.Lerp(fin, 0.55f));
			}
			sites.Add(pied.Lerp(bout, 0.62f));
			sites.Sort((a, b) => a.Y.CompareTo(b.Y));   // du fond vers l'avant, comme les touffes
			for (int k = 0; k < sites.Count; k++)
			{
				int taille = k % 3 == 2 && t > KitTailles[0] ? KitTailles[System.Array.IndexOf(KitTailles, t) - 1] : t;
				int vt = (int)(hg(511, k) * KitVariantes) % KitVariantes;
				if (!touffes.TryGetValue((forme, taille, vt), out var piece))
					touffes[(forme, taille, vt)] = piece = PeindreTouffe(forme, taille, vt);
				EstamperTouffe(rg, h, feuilles, sites[k], piece, taille);
			}
		}

		// Une touffe doit tenir entière dans la pièce : le rectangle voisin n'est pas à elle.
		private static Vector2 Dans(Vector2 p, int n, int t) =>
			new(Mathf.Clamp(p.X, t * 0.5f, n - t * 0.5f), Mathf.Clamp(p.Y, t * 0.5f, n - t * 0.5f));

		private static void EstamperTouffe(byte[] rg, int h, Rect2I r, Vector2 centre, (byte[] Niv, byte[] Codes) piece, int t)
		{
			int ox = Mathf.FloorToInt(centre.X - t * 0.5f), oy = Mathf.FloorToInt(centre.Y - t * 0.5f);
			for (int y = 0; y < t; y++)
				for (int x = 0; x < t; x++)
				{
					int i = y * t + x, px = ox + x, py = oy + y;
					if (piece.Niv[i] == KitVide || px < 0 || py < 0 || px >= r.Size.X || py >= r.Size.Y) continue;
					// Le contour (R seul, code 0) n'efface pas la feuille de derrière dans le canal des codes.
					Poser(rg, r, px, py, piece.Niv[i], piece.Codes[i] != 0 ? piece.Codes[i] : Code(rg, r, px, py));
				}
		}

		// Trait de bois au pas d'un pixel (tenu dans la pièce). Ton sombre, face plate : pas de volume
		// sur un rameau de 1 px, le bois se distingue par son n° de palette.
		private static void TracerBois(byte[] rg, int h, Rect2I r, Vector2 a, Vector2 b, int largeur, byte niveau)
		{
			byte code = PaletteIndexee.OctetB(niveau == KitOmbre ? 1 : PaletteIndexee.TonBase, PaletteIndexee.OrientPlat);
			int pas = Mathf.Max(1, Mathf.CeilToInt(a.DistanceTo(b)));
			for (int k = 0; k <= pas; k++)
			{
				Vector2 q = a.Lerp(b, k / (float)pas);
				for (int l = 0; l < largeur; l++)
				{
					int x = Mathf.FloorToInt(q.X) + l, y = Mathf.FloorToInt(q.Y);
					if (x >= 0 && y >= 0 && x < r.Size.X && y < r.Size.Y) Poser(rg, r, x, y, niveau, code);
				}
			}
		}

		private static void Poser(byte[] rg, Rect2I r, int x, int y, byte niveau, byte code)
		{
			int i = ((r.Position.Y + y) * GerbeAtlasLargeur + r.Position.X + x) * 2;
			rg[i] = niveau;
			rg[i + 1] = code;
		}

		private static byte Code(byte[] rg, Rect2I r, int x, int y) =>
			rg[((r.Position.Y + y) * GerbeAtlasLargeur + r.Position.X + x) * 2 + 1];
	}
}
