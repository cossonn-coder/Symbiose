// SYMBIOSE — Ecorces.cs (sprint BOIS & ARBRES ② — écorces cuites)
// Le CHARGEUR des bandes d'écorce cuites par tools/splat/cuire_ecorces.js : 13 essences (les 12
// arbres + « Generique ») × 3 âges (rameau, branche, tronc) × 4 paliers (×4 → ×32), rangées
// dans une planche par palier (`assets/splats/ecorces_x<z>.png`) + `ecorces.json`.
//
// Une bande = un cylindre sculpté photographié de face, PÉRIODIQUE en hauteur (la période en
// cm est dans le manifeste). Elle ne porte que des TONS (crevasses, plaques, lenticelles), en
// orientation « plate » : le modelé du flanc (côté soleil) reste celui de la géométrie du tube
// (décision C3, maquette du ②, cf. 00_etat). Le ton de base (2) est rendu TRANSPARENT : la
// bande se pose PAR-DESSUS l'âme et les flancs orientés du tube, seules ses marques se voient.
//
// Texture construite au chargement (une par palier, seul le palier courant est gardé) :
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
	internal static class Ecorces
	{
		public const int Rameau = 0, Branche = 1, Tronc = 2;
		public const string Generique = "Generique";
		private static readonly string[] Ages = { "rameau", "branche", "tronc" };
		private static readonly int[] Paliers = { 4, 8, 16, 32 };

		/// <summary>Une bande prête à plaquer : texture du palier, rectangle des CODES et du
		/// LITTÉRAL (texels), période en cm.</summary>
		internal readonly record struct Bande(ImageTexture Tex, Rect2 Codes, Rect2 Litteral, float PeriodeCm);

		private readonly record struct Brute(Rect2I Rect, float PeriodeCm);

		private static Dictionary<(string Essence, int Age, int Palier), Brute> _bandes;
		private static Dictionary<int, string> _fichiers;
		private static int _palier = -1;
		private static ImageTexture _tex;
		private static int _hPlanche;

		/// <summary>La bande `essence` × `age` au palier servi pour `zoom` (le plus grand ≤ zoom,
		/// ×4 au moins). Faux si l'écorce n'est pas cuite (manifeste ou planche absents).</summary>
		public static bool Trouver(string essence, int age, float zoom, out Bande b)
		{
			b = default;
			if (!Manifeste()) return false;
			int z = Paliers[0];
			foreach (int p in Paliers) if (p <= zoom + 1e-3f) z = p;
			if (!_bandes.TryGetValue((essence, age, z), out var br) || !Charger(z)) return false;
			var r = (Rect2)br.Rect;
			b = new Bande(_tex, r, new Rect2(r.Position + new Vector2(0f, _hPlanche), r.Size), br.PeriodeCm);
			return true;
		}

		private static bool Manifeste()
		{
			if (_bandes != null) return _bandes.Count > 0;
			_bandes = new();
			_fichiers = new();
			string chemin = SplatPlanches.Dossier + "ecorces.json";
			if (!FileAccess.FileExists(chemin)) { GD.PushWarning($"[Ecorces] manifeste absent : {chemin}"); return false; }
			var m = Json.ParseString(FileAccess.GetFileAsString(chemin)).AsGodotDictionary();
			foreach (var (k, v) in m["planches"].AsGodotDictionary())
				_fichiers[Mathf.RoundToInt(k.AsString().TrimStart('x').ToFloat())] = v.AsString();
			foreach (var v in m["bandes"].AsGodotArray())
			{
				var d = v.AsGodotDictionary();
				int[] rect = d["rect"].AsInt32Array();
				int age = System.Array.IndexOf(Ages, d["age"].AsString());
				_bandes[(d["essence"].AsString(), age, d["palier"].AsInt32())] =
					new Brute(new Rect2I(rect[0], rect[1], rect[2], rect[3]), d["periode_cm"].AsSingle());
			}
			return _bandes.Count > 0;
		}

		// Texture du palier `z` : codes en haut, littéral en bas (cf. en-tête). Un seul palier
		// gardé : au changement de zoom, l'ancien est libéré (mémoïsé tant que le palier tient).
		private static bool Charger(int z)
		{
			if (_palier == z) return _tex != null;
			_palier = z;
			_tex = null;
			if (!_fichiers.TryGetValue(z, out string f)) return false;
			var img = SplatPlanches.LireImage(SplatPlanches.Dossier + f);
			if (img == null) return false;
			int w = img.GetWidth(), h = img.GetHeight();
			byte[] src = img.GetData(), dst = new byte[w * h * 2 * 4];
			int moitie = w * h * 4;
			for (int i = 0; i < moitie; i += 4)
			{
				int ton = (src[i + 1] >> 4) & 7;
				if (src[i + 3] < 128 || ton == PaletteIndexee.TonBase) continue;   // base : transparent
				dst[i] = 255; dst[i + 1] = 255; dst[i + 2] = src[i + 1]; dst[i + 3] = 255;
				byte gris = (byte)(255f * PlantRenderer.GrisTon[Mathf.Clamp(ton, 0, 4)]);
				dst[moitie + i] = gris; dst[moitie + i + 1] = gris; dst[moitie + i + 2] = gris; dst[moitie + i + 3] = 255;
			}
			_tex = ImageTexture.CreateFromImage(Image.CreateFromData(w, h * 2, false, Image.Format.Rgba8, dst));
			_hPlanche = h;
			return true;
		}
	}
}
