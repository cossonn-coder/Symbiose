// SYMBIOSE — WorldView.BancCleStable.cs (partial de WorldView, sprint HOUPPIER ④)
// BANC VM : couper une branche ne déplace aucune feuille des AUTRES branches. Vrai clic du geste
// tailler, vraie réponse du moteur (donc `_rebuild` et sa réindexation), puis comparaison du
// feuillage avant/après : tout ce qui reste doit déjà avoir été là, au même endroit.
//
//   tools/capture_vm.sh -b houppiers -w 0 -z 2 -c 225,325 -Y AppleTree -n 120 --no-build
//
// Verdict au journal : `[CleStable] AppleTree ×2 : … OK` ou `KO`. Pas un livrable joueur.

using Godot;
using System.Linq;

namespace Symbiose
{
	public partial class WorldView
	{
		private static readonly string CaptureCleStable = ArgCapture("cle-stable");
		private const float CleStableAttenteSec = 4f;

		// Appelé en fin d'AppliquerCapture (caméra posée sur le point visé).
		private void LancerBancCleStable()
		{
			if (CaptureCleStable == null) return;
			GetTree().CreateTimer(CleStableAttenteSec).Timeout += () =>
			{
				// Le pied de cette espèce le plus proche du point visé : le clic doit tomber sur lui.
				var plante = _plantNodes.Values.Where(p => IsInstanceValid(p) && p.Espece == CaptureCleStable)
					.OrderBy(p => p.Position.DistanceSquaredTo(_camera.Position)).FirstOrDefault();
				if (plante == null) { GD.Print($"[CleStable] aucun {CaptureCleStable}."); GetTree().Quit(); return; }
				// Caméra sur lui : hors marge, sa nouvelle structure attendrait (WorldView.Attente.cs).
				_camera.Position = plante.Position;
				CullPlants();
				var avant = plante.EmpreinteFeuillage();
				int segs = plante.NombreSegments;
				_gesteIndex = System.Array.FindIndex(Gestes, g => g.Item1 == "tailler");
				TryAction(plante.MilieuSegmentCanvas(plante.SegmentACouper()), true);   // Maj : la branche entière
				GetTree().CreateTimer(CleStableAttenteSec).Timeout += () =>
				{
					var apres = plante.EmpreinteFeuillage();
					int deplacees = apres.Count(x => !avant.Contains(x));
					bool coupe = plante.NombreSegments < segs;
					GD.Print($"[CleStable] {CaptureCleStable} ×{CurrentZoom} : segments {segs} → {plante.NombreSegments}, "
						+ $"feuillage {avant.Count} → {apres.Count}, {deplacees} déplacés · « {_lastActionMsg} » · "
						+ (coupe && deplacees == 0 ? "OK" : "KO"));
					GetTree().Quit();
				};
			};
		}
	}
}
