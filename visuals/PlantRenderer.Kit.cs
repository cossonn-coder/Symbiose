// SYMBIOSE — PlantRenderer.Kit.cs (partial de PlantRenderer, PLANTE ASSEMBLÉE ④)
// ATLAS DU KIT : les petites pièces de pixel-art dont ⑤ assemblera les plantes
// aux paliers bas (×0,5 · ×1 · ×2), à la place des ellipses-blobs.
//  • TOUFFES : pour chaque `LeafShape` (Leaf.cs), 4 tailles internes (3, 5, 7,
//    9 px) × 3 variantes choisies au HASH (zéro Random, philo #3). Une touffe =
//    quelques feuilles de la forme rayonnant d'un point (le bout d'un rameau).
//  • FLEURONS : point 1×1, bouton 2×2, étoile 3×3.
// Les pièces sont peintes en NIVEAUX (indices de rampe), pas en couleur : ⑤ les
// teinte au moment de la cuisson avec la couleur d'espèce/saison/santé (même
// langage que les paliers actuels — on change la FORME, pas l'information).
//
// Niveaux : 0 vide · 1 contour · 2 ombre · 3 base · 4 lumière · 5 cœur (fleuron).
// Lumière côté SUD = vers le BAS de la pièce (sud de l'orientation 0 projeté :
// le kit est cuit une fois, il ne suit pas la rotation D35 — cf. 00_etat ④).
//
// CASSÉ À L'ÉCRAN ③ — 2ᵉ canal (G) : le CODE de palette indexée de chaque pixel
// (PaletteIndexee.cs : 128 | ton << 4 | orientation de face). Le canal R (niveaux
// ci-dessus, éclairés vers le bas) ne sert plus qu'à la planche du kit et au rendu
// littéral (F11 OFF, dessin direct) ; les plantes cuites lisent G : la lumière
// vient du shader, côté soleil réel. Masses SANS contour en G (anneau extérieur
// vide) ; trous intérieurs = ton « creux » teinté, jamais le fond. Calcul des
// codes : PlantRenderer.KitCodes.cs.
//
// 📖 Pédagogie Godot/C# : une `Image` est un tableau de pixels en MÉMOIRE CPU
// (pas encore une texture GPU). On y écrit les niveaux en format R8 (1 octet par
// pixel, comme un buffer d'indices de palette en embarqué) ; `TeindreKit` en fait
// une image RGBA8 en remplaçant chaque indice par sa couleur de rampe. Membres
// STATIQUES : le kit est partagé par toutes les plantes, généré à la 1ʳᵉ demande.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		internal const byte KitVide = 0, KitContour = 1, KitOmbre = 2, KitBase = 3,
			KitLumiere = 4, KitCoeur = 5;
		internal static readonly int[] KitTailles = { 3, 5, 7, 9 };
		internal const int KitVariantes = 3;
		internal enum Fleuron { Point, Bouton, Etoile }

		// Seuils de la rampe 3 valeurs (score d'éclairement s ∈ ~[-1,1]).
		private const float KitSeuilLumiere = 0.28f, KitSeuilOmbre = -0.28f;
		// Contour sombre 1 px seulement s'il reste lisible (touffes ≥ 7 px).
		private const int KitContourMin = 7;
		// Ombre portée d'une feuille de devant sur celle de derrière (≥ 5 px).
		private const int KitSeparationMin = 5;
		private const float KitContourLum = -0.62f;   // contour : ombre poussée

		private const int KitPas = 10;   // hauteur d'une rangée (9 px + 1 de jour)
		private static Image _kitNiveaux;
		private static readonly Dictionary<(LeafShape, int, int), Rect2I> _kitTouffes = new();
		private static readonly Rect2I[] _kitFleurons = new Rect2I[3];

		/// <summary>Hauteur d'une rangée de l'atlas (planche du kit).</summary>
		internal const int KitPasRangee = KitPas;
		internal static string[] KitFormes => System.Enum.GetNames(typeof(LeafShape));

		/// <summary>Atlas des niveaux (R) et des codes indexés (G), généré une seule fois.</summary>
		internal static Image KitNiveaux { get { AssurerKit(); return _kitNiveaux; } }

		private static Rect2I KitTouffe(LeafShape s, int taille, int variante)
		{
			AssurerKit();
			return _kitTouffes[(s, taille, variante)];
		}

		internal static Rect2I KitFleuron(Fleuron f) { AssurerKit(); return _kitFleurons[(int)f]; }

		/// <summary>Rampe de teinte d'une pièce : index = niveau. Même hue-shift que
		/// le volume des feuilles (OrganShade/OrganLit) → continuité avec ×4.</summary>
		internal static Color[] RampeKit(Color baseCol) => new[]
		{
			Colors.Transparent,
			HueShiftPur(baseCol, KitContourLum, 1f),
			HueShiftPur(baseCol, -OrganShade, 1f),
			baseCol,
			HueShiftPur(baseCol, OrganLit, 1f),
			FlowerHeart,
		};

		/// <summary>Région de l'atlas teintée par une rampe (image RGBA8).</summary>
		internal static Image TeindreKit(Rect2I r, Color[] rampe, Image atlas = null)
		{
			var src = atlas ?? KitNiveaux;
			var img = Image.CreateEmpty(r.Size.X, r.Size.Y, false, Image.Format.Rgba8);
			for (int y = 0; y < r.Size.Y; y++)
				for (int x = 0; x < r.Size.X; x++)
				{
					int n = (int)Mathf.Round(src.GetPixel(r.Position.X + x, r.Position.Y + y).R * 255f);
					img.SetPixel(x, y, rampe[Mathf.Clamp(n, 0, rampe.Length - 1)]);
				}
			return img;
		}

		// --- Construction de l'atlas -----------------------------------------
		// Rangée = une forme ; colonnes = tailles croissantes, variantes côte à côte
		// (1 px de jour entre pièces). Dernière rangée : les fleurons.
		private static void AssurerKit()
		{
			if (_kitNiveaux != null) return;
			var formes = (LeafShape[])System.Enum.GetValues(typeof(LeafShape));
			int largeur = 0;
			foreach (int t in KitTailles) largeur += (t + 1) * KitVariantes;
			var img = Image.CreateEmpty(largeur, KitPas * (formes.Length + 1), false, Image.Format.Rg8);
			for (int r = 0; r < formes.Length; r++)
			{
				int x = 0;
				foreach (int t in KitTailles)
					for (int v = 0; v < KitVariantes; v++, x += t + 1)
					{
						var rect = new Rect2I(x, r * KitPas, t, t);
						var (niv, codes) = PeindreTouffe(formes[r], t, v);
						Poser(img, rect.Position, niv, codes, t);
						_kitTouffes[(formes[r], t, v)] = rect;
					}
			}
			int yF = formes.Length * KitPas, xF = 0;
			byte[][] fleurons =
			{
				new byte[] { KitBase },
				new byte[] { KitBase, KitBase, KitLumiere, KitBase },
				new byte[] { 0, KitBase, 0, KitBase, KitCoeur, KitBase, 0, KitLumiere, 0 },
			};
			for (int f = 0; f < fleurons.Length; f++)
			{
				int t = f + 1;
				_kitFleurons[f] = new Rect2I(xF, yF, t, t);
				Poser(img, new Vector2I(xF, yF), fleurons[f], CodesFleuron(fleurons[f], t), t);
				xF += t + 1;
			}
			_kitNiveaux = img;
		}

		private static void Poser(Image img, Vector2I o, byte[] niv, byte[] codes, int t)
		{
			for (int y = 0; y < t; y++)
				for (int x = 0; x < t; x++)
					img.SetPixel(o.X + x, o.Y + y, new Color(niv[y * t + x] / 255f, codes[y * t + x] / 255f, 0f));
		}

		// --- Une touffe ------------------------------------------------------
		// Une feuille du kit : base B, axe a, longueur L, plus un centre propre pour
		// les formes « rondes » (lobée). Ordre de peinture = nord d'abord, sud devant.
		// `Rond` = rayon des formes rondes (lobée), centrées en B + A·L.
		private readonly record struct KitFeuille(Vector2 B, Vector2 A, float L, float Rond, float Epais);

		private static (byte[] niv, byte[] codes) PeindreTouffe(LeafShape forme, int n, int variante)
		{
			int marge = n >= KitContourMin ? 1 : 0;
			float r = n * 0.5f - marge;
			var c = new Vector2(n * 0.5f, n * 0.5f);
			var feuilles = DisposerFeuilles(forme, n, variante, c, r);
			feuilles.Sort((p, q) => (p.B + p.A * p.L).Y.CompareTo((q.B + q.A * q.L).Y));

			var proprio = new int[n * n];
			var score = new float[n * n];
			var face = new Vector2[n * n];
			for (int y = 0; y < n; y++)
				for (int x = 0; x < n; x++)
				{
					proprio[y * n + x] = -1;
					for (int k = 0; k < feuilles.Count; k++)
					{
						if (Couverture(forme, feuilles[k], x, y) < 3) continue;
						var p = new Vector2(x + 0.5f, y + 0.5f);
						proprio[y * n + x] = k;   // la dernière (la plus au sud) gagne
						score[y * n + x] = Eclairement(forme, feuilles[k], p, c, r, n, variante);
						face[y * n + x] = Face(forme, feuilles[k], p, c, r);
					}
				}

			var niv = new byte[n * n];
			for (int i = 0; i < n * n; i++)
			{
				if (proprio[i] < 0) continue;
				float s = score[i];
				niv[i] = s > KitSeuilLumiere ? KitLumiere : s < KitSeuilOmbre ? KitOmbre : KitBase;
				// Séparation : la feuille de devant ombre le bord de celle de derrière.
				if (n >= KitSeparationMin && VoisinDevant(proprio, n, i)) niv[i] = KitOmbre;
			}
			if (n >= KitContourMin)
				for (int i = 0; i < n * n; i++)
					if (proprio[i] < 0 && VoisinPlein(proprio, n, i)) niv[i] = KitContour;
			return (niv, CodesTouffe(proprio, face, n, variante));
		}

		// Placement des feuilles par forme (nombre, éventail, longueur) + jitter au
		// hash (canaux 61-67 : propres au kit, distincts de ceux des feuilles ×4).
		private static List<KitFeuille> DisposerFeuilles(LeafShape forme, int n, int v, Vector2 c, float r)
		{
			int graine = (int)forme * 16 + n;
			float h(int canal, int k) => Hash01(canal, graine, v * 16 + k);
			var liste = new List<KitFeuille>();
			// Petites touffes : limbes épaissis, sinon la feuille fond sous le pixel.
			float epais = n <= 3 ? 1.7f : n <= 5 ? 1.35f : 1f;
			int nb; float longueur, rond = 0f, depart = h(61, 0) * Mathf.Tau, eventail = Mathf.Tau;
			Vector2 origine = c;
			switch (forme)
			{
				case LeafShape.Lanceolee:   // rubans dressés, partant du bas
					nb = n <= 3 ? 2 : 3; longueur = r * 1.85f; eventail = Mathf.Pi * (n <= 3 ? 0.4f : 0.6f);
					depart = -Mathf.Pi * 0.5f - eventail * 0.5f + (h(61, 0) - 0.5f) * 0.4f;
					origine = c + new Vector2(0f, r * 0.85f);
					break;
				case LeafShape.Lobee:       // 1-2 grandes feuilles palmées
					nb = n <= 5 ? 1 : 2; longueur = r * (nb == 1 ? 0.1f : 0.42f);
					rond = r * (nb == 1 ? 1.05f : 0.68f);
					break;
				case LeafShape.Aciculaire:  // aiguilles en faisceau
					nb = n <= 3 ? 2 : n <= 5 ? 4 : 6; longueur = r * 1.0f;
					break;
				case LeafShape.Composee:   // 3 rachis : découpé mais pas clairsemé
					nb = 3; longueur = r * 1.05f;
					break;
				case LeafShape.Cordee:
					nb = n <= 3 ? 2 : 3; longueur = r * 1.0f;
					break;
				default:                    // Elliptique
					nb = n <= 3 ? 2 : 4; longueur = r * 0.95f;
					break;
			}
			for (int k = 0; k < nb; k++)
			{
				float pas = eventail >= Mathf.Tau - 0.01f ? eventail / nb : eventail / Mathf.Max(1, nb - 1);
				float ang = depart + pas * k + (h(63, k) - 0.5f) * pas * 0.35f;
				var a = new Vector2(Mathf.Cos(ang), Mathf.Sin(ang));
				float l = longueur * (0.85f + 0.2f * h(67, k));
				liste.Add(new KitFeuille(origine + a * (forme == LeafShape.Lanceolee ? 0f : r * 0.12f), a, l, rond, epais));
			}
			return liste;
		}

		// Couverture d'un pixel par une feuille, sur 3×3 sous-échantillons (0-9).
		// ≥ 3/9 = posé : les traits fins (aiguilles, rachis) survivent.
		private static int Couverture(LeafShape forme, KitFeuille f, int x, int y)
		{
			int nbIn = 0;
			for (int sy = 0; sy < 3; sy++)
				for (int sx = 0; sx < 3; sx++)
					if (Dedans(forme, f, new Vector2(x + (sx + 0.5f) / 3f, y + (sy + 0.5f) / 3f)))
						nbIn++;
			return nbIn;
		}

		// Silhouette analytique d'une feuille dans son repère (u le long, v en travers).
		private static bool Dedans(LeafShape forme, KitFeuille f, Vector2 p)
		{
			var cr = new Vector2(-f.A.Y, f.A.X);
			Vector2 d = p - f.B;
			float along = d.Dot(f.A), v = d.Dot(cr), u = along / f.L;
			switch (forme)
			{
				case LeafShape.Lobee:
				{
					// Étoile palmée de 5 lobes autour d'un centre décalé de la base.
					Vector2 q = p - (f.B + f.A * f.L);
					float rl = f.Rond;
					float phi = Mathf.Atan2(q.Dot(cr), q.Dot(f.A));
					return q.Length() < rl * (0.62f + 0.38f * Mathf.Cos(5f * phi));
				}
				case LeafShape.Aciculaire:
					return u >= 0f && u <= 1f && Mathf.Abs(v) < 0.3f;
				case LeafShape.Composee:
				{
					if (u < 0f || u > 1f) return false;
					if (Mathf.Abs(v) < 0.22f) return true;               // rachis
					float rl = Mathf.Max(0.55f, 0.17f * f.L);
					int k = Mathf.Max(2, Mathf.RoundToInt(f.L / 1.5f));
					for (int m = 0; m < k; m++)                         // folioles alternes
					{
						float side = (m & 1) == 0 ? 1f : -1f;
						var ctr = new Vector2((m + 0.7f) / (k + 0.2f) * f.L, side * (rl + 0.25f));
						if (new Vector2(along, v).DistanceTo(ctr) < rl) return true;
					}
					return false;
				}
				default:
				{
					if (u < 0f || u > 1f) return false;
					float hw = forme switch
					{
						LeafShape.Lanceolee => 0.09f * f.L * Mathf.Sqrt(Mathf.Max(0f, 1f - u)),
						LeafShape.Cordee => 0.46f * f.L * Mathf.Sin(Mathf.Pi * Mathf.Pow(u, 0.65f)),
						_ => 0.34f * f.L * Mathf.Sqrt(Mathf.Max(0f, 1f - (2f * u - 1f) * (2f * u - 1f))),
					};
					// Cordée : échancrure basale (le « cœur »), visible dès 7 px.
					if (forme == LeafShape.Cordee && u < 0.2f && Mathf.Abs(v) < 0.08f * f.L + 0.15f)
						return false;
					return Mathf.Abs(v) < Mathf.Max(hw * f.Epais, 0.3f);
				}
			}
		}

		// Score d'éclairement : position nord→sud dans la touffe (le sud est éclairé)
		// + face de la feuille tournée vers le sud + grain au hash.
		private static float Eclairement(LeafShape forme, KitFeuille f, Vector2 p, Vector2 c, float r, int n, int v)
		{
			float ny = Mathf.Clamp((p.Y - c.Y) / Mathf.Max(r, 0.5f), -1f, 1f);
			var cr = new Vector2(-f.A.Y, f.A.X);
			float cote = forme == LeafShape.Aciculaire ? 0f
				: Mathf.Clamp((p - f.B).Dot(cr) / Mathf.Max(0.35f * f.L, 0.5f), -1f, 1f) * Mathf.Sign(cr.Y);
			float grain = Hash01(69, (int)p.X + n * 16, (int)p.Y + v * 16) - 0.5f;
			return 0.6f * ny + 0.35f * cote + 0.2f * grain;
		}

		private static bool VoisinDevant(int[] proprio, int n, int i)
		{
			int x = i % n, y = i / n, k = proprio[i];
			return (x > 0 && proprio[i - 1] > k) || (x < n - 1 && proprio[i + 1] > k)
				|| (y > 0 && proprio[i - n] > k) || (y < n - 1 && proprio[i + n] > k);
		}

		private static bool VoisinPlein(int[] proprio, int n, int i)
		{
			int x = i % n, y = i / n;
			return (x > 0 && proprio[i - 1] >= 0) || (x < n - 1 && proprio[i + 1] >= 0)
				|| (y > 0 && proprio[i - n] >= 0) || (y < n - 1 && proprio[i + n] >= 0);
		}
	}
}
