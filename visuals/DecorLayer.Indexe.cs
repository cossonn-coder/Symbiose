// SYMBIOSE — DecorLayer.Indexe.cs (CASSÉ À L'ÉCRAN ⑥ — le décor dans la palette INDEXÉE)
// Partial de DecorLayer : branche la lisière sur le pipeline indexé du ③ (encodage :
// visuals/PaletteIndexee.cs) avec SON shader (visuals/decor_indexe.gdshader : lecture
// de palette + grains du dialecte 2 + vent). Trois pièces :
//  1. l'ATLAS du kit écrit en CODES (n° de palette de la teinte en R/G, ton +
//     orientation en B) au lieu de couleurs (DecorLayer.KitCodes.cs peint les codes) ;
//  2. des TEXELS-CODES pour les aplats (« échantillons ») : un aplat de couleur c pointe
//     son UV sur un texel (palette de c, ton, orientation) alloué à la demande dans une
//     bande réservée de l'atlas — la couleur passe DANS la palette, plus dans le sommet ;
//  3. l'ENCODEUR de sommets (hook LotTriangles.Encodeur) : chaque sommet du décor reçoit
//     sa couleur de contrat (R valeur · G amplitude du vent · B phase · A alpha).
//
// 📖 Pédagogie — POURQUOI un hook plutôt que réécrire chaque tracé : la lisière compte
// une centaine d'appels Polygone/Ligne/Quad répartis dans 6 fichiers. Les intercepter
// au point UNIQUE où un sommet entre dans le tampon (comme un driver qui transcode à
// l'écriture du registre) garde les motifs inchangés ; ils ne règlent que l'ÉTAT
// d'encodage (Aplats(...), Vent(...)) autour des tracés qui le demandent.
//
// Vidage de LUT (PaletteIndexee.Generation) : les n° de palette changent → l'atlas est
// RÉÉCRIT sur place (mêmes UV, les mailles restent valides). Déterministe, vue pure.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		private const string ShaderDecor = "res://visuals/decor_indexe.gdshader";
		public const int OrientTissage = 9, OrientRoche = 10, OrientEcorceG = 11, OrientEcorceD = 12;
		private const int OPlat = PaletteIndexee.OrientPlat, TonB = PaletteIndexee.TonBase;
		private const float AmpMaxPx = 32f;   // = AMP_MAX du shader (G = 1)
		private const int SwatchRangs = 32;   // bande des texels-codes (512 × 32)

		private static ShaderMaterial _matDecor;
		private static Image _kitImg;
		private static bool _kitSale;
		private static int _kitGen;
		private static int _swatchY0;
		private static Vector2 _uvBlanc;
		// Pièces du kit à (ré)encoder : rectangle, codes, source de palette de la teinte.
		private static readonly List<(Rect2I r, byte[] codes, long src)> _kitCodes = new();
		// Texels-codes : clé (source, ton, orientation) → UV ; liste pour la réécriture.
		private static readonly Dictionary<long, Vector2> _swatchUv = new();
		private static readonly List<(int x, int y, long cle)> _swatches = new();
		private static readonly List<string> _noms = new();

		/// <summary>Matériau du décor (partagé par la couche de fond et la couche devant).</summary>
		private static ShaderMaterial MateriauDecor
		{
			get
			{
				if (_matDecor != null) return _matDecor;
				_matDecor = new ShaderMaterial { Shader = GD.Load<Shader>(ShaderDecor) };
				_matDecor.SetShaderParameter("lut", PaletteIndexee.Lut);
				return _matDecor;
			}
		}

		// --- Sources de palette : couleur (dérivée, 18 bits) ou matière nommée du brief.
		private static long SourceCouleur(Color c) =>
			Q(c.R) << 12 | Q(c.G) << 6 | Q(c.B);
		private static long Q(float v) => Mathf.Clamp((int)(v * 63f + 0.5f), 0, 63);

		private static long SourceNom(string nom)
		{
			int i = _noms.IndexOf(nom);
			if (i < 0) { _noms.Add(nom); i = _noms.Count - 1; }
			return 1L << 20 | (long)i;
		}

		private static int IdSource(long src) =>
			(src & 1L << 20) != 0 ? PaletteIndexee.PaletteNommee(_noms[(int)(src & 0xffff)])
			: PaletteIndexee.Palette(new Color((src >> 12 & 63) / 63f, (src >> 6 & 63) / 63f, (src & 63) / 63f));

		// Teinte du kit → palette. Dialecte 2 : sous-bois = couvert olive EXACT du brief,
		// herbe de prairie claire = touffe claire, roche = pierre ; le reste dérivé de sa
		// couleur d'origine (ton 2 = la couleur d'avant ③).
		private static long SourceTeinte(int t) => (Teinte)t switch
		{
			Teinte.SousBois => SourceNom("couvert_olive"),
			Teinte.PrairieClair => SourceNom("touffe_claire"),
			Teinte.Roche => SourceNom("pierre"),
			_ => SourceCouleur(TeintesBase[t]),
		};

		/// <summary>Écrit l'atlas en codes (appelé par AssurerKitDecor, puis à chaque
		/// vidage de LUT). `hKit` = hauteur des étagères du kit.</summary>
		private static void EcrireAtlasCodes(int hKit)
		{
			if (_kitImg == null)
			{
				_swatchY0 = hKit;
				_kitImg = Image.CreateEmpty(AtlasW, hKit + SwatchRangs, false, Image.Format.Rgba8);
				_uvBlanc = new Vector2(1f, 1f) / new Vector2(AtlasW, hKit + SwatchRangs);
			}
			_kitGen = PaletteIndexee.Generation;
			foreach (var (r, codes, src) in _kitCodes)
			{
				int id = IdSource(src);
				for (int py = 0; py < r.Size.Y; py++)
					for (int px = 0; px < r.Size.X; px++)
					{
						byte b = codes[py * r.Size.X + px];
						if (b != 0) Texel(r.Position.X + px, r.Position.Y + py, id, b);
					}
			}
			foreach (var (x, y, cle) in _swatches)
				Texel(x, y, IdSource(cle & 0x1fffff), PaletteIndexee.OctetB((int)(cle >> 24 & 7), (int)(cle >> 28 & 15)));
			_kitSale = true;
		}

		private static void Texel(int x, int y, int id, byte b) =>
			_kitImg.SetPixel(x, y, new Color((id & 255) / 255f, (id >> 8) / 255f, b / 255f, 1f));

		/// <summary>UV du texel-code (source, ton, orientation), alloué au besoin.</summary>
		private static Vector2 UvSwatch(long src, int ton, int orient)
		{
			long cle = src | (long)ton << 24 | (long)orient << 28;
			if (_swatchUv.TryGetValue(cle, out Vector2 uv)) return uv;
			int n = _swatches.Count;
			if (n >= AtlasW * SwatchRangs)
			{
				GD.PushWarning("[DecorLayer] bande des texels-codes pleine : aplat ramené au 1er texel.");
				return _swatchUv.Count > 0 ? _swatchUv[_swatches[0].cle] : _uvBlanc;
			}
			int x = n % AtlasW, y = _swatchY0 + n / AtlasW;
			_swatches.Add((x, y, cle));
			Texel(x, y, IdSource(src), PaletteIndexee.OctetB(ton, orient));
			_kitSale = true;
			uv = new Vector2(x + 0.5f, y + 0.5f) / _kitTaille;
			_swatchUv[cle] = uv;
			return uv;
		}

		/// <summary>Envoie l'atlas au GPU s'il a changé (nouveaux texels-codes, ou
		/// réécriture après un vidage de LUT). Appelé après chaque construction.</summary>
		private static void TeleverserKit()
		{
			if (_kitImg == null) return;
			if (_kitGen != PaletteIndexee.Generation) EcrireAtlasCodes(_swatchY0);
			if (!_kitSale) return;
			_kitTex.Update(_kitImg);
			_kitSale = false;
		}

		// --- ÉTAT D'ENCODAGE courant (posé par les motifs autour de leurs tracés) ------
		private int _tonAplat = TonB, _orientAplat = OPlat;
		private long _srcAplat = -1;            // -1 = palette dérivée de la couleur de l'aplat
		private float _ventB;                   // phase au hash (ou face de roche / 16)
		private float _ventAmpPx, _ventPiedY, _ventHautPx = 1f;
		private bool _ventArbre;                // un arbre est en cours : ses bouquets gardent son vent
		private long _derCle = -1;
		private Vector2 _derUv;
		private LotTriangles.EncodeurSommet _encodeur;

		/// <summary>Aplats suivants : orientation (OPlat, OrientTissage, OrientRoche, 0..7),
		/// ton de base, et matière nommée (null = palette dérivée de leur couleur).</summary>
		private void Aplats(int orient, int ton = TonB, string matiere = null)
		{
			_orientAplat = orient;
			_tonAplat = ton;
			_srcAplat = matiere == null ? -1 : SourceNom(matiere);
		}

		/// <summary>Vent des sommets suivants : amplitude `ampPx` (px canvas) au sommet,
		/// nulle au pied (`piedY`), linéaire sur `hautPx` ; `phase` ∈ [0,1].</summary>
		private void Vent(float ampPx, float piedY, float hautPx, float phase)
		{
			_ventAmpPx = ampPx;
			_ventPiedY = piedY;
			_ventHautPx = Mathf.Max(hautPx, 0.01f);
			_ventB = phase;
		}

		/// <summary>Remet l'état par défaut (aplat plat, pas de vent) — début de tranche.</summary>
		private void EtatDefaut()
		{
			Aplats(OPlat);
			Vent(0f, 0f, 1f, 0f);
			_ventArbre = false;
		}

		/// <summary>Branche l'encodeur sur un lot (appelé par Tranche).</summary>
		private void Brancher(LotTriangles lot)
		{
			_encodeur ??= EncoderSommet;
			lot.Encodeur = _encodeur;
		}

		private void EncoderSommet(Vector2 p, bool uni, ref Vector2 uv, ref Color c)
		{
			float amp = _ventAmpPx <= 0f ? 0f
				: Mathf.Min(1f, _ventAmpPx * Mathf.Clamp((_ventPiedY - p.Y) / _ventHautPx, 0f, 1f) / AmpMaxPx);
			if (uni || uv == _uvBlanc)
			{
				long src = _srcAplat >= 0 ? _srcAplat : SourceCouleur(c);
				long cle = src | (long)_tonAplat << 24 | (long)_orientAplat << 28;
				if (cle != _derCle) { _derUv = UvSwatch(src, _tonAplat, _orientAplat); _derCle = cle; }
				uv = _derUv;
				c = new Color(1f, amp, _ventB, c.A);
			}
			else c = new Color(c.R, amp, _ventB, c.A);
		}
	}
}
