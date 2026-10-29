// SYMBIOSE — PlantRenderer.KitCodes.cs (partial, sprint CASSÉ À L'ÉCRAN ③)
// Les CODES INDEXÉS du kit (canal G de l'atlas, PlantRenderer.Kit.cs) : pour
// chaque pixel d'une touffe ou d'un fleuron, le ton dans la rampe et l'orientation
// de la face (PaletteIndexee.cs pour l'encodage). C'est la moitié « géométrie » de
// la lumière ; l'autre moitié (où est le soleil) est dans le shader de lecture.
//
// 📖 Pédagogie : on précalcule UNE fois, à la génération du kit, ce qui ne dépend
// que de la forme (la normale de chaque pixel) ; ce qui change pendant la partie
// (le soleil) reste un paramètre du GPU. Séparer l'invariant du variable est le
// même réflexe qu'en embarqué : tables en flash, registres en RAM.
//
// Déterministe (grain au hash, zéro Random), purement visuel : golden non concerné.

using Godot;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Codes d'un fleuron : chaque pixel orienté depuis le centre (le bouton 2×2
		// a ses 4 coins vers les diagonales → le côté soleil s'éclaire) ; le cœur et
		// le point isolé sont « plats ». Ton de base partout.
		private static byte[] CodesFleuron(byte[] niv, int t)
		{
			var codes = new byte[t * t];
			for (int i = 0; i < t * t; i++)
			{
				if (niv[i] == KitVide) continue;
				var n = new Vector2(i % t + 0.5f - t * 0.5f, i / t + 0.5f - t * 0.5f);
				int o = niv[i] == KitCoeur || n.LengthSquared() < 0.01f ? PaletteIndexee.OrientPlat : Orientation(n);
				codes[i] = PaletteIndexee.OctetB(PaletteIndexee.TonBase, o);
			}
			return codes;
		}

		/// <summary>Normale écran → orientation quantifiée 0..7 (k × 45°, 0 = droite,
		/// 2 = bas, 6 = haut), même convention que le shader de lecture.</summary>
		private static int Orientation(Vector2 n) =>
			Mathf.PosMod(Mathf.RoundToInt(Mathf.Atan2(n.Y, n.X) / (Mathf.Pi * 0.25f)), 8);

		// Codes indexés d'une touffe (③). Corps : ton de base + orientation de face,
		// un grain au hash descend ~1 pixel sur 8 d'un ton (texture sans bruit vivant) ;
		// séparation (bord de la feuille de derrière) = ombre « plate » ; trou
		// intérieur (≥ 3 voisins posés) = creux plat. Pas d'anneau de contour.
		private const float GrainOmbre = 0.12f;
		private const float FacePlate = 0.3f;   // normale plus courte = face « plate »
		private static byte[] CodesTouffe(int[] proprio, Vector2[] face, int n, int v)
		{
			var codes = new byte[n * n];
			for (int i = 0; i < n * n; i++)
			{
				int x = i % n, y = i / n;
				if (proprio[i] < 0)
				{
					if (n >= KitSeparationMin && VoisinsPleins(proprio, n, i) >= 3)
						codes[i] = PaletteIndexee.OctetB(0, PaletteIndexee.OrientPlat);
					continue;
				}
				if (n >= KitSeparationMin && VoisinDevant(proprio, n, i))
				{
					codes[i] = PaletteIndexee.OctetB(1, PaletteIndexee.OrientPlat);
					continue;
				}
				int ton = Hash01(70, x + n * 16, y + v * 16) < GrainOmbre ? 1 : PaletteIndexee.TonBase;
				int o = face[i].Length() < FacePlate ? PaletteIndexee.OrientPlat : Orientation(face[i]);
				codes[i] = PaletteIndexee.OctetB(ton, o);
			}
			return codes;
		}

		// Normale de face d'un pixel (③) : la touffe vue comme un DÔME (position dans
		// la touffe, du centre vers le bord) + le pli de la feuille (chaque moitié du
		// limbe regarde de son côté). Repère écran, sans « sud » codé en dur : c'est
		// le shader qui sait où est le soleil.
		private static Vector2 Face(LeafShape forme, KitFeuille f, Vector2 p, Vector2 c, float r)
		{
			Vector2 dome = (p - c) / Mathf.Max(r, 0.5f);
			if (dome.Length() > 1f) dome = dome.Normalized();
			if (forme == LeafShape.Aciculaire) return dome;
			var cr = new Vector2(-f.A.Y, f.A.X);
			float cote = Mathf.Clamp((p - f.B).Dot(cr) / Mathf.Max(0.35f * f.L, 0.5f), -1f, 1f);
			return dome * 0.8f + cr * (cote * 0.45f);
		}

		private static int VoisinsPleins(int[] proprio, int n, int i)
		{
			int x = i % n, y = i / n, k = 0;
			if (x > 0 && proprio[i - 1] >= 0) k++;
			if (x < n - 1 && proprio[i + 1] >= 0) k++;
			if (y > 0 && proprio[i - n] >= 0) k++;
			if (y < n - 1 && proprio[i + n] >= 0) k++;
			return k;
		}
	}
}
