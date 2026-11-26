// SYMBIOSE — DecorLayer.Hauts.cs (sprint LISIÈRE & CHARGEMENT ③, décision L2)
// Partial de DecorLayer : la lisière en PIXEL NATIF aux paliers ×8, ×16, ×32.
//
// Au-delà de ×4 le décor garde la maille ×4 (sa géométrie est en px canvas, la Camera2D
// l'agrandit) ; seule sa TEXTURE change. Pour le palier ×(4k), un atlas k fois plus fin
// (k = 2, 4, 8) aux MÊMES UV normalisées : chaque case de l'atlas ×4 (x, y, w, h) devient
// la case (kx, ky, kw, kh). Une pièce de w texels posée sur w/4 px canvas en reçoit donc
// k·w → un texel par pixel d'écran au palier réel.
//
// Ce que porte l'atlas k :
//  1. d'abord l'atlas ×4 AGRANDI k×k (plus proche voisin) : texels-codes des aplats (une
//     couleur unie ne gagne rien à être plus fine) et repli de toute pièce sans version fine ;
//  2. par-dessus, les pièces du kit cuites k fois plus grandes (`<recette>_hauts`, planche
//     `x<4k>`, tools/splat/cuire.js --echelles 2,4,8), seulement si les splats sont allumés ;
//  3. les bandes d'écorce du palier ×(4k) (BandesCuites, cuites en S2) rééchantillonnées sur la
//     case agrandie de la bande ×4 (la bande est une période entière : seule la proportion
//     compte, les tailles cuites ne sont pas exactement k fois celles de ×4).
//
// 📖 Pédagogie (analogie embarqué) : c'est un jeu de polices bitmap par taille d'écran — les
// mêmes codes de caractères (les UV), un glyphe dessiné pour chaque taille au lieu d'un
// glyphe 8×8 grossi. La maille (le texte) ne change pas, on change de ROM de glyphes.
//
// Mémoire : un seul atlas haut vit à la fois (celui du palier affiché) ; les autres sont
// rendus au GPU (« non affichés : libérables », conception §3.3), comptés dans BudgetCuisson.
// L'image CPU est jetée après l'envoi : resynchroniser (texels-codes neufs, LUT vidée,
// Maj+F11) = reconstruire. Déterministe (fichiers versionnés), purement visuel : golden non concerné.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class DecorLayer : Node2D
	{
		// Un atlas haut construit : sa texture et l'état de l'atlas ×4 qu'il recopie.
		private sealed class AtlasHaut
		{
			public int K;
			public ImageTexture Tex;
			public int Gen, Swatches;
			public bool Splats;
			public long Octets;
		}

		private static AtlasHaut _haut;                       // l'atlas haut vivant (un seul)
		private static readonly List<ImageTexture> _aRendre = new();   // libérés à l'image suivante
		// Pièces fines lues une fois par k : null = pas lues ; vide = lecture ratée (repli agrandi).
		private static readonly Dictionary<int, Dictionary<(Piece, int, int), byte[]>> _kitHaut = new();
		private Texture2D _texAffichee;                       // texture de la maille affichée

		// Construction EN TÂCHE DE FOND (mesuré : ~0,75 s pour ×32 sur le fil principal [VM chargée
		// ~10, n=1] → un à-coup neuf à chaque arrivée au palier). La demande (k et état de l'atlas ×4
		// recopié) est préparée sur le fil principal (lectures Godot : planches, bandes, palette) ;
		// seul le travail d'octets (agrandir, poser) part en Task.Run. En attendant, la maille garde
		// l'atlas ×4 grossi par la caméra — l'image d'avant ③ —, puis permute dès que c'est prêt.
		private sealed class Demande
		{
			public AtlasHaut A;
			public int W, H, Fines, Bandes;
			public ulong T0, PrepUs;
			public System.Threading.Tasks.Task<byte[]> Tache;
		}
		private static Demande _demande;

		/// <summary>Octets GPU de l'atlas haut vivant (BudgetCuisson).</summary>
		internal static long OctetsHauts => _haut?.Octets ?? 0;

		/// <summary>Une construction d'atlas haut vient de finir (_Process : redessiner).</summary>
		private static bool HautPret => _demande != null && _demande.Tache.IsCompleted;

		/// <summary>Texture à poser sur la maille `m` au palier courant : l'atlas ×4 jusqu'à
		/// ×4, l'atlas haut du palier au-delà dès qu'il est prêt (construit en tâche de fond).</summary>
		private static Texture2D TextureDecor(Maille m)
		{
			Texture2D kit = KitTexture;
			int k = Mathf.RoundToInt(WorldView.CurrentZoom / MaxZoom);
			if (k < 2) { Rendre(); _demande = null; return kit; }
			if (Valide(_haut, k, m)) return _haut.Tex;
			Rendre();
			if (_demande == null || !Valide(_demande.A, k, m)) _demande = Demander(k);
			if (!_demande.Tache.IsCompleted) return kit;   // l'image d'avant, le temps de la tâche
			_haut = Terminer(_demande);
			_demande = null;
			return _haut.Tex;
		}

		private static bool Valide(AtlasHaut a, int k, Maille m) =>
			a != null && a.K == k && a.Gen == PaletteIndexee.Generation && a.Swatches >= m.Swatches
			&& a.Splats == PlantRenderer.SplatsActifs;

		// L'atlas haut vivant part à l'image suivante (son ancienne maille peut encore le citer).
		private static void Rendre()
		{
			if (_haut == null) return;
			_aRendre.Add(_haut.Tex);
			_haut = null;
		}

		/// <summary>Chaque image (_Process) : libère les atlas remplacés à l'image d'avant.</summary>
		private static void LibererHauts()
		{
			foreach (var t in _aRendre) t.Dispose();
			_aRendre.Clear();
		}

		// Fil principal : tout ce qui lit Godot (atlas ×4, planches fines, bandes, palette).
		private static Demande Demander(int k)
		{
			var d = new Demande { T0 = Time.GetTicksUsec(), A = new AtlasHaut { K = k, Gen = PaletteIndexee.Generation,
				Swatches = _swatches.Count, Splats = PlantRenderer.SplatsActifs } };
			int w4 = _kitImg.GetWidth(), h4 = _kitImg.GetHeight();
			d.W = w4 * k; d.H = h4 * k;
			var poses = new List<(Rect2I dst, byte[] codes, Vector2I s, int id, int classe)>();
			var fin = d.A.Splats ? KitHaut(k) : null;
			if (fin != null)
				for (int t = 0; t < TeintesBase.Length; t++)
				{
					long src = SourceTeinte(t);
					int id = IdSource(src), classe = (int)(src >> DecalageClasse & 3);
					foreach (var (cle, codes) in fin)
					{
						Rect2I r = _kitRects[IndexKit(t, (int)cle.Item1, cle.Item2, cle.Item3)];
						poses.Add((new Rect2I(r.Position * k, r.Size * k), codes, r.Size * k, id, classe));
					}
				}
			d.Fines = poses.Count;
			foreach (var (r, _, src) in _codesEcorces)
				if (BandeHaute(r, k, out byte[] codes, out Vector2I s))
					poses.Add((new Rect2I(r.Position * k, r.Size * k), codes, s, IdSource(src), (int)(src >> DecalageClasse & 3)));
			d.Bandes = poses.Count - d.Fines;
			byte[] src4 = _kitImg.GetData();
			int w = d.W;
			d.PrepUs = Time.GetTicksUsec() - d.T0;
			d.Tache = System.Threading.Tasks.Task.Run(() =>
			{
				byte[] buf = Agrandir(src4, w4, h4, k);
				foreach (var (dst, codes, s, id, classe) in poses) Poser(buf, w, dst, codes, s, id, classe);
				return buf;
			});
			return d;
		}

		// Fil principal : l'image et son envoi au GPU.
		private static AtlasHaut Terminer(Demande d)
		{
			ulong t1 = Time.GetTicksUsec();
			var img = Image.CreateFromData(d.W, d.H, false, Image.Format.Rgba8, d.Tache.Result);
			d.A.Tex = ImageTexture.CreateFromImage(img);
			d.A.Octets = (long)d.W * d.H * 4;
			GD.Print($"[DecorLayer] atlas ×{4 * d.A.K} : {d.W}×{d.H}, {d.A.Octets / 1048576.0:F1} Mo, {d.Fines} pièces fines,"
				   + $" {d.Bandes} bandes, préparation {d.PrepUs / 1000.0:F0} ms + envoi {(Time.GetTicksUsec() - t1) / 1000.0:F0} ms"
				   + $" (fil principal), prêt en {(t1 - d.T0) / 1000.0:F0} ms"
				   + " (tâche de fond)");
			return d.A;
		}

		// L'atlas ×4 agrandi k×k au plus proche voisin : une rangée agrandie, recopiée k fois.
		private static byte[] Agrandir(byte[] src, int w4, int h4, int k)
		{
			int w = w4 * k;
			var dst = new byte[w * h4 * k * 4];
			var rang = new byte[w * 4];
			for (int y = 0; y < h4; y++)
			{
				for (int x = 0; x < w4; x++)
					for (int r = 0; r < k; r++)
						System.Buffer.BlockCopy(src, (y * w4 + x) * 4, rang, ((x * k + r) * 4), 4);
				for (int r = 0; r < k; r++)
					System.Buffer.BlockCopy(rang, 0, dst, (y * k + r) * w * 4, w * 4);
			}
			return dst;
		}

		// Remplace la case `dst` par les codes `codes` (taille `s`, rééchantillonnés au plus
		// proche sur la case s'ils n'en ont pas la taille) ; code 0 = transparent.
		private static void Poser(byte[] buf, int w, Rect2I dst, byte[] codes, Vector2I s, int id, int classe)
		{
			byte r = (byte)(id & 255), g = (byte)((id >> 8) | classe << 6);
			for (int py = 0; py < dst.Size.Y; py++)
			{
				int sy = py * s.Y / dst.Size.Y;
				for (int px = 0; px < dst.Size.X; px++)
				{
					byte b = codes[sy * s.X + px * s.X / dst.Size.X];
					int i = ((dst.Position.Y + py) * w + dst.Position.X + px) * 4;
					buf[i] = b == 0 ? (byte)0 : r;
					buf[i + 1] = b == 0 ? (byte)0 : g;
					buf[i + 2] = b;
					buf[i + 3] = b == 0 ? (byte)0 : (byte)255;
				}
			}
		}

		// Bande d'écorce du palier ×(4k) dont la bande ×4 occupe la case `r4` de l'atlas. Gardée
		// par (case, k) : relire la planche ×32 d'écorces coûte au fil principal, une fois suffit.
		private static readonly Dictionary<(Rect2I, int), (byte[] codes, Vector2I s)> _bandesHautes = new();
		private static bool BandeHaute(Rect2I r4, int k, out byte[] codes, out Vector2I s)
		{
			codes = null; s = default;
			if (_bandesHautes.TryGetValue((r4, k), out var deja)) { (codes, s) = deja; return codes != null; }
			foreach (var ((bois, age), b) in _bandesDecor)
				if (b.Rect == r4 && Ecorces.CodesBruts(bois, age, 4 * k, out codes, out s, out _, out _)) break;
			_bandesHautes[(r4, k)] = (codes, s);
			return codes != null;
		}

		// Pièces du kit cuites pour l'atlas k (clé : forme, index de taille, variante), à la
		// taille de leur case agrandie. Forme par forme : une recette `_hauts` absente ou
		// incomplète laisse CETTE forme agrandie (avertissement), les autres restent fines.
		private static Dictionary<(Piece, int, int), byte[]> KitHaut(int k)
		{
			if (_kitHaut.TryGetValue(k, out var deja)) return deja.Count > 0 ? deja : null;
			var tout = new Dictionary<(Piece, int, int), byte[]>();
			_kitHaut[k] = tout;
			string planche = "x" + 4 * k;
			for (int f = 0; f < NbPieces; f++)
			{
				var pieces = LirePlancheLisiere(RecettesLisiere[f] + "_hauts", (Piece)f, planche);
				if (pieces == null) continue;   // avertissement déjà écrit : forme agrandie
				var forme = new Dictionary<(Piece, int, int), byte[]>();
				for (int i = 0; i < Tailles[f].Length && forme != null; i++)
					for (int v = 0; v < Variantes; v++)
					{
						Vector2I s = Tailles[f][i] * k;
						if (!pieces.TryGetValue((s.X, v), out var p))
						{
							GD.PushWarning($"[DecorLayer] pièce fine absente ({RecettesLisiere[f]}_hauts {s.X} px v{v}) : forme agrandie à ×{4 * k}.");
							forme = null;
							break;
						}
						forme[((Piece)f, i, v)] = Caser(p, s.X, s.Y);
					}
				if (forme != null) foreach (var (c, p) in forme) tout[c] = p;
			}
			return tout.Count > 0 ? tout : null;
		}
	}
}
