// SYMBIOSE — DecorLayer.KitCodes.cs (CASSÉ À L'ÉCRAN ⑥ — les pièces du décor en DIALECTE 2, indexées)
// Partial de DecorLayer : peint chaque pièce du kit (DecorLayer.Kit.cs) non plus en
// niveaux de COULEUR mais en CODES de la palette indexée (octet B, cf.
// visuals/PaletteIndexee.cs) : un TON (0 creux · 1 ombre · 2 base · 3 clair · 4 éclat)
// et une ORIENTATION de face (0 droite · 2 bas · 4 gauche · 6 haut, 8 = plat). Le
// shader du décor (visuals/decor_indexe.gdshader) choisit la couleur selon le soleil
// RÉEL → l'éclat se pose côté soleil, comme sur les plantes (③).
//
// 📖 Pédagogie — le DIALECTE 2 du brief (Chrono Trigger, combat en forêt) :
//  • MASSES (sous-bois, ronciers, bouquets de houppier) : PAS de contour ; la masse est
//    faite d'un GRAIN EN CHEVRONS 2×3 px (cellules décalées d'1 px par colonne, sens
//    inversé toutes les 3 colonnes) ; rang haut de chaque grain clair, rang bas dans
//    l'ombre ; le BORD HAUT de la masse est le plus clair ; quelques grains creusés au
//    hash (les « tuiles retirées »).
//  • TOUFFE d'herbe : 3 à 5 grains elliptiques obliques ≈ 2×3 px (éclat en haut,
//    ombre dessous), serrés en chevrons ; aucun brin, aucun contour.
//  • ROCHERS (galets, blocs) : 3 tons + éclat par l'orientation (le soleil choisit),
//    une ombre SOUS le bord bas, jamais de contour noir.
// Zéro Random (philo #3) : formes tirées de H01 (hash fixe), comme le kit d'avant.

using Godot;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		private const int ODroite = 0, OBas = 2, OGauche = 4, OHaut = 6;

		private static byte C(int ton, int orient) => PaletteIndexee.OctetB(ton, orient);

		// Normale (repère écran, y vers le bas) → orientation quantifiée à 45°.
		private static int OrientDe(Vector2 n) =>
			n.LengthSquared() < 0.04f ? PaletteIndexee.OrientPlat
			: (Mathf.RoundToInt(Mathf.Atan2(n.Y, n.X) / (Mathf.Pi / 4f)) + 8) % 8;

		/// <summary>Codes d'une pièce (0 = vide), même taille que PeindrePiece.</summary>
		private static byte[] CoderPiece(Piece f, int w, int hh, int v)
		{
			var c = new byte[w * hh];
			switch (f)
			{
				case Piece.Fleur:
					// Étoile 3×3 : pétales base, pétale bas à l'ombre, cœur = éclat.
					// ⑥ : orientation « fleur » (plate), que la saison sait reconnaître.
					byte p = C(2, OrientFleur);
					return new byte[] { 0, p, 0, p, C(4, OrientFleur), p, 0, C(1, OrientFleur), 0 };
				case Piece.Herbe: CoderTouffe(c, w, hh, v); break;
				case Piece.HerbeHaute:
				case Piece.Roseau: CoderBrins(c, f, w, hh, v); break;
				case Piece.Galet: CoderGalet(c, w, hh); break;
				case Piece.Bloc: CoderBloc(c, w, hh, v); break;
				default: CoderMasse(c, f, w, hh, v); break;
			}
			return c;
		}

		// TOUFFE : grains 2×3 obliques (haut à droite), en couches : la couche du bas
		// (devant) a le plus de grains, chaque couche au-dessus en a un de moins et se
		// décale d'1 px (chevron). Un grain : haut clair face haute, milieu base de
		// côté (gauche/droite alternés), bas dans l'ombre.
		private static void CoderTouffe(byte[] c, int w, int hh, int v)
		{
			int couches = Mathf.Max(1, hh / 3);
			for (int k = couches - 1; k >= 0; k--)          // du fond (haut) vers l'avant
			{
				int n = Mathf.Max(1, w / 2 - k);
				int y0 = hh - 3 - k * 2;                      // ligne du haut du grain
				int x0 = (w - n * 2) / 2 + (k & 1);
				for (int g = 0; g < n; g++)
				{
					if (k > 0 && H01(Piece.Herbe, w, v, g + 7 * k) < 0.2f) continue;   // grain retiré
					int x = x0 + g * 2, sens = ((g + v + k) & 1) == 0 ? 1 : -1;
					Poser(c, w, hh, x + (sens > 0 ? 1 : 0), y0, C(3, OHaut));
					Poser(c, w, hh, x, y0 + 1, C(2, sens > 0 ? OGauche : ODroite));
					Poser(c, w, hh, x + 1, y0 + 1, C(2, sens > 0 ? OGauche : ODroite));
					Poser(c, w, hh, x + (sens > 0 ? 0 : 1), y0 + 2, C(1, OBas));
				}
			}
		}

		// BRINS (herbe haute de friche, roseaux) : la forme du kit d'avant (PeindreBrins,
		// PeindreRoseau), recodée SANS contour : brins éclairés d'avant → face gauche,
		// brins d'ombre → face droite, massette du roseau = creux (brun très sombre).
		private static void CoderBrins(byte[] c, Piece f, int w, int hh, int v)
		{
			var niv = new byte[w * hh];
			if (f == Piece.Roseau) PeindreRoseau(niv, w, hh, v);
			else PeindreBrins(niv, w, hh, v, true);
			for (int i = 0; i < niv.Length; i++)
				c[i] = niv[i] switch
				{
					0 => (byte)0,
					1 => C(0, PaletteIndexee.OrientPlat),
					2 => C(2, ODroite),
					4 => C(2, OGauche),
					_ => C(2, OHaut),
				};
		}

		// GALET : ellipse ; chaque pixel prend l'orientation de sa normale (le soleil
		// fait les 3 tons + l'éclat) ; dès 3 px de haut, le bord BAS = ombre plate.
		private static void CoderGalet(byte[] c, int w, int hh)
		{
			for (int py = 0; py < hh; py++)
				for (int px = 0; px < w; px++)
				{
					var n = new Vector2((px + 0.5f) / w * 2f - 1f, (py + 0.5f) / hh * 2f - 1f);
					if (n.LengthSquared() > 1.15f) continue;
					bool bas = hh >= 3 && (py == hh - 1 || !Dedans(px, py + 1, w, hh, 1.15f));
					c[py * w + px] = bas ? C(1, PaletteIndexee.OrientPlat) : C(2, OrientDe(n));
				}
		}

		private static bool Dedans(int px, int py, int w, int hh, float r2)
		{
			var n = new Vector2((px + 0.5f) / w * 2f - 1f, (py + 0.5f) / hh * 2f - 1f);
			return py < hh && n.LengthSquared() <= r2;
		}

		// BLOC d'éboulis : dessus = face haute, flanc gauche / droit = faces latérales
		// (le soleil choisit lequel s'éclaire), coins abattus au hash, rang du bas =
		// ombre sous le bloc.
		private static void CoderBloc(byte[] c, int w, int hh, int v)
		{
			int dessus = Mathf.Max(1, Mathf.RoundToInt(hh * (0.30f + 0.15f * H01(Piece.Bloc, w, v, 1))));
			int arete = Mathf.RoundToInt(w * (0.45f + 0.20f * H01(Piece.Bloc, w, v, 2)));
			int pan = 1 + (int)(H01(Piece.Bloc, w, v, 3) * 2f);
			for (int py = 0; py < hh; py++)
				for (int px = 0; px < w; px++)
				{
					int dx = Mathf.Min(px, w - 1 - px), dy = Mathf.Min(py, hh - 1 - py);
					if (dx + dy < pan) continue;
					c[py * w + px] = py == hh - 1 ? C(1, PaletteIndexee.OrientPlat)
								   : py < dessus ? C(2, OHaut) : px < arete ? C(2, OGauche) : C(2, ODroite);
				}
		}

		// MASSES (feuillu, roncier, sous-bois, conifère) : silhouette du kit d'avant
		// (union de disques, étages pour le conifère) remplie du GRAIN EN CHEVRONS.
		private static void CoderMasse(byte[] c, Piece f, int w, int hh, int v)
		{
			var niv = new byte[w * hh];
			PeindreMasse(niv, f, w, hh, v);   // silhouette seule (niveaux ignorés)
			var dc = new Vector2(w * 0.5f, hh * 0.55f);
			for (int py = 0; py < hh; py++)
				for (int px = 0; px < w; px++)
				{
					if (niv[py * w + px] == 0) continue;
					var n = new Vector2((px + 0.5f - dc.X) / (w * 0.5f), (py + 0.5f - dc.Y) / (hh * 0.5f));
					int o = OrientDe(n);
					if (py == 0 || niv[(py - 1) * w + px] == 0) { c[py * w + px] = C(3, OHaut); continue; }   // bord haut
					int cx = px >> 1, sens = ((cx / 3) & 1) == 0 ? 1 : -1;
					int y = py + sens * cx + 30, ly = y % 3;
					bool creux = H01(f, w, v, 200 + cx * 31 + y / 3) < (f == Piece.Feuillu || f == Piece.Conifere ? 0.06f : 0.12f);
					c[py * w + px] = ly == 2 ? (creux ? C(0, PaletteIndexee.OrientPlat) : C(1, o))
								   : ly == 0 ? C(3, o) : C(2, o);
				}
		}

		private static void Poser(byte[] c, int w, int hh, int x, int y, byte code)
		{
			if (x >= 0 && x < w && y >= 0 && y < hh) c[y * w + x] = code;
		}
	}
}
