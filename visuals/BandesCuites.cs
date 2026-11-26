// SYMBIOSE — BandesCuites.cs (sprint BOIS & ARBRES ③ — chargeur commun des bandes de tons)
// Le CHARGEUR d'un jeu de BANDES PÉRIODIQUES cuites par tools/splat/cuire_ecorces.js : les
// écorces (②, `ecorces.json`) et les limbes des graminées (③, `limbes.json`). Extrait d'Ecorces.cs
// au ③ : même code, un jeu par instance. Une bande = (nom, âge) × palier (×4 → ×32), rangée dans
// une planche par palier (`<jeu>_x<z>.png`) ; sa période en cm est dans le manifeste.
//
// Les bandes ne portent que des TONS (marques), en orientation « plate ». Le ton de base (2) est
// rendu TRANSPARENT : la bande se pose PAR-DESSUS une pièce déjà teinte et modelée (tube, brin).
//
// Texture construite au chargement (une par palier, seul le palier courant est gardé) :
//   rangées 0-1 = BLANC opaque (③) : le texel (0, 0) sert d'UV « uni ». Un aplat posé dans le
//                 même lot que les bandes (âme du petit bois, brin de graminée) lit ce blanc :
//                 couleur de sommet × blanc = sa couleur → aplats et marques en UN seul envoi ;
//   moitié haute = CODES (255, 255, code, 255) → × modulate (palette, palette, 1, 1), comme les
//                  pièces splat (SplatPlanches.cs) — lue par le shader de la LUT ;
//   moitié basse = gris LITTÉRAL (part de l'éclat par ton, `PlantRenderer.GrisTon`) → × la teinte
//                  d'éclat de la rampe : le dessin direct (repli, F11 OFF) montre le même motif.
//
// 📖 Pédagogie (embarqué) : c'est un masque de sérigraphie posé sur une pièce déjà peinte —
// le masque ne dit QUE où mettre l'encre sombre ; la couleur de la pièce et son éclairage
// restent ceux d'en dessous.
//
// Déterministe (fichiers versionnés), purement visuel : golden non concerné.

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	internal sealed class BandesCuites
	{
		private static readonly int[] Paliers = { 4, 8, 16, 32 };
		private const int RangeesBlanches = 2;

		/// <summary>Une bande prête à plaquer : texture du palier, rectangle des CODES et du
		/// LITTÉRAL (texels), période en cm.</summary>
		internal readonly record struct Bande(ImageTexture Tex, Rect2 Codes, Rect2 Litteral, float PeriodeCm);

		private readonly record struct Brute(Rect2I Rect, float PeriodeCm);

		private readonly string _manifeste;
		private readonly string[] _ages;
		private Dictionary<(string Nom, int Age, int Palier), Brute> _bandes;
		private Dictionary<int, string> _fichiers;
		private int _palier = -1;
		private ImageTexture _tex;
		private int _hPlanche;

		/// <summary>`manifeste` : nom du JSON dans assets/splats ; `ages` : noms d'âges du
		/// manifeste, dans l'ordre des indices passés à `Trouver`.</summary>
		public BandesCuites(string manifeste, params string[] ages)
		{
			_manifeste = manifeste;
			_ages = ages;
		}

		/// <summary>La bande `nom` × `age` au palier servi pour `zoom` (le plus grand ≤ zoom,
		/// ×4 au moins). Faux si elle n'est pas cuite (manifeste ou planche absents).</summary>
		public bool Trouver(string nom, int age, float zoom, out Bande b)
		{
			b = default;
			if (!Manifeste()) return false;
			int z = Paliers[0];
			foreach (int p in Paliers) if (p <= zoom + 1e-3f) z = p;
			if (!_bandes.TryGetValue((nom, age, z), out var br) || !Charger(z)) return false;
			var r = new Rect2(br.Rect.Position + new Vector2I(0, RangeesBlanches), br.Rect.Size);
			b = new Bande(_tex, r, new Rect2(r.Position + new Vector2(0f, _hPlanche), r.Size), br.PeriodeCm);
			return true;
		}

		private bool Manifeste()
		{
			if (_bandes != null) return _bandes.Count > 0;
			_bandes = new();
			_fichiers = new();
			string chemin = SplatPlanches.Dossier + _manifeste;
			if (!FileAccess.FileExists(chemin)) { GD.PushWarning($"[BandesCuites] manifeste absent : {chemin}"); return false; }
			var m = Json.ParseString(FileAccess.GetFileAsString(chemin)).AsGodotDictionary();
			foreach (var (k, v) in m["planches"].AsGodotDictionary())
				_fichiers[Mathf.RoundToInt(k.AsString().TrimStart('x').ToFloat())] = v.AsString();
			foreach (var v in m["bandes"].AsGodotArray())
			{
				var d = v.AsGodotDictionary();
				int[] rect = d["rect"].AsInt32Array();
				int age = System.Array.IndexOf(_ages, d["age"].AsString());
				_bandes[(d["essence"].AsString(), age, d["palier"].AsInt32())] =
					new Brute(new Rect2I(rect[0], rect[1], rect[2], rect[3]), d["periode_cm"].AsSingle());
			}
			return _bandes.Count > 0;
		}

		// Texture du palier `z` : blanc, codes, littéral (cf. en-tête). Un seul palier gardé : au
		// changement de zoom, l'ancien est libéré (mémoïsé tant que le palier tient).
		private bool Charger(int z)
		{
			if (_palier == z) return _tex != null;
			_palier = z;
			_tex = null;
			if (!_fichiers.TryGetValue(z, out string f)) return false;
			var img = SplatPlanches.LireImage(SplatPlanches.Dossier + f);
			if (img == null) return false;
			int w = img.GetWidth(), h = img.GetHeight();
			int blanc = w * RangeesBlanches * 4, moitie = w * h * 4;
			byte[] src = img.GetData(), dst = new byte[blanc + 2 * moitie];
			System.Array.Fill(dst, (byte)255, 0, blanc);
			for (int i = 0; i < moitie; i += 4)
			{
				int ton = (src[i + 1] >> 4) & 7;
				if (src[i + 3] < 128 || ton == PaletteIndexee.TonBase) continue;   // base : transparent
				int c = blanc + i, l = blanc + moitie + i;
				dst[c] = 255; dst[c + 1] = 255; dst[c + 2] = src[i + 1]; dst[c + 3] = 255;
				byte gris = (byte)(255f * PlantRenderer.GrisTon[Mathf.Clamp(ton, 0, 4)]);
				dst[l] = gris; dst[l + 1] = gris; dst[l + 2] = gris; dst[l + 3] = 255;
			}
			_tex = ImageTexture.CreateFromImage(Image.CreateFromData(w, RangeesBlanches + h * 2, false, Image.Format.Rgba8, dst));
			_hPlanche = h;
			return true;
		}
	}
}
