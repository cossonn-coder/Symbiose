// SYMBIOSE — PuddleLayer.Mare.cs (sprint SOL NOURRICIER ⑤, eau DA 16 bits MARE VIVANTE ②)
// La MARE lisible en grammaire SNES. On ne crée AUCUNE couche ni aucun champ : on
// CROISE ce que PuddleLayer a déjà lu (bloc `marais` : hystérèse `etat`, et depuis le
// pont 0.6.2 la LAME brute et la GLACE de chaque plot ; bloc `eau_surface`).
//
//   · MARE  = plot marais INSTALLÉ dans l'emprise de l'eau : en eau (lame > seuil de
//     flaque) OU voisin d'un plot en eau. Un plot de bord qui se découvre l'été RESTE
//     donc dans la mare : il passe en vase luisante puis sèche (marnage), au lieu de
//     basculer d'un coup en « terre brune » (défaut vu par Nico au F5 de ⑤).
//     Chaque plot = 4 triangles CODÉS (centre + 4 coins) : la couleur de sommet porte
//     lame / glace / bord (contrat dans `eau_mare.gdshader`), MOYENNÉS aux coins entre
//     les plots qui les partagent → le shader voit un champ CONTINU, le dégradé eau
//     profonde → vase ne suit plus la grille des plots. RIVE de vase (trait littéral)
//     sur les arêtes qui ne touchent pas la mare.
//   · BERGE = plot marécageux (voile de tourbe) hors mare, voisin (8-connexité) d'un
//     plot de mare → terre humide (rampe `vase`), piquée de mousse (sphaigne).
//   · Snapshot 0.6.1 (lame absente) : ancienne règle (installé ET flaque exportée).
//
// 📖 Pédagogie : l'œil reconnaît une mare à trois indices, pas à sa couleur seule :
// (1) l'eau est OPAQUE et plus sombre que le sol ; (2) des reflets en traits
// horizontaux qui scintillent (convention 16 bits de l'eau calme) ; (3) un BORD net
// (rive) qui ferme la forme. (1) et (2) sont dans le shader, (3) ici.
//
// Déterminisme : aucun aléa (moyennes, hash entier du plot pour la mousse) ; tout part
// dans le MÊME lot que la couche (0 draw call de plus). Les arêtes se calculent en
// projetant les coins MONDE du plot → la rive suit la rotation D35.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class PuddleLayer
	{
		// Rive : vase la plus sombre ; berge : vase mouillée + mousse (rampe `vase`).
		private static readonly Color RiveColor = RampesDa.Matieres["vase"][0];
		private static readonly Color BergeColor = RampesDa.Matieres["vase"][1];
		private static readonly Color MousseColor = new Color("5f7a3a");
		private const float BergeAlpha = 0.75f;
		// = SEUIL_FLAQUE du moteur (fields/ecofields/constants.py) : au-dessus, le plot
		// est « en eau » ; il ancre l'emprise de la mare.
		private const float SeuilFlaque = 0.10f;
		// UV des triangles codés (x ≥ 1 → branche « mare » du shader).
		private static readonly Vector2 UvMare = new(2f, 0f);

		private readonly List<Wet> _mare = new();
		private readonly List<Wet> _berge = new();
		private readonly HashSet<(string, int, int)> _installes = new();
		// Plots de mare indexés (moyennes aux coins).
		private readonly Dictionary<(string, int, int), Wet> _mareIdx = new();

		// Voisins partageant chaque coin (ordre NO, NE, SE, SO de Coins), hors soi.
		private static readonly (int, int)[][] VoisinsCoin =
		{
			new[] { (-1, -1), (-1, 0), (0, -1) },
			new[] { (-1, 0), (-1, 1), (0, 1) },
			new[] { (0, 1), (1, 0), (1, 1) },
			new[] { (0, -1), (1, -1), (1, 0) },
		};

		// Après lecture des deux blocs : les plots de mare quittent _flaques/_marais ;
		// un plot marais voisin d'une mare passe de _marais à _berge.
		private void ClasserMare()
		{
			_mareIdx.Clear();
			bool lameExportee = false;
			foreach (var w in _marais) if (w.Lame >= 0f) { lameExportee = true; break; }
			if (lameExportee)
			{
				var inst = new Dictionary<(string, int, int), Wet>();
				foreach (var w in _marais)
					if (w.Lame >= 0f && _installes.Contains((w.TileId, w.R, w.C)))
						inst[(w.TileId, w.R, w.C)] = w;
				foreach (var kv in inst)
					if (kv.Value.Lame > SeuilFlaque || ToucheEau(inst, kv.Value))
						_mareIdx[kv.Key] = kv.Value;
			}
			else
				foreach (var w in _flaques)
					if (_installes.Contains((w.TileId, w.R, w.C)))
					{
						var m = w;
						m.Lame = w.Depth * LameMax;
						_mareIdx[(w.TileId, w.R, w.C)] = m;
					}
			if (_mareIdx.Count == 0) return;
			_flaques.RemoveAll(w => _mareIdx.ContainsKey((w.TileId, w.R, w.C)));
			_marais.RemoveAll(w => _mareIdx.ContainsKey((w.TileId, w.R, w.C)));
			// Le moteur ne gèle que l'EAU (lame > seuil) : un plot découvert a glace 0.
			// Mare prise, il porte pourtant de la vase gelée, pas de l'eau libre → il
			// prend la glace la plus forte de ses voisins de mare (sinon la moyenne aux
			// coins ouvre un faux trou d'eau libre entre la glace et la vase).
			var gelVoisin = new Dictionary<(string, int, int), float>();
			foreach (var kv in _mareIdx)
				if (kv.Value.Lame <= SeuilFlaque) gelVoisin[kv.Key] = GlaceVoisine(kv.Value);
			foreach (var kv in gelVoisin)
			{
				var w = _mareIdx[kv.Key];
				w.Glace = Mathf.Max(w.Glace, kv.Value);
				_mareIdx[kv.Key] = w;
			}
			foreach (var kv in _mareIdx)
			{
				var w = kv.Value;
				w.Voisins = (EstMare(w, -1, 0) ? 1 : 0) | (EstMare(w, 0, 1) ? 2 : 0)
						  | (EstMare(w, 1, 0) ? 4 : 0) | (EstMare(w, 0, -1) ? 8 : 0);
				_mare.Add(w);
			}
			for (int i = _marais.Count - 1; i >= 0; i--)
			{
				var w = _marais[i];
				if (!ToucheMare(w)) continue;
				_berge.Add(w);
				_marais.RemoveAt(i);
			}
		}

		private bool EstMare(Wet w, int dr, int dc) =>
			_mareIdx.ContainsKey((w.TileId, w.R + dr, w.C + dc));

		private bool ToucheMare(Wet w)
		{
			for (int dr = -1; dr <= 1; dr++)
				for (int dc = -1; dc <= 1; dc++)
					if (EstMare(w, dr, dc)) return true;
			return false;
		}

		private float GlaceVoisine(Wet w)
		{
			float g = 0f;
			for (int dr = -1; dr <= 1; dr++)
				for (int dc = -1; dc <= 1; dc++)
					if (_mareIdx.TryGetValue((w.TileId, w.R + dr, w.C + dc), out var v))
						g = Mathf.Max(g, v.Glace);
			return g;
		}

		// Un voisin (8-connexité) installé est EN EAU → ce plot est dans l'emprise.
		private static bool ToucheEau(Dictionary<(string, int, int), Wet> inst, Wet w)
		{
			for (int dr = -1; dr <= 1; dr++)
				for (int dc = -1; dc <= 1; dc++)
					if (inst.TryGetValue((w.TileId, w.R + dr, w.C + dc), out var v)
						&& v.Lame > SeuilFlaque) return true;
			return false;
		}

		// Coins écran du plot, ordre NO, NE, SE, SO en MONDE (x = colonnes, y = lignes),
		// recalés au relief. Arête k = (coin k, coin k+1) touche le voisin de bit 1<<k.
		private static Vector2[] Coins(Wet w)
		{
			float h = WorldView.PlotCm / 2f;
			Vector2 up = new(0f, w.RisePx);
			return new[]
			{
				WorldView.WorldToScreen(w.Cx - h, w.Cy - h) - up,
				WorldView.WorldToScreen(w.Cx + h, w.Cy - h) - up,
				WorldView.WorldToScreen(w.Cx + h, w.Cy + h) - up,
				WorldView.WorldToScreen(w.Cx - h, w.Cy + h) - up,
			};
		}

		// Hash entier du plot (déterministe, stable d'un snapshot à l'autre). PAS
		// string.GetHashCode : en .NET il est randomisé à chaque lancement.
		private static int HashPlot(Wet w)
		{
			int t = 0;
			foreach (char ch in w.TileId) t = t * 31 + ch;
			return (w.R * 73856093) ^ (w.C * 19349663) ^ (t * 83492791);
		}

		// Code d'un sommet (contrat du shader) : R = lame normalisée, G = glace, B = bord.
		private static Color CodeEau(float lame, float glace, float bord) =>
			new(Mathf.Clamp(lame / LameMax, 0f, 1f), Mathf.Clamp(glace, 0f, 1f), bord, 1f);

		// Code du coin k : lame moyenne des 4 plots qui le partagent (la terre compte
		// pour 0 → le bord s'amincit vers la rive), glace moyenne des plots de mare,
		// bord = 1 dès qu'un des 4 n'est pas de la mare.
		private Color CodeCoin(Wet w, int k)
		{
			float lame = Mathf.Max(w.Lame, 0f), glace = w.Glace;
			int nMare = 1;
			bool bord = false;
			foreach (var (dr, dc) in VoisinsCoin[k])
			{
				if (_mareIdx.TryGetValue((w.TileId, w.R + dr, w.C + dc), out var v))
				{
					lame += Mathf.Max(v.Lame, 0f);
					glace += v.Glace;
					nMare++;
				}
				else bord = true;
			}
			return CodeEau(lame / 4f, glace / nMare, bord ? 1f : 0f);
		}

		private void DrawMare(Wet w, Rect2 vis)
		{
			var k = Coins(w);
			Vector2 ctr = (k[0] + k[2]) / 2f;
			if (!vis.HasPoint(ctr)) return;
			// Surface : 4 triangles codés en éventail autour du centre. Le centre d'un
			// plot de rive porte un demi-bord (sinon la glace partielle dessine une
			// croix qui suit la grille au lieu d'un anneau le long de la rive).
			Color cc = CodeEau(Mathf.Max(w.Lame, 0f), w.Glace, w.Voisins == 15 ? 0f : 0.5f);
			var code = new Color[4];
			for (int i = 0; i < 4; i++) code[i] = CodeCoin(w, i);
			for (int i = 0; i < 4; i++)
			{
				int j = (i + 1) % 4;
				_lot.TriangleCode(ctr, cc, k[i], code[i], k[j], code[j], UvMare);
			}
			// Rive : arêtes sans voisin de mare.
			for (int e = 0; e < 4; e++)
				if ((w.Voisins & (1 << e)) == 0)
					_lot.Ligne(k[e], k[(e + 1) % 4], RiveColor, 2f);
		}

		private void DrawBerge(Wet w, Rect2 vis)
		{
			var k = Coins(w);
			Vector2 ctr = (k[0] + k[2]) / 2f;
			if (!vis.HasPoint(ctr)) return;
			Color sol = BergeColor;
			sol.A = BergeAlpha;
			_lot.Polygone(k, sol);
			// Mousse : 3 touffes de 2×1 px internes, placées par hash.
			int hsh = HashPlot(w) & 0x7fffffff;
			float dl = WorldView.TileWPx / 2f, dh = WorldView.TileHPx / 2f;
			for (int i = 0; i < 3; i++)
			{
				float u = ((hsh >> (i * 7)) & 0x7f) / 127f - 0.5f;
				float v = ((hsh >> (i * 7 + 3)) & 0xf) / 15f - 0.5f;
				Vector2 p = ctr + new Vector2(u * dl * 0.8f, v * dh * 0.5f);
				_lot.Ligne(p, p + new Vector2(2f, 0f), MousseColor, 1f);
			}
		}
	}
}
