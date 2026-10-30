// SYMBIOSE — PaletteIndexee.cs (sprint CASSÉ À L'ÉCRAN ③ — palette indexée + soleil)
// La PALETTE INDEXÉE des plantes cuites aux paliers bas (×0,5 · ×1 · ×2) : la
// cuisson n'écrit plus une COULEUR par pixel mais un CODE, et un shader de lecture
// unique (`palette_indexee.gdshader`) choisit la couleur dans une LUT selon la
// direction du soleil RÉEL. Le soleil tourne → seul un uniform change : 0 recuisson.
//
// 📖 Pédagogie (analogie embarqué) : c'est la CGRAM de la SNES, ou la LUT d'un
// contrôleur d'écran 8 bits. Le framebuffer contient des indices ; la palette est
// une petite table à part. Changer une entrée de la table recolore tout ce qui
// pointe dessus, sans réécrire un seul pixel du framebuffer.
//
// ENCODAGE d'un pixel de l'atlas (RGBA8, documenté pour ④⑤⑥) :
//   R = n° de palette, octet bas      G = n° de palette, octet haut (≤ 63)
//   B = 128 | ton << 4 | orientation  (bit 7 = « pixel indexé »)
//       ton 0..4 = creux · ombre · BASE · clair · éclat (indice dans la rampe)
//       orientation 0..7 = normale de face quantifiée (k × 45°, 0 = droite, 2 = bas,
//       6 = haut, en repère ÉCRAN), 8 = « plat » (ne réagit pas au soleil)
//   A = 1 (pixel posé) / 0 (vide) — jamais de demi-transparence aux paliers bas.
// Le shader : face vers le soleil → ton +1 (+2 si franchement en face = éclat),
// face opposée → ton −1 ; puis lit la LUT (64 palettes de 8 texels par ligne).
//
// PALETTE = une rampe de 5 tons `RampesDa.Deriver(base)` (teinte qui dérive :
// ombre vers le bleu-vert, éclat vers le jaune ; ton 2 = la couleur d'origine).
// Une palette par couleur de base DISTINCTE (quantifiée à 6 bits par canal) :
// teinte d'espèce × saison × santé × givre, bois, neige, fleur. Mémoïsée — jamais
// recalculée tant que la couleur ne change pas (feedback « pas de recalcul »).
//
// Déterministe (aucun aléa), purement visuel : golden non concerné.

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	internal static class PaletteIndexee
	{
		private const string ShaderPath = "res://visuals/palette_indexee.gdshader";
		// LUT : 512 × 256 texels = 64 palettes × 8 texels par ligne × 256 lignes =
		// 16 384 palettes (n° sur 14 bits : R + 6 bits de G). 512 Ko de mémoire vidéo.
		private const int LutLargeur = 512, LutHauteur = 256, TexelsParPalette = 8;
		private const int PalettesParLigne = LutLargeur / TexelsParPalette;
		public const int Capacite = PalettesParLigne * LutHauteur;
		public const int TonBase = 2, OrientPlat = 8;
		private const int DrapeauIndexe = 128;

		private static readonly Dictionary<int, int> _parCouleur = new();
		// ⑥ : palettes NOMMÉES (rampe exacte du brief, pas dérivée) — décor dialecte 2.
		private static readonly Dictionary<string, int> _parNom = new();
		private static int _nb;   // palettes allouées (dérivées + nommées)
		private static Image _lut;
		private static ImageTexture _tex;
		private static bool _sale;
		private static ShaderMaterial _mat;
		private static Vector2 _soleil = new(float.NaN, 0f);

		/// <summary>F11 (debug) : palette indexée active (défaut) ou rendu littéral
		/// d'avant ③ (comparer avant/après au F5).</summary>
		public static bool Active { get; private set; } = true;

		/// <summary>Compteur de vidages de la LUT (⑤) : un atlas qui a mémorisé des n° de
		/// palette (portraits de faune) se recuit quand il change.</summary>
		public static int Generation { get; private set; }

		/// <summary>Matériau de LECTURE, partagé par toutes les plantes affichant une
		/// image indexée (un seul matériau → Godot garde le regroupement des envois).</summary>
		public static ShaderMaterial Materiau
		{
			get
			{
				if (_mat != null) return _mat;
				Assurer();
				_mat = new ShaderMaterial { Shader = GD.Load<Shader>(ShaderPath) };
				_mat.SetShaderParameter("lut", _tex);
				if (!float.IsNaN(_soleil.X)) _mat.SetShaderParameter("soleil", _soleil);   // ⑥
				return _mat;
			}
		}

		private static void Assurer()
		{
			if (_lut != null) return;
			_lut = Image.CreateEmpty(LutLargeur, LutHauteur, false, Image.Format.Rgba8);
			_tex = ImageTexture.CreateFromImage(_lut);
		}

		/// <summary>N° de palette de la rampe dérivée de `baseCol` (créée au besoin).</summary>
		public static int Palette(Color baseCol)
		{
			int cle = Quant(baseCol.R) << 12 | Quant(baseCol.G) << 6 | Quant(baseCol.B);
			if (_parCouleur.TryGetValue(cle, out int id)) return id;
			Assurer();
			if (_nb >= Capacite) Vider();
			id = _nb++;
			_parCouleur[cle] = id;
			Ecrire(id, RampesDa.Deriver(new Color(Dequant(cle >> 12), Dequant(cle >> 6), Dequant(cle))));
			return id;
		}

		/// <summary>⑥ : n° de la palette d'une matière du brief, rampe EXACTE
		/// (`RampesDa.Matieres[nom]`, pas dérivée). 5 tons tels quels ; 4 tons =
		/// [0, 0, 1, 2, 3] (le plus sombre sert de creux ET d'ombre, base = 2ᵉ ton :
		/// 3 tons + éclat, « pierre ») ; 6 tons = sans l'avant-dernier (éclat isolé gardé).</summary>
		public static int PaletteNommee(string nom)
		{
			if (_parNom.TryGetValue(nom, out int id)) return id;
			Assurer();
			if (_nb >= Capacite) Vider();
			id = _nb++;
			_parNom[nom] = id;
			Color[] m = RampesDa.Matieres[nom];
			Color[] r = m.Length switch
			{
				>= 6 => new[] { m[0], m[1], m[2], m[3], m[m.Length - 1] },
				5 => m,
				4 => new[] { m[0], m[0], m[1], m[2], m[3] },
				_ => RampesDa.Deriver(m[m.Length / 2]),
			};
			Ecrire(id, r);
			return id;
		}

		/// <summary>⑥ : direction écran vers le soleil courante (NaN avant la 1ʳᵉ
		/// MajSoleil) — le décor la pose sur son propre matériau.</summary>
		public static Vector2 Soleil => _soleil;

		private static void Ecrire(int id, Color[] rampe)
		{
			int x0 = id % PalettesParLigne * TexelsParPalette, y = id / PalettesParLigne;
			for (int t = 0; t < TexelsParPalette; t++)
				_lut.SetPixel(x0 + t, y, rampe[Mathf.Min(t, rampe.Length - 1)]);
			if (!_sale)
			{
				_sale = true;
				// Téléversement groupé en fin d'image (avant le rendu), une fois.
				Callable.From(Televerser).CallDeferred();
			}
		}

		/// <summary>⑥ : la LUT (texture) — le matériau du décor la lit aussi.</summary>
		public static Texture2D Lut { get { Assurer(); return _tex; } }

		/// <summary>Couleur ENCODÉE à passer comme couleur de dessin (DrawLine, modulate
		/// d'une pièce de kit…) : n° de palette, ton, orientation.</summary>
		public static Color Code(int palette, int ton = TonBase, int orient = OrientPlat) =>
			new(Octet(palette & 255), Octet(palette >> 8), Octet(OctetB(ton, orient)), 1f);

		/// <summary>Couleur littérale → son code (palette dérivée, ton de base, plat).</summary>
		public static Color Litterale(Color c) => Code(Palette(c));

		/// <summary>Modulate d'une pièce de kit : le canal B vient de la texture des
		/// codes (ton + orientation par pixel), R/G = n° de palette.</summary>
		public static Color ModulatePiece(int palette) =>
			new(Octet(palette & 255), Octet(palette >> 8), 1f, 1f);

		/// <summary>Octet B d'un pixel indexé (cf. en-tête).</summary>
		public static byte OctetB(int ton, int orient) => (byte)(DrapeauIndexe | ton << 4 | orient);

		/// <summary>Envoie la LUT au GPU si une palette a été ajoutée.</summary>
		public static void Televerser()
		{
			if (!_sale || _tex == null) return;
			_tex.Update(_lut);
			_sale = false;
		}

		/// <summary>Direction ÉCRAN vers le soleil : la direction d'ombre (monde)
		/// retournée et projetée (suit la rotation D35) + l'élévation (vers le haut de
		/// l'écran). Appelé chaque image, n'écrit l'uniform qu'au changement.</summary>
		public static void MajSoleil()
		{
			// ⑥ : calculé même sans matériau de plante (le décor lit `Soleil`).
			float sinE = Mathf.Clamp(WorldView.SunStrength, 0f, 1f);
			float cosE = Mathf.Sqrt(1f - sinE * sinE);
			Vector2 d = WorldView.SunShadowDir;
			Vector2 s = -WorldView.WorldToScreenOffset(d.X, d.Y) * cosE
				+ new Vector2(0f, -WorldView.PxPerCmZ) * sinE;
			s = s.LengthSquared() > 1e-8f ? s.Normalized() : new Vector2(0f, -1f);
			if (s.IsEqualApprox(_soleil)) return;
			_soleil = s;
			_mat?.SetShaderParameter("soleil", s);
		}

		/// <summary>Angle écran du soleil (0° = droite, 90° = haut : convention de
		/// `tools/mesure_da.py --soleil`), pour le journal du banc.</summary>
		public static float AngleSoleilDeg => float.IsNaN(_soleil.X) ? float.NaN
			: Mathf.PosMod(Mathf.RadToDeg(Mathf.Atan2(-_soleil.Y, _soleil.X)), 360f);

		/// <summary>F11 : bascule avant/après ; toutes les plantes recuisent.</summary>
		public static void Basculer()
		{
			Active = !Active;
			foreach (var p in BakeQueue.All) p.Invalidate();
			GD.Print($"[PaletteIndexee] F11 → palette indexée {(Active ? "ON" : "OFF (littéral d'avant ③)")}.");
		}

		// LUT pleine (16 384 couleurs distinctes vues depuis le lancement) : on repart
		// d'une table vide et tout le jardin recuit (rare ; journalisé).
		private static void Vider()
		{
			_parCouleur.Clear();
			_parNom.Clear();
			_nb = 0;
			Generation++;
			GD.Print($"[PaletteIndexee] LUT pleine ({Capacite} palettes) → vidée, recuisson générale.");
			foreach (var p in BakeQueue.All) p.Invalidate();
		}

		private static int Quant(float v) => Mathf.Clamp((int)(v * 63f + 0.5f), 0, 63);
		private static float Dequant(int q) => (q & 63) / 63f;
		private static float Octet(int v) => v / 255f;
	}
}
