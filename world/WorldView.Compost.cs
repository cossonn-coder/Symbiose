// SYMBIOSE — WorldView.Compost.cs (partial de WorldView, vue 03·C/D)
// Le câblage VUE de la décompo·compost (⑤) : applique les blocs `litiere` et
// `structures` du snapshot (lecture seule, protocole 0.3.7/0.3.5), et résout la
// désignation des 6 gestes compost pour TryAction (Actions.cs). La logique
// métier (coûts, cohérence, effet) reste à Python — ici on ne fait que PROJETER
// et DÉSIGNER, comme pour les autres gestes (Godot est « bête »).
//
// 📖 Pédagogie — deux modèles de rendu côte à côte (cf. en-têtes des nœuds) :
//  · LITIÈRE = un layer batché (LitterLayer), inerte, re-projeté au _Draw ;
//  · STRUCTURES = un nœud chacune (CompostStructure) dans la couche YSort des
//    objets, pour s'occulter en profondeur avec les plantes. Peu nombreuses →
//    reconstruction pleine à chaque snapshot (la jauge change, pas de fondu à
//    tenir) ; trivial, comme reconstruire le sol à la rotation.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Litière au sol (③·B) : layer batché, enfant direct de WorldView (survit
		// à RebuildWorld, il se re-projette seul). ZIndex 1 = au-dessus du sol (0),
		// sous la vie macro (5) et les plantes (10).
		private LitterLayer _litterLayer;

		// Structures posées affichées (③·C). On garde l'INDEX dans la liste de la
		// tuile (= `target.structure` attendu par le serveur, qui indexe
		// eco.structures de CETTE tuile) pour la désignation des gestes (③·D).
		private readonly List<(string Tile, int R, int C, string Kind,
							   int Index, CompostStructure Node)> _structs = new();

		// Crée le layer litière (appelé une fois en _Ready, avant le 1er snapshot).
		private void BuildLitterLayer()
		{
			_litterLayer = new LitterLayer { Name = "Litter", ZIndex = 1 };
			AddWorld(_litterLayer);
		}

		// Applique le bloc `litiere` (lecture tolérante : un snapshot pré-0.3.7
		// n'a pas la clé → pas de litière dessinée, jamais de crash).
		private void ApplyLitiere(GDict litiere) =>
			_litterLayer?.SetLitiere(litiere, _origins);

		// Applique le bloc `structures` : reconstruction pleine. Les anciens nœuds
		// sont libérés (sauf après RebuildWorld, qui a déjà vidé _objects ET
		// _structs → rien à libérer, on recrée seulement).
		private void ApplyStructures(GDict structures)
		{
			foreach (var s in _structs)
				if (IsInstanceValid(s.Node)) s.Node.QueueFree();
			_structs.Clear();

			foreach (var tileKv in structures)
			{
				string tileId = tileKv.Key.AsString();
				if (!_origins.TryGetValue(tileId, out Vector2 o))
					continue;   // tuile inconnue du init
				int idx = 0;
				foreach (var sv in tileKv.Value.AsGodotArray())
				{
					var st = sv.AsGodotDictionary();
					string kind = st["kind"].AsString();
					var plot = st["plot"].AsGodotArray();
					int r = plot[0].AsInt32(), c = plot[1].AsInt32();
					float mur = (float)st["compost_mur"].AsDouble();
					// `contenu` (0.3.8) : masse brute en cours de maturation. Absente
					// d'un snapshot pré-0.3.8 → 0 (lecture tolérante). Le remplissage
					// visuel = contenu + compost_mur (se remplit au compostage).
					float contenu = st.ContainsKey("contenu")
						? (float)st["contenu"].AsDouble() : 0f;
					// Ruche (⑥, 0.4.0) : essaim [0,1] + miel [0, MIEL_MAX]. Absents
					// d'un snapshot pré-0.4.0 ou d'un bac/pile → 0 (lecture tolérante).
					float essaim = st.ContainsKey("essaim")
						? (float)st["essaim"].AsDouble() : 0f;
					float miel = st.ContainsKey("miel")
						? (float)st["miel"].AsDouble() : 0f;
					float cx = o.X + (c + 0.5f) * PlotCm;
					float cy = o.Y + (r + 0.5f) * PlotCm;
					var node = new CompostStructure(kind, mur, contenu, essaim, miel)
					{
						Position = WorldToScreen(cx, cy),
						Name = $"struct_{tileId}_{r}_{c}_{kind}",
					};
					_objects.AddChild(node);
					_structs.Add((tileId, r, c, kind, idx, node));
					idx++;
				}
			}
		}

		/// <summary>
		/// Index (dans sa tuile) de la structure du plot (tile,r,c) qui CONVIENT
		/// au geste, ou -1 si aucune. Cohérence kind/geste résolue ICI pour un
		/// message clair côté vue (composter→bac, empiler→pile) ; retourner et
		/// epandre acceptent les deux → première structure du plot. Le serveur
		/// reste juge en dernier ressort (il refusera et le message sera relayé).
		/// </summary>
		private int FindStructureIndex(string verb, string tile, int r, int c)
		{
			int fallback = -1;
			foreach (var s in _structs)
			{
				if (s.Tile != tile || s.R != r || s.C != c) continue;
				if (verb == "composter" && s.Kind != "bac") continue;
				if (verb == "empiler_bois" && s.Kind != "pile") continue;
				return s.Index;             // structure adaptée trouvée
			}
			// retourner/epandre : n'importe quelle structure du plot fait l'affaire.
			if (verb == "retourner" || verb == "epandre")
				foreach (var s in _structs)
					if (s.Tile == tile && s.R == r && s.C == c)
						return s.Index;
			return fallback;
		}

		/// <summary>
		/// Index (dans sa tuile) de la structure du `kind` voulu la PLUS PROCHE du
		/// plot (tile,r,c) de litière cliqué, ou -1 si la tuile n'en porte aucune.
		/// Sert composter/empiler (retour F5) : on clique la litière au sol, la vue
		/// l'achemine vers le bac/pile le plus proche. Distance = Manhattan en plots
		/// (déterministe, premier index gagne à égalité). Le moteur composte la
		/// litière du plot (r,c) vers cette structure, où qu'elle soit dans la tuile.
		/// </summary>
		private int FindNearestStructure(string kind, string tile, int r, int c)
		{
			int best = -1, bestDist = int.MaxValue;
			foreach (var s in _structs)
			{
				if (s.Tile != tile || s.Kind != kind) continue;
				int d = Mathf.Abs(s.R - r) + Mathf.Abs(s.C - c);
				if (d < bestDist) { bestDist = d; best = s.Index; }
			}
			return best;
		}
	}
}
