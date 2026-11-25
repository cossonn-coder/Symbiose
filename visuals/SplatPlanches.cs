// SYMBIOSE — SplatPlanches.cs (sprint PRÉCUISSON SPLATS ④)
// Le CHARGEUR des pièces précuites en gaussian splats (tools/splat/, ①②③) :
// manifeste JSON + planches PNG de `assets/splats/`, une planche par recette et
// par palier. Il sert à la cuisson des plantes (PlantRenderer.Splats.cs) une
// pièce = (texture, rectangle, point d'attache), prête à poser.
//
// FORMAT d'une planche (00_etat ①) : R = niveau du kit (rendu littéral), G = code
// de palette indexée `128 | ton << 4 | orientation`, A = posé. Comme le kit
// (PlantRenderer.Assemblee.AssurerMasques), on en fait une texture de CODES :
// texel = (1, 1, code, 1) → × modulate (palette, palette, 1, 1) = pixel encodé
// que le shader de la LUT (palette_indexee.gdshader) éclaire côté soleil réel.
//
// CHARGEMENT (choix justifié, ④) : les PNG sont déclarés `importer="keep"`
// (`*.png.import` à côté de chaque planche), lus en octets par FileAccess puis décodés
// par `Image.LoadPngFromBuffer` (⑤ ; le ④ passait par `Image.LoadFromFile`).
//  • les octets arrivent INTACTS : c'est le décodeur PNG de Godot sur le fichier
//    lui-même — aucune compression VRAM, aucun mipmap, aucun filtrage, aucun
//    `fix_alpha_border` (que l'import « texture » par défaut appliquerait) ;
//  • à l'export (packaging t7), « keep » copie le fichier TEL QUEL dans le .pck —
//    VÉRIFIÉ au ⑤ (`--export-pack` sur la VM : les 280 planches y sont à l'octet) ;
//    l'avertissement « will not work on export » de `LoadFromFile` était un faux
//    positif (il vise les PNG importés en texture), le tampon le fait taire ;
//  • une planche > 16 384 px (limite d'une texture GPU : `feuille_paume_x32`,
//    `tete_soleil_x32`…) ne passe jamais par l'importeur de textures : on la
//    découpe ici en BANDES ≤ 16 384 px, coupées entre deux rangées de pièces
//    (aucune pièce à cheval) — les octets des pièces sont copiés à l'identique,
//    rien n'est régénéré côté outil (D2 : l'historique git ne grossit pas).
//  • les textures ne servent qu'à la CUISSON (l'image cuite vit ensuite dans
//    AtlasPages) : on ne garde que celles du palier courant (×16/×32 = 225 et
//    835 Mo RGBA si tout était chargé [somme des planches, mesurée au ④]).
//
// CLASSES DE TAILLE (RELIQUATS ②, tools/splat/lib/classes.js) : une recette est cuite
// à 1-3 échelles (champ `echelle` ×100 et `taille_cm` de chaque pièce, dans la MESURE
// de la vue : longueur de feuille, rayon du disque d'une tête). `Classe` rend l'échelle
// cuite la plus proche (en rapport) de la taille réelle que le crochet passe ; un
// manifeste sans classes a une seule échelle, 100.
//
// 📖 Pédagogie (embarqué) : c'est un chargeur de « tuiles » depuis une flash
// externe, à la demande, avec un cache borné à la page utile — on ne monte pas
// toute la ROM en RAM pour afficher un écran.
//
// Déterministe (lecture de fichiers versionnés), purement visuel : golden non concerné.

using System.Collections.Generic;
using Godot;

namespace Symbiose
{
	internal static class SplatPlanches
	{
		internal const string Dossier = "res://assets/splats/";
		private const int HauteurMaxTexture = 16384;

		/// <summary>Une pièce prête à poser : texture de codes, rectangle source,
		/// point d'attache (px de la pièce, coin haut-gauche = 0,0).</summary>
		internal readonly record struct Piece(Texture2D Tex, Rect2I Rect, Vector2I Attache);

		// Clé d'une pièce dans SA recette : palier ×2 (0,5 → 1), classe de taille (échelle ×100),
		// couche, vue, variante, trou.
		private readonly record struct Cle(int Palier2, int Echelle, int Couche, int Inclinaison, int Lacet, int Variante, int Trou);
		private readonly record struct Brute(string Planche, Rect2I Rect, Vector2I Attache);

		private sealed class Recette
		{
			public readonly Dictionary<Cle, Brute> Pieces = new();
			public string[] NomsCouches = { "" };
			public int Lacets = 1, Variantes = 1;
			public int[] Inclinaisons = { 0 };
			// Classes de taille, croissantes : (échelle ×100, taille vue en cm ; 0 = inconnue).
			public (int Echelle, float TailleCm)[] Tailles = { (100, 0f) };
		}

		// Une planche chargée = ses bandes (y0 de la bande dans la planche, texture).
		private sealed class Planche
		{
			public readonly List<(int Y0, int Y1, ImageTexture Tex)> Bandes = new();
			public int Palier2;
			public long Octets;
			public ulong DernierUsage;   // image (process frame) du dernier Trouver, RELIQUATS ①
		}

		private static readonly Dictionary<string, Recette> _recettes = new();
		private static readonly Dictionary<(string, string), Planche> _planches = new();
		private static int _palierCourant2 = -1;

		/// <summary>Mémoire vidéo des planches de codes chargées (octets RGBA8).</summary>
		internal static long OctetsCharges { get; private set; }
		/// <summary>Planches chargées depuis le lancement / temps cumulé de chargement.</summary>
		internal static int PlanchesChargees { get; private set; }
		internal static double MsChargement { get; private set; }

		/// <summary>Inclinaisons cuites (degrés) et nombre de lacets/variantes d'une
		/// recette ; false si la recette n'existe pas (manifeste absent).</summary>
		internal static bool Vues(string recette, out int[] inclinaisons, out int lacets, out int variantes)
		{
			var r = RecetteDe(recette);
			inclinaisons = r?.Inclinaisons; lacets = r?.Lacets ?? 0; variantes = r?.Variantes ?? 0;
			return r != null;
		}

		/// <summary>Noms des couches de la recette (un nom vide si une seule).</summary>
		internal static string[] Couches(string recette) => RecetteDe(recette)?.NomsCouches;

		/// <summary>Classe de taille (échelle ×100) la plus proche, EN RAPPORT, de `tailleCm` (mesure
		/// de la vue) ; `tailleCm` ≤ 0 (taille non suivie par le crochet) → la classe la plus
		/// proche de l'échelle nominale 100.</summary>
		internal static int Classe(string recette, float tailleCm)
		{
			var t = RecetteDe(recette)?.Tailles;
			if (t == null) return 100;
			int best = t[0].Echelle;
			float ecart = float.MaxValue;
			foreach (var (e, cm) in t)
			{
				float d = tailleCm > 0f && cm > 0f ? Mathf.Abs(Mathf.Log(cm / tailleCm)) : Mathf.Abs(Mathf.Log(e / 100f));
				if (d < ecart) { ecart = d; best = e; }
			}
			return best;
		}

		/// <summary>La pièce demandée, chargée au besoin ; false si elle n'existe pas ou
		/// est vide (couche effacée à ce palier, profil d'une feuille fine…).
		/// `echelle` : classe de taille (Classe) ; si sa pièce est VIDE (organe sous le pixel),
		/// la classe au-dessus la remplace — comme l'ancien dessin, borné à un pixel.
		/// `trou` : 0 sain, 1-2 morsure, 3-4 grêle (degré 1-2).</summary>
		internal static bool Trouver(string recette, float palier, int echelle, int couche, int inclinaison, int lacetDeg,
									 int variante, int trou, out Piece piece)
		{
			piece = default;
			var r = RecetteDe(recette);
			int p2 = Mathf.RoundToInt(palier * 2f);
			if (r == null) return false;
			Brute b = default;
			bool trouvee = false;
			foreach (var (e, _) in r.Tailles)
			{
				if (e < echelle || !r.Pieces.TryGetValue(new Cle(p2, e, couche, inclinaison, lacetDeg, variante, trou), out b)) continue;
				if (b.Rect.Size.X > 0 && b.Rect.Size.Y > 0) { trouvee = true; break; }
			}
			if (!trouvee) return false;
			OublierAutresPaliers(p2);
			var pl = PlancheDe(recette, b.Planche, p2, r);
			if (pl == null) return false;
			pl.DernierUsage = Engine.GetProcessFrames();
			foreach (var (y0, y1, tex) in pl.Bandes)
			{
				if (b.Rect.Position.Y < y0 || b.Rect.End.Y > y1) continue;
				piece = new Piece(tex, new Rect2I(b.Rect.Position.X, b.Rect.Position.Y - y0, b.Rect.Size), b.Attache);
				return true;
			}
			return false;
		}

		// --- Manifeste --------------------------------------------------------------

		private static Recette RecetteDe(string nom)
		{
			if (_recettes.TryGetValue(nom, out var r)) return r;
			long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
			_recettes[nom] = r = LireManifeste(nom);
			double ms = System.Diagnostics.Stopwatch.GetElapsedTime(t0).TotalMilliseconds;
			MsChargement += ms;
			GD.Print($"[Splats] manifeste {nom} : {r?.Pieces.Count ?? 0} pièces, {ms:F0} ms");
			return r;
		}

		private static Recette LireManifeste(string nom)
		{
			string chemin = Dossier + nom + ".json";
			if (!FileAccess.FileExists(chemin)) { GD.PushWarning($"[Splats] manifeste absent : {chemin}"); return null; }
			var m = Json.ParseString(FileAccess.GetFileAsString(chemin)).AsGodotDictionary();
			var r = new Recette { Lacets = m["lacets"].AsInt32(), Variantes = m["variantes"].AsInt32() };
			if (m.TryGetValue("inclinaisons_deg", out var inc)) r.Inclinaisons = inc.AsInt32Array();
			if (m.TryGetValue("couches", out var cs)) r.NomsCouches = cs.AsStringArray();
			if (m.TryGetValue("classes", out var cl))
			{
				var tailles = new List<(int, float)>();
				foreach (var v in cl.AsGodotArray())
				{
					var c = v.AsGodotDictionary();
					tailles.Add((Mathf.RoundToInt(c["echelle"].AsSingle() * 100f), c["taille_cm"].AsSingle()));
				}
				tailles.Sort();   // croissantes : Trouver remonte vers la classe au-dessus
				r.Tailles = tailles.ToArray();
			}
			foreach (var v in m["pieces"].AsGodotArray())
			{
				var p = v.AsGodotDictionary();
				int[] rect = p["rect"].AsInt32Array(), att = p["attache"].AsInt32Array();
				int couche = p.TryGetValue("couche", out var c) ? System.Array.IndexOf(r.NomsCouches, c.AsString()) : 0;
				int trou = 0;
				if (p.TryGetValue("trou", out var t))
					trou = p["degre"].AsInt32() + (t.AsString() == "grele" ? 2 : 0);
				int echelle = p.TryGetValue("echelle", out var e) ? Mathf.RoundToInt(e.AsSingle() * 100f) : 100;
				var cle = new Cle(Mathf.RoundToInt(p["palier"].AsSingle() * 2f), echelle, Mathf.Max(couche, 0),
					p["inclinaison_deg"].AsInt32(), p["lacet_deg"].AsInt32(), p["variante"].AsInt32(), trou);
				r.Pieces[cle] = new Brute(p["planche"].AsString(), new Rect2I(rect[0], rect[1], rect[2], rect[3]),
					new Vector2I(att[0], att[1]));
			}
			return r;
		}

		// --- Planches -----------------------------------------------------------------

		private static Planche PlancheDe(string recette, string planche, int p2, Recette r)
		{
			if (_planches.TryGetValue((recette, planche), out var pl)) return pl;
			long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
			string chemin = $"{Dossier}{recette}_{planche}.png";
			var img = LireImage(chemin);
			if (img == null) { _planches[(recette, planche)] = null; return null; }
			pl = new Planche { Palier2 = p2 };
			int w = img.GetWidth(), h = img.GetHeight();
			byte[] src = img.GetData();
			foreach (var (y0, y1) in Bandes(r, planche, h))
			{
				var codes = new byte[w * (y1 - y0) * 4];
				// Texel = (255, 255, code G, 255) là où la pièce est posée, vide ailleurs.
				for (int i = 0, j = y0 * w * 4; i < codes.Length; i += 4, j += 4)
				{
					if (src[j + 3] < 128) continue;
					codes[i] = 255; codes[i + 1] = 255; codes[i + 2] = src[j + 1]; codes[i + 3] = 255;
				}
				var bande = Image.CreateFromData(w, y1 - y0, false, Image.Format.Rgba8, codes);
				pl.Bandes.Add((y0, y1, ImageTexture.CreateFromImage(bande)));
				pl.Octets += codes.Length;
			}
			_planches[(recette, planche)] = pl;
			OctetsCharges += pl.Octets;
			PlanchesChargees++;
			pl.DernierUsage = Engine.GetProcessFrames();
			// RELIQUATS ① : au-delà du budget global, on rend les planches les plus
			// anciennes (jamais celles d'un pinceau des 2 dernières images).
			long trop = BudgetCuisson.Courant - BudgetCuisson.BudgetOctets;
			if (trop > 0) OublierPerimees(trop);
			double ms = System.Diagnostics.Stopwatch.GetElapsedTime(t0).TotalMilliseconds;
			MsChargement += ms;
			GD.Print($"[Splats] {recette}_{planche} {w}×{h} en {pl.Bandes.Count} bande(s), {ms:F0} ms, total {OctetsCharges / 1048576f:F1} Mo");
			return pl;
		}

		/// <summary>Une planche PNG en RGBA8, octets intacts ; null (avec avertissement) si
		/// illisible. Sert aussi au kit des paliers bas (PlantRenderer.KitSplats.cs, ⑤).</summary>
		internal static Image LireImage(string chemin)
		{
			// Octets du fichier (FileAccess, comme le manifeste) puis décodeur PNG de Godot
			// sur le tampon : même décodage que `Image.LoadFromFile`, sans son avertissement
			// « will not work on export » (cf. en-tête, CHARGEMENT).
			var img = new Image();
			byte[] octets = FileAccess.GetFileAsBytes(chemin);
			if (octets.Length == 0 || img.LoadPngFromBuffer(octets) != Error.Ok || img.IsEmpty())
			{
				GD.PushWarning($"[Splats] planche illisible : {chemin}");
				return null;
			}
			if (img.GetFormat() != Image.Format.Rgba8) img.Convert(Image.Format.Rgba8);
			return img;
		}

		// Bandes ≤ HauteurMaxTexture : chaque coupe tombe sur une ligne qu'aucune pièce
		// de la planche ne traverse (la plus basse possible sous la limite).
		private static List<(int, int)> Bandes(Recette r, string planche, int h)
		{
			var res = new List<(int, int)>();
			if (h <= HauteurMaxTexture) { res.Add((0, h)); return res; }
			var rects = new List<Rect2I>();
			foreach (var b in r.Pieces.Values) if (b.Planche == planche) rects.Add(b.Rect);
			int y0 = 0;
			while (y0 < h)
			{
				int y1 = Mathf.Min(h, y0 + HauteurMaxTexture);
				if (y1 < h)
				{
					bool coupe;
					do
					{
						coupe = true;
						foreach (var rc in rects)
							if (rc.Position.Y < y1 && rc.End.Y > y1) { y1 = rc.Position.Y; coupe = false; }
					} while (!coupe && y1 > y0);
					if (y1 <= y0) { GD.PushError($"[Splats] {planche} : pièce plus haute que {HauteurMaxTexture} px"); break; }
				}
				res.Add((y0, y1));
				y0 = y1;
			}
			return res;
		}

		/// <summary>Rend au GPU les planches non servies depuis 2 images, la plus
		/// ancienne d'abord, jusqu'à `octets` (RELIQUATS ①, appelé quand un chargement
		/// fait dépasser le budget de BudgetCuisson). Une planche
		/// lue par un pinceau en cours de rendu n'est jamais rendue (sa texture doit
		/// survivre au rendu de la page). Rechargeable à la demande : on ne perd que du
		/// temps de chargement. Renvoie les octets rendus.</summary>
		internal static long OublierPerimees(long octets)
		{
			ulong seuil = Engine.GetProcessFrames();
			seuil = seuil > 2 ? seuil - 2 : 0;
			var vieilles = new List<((string, string) Cle, ulong Usage, long Octets)>();
			foreach (var (cle, pl) in _planches)
				if (pl != null && pl.DernierUsage < seuil) vieilles.Add((cle, pl.DernierUsage, pl.Octets));
			vieilles.Sort((a, b) => a.Usage.CompareTo(b.Usage));
			long rendu = 0;
			foreach (var (cle, _, o) in vieilles)
			{
				if (rendu >= octets) break;
				// Dispose = rend la texture tout de suite (sans attendre le ramasse-miettes C#).
				foreach (var (_, _, tex) in _planches[cle].Bandes) tex.Dispose();
				_planches.Remove(cle);
				OctetsCharges -= o;
				rendu += o;
			}
			return rendu;
		}


		// Changement de palier : les planches d'un autre palier ne servent plus à rien (les
		// images déjà cuites vivent dans AtlasPages) → on les rend au GPU.
		private static void OublierAutresPaliers(int p2)
		{
			if (p2 == _palierCourant2) return;
			_palierCourant2 = p2;
			var cles = new List<(string, string)>();
			foreach (var (cle, pl) in _planches)
				if (pl != null && pl.Palier2 != p2) cles.Add(cle);
			foreach (var cle in cles)
			{
				OctetsCharges -= _planches[cle].Octets;
				_planches.Remove(cle);
			}
		}
	}
}
