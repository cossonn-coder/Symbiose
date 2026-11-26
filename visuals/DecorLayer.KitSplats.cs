// SYMBIOSE — DecorLayer.KitSplats.cs (partial, sprint LISIÈRE & CHARGEMENT ①, décision L7)
// Le KIT DE LA LISIÈRE tiré des pièces précuites en splats (tools/splat/recettes/lisiere.js :
// une recette `lisiere_<forme>` par forme de l'enum Piece, planche `kit` de chacune), au lieu
// du générateur à la règle (DecorLayer.KitCodes.cs). Patron : PlantRenderer.KitSplats.cs.
//
//  • MÊME FORMAT que CoderPiece : un octet de code de palette indexée par pixel
//    (`128 | ton << 4 | orientation`, 0 = vide), case EXACTE de `Tailles` (largeur ×
//    hauteur). Le code est COPIÉ tel quel depuis le canal G de la planche ; seules deux
//    couches reçoivent un ton à elles, comme le dessin d'avant : le cœur de la fleurette
//    (éclat) et la massette du roseau (creux brun). La fleurette entière garde
//    l'orientation « fleur » (OrientFleur) que la saison sait reconnaître.
//  • MÊMES CLÉS : (forme, index de taille, variante 0-2). La planche range ses pièces par
//    `taille_px` = LARGEUR de la case (unique dans une forme).
//  • MÊME ANCRAGE : PoserPiece pose le BAS-CENTRE de la case sur le pied. La pièce cuite
//    (toutes couches réunies sur leur attache) est donc posée en bas de sa case, centrée.
//    La cuisson l'a déjà mise à la taille de la case (cuire.js `boites`) ; un débord
//    éventuel serait rogné (haut et côtés), jamais le pied.
//  • INTERRUPTEUR : Maj+F11 / SYMBIOSE_SPLATS=0 (PlantRenderer.SplatsActifs). Les cases ne
//    changent pas de place d'une source à l'autre → la bascule RÉÉCRIT l'atlas en place et
//    le renvoie au GPU ; les mailles (qui ne portent que des UV de cases) restent valides,
//    aucune reconstruction. Recette, planche ou pièce absente → avertissement et kit
//    généré, ENTIER (jamais un mélange des deux sources).
//
// 📖 Pédagogie : un ADAPTATEUR — la nouvelle source est remise dans la forme exacte
// qu'attend l'ancien consommateur (l'atlas de codes, les UV des mailles). En embarqué :
// changer le contenu d'une table en ROM sans toucher aux adresses que le code lit.
//
// Déterministe (fichiers versionnés, aucune graine), purement visuel : golden non concerné.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// Recette de chaque forme, dans l'ordre de l'enum Piece.
		private static readonly string[] RecettesLisiere =
		{
			"lisiere_herbe", "lisiere_herbe_haute", "lisiere_fleur", "lisiere_roncier", "lisiere_sous_bois",
			"lisiere_feuillu", "lisiere_conifere", "lisiere_galet", "lisiere_bloc", "lisiere_roseau",
		};

		// Pièces splat lues une fois : null = pas encore lues, vide = lecture ratée (repli
		// définitif sur le kit généré, un seul avertissement).
		private static Dictionary<(Piece, int, int), byte[]> _kitSplat;

		/// <summary>Codes de toutes les pièces (forme, taille, variante), dans l'ordre de
		/// rangement de l'atlas : splats si l'interrupteur est allumé et le kit complet,
		/// sinon les pièces générées (CoderPiece).</summary>
		private static Dictionary<(Piece, int, int), byte[]> CodesKit()
		{
			var splat = PlantRenderer.SplatsActifs ? KitSplat() : null;
			var codes = new Dictionary<(Piece, int, int), byte[]>();
			for (int f = 0; f < NbPieces; f++)
				for (int i = 0; i < Tailles[f].Length; i++)
					for (int v = 0; v < Variantes; v++)
						codes[((Piece)f, i, v)] = splat != null ? splat[((Piece)f, i, v)]
							: CoderPiece((Piece)f, Tailles[f][i].X, Tailles[f][i].Y, v);
			return codes;
		}

		/// <summary>Maj+F11 : la lisière change de source. Atlas réécrit en place (mêmes
		/// cases) puis renvoyé ; rien à faire s'il n'est pas encore construit (il lira
		/// l'interrupteur à sa construction).</summary>
		internal static void BasculerSplats()
		{
			if (_kitTex == null || _kitImg == null) return;
			var codes = CodesKit();
			_kitImg.FillRect(new Rect2I(0, 0, AtlasW, _swatchY0), new Color(0f, 0f, 0f, 0f));
			_kitCodes.Clear();
			for (int t = 0; t < TeintesBase.Length; t++)
			{
				long src = SourceTeinte(t);
				foreach (var ((f, i, v), c) in codes)
					_kitCodes.Add((_kitRects[IndexKit(t, (int)f, i, v)], c, src));
			}
			BasculerBois();   // LISIÈRE ② : bandes d'écorce gardées, bois des arbres reconstruit
			EcrireAtlasCodes(_swatchY0);
			TeleverserKit();
			GD.Print($"[DecorLayer] lisière : kit {(PlantRenderer.SplatsActifs && KitSplat() != null ? "splats" : "généré")}.");
		}

		// Lit les 10 recettes ; null (et repli) s'il en manque une, ou une pièce attendue.
		private static Dictionary<(Piece, int, int), byte[]> KitSplat()
		{
			if (_kitSplat != null) return _kitSplat.Count > 0 ? _kitSplat : null;
			_kitSplat = new();
			ulong t0 = Time.GetTicksUsec();
			var tout = new Dictionary<(Piece, int, int), byte[]>();
			for (int f = 0; f < NbPieces; f++)
			{
				var pieces = LirePlancheLisiere(RecettesLisiere[f], (Piece)f);
				if (pieces == null) return null;
				for (int i = 0; i < Tailles[f].Length; i++)
					for (int v = 0; v < Variantes; v++)
					{
						Vector2I s = Tailles[f][i];
						if (!pieces.TryGetValue((s.X, v), out var p))
						{
							GD.PushWarning($"[DecorLayer] pièce splat absente ({RecettesLisiere[f]} {s.X} px v{v}) : kit généré.");
							return null;
						}
						tout[((Piece)f, i, v)] = Caser(p, s.X, s.Y);
					}
			}
			_kitSplat = tout;
			GD.Print($"[DecorLayer] lisière : kit splats lu ({tout.Count} pièces, {(Time.GetTicksUsec() - t0) / 1000.0:F1} ms).");
			return tout;
		}

		// Une pièce fondue : codes rangée par rangée, taille, boîte de toutes les couches.
		private readonly record struct PieceLisiere(byte[] Codes, int L, int H);

		// Pièces d'une recette par (taille_px, variante), couches fondues sur leur attache
		// commune (couche 0 d'abord, les suivantes par-dessus). LISIÈRE ③ : `planche` choisit
		// la planche lue (« kit » = ×4 ; « x8 »… = paliers hauts, DecorLayer.Hauts.cs).
		private static Dictionary<(int, int), PieceLisiere> LirePlancheLisiere(string recette, Piece forme, string planche = "kit")
		{
			string chemin = SplatPlanches.Dossier + recette + ".json";
			// Repli annoncé selon l'appelant (LISIÈRE ⑤) : planche « kit » → kit généré ;
			// paliers hauts → forme ×4 agrandie (DecorLayer.Hauts.cs), pas le kit généré.
			string repli = planche == "kit" ? "kit généré" : "forme ×4 agrandie";
			if (!FileAccess.FileExists(chemin)) { GD.PushWarning($"[DecorLayer] manifeste absent : {chemin} ({repli})."); return null; }
			var m = Json.ParseString(FileAccess.GetFileAsString(chemin)).AsGodotDictionary();
			if (!m["planches"].AsGodotDictionary().TryGetValue(planche, out var fichier))
			{
				GD.PushWarning($"[DecorLayer] planche « {planche} » absente de {chemin} ({repli}).");
				return null;
			}
			var img = SplatPlanches.LireImage(SplatPlanches.Dossier + fichier.AsString());
			if (img == null) return null;
			var nomsCouches = new List<string>();
			if (m.TryGetValue("couches", out var cs)) foreach (var c in cs.AsGodotArray()) nomsCouches.Add(c.AsString());
			var brutes = new Dictionary<(int, int), List<(Rect2I R, Vector2I A, int Couche)>>();
			foreach (var e in m["pieces"].AsGodotArray())
			{
				var p = e.AsGodotDictionary();
				if (p.TryGetValue("planche", out var pl) && pl.AsString() != planche) continue;
				int[] rc = p["rect"].AsInt32Array(), at = p["attache"].AsInt32Array();
				int couche = p.TryGetValue("couche", out var c) ? Mathf.Max(0, nomsCouches.IndexOf(c.AsString())) : 0;
				var cle = (p["taille_px"].AsInt32(), p["variante"].AsInt32());
				if (!brutes.TryGetValue(cle, out var liste)) brutes[cle] = liste = new();
				liste.Add((new Rect2I(rc[0], rc[1], rc[2], rc[3]), new Vector2I(at[0], at[1]), couche));
			}
			byte[] src = img.GetData();
			var res = new Dictionary<(int, int), PieceLisiere>();
			foreach (var (cle, liste) in brutes) res[cle] = Fondre(liste, src, img.GetWidth(), forme);
			return res;
		}

		private static PieceLisiere Fondre(List<(Rect2I R, Vector2I A, int Couche)> couches, byte[] src, int w, Piece forme)
		{
			int x0 = int.MaxValue, y0 = int.MaxValue, x1 = int.MinValue, y1 = int.MinValue;
			foreach (var (r, a, _) in couches)
			{
				if (r.Size.X <= 0 || r.Size.Y <= 0) continue;
				x0 = Mathf.Min(x0, -a.X); y0 = Mathf.Min(y0, -a.Y);
				x1 = Mathf.Max(x1, r.Size.X - a.X); y1 = Mathf.Max(y1, r.Size.Y - a.Y);
			}
			if (x1 <= x0) return new PieceLisiere(new byte[1], 1, 1);   // pièce vide
			int l = x1 - x0, h = y1 - y0;
			var codes = new byte[l * h];
			couches.Sort((p, q) => p.Couche.CompareTo(q.Couche));
			foreach (var (r, a, couche) in couches)
				for (int y = 0; y < r.Size.Y; y++)
					for (int x = 0; x < r.Size.X; x++)
					{
						int s = ((r.Position.Y + y) * w + r.Position.X + x) * 4;
						if (src[s + 3] < 128) continue;
						codes[(y - a.Y - y0) * l + (x - a.X - x0)] = CodeLisiere(src[s + 1], forme, couche);
					}
			return new PieceLisiere(codes, l, h);
		}

		// Code d'un pixel cuit : tel quel, sauf la fleurette (orientation « fleur », cœur à
		// l'éclat) et la massette du roseau (creux) — les tons du dessin d'avant.
		private static byte CodeLisiere(byte g, Piece forme, int couche) => forme switch
		{
			Piece.Fleur => couche > 0 ? C(4, OrientFleur) : C((g >> 4) & 7, OrientFleur),
			Piece.Roseau when couche > 0 => C(0, PaletteIndexee.OrientPlat),
			_ => g,
		};

		// La pièce dans sa case w × hh : en bas, centrée (pied = bas-centre, PoserPiece).
		private static byte[] Caser(PieceLisiere p, int w, int hh)
		{
			var c = new byte[w * hh];
			int ox = (w - p.L) / 2, oy = hh - p.H;
			for (int y = 0; y < p.H; y++)
				for (int x = 0; x < p.L; x++)
				{
					int dx = ox + x, dy = oy + y;
					if (dx < 0 || dx >= w || dy < 0) continue;   // débord rogné (jamais le pied)
					c[dy * w + dx] = p.Codes[y * p.L + x];
				}
			return c;
		}
	}
}
