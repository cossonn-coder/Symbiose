// SYMBIOSE — WorldView.BancClicMur.cs (partial de WorldView, PALETTE & TIROIR ③)
// BANC VM de D118 (c) : « une plante au premier plan contre la maison doit recevoir
// le clic ». Avant de corriger, MESURER : pour chaque morceau de bois DESSINÉ devant
// la maison (le milieu de chaque segment, là où l'on clique vraiment), le test de
// priorité `PointeUnePlante` voit-il une plante ? S'il ne la voit pas, le clic part
// à la maison (le carnet s'ouvre) au lieu d'agir sur la plante.
//
//   tools/capture_vm.sh -b verger_mur -w 0 -z 8 -M -n 60
//
// Journal : `[ClicMur] ×zoom ESPECE : vus/total` par espèce, puis le total. Lecture
// seule : aucun clic n'est envoyé. « Yeux » de l'agent, inactif sans l'argument.

using Godot;
using System.Collections.Generic;

namespace Symbiose
{
	public partial class WorldView
	{
		private static readonly bool CaptureClicMur = ArgCapture("clicmur") == "1";

		// Appelé en fin d'AppliquerCapture.
		private void LancerBancClicMur()
		{
			if (!CaptureClicMur) return;
			GetTree().CreateTimer(4f).Timeout += () =>
			{
				// Cadrer d'abord sur une plante qui a du bois devant la maison : hors champ,
				// un nœud est masqué (CullPlants) et ne compterait pas — à ×8 et ×16 les
				// plantes du mur sont hors de l'écran au cadrage par défaut.
				PlantRenderer cible = null;
				foreach (var node in _plantNodes.Values)
				{
					if (!IsInstanceValid(node)) continue;
					for (int i = 1; i < node.NombreSegments && cible == null; i++)
						if (ClicSurMaison(node.MilieuSegmentCanvas(i))) cible = node;
					if (cible != null) break;
				}
				if (cible != null) { _camera.Position = cible.Position; CullPlants(); }
				int visibles = 0;
				foreach (var node in _plantNodes.Values)
					if (IsInstanceValid(node) && node.Visible) visibles++;
				GD.Print($"[ClicMur] ×{CurrentZoom} cadré sur {(cible == null ? "rien" : cible.Espece)} · {visibles} plantes visibles");
				var parEspece = new SortedDictionary<string, (int Vus, int Total)>();
				int vus = 0, total = 0;
				foreach (var node in _plantNodes.Values)
				{
					if (!IsInstanceValid(node) || !node.Visible) continue;
					for (int i = 1; i < node.NombreSegments; i++)
					{
						Vector2 m = node.MilieuSegmentCanvas(i);
						if (!ClicSurMaison(m)) continue;          // pas devant la maison
						bool vu = PointeUnePlante(m);
						parEspece.TryGetValue(node.Espece, out var t);
						parEspece[node.Espece] = (t.Vus + (vu ? 1 : 0), t.Total + 1);
						total++;
						if (vu) vus++;
					}
				}
				foreach (var (espece, t) in parEspece)
					GD.Print($"[ClicMur] ×{CurrentZoom} {espece} : {t.Vus}/{t.Total}");
				GD.Print($"[ClicMur] ×{CurrentZoom} TOTAL : {vus}/{total} milieux de segments devant la maison vus par PointeUnePlante");
			};
		}
	}
}
