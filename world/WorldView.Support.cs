// SYMBIOSE — WorldView.Support.cs (partial de WorldView, sprint grimpantes ⑥)
// Le câblage VUE des supports de grimpe posables : applique le bloc `supports` du
// snapshot (lecture seule, protocole 0.5.18) en plaçant un placeholder procédural
// (SupportRenderer) par support. Même modèle de rendu que les structures compost
// (un nœud chacun dans la couche YSort des objets, reconstruction pleine à chaque
// snapshot : peu nombreux, aucune jauge à fondre) — cf. WorldView.Compost.cs.
//
// Godot est une VUE (Option B) : on ne fait que PROJETER ce que Python a calculé.
// La grimpe elle-même n'a AUCUN code ici — la géométrie des segments (montée le
// long du support ou affalée au sol) vient du snapshot et PlantRenderer la dessine
// (décision A géométrique). Ce partial ne peint que le support inerte.

using Godot;
using System.Collections.Generic;
using GDict = Godot.Collections.Dictionary;

namespace Symbiose
{
	public partial class WorldView : Node2D
	{
		// Supports affichés. On ne garde pas d'index de désignation (les gestes
		// poser_tuteur/treillis/pergola ciblent une POSITION monde, pas un index) —
		// juste les nœuds pour les libérer à la reconstruction.
		private readonly List<SupportRenderer> _supportNodes = new();

		// Applique le bloc `supports` : reconstruction pleine (les anciens nœuds sont
		// libérés, sauf après RebuildWorld qui a déjà vidé _objects ET _supportNodes).
		private void ApplySupports(GDict supports)
		{
			foreach (var n in _supportNodes)
				if (IsInstanceValid(n)) n.QueueFree();
			_supportNodes.Clear();

			foreach (var tileKv in supports)
			{
				string tileId = tileKv.Key.AsString();
				if (!_origins.TryGetValue(tileId, out Vector2 o))
					continue;   // tuile inconnue du init
				foreach (var sv in tileKv.Value.AsGodotArray())
				{
					var st = sv.AsGodotDictionary();
					string kind = st["type"].AsString();
					// Position TUILE-locale (cm) → monde (offset origine) → écran.
					float lx = (float)st["x_cm"].AsDouble();
					float ly = (float)st["y_cm"].AsDouble();
					float height = (float)st["height_cm"].AsDouble();
					var node = new SupportRenderer(kind, height)
					{
						Position = WorldToScreen(o.X + lx, o.Y + ly),
						Name = $"support_{tileId}_{kind}_{_supportNodes.Count}",
					};
					_objects.AddChild(node);
					_supportNodes.Add(node);
				}
			}
		}
	}
}
