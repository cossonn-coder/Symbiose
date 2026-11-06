// SYMBIOSE — PlantRenderer.PiecesFleur.cs (partial, sprint VERGER VIVANT ④)
// Les FLEURS D'ARBRE DE PRÈS (×8, ×16, ×32) : une fleur = une pièce de pixel-art de l'atlas des
// gerbes, à sa taille réelle (4 cm de diamètre, relevée d'un tiers comme les limbes), posée en
// quatre couches au plus : pétales, liseré, cœur et étamines, ou bouton.
//
// 📖 Pédagogie — pourquoi une pièce et pas des disques. Une fleur en disques de triangles coûtait
// ~11 disques, soit une centaine de triangles ; 1 500 fleurs doublaient les primitives de l'image
// et divisaient les FPS de la VM par deux [`verger_mur` ×8, n=1 relevé par côté]. Une pièce, c'est
// un rectangle texturé : deux triangles par couche, et la forme est dessinée une seule fois, au
// chargement, comme un glyphe de police qu'on recopie.
//
// Mêmes codes que le kit (canal G) : la teinte vient du `modulate` (pétale, liseré, cœur, bouton),
// la lumière du shader. Lumière côté sud = bas de la pièce. Déterministe, golden non concerné.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		internal enum CouchePiece { Petales, Lisere, Coeur, Bouton }

		// Côté de la pièce à ×8, ×16, ×32 : 2 × FleurArbreRayonCm × PxPerCmX (0,39) × zoom, impair.
		private static readonly int[] CotesPieceFleur = { 13, 25, 49 };
		private const int VariantesPiece = 2;
		private static readonly Dictionary<(int, int, CouchePiece), Rect2I> _piecesFleur = new();

		private static int PalierPiece(float zoom) => zoom < 16f ? 0 : zoom < 32f ? 1 : 2;

		private static int RangerPiecesFleur(int y)
		{
			for (int g = 0; g < CotesPieceFleur.Length; g++)
			{
				int n = CotesPieceFleur[g], x = 0;
				for (int v = 0; v < VariantesPiece; v++)
					foreach (CouchePiece couche in System.Enum.GetValues(typeof(CouchePiece)))
					{
						if (x + n > GerbeAtlasLargeur) { x = 0; y += n + 1; }
						_piecesFleur[(g, v, couche)] = new Rect2I(x, y, n, n);
						x += n + 1;
					}
				y += n + 1;
			}
			return y;
		}

		private static void PeindrePiecesFleur(byte[] rg)
		{
			for (int g = 0; g < CotesPieceFleur.Length; g++)
				for (int v = 0; v < VariantesPiece; v++)
					PeindrePiece(rg, g, v, CotesPieceFleur[g]);
		}

		// Cinq pétales ronds autour d'un cœur ; dès ×16, un anneau d'étamines. Variante 1 : tournée d'un
		// demi-pétale. Le liseré = pixels de pétale qui touchent le vide ou un autre pétale.
		private static void PeindrePiece(byte[] rg, int g, int v, int t)
		{
			var proprio = new int[t * t];
			var niv = new byte[t * t];
			float c = t * 0.5f, rp = t * 0.23f, dp = t * 0.26f, a0 = -Mathf.Pi * 0.5f + v * Mathf.Pi / 5f;
			for (int i = 0; i < t * t; i++)
			{
				var q = new Vector2(i % t + 0.5f - c, i / t + 0.5f - c);
				proprio[i] = -1;
				float dc = q.Length();
				bool etamine = g > 0 && Mathf.Abs(dc - t * 0.2f) < 0.6f && Mathf.PosMod(Mathf.Atan2(q.Y, q.X) * 8f / Mathf.Tau, 1f) < 0.4f;
				if (dc < t * 0.12f || etamine) { niv[i] = KitCoeur; proprio[i] = 5; continue; }
				for (int k = 0; k < 5; k++)
				{
					float a = a0 + Mathf.Tau * k / 5f;
					if (q.DistanceTo(new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * dp) > rp) continue;
					proprio[i] = k;
					niv[i] = q.Y > t * 0.12f ? KitLumiere : q.Y < -t * 0.12f ? KitOmbre : KitBase;
					break;
				}
			}
			// Pétales à plat, en codes (shader) comme en niveaux (dessin direct, littéral) : un cerisier reste
			// blanc pur, côté ombre compris. Seul le bas s'éclaire d'un ton, comme l'éclat du brief SNES.
			byte plat = PaletteIndexee.OctetB(PaletteIndexee.TonBase, PaletteIndexee.OrientPlat);
			byte eclat = PaletteIndexee.OctetB(3, PaletteIndexee.OrientPlat);
			byte coeur = PaletteIndexee.OctetB(PaletteIndexee.TonBase, PaletteIndexee.OrientPlat);
			byte lisere = PaletteIndexee.OctetB(0, PaletteIndexee.OrientPlat);
			for (int i = 0; i < t * t; i++)
			{
				int x = i % t, y = i / t;
				if (niv[i] == KitVide) continue;
				Poser(rg, _piecesFleur[(g, v, CouchePiece.Petales)], x, y, niv[i] == KitLumiere ? KitLumiere : KitBase, niv[i] == KitLumiere ? eclat : plat);
				if (niv[i] == KitCoeur) Poser(rg, _piecesFleur[(g, v, CouchePiece.Coeur)], x, y, KitBase, coeur);
				else if (Bordure(proprio, t, x, y)) Poser(rg, _piecesFleur[(g, v, CouchePiece.Lisere)], x, y, KitContour, lisere);
			}
			// Le bouton : une perle au tiers de la fleur, éclairée par-dessous comme tout le kit.
			float rb = t * 0.2f;
			for (int i = 0; i < t * t; i++)
			{
				var q = new Vector2(i % t + 0.5f - c, i / t + 0.5f - c);
				if (q.Length() > rb) continue;
				byte n = q.Length() > rb - 1f ? KitContour : q.Y > rb * 0.3f ? KitLumiere : KitBase;
				byte code = n == KitContour ? lisere : PaletteIndexee.OctetB(n == KitLumiere ? 3 : PaletteIndexee.TonBase, Orientation(q));
				Poser(rg, _piecesFleur[(g, v, CouchePiece.Bouton)], i % t, i / t, n, code);
			}
		}

		private static bool Bordure(int[] proprio, int t, int x, int y)
		{
			int p = proprio[y * t + x];
			for (int d = 0; d < 4; d++)
			{
				int nx = x + (d == 0 ? 1 : d == 1 ? -1 : 0), ny = y + (d == 2 ? 1 : d == 3 ? -1 : 0);
				if (nx < 0 || ny < 0 || nx >= t || ny >= t) return true;
				int o = proprio[ny * t + nx];
				if (o < 0 || (o != p && o != 5 && o < p)) return true;   // le vide, ou le pétale d'avant
			}
			return false;
		}

		/// <summary>Une pièce de fleur centrée en `centre` (px canvas locaux), indexée ou littérale. En littéral,
		/// seuls les niveaux `n0..n1` de la couche existent : un masque par niveau présent, pas quatre.</summary>
		private void PoserPieceFleur(Rect2I r, Vector2 centre, float z, int palette, Color[] rampe, int n0, int n1)
		{
			Vector2 coin = ((centre * z) - (Vector2)r.Size * 0.5f).Round() / z;
			var dst = new Rect2(coin, (Vector2)r.Size / z);
			if (palette >= 0)
			{
				DrawTextureRectRegion(_gerbesCodes, dst, (Rect2)r, PaletteIndexee.ModulatePiece(palette));
				return;
			}
			AssurerMasquesGerbes();
			for (int n = n0; n <= n1; n++)
				DrawTextureRectRegion(_gerbesMasques, dst, new Rect2(r.Position + new Vector2I((n - KitContour) * GerbeAtlasLargeur, 0), r.Size), rampe[n]);
		}

		/// <summary>×8 et plus : chaque fleur des bouquets (FleursHouppier) en pièces ; les chatons restent tracés.</summary>
		private void DrawPiecesFleurs(Vector3 c, in OrganPalette pal, in FicheFleurArbre fiche)
		{
			AssurerGerbes();
			float z = WorldView.CurrentZoom;
			int g = PalierPiece(z);
			bool idx = Indexe;
			int pP = idx ? PaletteIndexee.Palette(pal.Flower) : -1, pL = idx ? PaletteIndexee.Palette(fiche.Bord) : -1;
			int pC = idx ? PaletteIndexee.Palette(FlowerHeart) : -1, pB = idx ? PaletteIndexee.Palette(fiche.Bouton) : -1;
			Color[] rP = idx ? null : RampeLitterale(pal.Flower, false), rL = idx ? null : RampeLitterale(fiche.Bord, false);
			Color[] rC = idx ? null : RampeLitterale(FlowerHeart, false), rB = idx ? null : RampeLitterale(fiche.Bouton, false);
			foreach (var f in FleursHouppier(pal))
			{
				Vector2 pos = Iso(f.P.X - c.X, f.P.Y - c.Y, f.P.Z);
				int v = f.K % VariantesPiece;
				if (f.Bouton) { PoserPieceFleur(_piecesFleur[(g, v, CouchePiece.Bouton)], pos, z, pB, rB, KitContour, KitLumiere); continue; }
				PoserPieceFleur(_piecesFleur[(g, v, CouchePiece.Petales)], pos, z, pP, rP, KitBase, KitLumiere);
				PoserPieceFleur(_piecesFleur[(g, v, CouchePiece.Lisere)], pos, z, pL, rL, KitContour, KitContour);
				PoserPieceFleur(_piecesFleur[(g, v, CouchePiece.Coeur)], pos, z, pC, rC, KitBase, KitBase);
			}
		}
	}
}
