// SYMBIOSE — WorldView.BancVivant.cs (partial de WorldView, INFO-BULLE DU VIVANT ③)
// BANC VM des captures de l'info-bulle d'une BÊTE ou d'un CARPOPHORE (bilan ③) :
// pose ×4 sur l'entrée la plus proche du point visé, souris dessus, recadrage PNG.
// « Yeux » de l'agent sur la VM sans écran — pas un livrable joueur. Lancé par
// sprints/…/sprint_infobulle_vivant/mesures/capture_vivant.sh.
//
// Arguments (après `--`) :
//   --capture-vivant=bete                 la bête (MacroLife, sinon butineur) la
//                                         plus proche de --capture-centre
//   --capture-vivant=carpophore[,b|r|h]   le carpophore le plus proche (de ce rôle)
//   --capture-vivant-png=<chemin>         PNG 640×400 autour de la souris
// Se combine avec --capture-palier3=1 (bête nommée) et --capture-technique=1.
//
// Carpophore SYNTHÉTIQUE : si le snapshot n'en porte aucun du rôle demandé (cas
// des premières années — mycélium lent, cf. 00_etat §Mesures), le banc en pose UN
// dans la couche (rôle demandé, densité 0,80 pour b/r, 0,40 pour h), au plot (2,2)
// de la 1ʳᵉ tuile. Il ne teste que la LIGNE d'info-bulle, jamais le moteur — et le
// log le dit (« synthétique »).

using Godot;

namespace Symbiose
{
	public partial class WorldView
	{
		private static readonly string CaptureVivant = ArgCapture("vivant");
		private static readonly string CaptureVivantPng = ArgCapture("vivant-png");
		private const float VivantAttenteSec = 5f;   // snapshot appliqué, fondus finis

		// Appelé en fin d'AppliquerCapture (caméra posée sur le point visé).
		private void LancerBancVivant()
		{
			if (CaptureVivant == null) return;
			GetTree().CreateTimer(VivantAttenteSec).Timeout += () =>
			{
				string[] a = CaptureVivant.Split(',');
				Vector2 centre = ScreenToWorld(_camera.Position);
				MacroPick? p = a[0] == "carpophore"
					? _carpophoreLayer?.Near(centre, 1e5f, a.Length > 1 ? a[1] : null)
					: _macroLife?.Near(centre, 1e5f) ?? _foragerLayer?.Near(centre, 1e5f);
				if (p == null && a[0] == "carpophore") p = CarpophoreSynthetique(a.Length > 1 ? a[1] : "b");
				if (p == null) { GD.Print($"[Vivant] aucun « {CaptureVivant} »."); GetTree().Quit(); return; }
				Vector2 canvas = WorldToScreen(p.Value.Pos.X, p.Value.Pos.Y);
				PoserCamera(System.Array.IndexOf(ZoomSteps, 4f), canvas);
				GetTree().CreateTimer(2.0).Timeout += () =>
				{
					Vector2 px = WorldToWindow(canvas);
					Input.WarpMouse(px);
					ResemerSouris();
					GetTree().CreateTimer(1.0).Timeout += () =>
					{
						var img = GetViewport().GetTexture().GetImage();
						var r = new Rect2I((int)px.X - 320, (int)px.Y - 200, 640, 400)
							.Intersection(new Rect2I(Vector2I.Zero, img.GetSize()));
						if (CaptureVivantPng != null) img.GetRegion(r).SavePng(CaptureVivantPng);
						GD.Print($"[Vivant] {p.Value} → {CaptureVivantPng} · info-bulle « {_infoBulle?.Text} »");
						GetTree().Quit();
					};
				};
			};
		}

		private MacroPick? CarpophoreSynthetique(string role)
		{
			if (_carpophoreLayer == null || _origins == null || _origins.Count == 0) return null;
			string tuile = null;
			foreach (var k in _origins.Keys) { tuile = k; break; }
			float dens = role == "h" ? 0.40f : 0.80f;
			var bloc = new Godot.Collections.Dictionary
			{
				[tuile] = new Godot.Collections.Array
					{ new Godot.Collections.Array { 2, 2, 0.5, 0.5, dens, role } },
			};
			_carpophoreLayer.SetCarpophores(bloc, _origins, fade: false);
			GD.Print($"[Vivant] carpophore synthétique ({role}, densité {dens}) posé sur {tuile} (2,2).");
			return _carpophoreLayer.Near(Vector2.Zero, 1e7f, role);
		}
	}
}
