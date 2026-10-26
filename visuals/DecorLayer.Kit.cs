// SYMBIOSE — DecorLayer.Kit.cs (FLUIDITÉ PC ③ — l'ATLAS « patchwork » de la lisière)
// Partial de DecorLayer : génère UNE fois les petites pièces pixel-art du décor
// (touffes d'herbe, herbes sèches, fleurettes, ronciers, sous-bois, bouquets de
// feuillage et d'aiguilles des houppiers) et les range, teintées, dans UNE texture.
// Les motifs (DecorLayer.Patchwork.cs, DecorLayer.Houppiers.cs) ne font ensuite
// que POSER ces pièces au hash ; ici aucune règle de placement, seulement le kit.
//
// 📖 Pédagogie — même langage que le kit des plantes (PlantRenderer.Kit.cs) :
// une pièce est d'abord peinte en NIVEAUX de rampe (0 vide · 1 contour · 2 ombre ·
// 3 base · 4 lumière · 5 cœur), comme un buffer d'indices de palette en
// embarqué ; puis chaque niveau est remplacé par la couleur de la rampe d'une
// TEINTE (PlantRenderer.RampeKit : même hue-shift que les plantes → le décor et
// le jardin parlent la même langue). Lumière venue du SUD-OUEST = bas-gauche de
// la pièce (la calotte claire des anciens houppiers, le soleil de la maison).
//
// 📖 Pédagogie — POURQUOI une seule texture : le GPU paie les ENVOIS, pas les
// pixels. Toutes les pièces, dans toutes leurs teintes, vivent dans le même
// atlas ; un texel blanc y sert aussi aux aplats (couleur de sommet × blanc).
// Le décor entier reste donc UN DrawMesh (LotTriangles), comme avant ③.
// Zéro Random (philo #3) : variantes tirées d'un hash fixe à la génération.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// Formes du kit. Chaque forme existe en plusieurs TAILLES (px) × 3 variantes.
		private enum Piece { Herbe, HerbeHaute, Fleur, Roncier, SousBois, Feuillu, Conifere }

		// Teintes cuites : une rampe par entrée (RampeKit). L'index est la clé d'atlas.
		private enum Teinte
		{
			PrairieClair, Prairie, Paille, Roncier, SousBois, FleurBlanc, FleurJaune,
			Chene, Hetre, Bouleau, Charme, Sapin,
		}

		private static readonly Color[] TeintesBase =
		{
			Palette16.DecorPrairieClair, Palette16.DecorPrairie, new Color("b2a85c"),
			new Color("557a40"), new Color("44694a"), Palette16.FleurPrairieBlanc,
			Palette16.FleurPrairieJaune, Palette16.FeuillageChene, Palette16.FeuillageHetre,
			Palette16.FeuillageBouleau, Palette16.FeuillageCharme, Palette16.FeuillageSapin,
		};

		// Tailles (largeur, hauteur) par forme, de la plus petite à la plus grande.
		// Tableau indexé par (int)Piece — dans l'ordre de l'enum (accès chaud : un
		// dictionnaire coûtait trop cher sur ~20 000 poses par redessin [VM]).
		private static readonly Vector2I[][] Tailles =
		{
			new Vector2I[] { new(5, 4), new(7, 6), new(9, 7) },     // Herbe
			new Vector2I[] { new(5, 7), new(7, 10), new(9, 12) },   // HerbeHaute
			new Vector2I[] { new(3, 3) },                           // Fleur
			new Vector2I[] { new(7, 5), new(11, 7), new(15, 9) },   // Roncier
			new Vector2I[] { new(7, 4), new(11, 6), new(15, 8) },   // SousBois
			// Bouquets de houppier : 5 tailles, choisies selon la taille de l'ARBRE à
			// l'écran (pas du palier) → un houppier compte toujours ~10-30 bouquets.
			new Vector2I[] { new(7, 6), new(11, 9), new(15, 12), new(19, 15), new(25, 20) },  // Feuillu
			new Vector2I[] { new(5, 7), new(9, 11), new(13, 15), new(17, 19), new(21, 25) },  // Conifere
		};
		private const int NbPieces = 7, NbTaillesMax = 5;
		private const int Variantes = 3;
		private const int AtlasW = 512;
		private const float LumSeuil = 0.30f, OmbreSeuil = -0.25f;
		private static readonly Vector2 Lumiere = new Vector2(-0.45f, 0.89f);   // bas-gauche

		private static ImageTexture _kitTex;
		private static Vector2 _kitTaille;
		// Rectangles de l'atlas, index plat (teinte, forme, taille, variante) → Rect2I.
		private static Rect2I[] _kitRects;
		private static int IndexKit(int t, int f, int taille, int v) =>
			((t * NbPieces + f) * NbTaillesMax + taille) * Variantes + v;

		/// <summary>La texture de l'atlas (générée à la 1ʳᵉ demande, puis partagée).</summary>
		private static ImageTexture KitTexture { get { AssurerKitDecor(); return _kitTex; } }

		/// <summary>UV du texel blanc (2×2 en haut à gauche) : les aplats du lot.</summary>
		private static Vector2 UvBlanc { get { AssurerKitDecor(); return new Vector2(1f, 1f) / _kitTaille; } }

		/// <summary>Index de taille d'une forme selon le palier : ×0,5 la plus
		/// petite, ×1 la moyenne, ×2 et plus la plus grande. `decal` (−1, 0, +1)
		/// = variation par pièce, bornée aux tailles existantes.</summary>
		private static int TailleZoom(Piece f, int decal = 0)
		{
			float z = WorldView.CurrentZoom;
			int i = z <= 0.5f ? 0 : z <= 1f ? 1 : 2;
			return Mathf.Clamp(i + decal, 0, Tailles[(int)f].Length - 1);
		}

		/// <summary>Pose une pièce du kit, son PIED (bas-centre) en `pied` (canvas),
		/// calée sur la grille des px du SubViewport (1 texel = 1 px interne, comme
		/// les touffes des plantes) ; `mod` assombrit (arrière-plan) ou laisse tel quel.</summary>
		private void PoserPiece(Piece f, int taille, uint h, Teinte t, Vector2 pied, Color mod)
		{
			AssurerKitDecor();
			var r = _kitRects[IndexKit((int)t, (int)f, taille, (int)(h % Variantes))];
			float z = WorldView.CurrentZoom;
			Vector2 coin = (pied * z - new Vector2(r.Size.X * 0.5f, r.Size.Y)).Round() / z;
			_lot.Quad(new Rect2(coin, (Vector2)r.Size / z),
					  new Rect2((Vector2)r.Position / _kitTaille, (Vector2)r.Size / _kitTaille), mod);
		}

		/// <summary>Taille d'une pièce en px canvas (pour espacer les poses).</summary>
		private static Vector2 TaillePiece(Piece f, int taille) =>
			(Vector2)Tailles[(int)f][taille] / WorldView.CurrentZoom;

		// --- Génération de l'atlas -----------------------------------------
		// Étagères : chaque pièce de chaque teinte posée de gauche à droite, 1 px de
		// jour entre pièces ; on passe à la ligne quand la largeur est pleine.
		private static void AssurerKitDecor()
		{
			if (_kitTex != null) return;
			var niveaux = new Dictionary<(Piece, int, int), byte[]>();
			for (int f = 0; f < NbPieces; f++)
				for (int i = 0; i < Tailles[f].Length; i++)
					for (int v = 0; v < Variantes; v++)
						niveaux[((Piece)f, i, v)] = PeindrePiece((Piece)f, Tailles[f][i].X, Tailles[f][i].Y, v);
			_kitRects = new Rect2I[TeintesBase.Length * NbPieces * NbTaillesMax * Variantes];
			var places = new List<(Rect2I r, byte[] niv, Color[] rampe)>();
			int x = 3, y = 0, hRang = 3;   // (0..1, 0..1) = texel blanc
			for (int t = 0; t < TeintesBase.Length; t++)
			{
				Color[] rampe = PlantRenderer.RampeKit(TeintesBase[t]);
				foreach (var ((f, i, v), niv) in niveaux)
				{
					Vector2I s = Tailles[(int)f][i];
					if (x + s.X > AtlasW) { x = 0; y += hRang; hRang = 0; }
					var r = new Rect2I(x, y, s.X, s.Y);
					_kitRects[IndexKit(t, (int)f, i, v)] = r;
					places.Add((r, niv, rampe));
					x += s.X + 1;
					hRang = Mathf.Max(hRang, s.Y + 1);
				}
			}
			int hauteur = y + hRang;
			var data = new byte[AtlasW * hauteur * 4];
			foreach (int i in new[] { 0, 1, AtlasW, AtlasW + 1 })
				for (int c = 0; c < 4; c++) data[i * 4 + c] = 255;            // texel blanc
			foreach (var (r, niv, rampe) in places)
				for (int py = 0; py < r.Size.Y; py++)
					for (int px = 0; px < r.Size.X; px++)
					{
						byte n = niv[py * r.Size.X + px];
						if (n == 0) continue;
						Color c = rampe[n];
						int o = ((r.Position.Y + py) * AtlasW + r.Position.X + px) * 4;
						data[o] = (byte)c.R8; data[o + 1] = (byte)c.G8;
						data[o + 2] = (byte)c.B8; data[o + 3] = 255;
					}
			var img = Image.CreateFromData(AtlasW, hauteur, false, Image.Format.Rgba8, data);
			_kitTaille = new Vector2(AtlasW, hauteur);
			_kitTex = ImageTexture.CreateFromImage(img);
		}

		// Hash entier stable d'une pièce (forme, taille, variante, canal) ∈ [0,1).
		private static float H01(Piece f, int w, int v, int canal) =>
			(Melange((uint)f * 7919u ^ (uint)w * 104729u ^ (uint)v * 15485863u ^ (uint)canal * 2654435761u)
			 & 0xffffff) / 16777216f;

		// Une pièce en niveaux. Deux familles : les BRINS (herbes) tracés pixel par
		// pixel, et les MASSES (ronciers, feuillus, aiguilles) = union de disques ou
		// d'étages, ombrées par la normale du disque propriétaire.
		private static byte[] PeindrePiece(Piece f, int w, int hh, int v)
		{
			var niv = new byte[w * hh];
			if (f == Piece.Fleur)
			{
				byte[] etoile = { 0, 3, 0, 3, 5, 3, 0, 4, 0 };
				return etoile;
			}
			if (f == Piece.Herbe || f == Piece.HerbeHaute)
				PeindreBrins(niv, w, hh, v, f == Piece.HerbeHaute);
			else
				PeindreMasse(niv, f, w, hh, v);
			// Contour sombre d'1 px dès 7 px (lisible au-delà). Herbes : tout autour
			// (la touffe se détache). MASSES : côté OMBRE seulement (haut-droite, à
			// l'opposé du soleil SO) — un anneau complet sur chaque bouquet faisait
			// des « bulles » cerclées de noir au F5 VM (capture ③, 1er essai).
			if (w >= 7)
				ContourNiveaux(niv, w, hh, f == Piece.Herbe || f == Piece.HerbeHaute);
			return niv;
		}

		// BRINS : 3-5 brins partent du pied (bas-centre) en éventail ; brins de
		// gauche éclairés, de droite à l'ombre, pointes claires. Herbe HAUTE = brins
		// plus longs et plus couchés (la friche : herbe sèche qui verse).
		private static void PeindreBrins(byte[] niv, int w, int hh, int v, bool haute)
		{
			int nb = w <= 5 ? 3 : w <= 7 ? 4 : 5;
			for (int b = 0; b < nb; b++)
			{
				float tb = nb > 1 ? b / (float)(nb - 1) : 0.5f;           // 0 gauche → 1 droite
				float x0 = w * 0.5f + (tb - 0.5f) * w * 0.35f;
				float pente = (tb - 0.5f) * (haute ? 1.3f : 0.9f) + (H01(Piece.Herbe, w, v, b) - 0.5f) * 0.5f;
				float lg = hh * (0.65f + 0.35f * H01(Piece.Herbe, w, v, b + 9));
				for (int k = 0; k < Mathf.CeilToInt(lg); k++)
				{
					int px = Mathf.Clamp((int)(x0 + pente * k), 0, w - 1);
					int py = hh - 1 - k;
					if (py < 0) break;
					byte n = k >= lg - 1.5f ? (byte)4 : tb < 0.4f ? (byte)4 : tb > 0.6f ? (byte)2 : (byte)3;
					niv[py * w + px] = n;
				}
			}
		}

		// MASSES : union de disques (feuillu, roncier, sous-bois) ou d'étages
		// triangulaires (conifère). Chaque pixel prend l'éclairement de son disque
		// PROPRIÉTAIRE (le plus au sud gagne, comme le kit des plantes) ; ronciers et
		// sous-bois reçoivent des trous sombres (épines, frondes) au hash.
		private static void PeindreMasse(byte[] niv, Piece f, int w, int hh, int v)
		{
			var disques = new List<Vector3>();   // (cx, cy, r)
			if (f != Piece.Conifere)
			{
				int n = f == Piece.Feuillu ? 5 : 4;
				for (int k = 0; k < n; k++)
				{
					float a = H01(f, w, v, k) * Mathf.Tau, rho = 0.55f * Mathf.Sqrt(H01(f, w, v, k + 20));
					float r = Mathf.Min(w, hh * 1.3f) * (0.24f + 0.12f * H01(f, w, v, k + 40));
					disques.Add(new Vector3(w * 0.5f + Mathf.Cos(a) * rho * (w * 0.5f - r),
											hh * 0.55f + Mathf.Sin(a) * rho * (hh * 0.5f - r * 0.8f), r));
				}
				disques.Sort((p, q) => p.Y.CompareTo(q.Y));
			}
			for (int py = 0; py < hh; py++)
				for (int px = 0; px < w; px++)
				{
					var p = new Vector2(px + 0.5f, py + 0.5f);
					float s;
					if (f == Piece.Conifere)
					{
						// 3 étages : demi-largeur ∝ descente dans l'étage (sapin étagé).
						float et = p.Y / hh * 3f, dans = et - Mathf.Floor(et);
						float demi = w * 0.5f * (0.35f + 0.65f * dans) * (0.6f + 0.4f * p.Y / hh);
						float dx = p.X - w * 0.5f;
						if (Mathf.Abs(dx) > demi) continue;
						s = -dx / Mathf.Max(demi, 0.5f) * 0.6f + (dans - 0.5f) * 0.9f;
					}
					else
					{
						int k = -1;
						for (int i = 0; i < disques.Count; i++)
							if (p.DistanceTo(new Vector2(disques[i].X, disques[i].Y)) <= disques[i].Z) k = i;
						if (k < 0) continue;
						var nrm = (p - new Vector2(disques[k].X, disques[k].Y)) / disques[k].Z;
						s = nrm.Dot(Lumiere);
					}
					byte n = s > LumSeuil ? (byte)4 : s < OmbreSeuil ? (byte)2 : (byte)3;
					if ((f == Piece.Roncier || f == Piece.SousBois)
						&& H01(f, w, v, 100 + py * w + px) < (f == Piece.SousBois ? 0.10f : 0.07f))
						n = 1;   // trou sombre : épine, creux entre frondes
					niv[py * w + px] = n;
				}
		}

		// Un pixel VIDE voisin (4-connexité) d'un pixel plein devient contour.
		// `complet = false` : seulement les vides AU-DESSUS ou À DROITE d'un plein
		// (le côté que le soleil du SO n'éclaire pas).
		private static void ContourNiveaux(byte[] niv, int w, int hh, bool complet)
		{
			var plein = (byte[])niv.Clone();
			for (int y = 0; y < hh; y++)
				for (int x = 0; x < w; x++)
				{
					if (plein[y * w + x] != 0) continue;
					bool voisin = (x > 0 && plein[y * w + x - 1] > 1) || (y < hh - 1 && plein[(y + 1) * w + x] > 1)
							   || (complet && ((x < w - 1 && plein[y * w + x + 1] > 1)
											|| (y > 0 && plein[(y - 1) * w + x] > 1)));
					if (voisin) niv[y * w + x] = 1;
				}
		}

		/// <summary>Brassage d'un hash (finaliseur murmur3 « fmix32 ») : chaque bit
		/// d'entrée touche tous les bits de sortie. 📖 Le djb2-xor de HashKey ne
		/// mélange que les bits BAS quand les clés ne diffèrent que du dernier
		/// caractère (cf. D92) — d'où la forêt O « 13 bouleaux au bout SO » du
		/// bilan ②. Tout tirage du kit passe donc par Melange.</summary>
		private static uint Melange(uint h)
		{
			h ^= h >> 16; h *= 0x85ebca6bu;
			h ^= h >> 13; h *= 0xc2b2ae35u;
			h ^= h >> 16;
			return h;
		}

		/// <summary>Hash brassé de (graine, i, j) — tirage par cellule de grille.</summary>
		private static uint HashCase(uint graine, int i, int j, uint canal = 0u) =>
			Melange(graine ^ Melange((uint)i * 0x9e3779b1u ^ (uint)j * 0x85ebca77u ^ canal * 0xc2b2ae3du));
	}
}
