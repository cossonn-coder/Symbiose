// SYMBIOSE — PlantRenderer.KitSplats.cs (partial, sprint PRÉCUISSON SPLATS ⑤)
// Le KIT DES PALIERS BAS (×0,5 · ×1 · ×2) tiré des pièces précuites en splats (D4) :
// touffes `touffe_<forme>` du ② et fleurons `fleuron` du ③ (assets/splats/, planche
// `kit` de chaque recette), au lieu du générateur à la règle de PlantRenderer.Kit.cs.
//
//  • MÊME FORMAT que l'atlas généré (Rg8) : R = niveau (2 ombre · 3 base · 4 lumière,
//    5 cœur de fleuron), G = code de palette indexée `128 | ton << 4 | orientation`.
//    Les deux canaux sont COPIÉS tels quels depuis la planche (aucun recalcul) ;
//    l'assemblage (Assemblee.cs) et la planche du kit ne voient pas la différence.
//  • MÊMES CLÉS : (forme, taille 3/5/7/9 px, variante 0-2) pour les touffes ;
//    Point/Bouton/Etoile = fleuron de 1/2/3 px, variante 0 (l'API n'en a pas).
//  • ANCRAGE : l'assemblage CENTRE une pièce du kit sur sa position. Une pièce splat,
//    elle, a un point d'ATTACHE (le bout du rameau d'où partent les feuilles, en bas
//    pour les rubans de la lancéolée). On range donc chaque pièce dans une case de
//    côté impair dont le CENTRE est l'attache (marges vides) : centrer la case = poser
//    l'attache, sans toucher au code de l'assemblage.
//  • INTERRUPTEUR : le même que les paliers hauts (Maj+F11, SYMBIOSE_SPLATS=0) ; à la
//    bascule, le kit est oublié puis reconstruit (OublierKit). Recette ou planche
//    absente → avertissement et retour au kit généré, entier.
//
// 📖 Pédagogie : c'est un « adaptateur » au sens des patrons de conception — la
// nouvelle source de données est remise dans la forme exacte qu'attend l'ancien
// consommateur. En embarqué : un pilote qui présente un nouveau capteur avec le même
// registre que l'ancien, pour ne pas réécrire l'application.
//
// Déterministe (fichiers versionnés, aucune graine), purement visuel : golden non concerné.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PlantRenderer
	{
		// Une pièce lue dans une planche : niveaux et codes (rangée par rangée), taille, attache.
		private readonly record struct PieceKit(byte[] Niv, byte[] Codes, int L, int H, int Ax, int Ay);

		// Pièces lues une fois (les fichiers ne changent pas en cours de partie) ; null = pas
		// encore lues, vide = lecture ratée (repli définitif sur le kit généré).
		private static Dictionary<(LeafShape, int, int), PieceKit> _touffesSplat;
		private static PieceKit[] _fleuronsSplat;

		/// <summary>Oublie le kit et les gerbes (atlas, masques, codes) : la prochaine demande les
		/// reconstruit depuis la source choisie par l'interrupteur des splats.</summary>
		private static void OublierKit()
		{
			_kitNiveaux = null;
			_kitTouffes.Clear();
			_kitMasques = null;
			_kitCodes = null;
			_gerbesNiveaux = null;
			_gerbesCodes = null;
			_gerbesMasques = null;
		}

		/// <summary>Atlas du kit depuis les planches splats ; false (rien de posé) s'il manque
		/// une recette, une planche ou une pièce attendue.</summary>
		private static bool ConstruireKitSplats()
		{
			if (!ChargerKitSplats()) return false;
			var formes = (LeafShape[])System.Enum.GetValues(typeof(LeafShape));
			var rangees = new List<List<(object Cle, PieceKit P)>>();
			foreach (var forme in formes)
			{
				var rangee = new List<(object, PieceKit)>();
				foreach (int t in KitTailles)
					for (int v = 0; v < KitVariantes; v++)
						rangee.Add(((forme, t, v), _touffesSplat[(forme, t, v)]));
				rangees.Add(rangee);
			}
			var derniere = new List<(object, PieceKit)>();
			for (int f = 0; f < _fleuronsSplat.Length; f++) derniere.Add((f, _fleuronsSplat[f]));
			rangees.Add(derniere);
			RangerKitSplats(rangees);
			GD.Print($"[Kit] source splats : atlas {_kitNiveaux.GetWidth()}×{_kitNiveaux.GetHeight()} px, rangée {_kitPasRangee} px.");
			return true;
		}

		/// <summary>Touffe d'une GERBE d'arbre (Gerbes.cs) : carré de côté impair, attache au
		/// centre — la pièce splat si l'interrupteur est allumé, sinon la touffe générée.</summary>
		private static (byte[] Niv, byte[] Codes) TouffeGerbe(LeafShape forme, int taille, int v)
		{
			if (!SplatsActifs || !ChargerKitSplats()) return PeindreTouffe(forme, taille, v);
			var p = _touffesSplat[(forme, taille, v)];
			var c = CaseKit(p);
			int n = Mathf.Max(c.X, c.Y), ox = n / 2 - p.Ax, oy = n / 2 - p.Ay;
			var niv = new byte[n * n];
			var codes = new byte[n * n];
			for (int y = 0; y < p.H; y++)
				for (int x = 0; x < p.L; x++)
				{
					int s = y * p.L + x, d = (oy + y) * n + ox + x;
					niv[d] = p.Niv[s]; codes[d] = p.Codes[s];
				}
			return (niv, codes);
		}

		// Lit toutes les pièces du kit (6 touffes + fleurons), une fois. False si une manque.
		private static bool ChargerKitSplats()
		{
			if (_touffesSplat != null) return _touffesSplat.Count > 0;
			_touffesSplat = new();
			var touffes = new Dictionary<(LeafShape, int, int), PieceKit>();
			foreach (var forme in (LeafShape[])System.Enum.GetValues(typeof(LeafShape)))
			{
				var pieces = LirePiecesKit($"touffe_{forme.ToString().ToLowerInvariant()}");
				if (pieces == null) return false;
				foreach (int t in KitTailles)
					for (int v = 0; v < KitVariantes; v++)
					{
						if (!pieces.TryGetValue((t, v), out var p)) return Manque($"touffe_{forme} {t} px v{v}");
						touffes[(forme, t, v)] = p;
					}
			}
			var fleurons = LirePiecesKit("fleuron");
			if (fleurons == null) return false;
			_fleuronsSplat = new PieceKit[_kitFleurons.Length];
			for (int f = 0; f < _fleuronsSplat.Length; f++)
				if (!fleurons.TryGetValue((f + 1, 0), out _fleuronsSplat[f])) return Manque($"fleuron {f + 1} px");
			_touffesSplat = touffes;
			return true;
		}

		private static bool Manque(string quoi)
		{
			GD.PushWarning($"[Kit] pièce splat absente ({quoi}) : retour au kit généré.");
			return false;
		}

		// Rangée = une forme (puis les fleurons) ; cases côte à côte, 1 px de jour ; pas de
		// rangée commun = plus haute case + 1. Case de côté impair, attache au centre.
		private static void RangerKitSplats(List<List<(object Cle, PieceKit P)>> rangees)
		{
			int largeur = 0, pas = 0;
			foreach (var rangee in rangees)
			{
				int x = 0;
				foreach (var (_, p) in rangee) { x += CaseKit(p).X + 1; pas = Mathf.Max(pas, CaseKit(p).Y + 1); }
				largeur = Mathf.Max(largeur, x);
			}
			var rg = new byte[largeur * pas * rangees.Count * 2];
			for (int r = 0; r < rangees.Count; r++)
			{
				int x = 0;
				foreach (var (cle, p) in rangees[r])
				{
					var c = CaseKit(p);
					var rect = new Rect2I(x, r * pas, c.X, c.Y);
					int ox = rect.Position.X + c.X / 2 - p.Ax, oy = rect.Position.Y + c.Y / 2 - p.Ay;
					for (int y = 0; y < p.H; y++)
						for (int xx = 0; xx < p.L; xx++)
						{
							int s = y * p.L + xx, d = ((oy + y) * largeur + ox + xx) * 2;
							if (p.Codes[s] == 0) continue;
							rg[d] = p.Niv[s]; rg[d + 1] = p.Codes[s];
						}
					if (cle is int f) _kitFleurons[f] = rect;
					else _kitTouffes[((LeafShape, int, int))cle] = rect;
					x += c.X + 1;
				}
			}
			_kitPasRangee = pas;
			_kitNiveaux = Image.CreateFromData(largeur, pas * rangees.Count, false, Image.Format.Rg8, rg);
		}

		// Côté (impair) de la case qui centre l'attache : 2 × la plus grande distance attache → bord + 1.
		private static Vector2I CaseKit(PieceKit p) =>
			new(2 * Mathf.Max(p.Ax, p.L - 1 - p.Ax) + 1, 2 * Mathf.Max(p.Ay, p.H - 1 - p.Ay) + 1);

		// Pièces d'une recette du kit, par (taille_px, variante). Les couches (pétales | cœur
		// du fleuron) sont fondues dans UNE pièce : le cœur prend le niveau KitCoeur, comme
		// l'étoile du kit généré (sa 2ᵉ palette). Pièce vide (couche effacée) = 1 px vide.
		private static Dictionary<(int, int), PieceKit> LirePiecesKit(string recette)
		{
			string chemin = SplatPlanches.Dossier + recette + ".json";
			if (!FileAccess.FileExists(chemin)) { GD.PushWarning($"[Kit] manifeste absent : {chemin}"); return null; }
			var m = Json.ParseString(FileAccess.GetFileAsString(chemin)).AsGodotDictionary();
			var img = SplatPlanches.LireImage($"{SplatPlanches.Dossier}{recette}_kit.png");
			if (img == null) return null;
			int w = img.GetWidth();
			byte[] src = img.GetData();
			var brutes = new Dictionary<(int, int), List<(Rect2I R, Vector2I A, bool Coeur)>>();
			foreach (var v in m["pieces"].AsGodotArray())
			{
				var p = v.AsGodotDictionary();
				int[] rc = p["rect"].AsInt32Array(), at = p["attache"].AsInt32Array();
				bool coeur = p.TryGetValue("couche", out var c) && c.AsString() == "coeur";
				var cle = (p["taille_px"].AsInt32(), p["variante"].AsInt32());
				if (!brutes.TryGetValue(cle, out var liste)) brutes[cle] = liste = new();
				liste.Add((new Rect2I(rc[0], rc[1], rc[2], rc[3]), new Vector2I(at[0], at[1]), coeur));
			}
			var res = new Dictionary<(int, int), PieceKit>();
			foreach (var (cle, liste) in brutes) res[cle] = FondreCouches(liste, src, w);
			return res;
		}

		// Toutes les couches d'une pièce partagent l'attache (③) : on les recale sur elle dans
		// la boîte qui les contient toutes, pétales d'abord, cœur par-dessus.
		private static PieceKit FondreCouches(List<(Rect2I R, Vector2I A, bool Coeur)> couches, byte[] src, int w)
		{
			int x0 = 0, y0 = 0, x1 = 1, y1 = 1;   // repère de l'attache ; une case vide par défaut
			bool premier = true;
			foreach (var (r, a, _) in couches)
			{
				if (r.Size.X <= 0 || r.Size.Y <= 0) continue;
				int gx = -a.X, gy = -a.Y;
				if (premier) { x0 = gx; y0 = gy; x1 = gx + r.Size.X; y1 = gy + r.Size.Y; premier = false; }
				else { x0 = Mathf.Min(x0, gx); y0 = Mathf.Min(y0, gy); x1 = Mathf.Max(x1, gx + r.Size.X); y1 = Mathf.Max(y1, gy + r.Size.Y); }
			}
			int l = x1 - x0, h = y1 - y0;
			var niv = new byte[l * h];
			var codes = new byte[l * h];
			couches.Sort((p, q) => p.Coeur.CompareTo(q.Coeur));
			bool aCoeur = false, coeurPose = false;
			foreach (var (r, a, coeur) in couches)
			{
				aCoeur |= coeur;
				for (int y = 0; y < r.Size.Y; y++)
					for (int x = 0; x < r.Size.X; x++)
					{
						int s = ((r.Position.Y + y) * w + r.Position.X + x) * 4;
						if (src[s + 3] < 128) continue;
						int d = (y - a.Y - y0) * l + (x - a.X - x0);
						niv[d] = coeur ? KitCoeur : src[s];
						codes[d] = src[s + 1];
						coeurPose |= coeur;
					}
			}
			// RELIQUATS ④ : un fleuron de 2 px a un cœur sous le pixel (couche vide à la cuisson) —
			// on force le pixel de l'attache (le centre de la fleur), sinon le cœur jaune disparaît.
			// À 1 px, le pixel unique garde la teinte des pétales (comme l'ancien Fleuron.Point).
			int centre = -y0 * l - x0;
			if (aCoeur && !coeurPose && l * h >= 4 && centre >= 0 && centre < niv.Length && niv[centre] != KitVide)
				niv[centre] = KitCoeur;
			return new PieceKit(niv, codes, l, h, -x0, -y0);
		}
	}
}
